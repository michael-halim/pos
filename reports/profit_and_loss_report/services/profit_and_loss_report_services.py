from typing import List, Optional
from reports.profit_and_loss_report.repositories.profit_and_loss_report_repositories import ProfitAndLossReportRepository

class ProfitAndLossReportService:
    def __init__(self):
        self.repository = ProfitAndLossReportRepository()
