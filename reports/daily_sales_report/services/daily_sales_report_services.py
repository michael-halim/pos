from datetime import datetime

from reports.daily_sales_report.repositories.daily_sales_report_repositories import DailySalesReportRepository

from generals.permission_manager import PermissionManager
from generals.constants import PERM_R_DAILY_SALES_REPORT
from generals.messages import ERR_PERM_R_DAILY_SALES_REPORT
from response.response_message import ResponseMessage


class DailySalesReportService:
    def __init__(self):
        self.repository = DailySalesReportRepository()
        self.permission_manager = PermissionManager()


    def get_daily_sales_report(self, start_date: datetime, end_date: datetime):
        if not self.permission_manager.has_permission(PERM_R_DAILY_SALES_REPORT):
            return ResponseMessage.fail(message=ERR_PERM_R_DAILY_SALES_REPORT)

        return self.repository.get_daily_sales_report(start_date, end_date)
