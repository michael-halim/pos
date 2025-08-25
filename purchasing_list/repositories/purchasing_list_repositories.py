from connect_db import DatabaseConnection
from datetime import datetime
import json

from purchasing_list.models.purchasing_list_models import PurchasingListModel, DetailPurchasingModel

from generals.permission_manager import PermissionManager
from response.response_message import ResponseMessage

class PurchasingListRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()


    def get_purchasing_list(self, start_date: datetime, end_date: datetime, search_text: str = None):
        try:
            purchasing_result = []
            if search_text:
                sql = '''SELECT ph.created_at, ph.purchasing_id, s.supplier_name, ph.total_amount, ph.purchasing_remarks
                            FROM purchasing_history ph
                            LEFT JOIN suppliers s ON s.supplier_id = ph.supplier_id
                            WHERE ph.created_at BETWEEN ? AND ? 
                                AND (ph.purchasing_id LIKE ? OR ph.total_amount LIKE ? OR ph.purchasing_remarks LIKE ?)
                            ORDER BY ph.created_at DESC'''
                
                search_text = f'%{search_text}%'
                purchasing_result = self.cursor.execute(sql, (start_date, end_date, search_text, search_text, search_text, search_text))
            else:

                sql = '''SELECT ph.created_at, ph.purchasing_id, s.supplier_name, ph.total_amount, ph.purchasing_remarks 
                            FROM purchasing_history ph
                            LEFT JOIN suppliers s ON s.supplier_id = ph.supplier_id
                            WHERE ph.created_at BETWEEN ? AND ?
                            ORDER BY ph.created_at DESC'''
                purchasing_result = self.cursor.execute(sql, (start_date, end_date))
            
            purchasing_list = [
                PurchasingListModel(
                    created_at=row[0], purchasing_id=row[1],
                    supplier_name=row[2], total_amount=row[3], remarks=row[4]
                )
                for row in purchasing_result
            ]

            # If everything successful, commit the transaction
            self.db.commit()
            
            return ResponseMessage.ok(
                message="Purchasing list fetched successfully!",
                data=purchasing_list
            )

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(
                message=f"Failed to fetch purchasing list {str(e)}",
            )


    def get_detail_purchasing_by_id(self, purchasing_id: str):
        try:
            sql = '''SELECT dph.sku, p.product_name, dph.price, dph.qty, dph.unit, dph.discount_pct, dph.discount_rp, dph.subtotal
                    FROM detail_purchasing_history dph 
                    JOIN purchasing_history ph on ph.purchasing_id = dph.purchasing_id
                    JOIN products p ON p.sku = dph.sku
                    WHERE dph.purchasing_id = ?'''
            
            detail_purchasing_result = self.cursor.execute(sql, (purchasing_id,))
            
            # If everything successful, commit the transaction
            self.db.commit()

            detail_purchasing_list = [
                    DetailPurchasingModel(
                        sku=row[0], product_name=row[1], 
                    price=row[2], qty=row[3], unit=row[4], 
                    discount_rp=row[5], discount_pct=row[6], subtotal=row[7]
                )
                for row in detail_purchasing_result
            ]

            return ResponseMessage.ok(
                message="Purchasing detail fetched successfully!",
                data=detail_purchasing_list
            )
        
        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(
                message=f"Failed to fetch purchasing detail {str(e)}",
            )    
        

    def delete_purchasing_by_id(self, purchasing_id: str):
        try:
            self.cursor.execute('BEGIN TRANSACTION')


            # Get old purchasing data
            sql = '''SELECT supplier_id, invoice_date, invoice_number, invoice_expired_date, 
                                                total_amount, total_discount, purchasing_remarks 
                                        FROM purchasing_history 
                                        WHERE purchasing_id = ?
                                        LIMIT 1'''
            self.cursor.execute(sql, (purchasing_id,))
            purchasing_result = self.cursor.fetchone()

            old_data = {
                'purchasing_id': purchasing_id,
                'supplier_id': purchasing_result[0],
                'invoice_date': purchasing_result[1],
                'invoice_number': purchasing_result[2],
                'invoice_expired_date': purchasing_result[3],
                'total_amount': purchasing_result[4],
                'total_discount': purchasing_result[5],
                'purchasing_remarks': purchasing_result[6]
            }

            # Get old detail purchasing data
            sql = '''SELECT sku, unit, unit_value, qty, price, discount_rp, discount_pct, subtotal 
                    FROM detail_purchasing_history 
                    WHERE purchasing_id = ?'''
            
            self.cursor.execute(sql, (purchasing_id,))

            detail_purchasing_results = self.cursor.fetchall()

            old_detail_purchasing_data = []
            for detail in detail_purchasing_results:
                old_detail_purchasing_data.append({
                    'sku': detail[0],
                    'unit': detail[1],
                    'unit_value': detail[2],
                    'qty': detail[3],
                    'price': detail[4],
                    'discount_rp': detail[5],
                    'discount_pct': detail[6],
                    'subtotal': detail[7]
                })

            old_data['detail_purchasing'] = old_detail_purchasing_data


            # Delete the purchasing history
            sql = '''DELETE FROM purchasing_history WHERE purchasing_id = ?'''
            self.cursor.execute(sql, (purchasing_id,))

            # MUST TEST THIS, BECAUSE THE SAME WITH LINE 130 - 133
            # Get detail purchasing history
            sql = '''SELECT sku, unit, qty, unit_value FROM detail_purchasing_history WHERE purchasing_id = ?'''
            self.cursor.execute(sql, (purchasing_id,))
            detail_purchasing = self.cursor.fetchall()

            # Delete the detail purchasing history
            for dp in detail_purchasing:
                # Update product stock
                stock_affected: int = int(dp[2]) * int(dp[3])
                update_sql = 'UPDATE products SET stock = stock - ? WHERE sku = ?'
                self.cursor.execute(update_sql, (stock_affected, dp[0]))

                # Get updated stock value directly after update
                get_updated_stock_sql = 'SELECT stock FROM products WHERE sku = ?'
                self.cursor.execute(get_updated_stock_sql, (dp[0],))
                updated_stock = self.cursor.fetchone()[0]

                # Update Stock Card by Inserting Data to Stock Card Table
                remarks = f'Correction Stock from Delete Purchasing#{purchasing_id} by {self.permission_manager.get_username()}'
                stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''
                self.cursor.execute(stock_card_sql, (dp[0], purchasing_id, stock_affected, None, updated_stock, remarks))


            # Delete the detail purchasing history
            sql = '''DELETE FROM detail_purchasing_history WHERE purchasing_id = ?'''
            self.cursor.execute(sql, (purchasing_id,))


            # Insert Log    
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)''' 
            
            self.cursor.execute(sql, (f'Purchasing#{purchasing_id} deleted', f'Purchasing#{purchasing_id} deleted successfully!', 'D', 
                                        json.dumps(old_data), None, today, self.permission_manager.get_user_id()))
            

            # Commit Transactions
            self.db.commit()
            return ResponseMessage.ok(message="Purchasing deleted successfully!")
        
        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(
                message=f"Failed to delete purchasing {str(e)}",
            )   
