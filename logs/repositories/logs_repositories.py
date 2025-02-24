from datetime import datetime
from connect_db import DatabaseConnection

from logs.models.logs_models import LogsModel
from response.response_message import ResponseMessage

class LogsRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        

    def get_logs(self, start_date: datetime, end_date: datetime, search_text: str = None):
        try:
            logs_result = []
            if search_text:
                sql = '''SELECT l.created_at, l.log_type, l.log_description, l.old_data, l.new_data, u.user_name
                            FROM logs l
                            JOIN users u ON l.created_by = u.user_id
                            WHERE l.created_at BETWEEN ? AND ? 
                                AND (log_type LIKE ? OR log_description LIKE ? OR old_data LIKE ? OR new_data LIKE ? OR u.user_name LIKE ?)'''
                
                search_text = f'%{search_text}%'
                logs_result = self.cursor.execute(sql, (start_date, end_date, search_text, search_text, search_text, search_text, search_text))
            else:

                sql = '''SELECT l.created_at, l.log_type, l.log_description, l.old_data, l.new_data, u.user_name
                            FROM logs l
                            JOIN users u ON l.created_by = u.user_id
                            WHERE l.created_at BETWEEN ? AND ?'''
                logs_result = self.cursor.execute(sql, (start_date, end_date))
            
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