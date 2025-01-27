from PyQt6 import QtWidgets, uic, QtGui, QtCore
from connect_db import DatabaseConnection

class CategoriesWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi('./ui/categories.ui', self)
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        
        # Init Dialog(s)
        self.categories_table = self.ui.categories_table
        self.products_table_in_categories = self.ui.products_table_in_categories

        self.categories_table.setSortingEnabled(True)
        self.products_table_in_categories.setSortingEnabled(True)

        # Add a set to keep track of checked SKUs
        self.checked_items = set()

        # Connect Add Category Button
        self.ui.add_category_button.clicked.connect(self.add_category)
        self.ui.edit_category_button.clicked.connect(self.edit_category)
        self.ui.delete_category_button.clicked.connect(self.delete_category)
        self.ui.close_category_button.clicked.connect(lambda: self.close())
        self.ui.clear_category_button.clicked.connect(self.clear_category)
        self.ui.submit_category_button.clicked.connect(self.submit_category)

        # Connect search input to filter function
        self.ui.product_filter_input_in_categories.textChanged.connect(self.show_products_data)
        self.ui.category_filter_input.textChanged.connect(self.show_categories_data)
        
        # Add selected category tracking
        self.current_category_id = None
        
        # Connect table selection
        self.categories_table.itemSelectionChanged.connect(self.on_category_selected)

        # Set table properties
        self.products_table_in_categories.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.products_table_in_categories.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.products_table_in_categories.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        # Connect table item changes to track checkbox changes
        self.products_table_in_categories.itemChanged.connect(self.on_checkbox_changed)

        # Show data for both tables
        self.show_categories_data()
        self.show_products_data()

    def submit_category(self):
        category_name = self.ui.category_name_input.text().strip()
        if not category_name:
            QtWidgets.QMessageBox.warning(self, "Error", "Category name is required")
            return
        
        # Get the checkbox
        checked_items = self.checked_items
        try:
            self.cursor.execute('BEGIN TRANSACTION')

            # Insert category and get the ID
            self.cursor.execute('INSERT INTO categories (category_name) VALUES (?)', (category_name,))
            
            # Get the last inserted category_id
            self.cursor.execute('SELECT last_insert_rowid()')
            category_id = self.cursor.fetchone()[0]

            # Insert products to category
            for sku in checked_items:
                self.cursor.execute('INSERT INTO product_categories_detail (category_id, sku) VALUES (?, ?)', (category_id, sku))

            self.db.commit()
            
            # Reset UI
            self.clear_category()
            self.show_categories_data()
            self.show_products_data()

        except Exception as e:
            self.db.rollback()
            print(f"Error: {e}")

    def clear_category(self):
        self.ui.category_name_input.clear()
        self.ui.category_name_input.setEnabled(True)
        self.ui.product_filter_input_in_categories.clear()
        self.checked_items.clear()
        self.current_category_id = None
        
        # Reset button if it was in update mode
        if self.ui.submit_category_button.text() == "Update Category":
            self.ui.submit_category_button.setText("Submit Category")
            self.ui.submit_category_button.clicked.disconnect()
            self.ui.submit_category_button.clicked.connect(self.submit_category)
        
        # Refresh the products table to show unchecked boxes
        self.show_products_data()

    def toggle_add_edit_categories_and_products(self, mode: bool = True):
        self.ui.category_name_label.setEnabled(mode)
        self.ui.category_name_input.setEnabled(mode)
        self.ui.filter_products_table_in_categories.setEnabled(mode)
        self.ui.product_filter_input_in_categories.setEnabled(mode)
        self.ui.products_table_in_categories.setEnabled(mode)
        self.ui.clear_category_button.setEnabled(mode)
        self.ui.submit_category_button.setEnabled(mode)

    def add_category(self):
        self.clear_category()
        self.ui.submit_category_button.setText("Submit Category")
        self.toggle_add_edit_categories_and_products(True)


    def show_categories_data(self):
        # Temporarily disable sorting
        self.categories_table.setSortingEnabled(False)

        # Clear the table
        self.categories_table.setRowCount(0)

        # Get search text if any
        search_text = self.ui.category_filter_input.text().strip() 

        # Modify SQL query to include search filter
        sql = '''SELECT category_id, category_name 
                    FROM categories 
                    WHERE category_name LIKE ? or category_id LIKE ?
                    LIMIT 100'''
        
        # If no search text, show all categories
        if not search_text:
            sql = 'SELECT category_id, category_name FROM categories LIMIT 100'
            self.cursor.execute(sql)

        else:
            # Add wildcards for LIKE query
            search_pattern = f"%{search_text}%"
            self.cursor.execute(sql, (search_pattern, search_pattern))

        categories_result = self.cursor.fetchall()

        # Display the data in the table
        self.categories_table.setRowCount(len(categories_result))
        self.load_categories_table(categories_result)

        # Re-enable sorting after data is loaded
        self.categories_table.setSortingEnabled(True)   

    def load_categories_table(self, data_result):
        for row_num, category in enumerate(data_result):
            self.categories_table.setItem(row_num, 0, QtWidgets.QTableWidgetItem(str(category[0])))
            self.categories_table.setItem(row_num, 1, QtWidgets.QTableWidgetItem(str(category[1])))

    
    def show_products_data(self):
        # Temporarily disable sorting
        self.products_table_in_categories.setSortingEnabled(False)
        
        # Clear the table
        self.products_table_in_categories.setRowCount(0)

        # Get search text if any
        search_text = self.ui.product_filter_input_in_categories.text().strip()
        
        # Modify SQL query to include search filter
        sql = '''SELECT sku, product_name, price, stock, unit, created_at 
                FROM products 
                WHERE sku LIKE ? OR product_name LIKE ? OR unit LIKE ?
                LIMIT 100'''
        
        # If no search text, show all products
        if not search_text:
            sql = 'SELECT sku, product_name, price, stock, unit, created_at FROM products LIMIT 100'
            self.cursor.execute(sql)
        else:
            # Add wildcards for LIKE query
            search_pattern = f"%{search_text}%"
            self.cursor.execute(sql, (search_pattern, search_pattern, search_pattern,))
            
        products_result = self.cursor.fetchall()
        
        # Display the data in the table
        self.products_table_in_categories.setRowCount(len(products_result))
        self.load_products_table(products_result)
        
        # Re-enable sorting after data is loaded
        self.products_table_in_categories.setSortingEnabled(True)

    def load_products_table(self, data_result):
        # Temporarily disconnect itemChanged signal to prevent duplicate updates
        self.products_table_in_categories.itemChanged.disconnect(self.on_checkbox_changed)
        
        for row_num, product in enumerate(data_result):
            # Create checkbox item for the first column
            checkbox_item = QtWidgets.QTableWidgetItem()
            checkbox_item.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEnabled)
            
            # Check if this SKU was previously checked
            sku = str(product[0])
            checkbox_item.setData(QtCore.Qt.ItemDataRole.UserRole, sku)
            
            if sku in self.checked_items:
                checkbox_item.setCheckState(QtCore.Qt.CheckState.Checked)
            else:
                checkbox_item.setCheckState(QtCore.Qt.CheckState.Unchecked)
            
            self.products_table_in_categories.setItem(row_num, 0, checkbox_item)

            # Shift the product data one column to the right
            for col_num, data in enumerate(product):
                item = QtWidgets.QTableWidgetItem(str(data))
                # Make item not editable
                item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                self.products_table_in_categories.setItem(row_num, col_num + 1, item)
        
        # Reconnect itemChanged signal after loading
        self.products_table_in_categories.itemChanged.connect(self.on_checkbox_changed)

    def on_checkbox_changed(self, item):
        # Only process checkbox column
        if item.column() != 0:
            return
            
        sku = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if item.checkState() == QtCore.Qt.CheckState.Checked:
            self.checked_items.add(sku)
            print(f"Added {sku} to checked items. Current items: {self.checked_items}")
        else:
            self.checked_items.discard(sku)
            print(f"Removed {sku} from checked items. Current items: {self.checked_items}")

    def on_category_selected(self):
        selected_rows = self.categories_table.selectedItems()
        if selected_rows:
            # Get the first selected row
            row = selected_rows[0].row()
            self.current_category_id = int(self.categories_table.item(row, 0).text())
           

    def edit_category(self):
        if not self.current_category_id:
            return
        
        # Enable necessary UI elements
        self.toggle_add_edit_categories_and_products(True)
        
        # Get category data
        self.cursor.execute('SELECT category_name FROM categories WHERE category_id = ?', 
                           (self.current_category_id,))
        category = self.cursor.fetchone()
        
        if category:
            # Set category name (disabled for editing)
            self.ui.category_name_input.setText(category[0])
            self.ui.category_name_input.setEnabled(False)
            
            # Get products in this category
            self.cursor.execute('''SELECT sku 
                                    FROM product_categories_detail 
                                    WHERE category_id = ?''', (self.current_category_id,))
            
            category_products = self.cursor.fetchall()

            # Clear previous checked items
            self.checked_items.clear()
            
            # Add all products from this category to checked items
            for product in category_products:
                self.checked_items.add(str(product[0]))
            
            # Refresh products table to show checked items
            self.show_products_data()
            
            # Change submit button to update
            self.ui.submit_category_button.setText("Update Category")
            self.ui.submit_category_button.clicked.disconnect()
            self.ui.submit_category_button.clicked.connect(self.update_category)

    def update_category(self):
        try:
            self.cursor.execute('BEGIN TRANSACTION')
            
            # Delete existing product relationships
            self.cursor.execute('DELETE FROM product_categories_detail WHERE category_id = ?', 
                              (self.current_category_id,))
            
            # Insert updated product relationships
            for sku in self.checked_items:
                self.cursor.execute('INSERT INTO product_categories_detail (category_id, sku) VALUES (?, ?)', 
                                    (self.current_category_id, sku))
            
            self.db.commit()
            
            # Reset UI
            self.clear_category()
            self.show_categories_data()
            self.show_products_data()
            
            # Reset button
            self.ui.submit_category_button.setText("Submit Category")
            self.ui.submit_category_button.clicked.disconnect()
            self.ui.submit_category_button.clicked.connect(self.submit_category)
            
        except Exception as e:
            self.db.rollback()
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to update category: {str(e)}")

    def delete_category(self):
        if not self.current_category_id:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select a category to delete")
            return
        
        # Get category name for confirmation message
        self.cursor.execute('SELECT category_name FROM categories WHERE category_id = ?', (self.current_category_id,))

        category = self.cursor.fetchone()
        
        # Confirm deletion with user
        reply = QtWidgets.QMessageBox.question(
            self,
            'Confirm Deletion',
            f'Are you sure you want to delete category "{category[0]}"?\nThis action cannot be undone.',
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )
        
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                # Delete product relationships
                self.cursor.execute('DELETE FROM product_categories_detail WHERE category_id = ?', (self.current_category_id,))
                
                # Delete the category
                self.cursor.execute('DELETE FROM categories WHERE category_id = ?', (self.current_category_id,))
                
                self.db.commit()
                
                # Reset UI
                self.clear_category()
                self.show_categories_data()
                self.show_products_data()
                
                # Show success message
                QtWidgets.QMessageBox.information(self, 'Success', 'Category deleted successfully!')
                
            except Exception as e:
                self.db.rollback()
                QtWidgets.QMessageBox.warning(self, 'Error', f"Failed to delete category: {str(e)}")