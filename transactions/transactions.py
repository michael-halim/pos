from PyQt6 import QtWidgets, uic, QtGui, QtCore
from connect_db import DatabaseConnection
from datetime import datetime, timedelta

from helper import format_number, add_prefix, remove_non_digit
from transactions.pending_transactions import PendingTransactionsWindow
from transactions.products_in_transactions import ProductsInTransactionWindow


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
        self.pending_transactions_dialog.pending_transaction_selected.connect(self.handle_pending_transaction_selected)

        self.ui.filter_transaction_input.textChanged.connect(self.filter_transactions)

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
        self.ui.find_sku_transaction_button.clicked.connect(lambda: self.products_in_transaction_dialog.show())
        self.ui.check_sku_transaction_button.clicked.connect(self.check_sku)
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

        # Set selection behavior to select entire rows
        self.transactions_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.transactions_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)

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
        if self.transactions_table.selectedItems():
            self.current_selected_sku = self.transactions_table.selectedItems()[0].row()

    def clear_transaction(self):
        # Remove All Items from Transactions Table
        self.transactions_table.setRowCount(0)
        self.ui.total_transaction_input.setText(add_prefix('0'))
        self.cached_transaction_index = {}
        self.cached_qty = {}
        self.current_selected_sku = None


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
        # Stop temporary sorting
        self.transactions_table.setSortingEnabled(False)

        try:
            sku: str = self.ui.sku_transaction_input.text().strip()
            name: str = self.ui.product_name_transaction_input.text().strip()
            price: str = remove_non_digit(self.ui.price_transaction_input.text().strip())

            qty: str = remove_non_digit(self.ui.qty_transaction_input.text().strip())
            unit: str = self.ui.qty_transaction_combobox.currentText().strip()
            unit_value: str = remove_non_digit(self.ui.unit_value_transaction_input.text().strip())
            discount_rp: str = remove_non_digit(self.ui.discount_rp_transaction_input.text()) if self.ui.discount_rp_transaction_input.text() else '0'
            discount_pct: str = remove_non_digit(self.ui.discount_pct_transaction_input.text()) if self.ui.discount_pct_transaction_input.text() else '0'
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
                self.transactions_table.item(idx, 8).setText(add_prefix(format_number(str(updated_amount))))

            else:
                current_row = self.transactions_table.rowCount()
                self.transactions_table.insertRow(current_row)
                

                # Add item to transactions table
                items = [
                    QtWidgets.QTableWidgetItem(value) for value in 
                    [sku, name, add_prefix(format_number(price)), format_number(qty), unit, 
                     unit_value, add_prefix(format_number(discount_rp)), 
                     add_prefix(format_number(discount_pct)), add_prefix(format_number(amount))]
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
           
            # After adding new row, reapply filter if there's any
            self.filter_transactions()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to add transaction: {str(e)}")

        finally:
            # Re-enable sorting
            self.transactions_table.setSortingEnabled(True)
            

    def edit_transaction(self):
        # Get selected row

        selected_rows = self.transactions_table.selectedItems()
        if selected_rows:
            self.current_selected_sku = selected_rows[0].row()

            self.ui.add_transaction_button.setText('Update')
            
            # Disconnect existing connections and connect to update function
            self.ui.add_transaction_button.clicked.disconnect()
            self.ui.add_transaction_button.clicked.connect(self.update_transaction)

            # Get sku, unit, unit_value, qty, price, discount_rp, discount_pct, subtotal
            sku = self.transactions_table.item(self.current_selected_sku, 0).text()
            product_name = self.transactions_table.item(self.current_selected_sku, 1).text()
            unit = self.transactions_table.item(self.current_selected_sku, 4).text()

            unit_value = self.transactions_table.item(self.current_selected_sku, 5).text()
            qty = remove_non_digit(self.transactions_table.item(self.current_selected_sku, 3).text())
            price = remove_non_digit(self.transactions_table.item(self.current_selected_sku, 2).text())
            discount_rp = remove_non_digit(self.transactions_table.item(self.current_selected_sku, 6).text())
            discount_pct = remove_non_digit(self.transactions_table.item(self.current_selected_sku, 7).text())

            # Put the data into the form
            self.ui.sku_transaction_input.setText(sku)
            self.ui.product_name_transaction_input.setText(product_name)
            self.ui.price_transaction_input.setText(price)
            self.ui.qty_transaction_input.setText(qty)
            self.ui.qty_transaction_combobox.setCurrentText(unit)
            self.ui.unit_value_transaction_input.setText(unit_value)
            self.ui.discount_rp_transaction_input.setText(discount_rp)
            self.ui.discount_pct_transaction_input.setText(discount_pct)

            # Make sure only qty is editable
            self.ui.qty_transaction_input.setReadOnly(False)
            self.ui.sku_transaction_input.setEnabled(False)
            self.ui.price_transaction_input.setEnabled(False)
            self.ui.product_name_transaction_input.setEnabled(False)
            self.ui.unit_value_transaction_input.setEnabled(False)
            self.ui.discount_rp_transaction_input.setEnabled(False)
            self.ui.discount_pct_transaction_input.setEnabled(False)

    def update_transaction(self):
        if self.current_selected_sku is not None:
            try:
                # Get the updated values
                qty = self.ui.qty_transaction_input.text().strip()
                price = remove_non_digit(self.ui.price_transaction_input.text())
                
                # Calculate new subtotal
                subtotal = int(price) * int(qty)
                
                # Update the row in the table
                self.transactions_table.item(self.current_selected_sku, 3).setText(format_number(qty))
                self.transactions_table.item(self.current_selected_sku, 8).setText(add_prefix(format_number(str(subtotal))))
                
                # Update total amount
                total = 0
                for row in range(self.transactions_table.rowCount()):
                    total += int(remove_non_digit(self.transactions_table.item(row, 8).text()))
                self.ui.total_transaction_input.setText(add_prefix(format_number(str(total))))
                
                # Reset the form
                self.clear_data_transaction()
                
                # Reset button and connection
                self.ui.add_transaction_button.setText('Add')
                self.ui.add_transaction_button.clicked.disconnect()
                self.ui.add_transaction_button.clicked.connect(self.add_transaction)
                
                # Reset selection
                self.current_selected_sku = None
                
                # Re-enable all inputs
                self.ui.sku_transaction_input.setEnabled(True)
                self.ui.discount_rp_transaction_input.setEnabled(True)
                self.ui.discount_pct_transaction_input.setEnabled(True)
                
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to update transaction: {str(e)}")

    def delete_transaction(self):
        pass


    def submit_transaction(self):
        # Get detail transactions from transactions table
        detail_transactions = []
        total_amount = 0
        transaction_id = self.create_transaction_id()
        for row in range(self.transactions_table.rowCount()):
            sku = self.transactions_table.item(row, 0).text()
            price = remove_non_digit(self.transactions_table.item(row, 2).text())
            qty = remove_non_digit(self.transactions_table.item(row, 3).text())
            unit = self.transactions_table.item(row, 4).text()
            unit_value = self.transactions_table.item(row, 5).text()
            discount_rp = remove_non_digit(self.transactions_table.item(row, 6).text())
            discount_pct = remove_non_digit(self.transactions_table.item(row, 7).text())
            subtotal = remove_non_digit(self.transactions_table.item(row, 8).text())

            total_amount += int(subtotal)
            detail_transactions.append((transaction_id, sku, unit, unit_value, qty, price, discount_rp, subtotal))


        payment_remarks = self.ui.remarks_transaction_input.toPlainText().strip()

        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get current timestamp
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert main transaction first
            sql = '''INSERT INTO transactions (transaction_id, total_amount, discount_transaction_id, discount_amount, created_at, payment_remarks) 
                    VALUES (?, ?, ?, ?, ?, ?)'''
            
            self.cursor.execute(sql, (transaction_id, total_amount, 1, discount_rp, current_time, payment_remarks))
            
            # Insert all detail transactions
            sql = '''INSERT INTO detail_transactions 
                    (transaction_id, sku, unit, unit_value, qty, price, discount, sub_total) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
                

            for detail in detail_transactions:
                transaction_id, sku, unit, unit_value, qty, price, discount_rp, subtotal = detail
                
                # Insert detail transaction
                self.cursor.execute(sql, (transaction_id, sku, unit, unit_value, 
                                          qty, price, discount_rp, subtotal))
                
                # Update product stock
                update_sql = 'UPDATE products SET stock = stock - ? WHERE sku = ? AND unit = ?'
                self.cursor.execute(update_sql, (qty, sku, unit))

            # If everything successful, commit the transaction
            self.db.commit()
            
            # Clear the transactions table and total
            self.clear_transaction()
            
            QtWidgets.QMessageBox.information(self, "Success", "Transaction submitted successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to submit transaction: {str(e)}")


    def create_transaction_id(self, is_pending: bool = False) -> str:
        # Get Today's Date
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        # Get count of all transactions today   
        sql = '''SELECT COUNT(*) FROM transactions WHERE created_at >= ? and created_at < ?'''
        self.cursor.execute(sql, (f'{today}', f'{tomorrow}'))

        transaction_count_today = self.cursor.fetchone()[0]
        transaction_count_today += 1

        if is_pending:
            return f'P{datetime.now().strftime("%Y%m%d")}{transaction_count_today:04d}'

        return f'A{datetime.now().strftime("%Y%m%d")}{transaction_count_today:04d}'



    def create_pending_transaction(self):
        transaction_id = self.create_transaction_id(is_pending=True)

        # Get detail transactions from transactions table
        detail_transactions = []
        total_amount = 0
        for row in range(self.transactions_table.rowCount()):
            sku = self.transactions_table.item(row, 0).text()
            price = remove_non_digit(self.transactions_table.item(row, 2).text())
            qty = remove_non_digit(self.transactions_table.item(row, 3).text())
            unit = self.transactions_table.item(row, 4).text()
            unit_value = self.transactions_table.item(row, 5).text()
            discount_rp = remove_non_digit(self.transactions_table.item(row, 6).text())
            discount_pct = remove_non_digit(self.transactions_table.item(row, 7).text())
            subtotal = remove_non_digit(self.transactions_table.item(row, 8).text())

            total_amount += int(subtotal)
            detail_transactions.append((transaction_id, sku, unit, unit_value, qty, price, discount_rp, subtotal))


        payment_remarks = self.ui.remarks_transaction_input.toPlainText().strip()

        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get current timestamp
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert main transaction first
            sql = '''INSERT INTO pending_transactions (transaction_id, total_amount, discount_transaction_id, discount_amount, created_at, payment_remarks) 
                    VALUES (?, ?, ?, ?, ?, ?)'''
            

            self.cursor.execute(sql, (transaction_id, total_amount, 1, discount_rp, current_time, payment_remarks))
            
            # Insert all detail transactions
            sql = '''INSERT INTO pending_detail_transactions 
                    (transaction_id, sku, unit, unit_value, qty, price, discount, sub_total) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
                

            for detail in detail_transactions:
                transaction_id, sku, unit, unit_value, qty, price, discount_rp, subtotal = detail
                
                # Insert detail transaction
                self.cursor.execute(sql, (transaction_id, sku, unit, unit_value, 
                                          qty, price, discount_rp, subtotal))
                

            # If everything successful, commit the transaction
            self.db.commit()
            
            # Clear the transactions table and total
            self.clear_transaction()
            
            QtWidgets.QMessageBox.information(self, "Success", "Transaction pending successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to create pending transaction: {str(e)}")

    def handle_product_selected(self, product_data):
         # Fill the form fields with selected product data
        self.ui.sku_transaction_input.setText(product_data['sku'])
        self.ui.product_name_transaction_input.setText(product_data['product_name'])
        self.ui.price_transaction_input.setText(add_prefix(format_number(str(product_data['price']))))
        self.ui.stock_transaction_input.setText(format_number(str(product_data['stock'])))
        self.ui.unit_value_transaction_input.setText(format_number(str(product_data['unit_value'])))

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
            

    def check_sku(self):
        sku = self.ui.sku_transaction_input.text().strip()
        sql = 'SELECT product_name, price, stock FROM products WHERE sku = ?'
        self.cursor.execute(sql, (sku,))
        result = self.cursor.fetchone()

        if result:
            self.ui.product_name_transaction_input.setText(result[0])
            self.ui.price_transaction_input.setText(add_prefix(format_number(str(result[1]))))
            self.ui.stock_transaction_input.setText(format_number(str(result[2])))
            
            # Set loading flag
            self.is_loading_combo = True
            
            # Clear existing items
            self.ui.qty_transaction_combobox.clear()
            
            sql = '''SELECT u.unit, u.unit_value, p.price, p.stock 
                    FROM products p 
                    LEFT JOIN units u ON p.sku = u.sku and p.unit = u.unit
                    WHERE p.sku = ?'''

            self.cursor.execute(sql, (sku,))
            results = self.cursor.fetchall()


            for result in results:
                # key = <sku>_<unit>, value = (unit_value, price)
                cache_key = f'{sku}_{result[0]}'
                self.cached_qty[cache_key] = (result[1], result[2], result[3])
                self.ui.qty_transaction_combobox.addItem(result[0])


            # Reset loading flag
            self.is_loading_combo = False
            
            # Set the unit in combobox
            self.ui.qty_transaction_combobox.setCurrentIndex(0)
            
            self.ui.unit_value_transaction_input.setText(format_number(str(results[0][1])))


        else:
            QtWidgets.QMessageBox.critical(self, "Error", "Product not found")


    def handle_pending_transaction_selected(self, pending_transaction_data):
        results = []
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            sql = '''SELECT pdt.sku, p.product_name, pdt.price, pdt.qty, pdt.unit, pdt.unit_value, pdt.discount, pdt.sub_total 
                    FROM pending_detail_transactions pdt
                    JOIN products p ON p.sku = pdt.sku and p.unit = pdt.unit
                    WHERE pdt.transaction_id = ?'''
            
            self.cursor.execute(sql, (pending_transaction_data['transaction_id'],))

            results = self.cursor.fetchall()

            # Delete pending detail transactions
            sql = '''DELETE FROM pending_detail_transactions WHERE transaction_id = ?'''

            self.cursor.execute(sql, (pending_transaction_data['transaction_id'],))

            # Delete pending transactions
            sql = '''DELETE FROM pending_transactions WHERE transaction_id = ?'''

            self.cursor.execute(sql, (pending_transaction_data['transaction_id'],))

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to add transaction: {str(e)}")
        

        # put the data into transactions table
        subtotal = 0
        for result in results:
            current_row = self.transactions_table.rowCount()
            self.transactions_table.insertRow(current_row)
            subtotal += int(result[7])
            items = [
                QtWidgets.QTableWidgetItem(value) for value in 
                [result[0], result[1], add_prefix(format_number(result[2])), format_number(result[3]), result[4], 
                 format_number(result[5]), add_prefix(format_number(result[6])), add_prefix(format_number(result[6])), 
                add_prefix(format_number(result[7]))]
            ]

            font = QtGui.QFont()
            font.setPointSize(16)

            for col, item in enumerate(items):
                item.setFont(font)
                self.transactions_table.setItem(current_row, col, item)
        
        self.ui.total_transaction_input.setText(add_prefix(format_number(str(subtotal))))

    
    def on_qty_transaction_combobox_changed(self, text):
        # Skip if we're loading items
        if self.is_loading_combo:
            return
            
        sku = self.ui.sku_transaction_input.text().strip()
        cache_key = f'{sku}_{text}'
        if cache_key in self.cached_qty:
            self.ui.unit_value_transaction_input.setText(format_number(str(self.cached_qty[cache_key][0])))
            self.ui.price_transaction_input.setText(add_prefix(format_number(str(self.cached_qty[cache_key][1]))))
            self.ui.stock_transaction_input.setText(format_number(str(self.cached_qty[cache_key][2])))


    def filter_transactions(self):
        search_text = self.ui.filter_transaction_input.text().lower()
        
        # Show all rows if search text is empty
        if not search_text:
            for row in range(self.transactions_table.rowCount()):
                self.transactions_table.setRowHidden(row, False)
            return
        
        # Iterate through all rows
        for row in range(self.transactions_table.rowCount()):
            match_found = False
            
            # Search through all columns in the row
            for col in range(self.transactions_table.columnCount()):
                item = self.transactions_table.item(row, col)
                if item and search_text in item.text().lower():
                    match_found = True
                    break
            
            # Hide/show row based on whether match was found
            self.transactions_table.setRowHidden(row, not match_found)