from typing import List

# Import Models
from connect_db import DatabaseConnection
from datetime import datetime, timedelta

from transactions_list.models.transactions_list_models import TransactionListModel, DetailTransactionListModel
from transactions_list.models.response_message import ResponseMessage

class TransactionRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
    
    def get_transactions_list(self, start_date: datetime, end_date: datetime, search_text: str = None):
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
        try:
            sql = '''SELECT dt.sku, p.product_name, dt.price, dt.qty, dt.unit, dt.discount, dt.discount, dt.sub_total 
                        FROM detail_transactions dt
                        JOIN products p ON dt.sku = p.sku
                        WHERE dt.transaction_id = ?'''
            
            detail_transactions_result = self.cursor.execute(sql, (transaction_id,))
            
            # If everything successful, commit the transaction
            self.db.commit()

            detail_transactions_list = []
            detail_transactions_list = [
                    DetailTransactionListModel(
                        sku=row[0], product_name=row[1], 
                    price=row[2], qty=row[3], unit=row[4], 
                    discount_rp=row[5], discount_pct=row[6], subtotal=row[7]
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
