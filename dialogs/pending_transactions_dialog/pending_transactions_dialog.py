from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import pyqtSignal
from datetime import datetime

from dialogs.pending_transactions_dialog.services.pending_transactions_dialog_services import PendingTransactionsDialogService
from dialogs.pending_transactions_dialog.models.pending_transactions_dialog_models import PendingTransactionModel, PendingDetailTransactionModel

from helper import format_number, add_prefix
from generals.message_box import POSMessageBox
from generals.build import resource_path
from generals.fonts import POSFonts
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS,
    PERM_R_PENDING_TRANSACTIONS
) 
from generals.messages import ( 
    ERR_PERM_R_PENDING_TRANSACTIONS, PERM_DENIED
)
from generals.permission_manager import PermissionManager

class PendingTransactionsDialogWindow(QtWidgets.QWidget):
    pending_transaction_selected = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_R_PENDING_TRANSACTIONS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_PENDING_TRANSACTIONS)
            self.close()
            return
        
        
        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/pending_transactions_dialog.ui'), self)
        
        # Init Services
        self.pending_transactions_dialog_service = PendingTransactionsDialogService()

        # Init Tables
        self.pending_transactions_table = self.ui.pending_transactions_table
        self.pending_detail_transactions_table = self.ui.pending_detail_transactions_table

        self.pending_transactions_table.setSortingEnabled(True)
        self.pending_detail_transactions_table.setSortingEnabled(True)

        # Connect Add Pending Transaction Button
        self.ui.add_pending_transactions_button.clicked.connect(self.send_pending_transaction)
        self.ui.close_pending_transactions_button.clicked.connect(lambda: self.close())

        # Connect search input to filter function
        self.ui.pending_transactions_filter_input.textChanged.connect(self.show_pending_transactions_data)
        
        # Add selected supplier tracking
        self.current_pending_transaction_id = None

        # Connect table selection
        self.pending_transactions_table.itemSelectionChanged.connect(self.on_pending_transaction_selected)

        # Set selection behavior to select entire rows
        self.pending_transactions_table.setSelectionBehavior(SELECT_ROWS)
        self.pending_transactions_table.setSelectionMode(SINGLE_SELECTION)

        self.pending_detail_transactions_table.setSelectionBehavior(SELECT_ROWS)
        self.pending_detail_transactions_table.setSelectionMode(SINGLE_SELECTION)

        self.pending_transactions_table.setEditTriggers(NO_EDIT_TRIGGERS)
        self.pending_detail_transactions_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties
        self.pending_transactions_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.pending_transactions_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        self.pending_detail_transactions_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.pending_detail_transactions_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        # Add filter input for detail transactions
        self.ui.pending_detail_transactions_filter_input.textChanged.connect(self.filter_detail_transactions)

        self.show_pending_transactions_data()
        self.show_detail_pending_transactions_data()
    

    # Setters
    # ===============
    def set_pending_transactions_table_data(self, data: list[PendingTransactionModel]):
        # Clear the table
        self.pending_transactions_table.setRowCount(0)

        for pending_transaction in data:
            current_row = self.pending_transactions_table.rowCount()
            self.pending_transactions_table.insertRow(current_row)
            
            created_at_dt = datetime.strptime(pending_transaction.created_at, '%Y-%m-%d %H:%M:%S')
            formatted_date = created_at_dt.strftime('%d %b %y %H:%M')

            # Set table items
            table_items = [
                QtWidgets.QTableWidgetItem(pending_transaction.transaction_id),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(pending_transaction.total_amount))),
                QtWidgets.QTableWidgetItem(formatted_date),
                QtWidgets.QTableWidgetItem(pending_transaction.payment_remarks)
            ]

            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.pending_transactions_table.setItem(current_row, col, item)


    # Overrides
    # ===============
    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        # Reset the current selection
        self.current_pending_transaction_id = None
        # Refresh the data
        self.show_pending_transactions_data()
        self.show_detail_pending_transactions_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        # Reset the current selection
        self.current_pending_transaction_id = None
        # Refresh the data
        self.show_pending_transactions_data()
        self.show_detail_pending_transactions_data()

    
    # Shows
    # ===============
    def show_pending_transactions_data(self):
        # Temporarily disable sorting
        self.pending_transactions_table.setSortingEnabled(False)
        
        # Get search text if any
        search_text = self.ui.pending_transactions_filter_input.text().strip()
        search_text = search_text.lower() if search_text else None
        
        pending_transactions_result = self.pending_transactions_dialog_service.get_pending_transactions(search_text)

        self.set_pending_transactions_table_data(pending_transactions_result.data)

        self.pending_transactions_table.setSortingEnabled(True)


    def show_detail_pending_transactions_data(self):
        if not self.current_pending_transaction_id:
            return
        
        # Temporarily disable sorting
        self.pending_detail_transactions_table.setSortingEnabled(False)
        
        pending_detail_transactions_result = self.pending_transactions_dialog_service.get_pending_detail_transactions(self.current_pending_transaction_id)

        self.set_pending_detail_transactions_table_data(pending_detail_transactions_result.data)

        self.pending_detail_transactions_table.setSortingEnabled(True)


    # Setters
    # ===============
    def set_pending_detail_transactions_table_data(self, data: list[PendingDetailTransactionModel]):
        # Clear the table
        self.pending_detail_transactions_table.setRowCount(0)

        for pdt in data:
            current_row = self.pending_detail_transactions_table.rowCount()
            self.pending_detail_transactions_table.insertRow(current_row)
            
            # Set table items
            table_items = [
                QtWidgets.QTableWidgetItem(pdt.sku),
                QtWidgets.QTableWidgetItem(pdt.product_name),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(pdt.price))),
                QtWidgets.QTableWidgetItem(format_number(pdt.qty)),
                QtWidgets.QTableWidgetItem(pdt.unit),
                QtWidgets.QTableWidgetItem(format_number(pdt.discount_pct)),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(pdt.discount_rp_per_item))),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(pdt.discount_rp))),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(pdt.subtotal)))
            ]

            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.pending_detail_transactions_table.setItem(current_row, col, item)


    # Emitters
    # ===============
    def send_pending_transaction(self):
        selected_rows = self.pending_transactions_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()

            # Get the transaction id
            pending_transaction_data = {
                'transaction_id': self.pending_transactions_table.item(row, 0).text(),
            }
            
            # Emit signal with product data
            self.pending_transaction_selected.emit(pending_transaction_data)
            self.close()


    # Handlers
    # ===============
    def on_pending_transaction_selected(self):
        selected_rows = self.pending_transactions_table.selectedItems()
        if selected_rows:
            # Get the first selected row
            row = selected_rows[0].row()
            self.current_pending_transaction_id = self.pending_transactions_table.item(row, 0).text()
            # Show details when a transaction is selected
            self.show_detail_pending_transactions_data()



    def filter_detail_transactions(self):
        search_text = self.ui.pending_detail_transactions_filter_input.text().lower()
        
        # Show all rows if search text is empty
        if not search_text:
            for row in range(self.pending_detail_transactions_table.rowCount()):
                self.pending_detail_transactions_table.setRowHidden(row, False)
            return
        
        # Iterate through all rows
        for row in range(self.pending_detail_transactions_table.rowCount()):
            match_found = False
            
            # Search through all columns in the row
            for col in range(self.pending_detail_transactions_table.columnCount()):
                item = self.pending_detail_transactions_table.item(row, col)
                if item and search_text in item.text().lower():
                    match_found = True
                    break
            
            # Hide/show row based on whether match was found
            self.pending_detail_transactions_table.setRowHidden(row, not match_found)