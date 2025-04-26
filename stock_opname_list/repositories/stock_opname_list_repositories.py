from datetime import datetime
from connect_db import DatabaseConnection
import json

from stock_opname_list.models.stock_opname_list_models import StockOpnameListModel

from response.response_message import ResponseMessage
from generals.constants import PERM_R_STOCK_OPNAME, PERM_D_STOCK_OPNAME
from generals.messages import ERR_PERM_R_STOCK_OPNAME, ERR_PERM_D_STOCK_OPNAME
from generals.permission_manager import PermissionManager


class StockOpnameListRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()


    def get_stock_opname_list(self, start_date: datetime, end_date: datetime, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_STOCK_OPNAME):
            return ResponseMessage.fail(message=ERR_PERM_R_STOCK_OPNAME)
        
        try:
            stock_opname_result = []
            if search_text:
                sql = '''SELECT stock_opname_id, created_at, sku, product_name, price, original_stock, opname_stock, final_stock 
                            FROM stock_opname 
                            WHERE created_at BETWEEN ? AND ? 
                                AND (sku LIKE ? OR product_name LIKE ?)'''
                
                search_text = f'%{search_text}%'
                stock_opname_result = self.cursor.execute(sql, (start_date, end_date, search_text, search_text))
            else:

                sql = '''SELECT stock_opname_id, created_at, sku, product_name, price, original_stock, opname_stock, final_stock 
                            FROM stock_opname 
                            WHERE created_at BETWEEN ? AND ?'''
                stock_opname_result = self.cursor.execute(sql, (start_date, end_date))
            
            stock_opname_list = [
                StockOpnameListModel(
                    stock_opname_id=row[0], created_at=row[1], sku=row[2], product_name=row[3], 
                    price=row[4], original_stock=row[5], opname_stock=row[6], final_stock=row[7]
                )
                for row in stock_opname_result
            ]

            # If everything successful, commit the transaction
            self.db.commit()
            
            return ResponseMessage.ok(
                message="Stock opname list fetched successfully!",
                data=stock_opname_list
            )

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(
                message=f"Failed to fetch stock opname list {str(e)}",
            )
        

    def delete_stock_opname_by_id(self, stock_opname_id: str):
        if not self.permission_manager.has_permission(PERM_D_STOCK_OPNAME):
            return ResponseMessage.fail(message=ERR_PERM_D_STOCK_OPNAME)
        
        try:
            self.cursor.execute('BEGIN TRANSACTION')
                
            # Get old stock opname data
            sql = '''SELECT sku, product_name, price, original_stock, opname_stock, final_stock, created_at, created_by
                    FROM stock_opname 
                    WHERE stock_opname_id = ?
                    LIMIT 1'''
            
            self.cursor.execute(sql, (stock_opname_id,))
            stock_opname_result = self.cursor.fetchone()
            sku = stock_opname_result[0]
            product_name = stock_opname_result[1]
            price = stock_opname_result[2]
            original_stock = stock_opname_result[3]
            opname_stock = stock_opname_result[4]
            final_stock = stock_opname_result[5]
            created_at = stock_opname_result[6]
            created_by = stock_opname_result[7]

            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            old_data = {
                'stock_opname_id': stock_opname_id, 'sku': sku, 'product_name': product_name,
                'price': price, 'original_stock': original_stock, 'opname_stock': opname_stock,
                'final_stock': final_stock, 'created_at': created_at, 'created_by': created_by
            }

            # Delete the stock opname
            sql = '''DELETE FROM stock_opname WHERE stock_opname_id = ?'''
            self.cursor.execute(sql, (stock_opname_id,))


            # Insert Stock Card
            remarks = f'Correction Stock Revert from {final_stock} back to {original_stock} with Stock Opname Id: {stock_opname_id} by {self.permission_manager.get_username()}'
            sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                stock_out, running_balance, remarks) 
                     VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''
            
            self.cursor.execute(sql, (sku, stock_opname_id, None, None, original_stock, remarks))


            # Insert Log
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
           
            self.cursor.execute(sql, (f'Stock Opname#{stock_opname_id} deleted', remarks, 'D', 
                                        json.dumps(old_data), None, today, self.permission_manager.get_user_id()))
            
            
            # Commit the transaction
            self.db.commit()
            return ResponseMessage.ok(message="Transaction deleted successfully!")
        
        
        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(
                message=f"Failed to delete transaction {str(e)}",
            )   


