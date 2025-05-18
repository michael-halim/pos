from PyQt6 import QtWidgets, uic
from datetime import datetime, timedelta

from transactions_list.models.transactions_list_models import TransactionListModel, DetailTransactionListModel
from transactions_list.services.transactions_list_services import TransactionListService
from transactions.transactions import TransactionsWindow
from printers.printer_service import PrinterService

from helper import format_number, add_prefix
from generals.fonts import POSFonts
from generals.build import resource_path
from generals.message_box import POSMessageBox
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS,
    PERM_R_TRANSACTIONS, PERM_C_TRANSACTIONS, PERM_U_TRANSACTIONS, PERM_D_TRANSACTIONS, DATE_FORMAT_DDMMYYYY
) 
from generals.messages import (
    ERR, OK, ERR_PERM_R_TRANSACTIONS, ERR_PERM_C_TRANSACTIONS, ERR_PERM_U_TRANSACTIONS, ERR_PERM_D_TRANSACTIONS,
    PERM_DENIED, CONFIRM
)
from transactions_list.translations import TRANSACTION_LIST_TRANSLATIONS
from generals.permission_manager import PermissionManager
from generals.language_manager import LanguageManager


class TransactionsListWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_R_TRANSACTIONS):
            return
        
        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/transactions_list.ui'), self)

        # Init Transactions Window
        self.transactions_window = TransactionsWindow()

        # Init Services
        self.transaction_list_service = TransactionListService()

        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(TRANSACTION_LIST_TRANSLATIONS)
        
        
        self.ui.delete_transactions_button.clicked.connect(self.delete_transactions)
        self.ui.edit_transactions_button.clicked.connect(self.edit_transactions)

        # Connect Filter Transactions
        self.ui.filter_transactions_input.textChanged.connect(self.show_transactions_data)
        self.ui.filter_detail_transactions_input.textChanged.connect(self.filter_detail_transactions)
        self.ui.create_transactions_button.clicked.connect(self.create_transactions)
        self.ui.print_transactions_button.clicked.connect(self.print_transactions)
        self.ui.close_transactions_list_button.clicked.connect(lambda: self.close())

        # Connect Buttons
        self.ui.find_transactions_list_button.clicked.connect(self.show_transactions_data)

        # Init Tables
        self.transactions_table = self.ui.transactions_table
        self.detail_transactions_table = self.ui.detail_transactions_table

        # Connect table selection
        self.transactions_table.itemSelectionChanged.connect(self.on_transaction_selected)
        
        # Set date input
        self.ui.start_date_transactions_list_input.setDate(datetime.now() - timedelta(days=1))
        self.ui.end_date_transactions_list_input.setDate(datetime.now())

        self.ui.start_date_transactions_list_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)
        self.ui.end_date_transactions_list_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)

        # Add selected tracking
        self.current_selected_sku = None
     
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
        


    # Overrides
    # ==============
    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        if not self.permission_manager.has_permission(PERM_R_TRANSACTIONS):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_R_TRANSACTIONS)
            self.close()
            return
        
        # Set window title
        if self.permission_manager.get_username().lower() not in self.windowTitle().lower():
            self.setWindowTitle(self.windowTitle() + ' - ' + self.permission_manager.get_username())

        # Translate Widget Text
        self.language_manager.translate_widget_text(self)

        self.transaction_headers = ['Date', 'Tx Num', 'Total Payment', 'Method', 'Remarks']
        self.detail_transaction_headers = ['SKU', 'Product Name', 'Price', 'Qty', 'Unit', 'Disc (%)', 'Disc Per Item (Rp)', 'Disc (Rp)', 'Subtotal']
        if self.language_manager.get_current_language() == 'id':
            self.transaction_headers = ['Tanggal', 'ID Transaksi', 'Total Belanja', 'Metode', 'Keterangan']
            self.detail_transaction_headers = ['Kode Barang', 'Nama Produk', 'Harga', 'Qty', 'Satuan', 'Disc (%)', 'Disc Per Item (Rp)', 'Disc (Rp)', 'Subtotal']

        self.language_manager.translate_table_headers(self.ui.transactions_table, self.transaction_headers)
        self.language_manager.translate_table_headers(self.ui.detail_transactions_table, self.detail_transaction_headers)


        # Refresh the data
        self.show_transactions_data()


    def show(self):
        """Override show to refresh data when window is shown"""
        super().show()
        if not self.permission_manager.has_permission(PERM_R_TRANSACTIONS):
            self.close()
            return
        
        # Refresh the data
        self.show_transactions_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_R_TRANSACTIONS):
            self.close()
            return
        
        # Refresh the data
        self.show_transactions_data()

    
    def create_transactions(self):
        if not self.permission_manager.has_permission(PERM_C_TRANSACTIONS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_C_TRANSACTIONS)
            return
        
        self.transactions_window.showMaximized()


    def edit_transactions(self):
        if not self.permission_manager.has_permission(PERM_U_TRANSACTIONS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_U_TRANSACTIONS)
            return
        
        selected_rows = self.transactions_table.selectedItems()
        if not selected_rows:
            POSMessageBox.warning(self, title=ERR, message="Please select a transaction to edit")
            return
        
        row = selected_rows[0].row()
        transaction_id = self.transactions_table.item(row, 1).text()

        self.transactions_window.set_transactions_by_id(transaction_id)
        self.transactions_window.showMaximized()


    def delete_transactions(self):
        if not self.permission_manager.has_permission(PERM_D_TRANSACTIONS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_D_TRANSACTIONS)
            return
        
        selected_rows = self.transactions_table.selectedItems()
        if not selected_rows:
            POSMessageBox.warning(self, title=ERR, message="Please select a transaction to delete")
            return
        
        row = selected_rows[0].row()
        transaction_id = self.transactions_table.item(row, 1).text()

        confirm = POSMessageBox.confirm(
                    self, title=CONFIRM, 
                    message=f'Are you sure you want to delete {transaction_id} ?')

        if confirm:
            result = self.transaction_list_service.delete_transactions_by_id(transaction_id)
            if result.success:
                POSMessageBox.info(self, title=OK, message=result.message)

                # Just refresh the data directly
                self.show_transactions_data()

            else:
                POSMessageBox.error(self, title=ERR, message=result.message)


    def print_transactions(self):
        selected_rows = self.transactions_table.selectedItems()
        if not selected_rows:
            POSMessageBox.warning(self, title=ERR, message="Please select a transaction to print")
            return


        row = selected_rows[0].row()
        transaction_id = self.transactions_table.item(row, 1).text()


        # Get transaction data
        transaction_result = self.transaction_list_service.get_transaction_by_id(transaction_id)
        if not transaction_result.success:
            POSMessageBox.error(self, title=ERR, message=transaction_result.message)
            return


        # Get detail transactions data
        detail_transactions_result = self.transaction_list_service.get_transactions_table_data(transaction_id)
        if not detail_transactions_result.success:
            POSMessageBox.error(self, title=ERR, message=detail_transactions_result.message)
            return


        # Get customer data
        customer_result = self.transaction_list_service.get_customer_by_id(transaction_result.data.customer_id)
        if not customer_result.success:
            POSMessageBox.error(self, title=ERR, message=customer_result.message)
            return

        # Print the transaction
        printer_service = PrinterService()
        printer_service.print_receipt(transaction_result.data, detail_transactions_result.data, customer_result.data)


    # Shows
    # ==============
    def show_transactions_data(self):
        if not self.permission_manager.has_permission(PERM_R_TRANSACTIONS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_TRANSACTIONS)
            return
        
        # Temporarily disable sorting
        self.transactions_table.setSortingEnabled(False)
        
        # Get Dates
        start_date = datetime.strptime(self.ui.start_date_transactions_list_input.date().toString(DATE_FORMAT_DDMMYYYY), '%d/%m/%Y')
        end_date = datetime.strptime(self.ui.end_date_transactions_list_input.date().toString(DATE_FORMAT_DDMMYYYY), '%d/%m/%Y')

        # Get search text if any
        search_text = self.ui.filter_transactions_input.text().strip()
        search_text = search_text if search_text != '' else None

        # Get all transactions
        transactions_result = self.transaction_list_service.get_transactions_list(
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
        search_text = self.ui.filter_detail_transactions_input.text().lower()
        
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
            
            dt_results = self.transaction_list_service.get_detail_transactions_list(selected_transaction)
            if dt_results.success:
                self.set_detail_transactions_table_data(dt_results.data)
                
            else:
                POSMessageBox.error(self, title=ERR, message=dt_results.message)
