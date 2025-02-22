from PyQt6 import QtWidgets, uic, QtGui, QtCore
from connect_db import DatabaseConnection
from generals.build import resource_path

class AddEditProductWindow(QtWidgets.QWidget):
    # Add signal definition at class level
    product_added = QtCore.pyqtSignal()
    product_updated = QtCore.pyqtSignal()  # New signal for updates

    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/add_edit_product.ui'), self)
        
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()

        # Initialize error labels
        self.error_labels = {
            'sku': self.ui.sku_error_message,
            'product_name': self.ui.product_name_error_message,
            'cost_price': self.ui.cost_price_error_message,
            'price': self.ui.price_error_message,
            'stock': self.ui.stock_error_message,
            'unit': self.ui.unit_error_message,
            'unit_value': self.ui.unit_value_error_message
        }

        # Set error labels initially hidden
        for label in self.error_labels.values():
            label.setVisible(False)
            label.setStyleSheet('color: red;')

        # Connect the button to the function
        self.ui.submit_add_edit_product_button.clicked.connect(lambda: self.add_product())
        self.ui.cancel_add_edit_product_button.clicked.connect(lambda: self.close())

        self.is_edit_mode = False
        self.current_sku = None

    def validate_input(self):
        is_valid = True
        
        # Reset all error messages
        for label in self.error_labels.values():
            label.setVisible(False)

        # Validate SKU
        if not self.ui.sku_input.text().strip():
            self.error_labels['sku'].setText('SKU cannot be empty')
            self.error_labels['sku'].setVisible(True)
            self.ui.sku_input.setFocus()
            is_valid = False

        # Validate Product Name
        if not self.ui.product_name_input.text().strip():
            self.error_labels['product_name'].setText('Product name cannot be empty')
            self.error_labels['product_name'].setVisible(True)
            if is_valid:  # Only set focus if no previous error
                self.ui.product_name_input.setFocus()
            is_valid = False

        # Validate Unit
        if not self.ui.unit_input.text().strip():
            self.error_labels['unit'].setText('Unit cannot be empty')
            self.error_labels['unit'].setVisible(True)
            if is_valid:
                self.ui.unit_input.setFocus()
            is_valid = False

        # Validate Unit Value
        unit_value = self.ui.unit_value_input.text().strip()
        if not unit_value or not unit_value.isdigit():
            self.error_labels['unit_value'].setText('Please enter a valid unit value')
            self.error_labels['unit_value'].setVisible(True)
            if is_valid:
                self.ui.unit_value_input.setFocus()
            is_valid = False

        return is_valid

    def add_product(self):
        # Validate input before proceeding
        if not self.validate_input():
            return

        # Get the data from the input fields
        sku = self.ui.sku_input.text().strip()
        product_name = self.ui.product_name_input.text().strip()
        cost_price = self.ui.cost_price_input.text().replace('Rp.', '').strip()
        price = self.ui.price_input.text().replace('Rp.', '').strip()
        stock = self.ui.stock_input.text().strip()
        remarks = self.ui.remarks_input.toPlainText().strip()
        unit = self.ui.unit_input.text().strip()
        unit_value = self.ui.unit_value_input.text().strip()
    
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')
            
            # Insert product
            sql_insert_products = '''INSERT INTO products (sku, product_name, cost_price, price, stock, remarks, unit) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?)'''

            self.cursor.execute(sql_insert_products, (sku, product_name, cost_price, price, stock, remarks, unit))
            
            # Insert unit
            sql_insert_units = '''INSERT INTO units (sku, unit, unit_value) VALUES (?, ?, ?)'''

            self.cursor.execute(sql_insert_units, (sku, unit, unit_value))


            # Commit changes if everything is successful
            self.db.commit()

            # Emit signal after successful addition
            self.product_added.emit()

        except Exception as e:
            # Rollback the transaction in case of error
            self.db.rollback()
            print(f"Transaction failed: {e}")

        # Clear the input fields
        self.clear_product_input()
        
        # Close the dialog
        self.close()

    def clear_product_input(self):
        self.ui.sku_input.clear()
        self.ui.product_name_input.clear()
        self.ui.cost_price_input.clear()
        self.ui.price_input.clear()
        self.ui.stock_input.clear()
        self.ui.remarks_input.clear()
        self.ui.unit_input.clear()

    def setup_edit_mode(self, sku, unit):
        """Configure window for editing an existing product"""

        self.is_edit_mode = True
        self.current_sku = sku
        
        # Get product data
        self.cursor.execute('''
            SELECT p.sku, p.product_name, p.cost_price, p.price, p.stock, p.unit, p.remarks, u.unit_value 
            FROM products p 
            LEFT JOIN units u ON p.sku = u.sku and p.unit = u.unit
            WHERE p.sku = ? and p.unit = ?
        ''', (sku, unit))
        product_result = self.cursor.fetchone()
        
        if product_result:
            # Populate fields with safe conversion
            self.ui.sku_input.setText(str(product_result[0]))
            self.ui.product_name_input.setText(str(product_result[1]))
            
            # Safe conversion for numeric fields
            self.ui.cost_price_input.setValue(int(product_result[2]) if product_result[2] else 0)
            self.ui.price_input.setValue(int(product_result[3]) if product_result[3] else 0)
            self.ui.stock_input.setValue(int(product_result[4]) if product_result[4] else 0)
            self.ui.unit_input.setText(str(product_result[5]) if product_result[5] else '')
            self.ui.remarks_input.setPlainText(str(product_result[6]) if product_result[6] else '')
            self.ui.unit_value_input.setValue(int(product_result[7]) if product_result[7] else 0)
            
            # Disable SKU and product name fields in edit mode
            self.ui.sku_input.setEnabled(False)
            self.ui.product_name_input.setEnabled(False)
            
            # Change button text
            self.ui.submit_add_edit_product_button.setText("Update Product")
            self.ui.submit_add_edit_product_button.clicked.disconnect()
            self.ui.submit_add_edit_product_button.clicked.connect(self.update_product)

    def update_product(self):
        """Handle product updates"""
        if not self.validate_input():
            return

        try:
            self.cursor.execute('BEGIN TRANSACTION')
            
            # Update product
            sql_update_products = '''UPDATE products 
                                    SET cost_price = ?, price = ?, stock = ?, 
                                        remarks = ?, unit = ?
                                    WHERE sku = ? and unit = ?'''
            
            self.cursor.execute(sql_update_products, (
                self.ui.cost_price_input.text().replace('Rp.', '').strip(),
                self.ui.price_input.text().replace('Rp.', '').strip(),
                self.ui.stock_input.text().strip(),
                self.ui.remarks_input.toPlainText().strip(),
                self.ui.unit_input.text().strip(),
                self.current_sku,
                self.ui.unit_input.text().strip()
            ))
            
            # Update unit
            sql_update_units = '''UPDATE units 
                                SET unit = ?, unit_value = ?
                                WHERE sku = ? and unit = ?'''
            
            self.cursor.execute(sql_update_units, (
                self.ui.unit_input.text().strip(),
                self.ui.unit_value_input.text().strip(),
                self.current_sku,
                self.ui.unit_input.text().strip()
            ))

            self.db.commit()
            self.product_updated.emit()
            self.close()

        except Exception as e:
            self.db.rollback()
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to update product: {str(e)}")

    def reset_form(self):
        """Reset form to add mode"""
        self.is_edit_mode = False
        self.current_sku = None
        self.clear_product_input()
        self.ui.sku_input.setEnabled(True)
        self.ui.product_name_input.setEnabled(True)
        self.ui.submit_add_edit_product_button.setText("Add Product")
        self.ui.submit_add_edit_product_button.clicked.disconnect()
        self.ui.submit_add_edit_product_button.clicked.connect(self.add_product)


class ProductsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/products.ui'), self)
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        
        # Init Dialog(s)
        self.add_product_dialog = AddEditProductWindow()
        self.products_table = self.ui.products_table
        self.products_table.setSortingEnabled(True)
        
        self.show_data()

        # Connect the signal to refresh table
        self.add_product_dialog.product_added.connect(self.show_data)
        self.add_product_dialog.product_updated.connect(self.show_data)

        # Connect the button to the function
        self.ui.add_product_button.clicked.connect(lambda: self.add_product_dialog.show())

        # Connect search input to filter function
        self.ui.products_filter_input.textChanged.connect(self.show_data)
    
    def show_data(self):
        # Temporarily disable sorting
        self.products_table.setSortingEnabled(False)
        
        # Clear the table
        self.products_table.setRowCount(0)

        # Get search text if any
        search_text = self.ui.products_filter_input.text().strip()
        
        # Modify SQL query to include search filter
        sql = '''SELECT sku, product_name, cost_price, price, stock, unit, remarks 
                FROM products 
                WHERE sku LIKE ? OR product_name LIKE ? OR unit LIKE ? OR remarks LIKE ?
                LIMIT 100'''
        
        # If no search text, show all products
        if not search_text:
            sql = 'SELECT sku, product_name, cost_price, price, stock, unit, remarks FROM products LIMIT 100'
            self.cursor.execute(sql)
        else:
            # Add wildcards for LIKE query
            search_pattern = f"%{search_text}%"
            self.cursor.execute(sql, (search_pattern, search_pattern, search_pattern, search_pattern))
            
        products_result = self.cursor.fetchall()
        
        # Display the data in the table
        self.products_table.setRowCount(len(products_result))
        self.load_table(products_result)
        
        # Re-enable sorting after data is loaded
        self.products_table.setSortingEnabled(True)
    
    def load_table(self, data_result):
        for row_num, product in enumerate(data_result):
            action_edit = QtGui.QAction('Edit', self)
            action_delete = QtGui.QAction('Delete', self)
            
            # Connect edit action
            action_edit.triggered.connect(lambda checked, sku=product[0], unit=product[5]: self.edit_product(sku, unit))
            action_delete.triggered.connect(lambda checked, sku=product[0], unit=product[5]: self.delete_product(sku, unit))

            # Create QMenu
            menu = QtWidgets.QMenu(self)
            menu.addActions([action_edit, action_delete])

            option_btn = QtWidgets.QPushButton(self)
            option_btn.setText('Option')
            option_btn.setMenu(menu)
            
            row_data = [p for p in product] + [option_btn]

            for col_num, data in enumerate(row_data):
                if col_num == 7:  # Options column
                    self.ui.products_table.setCellWidget(row_num, col_num, data)
                else:
                    self.ui.products_table.setItem(row_num, col_num, QtWidgets.QTableWidgetItem(str(data)))


    def edit_product(self, sku, unit):
        """Open edit window for selected product"""
        self.add_product_dialog.reset_form()
        self.add_product_dialog.setup_edit_mode(sku, unit)
        self.add_product_dialog.show()


    def delete_product(self, sku, unit):
        if not sku:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select a product to delete")
            return
        
        # Get product name for confirmation message
        self.cursor.execute('SELECT product_name FROM products WHERE sku = ?', (sku,))
        product = self.cursor.fetchone()

        # Confirm deletion with user
        reply = QtWidgets.QMessageBox.question(
            self,
            'Confirm Deletion',
            f'Are you sure you want to delete product "{product[0]}"?\nThis action cannot be undone.',
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                self.cursor.execute('DELETE FROM products WHERE sku = ? and unit = ?', (sku, unit))

                self.cursor.execute('DELETE FROM units WHERE sku = ? and unit = ?', (sku, unit))

                self.db.commit()
                self.show_data()

            except Exception as e:
                self.db.rollback()
                QtWidgets.QMessageBox.warning(self, "Error", f"Failed to delete product: {str(e)}")