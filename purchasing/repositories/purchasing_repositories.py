from typing import List
from datetime import datetime, timedelta
from connect_db import DatabaseConnection

from purchasing.models.purchasing_models import (
    ProductModel, 
    ProductUnitsModel, 
    PurchasingModel, 
    DetailPurchasingModel, 
    PurchasingHistoryTableItemModel
)
from dialogs.suppliers_dialog.models.suppliers_dialog_models import SupplierModel

from generals.permission_manager import PermissionManager

from response.response_message import ResponseMessage

class PurchasingRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()

        
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


    def create_purchasing_id(self) -> str:
        # Get Today's Date
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        # Get count of all transactions today   
        sql = '''SELECT COUNT(*) FROM purchasing_history WHERE created_at >= ? and created_at < ?'''
        self.cursor.execute(sql, (f'{today}', f'{tomorrow}'))

        purchasing_count_today = self.cursor.fetchone()[0]
        purchasing_count_today += 1

        return f'PO{datetime.now().strftime("%Y%m%d")}{purchasing_count_today:04d}'
    

    def submit_purchasing(self, purchasing: PurchasingModel, detail_purchasing: List[DetailPurchasingModel]) -> ResponseMessage:
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get current timestamp
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Insert main purchasing first
            sql = '''INSERT INTO purchasing_history (purchasing_id, supplier_id, invoice_date, invoice_number, 
                                                    invoice_expired_date, total_amount, total_discount, created_at, 
                                                    created_by, purchasing_remarks) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
            
            purchasing_id = purchasing.purchasing_id
            self.cursor.execute(sql, (purchasing_id, purchasing.supplier_id, purchasing.invoice_date, purchasing.invoice_number, 
                                      purchasing.invoice_expired_date, purchasing.total_amount, purchasing.total_discount, current_time, 
                                      self.permission_manager.get_user_id(), purchasing.purchasing_remarks))
            

            # Insert all detail purchasing
            sql = '''INSERT INTO detail_purchasing_history (purchasing_id, sku, unit, unit_value, qty, price, 
                                                                discount_rp, discount_pct, subtotal) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'''

            for detail in detail_purchasing:  
                sku = detail.sku
                qty = detail.qty
                unit_value = detail.unit_value
                unit = detail.unit
                stock_affected: int = int(qty) * int(unit_value)

                # Net Price = Subtotal / Stock Affected -> Price for each smallest unit
                net_price: int =  int(detail.subtotal) / int(stock_affected)
                
                # Insert detail purchasing
                self.cursor.execute(sql, (detail.purchasing_id, sku, unit, unit_value, qty, detail.price,  
                                          detail.discount_rp, detail.discount_pct, detail.subtotal))
                
                # Update product stock, average price, and last price
                # Average Price = ((Average Price * Old Stock) + (New Price * New Qty)) / (Old Stock + New Qty)
                update_sql = '''UPDATE products 
                                SET stock = stock + ?, 
                                    last_price = ?, 
                                    average_price = ((average_price * stock) + ( ? * ? )) / (stock + ?) 
                                WHERE sku = ?'''
                self.cursor.execute(update_sql, (stock_affected, net_price, net_price, stock_affected, stock_affected, sku))


                # Get Updated Stock Value
                get_updated_stock_sql = 'SELECT stock FROM products WHERE sku = ?'
                self.cursor.execute(get_updated_stock_sql, (sku,))
                updated_stock = self.cursor.fetchone()[0]


                # Update Stock Card
                stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''
                
                self.cursor.execute(stock_card_sql, (sku, purchasing_id, stock_affected, None, updated_stock, ''))


            # If everything successful, commit the transaction
            self.db.commit()
            
            return ResponseMessage.ok(f"Purchasing#{purchasing_id} submitted successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(f"Failed to submit purchasing: {str(e)}")
        


    def update_purchasing(self, purchasing: PurchasingModel, 
                          added_detail_purchasing: List[DetailPurchasingModel], 
                          updated_detail_purchasing: List[DetailPurchasingModel], 
                          deleted_detail_purchasing: List[DetailPurchasingModel]):
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get current timestamp
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Update main transaction
            sql = '''UPDATE purchasing_history 
                    SET supplier_id = ?, invoice_date = ?, invoice_number = ?, invoice_expired_date = ?, total_amount = ?, 
                        updated_at = ?, updated_by = ?, purchasing_remarks = ?
                    WHERE purchasing_id = ?'''

            print(f'purchasing_id in repository: {purchasing.purchasing_id}')
            self.cursor.execute(sql, (purchasing.supplier_id, purchasing.invoice_date, purchasing.invoice_number, purchasing.invoice_expired_date, purchasing.total_amount, 
                                      current_time, self.permission_manager.get_user_id(), purchasing.purchasing_remarks, purchasing.purchasing_id))


            # Update updated detail purchasing
            for updated_detail in updated_detail_purchasing:
                # Get Old Stock
                get_old_stock_sql = 'SELECT qty FROM detail_purchasing_history WHERE sku = ? and unit = ? and purchasing_id = ?'
                self.cursor.execute(get_old_stock_sql, (updated_detail.sku, updated_detail.unit, purchasing.purchasing_id))

                old_stock = self.cursor.fetchone()[0]

                # If now stock is less than old stock, then update stock
                if int(updated_detail.qty) < int(old_stock):
                    # Subtract Stock if updated detail purchasing qty is less than old detail purchasing qty
                    stock_affected: int = int(updated_detail.qty) * int(updated_detail.unit_value)
                    stock_subtracted: int = int(old_stock) - int(stock_affected)

                    # Net Price = Subtotal / Stock Affected -> Price for each smallest unit
                    net_price: int =  int(updated_detail.subtotal) / int(stock_affected)

                    # Average Price = ((Average Price * Old Stock) - (New Price * New Qty)) / (Old Stock - New Qty)
                    update_sql = '''UPDATE products 
                                    SET stock = stock - ?,
                                    last_price = ?,
                                    average_price = ((average_price * stock) + ( ? * ? )) / (stock + ?) 
                                    WHERE sku = ?'''
                    self.cursor.execute(update_sql, (stock_subtracted, net_price, net_price, stock_affected, stock_affected, updated_detail.sku))

                    # Get updated stock value directly after update
                    get_updated_stock_sql = 'SELECT stock FROM products WHERE sku = ?'
                    self.cursor.execute(get_updated_stock_sql, (updated_detail.sku,))

                    updated_stock = self.cursor.fetchone()[0]


                    # Update Stock Card by Inserting Data to Stock Card Table
                    remarks = f'Correction Stock from {old_stock} to {stock_affected} in Edit Purchasing#{purchasing.purchasing_id} by {self.permission_manager.get_username()}'
                    stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''

                    self.cursor.execute(stock_card_sql, (updated_detail.sku, purchasing.purchasing_id, None, stock_subtracted, updated_stock, remarks))

                
                elif int(updated_detail.qty) > int(old_stock):
                    # Add Stock if updated detail purchasing qty is more than old detail purchasing qty
                    stock_affected: int = int(updated_detail.qty) * int(updated_detail.unit_value)
                    stock_added: int = int(stock_affected) - int(old_stock)

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
                    remarks = f'Correction Stock from {old_stock} to {stock_affected} in Edit Purchasing#{purchasing.purchasing_id} by {self.permission_manager.get_username()}'
                    stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''    
                    
                    self.cursor.execute(stock_card_sql, (updated_detail.sku, purchasing.purchasing_id, stock_added, None, updated_stock, remarks)) 


                sql = '''UPDATE detail_purchasing_history 
                        SET qty = ?, price = ?, discount_rp = ?, discount_pct = ?, subtotal = ?
                         WHERE purchasing_id = ? AND sku = ? AND unit = ?'''
                
                self.cursor.execute(sql, (updated_detail.qty, updated_detail.price, updated_detail.discount_rp, 
                                        updated_detail.discount_pct, updated_detail.subtotal, 
                                        purchasing.purchasing_id, updated_detail.sku, updated_detail.unit))


            # Delete detail purchasing
            for deleted_detail in deleted_detail_purchasing:
                sql = '''DELETE FROM detail_purchasing_history WHERE purchasing_id = ? AND sku = ? and unit = ?'''
                self.cursor.execute(sql, (purchasing.purchasing_id, deleted_detail.sku, deleted_detail.unit))

                # Update product stock
                stock_affected: int = int(deleted_detail.qty) * int(deleted_detail.unit_value)
                stock_subtracted: int = int(deleted_detail.qty) - int(stock_affected)

                # Net Price = Subtotal / Stock Affected -> Price for each smallest unit
                net_price: int =  int(deleted_detail.subtotal) / int(stock_affected)

                # Average Price = ((Average Price * Old Stock) - (New Price * New Qty)) / (Old Stock - New Qty)
                update_sql = '''UPDATE products 
                                SET stock = stock - ?,
                                    last_price = ?,
                                    average_price = ((average_price * stock) - ( ? * ? )) / (stock - ?) 
                                WHERE sku = ?'''
                self.cursor.execute(update_sql, (stock_subtracted, net_price, net_price, stock_affected, stock_affected, deleted_detail.sku))

                # Get updated stock value directly after update
                get_updated_stock_sql = 'SELECT stock FROM products WHERE sku = ?'
                self.cursor.execute(get_updated_stock_sql, (deleted_detail.sku,))

                updated_stock = self.cursor.fetchone()[0]


                # Update Stock Card by Inserting Data to Stock Card Table
                remarks = f'Correction Stock from {old_stock} to 0 in Edit Purchasing#{purchasing.purchasing_id} by {self.permission_manager.get_username()}'
                stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''

                self.cursor.execute(stock_card_sql, (deleted_detail.sku, purchasing.purchasing_id, None, stock_affected, updated_stock, remarks))


            # Insert added detail purchasing
            for added_detail in added_detail_purchasing:
                sql = '''INSERT INTO detail_purchasing_history (purchasing_id, sku, unit, unit_value, qty, 
                                                            price, discount_rp, discount_pct, subtotal) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'''

                self.cursor.execute(sql, (purchasing.purchasing_id, added_detail.sku, added_detail.unit, added_detail.unit_value, 
                                          added_detail.qty, added_detail.price, added_detail.discount_rp, added_detail.discount_pct, 
                                          added_detail.subtotal))

                # Update product stock
                stock_affected: int = int(added_detail.qty) * int(added_detail.unit_value)

                # Net Price = Subtotal / Stock Affected -> Price for each smallest unit
                net_price: int =  int(added_detail.subtotal) / int(stock_affected)

                # Average Price = ((Average Price * Old Stock) + (New Price * New Qty)) / (Old Stock + New Qty)
                update_sql = '''UPDATE products 
                                SET stock = stock + ?,
                                    last_price = ?,
                                    average_price = ((average_price * stock) + ( ? * ? )) / (stock + ?) 
                                WHERE sku = ?'''
                self.cursor.execute(update_sql, (stock_affected, net_price, net_price, stock_affected, stock_affected, added_detail.sku))

                # Get updated stock value directly after update
                get_updated_stock_sql = 'SELECT stock FROM products WHERE sku = ?'
                self.cursor.execute(get_updated_stock_sql, (added_detail.sku,))  


                updated_stock = self.cursor.fetchone()[0]

                # Update Stock Card by Inserting Data to Stock Card Table
                remarks = f'Correction Stock from 0 to {stock_affected} in Edit Purchasing#{purchasing.purchasing_id} by {self.permission_manager.get_username()}'
                stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''

                self.cursor.execute(stock_card_sql, (added_detail.sku, purchasing.purchasing_id, stock_affected, None, updated_stock, remarks))


            self.db.commit()

            return ResponseMessage.ok(f"Purchasing#{purchasing.purchasing_id} updated successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            print('error in update purchasing ', e)
            self.db.rollback()
            return ResponseMessage.fail(f"Failed to update purchasing: {str(e)}")
        

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
        

    def get_purchasing_history_by_sku(self, sku: str) -> list[PurchasingHistoryTableItemModel]:
        try:
            sql = '''SELECT ph.created_at, s.supplier_name, dph.qty, dph.unit, dph.price,
                            dph.discount_rp, dph.discount_pct, dph.subtotal
                    FROM detail_purchasing_history dph 
                    JOIN purchasing_history ph on ph.purchasing_id = dph.purchasing_id
                    LEFT JOIN suppliers s on s.supplier_id = ph.supplier_id
                    WHERE dph.sku = ?
                    ORDER BY ph.created_at DESC'''
            
            self.cursor.execute(sql, (sku,))

            purchasing_history_results = self.cursor.fetchall()

            if purchasing_history_results:
                purchasing_history = [
                    PurchasingHistoryTableItemModel(created_at=ph[0], 
                                                    supplier_name=ph[1], 
                                                    qty=ph[2], 
                                                    unit=ph[3], 
                                                    price=ph[4], 
                                                    discount_rp=ph[5], 
                                                    discount_pct=ph[6], 
                                                    subtotal=ph[7]) 
                    for ph in purchasing_history_results
                ]

                return ResponseMessage.ok(
                    message="Purchasing history fetched successfully!",
                    data=purchasing_history
                )
            
            return ResponseMessage.ok(
                message="Purchasing history not found!",
                data=None
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
        

    def get_detail_purchasing_by_id(self, purchasing_id: str):
        try:
            sql = '''SELECT dph.purchasing_id, dph.sku, p.product_name, dph.unit, dph.unit_value, dph.qty, dph.price, dph.discount_rp, 
                            dph.discount_pct, dph.subtotal
                    FROM detail_purchasing_history dph 
                    JOIN products p on p.sku = dph.sku
                    WHERE dph.purchasing_id = ?'''
            
            self.cursor.execute(sql, (purchasing_id,))
            
            results = self.cursor.fetchall()

            if results:
                detail_purchasing = [
                    DetailPurchasingModel(purchasing_id=r[0], sku=r[1], product_name=r[2], unit=r[3], 
                                          unit_value=r[4], qty=r[5], price=r[6], discount_rp=r[7], 
                                          discount_pct=r[8], subtotal=r[9])
                    for r in results
                ]

                return ResponseMessage.ok(message="Detail purchasing fetched successfully!", data=detail_purchasing)
            
            return ResponseMessage.ok(message="Detail purchasing not found!", data=None)
        
        except Exception as e:
            print('error in get detail purchasing by id ', e)
            return ResponseMessage.fail(message=f"Error: {str(e)}")
        

    def get_purchasing_by_id(self, purchasing_id: str):
        try:
            sql = '''SELECT ph.purchasing_id, ph.supplier_id, ph.invoice_date, ph.invoice_number, ph.invoice_expired_date, 
                            ph.total_amount, ph.total_discount, ph.created_at, ph.purchasing_remarks
                    FROM purchasing_history ph
                    WHERE ph.purchasing_id = ?'''
            
            self.cursor.execute(sql, (purchasing_id,))

            result = self.cursor.fetchone()

            purchasing = PurchasingModel(purchasing_id=result[0], supplier_id=result[1], invoice_date=result[2], 
                                            invoice_number=result[3], invoice_expired_date=result[4], total_amount=result[5], 
                                            total_discount=result[6], created_at=result[7], purchasing_remarks=result[8])
            
            return ResponseMessage.ok(
                message="Purchasing fetched successfully!",
                data=purchasing
            )
            
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")

