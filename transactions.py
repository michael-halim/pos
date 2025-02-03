from PyQt6 import QtWidgets, uic, QtGui, QtCore
from connect_db import DatabaseConnection

from helper import format_number, add_prefix, remove_non_digit
from pending_transactions import PendingTransactionsWindow

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
        # Temporarily disconnect itemChanged signal to prevent duplicate updates
        for row_num, product in enumerate(data_result):
            for col_num, data in enumerate(product):
                item = QtWidgets.QTableWidgetItem(str(data))
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

    def close_product(self):
        pass

class TransactionsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi('./ui/transactions.ui', self)
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()

        # Init Dialog
        self.products_in_transaction_dialog = ProductsInTransactionWindow()
        self.pending_transactions_dialog = PendingTransactionsWindow()

        # Connect the product_selected signal to handle_product_selected method
        self.products_in_transaction_dialog.product_selected.connect(self.handle_product_selected)

        # Init Tables
        self.transactions_table = self.ui.transactions_table
        self.history_transactions_table = self.ui.history_transactions_table
        self.wholesale_transactions_table = self.ui.wholesale_transactions_table

        self.transactions_table.setSortingEnabled(True)
        self.history_transactions_table.setSortingEnabled(True)
        self.wholesale_transactions_table.setSortingEnabled(True)

        # Connect the add button to add_transaction method
        self.ui.clear_data_transaction_button.clicked.connect(self.clear_data_transaction)
        self.ui.clear_transaction_button.clicked.connect(self.clear_transaction)
        self.ui.add_transaction_button.clicked.connect(self.add_transaction)
        self.ui.find_sku_transaction_input.clicked.connect(lambda: self.products_in_transaction_dialog.show())
        self.ui.edit_transaction_button.clicked.connect(self.edit_transaction)
        self.ui.delete_transaction_button.clicked.connect(self.delete_transaction)
        self.ui.submit_transaction_button.clicked.connect(self.submit_transaction)
        self.ui.pending_transaction_button.clicked.connect(self.create_pending_transaction)
        self.ui.open_pending_transaction_button.clicked.connect(lambda: self.pending_transactions_dialog.showMaximized())


        # Add selected tracking
        self.current_selected_sku = None
        self.cached_qty = {} # key = <sku>_<unit>, value = (unit_value, stock, price)
        self.cached_transaction_index = {} # key = <sku>_<unit>, value = transaction_table_index


        # Connect table selection
        self.transactions_table.itemSelectionChanged.connect(self.on_transaction_selected)
    
        # Add a flag to track if we're loading items
        self.is_loading_combo = False
        
        # Connect qty combobox to update qty input
        self.ui.qty_transaction_combobox.currentTextChanged.connect(self.on_qty_transaction_combobox_changed)

        # Set table properties
        self.transactions_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.transactions_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        self.wholesale_transactions_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.wholesale_transactions_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        self.history_transactions_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.history_transactions_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

    def show_history_transactions_data(self):
        pass


    def show_wholesale_transactions_data(self):
        pass
    
    def on_transaction_selected(self):
        pass
    

    def clear_transaction(self):
        # Remove All Items from Transactions Table
        self.transactions_table.setRowCount(0)
        self.ui.total_transaction_input.setText(add_prefix('0'))

    def clear_data_transaction(self):
        self.ui.sku_transaction_input.clear()
        self.ui.product_name_transaction_input.clear()
        self.ui.price_transaction_input.clear()
        self.ui.stock_transaction_input.clear()
        self.ui.unit_value_transaction_input.clear()
        self.ui.qty_transaction_input.clear()
        self.ui.qty_transaction_combobox.clear()
        self.ui.discount_rp_transaction_input.clear()
        self.ui.discount_pct_transaction_input.clear()
    
    def add_transaction(self):
        try:
            sku: str = self.ui.sku_transaction_input.text().strip()
            name: str = self.ui.product_name_transaction_input.text().strip()
            price: str = self.ui.price_transaction_input.text().strip()
            qty: str = self.ui.qty_transaction_input.text().strip()
            unit: str = self.ui.qty_transaction_combobox.currentText().strip()
            discount_rp: str = self.ui.discount_rp_transaction_input.text() if self.ui.discount_rp_transaction_input.text() else '0'
            discount_pct: str = self.ui.discount_pct_transaction_input.text() if self.ui.discount_pct_transaction_input.text() else '0'
            amount: str = str(int(price) * int(qty))
            
            # Check transaction index if sku and unit is same
            transaction_index_key = f'{sku}_{unit}'
            if transaction_index_key in self.cached_transaction_index:
                # Update qty, amount
                idx = self.cached_transaction_index[transaction_index_key]
                price: str = remove_non_digit(self.transactions_table.item(idx, 2).text())
                updated_qty: int = int(remove_non_digit(self.transactions_table.item(idx, 3).text())) + int(qty)
                updated_amount: int = int(price) * int(updated_qty)

                self.transactions_table.item(idx, 3).setText(format_number(str(updated_qty)))
                self.transactions_table.item(idx, 7).setText(add_prefix(format_number(str(updated_amount))))

            else:
                current_row = self.transactions_table.rowCount()
                self.transactions_table.insertRow(current_row)
                
                # Add item to transactions table
                items = [
                    QtWidgets.QTableWidgetItem(value) for value in 
                    [sku, name, add_prefix(format_number(price)), format_number(qty), unit, 
                    add_prefix(format_number(discount_rp)), add_prefix(format_number(discount_pct)), 
                    add_prefix(format_number(amount))]
                ]

                font = QtGui.QFont()
                font.setPointSize(16)

                for col, item in enumerate(items):
                    item.setFont(font)
                    self.transactions_table.setItem(current_row, col, item)

                # Add transaction index
                self.cached_transaction_index[transaction_index_key] = current_row

            # Update total amount
            total_amount = int(remove_non_digit(self.ui.total_transaction_input.text())) + int(amount)
            self.ui.total_transaction_input.setText(add_prefix(format_number(str(total_amount))))

            # Clear data transaction
            self.clear_data_transaction()
           
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to add transaction: {str(e)}")

    def edit_transaction(self):
        pass

    def delete_transaction(self):
        pass

    def submit_transaction(self):
        pass

    def create_pending_transaction(self):
        pass

    def open_pending_transaction(self):
        pass

    def handle_product_selected(self, product_data):
         # Fill the form fields with selected product data
        self.ui.sku_transaction_input.setText(product_data['sku'])
        self.ui.product_name_transaction_input.setText(product_data['product_name'])
        self.ui.price_transaction_input.setText(product_data['price'])
        self.ui.stock_transaction_input.setText(product_data['stock'])
        # Set loading flag
        self.is_loading_combo = True
        
        # Clear existing items
        self.ui.qty_transaction_combobox.clear()
        
        sql = '''SELECT u.unit, u.unit_value, p.price, p.stock 
                FROM products p 
                LEFT JOIN units u ON p.sku = u.sku and p.unit = u.unit
                WHERE p.sku = ?'''

        self.cursor.execute(sql, (product_data['sku'],))
        results = self.cursor.fetchall()

        for result in results:
            # key = <sku>_<unit>, value = (unit_value, price)
            cache_key = f'{product_data["sku"]}_{result[0]}'
            self.cached_qty[cache_key] = (result[1], result[2], result[3])
            self.ui.qty_transaction_combobox.addItem(result[0])

        # Reset loading flag
        self.is_loading_combo = False
        
        # Set the unit in combobox
        index = self.ui.qty_transaction_combobox.findText(product_data['unit'])
        if index >= 0:
            self.ui.qty_transaction_combobox.setCurrentIndex(index)
            
        # Set unit value if you have this field
        self.ui.unit_value_transaction_input.setText(product_data['unit_value'])
        
    def on_qty_transaction_combobox_changed(self, text):
        # Skip if we're loading items
        if self.is_loading_combo:
            return
            
        sku = self.ui.sku_transaction_input.text().strip()
        cache_key = f'{sku}_{text}'
        if cache_key in self.cached_qty:
            self.ui.unit_value_transaction_input.setText(str(self.cached_qty[cache_key][0]))
            self.ui.price_transaction_input.setText(str(self.cached_qty[cache_key][1]))
            self.ui.stock_transaction_input.setText(str(self.cached_qty[cache_key][2]))

