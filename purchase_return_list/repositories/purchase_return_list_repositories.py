from connect_db import DatabaseConnection
from typing import List
from response.response_message import ResponseMessage
from purchase_return_list.models.purchase_return_list_models import PurchaseReturnListModel
from purchase_return.models.purchase_return_models import DetailPurchaseReturnModel
from generals.permission_manager import PermissionManager
from datetime import datetime


class PurchaseReturnListRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()
        

    def get_purchase_return_list(self, start_date: datetime, end_date: datetime, search_text: str = None):
        try:
            purchase_return_result = []
            if search_text:
                sql = '''SELECT pr.created_at, pr.purchase_return_id, s.supplier_name, pr.total_amount, pr.purchase_return_remarks
                            FROM purchase_return pr
                            LEFT JOIN suppliers s ON s.supplier_id = pr.supplier_id
                            WHERE pr.created_at BETWEEN ? AND ? 
                                AND (pr.purchase_return_id LIKE ? OR pr.total_amount LIKE ? OR pr.purchase_return_remarks LIKE ?)
                            ORDER BY pr.created_at DESC'''
                
                search_text = f'%{search_text}%'
                purchase_return_result = self.cursor.execute(sql, (start_date, end_date, search_text, search_text, search_text))
            else:

                sql = '''SELECT pr.created_at, pr.purchase_return_id, s.supplier_name, pr.total_amount, pr.purchase_return_remarks 
                            FROM purchase_return pr
                            LEFT JOIN suppliers s ON s.supplier_id = pr.supplier_id
                            WHERE pr.created_at BETWEEN ? AND ?
                            ORDER BY pr.created_at DESC'''
                purchase_return_result = self.cursor.execute(sql, (start_date, end_date))
            
            purchase_return_list = [
                PurchaseReturnListModel(
                    created_at=row[0], purchase_return_id=row[1],
                    supplier_name=row[2], total_amount=row[3], remarks=row[4]
                )
                for row in purchase_return_result
            ]

            # If everything successful, commit the transaction
            self.db.commit()
            
            return ResponseMessage.ok(
                message="Purchase return list fetched successfully!",
                data=purchase_return_list
            )

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(
                message=f"Failed to fetch purchase return list {str(e)}",
            )
        

    def get_detail_purchase_return_by_id(self, purchase_return_id: str):
        try:
            sql = '''SELECT dpr.sku, p.product_name, dpr.price, dpr.qty, dpr.unit, dpr.subtotal
                    FROM detail_purchase_return dpr 
                    JOIN purchase_return pr on pr.purchase_return_id = dpr.purchase_return_id
                    JOIN products p ON p.sku = dpr.sku
                    WHERE dpr.purchase_return_id = ?'''
            
            detail_purchase_return_result = self.cursor.execute(sql, (purchase_return_id,))
            
            # If everything successful, commit the transaction
            self.db.commit()

            detail_purchase_return_list = [
                    DetailPurchaseReturnModel(
                        sku=row[0], product_name=row[1], 
                    price=row[2], qty=row[3], unit=row[4], 
                    discount_rp=row[5], discount_pct=row[6], subtotal=row[7]
                )
                for row in detail_purchase_return_result
            ]

            return ResponseMessage.ok(
                message="Purchase return detail fetched successfully!",
                data=detail_purchase_return_list
            )
        
        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(
                message=f"Failed to fetch purchase return detail {str(e)}",
            )  
        
    
    def delete_purchase_return_by_id(self, purchase_return_id: str):
        try:
            self.cursor.execute('BEGIN TRANSACTION')

            # Get old purchase return data
            sql = '''SELECT supplier_id, purchase_return_date, total_amount, 
                            purchase_return_remarks, created_at, created_by, updated_at, updated_by
                    FROM purchase_return 
                    WHERE purchase_return_id = ?
                    LIMIT 1'''
            
            self.cursor.execute(sql, (purchase_return_id,))
            purchase_return_result = self.cursor.fetchone()

            old_data = {
                'purchase_return_id': purchase_return_id,
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
            
            self.cursor.execute(sql, (purchase_return_id,))

            detail_purchase_return_results = self.cursor.fetchall()

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


            # Delete the transaction
            sql = '''DELETE FROM purchasing_history WHERE purchasing_id = ?'''
            self.cursor.execute(sql, (purchasing_id,))

            # Get detail transactions
            sql = '''SELECT sku, unit, qty, unit_value FROM detail_purchasing_history WHERE purchasing_id = ?'''
            self.cursor.execute(sql, (purchasing_id,))
            detail_purchasing = self.cursor.fetchall()

            # Delete the detail transactions
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
