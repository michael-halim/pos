from typing import List, Optional
from datetime import datetime
from reports.sales_per_item_report.repositories.sales_per_item_report_repositories import SalesPerItemReportRepository
from generals.constants import PERM_C_TRANSACTIONS
from generals.permission_manager import PermissionManager


class SalesPerItemReportService:
    def __init__(self):
        self.repository = SalesPerItemReportRepository()
        self.permission_manager = PermissionManager()

    def get_product_by_sku(self, sku: str):
        return self.repository.get_product_by_sku(sku)
    

    def get_sales_per_item_report(self, start_date: datetime, end_date: datetime, sku: str, category_id: int | None = None):
        return self.repository.get_sales_per_item_report(start_date, end_date, sku, category_id)

