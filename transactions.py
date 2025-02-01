from PyQt6 import QtWidgets, uic, QtGui, QtCore
from connect_db import DatabaseConnection

class TransactionsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi('./ui/transactions.ui', self)
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()

        # Init Tables
        self.transactions_table = self.ui.transactions_table
        self.history_transactions_table = self.ui.history_transactions_table
        self.wholesale_transactions_table = self.ui.wholesale_transactions_table

        self.transactions_table.setSortingEnabled(True)
        self.history_transactions_table.setSortingEnabled(True)
        self.wholesale_transactions_table.setSortingEnabled(True)

        # Connect the add button to add_transaction method
        self.ui.add_transaction_button.clicked.connect(self.add_transaction)

        # Add selected supplier tracking
        self.current_selected_sku = None
        

        # Connect table selection
        self.transactions_table.itemSelectionChanged.connect(self.on_transaction_selected)


        # Set table properties
        self.transactions_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.transactions_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        self.wholesale_transactions_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.wholesale_transactions_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        self.history_transactions_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.history_transactions_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)


        # Show data for both tables
        self.show_transactions_data()
    
    def show_transactions_data(self):
        # Temporarily disable sorting
        self.transactions_table.setSortingEnabled(False)
        

        # Clear the table
        self.transactions_table.setRowCount(0)

        
       

        transactions_result = self.cursor.fetchall()


        self.transactions_table.setRowCount(len(transactions_result))
        # self.load_transactions_data(transactions_result)


    def show_history_transactions_data(self):
        pass


    def show_wholesale_transactions_data(self):
        pass
    
    def on_transaction_selected(self):
        pass

    def add_transaction(self):
        try:
            # Add a new row at the end of the table
            current_row = self.transactions_table.rowCount()
            self.transactions_table.insertRow(current_row)
            
            # Create font with size 12
            font = QtGui.QFont()
            font.setPointSize(16)
            
            # Get input values from your UI elements
            sku = "21163528"
            name = "PENSIL 2B P-987 VANCO SEGITIGA DIAMOND"
            price = "10000"
            qty = "100"
            unit = "PCS"
            discount = "10"
            amount = "1000000"
            
            # Create items with the specified font
            items = [
                QtWidgets.QTableWidgetItem(value) for value in 
                [sku, name, price, qty, unit, discount, amount]
            ]
            
            # Set font for each item and add to table
            for col, item in enumerate(items):
                item.setFont(font)
                self.transactions_table.setItem(current_row, col, item)
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to add transaction: {str(e)}")
