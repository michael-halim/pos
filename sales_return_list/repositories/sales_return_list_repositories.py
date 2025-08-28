from connect_db import DatabaseConnection
import json
from response.response_message import ResponseMessage
from sales_return_list.models.sales_return_list_models import SalesReturnListModel, DetailSalesReturnListModel
from generals.permission_manager import PermissionManager
from datetime import datetime

class SalesReturnListRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()
        

    def get_sales_return_list(self, start_date: datetime, end_date: datetime, search_text: str = None):
        try:
            sales_return_result = []
            if search_text:
                sql = '''SELECT sr.created_at, sr.sales_return_id, c.customer_name, sr.total_amount, sr.sales_return_remarks
                            FROM sales_return sr
                            LEFT JOIN customers c ON c.customer_id = sr.customer_id
                            WHERE sr.created_at BETWEEN ? AND ? 
                                AND (sr.sales_return_id LIKE ? OR sr.total_amount LIKE ? OR sr.sales_return_remarks LIKE ?)
                            ORDER BY sr.created_at DESC'''
                
                search_text = f'%{search_text}%'
                sales_return_result = self.cursor.execute(sql, (start_date, end_date, search_text, search_text, search_text))
            else:

                sql = '''SELECT sr.created_at, sr.sales_return_id, c.customer_name, sr.total_amount, sr.sales_return_remarks 
                            FROM sales_return sr
                            LEFT JOIN customers c ON c.customer_id = sr.customer_id
                            WHERE sr.created_at BETWEEN ? AND ?
                            ORDER BY sr.created_at DESC'''
                sales_return_result = self.cursor.execute(sql, (start_date, end_date))
            
            sales_return_list = [
                SalesReturnListModel(
                    created_at=row[0], sales_return_id=row[1],
                    customer_name=row[2], total_amount=row[3], remarks=row[4]
                )
                for row in sales_return_result
            ]

            # If everything successful, commit the transaction
            self.db.commit()
            
            return ResponseMessage.ok(
                message="Sales return list fetched successfully!",
                data=sales_return_list
            )

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(
                message=f"Failed to fetch sales return list {str(e)}",
            )
        

    def get_detail_sales_return_by_id(self, sales_return_id: str):
        try:
            sql = '''SELECT dsr.sku, p.product_name, dsr.price, dsr.qty, dsr.unit, dsr.subtotal
                    FROM detail_sales_return dsr
                    JOIN products p ON p.sku = dsr.sku
                    WHERE dsr.sales_return_id = ? '''
            
            detail_sales_return_result = self.cursor.execute(sql, (sales_return_id,))
            
            detail_sales_return_list = [
                    DetailSalesReturnListModel(
                        sku=row[0], product_name=row[1], price=row[2], 
                        qty=row[3], unit=row[4], subtotal=row[5]
                )
                for row in detail_sales_return_result
            ]

            return ResponseMessage.ok(
                message="Sales return detail fetched successfully!",
                data=detail_sales_return_list
            )
        
        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(
                message=f"Failed to fetch sales return detail {str(e)}",
            )
        
    
    def delete_sales_return_by_id(self, sales_return_id: str):
        try:
            self.cursor.execute('BEGIN TRANSACTION')

            # Get old sales return data
            sql = '''SELECT customer_id, sales_return_date, total_amount, 
                            sales_return_remarks, created_at, created_by, updated_at, updated_by
                    FROM sales_return 
                    WHERE sales_return_id = ?
                    LIMIT 1'''
            
            self.cursor.execute(sql, (sales_return_id,))
            sales_return_result = self.cursor.fetchone()

            old_data = {
                'sales_return_id': sales_return_id,
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
            
            self.cursor.execute(sql, (sales_return_id,))

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


            # Delete the transaction
            sql = '''DELETE FROM sales_return WHERE sales_return_id = ?'''
            self.cursor.execute(sql, (sales_return_id,))

            # Delete the detail sales return
            for ds in detail_sales_return_results:
                # Update product stock
                stock_affected: int = int(ds[2]) * int(ds[3])
                update_sql = 'UPDATE products SET stock = stock - ? WHERE sku = ?'
                self.cursor.execute(update_sql, (stock_affected, ds[0]))

                # Get updated stock value directly after update
                get_updated_stock_sql = 'SELECT stock FROM products WHERE sku = ?'
                self.cursor.execute(get_updated_stock_sql, (ds[0],))
                updated_stock = self.cursor.fetchone()[0]

                # Update Stock Card by Inserting Data to Stock Card Table
                remarks = f'Correction Stock from Delete Sales Return#{sales_return_id} by {self.permission_manager.get_username()}'
                stock_card_sql = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, 
                                                            stock_out, running_balance, remarks) 
                                    VALUES (?, CURRENT_DATE, CURRENT_TIME, ?, ?, ?, ?, ?)'''
                self.cursor.execute(stock_card_sql, (ds[0], sales_return_id, None, stock_affected, updated_stock, remarks))


            sql = '''DELETE FROM detail_sales_return WHERE sales_return_id = ?'''
            self.cursor.execute(sql, (sales_return_id,))


            # Insert Log    
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)''' 
            
            self.cursor.execute(sql, (f'Sales Return#{sales_return_id} deleted', f'Sales Return#{sales_return_id} deleted successfully!', 'D', 
                                        json.dumps(old_data), None, today, self.permission_manager.get_user_id()))
            

            # Commit Transactions
            self.db.commit()
            return ResponseMessage.ok(message="Sales return deleted successfully!")
        
        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(
                message=f"Failed to delete sales return {str(e)}",
            )   
