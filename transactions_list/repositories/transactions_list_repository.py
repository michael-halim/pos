from connect_db import DatabaseConnection
from datetime import datetime
import json

from transactions_list.models.transactions_list_models import TransactionListModel, DetailTransactionListModel
from generals.permission_manager import PermissionManager

from response.response_message import ResponseMessage
from generals.permission_manager import PermissionManager
from generals.constants import PERM_R_TRANSACTIONS, PERM_D_TRANSACTIONS
from generals.messages import ERR_PERM_R_TRANSACTIONS, ERR_PERM_D_TRANSACTIONS


class TransactionRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()
    

    def get_transactions_list(self, start_date: datetime, end_date: datetime, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_R_TRANSACTIONS)
        
        try:
            transactions_result = []
            if search_text:
                sql = '''SELECT created_at, transaction_id, payment_rp, payment_method, payment_remarks 
                            FROM transactions 
                            WHERE created_at BETWEEN ? AND ? 
                                AND (transaction_id LIKE ? OR payment_rp LIKE ? OR payment_method LIKE ? OR payment_remarks LIKE ?)'''
                
                search_text = f'%{search_text}%'
                transactions_result = self.cursor.execute(sql, (start_date, end_date, search_text, search_text, search_text, search_text))
            else:

                sql = '''SELECT created_at, transaction_id, payment_rp, payment_method, payment_remarks 
                            FROM transactions 
                            WHERE created_at BETWEEN ? AND ?'''
                transactions_result = self.cursor.execute(sql, (start_date, end_date))
            
            transactions_list = [
                TransactionListModel(
                    created_at=row[0], transaction_id=row[1],
                    payment_rp=row[2], payment_method=row[3],
                    payment_remarks=row[4]
                )
                for row in transactions_result
            ]

            # If everything successful, commit the transaction
            self.db.commit()
            
            return ResponseMessage.ok(
                message="Transaction list fetched successfully!",
                data=transactions_list
            )

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(
                message=f"Failed to fetch transaction list {str(e)}",
            )
        
        
    def get_detail_transactions_list(self, transaction_id: str):
        if not self.permission_manager.has_permission(PERM_R_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_R_TRANSACTIONS)
        
        try:
            sql = '''SELECT dt.sku, p.product_name, dt.price, dt.qty, dt.unit, dt.discount_rp, 
                            dt.discount_rp_per_item, dt.discount_pct, dt.sub_total 
                        FROM detail_transactions dt
                        JOIN products p ON dt.sku = p.sku
                        WHERE dt.transaction_id = ?'''
            
            detail_transactions_result = self.cursor.execute(sql, (transaction_id,))
            
            # If everything successful, commit the transaction
            self.db.commit()

            detail_transactions_list = []
            detail_transactions_list = [
                    DetailTransactionListModel(sku=row[0], product_name=row[1], price=row[2], 
                            qty=row[3], unit=row[4], discount_rp=row[5], 
                            discount_rp_per_item=row[6], discount_pct=row[7], subtotal=row[8]
                    )
                for row in detail_transactions_result
            ]

            return ResponseMessage.ok(
                message="Transaction detail fetched successfully!",
                data=detail_transactions_list
            )
        
        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(
                message=f"Failed to fetch transaction detail {str(e)}",
            )


    def delete_transactions_by_id(self, transaction_id: str):
        if not self.permission_manager.has_permission(PERM_D_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_D_TRANSACTIONS)
        
        try:
            self.cursor.execute('BEGIN TRANSACTION')
            
            # Get old transaction data
            sql = '''SELECT transaction_id, customer_id, total_amount, payment_method, payment_rp, payment_change, 
                            discount_amount, tax_pct, tax_amount, payment_remarks 
                    FROM transactions 
                    WHERE transaction_id = ?
                    LIMIT 1'''
            self.cursor.execute(sql, (transaction_id,))
            result = self.cursor.fetchone()

            # Get old detail transactions data
            sql = '''SELECT sku, unit, unit_value, qty, price, discount_rp, discount_rp_per_item, discount_pct, subtotal 
                    FROM detail_transactions 
                    WHERE transaction_id = ?'''
            self.cursor.execute(sql, (transaction_id,))
            detail_result = self.cursor.fetchall()

            old_data_detail_transactions = []
            for detail in detail_result:
                old_data_detail_transactions.append({
                    'sku': detail[0],
                    'unit': detail[1],
                    'unit_value': detail[2],
                    'qty': detail[3],
                    'price': detail[4],
                    'discount_rp': detail[5],
                    'discount_rp_per_item': detail[6],
                    'discount_pct': detail[7],
                    'subtotal': detail[8]
                })

            old_data = {
                'transaction_id': result[0],
                'customer_id': result[1],
                'total_amount': result[2],
                'payment_method': result[3],
                'payment_rp': result[4],
                'payment_change': result[5],
                'discount_amount': result[6],
                'tax_pct': result[7],
                'tax_amount': result[8],
                'payment_remarks': result[9],
                'detail_transactions': old_data_detail_transactions
            }


            # Delete the transaction
            sql = '''DELETE FROM transactions WHERE transaction_id = ?'''
            self.cursor.execute(sql, (transaction_id,))

            # Get detail transactions
            sql = '''SELECT sku, unit, qty, unit_value FROM detail_transactions WHERE transaction_id = ?'''
            self.cursor.execute(sql, (transaction_id,))
            detail_transactions = self.cursor.fetchall()


            # Delete the detail transactions
            for dt in detail_transactions:
                # Update product stock
                stock_affected: int = int(dt[2]) * int(dt[3])
                update_sql = 'UPDATE products SET stock = stock + ? WHERE sku = ?'
                self.cursor.execute(update_sql, (stock_affected, dt[0]))

                # Get updated stock value directly after update
                get_updated_stock_sql = 'SELECT stock FROM products WHERE sku = ?'
                self.cursor.execute(get_updated_stock_sql, (dt[0],))
                updated_stock = self.cursor.fetchone()[0]

                # Update Stock Card by Inserting Data to Stock Card Table
                remarks = f'Correction Stock from Delete Transaction#{transaction_id} by {self.permission_manager.get_username()}'
                stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''
                self.cursor.execute(stock_card_sql, (dt[0], transaction_id, stock_affected, None, updated_stock, remarks))


            sql = '''DELETE FROM detail_transactions WHERE transaction_id = ?'''
            self.cursor.execute(sql, (transaction_id,))


            # Insert Log
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
           
            self.cursor.execute(sql, (f'Transaction#{transaction_id} deleted', f'Transaction#{transaction_id} deleted successfully!', 'D', 
                                        json.dumps(old_data), None, today, self.permission_manager.get_user_id()))
            
            # Commit the transaction
            self.db.commit()
            return ResponseMessage.ok(message="Transaction deleted successfully!")
        
        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(
                message=f"Failed to delete transaction {str(e)}",
            )   
