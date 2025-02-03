from PyQt6 import QtWidgets, uic, QtGui, QtCore
from connect_db import DatabaseConnection

from helper import format_number, add_prefix, remove_non_digit

class PendingTransactionsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi('./ui/pending_transactions.ui', self)
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()

        # Init Tables
        self.pending_transactions_table = self.ui.pending_transactions_table
        self.pending_detail_transactions_table = self.ui.pending_detail_transactions_table

        self.pending_transactions_table.setSortingEnabled(True)
        self.pending_detail_transactions_table.setSortingEnabled(True)

        # Connect Add Supplier Button
        self.ui.add_pending_transactions_button.clicked.connect(self.add_pending_transaction)
        self.ui.close_pending_transactions_button.clicked.connect(lambda: self.close())

        # Connect search input to filter function
        self.ui.pending_transactions_filter_input.textChanged.connect(self.show_pending_transactions_data)
        
        # Add selected supplier tracking
        self.current_pending_transaction_id = None

        # Connect table selection
        self.pending_transactions_table.itemSelectionChanged.connect(self.on_pending_transaction_selected)

        # Set selection behavior to select entire rows
        self.pending_transactions_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.pending_transactions_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)

        self.pending_detail_transactions_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.pending_detail_transactions_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)

        # Set table properties
        self.pending_transactions_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.pending_transactions_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        self.pending_detail_transactions_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.pending_detail_transactions_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        self.show_pending_transactions_data()
        self.show_detail_pending_transactions_data()
    
    def show_pending_transactions_data(self):
        # Temporarily disable sorting
        self.pending_transactions_table.setSortingEnabled(False)
        
        # Clear the table
        self.pending_transactions_table.setRowCount(0)

        # Get search text if any
        search_text = self.ui.pending_transactions_filter_input.text().strip()

        # Modify SQL query to include search filter
        sql = '''SELECT transaction_id, total_amount, created_at, payment_remarks 
                FROM pending_transactions 
                WHERE transaction_id LIKE ? OR total_amount LIKE ? OR created_at LIKE ? OR payment_remarks LIKE ?'''

        # If no search text, show all suppliers 
        if not search_text:
            sql = 'SELECT transaction_id, total_amount, created_at, payment_remarks FROM pending_transactions'
            self.cursor.execute(sql)

        else:
            # Add wildcards for LIKE query

            search_pattern = f"%{search_text}%"
            self.cursor.execute(sql, (search_pattern, search_pattern, search_pattern, search_pattern))

        pending_transactions_result = self.cursor.fetchall()

        self.pending_transactions_table.setRowCount(len(pending_transactions_result))

        # Get filtered data
        self.load_pending_transactions_data(pending_transactions_result)

        self.pending_transactions_table.setSortingEnabled(True)

    

    def load_pending_transactions_data(self, pending_transactions):
        font = QtGui.QFont()
        font.setPointSize(14)
        for row, pt in enumerate(pending_transactions):
            for col, value in enumerate(pt):
                item = QtWidgets.QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                item.setFont(font)
                if col == 1:
                    item.setText(add_prefix(format_number(value)))
                self.pending_transactions_table.setItem(row, col, item)

    
    def add_pending_transaction(self):
        pass

    def on_pending_transaction_selected(self):
        selected_rows = self.pending_transactions_table.selectedItems()
        if selected_rows:
            # Get the first selected row
            row = selected_rows[0].row()
            self.current_pending_transaction_id = self.pending_transactions_table.item(row, 0).text()
            # Show details when a transaction is selected
            self.show_detail_pending_transactions_data()

    def show_detail_pending_transactions_data(self):
        # Temporarily disable sorting
        self.pending_detail_transactions_table.setSortingEnabled(False)

        # Clear the details table
        self.pending_detail_transactions_table.setRowCount(0)
        
        if not self.current_pending_transaction_id:
            return

        # Query to get transaction details
        sql = '''
            SELECT p.sku, p.product_name, pdt.price, pdt.qty, pdt.unit, 0, 0, pdt.sub_total
            FROM pending_detail_transactions pdt
            JOIN products p ON p.sku = pdt.sku and p.unit = pdt.unit
            WHERE pdt.transaction_id = ?

        '''
        
        self.cursor.execute(sql, (self.current_pending_transaction_id,))
        details_result = self.cursor.fetchall()
        
        # Set row count and populate data
        self.pending_detail_transactions_table.setRowCount(len(details_result))
        
        self.load_detail_pending_transactions_data(details_result)

        self.pending_detail_transactions_table.setSortingEnabled(True)

    def load_detail_pending_transactions_data(self, details_result):
        font = QtGui.QFont()
        font.setPointSize(14)


        for row, detail in enumerate(details_result):
            for col, value in enumerate(detail):
                item = QtWidgets.QTableWidgetItem(str(value))
                item.setFont(font)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                # Format price and subtotal columns
                if col == 3:
                    item.setText(format_number(value))
                elif col in [2, 7]:
                    item.setText(add_prefix(format_number(value)))
                    
                self.pending_detail_transactions_table.setItem(row, col, item)