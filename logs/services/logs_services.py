from datetime import datetime

from logs.repositories.logs_repositories import LogsRepository
from generals.permission_manager import PermissionManager
from generals.constants import PERM_R_LOGS
from generals.messages import ERR_PERM_R_LOGS
from response.response_message import ResponseMessage

class LogsService:
    def __init__(self):
        self.repository = LogsRepository()
        self.permission_manager = PermissionManager()


    def get_logs(self, start_date: datetime, end_date: datetime, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_LOGS):
            return ResponseMessage.fail(message=ERR_PERM_R_LOGS)
        
        return self.repository.get_logs(start_date, end_date, search_text)

