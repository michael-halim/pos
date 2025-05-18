from PyQt6.QtWidgets import QWidget, QFileDialog

import os
import sys
from datetime import datetime
import shutil
import sqlite3

from generals.message_box import POSMessageBox
from generals.constants import (
    PERM_B_DATABASE, PERM_R_DATABASE,
) 
from generals.messages import (
    ERR_PERM_B_DATABASE, ERR_PERM_R_DATABASE,
    PERM_DENIED
)
from generals.permission_manager import PermissionManager


def get_application_path():
    """Get the correct application path for both development and installed versions"""
    if getattr(sys, 'frozen', False):
        # Running as installed application
        return os.path.dirname(sys.executable)
    else:
        # Running in development
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class BackupRestoreDatabase(QWidget):
    def __init__(self):
        super().__init__()

        self.permission_manager = PermissionManager()

        # Get the correct base path
        base_path = get_application_path()
        self.db_path = os.path.join(base_path, 'data', 'pos.db')
        self.backup_dir = os.path.join(base_path, 'backups')
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)


    def export_database(self):
        """Export/backup the current database, allowing user to choose location"""
        if not self.permission_manager.has_permission(PERM_B_DATABASE):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_B_DATABASE)
            return

        try:
            # Generate default filename with timestamp
            timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
            default_filename = f"backup_{timestamp}.db"

            # Show file dialog to choose where to save the backup
            backup_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Database Backup",
                os.path.join(self.backup_dir, default_filename),
                "SQLite Database (*.db)"
            )

            if not backup_path:
                return  # User cancelled

            # Create a copy of the database file
            if not os.path.exists(self.db_path):
                POSMessageBox.error(self, title="Error", message="Source DB does not exist!")
                return

            if not os.path.exists(os.path.dirname(backup_path)):
                POSMessageBox.error(self, title="Error", message="Backup directory does not exist!")
                return

            shutil.copy2(self.db_path, backup_path)

            POSMessageBox.info(
                self,
                title="Success",
                message=f"Database backed up successfully to {backup_path}"
            )

        except Exception as e:
            POSMessageBox.error(
                self,
                title="Error",
                message=f"Failed to backup database: {str(e)}"
            )


    def import_database(self):
        """Import/restore database from backup"""
        if not self.permission_manager.has_permission(PERM_R_DATABASE):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_R_DATABASE)
            return

        try:
            # Show file dialog to select backup file
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Database Backup",
                self.backup_dir,
                "SQLite Database (*.db)"
            )
            
            if not file_path:
                return
            
            # Verify backup file exists
            if not os.path.exists(file_path):
                POSMessageBox.error(self, title="Error", message="Backup file does not exist")
                return

            # Verify backup file is valid SQLite database
            try:
                conn = sqlite3.connect(file_path)
                conn.close()
            except sqlite3.Error:
                POSMessageBox.error(self, title="Error", message="Invalid SQLite database file")
                return

            # Confirm restore
            confirm = POSMessageBox.confirm(
                self,
                title="Confirm Restore",
                message="This will replace the current database. Are you sure?",
            )
            
            if confirm:
                # Create backup of current database before importing
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                current_backup = os.path.join(
                    self.backup_dir, 
                    f"pre_restore_backup_{timestamp}.db"
                )
                
                # Ensure the data directory exists
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

                try:
                    # Only backup if the current database exists
                    if os.path.exists(self.db_path):
                        shutil.copy2(self.db_path, current_backup)
                    
                    # Copy the new database
                    shutil.copy2(file_path, self.db_path)

                    POSMessageBox.info(
                        self,
                        title="Success",
                        message="Database restored successfully. Please restart the application manually."
                    )

                except Exception as e:
                    POSMessageBox.error(
                        self,
                        title="Error",
                        message=f"Failed to restore database: {str(e)}"
                    )

        except Exception as e:
            POSMessageBox.error(
                self,
                title="Error",
                message=f"An error occurred: {str(e)}"
            )
