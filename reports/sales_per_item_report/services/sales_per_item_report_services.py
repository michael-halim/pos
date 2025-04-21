from datetime import datetime

from reports.sales_per_item_report.repositories.sales_per_item_report_repositories import SalesPerItemReportRepository

from generals.constants import PERM_R_SALES_PER_ITEM_REPORT
from generals.messages import ERR_PERM_R_SALES_PER_ITEM_REPORT
from generals.permission_manager import PermissionManager
from response.response_message import ResponseMessage


class SalesPerItemReportService:
    def __init__(self):
        self.repository = SalesPerItemReportRepository()
        self.permission_manager = PermissionManager()

    def get_product_by_sku(self, sku: str):
        if not self.permission_manager.has_permission(PERM_R_SALES_PER_ITEM_REPORT):
            return ResponseMessage.fail(message=ERR_PERM_R_SALES_PER_ITEM_REPORT)
        
        return self.repository.get_product_by_sku(sku)
    

    def get_sales_per_item_report(self, start_date: datetime, end_date: datetime, sku: str, category_id: int | None = None):
        if not self.permission_manager.has_permission(PERM_R_SALES_PER_ITEM_REPORT):
            return ResponseMessage.fail(message=ERR_PERM_R_SALES_PER_ITEM_REPORT)
        
        return self.repository.get_sales_per_item_report(start_date, end_date, sku, category_id)

