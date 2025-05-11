from reports.profit_and_loss_report.repositories.profit_and_loss_report_repositories import ProfitAndLossReportRepository

from generals.permission_manager import PermissionManager
from generals.constants import PERM_R_PROFIT_AND_LOSS_REPORT
from generals.messages import ERR_PERM_R_PROFIT_AND_LOSS_REPORT
from response.response_message import ResponseMessage


class ProfitAndLossReportService:
    def __init__(self):
        self.repository = ProfitAndLossReportRepository()
        self.permission_manager = PermissionManager()


    def get_profit_and_loss_report(self, year: str):
        if not self.permission_manager.has_permission(PERM_R_PROFIT_AND_LOSS_REPORT):
            return ResponseMessage.fail(message=ERR_PERM_R_PROFIT_AND_LOSS_REPORT)
        
        return self.repository.get_profit_and_loss_report(year)
