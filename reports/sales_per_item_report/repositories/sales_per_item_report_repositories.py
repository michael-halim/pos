from connect_db import DatabaseConnection
from datetime import datetime

from reports.sales_per_item_report.models.sales_per_item_report_models import SalesPerItemReportModel, ProductModel

from generals.permission_manager import PermissionManager
from response.response_message import ResponseMessage


class SalesPerItemReportRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()
    

    def get_sales_per_item_report(self, start_date: datetime, end_date: datetime, sku: str, category_id: int | None = None):
        try:
            sales_per_item_report = []
            if category_id is None:
                sql = '''SELECT t.transaction_id, t.created_at, u.username, dt.qty, dt.price, dt.unit, dt.unit_value, dt.discount_pct, 
                                dt.discount_rp_per_item, dt.discount_rp, dt.sub_total
                        FROM detail_transactions dt
                        JOIN transactions t ON t.transaction_id = dt.transaction_id
                        JOIN products p ON p.sku = dt.sku
                        JOIN users u ON u.user_id = t.created_by
                        WHERE dt.sku = ? AND t.created_at >= ? AND t.created_at <= ?
                        ORDER BY t.created_at ASC, dt.unit_value DESC'''
                sales_per_item_report = self.cursor.execute(sql, (sku, start_date, end_date))

            else:
                sql = '''SELECT t.transaction_id, t.created_at, u.username, dt.qty, dt.price, dt.unit, dt.unit_value, dt.discount_pct, 
                                dt.discount_rp_per_item, dt.discount_rp, dt.sub_total
                        FROM detail_transactions dt
                        JOIN transactions t ON t.transaction_id = dt.transaction_id
                        JOIN products p ON p.sku = dt.sku
                        JOIN users u ON u.user_id = t.created_by
                        WHERE dt.sku = ? AND t.created_at >= ? AND t.created_at <= ? and created_by = ?'''
                
                sales_per_item_report = self.cursor.execute(sql, (sku, start_date, end_date, category_id))  


            sales_per_item_report = [
                SalesPerItemReportModel(
                    transaction_id=row[0], created_at=row[1], username=row[2],
                    qty=row[3], price=row[4], unit=row[5], unit_value=row[6],
                    discount_pct=row[7], discount_rp_per_item=row[8], discount_rp=row[9],
                    sub_total=row[10]
                )
                for row in sales_per_item_report
            ]

            # If everything successful, commit the transaction
            self.db.commit()
            
            return ResponseMessage.ok(
                message="Sales per item report fetched successfully!",
                data=sales_per_item_report
            )
            
        except Exception as e:
            return ResponseMessage.fail(
                message=f"Failed to fetch sales per item report {str(e)}",
            )


    def get_product_by_sku(self, sku: str):
        try:
            sql = 'SELECT product_name, price, unit, stock FROM products WHERE sku = ?'
            self.cursor.execute(sql, (sku,))

            if self.cursor.rowcount == 0:
                return {
                    'success': True,
                    'message': f"Product with sku {sku} not found",
                    'data': None
                }

            result = self.cursor.fetchone()
            return {
                'success': True,
                'message': "Success",
                'data': ProductModel(product_name=result[0], price=result[1], unit=result[2], stock=result[3])
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"Error: {str(e)}",
                'data': None
            }