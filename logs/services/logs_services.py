from datetime import datetime
from ..repositories.logs_repositories import LogsRepository

class LogsService:
    def __init__(self):
        self.repository = LogsRepository()


    def get_logs(self, start_date: datetime, end_date: datetime, search_text: str = None):
        return self.repository.get_logs(start_date, end_date, search_text)

