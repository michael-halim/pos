from connect_db import DatabaseConnection
from typing import List
from datetime import datetime, timedelta
from response.response_message import ResponseMessage
import json

from generals.permission_manager import PermissionManager
from dialogs.suppliers_dialog.models.suppliers_dialog_models import SupplierModel

from purchase_return.models.purchase_return_models import ProductModel, ProductUnitsModel
from purchase_return.models.purchase_return_models import PurchaseReturnModel, DetailPurchaseReturnModel


class PurchaseReturnRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()
        

    def get_supplier_by_id(self, supplier_id: str):
        try:
            sql = '''SELECT supplier_id, supplier_name, supplier_address, supplier_city, 
                            supplier_phone, supplier_remarks 
                     FROM suppliers 
                     WHERE supplier_id = ? 
                     LIMIT 1'''
            
            self.cursor.execute(sql, (supplier_id,))
            result = self.cursor.fetchone()
            
            if result:
                supplier = SupplierModel(
                    supplier_id=result[0],
                    supplier_name=result[1],
                    supplier_address=result[2],
                    supplier_city=result[3],
                    supplier_phone=result[4],
                    supplier_remarks=result[5]
                )

                return ResponseMessage.ok(
                    message="Supplier fetched successfully!",
                    data=supplier
                )
            
            return ResponseMessage.ok(
                message="Supplier not found!",
                data=None
            )
            
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
        

    
    def get_product_by_sku(self, sku: str):
        try:
            sql = 'SELECT product_name, price, unit, stock FROM products WHERE sku = ?'
            self.cursor.execute(sql, (sku,))

            if self.cursor.rowcount == 0:
                return ResponseMessage.ok(
                    message=f"Product with sku {sku} not found",
                    data=None
                )

            result = self.cursor.fetchone()
            return ResponseMessage.ok(
                message="Success",
                data=ProductModel(product_name=result[0], price=result[1], unit=result[2], stock=result[3])
            )

        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
        
    
    def get_product_unit_details(self, sku: str) -> list[ProductUnitsModel]:
        try:
            sql = '''SELECT u.unit, u.unit_value FROM units u WHERE u.sku = ?'''

            self.cursor.execute(sql, (sku,))
            results =  self.cursor.fetchall()

            if self.cursor.rowcount == 0:
                return ResponseMessage.ok(
                    message=f"Product with sku {sku} not found",
                    data=None
                )

            product_units = [
                ProductUnitsModel(unit=r[0], unit_value=r[1])  for r in results
            ]

            return ResponseMessage.ok(
                message="Success",
                data=product_units
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
        

    def create_purchase_return_id(self) -> str:
        # Get Today's Date
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        # Get count of all transactions today   
        sql = '''SELECT COUNT(*) FROM purchase_return WHERE created_at >= ? and created_at < ?'''
        self.cursor.execute(sql, (f'{today}', f'{tomorrow}'))

        purchase_return_count_today = self.cursor.fetchone()[0]
        purchase_return_count_today += 1

        return f'RTP{datetime.now().strftime("%Y%m%d")}{purchase_return_count_today:04d}'
    

    def submit_purchase_return(self, purchase_return_data: PurchaseReturnModel, detail_purchase_return: list[DetailPurchaseReturnModel]):
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get current timestamp
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Insert main purchase return first
            sql = '''INSERT INTO purchase_return (purchase_return_id, supplier_id, purchase_return_date, total_amount, created_at, 
                                                    created_by, purchase_return_remarks, updated_at, updated_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'''
            
            self.cursor.execute(sql, (purchase_return_data.purchase_return_id, purchase_return_data.supplier_id, purchase_return_data.purchase_return_date, purchase_return_data.total_amount, today, 
                                      self.permission_manager.get_user_id(), purchase_return_data.purchase_return_remarks, today, 
                                      self.permission_manager.get_user_id()))
            

            # Insert all detail purchase return
            sql = '''INSERT INTO detail_purchase_return (purchase_return_id, sku, unit, unit_value, qty, price, subtotal) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''

            detail_purchase_return_data = []
            for detail in detail_purchase_return:  
                sku = detail.sku
                qty = detail.qty
                unit_value = detail.unit_value
                unit = detail.unit
                stock_affected: int = int(qty) * int(unit_value)

                # Net Price = Subtotal / Stock Affected -> Price for each smallest unit
                net_price: int =  int(detail.subtotal) / int(stock_affected)

                # Insert detail purchase return
                self.cursor.execute(sql, (detail.purchase_return_id, sku, unit, unit_value, qty, detail.price,  detail.subtotal))
                
                # Update product stock, average price, and last price
                # Average Price = ((Average Price * Old Stock) - (Return Purchase Price * Return Qty)) / (Old Stock - Return Qty)
                update_sql = '''UPDATE products 
                                SET stock = stock - ?, 
                                    average_price = ((average_price * stock) - ( ? * ? )) / (stock - ?) 
                                WHERE sku = ?'''
                self.cursor.execute(update_sql, (stock_affected, net_price, stock_affected,  stock_affected, sku))


                # Get Updated Stock Value
                get_updated_stock_sql = 'SELECT stock FROM products WHERE sku = ?'
                self.cursor.execute(get_updated_stock_sql, (sku,))
                updated_stock = self.cursor.fetchone()[0]

                detail_purchase_return_data.append({
                       'sku': sku,
                       'unit': unit,
                       'unit_value': unit_value,
                       'qty': qty,
                       'price': detail.price,
                       'subtotal': detail.subtotal
                })

                # Update Stock Card
                remarks = f'Purchase Return#{purchase_return_data.purchase_return_id} by {self.permission_manager.get_username()}'
                stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''
                
                self.cursor.execute(stock_card_sql, (sku, purchase_return_data.purchase_return_id, None, stock_affected, updated_stock, remarks))


            # Insert Log
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            
            new_data = {
                'purchase_return_id': purchase_return_data.purchase_return_id,
                'supplier_id': purchase_return_data.supplier_id,
                'purchase_return_date': purchase_return_data.purchase_return_date,
                'total_amount': purchase_return_data.total_amount,
                'purchase_return_remarks': purchase_return_data.purchase_return_remarks,
                'detail_purchase_return': detail_purchase_return_data
            }
            
            self.cursor.execute(sql, (f'Purchase Return#{purchase_return_data.purchase_return_id} submitted', f'Purchase Return#{purchase_return_data.purchase_return_id} submitted successfully!', 'C', 
                                        None, json.dumps(new_data), today, self.permission_manager.get_user_id()))


            # If everything successful, commit the transaction
            self.db.commit()
            
            return ResponseMessage.ok(f"Purchase Return#{purchase_return_data.purchase_return_id} submitted successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(f"Failed to submit purchase return: {str(e)}")
        

    def update_purchase_return(self, purchase_return_data: PurchaseReturnModel, 
                          added_detail_purchase_return: List[DetailPurchaseReturnModel], 
                          updated_detail_purchase_return: List[DetailPurchaseReturnModel], 
                          deleted_detail_purchase_return: List[DetailPurchaseReturnModel]):
                          
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get current timestamp
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Get old purchase return data
            sql = '''SELECT supplier_id, purchase_return_date, total_amount, 
                            purchase_return_remarks, created_at, created_by, updated_at, updated_by
                    FROM purchase_return 
                    WHERE purchase_return_id = ?
                    LIMIT 1'''
            
            self.cursor.execute(sql, (purchase_return_data.purchase_return_id,))
            purchase_return_result = self.cursor.fetchone()

            old_data = {
                'purchase_return_id': purchase_return_data.purchase_return_id,
                'supplier_id': purchase_return_result[0],
                'purchase_return_date': purchase_return_result[1],
                'total_amount': purchase_return_result[2],
                'purchase_return_remarks': purchase_return_result[3],
                'created_at': purchase_return_result[4],
                'created_by': purchase_return_result[5],
                'updated_at': purchase_return_result[6],
                'updated_by': purchase_return_result[7]
            }

            # Get old detail purchase return data
            sql = '''SELECT sku, unit, unit_value, qty, price, subtotal 
                    FROM detail_purchase_return 
                    WHERE purchase_return_id = ?'''
            
            self.cursor.execute(sql, (purchase_return_data.purchase_return_id,))

            detail_purchase_return_results = self.cursor.fetchall()

            old_detail_purchase_return_data = []
            for detail in detail_purchase_return_results:
                old_detail_purchase_return_data.append({
                    'sku': detail[0],
                    'unit': detail[1],
                    'unit_value': detail[2],
                    'qty': detail[3],
                    'price': detail[4],
                    'subtotal': detail[5]
                })

            old_data['detail_purchase_return'] = old_detail_purchase_return_data


            # Update main purchase return
            sql = '''UPDATE purchase_return
                    SET supplier_id = ?, purchase_return_date = ?, total_amount = ?, 
                        purchase_return_remarks = ?, updated_at = ?, updated_by = ?
                    WHERE purchase_return_id = ?'''

            self.cursor.execute(sql, (purchase_return_data.supplier_id, purchase_return_data.purchase_return_date, purchase_return_data.total_amount, 
                                      purchase_return_data.purchase_return_remarks, today, self.permission_manager.get_user_id(), purchase_return_data.purchase_return_id))


            # Update updated detail purchase return
            updated_detail_purchase_return_data = []
            for updated_detail in updated_detail_purchase_return:
                # Get Old Stock
                get_old_stock_sql = 'SELECT qty FROM detail_purchase_return WHERE sku = ? and unit = ? and purchase_return_id = ?'
                self.cursor.execute(get_old_stock_sql, (updated_detail.sku, updated_detail.unit, purchase_return_data.purchase_return_id))

                old_stock = self.cursor.fetchone()[0]

                # If now stock is less than old stock, then update stock
                if int(updated_detail.qty) < int(old_stock):
                    # Add Stock if updated detail purchase return qty is less than old detail purchase return qty
                    stock_affected: int = int(updated_detail.qty) * int(updated_detail.unit_value)
                    stock_added: int = int(old_stock) - int(stock_affected)

                    # Net Price = Subtotal / Stock Affected -> Price for each smallest unit
                    net_price: int =  int(updated_detail.subtotal) / int(stock_affected)

                    # Average Price = ((Average Price * Old Stock) + (New Price * New Qty)) / (Old Stock + New Qty)
                    update_sql = '''UPDATE products 
                                    SET stock = stock + ?,
                                    last_price = ?,
                                    average_price = ((average_price * stock) + ( ? * ? )) / (stock + ?) 
                                    WHERE sku = ?'''
                    self.cursor.execute(update_sql, (stock_added, net_price, net_price, stock_affected, stock_affected, updated_detail.sku))

                    # Get updated stock value directly after update
                    get_updated_stock_sql = 'SELECT stock FROM products WHERE sku = ?'
                    self.cursor.execute(get_updated_stock_sql, (updated_detail.sku,))

                    updated_stock = self.cursor.fetchone()[0]


                    # Update Stock Card by Inserting Data to Stock Card Table
                    remarks = f'Correction Stock from {old_stock} to {stock_affected} in Edit Purchase Return#{purchase_return_data.purchase_return_id} by {self.permission_manager.get_username()}'
                    stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''

                    self.cursor.execute(stock_card_sql, (updated_detail.sku, purchase_return_data.purchase_return_id, stock_added, None, updated_stock, remarks))

                
                elif int(updated_detail.qty) > int(old_stock):
                    # Subtract Stock if updated detail purchase return qty is more than old detail purchase return qty
                    stock_affected: int = int(updated_detail.qty) * int(updated_detail.unit_value)
                    stock_subtracted: int = int(stock_affected) - int(old_stock)

                    # Net Price = Subtotal / Stock Affected -> Price for each smallest unit
                    net_price: int =  int(updated_detail.subtotal) / int(stock_affected)

                    # Average Price = ((Average Price * Old Stock) - (New Price * New Qty)) / (Old Stock - New Qty)
                    update_sql = '''UPDATE products 
                                    SET stock = stock - ?,
                                        last_price = ?,
                                        average_price = ((average_price * stock) - ( ? * ? )) / (stock - ?) 
                                    WHERE sku = ?'''
                    self.cursor.execute(update_sql, (stock_subtracted, net_price, net_price, stock_affected, stock_affected, updated_detail.sku))

                    # Get updated stock value directly after update
                    get_updated_stock_sql = 'SELECT stock FROM products WHERE sku = ?'
                    self.cursor.execute(get_updated_stock_sql, (updated_detail.sku,))

                    updated_stock = self.cursor.fetchone()[0]

                    
                    # Update Stock Card by Inserting Data to Stock Card Table
                    remarks = f'Correction Stock from {old_stock} to {stock_affected} in Edit Purchase Return#{purchase_return_data.purchase_return_id} by {self.permission_manager.get_username()}'
                    stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''    
                    
                    self.cursor.execute(stock_card_sql, (updated_detail.sku, purchase_return_data.purchase_return_id, None, stock_subtracted, updated_stock, remarks)) 


                sql = '''UPDATE detail_purchase_return 
                        SET qty = ?, price = ?, subtotal = ?
                         WHERE purchase_return_id = ? AND sku = ? AND unit = ?'''
                
                self.cursor.execute(sql, (updated_detail.qty, updated_detail.price, updated_detail.subtotal, 
                                        purchase_return_data.purchase_return_id, updated_detail.sku, updated_detail.unit))
                

                updated_detail_purchase_return_data.append({
                    'sku': updated_detail.sku,
                    'unit': updated_detail.unit,
                    'unit_value': updated_detail.unit_value,
                    'qty': updated_detail.qty,
                    'price': updated_detail.price,
                    'subtotal': updated_detail.subtotal
                })


            # Delete detail purchase return
            deleted_detail_purchase_return_data = []
            for deleted_detail in deleted_detail_purchase_return:
                sql = '''DELETE FROM detail_purchase_return WHERE purchase_return_id = ? AND sku = ? and unit = ?'''
                self.cursor.execute(sql, (purchase_return_data.purchase_return_id, deleted_detail.sku, deleted_detail.unit))

                # Update product stock
                stock_affected: int = int(deleted_detail.qty) * int(deleted_detail.unit_value)

                # Net Price = Subtotal / Stock Affected -> Price for each smallest unit
                net_price: int =  int(deleted_detail.subtotal) / int(stock_affected)

                # Average Price = ((Average Price * Old Stock) + (New Price * New Qty)) / (Old Stock + New Qty)
                update_sql = '''UPDATE products 
                                SET stock = stock + ?,
                                    last_price = ?,
                                    average_price = ((average_price * stock) + ( ? * ? )) / (stock + ?) 
                                WHERE sku = ?'''
                self.cursor.execute(update_sql, (stock_affected, net_price, net_price, stock_affected, stock_affected, deleted_detail.sku))

                # Get updated stock value directly after update
                get_updated_stock_sql = 'SELECT stock FROM products WHERE sku = ?'
                self.cursor.execute(get_updated_stock_sql, (deleted_detail.sku,))

                updated_stock = self.cursor.fetchone()[0]


                # Update Stock Card by Inserting Data to Stock Card Table
                remarks = f'Correction Stock from {stock_affected} to 0 in Edit Purchase Return#{purchase_return_data.purchase_return_id} by {self.permission_manager.get_username()}'
                stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''
                
                self.cursor.execute(stock_card_sql, (deleted_detail.sku, purchase_return_data.purchase_return_id, stock_affected, None,  updated_stock, remarks))

                deleted_detail_purchase_return_data.append({
                    'sku': deleted_detail.sku,
                    'unit': deleted_detail.unit,
                    'unit_value': deleted_detail.unit_value,
                    'qty': deleted_detail.qty,
                    'price': deleted_detail.price,
                    'subtotal': deleted_detail.subtotal
                })


            # Insert added detail purchase return
            added_detail_purchase_return_data = []
            for added_detail in added_detail_purchase_return:
                sql = '''INSERT INTO detail_purchase_return (purchase_return_id, sku, unit, unit_value, qty, 
                                                            price, subtotal) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)'''

                self.cursor.execute(sql, (purchase_return_data.purchase_return_id, added_detail.sku, added_detail.unit, added_detail.unit_value, 
                                          added_detail.qty, added_detail.price, added_detail.subtotal))

                # Update product stock
                stock_affected: int = int(added_detail.qty) * int(added_detail.unit_value)

                # Net Price = Subtotal / Stock Affected -> Price for each smallest unit
                net_price: int =  int(added_detail.subtotal) / int(stock_affected)

                # Average Price = ((Average Price * Old Stock) - (New Price * New Qty)) / (Old Stock - New Qty)
                update_sql = '''UPDATE products 
                                SET stock = stock - ?,
                                    last_price = ?,
                                    average_price = ((average_price * stock) - ( ? * ? )) / (stock - ?) 
                                WHERE sku = ?'''
                self.cursor.execute(update_sql, (stock_affected, net_price, net_price, stock_affected, stock_affected, added_detail.sku))

                # Get updated stock value directly after update
                get_updated_stock_sql = 'SELECT stock FROM products WHERE sku = ?'
                self.cursor.execute(get_updated_stock_sql, (added_detail.sku,))  


                updated_stock = self.cursor.fetchone()[0]

                # Update Stock Card by Inserting Data to Stock Card Table
                remarks = f'Correction Stock from 0 to {stock_affected} in Edit Purchase Return#{purchase_return_data.purchase_return_id} by {self.permission_manager.get_username()}'
                stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''
                
                self.cursor.execute(stock_card_sql, (added_detail.sku, purchase_return_data.purchase_return_id, None, stock_affected, updated_stock, remarks))

                added_detail_purchase_return_data.append({
                    'sku': added_detail.sku,
                    'unit': added_detail.unit,
                    'unit_value': added_detail.unit_value,
                    'qty': added_detail.qty,
                    'price': added_detail.price,
                    'subtotal': added_detail.subtotal
                })


            new_data = {
                'purchase_return_id': purchase_return_data.purchase_return_id,
                'supplier_id': purchase_return_data.supplier_id,
                'purchase_return_date': purchase_return_data.purchase_return_date,
                'total_amount': purchase_return_data.total_amount,
                'purchase_return_remarks': purchase_return_data.purchase_return_remarks,
                'updated_detail_purchase_return': updated_detail_purchase_return_data,
                'added_detail_purchase_return': added_detail_purchase_return_data,
                'deleted_detail_purchase_return': deleted_detail_purchase_return_data
            }


            # Insert Log
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)''' 
            
            self.cursor.execute(sql, (f'Purchase Return#{purchase_return_data.purchase_return_id} updated', f'Purchase Return#{purchase_return_data.purchase_return_id} updated successfully!', 'U', 
                                        json.dumps(old_data), json.dumps(new_data), today, self.permission_manager.get_user_id()))
            
            # If everything successful, commit the transaction
            self.db.commit()

            return ResponseMessage.ok(f"Purchase Return#{purchase_return_data.purchase_return_id} updated successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            print('error in update purchase return ', e)
            self.db.rollback()
            return ResponseMessage.fail(f"Failed to update purchase return: {str(e)}")
        

    def get_purchase_return_by_id(self, purchase_return_id: str):
        try:
            sql = '''SELECT pr.supplier_id, pr.purchase_return_date, pr.total_amount, 
                            pr.purchase_return_remarks, pr.created_at, pr.created_by, pr.updated_at, pr.updated_by
                    FROM purchase_return pr
                    WHERE pr.purchase_return_id = ?'''

            self.cursor.execute(sql, (purchase_return_id,))

            result = self.cursor.fetchone()

            purchase_return = PurchaseReturnModel(purchase_return_id=purchase_return_id, supplier_id=result[0], purchase_return_date=result[1], total_amount=result[2], 
                                            purchase_return_remarks=result[3], created_at=result[4], created_by=result[5], 
                                            updated_at=result[6], updated_by=result[7])
            
            return ResponseMessage.ok(
                message="Purchase Return fetched successfully!",
                data=purchase_return
            )
            
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def get_detail_purchase_return_by_id(self, purchase_return_id: str):
        try:
            sql = '''SELECT dpr.sku, p.product_name, dpr.unit, dpr.unit_value, dpr.qty, dpr.price, dpr.subtotal
                    FROM detail_purchase_return dpr 
                    JOIN products p on p.sku = dpr.sku
                    WHERE dpr.purchase_return_id = ?'''
            
            self.cursor.execute(sql, (purchase_return_id,))
            
            results = self.cursor.fetchall()

            if results:
                detail_purchase_return = [
                    DetailPurchaseReturnModel(purchase_return_id=purchase_return_id, sku=r[0], product_name=r[1], unit=r[2], 
                                          unit_value=r[3], qty=r[4], price=r[5], subtotal=r[6])
                    for r in results
                ]

                return ResponseMessage.ok(message="Detail purchase return fetched successfully!", data=detail_purchase_return)
            
            return ResponseMessage.ok(message="Detail purchase return not found!", data=None)
        
        except Exception as e:
            print('error in get detail purchase return by id ', e)
            return ResponseMessage.fail(message=f"Error: {str(e)}")