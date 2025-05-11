from connect_db import DatabaseConnection
from datetime import datetime

from logs.models.logs_models import LogsModel

from response.response_message import ResponseMessage
from generals.constants import PERM_R_LOGS
from generals.messages import ERR_PERM_R_LOGS
from generals.permission_manager import PermissionManager


class LogsRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()


    def get_logs(self, start_date: datetime, end_date: datetime, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_LOGS):
            return ResponseMessage.fail(message=ERR_PERM_R_LOGS)
        
        try:
            logs_result = []
            if search_text:
                sql = '''SELECT l.created_at, l.log_type, l.log_description, l.old_data, l.new_data, u.username
                            FROM logs l
                            JOIN users u ON l.created_by = u.user_id
                            WHERE l.created_at BETWEEN ? AND ? 
                                AND (log_type LIKE ? OR log_description LIKE ? OR old_data LIKE ? OR new_data LIKE ? OR u.username LIKE ?)
                            ORDER BY l.created_at DESC'''
                
                
                search_text = f'%{search_text}%'
                logs_result = self.cursor.execute(sql, (start_date, end_date, search_text, search_text, search_text, search_text, search_text))
            else:

                sql = '''SELECT l.created_at, l.log_type, l.log_description, l.old_data, l.new_data, u.username
                            FROM logs l
                            JOIN users u ON l.created_by = u.user_id
                            WHERE l.created_at BETWEEN ? AND ?
                            ORDER BY l.created_at DESC'''
                
                logs_result = self.cursor.execute(sql, (start_date, end_date,))

            logs_list = [
                LogsModel(
                    created_at=row[0], log_type=row[1],
                    log_description=row[2], old_data=row[3],
                    new_data=row[4], created_by=row[5]
                )
                for row in logs_result
            ]

            # Commit Transaction
            self.db.commit()
            
            return ResponseMessage.ok(
                message="Logs fetched successfully!",
                data=logs_list
            )

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(
                message=f"Failed to fetch logs {str(e)}",
            )