from connect_db import DatabaseConnection
from typing import List
from datetime import datetime, timedelta
import json

from sales_return.models.sales_return_models import (
     ProductModel, ProductUnitsModel , SalesReturnModel, 
     DetailSalesReturnModel, CustomerModel
)
from response.response_message import ResponseMessage

from generals.constants import PERM_C_SALES_RETURN, PERM_U_SALES_RETURN
from generals.messages import ERR_PERM_C_SALES_RETURN, ERR_PERM_U_SALES_RETURN
from generals.permission_manager import PermissionManager


class SalesReturnRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()
  

    def get_customer_by_id(self, customer_id: str):
        try:
            sql = '''SELECT customer_id, customer_name
                     FROM customers 
                     WHERE customer_id = ? 
                     LIMIT 1'''
            
            self.cursor.execute(sql, (customer_id,))
            result = self.cursor.fetchone()
            
            if result:
                customer = CustomerModel(
                    customer_id=result[0],
                    customer_name=result[1],
                )

                return ResponseMessage.ok(
                    message="Customer fetched successfully!",
                    data=customer
                )
            
            return ResponseMessage.ok(
                message="Customer not found!",
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
        

    def create_sales_return_id(self) -> str:
        # Get Today's Date
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        # Get count of all transactions today   
        sql = '''SELECT COUNT(*) FROM sales_return WHERE created_at >= ? and created_at < ?'''
        self.cursor.execute(sql, (f'{today}', f'{tomorrow}'))

        sales_return_count_today = self.cursor.fetchone()[0]
        sales_return_count_today += 1

        return f'RTS{datetime.now().strftime("%Y%m%d")}{sales_return_count_today:04d}'
    

    def submit_sales_return(self, sales_return_data: SalesReturnModel, detail_sales_return: list[DetailSalesReturnModel]):
        if not self.permission_manager.has_permission(PERM_C_SALES_RETURN):
            return ResponseMessage.fail(message=ERR_PERM_C_SALES_RETURN)
        
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get current timestamp
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Insert main sales return first
            sql = '''INSERT INTO sales_return (sales_return_id, customer_id, sales_return_date, total_amount, created_at, 
                                                    created_by, sales_return_remarks) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            
            self.cursor.execute(sql, (sales_return_data.sales_return_id, sales_return_data.customer_id, sales_return_data.sales_return_date, sales_return_data.total_amount, today, 
                                      self.permission_manager.get_user_id(), sales_return_data.sales_return_remarks))
            

            # Insert all detail sales return
            sql = '''INSERT INTO detail_sales_return (sales_return_id, sku, unit, unit_value, qty, price, subtotal) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''

            detail_sales_return_data = []
            for detail in detail_sales_return:  
                sku = detail.sku
                qty = detail.qty
                unit_value = detail.unit_value
                unit = detail.unit
                stock_affected: int = int(qty) * int(unit_value)

                # Net Price = Subtotal / Stock Affected -> Price for each smallest unit
                net_price: int =  int(detail.subtotal) / int(stock_affected)

                # Insert detail sales return
                self.cursor.execute(sql, (detail.sales_return_id, sku, unit, unit_value, qty, detail.price,  detail.subtotal))
                
                # Update product stock, average price, and last price
                # Average Price = ((Average Price * Old Stock) + (Return Sales Price * Return Qty)) / (Old Stock + Return Qty)
                update_sql = '''UPDATE products 
                                SET stock = stock + ?, 
                                    average_price = ((average_price * stock) + ( ? * ? )) / (stock + ?) 
                                WHERE sku = ?'''
                self.cursor.execute(update_sql, (stock_affected, net_price, stock_affected,  stock_affected, sku))


                # Get Updated Stock Value
                get_updated_stock_sql = 'SELECT stock FROM products WHERE sku = ?'
                self.cursor.execute(get_updated_stock_sql, (sku,))
                updated_stock = self.cursor.fetchone()[0]

                detail_sales_return_data.append({
                       'sku': sku,
                       'unit': unit,
                       'unit_value': unit_value,
                       'qty': qty,
                       'price': detail.price,
                       'subtotal': detail.subtotal
                })

                # Update Stock Card
                remarks = f'Sales Return#{sales_return_data.sales_return_id} by {self.permission_manager.get_username()}'
                stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''
                
                self.cursor.execute(stock_card_sql, (sku, sales_return_data.sales_return_id, stock_affected, None, updated_stock, remarks))


            # Insert Log
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            
            new_data = {
                'sales_return_id': sales_return_data.sales_return_id,
                'customer_id': sales_return_data.customer_id,
                'sales_return_date': sales_return_data.sales_return_date,
                'total_amount': sales_return_data.total_amount,
                'sales_return_remarks': sales_return_data.sales_return_remarks,
                'detail_sales_return': detail_sales_return_data
            }
            
            self.cursor.execute(sql, (f'Sales Return#{sales_return_data.sales_return_id} submitted', f'Sales Return#{sales_return_data.sales_return_id} submitted successfully!', 'C', 
                                        None, json.dumps(new_data), today, self.permission_manager.get_user_id()))


            # If everything successful, commit the transaction
            self.db.commit()
            
            return ResponseMessage.ok(f"Sales Return#{sales_return_data.sales_return_id} submitted successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(f"Failed to submit sales return: {str(e)}")
        

    def update_sales_return(self, sales_return_data: SalesReturnModel, 
                          added_detail_sales_return: List[DetailSalesReturnModel], 
                          updated_detail_sales_return: List[DetailSalesReturnModel], 
                          deleted_detail_sales_return: List[DetailSalesReturnModel]):
                          
        if not self.permission_manager.has_permission(PERM_U_SALES_RETURN):
            return ResponseMessage.fail(message=ERR_PERM_U_SALES_RETURN)
        
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get current timestamp
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Get old sales return data
            sql = '''SELECT customer_id, sales_return_date, total_amount, 
                            sales_return_remarks, created_at, created_by, updated_at, updated_by
                    FROM sales_return 
                    WHERE sales_return_id = ?
                    LIMIT 1'''
            
            self.cursor.execute(sql, (sales_return_data.sales_return_id,))
            sales_return_result = self.cursor.fetchone()

            old_data = {
                'sales_return_id': sales_return_data.sales_return_id,
                'customer_id': sales_return_result[0],
                'sales_return_date': sales_return_result[1],
                'total_amount': sales_return_result[2],
                'sales_return_remarks': sales_return_result[3],
                'created_at': sales_return_result[4],
                'created_by': sales_return_result[5],
                'updated_at': sales_return_result[6],
                'updated_by': sales_return_result[7]
            }

            # Get old detail sales return data
            sql = '''SELECT sku, unit, unit_value, qty, price, subtotal 
                    FROM detail_sales_return 
                    WHERE sales_return_id = ?'''
            
            self.cursor.execute(sql, (sales_return_data.sales_return_id,))

            detail_sales_return_results = self.cursor.fetchall()

            old_detail_sales_return_data = []
            for detail in detail_sales_return_results:
                old_detail_sales_return_data.append({
                    'sku': detail[0],
                    'unit': detail[1],
                    'unit_value': detail[2],
                    'qty': detail[3],
                    'price': detail[4],
                    'subtotal': detail[5]
                })

            old_data['detail_sales_return'] = old_detail_sales_return_data


            # Update main purchase return
            sql = '''UPDATE sales_return
                    SET customer_id = ?, sales_return_date = ?, total_amount = ?, 
                        sales_return_remarks = ?, updated_at = ?, updated_by = ?
                    WHERE sales_return_id = ?'''

            self.cursor.execute(sql, (sales_return_data.customer_id, sales_return_data.sales_return_date, sales_return_data.total_amount, 
                                      sales_return_data.sales_return_remarks, today, self.permission_manager.get_user_id(), sales_return_data.sales_return_id))


            # Update updated detail sales return
            updated_detail_sales_return_data = []
            for updated_detail in updated_detail_sales_return:
                # Get Old Stock
                get_old_stock_sql = 'SELECT qty FROM detail_sales_return WHERE sku = ? and unit = ? and sales_return_id = ?'
                self.cursor.execute(get_old_stock_sql, (updated_detail.sku, updated_detail.unit, sales_return_data.sales_return_id))

                old_stock = self.cursor.fetchone()[0]

                # If now stock is less than old stock, then update stock
                if int(updated_detail.qty) < int(old_stock):
                    # Add Stock if updated detail sales return qty is less than old detail sales return qty
                    stock_affected: int = int(updated_detail.qty) * int(updated_detail.unit_value)
                    stock_subtracted: int = int(old_stock) - int(stock_affected)

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
                    remarks = f'Correction Stock from {old_stock} to {stock_affected} in Edit Sales Return#{sales_return_data.sales_return_id} by {self.permission_manager.get_username()}'
                    stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''

                    self.cursor.execute(stock_card_sql, (updated_detail.sku, sales_return_data.sales_return_id, None, stock_subtracted, updated_stock, remarks))

                
                elif int(updated_detail.qty) > int(old_stock):
                    # Subtract Stock if updated detail sales return qty is more than old detail sales return qty
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
                    remarks = f'Correction Stock from {old_stock} to {stock_affected} in Edit Sales Return#{sales_return_data.sales_return_id} by {self.permission_manager.get_username()}'
                    stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''    
                    
                    self.cursor.execute(stock_card_sql, (updated_detail.sku, sales_return_data.sales_return_id, stock_added, None, updated_stock, remarks)) 


                sql = '''UPDATE detail_sales_return 
                        SET qty = ?, price = ?, subtotal = ?
                         WHERE sales_return_id = ? AND sku = ? AND unit = ?'''
                
                self.cursor.execute(sql, (updated_detail.qty, updated_detail.price, updated_detail.subtotal, 
                                        sales_return_data.sales_return_id, updated_detail.sku, updated_detail.unit))
                

                updated_detail_sales_return_data.append({
                    'sku': updated_detail.sku,
                    'unit': updated_detail.unit,
                    'unit_value': updated_detail.unit_value,
                    'qty': updated_detail.qty,
                    'price': updated_detail.price,
                    'subtotal': updated_detail.subtotal
                })


            # Delete detail sales return
            deleted_detail_sales_return_data = []
            for deleted_detail in deleted_detail_sales_return:
                sql = '''DELETE FROM detail_sales_return WHERE sales_return_id = ? AND sku = ? and unit = ?'''
                self.cursor.execute(sql, (sales_return_data.sales_return_id, deleted_detail.sku, deleted_detail.unit))

                # Update product stock
                stock_affected: int = int(deleted_detail.qty) * int(deleted_detail.unit_value)

                # Net Price = Subtotal / Stock Affected -> Price for each smallest unit
                net_price: int =  int(deleted_detail.subtotal) / int(stock_affected)

                # Average Price = ((Average Price * Old Stock) - (New Price * New Qty)) / (Old Stock - New Qty)
                update_sql = '''UPDATE products 
                                SET stock = stock - ?,
                                    last_price = ?,
                                    average_price = ((average_price * stock) - ( ? * ? )) / (stock - ?) 
                                WHERE sku = ?'''
                self.cursor.execute(update_sql, (stock_affected, net_price, net_price, stock_affected, stock_affected, deleted_detail.sku))

                # Get updated stock value directly after update
                get_updated_stock_sql = 'SELECT stock FROM products WHERE sku = ?'
                self.cursor.execute(get_updated_stock_sql, (deleted_detail.sku,))

                updated_stock = self.cursor.fetchone()[0]


                # Update Stock Card by Inserting Data to Stock Card Table
                remarks = f'Correction Stock from {stock_affected} to 0 in Edit Sales Return#{sales_return_data.sales_return_id} by {self.permission_manager.get_username()}'
                stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''
                
                self.cursor.execute(stock_card_sql, (deleted_detail.sku, sales_return_data.sales_return_id, None, stock_affected, updated_stock, remarks))

                deleted_detail_sales_return_data.append({
                    'sku': deleted_detail.sku,
                    'unit': deleted_detail.unit,
                    'unit_value': deleted_detail.unit_value,
                    'qty': deleted_detail.qty,
                    'price': deleted_detail.price,
                    'subtotal': deleted_detail.subtotal
                })


            # Insert added detail sales return
            added_detail_sales_return_data = []
            for added_detail in added_detail_sales_return:
                sql = '''INSERT INTO detail_sales_return (sales_return_id, sku, unit, unit_value, qty, 
                                                            price, subtotal) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)'''

                self.cursor.execute(sql, (sales_return_data.sales_return_id, added_detail.sku, added_detail.unit, added_detail.unit_value, 
                                          added_detail.qty, added_detail.price, added_detail.subtotal))

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
                remarks = f'Correction Stock from 0 to {stock_affected} in Edit Sales Return#{sales_return_data.sales_return_id} by {self.permission_manager.get_username()}'
                stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''
                
                self.cursor.execute(stock_card_sql, (added_detail.sku, sales_return_data.sales_return_id, stock_affected, None, updated_stock, remarks))

                added_detail_sales_return_data.append({
                    'sku': added_detail.sku,
                    'unit': added_detail.unit,
                    'unit_value': added_detail.unit_value,
                    'qty': added_detail.qty,
                    'price': added_detail.price,
                    'subtotal': added_detail.subtotal
                })


            new_data = {
                'sales_return_id': sales_return_data.sales_return_id,
                'customer_id': sales_return_data.customer_id,
                'sales_return_date': sales_return_data.sales_return_date,
                'total_amount': sales_return_data.total_amount,
                'sales_return_remarks': sales_return_data.sales_return_remarks,
                'updated_detail_sales_return': updated_detail_sales_return_data,
                'added_detail_sales_return': added_detail_sales_return_data,
                'deleted_detail_sales_return': deleted_detail_sales_return_data
            }


            # Insert Log
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)''' 
            
            self.cursor.execute(sql, (f'Sales Return#{sales_return_data.sales_return_id} updated', f'Sales Return#{sales_return_data.sales_return_id} updated successfully!', 'U', 
                                        json.dumps(old_data), json.dumps(new_data), today, self.permission_manager.get_user_id()))
            
            # If everything successful, commit the transaction
            self.db.commit()

            return ResponseMessage.ok(f"Sales Return#{sales_return_data.sales_return_id} updated successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            print('error in update sales return ', e)
            self.db.rollback()
            return ResponseMessage.fail(f"Failed to update sales return: {str(e)}")
        

    def get_sales_return_by_id(self, sales_return_id: str):
        try:
            sql = '''SELECT sr.customer_id, sr.sales_return_date, sr.total_amount, 
                            sr.sales_return_remarks, sr.created_at, sr.created_by, sr.updated_at, sr.updated_by
                    FROM sales_return sr
                    WHERE sr.sales_return_id = ?'''

            self.cursor.execute(sql, (sales_return_id,))

            result = self.cursor.fetchone()

            sales_return = SalesReturnModel(sales_return_id=sales_return_id, customer_id=result[0], sales_return_date=result[1], total_amount=result[2], 
                                            sales_return_remarks=result[3], created_at=result[4], created_by=result[5], 
                                            updated_at=result[6], updated_by=result[7])
            
            return ResponseMessage.ok(
                message="Sales Return fetched successfully!",
                data=sales_return
            )
            
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def get_detail_sales_return_by_id(self, sales_return_id: str):
        try:
            sql = '''SELECT dsr.sku, p.product_name, dsr.unit, dsr.unit_value, dsr.qty, dsr.price, dsr.subtotal
                    FROM detail_sales_return dsr 
                    JOIN products p on p.sku = dsr.sku
                    WHERE dsr.sales_return_id = ?'''
            
            self.cursor.execute(sql, (sales_return_id,))
            
            results = self.cursor.fetchall()

            if results:
                detail_sales_return = [
                    DetailSalesReturnModel(sales_return_id=sales_return_id, sku=r[0], product_name=r[1], unit=r[2], 
                                          unit_value=r[3], qty=r[4], price=r[5], subtotal=r[6])
                    for r in results
                ]

                return ResponseMessage.ok(message="Detail sales return fetched successfully!", data=detail_sales_return)
            
            return ResponseMessage.ok(message="Detail sales return not found!", data=None)
        
        except Exception as e:
            print('error in get detail sales return by id ', e)
            return ResponseMessage.fail(message=f"Error: {str(e)}")