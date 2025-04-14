from connect_db import DatabaseConnection
from typing import List
from response.response_message import ResponseMessage
from reports.profit_and_loss_report.models.profit_and_loss_report_models import ProfitAndLossReportModel

class ProfitAndLossReportRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        
