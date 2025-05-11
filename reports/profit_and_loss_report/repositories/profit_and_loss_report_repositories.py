from connect_db import DatabaseConnection

from reports.profit_and_loss_report.models.profit_and_loss_report_models import ProfitAndLossReportModel

from response.response_message import ResponseMessage
from generals.permission_manager import PermissionManager
from generals.constants import PERM_R_PROFIT_AND_LOSS_REPORT
from generals.messages import ERR_PERM_R_PROFIT_AND_LOSS_REPORT


class ProfitAndLossReportRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()


    def get_profit_and_loss_report(self, year: str):
        if not self.permission_manager.has_permission(PERM_R_PROFIT_AND_LOSS_REPORT):
            return ResponseMessage.fail(message=ERR_PERM_R_PROFIT_AND_LOSS_REPORT)

        try:
            sql = '''WITH all_months AS (
                        SELECT 1 AS month UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL
                        SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL
                        SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL
                        SELECT 10 UNION ALL SELECT 11 UNION ALL SELECT 12
                    ),
                    monthly_data AS (
                        SELECT 
                            CAST(strftime('%m', created_at) AS INTEGER) AS month_num,
                            SUM(total_amount) AS revenue,
                            SUM(total_net_profit) AS profit
                        FROM transactions
                        WHERE strftime('%Y', created_at) = ?
                        GROUP BY month_num
                    ),
                    data_with_accumulation AS (
                        SELECT 
                            am.month AS month,
                            COALESCE(md.revenue, 0) AS monthly_revenue,
                            COALESCE(md.profit, 0) AS monthly_profit,
                            SUM(COALESCE(md.revenue, 0)) OVER (ORDER BY am.month) AS accumulated_revenue,
                            SUM(COALESCE(md.profit, 0)) OVER (ORDER BY am.month) AS accumulated_profit
                        FROM all_months am
                        LEFT JOIN monthly_data md ON am.month = md.month_num
                    )

                    SELECT 
                        month,
                        monthly_revenue AS revenue,
                        accumulated_revenue,
                        monthly_profit AS profit,
                        accumulated_profit
                    FROM data_with_accumulation
                    ORDER BY month;'''
                                
            profit_and_loss_result = self.cursor.execute(sql, (year,))
            profit_and_loss_list = [
                ProfitAndLossReportModel(
                   period=row[0], revenue=row[1],
                   accumulated_revenue=row[2], profit=row[3],
                   accumulated_profit=row[4]
                )
                for row in profit_and_loss_result
            ]

            # If everything successful, commit the transaction
            self.db.commit()

            return ResponseMessage.ok(
                message="Profit and loss report fetched successfully!",
                data=profit_and_loss_list
            )

        except Exception as e:
            # If any error occurs, rollback all changes
            return ResponseMessage.fail(
                message=f"Failed to fetch profit and loss report {str(e)}",
            )
