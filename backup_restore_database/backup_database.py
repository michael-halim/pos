from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QProcess

import os
import sys
from datetime import datetime
import shutil
import sqlite3

from generals.message_box import POSMessageBox
from generals.build import resource_path


class BackupRestoreDatabase(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.backup_dir = "backups"
        self.db_path = resource_path('db/pos.db')
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)


    def export_database(self):
        """Export/backup the current database"""
        try:
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}.db")
            
            # Create a copy of the database file
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
        try:
            # Show file dialog to select backup file
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
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
                shutil.copy2(self.db_path, current_backup)
                    
                # Replace current database with backup
                shutil.copy2(file_path, self.db_path)
                POSMessageBox.info(
                    self,
                    title="Success",
                    message="Database restored successfully. Application will now close.\n"
                )

                # Restart application
                self.restart_application()


        except Exception as e:
            POSMessageBox.error(
                self,
                title="Error",
                message=f"Failed to restore database: {str(e)}"
            )

    def restart_application(self):
        """Restart the application using QProcess"""
        QApplication.quit()
        process = QProcess()
        process.startDetached(sys.executable, sys.argv)