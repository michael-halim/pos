from connect_db import DatabaseConnection
import json
from datetime import datetime

from response.response_message import ResponseMessage

from generals.permission_manager import PermissionManager
from generals.constants import PERM_U_STOCK_OPNAME
from generals.messages import ERR_PERM_U_STOCK_OPNAME


class EditStockOpnameDialogRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()


    def edit_stock_opname(self, stock_opname_id: str, updated_final_stock: str):
        if not self.permission_manager.has_permission(PERM_U_STOCK_OPNAME):
            return ResponseMessage.fail(message=ERR_PERM_U_STOCK_OPNAME)

        try:
            self.cursor.execute('BEGIN TRANSACTION')
            
            # Get Old Stock Opname Data
            sql = '''SELECT sku, product_name, price, original_stock, opname_stock, final_stock, created_at, created_by
                    FROM stock_opname 
                    WHERE stock_opname_id = ?
                    LIMIT 1'''
            
            self.cursor.execute(sql, (stock_opname_id,))
            stock_opname_result = self.cursor.fetchone()
            old_sku = stock_opname_result[0]
            old_product_name = stock_opname_result[1]
            old_price = stock_opname_result[2]
            old_original_stock = stock_opname_result[3]
            old_opname_stock = stock_opname_result[4]
            old_final_stock = stock_opname_result[5]
            old_created_at = stock_opname_result[6]
            old_created_by = stock_opname_result[7]

            old_data = {
                'stock_opname_id': stock_opname_id, 'sku': old_sku, 'product_name': old_product_name,
                'price': old_price, 'original_stock': old_original_stock, 'opname_stock': old_opname_stock,
                'final_stock': old_final_stock, 'created_at': old_created_at, 'created_by': old_created_by
            }

            difference_stock = int(updated_final_stock) - int(old_original_stock)
            new_data = {
                'stock_opname_id': stock_opname_id, 'sku': old_sku, 'product_name': old_product_name,
                'price': old_price, 'original_stock': old_original_stock, 'opname_stock': difference_stock,
                'final_stock': updated_final_stock, 'created_at': old_created_at, 'created_by': old_created_by
            }

            # Update Stock Opname
            sql = '''UPDATE stock_opname SET final_stock = ?, opname_stock = ? WHERE stock_opname_id = ?'''
            self.cursor.execute(sql, (updated_final_stock, difference_stock, stock_opname_id))


            # Insert Stock Card
            remarks = f'Edit Stock Opname from {old_final_stock} to {updated_final_stock} with Stock Opname Id: {stock_opname_id} by {self.permission_manager.get_username()}'
            sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                stock_out, running_balance, remarks) 
                     VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''
            
            self.cursor.execute(sql, (old_sku, stock_opname_id, None, None, updated_final_stock, remarks))
            

            # Insert Log
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
           
            self.cursor.execute(sql, (f'Stock Opname#{stock_opname_id} updated', remarks, 'U', 
                                        json.dumps(old_data), json.dumps(new_data), today, self.permission_manager.get_user_id()))
            

            # Commit the transaction
            self.db.commit()

            return ResponseMessage.ok(message="Stock opname updated successfully")
        

        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(message=str(e))
