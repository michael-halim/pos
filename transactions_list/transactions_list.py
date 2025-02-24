from PyQt6 import QtWidgets, uic
from datetime import datetime

from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS
from generals.fonts import POSFonts
from helper import format_number, add_prefix

from transactions_list.models.transactions_list_models import TransactionListModel, DetailTransactionListModel
from transactions_list.services.transactions_list_services import TransactionListService
from generals.build import resource_path
class TransactionsListWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/transactions_list.ui'), self)

        # Init Services
        self.transaction_list_service = TransactionListService()

        # Connect Filter Transactions
        self.ui.filter_transactions_input.textChanged.connect(self.show_transactions_data)
        self.ui.filter_detail_transactions_input.textChanged.connect(self.filter_detail_transactions)

        # Connect Buttons
        self.ui.find_transactions_list_button.clicked.connect(self.show_transactions_data)

        # Init Tables
        self.transactions_table = self.ui.transactions_table
        self.detail_transactions_table = self.ui.detail_transactions_table

        self.transactions_table.setSortingEnabled(True)
        self.detail_transactions_table.setSortingEnabled(True)

        # Connect table selection
        self.transactions_table.itemSelectionChanged.connect(self.on_transaction_selected)
        
        # Set date input
        self.ui.start_date_transactions_list_input.setDate(datetime.now())
        self.ui.end_date_transactions_list_input.setDate(datetime.now())

        self.ui.start_date_transactions_list_input.setDisplayFormat("dd/MM/yyyy")
        self.ui.end_date_transactions_list_input.setDisplayFormat("dd/MM/yyyy")

        # Add selected tracking
        self.current_selected_sku = None
     
        # Set selection behavior to select entire rows
        self.transactions_table.setSelectionBehavior(SELECT_ROWS)
        self.transactions_table.setSelectionMode(SINGLE_SELECTION)
        self.detail_transactions_table.setSelectionBehavior(SELECT_ROWS)
        self.detail_transactions_table.setSelectionMode(SINGLE_SELECTION)

        # Set wholesale transactions table to be read only
        self.transactions_table.setEditTriggers(NO_EDIT_TRIGGERS)
        self.detail_transactions_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties to resize to contents
        self.transactions_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.transactions_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.detail_transactions_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.detail_transactions_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        
        # Show data for both tables
        self.show_transactions_data()


    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        # Reset the current selection
        self.current_selected_transaction_id = None
        # Refresh the data
        self.show_transactions_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        # Reset the current selection
        self.current_selected_transaction_id = None
        # Refresh the data
        self.show_transactions_data()


    def show_transactions_data(self):
        # Temporarily disable sorting
        self.transactions_table.setSortingEnabled(False)
        
        # Clear the table
        self.transactions_table.setRowCount(0)
        
        # Get Dates
        start_date = datetime.strptime(self.ui.start_date_transactions_list_input.date().toString('dd/MM/yyyy'), '%d/%m/%Y')
        end_date = datetime.strptime(self.ui.end_date_transactions_list_input.date().toString('dd/MM/yyyy'), '%d/%m/%Y')

        # Get search text if any
        search_text = self.ui.filter_transactions_input.text().strip()
        search_text = search_text if search_text != '' else None

        # Get all transactions
        transactions_result = self.transaction_list_service.get_transactions_list(
            start_date = start_date.replace(hour=0, minute=0, second=0),
            end_date = end_date.replace(hour=23, minute=59, second=59),
            search_text=search_text
        )

        # Set transactions_data table data
        self.set_transactions_table_data(transactions_result.data)
        
        # Enable sorting
        self.transactions_table.setSortingEnabled(True)


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
    

    def on_transaction_selected(self):
        selected_rows = self.transactions_table.selectedItems()
        if selected_rows:
            # Get the first selected row
            row = selected_rows[1].row()
            self.current_selected_transaction_id = self.transactions_table.item(row, 1).text()
            
            dt_results = self.transaction_list_service.get_detail_transactions_list(self.current_selected_transaction_id)
            if dt_results.success :
                self.set_detail_transactions_table_data(dt_results.data)


    # Setters
    # ==============
    def set_transactions_table_data(self, data: list[TransactionListModel]):
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
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.transactions_table.setItem(current_row, col, item)


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
                QtWidgets.QTableWidgetItem(add_prefix(format_number(detail_transaction.discount_rp))),
                QtWidgets.QTableWidgetItem(format_number(detail_transaction.discount_pct)),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(detail_transaction.subtotal))),
            ]

            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.detail_transactions_table.setItem(current_row, col, item)