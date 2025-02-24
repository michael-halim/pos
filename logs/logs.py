from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QDateEdit
from datetime import datetime

from helper import format_number, add_prefix, remove_non_digit

from logs.services.logs_services import LogsService
from logs.models.logs_models import LogsModel

from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS
from generals.build import resource_path

class LogsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/logs.ui'), self)

        # Init Services
        self.logs_service = LogsService()

        # Connect Filter Transactions
        self.ui.filter_logs_input.textChanged.connect(self.show_logs_data)

        # Connect Buttons
        self.ui.find_logs_button.clicked.connect(self.show_logs_data)

        # Init Tables
        self.logs_table = self.ui.logs_table

        self.logs_table.setSortingEnabled(True)

        # Set date input
        self.ui.start_date_logs_input.setDate(datetime.now())
        self.ui.end_date_logs_input.setDate(datetime.now())

        self.ui.start_date_logs_input.setDisplayFormat("dd/MM/yyyy")
        self.ui.end_date_logs_input.setDisplayFormat("dd/MM/yyyy")

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
        # Refresh the data
        self.show_logs_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        # Refresh the data
        self.show_logs_data()


    def show_logs_data(self):
        # Temporarily disable sorting
        self.logs_table.setSortingEnabled(False)
        
        # Clear the table
        self.logs_table.setRowCount(0)
        
        # Get Dates
        start_date = datetime.strptime(self.ui.start_date_logs_input.date().toString('dd/MM/yyyy'), '%d/%m/%Y')
        end_date = datetime.strptime(self.ui.end_date_logs_input.date().toString('dd/MM/yyyy'), '%d/%m/%Y')

        # Get search text if any
        search_text = self.ui.filter_logs_input.text().strip()
        search_text = search_text if search_text != '' else None

        # Get all logs
        logs_result = self.logs_service.get_logs(
            start_date = start_date.replace(hour=0, minute=0, second=0),
            end_date = end_date.replace(hour=23, minute=59, second=59),
            search_text=search_text
        )

        # Set logs_data table data
        self.set_logs_table_data(logs_result.data)
        
        # Enable sorting
        self.logs_table.setSortingEnabled(True)


    # Setters
    # ==============
    def set_logs_table_data(self, data: list[LogsModel]):
        for log in data:
            current_row = self.logs_table.rowCount()
            self.logs_table.insertRow(current_row)

            # Convert created_at string to datetime and format
            created_at_dt = datetime.strptime(log.created_at, '%Y-%m-%d %H:%M:%S')
            formatted_date = created_at_dt.strftime('%d %b %y %H:%M')

            table_items =  [ 
                QtWidgets.QTableWidgetItem(formatted_date),
                QtWidgets.QTableWidgetItem(log.log_type),
                QtWidgets.QTableWidgetItem(log.log_description),
                QtWidgets.QTableWidgetItem(log.old_data),
                QtWidgets.QTableWidgetItem(log.new_data)
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.logs_table.setItem(current_row, col, item)
