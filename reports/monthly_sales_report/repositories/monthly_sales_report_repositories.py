from connect_db import DatabaseConnection
from datetime import datetime   

from reports.monthly_sales_report.models.monthly_sales_report_models import MonthlySalesReportModel

from response.response_message import ResponseMessage
from generals.permission_manager import PermissionManager
from generals.constants import PERM_R_MONTHLY_SALES_REPORT
from generals.messages import ERR_PERM_R_MONTHLY_SALES_REPORT


class MonthlySalesReportRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()


    def get_monthly_sales_report(self, start_date: datetime, end_date: datetime):   
        if not self.permission_manager.has_permission(PERM_R_MONTHLY_SALES_REPORT):
            return ResponseMessage.fail(message=ERR_PERM_R_MONTHLY_SALES_REPORT)

        try:
            sql = '''SELECT t.created_at, t.total_amount, t.payment_method, u.username
                        FROM transactions t
                        JOIN users u ON u.user_id = t.created_by
                        WHERE t.created_at BETWEEN ? AND ?'''
            
            monthly_sales_result = self.cursor.execute(sql, (start_date, end_date))
            monthly_sales_list = [
                MonthlySalesReportModel(
                    created_at=row[0], total_sales=row[1],
                    payment_method=row[2], created_by=row[3]
                )
                for row in monthly_sales_result
            ]

            # If everything successful, commit the transaction
            self.db.commit()

            return ResponseMessage.ok(
                message="Monthly sales report fetched successfully!",
                data=monthly_sales_list
            )

        except Exception as e:
            # If any error occurs, rollback all changes
            return ResponseMessage.fail(
                message=f"Failed to fetch monthly sales report {str(e)}",
            )