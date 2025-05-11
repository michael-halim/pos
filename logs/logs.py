from PyQt6 import QtWidgets, uic
from datetime import datetime

from logs.services.logs_services import LogsService
from logs.models.logs_models import LogsModel

from generals.fonts import POSFonts
from generals.build import resource_path
from generals.message_box import POSMessageBox
from generals.constants import (
    RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS,
    PERM_R_LOGS, DATE_FORMAT_DDMMYYYY
)
from generals.messages import (
    ERR, ERR_PERM_R_LOGS, PERM_DENIED
)
from logs.translations import LOGS_TRANSLATIONS
from generals.permission_manager import PermissionManager
from generals.language_manager import LanguageManager


class LogsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_R_LOGS):
            return

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/logs.ui'), self)

        # Init Services
        self.logs_service = LogsService()

        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(LOGS_TRANSLATIONS)

        # Connect Filter Transactions
        self.ui.filter_logs_input.textChanged.connect(self.show_logs_data)

        # Connect Buttons
        self.ui.find_logs_button.clicked.connect(self.show_logs_data)
        self.ui.close_logs_button.clicked.connect(lambda: self.close())

        # Init Tables
        self.logs_table = self.ui.logs_table

        # Set date input
        self.ui.start_date_logs_input.setDate(datetime.now())
        self.ui.end_date_logs_input.setDate(datetime.now())

        self.ui.start_date_logs_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)
        self.ui.end_date_logs_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)

        # Set selection behavior to select entire rows
        self.logs_table.setSelectionBehavior(SELECT_ROWS)
        self.logs_table.setSelectionMode(SINGLE_SELECTION)

        # Set wholesale transactions table to be read only
        self.logs_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties to resize to contents
        self.logs_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.logs_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        
        # Show data for both tables
        self.show_logs_data()


    # Overrides
    # ===============
    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        if not self.permission_manager.has_permission(PERM_R_LOGS):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_R_LOGS)
            self.close()
            return
        
        # Set window title
        if self.permission_manager.get_username().lower() not in self.windowTitle().lower():
            self.setWindowTitle(self.windowTitle() + ' - ' + self.permission_manager.get_username())

        # Translate Widget Text
        self.language_manager.translate_widget_text(self)
        
        self.logs_headers = ['Date', 'Log Type', 'Log Description', 'Old Data', 'New Data', 'Created By']
        if self.language_manager.get_current_language() == 'id':
            self.logs_headers = ['Tanggal', 'Tipe Log', 'Deskripsi Log', 'Data Lama', 'Data Baru', 'Dibuat Oleh']

        self.language_manager.translate_table_headers(self.logs_table, self.logs_headers)

        # Refresh the data
        self.show_logs_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_R_LOGS):
            self.close()
            return
        
        # Refresh the data
        self.show_logs_data()


    def show(self):
        """Override show to ensure data is refreshed"""
        super().show()
        if not self.permission_manager.has_permission(PERM_R_LOGS):
            self.close()
            return


    def show_logs_data(self):
        # Temporarily disable sorting
        self.logs_table.setSortingEnabled(False)
        
        # Get Dates
        start_date = datetime.strptime(self.ui.start_date_logs_input.date().toString(DATE_FORMAT_DDMMYYYY), '%d/%m/%Y')
        end_date = datetime.strptime(self.ui.end_date_logs_input.date().toString(DATE_FORMAT_DDMMYYYY), '%d/%m/%Y')

        # Get search text if any
        search_text = self.ui.filter_logs_input.text().strip()
        search_text = search_text if search_text != '' else None

        # Get all logs
        logs_result = self.logs_service.get_logs(
            start_date = start_date.replace(hour=0, minute=0, second=0),
            end_date = end_date.replace(hour=23, minute=59, second=59),
            search_text=search_text
        )

        if logs_result.success and logs_result.data is not None:
            self.set_logs_table_data(logs_result.data)

        elif not logs_result.success:
            POSMessageBox.warning(self, title=ERR, message=logs_result.message)
            self.set_logs_table_data([])
        

    # Setters
    # ==============
    def set_logs_table_data(self, data: list[LogsModel]):
        self.logs_table.setRowCount(0)

        for log in data:
            current_row = self.logs_table.rowCount()
            self.logs_table.insertRow(current_row)

            # Convert created_at string to datetime and format
            created_at_dt = datetime.strptime(log.created_at, '%Y-%m-%d %H:%M:%S')
            formatted_date = created_at_dt.strftime('%d %b %y %H:%M:%S')

            table_items =  [ 
                QtWidgets.QTableWidgetItem(formatted_date),
                QtWidgets.QTableWidgetItem(log.log_type),
                QtWidgets.QTableWidgetItem(log.log_description),
                QtWidgets.QTableWidgetItem(log.old_data),
                QtWidgets.QTableWidgetItem(log.new_data),
                QtWidgets.QTableWidgetItem(log.created_by)
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.logs_table.setItem(current_row, col, item)

        self.logs_table.setSortingEnabled(True)