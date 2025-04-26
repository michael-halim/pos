from PyQt6 import QtWidgets, uic
from datetime import datetime

from reports.profit_and_loss_report.services.profit_and_loss_report_services import ProfitAndLossReportService
from reports.profit_and_loss_report.models.profit_and_loss_report_models import ProfitAndLossReportModel

from helper import format_number, add_prefix
from generals.build import resource_path
from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS,
    PERM_R_PROFIT_AND_LOSS_REPORT
) 
from generals.messages import (
    ERR, ERR_PERM_R_PROFIT_AND_LOSS_REPORT, PERM_DENIED
)
from generals.permission_manager import PermissionManager


class ProfitAndLossReportWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_R_PROFIT_AND_LOSS_REPORT):
            return
        
        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/profit_and_loss_report.ui'), self)

        # Init Services
        self.profit_and_loss_report_service = ProfitAndLossReportService()

        # Connect Filter Profit and Loss
        self.ui.find_profit_and_loss_button.clicked.connect(self.show_profit_and_loss_data)
        self.ui.close_button.clicked.connect(lambda: self.close())

        # Add years 2020-2100
        years = [str(i) for i in range(2020, 2100)]
        self.year_input.addItems(years)
        
        self.month_map = {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December"
        }

        # Set current year
        current_year = str(datetime.now().year)
        self.year_input.setCurrentText(current_year)

        # Set selection behavior to select entire rows
        self.ui.profit_and_loss_table.setSelectionBehavior(SELECT_ROWS)
        self.ui.profit_and_loss_table.setSelectionMode(SINGLE_SELECTION)

        # Set transactions and detail transactions table to be read only
        self.ui.profit_and_loss_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties to resize to contents
        self.ui.profit_and_loss_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.ui.profit_and_loss_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        

    # Overrides
    # ==============
    def show(self):
        """Override show to refresh data when window is shown"""
        super().show()
        if not self.permission_manager.has_permission(PERM_R_PROFIT_AND_LOSS_REPORT):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_PROFIT_AND_LOSS_REPORT)
            self.close()
            return
        

    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        if not self.permission_manager.has_permission(PERM_R_PROFIT_AND_LOSS_REPORT):
            self.close()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_R_PROFIT_AND_LOSS_REPORT):
            self.close()
        

    # Shows
    # ==============
    def show_profit_and_loss_data(self):
        if not self.permission_manager.has_permission(PERM_R_PROFIT_AND_LOSS_REPORT):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_PROFIT_AND_LOSS_REPORT)
            return
        
        # Temporarily disable sorting
        self.profit_and_loss_table.setSortingEnabled(False)
        
        year = self.ui.year_input.currentText()

        # Get all profit and loss
        profit_and_loss_result = self.profit_and_loss_report_service.get_profit_and_loss_report(
            year = year
        )

        if not profit_and_loss_result.success:
            POSMessageBox.error(self, title=ERR, message=profit_and_loss_result.message)
            return

        # Set profit and loss table data
        self.set_profit_and_loss_table_data(profit_and_loss_result.data)


    # Setters
    # ==============
    def set_profit_and_loss_table_data(self, data: list[ProfitAndLossReportModel]):
        self.profit_and_loss_table.setRowCount(0)
        total_transactions = 0

        for pnl_data in data:
            current_row = self.profit_and_loss_table.rowCount()
            self.profit_and_loss_table.insertRow(current_row)

            # Convert created_at string to datetime and format
            month_name = self.month_map[pnl_data.period]

            table_items =  [ 
                QtWidgets.QTableWidgetItem(month_name),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(str(pnl_data.profit)))),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(str(pnl_data.accumulated_profit)))),
            ]

            total_transactions += pnl_data.profit

            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.profit_and_loss_table.setItem(current_row, col, item)

        self.ui.total_transactions_input.setText(add_prefix(format_number(total_transactions)))

        self.profit_and_loss_table.setSortingEnabled(True)