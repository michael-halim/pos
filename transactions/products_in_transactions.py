from PyQt6 import QtWidgets, uic, QtGui, QtCore
from connect_db import DatabaseConnection

from helper import format_number, add_prefix, remove_non_digit

class ProductsInTransactionWindow(QtWidgets.QWidget):
    # Add signal to communicate with main window
    product_selected = QtCore.pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()

        self.ui = uic.loadUi('./ui/products_in_transactions.ui', self)
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()

        # Init Table
        self.products_in_transactions_table = self.ui.products_in_transactions_table
        self.products_in_transactions_table.setSortingEnabled(True)
        
        # Init Button
        self.ui.add_products_in_transactions_button.clicked.connect(self.send_product_data)
        self.ui.close_products_in_transactions_button.clicked.connect(lambda: self.close())

        # Connect search input to filter function
        self.ui.filter_products_in_transactions_input.textChanged.connect(self.show_products_in_transactions_data)

        # Add selected product tracking
        self.current_product_in_transaction = (None, None)
        
        # Set selection behavior to select entire rows
        self.products_in_transactions_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.products_in_transactions_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)

        # Set table properties
        self.products_in_transactions_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.products_in_transactions_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        # Connect table selection
        self.products_in_transactions_table.itemSelectionChanged.connect(self.on_product_selected)
        
        self.show_products_in_transactions_data()

    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        # Reset the current selection
        self.current_product_in_transaction = (None, None)
        # Refresh the data
        self.show_products_in_transactions_data()

    def show(self):
        """Override show to ensure data is refreshed"""
        super().show()
        # Reset the current selection
        self.current_product_in_transaction = (None, None)
        # Refresh the data
        self.show_products_in_transactions_data()

    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        # Reset the current selection
        self.current_product_in_transaction = (None, None)
        # Refresh the data
        self.show_products_in_transactions_data()

    def show_products_in_transactions_data(self):
        # Temporarily disable sorting
        self.products_in_transactions_table.setSortingEnabled(False)
        
        # Clear the table
        self.products_in_transactions_table.setRowCount(0)

        # Get search text if any
        search_text: str = self.ui.filter_products_in_transactions_input.text().strip()
        
        # Modify SQL query to include search filter
        sql: str = '''SELECT p.sku, p.product_name, p.price, p.stock, p.unit, u.unit_value, p.created_at 
                FROM products p 
                LEFT JOIN units u ON p.sku = u.sku and p.unit = u.unit  
                WHERE p.sku LIKE ? OR p.product_name LIKE ? OR p.unit LIKE ?
                LIMIT 100'''
        
        # If no search text, show all products
        if not search_text:
            sql: str = '''SELECT p.sku, p.product_name, p.price, p.stock, p.unit, u.unit_value, p.created_at 
                    FROM products p 
                    LEFT JOIN units u ON p.sku = u.sku and p.unit = u.unit 
                    LIMIT 100'''
            
            self.cursor.execute(sql)
        else:
            # Add wildcards for LIKE query
            search_pattern = f"%{search_text}%"
            self.cursor.execute(sql, (search_pattern, search_pattern, search_pattern,))
            
        products_result = self.cursor.fetchall()
        
        # Display the data in the table
        self.products_in_transactions_table.setRowCount(len(products_result))
        self.load_products_in_transactions_table(products_result)
        
        # Re-enable sorting after data is loaded
        self.products_in_transactions_table.setSortingEnabled(True)

    def on_product_selected(self):
        selected_rows = self.products_in_transactions_table.selectedItems()
        if selected_rows:
            # Get the sku and unit as tuple (because both are unique)
            row = selected_rows[0].row()
            self.current_product_in_transaction = (self.products_in_transactions_table.item(row, 0).text(), 
                                                   self.products_in_transactions_table.item(row, 4).text())
            

    def load_products_in_transactions_table(self, data_result):
        font = QtGui.QFont()
        font.setPointSize(16)

        for row_num, product in enumerate(data_result):
            for col_num, data in enumerate(product):
                # Col 2 = Price, Col 3 = Stock, Col 5 = Unit Value
                if col_num == 2:
                    item = QtWidgets.QTableWidgetItem(add_prefix(format_number(str(data))))

                elif col_num == 3:
                    # Stock can be negative
                    item = QtWidgets.QTableWidgetItem(format_number(str(data)))
                    if int(data) < 0:
                        item = QtWidgets.QTableWidgetItem(f'-{format_number(str(abs(int(data))))}')
                        item.setForeground(QtGui.QColor('red'))

                elif col_num == 5:
                    item = QtWidgets.QTableWidgetItem(format_number(str(data)))
              
                else:
                    item = QtWidgets.QTableWidgetItem(str(data))

                item.setFont(font)

                # Make item not editable
                item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)

                self.products_in_transactions_table.setItem(row_num, col_num, item)
        
    def send_product_data(self):
        selected_rows = self.products_in_transactions_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            
            # Create dictionary with product details
            product_data = {
                'sku': self.products_in_transactions_table.item(row, 0).text(),
                'product_name': self.products_in_transactions_table.item(row, 1).text(),
                'price': self.products_in_transactions_table.item(row, 2).text(),
                'stock': self.products_in_transactions_table.item(row, 3).text(),
                'unit': self.products_in_transactions_table.item(row, 4).text(),
                'unit_value': self.products_in_transactions_table.item(row, 5).text()
            }
            
            # Emit signal with product data
            self.product_selected.emit(product_data)
            self.close()
