from PyQt6 import QtWidgets, uic, QtGui
from PyQt6.QtCore import Qt
from datetime import datetime, date, timedelta

from dialogs.stock_card_dialog.services.stock_card_dialog_services import StockCardDialogService
from dialogs.stock_card_dialog.models.stock_card_dialog_models import StockCardTableItemModel

from helper import format_number
from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import (
    RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS, DATE_FORMAT_DDMMYYYY
)
from generals.build import resource_path


class StockCardDialogWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/stock_card_dialog.ui'), self)

        # Init Services
        self.stock_card_dialog_service = StockCardDialogService()

        # Init Tables
        self.stock_card_table = self.ui.stock_card_table
        
        # Set date input
        self.ui.start_date_stock_card_dialog_input.setDate(datetime.now() - timedelta(days=1))
        self.ui.end_date_stock_card_dialog_input.setDate(datetime.now())

        # Connect find stock card button
        self.ui.find_stock_card_dialog_button.clicked.connect(lambda: self.show_stock_card_data(self.saved_sku))
        self.ui.close_stock_card_dialog_button.clicked.connect(lambda: self.close())

        # Saved SKU
        self.saved_sku = None

        self.ui.start_date_stock_card_dialog_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)
        self.ui.end_date_stock_card_dialog_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)
       
        # Set selection behavior to select entire rows
        self.stock_card_table.setSelectionBehavior(SELECT_ROWS)
        self.stock_card_table.setSelectionMode(SINGLE_SELECTION)

        self.stock_card_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties
        self.stock_card_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.stock_card_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)


    def showEvent(self, event):
        super().showEvent(event)

    
    def show(self):
        super().show()
    

    def showMaximized(self):
        super().showMaximized()


    def set_stock_card_data(self, data: list[StockCardTableItemModel]):
        # Clear the table
        self.stock_card_table.setRowCount(0)

        for stock_card in data:
            current_row = self.stock_card_table.rowCount()
            self.stock_card_table.insertRow(current_row)

            # Set stock in and align center
            stock_in = QtWidgets.QTableWidgetItem('-')
            
            if stock_card.stock_in is not None:
                stock_in = QtWidgets.QTableWidgetItem(format_number(str(stock_card.stock_in)))
                stock_in.setForeground(QtGui.QColor(0, 0, 255))

            stock_in.setTextAlignment(Qt.AlignmentFlag.AlignCenter)


            # Set stock out and align center
            stock_out = QtWidgets.QTableWidgetItem('-')
            if stock_card.stock_out is not None:
                stock_out = QtWidgets.QTableWidgetItem(format_number(str(stock_card.stock_out)))
                stock_out.setForeground(QtGui.QColor(0, 255, 0))

            stock_out.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Set running balance and align center
            running_balance = QtWidgets.QTableWidgetItem(format_number(str(stock_card.running_balance)))
            running_balance.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Set date
            tmp_date = datetime.strptime(stock_card.date, '%Y-%m-%d')
            formatted_date = tmp_date.strftime('%d %b %y')
            
            # Set time
            tmp_time = datetime.strptime(stock_card.time, '%H:%M:%S')
            formatted_time = tmp_time.strftime('%H:%M')

            table_items =  [ 
               QtWidgets.QTableWidgetItem(formatted_date),
               QtWidgets.QTableWidgetItem(formatted_time),
               QtWidgets.QTableWidgetItem(stock_card.transaction_id),
               stock_in,
               stock_out,
               running_balance,
               QtWidgets.QTableWidgetItem(stock_card.remarks),
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.stock_card_table.setItem(current_row, col, item)


    def show_stock_card_data(self, sku: str = None, start_date_params: date = None, end_date_params: date = None):
        if not sku and not self.saved_sku:
            POSMessageBox.warning(self, 'Warning', 'Please enter a valid SKU')
            return
        
        if not sku:
            sku = self.saved_sku

        self.saved_sku = sku

        # Disable sorting
        self.stock_card_table.setSortingEnabled(False)

        start_date = start_date_params
        end_date = end_date_params
        if start_date is None or end_date is None:
            start_date = datetime.strptime(self.ui.start_date_stock_card_dialog_input.date().toString(DATE_FORMAT_DDMMYYYY), '%d/%m/%Y')
            end_date = datetime.strptime(self.ui.end_date_stock_card_dialog_input.date().toString(DATE_FORMAT_DDMMYYYY), '%d/%m/%Y')

        stock_card_result = self.stock_card_dialog_service.get_stock_card(sku, start_date, end_date)

        self.ui.sku_stock_card_dialog_input.setText(str(self.saved_sku))

        self.set_stock_card_data(stock_card_result.data)

        # Re-enable sorting
        self.stock_card_table.setSortingEnabled(True)
