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
    

    def submit_purchase_return(self, purchase_return_data: PurchaseReturnModel, detail_purchase_return_data: list[DetailPurchaseReturnModel]):
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
            for detail in detail_purchase_return_data:  
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