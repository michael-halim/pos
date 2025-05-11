from PyQt6 import QtWidgets, uic
from datetime import datetime, timedelta

from transactions_list.models.transactions_list_models import TransactionListModel, DetailTransactionListModel
from reports.back_office_sales_report.services.back_office_sales_report_services import BackOfficeSalesReportService

from helper import format_number, add_prefix
from generals.message_box import POSMessageBox
from generals.build import resource_path
from generals.fonts import POSFonts
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS,
    PERM_R_BACK_OFFICE_SALES_REPORT, DATE_FORMAT_DDMMYYYY
) 
from generals.messages import (
    ERR, ERR_PERM_R_BACK_OFFICE_SALES_REPORT,
    PERM_DENIED
)
from reports.back_office_sales_report.translations import BACK_OFFICE_SALES_REPORT_TRANSLATIONS
from generals.permission_manager import PermissionManager
from generals.language_manager import LanguageManager


class BackOfficeSalesReportWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        
        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_R_BACK_OFFICE_SALES_REPORT):
            return
        
        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/back_office_sales_report.ui'), self)

        # Init Services
        self.back_office_sales_report_service = BackOfficeSalesReportService()

        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(BACK_OFFICE_SALES_REPORT_TRANSLATIONS)

        # Connect Filter Transactions
        self.ui.filter_back_office_sales_transactions_input.textChanged.connect(self.show_transactions_data)
        self.ui.filter_back_office_sales_detail_transactions_input.textChanged.connect(self.filter_detail_transactions)
        self.ui.close_button.clicked.connect(lambda: self.close())

        # Connect Buttons
        self.ui.find_back_office_sales_button.clicked.connect(self.show_transactions_data)

        # Init Tables
        self.transactions_table = self.ui.back_office_sales_transactions_table
        self.detail_transactions_table = self.ui.back_office_sales_detail_transactions_table

        # Connect table selection
        self.transactions_table.itemSelectionChanged.connect(self.on_transaction_selected)
        
        # Set date input
        self.ui.start_date_back_office_sales_input.setDate(datetime.now() - timedelta(days=1))
        self.ui.end_date_back_office_sales_input.setDate(datetime.now())

        self.ui.start_date_back_office_sales_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)
        self.ui.end_date_back_office_sales_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)

        # Set selection behavior to select entire rows
        self.transactions_table.setSelectionBehavior(SELECT_ROWS)
        self.transactions_table.setSelectionMode(SINGLE_SELECTION)
        self.detail_transactions_table.setSelectionBehavior(SELECT_ROWS)
        self.detail_transactions_table.setSelectionMode(SINGLE_SELECTION)

        # Set transactions and detail transactions table to be read only
        self.transactions_table.setEditTriggers(NO_EDIT_TRIGGERS)
        self.detail_transactions_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties to resize to contents
        self.transactions_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.transactions_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.detail_transactions_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.detail_transactions_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        
        # Show data for both tables
        self.show_transactions_data()


    # Overrides
    # ==============
    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        if not self.permission_manager.has_permission(PERM_R_BACK_OFFICE_SALES_REPORT):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_R_BACK_OFFICE_SALES_REPORT)
            self.close()
            return


        # Set window title
        if self.permission_manager.get_username().lower() not in self.windowTitle().lower():
            self.setWindowTitle(self.windowTitle() + ' - ' + self.permission_manager.get_username())

        # Translate Widget Text
        self.language_manager.translate_widget_text(self)

        self.transactions_headers = ['Date', 'Tx Num', 'Total', 'Method', 'Remarks']
        self.detail_transactions_headers = ['SKU', 'Product Name', 'Price', 'Qty', 'Unit', 'Disc (%)', 'Disc Per Item (Rp)', 'Disc (Rp)', 'Subtotal']
        if self.language_manager.get_current_language() == 'id':
            self.transactions_headers = ['Tanggal', 'ID Transaksi', 'Total', 'Metode Pembayaran', 'Keterangan']
            self.detail_transactions_headers = ['Kode Barang', 'Nama Produk', 'Harga', 'Qty', 'Satuan', 'Diskon (%)', 'Diskon Per Item (Rp)', 'Diskon (Rp)', 'Subtotal']

        self.language_manager.translate_table_headers(self.transactions_table, self.transactions_headers)
        self.language_manager.translate_table_headers(self.detail_transactions_table, self.detail_transactions_headers)


        # Refresh the data
        self.show_transactions_data()


    def show(self):
        """Override show to refresh data when window is shown"""
        super().show()
        if not self.permission_manager.has_permission(PERM_R_BACK_OFFICE_SALES_REPORT):
            self.close()
            return
        
        # Refresh the data
        self.show_transactions_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_R_BACK_OFFICE_SALES_REPORT):
            self.close()
            return
        
        # Refresh the data
        self.show_transactions_data()

    
    # Shows
    # ==============
    def show_transactions_data(self):
        if not self.permission_manager.has_permission(PERM_R_BACK_OFFICE_SALES_REPORT):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_BACK_OFFICE_SALES_REPORT)
            return
        
        # Temporarily disable sorting
        self.transactions_table.setSortingEnabled(False)
        
        # Get Dates
        start_date = datetime.strptime(self.ui.start_date_back_office_sales_input.date().toString(DATE_FORMAT_DDMMYYYY), '%d/%m/%Y')
        end_date = datetime.strptime(self.ui.end_date_back_office_sales_input.date().toString(DATE_FORMAT_DDMMYYYY), '%d/%m/%Y')

        # Get search text if any
        search_text = self.ui.filter_back_office_sales_transactions_input.text().strip()
        search_text = search_text if search_text != '' else None

        # Get all transactions
        transactions_result = self.back_office_sales_report_service.get_transactions_list(
            start_date = start_date.replace(hour=0, minute=0, second=0),
            end_date = end_date.replace(hour=23, minute=59, second=59),
            search_text=search_text
        )

        if not transactions_result.success:
            POSMessageBox.error(self, title=ERR, message=transactions_result.message)
            return
        
        # Set transactions_data table data
        self.set_transactions_table_data(transactions_result.data)
        

    def filter_detail_transactions(self):
        search_text = self.ui.filter_back_office_sales_detail_transactions_input.text().lower()
        
        # Show all rows if search text is empty
        if not search_text:
            for row in range(self.detail_transactions_table.rowCount()):
                self.detail_transactions_table.setRowHidden(row, False)
            return
        
        # Iterate through all rows
        for row in range(self.detail_transactions_table.rowCount()):
            match_found = False
            
            # Search through all columns in the row
            for col in range(self.detail_transactions_table.columnCount()):
                item = self.detail_transactions_table.item(row, col)
                if item and search_text in item.text().lower():
                    match_found = True
                    break
            
            # Hide/show row based on whether match was found
            self.detail_transactions_table.setRowHidden(row, not match_found)
    

    # Setters
    # ==============
    def set_transactions_table_data(self, data: list[TransactionListModel]):
        self.transactions_table.setRowCount(0)
        total_transactions = 0
        for transaction in data:
            current_row = self.transactions_table.rowCount()
            self.transactions_table.insertRow(current_row)

            # Convert created_at string to datetime and format
            created_at_dt = datetime.strptime(transaction.created_at, '%Y-%m-%d %H:%M:%S')
            formatted_date = created_at_dt.strftime('%d %b %y %H:%M')

            table_items =  [ 
                QtWidgets.QTableWidgetItem(formatted_date),
                QtWidgets.QTableWidgetItem(transaction.transaction_id),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(transaction.payment_rp))),
                QtWidgets.QTableWidgetItem(transaction.payment_method),
                QtWidgets.QTableWidgetItem(transaction.payment_remarks)
            ]

            total_transactions += transaction.payment_rp

            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.transactions_table.setItem(current_row, col, item)

        self.ui.total_transactions_input.setText(add_prefix(format_number(total_transactions)))
        
        self.transactions_table.setSortingEnabled(True)


    def set_detail_transactions_table_data(self, data: list[DetailTransactionListModel]):
        # Clear the table
        self.detail_transactions_table.setRowCount(0)

        for detail_transaction in data:
            current_row = self.detail_transactions_table.rowCount()
            self.detail_transactions_table.insertRow(current_row)

            table_items = [
                QtWidgets.QTableWidgetItem(detail_transaction.sku),
                QtWidgets.QTableWidgetItem(detail_transaction.product_name),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(detail_transaction.price))),
                QtWidgets.QTableWidgetItem(format_number(detail_transaction.qty)),
                QtWidgets.QTableWidgetItem(detail_transaction.unit),
                QtWidgets.QTableWidgetItem(format_number(detail_transaction.discount_pct)),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(detail_transaction.discount_rp_per_item))),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(detail_transaction.discount_rp))),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(detail_transaction.subtotal))),
            ]

            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.detail_transactions_table.setItem(current_row, col, item)

        self.detail_transactions_table.setSortingEnabled(True)


    # Event Listeners
    # ==============
    def on_transaction_selected(self):
        selected_rows = self.transactions_table.selectedItems()
        if selected_rows:
            # Temporarily disable sorting
            self.detail_transactions_table.setSortingEnabled(False)

            # Get the first selected row
            row = selected_rows[0].row()
            selected_transaction = self.transactions_table.item(row, 1).text()
            
            dt_results = self.back_office_sales_report_service.get_detail_transactions_list(selected_transaction)
            if dt_results.success:
                self.set_detail_transactions_table_data(dt_results.data)
                
            else:
                POSMessageBox.error(self, title=ERR, message=dt_results.message)