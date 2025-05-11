from PyQt6 import QtWidgets, uic
from datetime import datetime
import calendar

from reports.monthly_sales_report.services.monthly_sales_report_services import MonthlySalesReportService
from reports.monthly_sales_report.models.monthly_sales_report_models import MonthlySalesReportModel

from helper import format_number, add_prefix
from generals.build import resource_path
from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS,
    PERM_R_MONTHLY_SALES_REPORT
) 
from generals.messages import (
    ERR, ERR_PERM_R_MONTHLY_SALES_REPORT, PERM_DENIED
)
from reports.monthly_sales_report.translations import MONTHLY_SALES_REPORT_TRANSLATIONS
from generals.permission_manager import PermissionManager
from generals.language_manager import LanguageManager


class MonthlySalesReportWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_R_MONTHLY_SALES_REPORT):
            return
        
        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/monthly_sales_report.ui'), self)

        # Init Services
        self.monthly_sales_report_service = MonthlySalesReportService()
        
        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(MONTHLY_SALES_REPORT_TRANSLATIONS)

        # Connect Filter Transactions
        self.ui.close_button.clicked.connect(lambda: self.close())

        # Connect Buttons
        self.ui.find_monthly_sales_report_button.clicked.connect(self.show_monthly_sales_data)

        # Add years 2020-2100
        years = [str(i) for i in range(2020, 2100)]
        self.year_input.addItems(years)
        
        # Set current year
        current_year = str(datetime.now().year)
        self.year_input.setCurrentText(current_year)

        # Initialize calendar map
        self.calendar_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        # Set selection behavior to select entire rows
        self.ui.monthly_sales_table.setSelectionBehavior(SELECT_ROWS)
        self.ui.monthly_sales_table.setSelectionMode(SINGLE_SELECTION)

        # Set transactions and detail transactions table to be read only
        self.ui.monthly_sales_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties to resize to contents
        self.ui.monthly_sales_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.ui.monthly_sales_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        
        # Show data for both tables
        self.show_monthly_sales_data()


    # Overrides
    # ==============
    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        if not self.permission_manager.has_permission(PERM_R_MONTHLY_SALES_REPORT):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_R_MONTHLY_SALES_REPORT)
            self.close()
            return

        # Set window title
        if self.permission_manager.get_username().lower() not in self.windowTitle().lower():
            self.setWindowTitle(self.windowTitle() + ' - ' + self.permission_manager.get_username())

        # Translate Widget Text
        self.language_manager.translate_widget_text(self)
        
        self.monthly_sales_headers = ['Date', 'Total', 'Method', 'Created By']
        if self.language_manager.get_current_language() == 'id':
            self.monthly_sales_headers = ['Bulan', 'Total', 'Metode', 'Dibuat Oleh']

        self.language_manager.translate_table_headers(self.ui.monthly_sales_table, self.monthly_sales_headers)

        # Refresh the data
        self.show_monthly_sales_data()


    def show(self):
        """Override show to refresh data when window is shown"""
        super().show()
        if not self.permission_manager.has_permission(PERM_R_MONTHLY_SALES_REPORT):
            self.close()
            return
        
        # Refresh the data
        self.show_monthly_sales_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_R_MONTHLY_SALES_REPORT):
            self.close()
            return
        
        # Refresh the data
        self.show_monthly_sales_data()


    # Shows
    # ==============
    def show_monthly_sales_data(self):
        if not self.permission_manager.has_permission(PERM_R_MONTHLY_SALES_REPORT):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_MONTHLY_SALES_REPORT)
            return
        
        # Temporarily disable sorting
        self.monthly_sales_table.setSortingEnabled(False)
        
        # Get Year and Month
        year = self.year_input.currentText()
        month = self.month_input.currentText()

        month = self.calendar_map[month.lower()]

        # Get start and end of month
        start_of_month = datetime(int(year), int(month), 1)
        start_of_month_date = start_of_month.replace(hour=0, minute=0, second=0)

        end_of_month = calendar.monthrange(int(year), int(month))[1]
        end_of_month_date = datetime(int(year), int(month), end_of_month)
        end_of_month_date = end_of_month_date.replace(hour=23, minute=59, second=59)

        # Get all monthly sales
        monthly_sales_result = self.monthly_sales_report_service.get_monthly_sales_report(
            start_date = start_of_month_date,
            end_date = end_of_month_date
        )

        if not monthly_sales_result.success:
            POSMessageBox.error(self, title=ERR, message=monthly_sales_result.message)
            return

        # Set monthly sales table data
        self.set_monthly_sales_table_data(monthly_sales_result.data)


    # Setters
    # ==============
    def set_monthly_sales_table_data(self, data: list[MonthlySalesReportModel]):
        self.monthly_sales_table.setRowCount(0)
        total_transactions = 0

        for monthly_data in data:
            current_row = self.monthly_sales_table.rowCount()
            self.monthly_sales_table.insertRow(current_row)

            # Convert created_at string to datetime and format
            created_at_dt = datetime.strptime(monthly_data.created_at, '%Y-%m-%d %H:%M:%S')
            formatted_date = created_at_dt.strftime('%d %b %y %H:%M:%S')

            table_items =  [ 
                QtWidgets.QTableWidgetItem(formatted_date),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(monthly_data.total_sales))),
                QtWidgets.QTableWidgetItem(monthly_data.payment_method),
                QtWidgets.QTableWidgetItem(monthly_data.created_by)
            ]

            total_transactions += monthly_data.total_sales

            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.monthly_sales_table.setItem(current_row, col, item)

        self.ui.total_transactions_input.setText(add_prefix(format_number(total_transactions)))

        self.monthly_sales_table.setSortingEnabled(True)