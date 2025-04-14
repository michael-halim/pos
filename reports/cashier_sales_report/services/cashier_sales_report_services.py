from datetime import datetime   


from reports.cashier_sales_report.repositories.cashier_sales_report_repositories import CashierSalesReportRepository
from generals.permission_manager import PermissionManager
from generals.constants import PERM_R_CASHIER_SALES_REPORT
from generals.messages import ERR_PERM_R_CASHIER_SALES_REPORT
from response.response_message import ResponseMessage


class CashierSalesReportService:
    def __init__(self):
        self.repository = CashierSalesReportRepository()
        self.permission_manager = PermissionManager()
        

    def get_transactions_list(self, start_date: datetime, end_date: datetime, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_CASHIER_SALES_REPORT):
            return ResponseMessage.fail(message=ERR_PERM_R_CASHIER_SALES_REPORT)
        
        return self.repository.get_transactions_list(start_date, end_date, search_text)
    

    def get_detail_transactions_list(self, transaction_id: str):
        if not self.permission_manager.has_permission(PERM_R_CASHIER_SALES_REPORT):
            return ResponseMessage.fail(message=ERR_PERM_R_CASHIER_SALES_REPORT)
        
        return self.repository.get_detail_transactions_list(transaction_id)