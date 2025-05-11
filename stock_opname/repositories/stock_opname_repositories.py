from connect_db import DatabaseConnection
from datetime import datetime
from typing import List
import json

from stock_opname.models.stock_opname_models import StockOpnameModel, EditStockOpnameModel

from response.response_message import ResponseMessage
from generals.constants import PERM_R_STOCK_OPNAME, PERM_C_STOCK_OPNAME
from generals.messages import ERR_PERM_R_STOCK_OPNAME, ERR_PERM_C_STOCK_OPNAME
from generals.permission_manager import PermissionManager


class StockOpnameRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()


    def create_stock_opname(self, edit_stock_opname_data: EditStockOpnameModel):
        if not self.permission_manager.has_permission(PERM_C_STOCK_OPNAME):
            return ResponseMessage.fail(message=ERR_PERM_C_STOCK_OPNAME)

        try:
            self.cursor.execute('BEGIN TRANSACTION')
            
            # Insert stock opname
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            sql = '''INSERT INTO stock_opname (sku, product_name, price, original_stock, 
                                                opname_stock, final_stock, created_at, created_by)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
            
            difference_stock = int(edit_stock_opname_data.final_stock) - int(edit_stock_opname_data.original_stock)
            self.cursor.execute(sql, (edit_stock_opname_data.sku, edit_stock_opname_data.product_name, 
                                      edit_stock_opname_data.price,  edit_stock_opname_data.original_stock, 
                                      difference_stock, edit_stock_opname_data.final_stock,
                                      today, self.permission_manager.get_user_id()))
            

            # Update product stock
            sql = '''UPDATE products SET stock = ? WHERE sku = ?'''
            self.cursor.execute(sql, (edit_stock_opname_data.final_stock, edit_stock_opname_data.sku))


            # Update Stock Card
            stock_opname_id = self.cursor.lastrowid
            remarks = f'Correction Stock from {edit_stock_opname_data.original_stock} to {edit_stock_opname_data.final_stock} with Stock Opname Id: {stock_opname_id} by {self.permission_manager.get_username()}'
            sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                stock_out, running_balance, remarks) 
                     VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''
            self.cursor.execute(sql, (edit_stock_opname_data.sku, stock_opname_id, None, 
                                      None, edit_stock_opname_data.final_stock, remarks))


            # Insert Log
            new_data = {
                'sku': edit_stock_opname_data.sku,
                'product_name': edit_stock_opname_data.product_name,
                'price': edit_stock_opname_data.price,
                'original_stock': edit_stock_opname_data.original_stock,
                'opname_stock': difference_stock,
                'final_stock': edit_stock_opname_data.final_stock
            }

            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            
            self.cursor.execute(sql, (f'Stock Opname#{stock_opname_id}', remarks, 'C', 
                                        None,  json.dumps(new_data),today, self.permission_manager.get_user_id()))


            # Commit Transaction
            self.db.commit()
            return ResponseMessage.ok(
                message="Stock Opname created successfully!",
                data=edit_stock_opname_data
            )

        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to create stock opname {str(e)}")
        

    def get_stock_opname(self, search_text: str = None) -> List[StockOpnameModel]:
        if not self.permission_manager.has_permission(PERM_R_STOCK_OPNAME):
            return ResponseMessage.fail(message=ERR_PERM_R_STOCK_OPNAME)

        try:
            stock_opname_result = []
            if search_text:
                sql = '''SELECT sku, product_name, price, stock, unit
                            FROM products
                            WHERE sku LIKE ? OR product_name LIKE ? OR unit LIKE ?'''
                
                search_text = f'%{search_text}%'
                stock_opname_result = self.cursor.execute(sql, (search_text, search_text, search_text))
            else:

                sql = '''SELECT sku, product_name, price, stock, unit
                            FROM products'''
                stock_opname_result = self.cursor.execute(sql)
            
            stock_opname_list = [
                StockOpnameModel(
                    sku=row[0], product_name=row[1],
                    price=row[2], qty=row[3], unit=row[4]
                )
                for row in stock_opname_result
            ]

            # Commit Transaction
            self.db.commit()
            
            return ResponseMessage.ok(
                message="Stock Opname fetched successfully!",
                data=stock_opname_list
            )

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(
                message=f"Failed to fetch stock opname {str(e)}",
            )