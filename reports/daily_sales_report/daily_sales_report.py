from PyQt6 import QtWidgets, uic
from datetime import datetime, timedelta

from reports.daily_sales_report.services.daily_sales_report_services import DailySalesReportService
from reports.daily_sales_report.models.daily_sales_report_models import DailySalesReportModel

from helper import format_number, add_prefix
from generals.build import resource_path
from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS,
    PERM_R_DAILY_SALES_REPORT, DATE_FORMAT_DDMMYYYY
) 
from generals.messages import (
    ERR, ERR_PERM_R_DAILY_SALES_REPORT, PERM_DENIED
)
from reports.daily_sales_report.translations import DAILY_SALES_REPORT_TRANSLATIONS
from generals.permission_manager import PermissionManager
from generals.language_manager import LanguageManager


class DailySalesReportWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_R_DAILY_SALES_REPORT):
            return
        
        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/daily_sales_report.ui'), self)

        # Init Services
        self.daily_sales_report_service = DailySalesReportService()

        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(DAILY_SALES_REPORT_TRANSLATIONS)

        # Connect Filter Daily Sales
        self.ui.find_daily_sales_report_button.clicked.connect(self.show_daily_sales_data)
        self.ui.close_button.clicked.connect(lambda: self.close())

         # Set date input
        self.ui.start_date_daily_sales_input.setDate(datetime.now() - timedelta(days=1))
        self.ui.end_date_daily_sales_input.setDate(datetime.now())

        self.ui.start_date_daily_sales_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)
        self.ui.end_date_daily_sales_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)

        # Set selection behavior to select entire rows
        self.ui.daily_sales_table.setSelectionBehavior(SELECT_ROWS)
        self.ui.daily_sales_table.setSelectionMode(SINGLE_SELECTION)

        # Set transactions and detail transactions table to be read only
        self.ui.daily_sales_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties to resize to contents
        self.ui.daily_sales_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.ui.daily_sales_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        

    # Overrides
    # ==============
    def show(self):
        """Override show to refresh data when window is shown"""
        super().show()
        if not self.permission_manager.has_permission(PERM_R_DAILY_SALES_REPORT):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_DAILY_SALES_REPORT)
            self.close()
            return
        

    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        if not self.permission_manager.has_permission(PERM_R_DAILY_SALES_REPORT):
            self.close()


        # Translate Widget Text
        self.language_manager.translate_widget_text(self)

        self.daily_sales_headers = ['Date', 'Total', 'Method', 'Created By']
        if self.language_manager.get_current_language() == 'id':
            self.daily_sales_headers = ['Tanggal', 'Total', 'Metode', 'Dibuat Oleh']

        self.language_manager.translate_table_headers(self.ui.daily_sales_table, self.daily_sales_headers)


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_R_DAILY_SALES_REPORT):
            self.close()
        


    # Shows
    # ==============
    def show_daily_sales_data(self):
        if not self.permission_manager.has_permission(PERM_R_DAILY_SALES_REPORT):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_DAILY_SALES_REPORT)
            return
        
        # Temporarily disable sorting
        self.daily_sales_table.setSortingEnabled(False)
        
        # Get Dates
        start_date = datetime.strptime(self.ui.start_date_daily_sales_input.date().toString(DATE_FORMAT_DDMMYYYY), '%d/%m/%Y')
        end_date = datetime.strptime(self.ui.end_date_daily_sales_input.date().toString(DATE_FORMAT_DDMMYYYY), '%d/%m/%Y')

        # Get all daily sales
        daily_sales_result = self.daily_sales_report_service.get_daily_sales_report(
            start_date = start_date.replace(hour=0, minute=0, second=0),
            end_date = end_date.replace(hour=23, minute=59, second=59),
        )

        if not daily_sales_result.success:
            POSMessageBox.error(self, title=ERR, message=daily_sales_result.message)
            return

        # Set daily sales table data
        self.set_daily_sales_table_data(daily_sales_result.data)


    # Setters
    # ==============
    def set_daily_sales_table_data(self, data: list[DailySalesReportModel]):
        self.daily_sales_table.setRowCount(0)
        total_transactions = 0

        for daily_data in data:
            current_row = self.daily_sales_table.rowCount()
            self.daily_sales_table.insertRow(current_row)

            # Convert created_at string to datetime and format
            created_at_dt = datetime.strptime(daily_data.created_at, '%Y-%m-%d %H:%M:%S')
            formatted_date = created_at_dt.strftime('%d %b %y %H:%M:%S')

            table_items =  [ 
                QtWidgets.QTableWidgetItem(formatted_date),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(daily_data.total_sales))),
                QtWidgets.QTableWidgetItem(daily_data.payment_method),
                QtWidgets.QTableWidgetItem(daily_data.created_by)
            ]

            total_transactions += daily_data.total_sales

            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.daily_sales_table.setItem(current_row, col, item)

        self.ui.total_transactions_input.setText(add_prefix(format_number(total_transactions)))

        self.daily_sales_table.setSortingEnabled(True)
