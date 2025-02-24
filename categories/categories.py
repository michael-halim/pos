from PyQt6 import QtWidgets, uic, QtGui, QtCore
from connect_db import DatabaseConnection
from generals.build import resource_path
from .services.categories_services import CategoriesService
from .models.categories_models import CategoriesTableModel, ProcuctsTableModel
from generals.fonts import POSFonts
from helper import add_prefix, format_number, remove_non_digit
from generals.widget import create_checkbox_item
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS
from generals.message_box import POSMessageBox

class CategoriesWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        # Init Services
        self.categories_service = CategoriesService()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/categories.ui'), self)
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        
        # Init Tables
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
        
        # Set selection behavior to select entire rows
        self.categories_table.setSelectionBehavior(SELECT_ROWS)
        self.categories_table.setSelectionMode(SINGLE_SELECTION)
        self.products_table_in_categories.setSelectionBehavior(SELECT_ROWS)
        self.products_table_in_categories.setSelectionMode(SINGLE_SELECTION)

        self.categories_table.setEditTriggers(NO_EDIT_TRIGGERS)
        self.products_table_in_categories.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties
        self.categories_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.categories_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        self.products_table_in_categories.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.products_table_in_categories.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        # Show data for both tables
        self.show_categories_data()
        self.show_products_data()


    def edit_category(self):
        selected_row = self.categories_table.selectedItems()
        if not selected_row:
            POSMessageBox.error(self, title='Error', message="Please select a role to edit")
            return
        
        self.toggle_add_edit_categories_and_products(True)

        row = selected_row[0].row()
        category_id = self.categories_table.item(row, 0).text()

        # Get category data
        category_result = self.categories_service.get_category_by_id(category_id)

        # Set category data
        self.set_category_form_data(category_result.data)

        # Get all products
        all_products = self.categories_service.get_products()

        # Get selected products by category id
        products_selected = self.categories_service.get_selected_products_by_category_id(category_id)

        # Set products table data
        self.set_products_table_data(all_products.data, products_selected.data)

        self.ui.submit_category_button.setText('Update')
        self.ui.submit_category_button.clicked.disconnect()
        self.ui.submit_category_button.clicked.connect(self.update_category)
        

    def update_category(self):
        category_form_data: CategoriesTableModel = self.get_category_form_data()
        category_id = self.ui.category_id_input.text().strip()

        if not category_form_data.category_name:
            POSMessageBox.error(self, title='Error', message="Category name is required")
            return
        
        past_products_result = self.categories_service.get_selected_products_by_category_id(category_id)
        current_products = self.get_selected_products_table_data()

        added_data = current_products - past_products_result.data
        deleted_data = past_products_result.data - current_products

        result = self.categories_service.update_category(category_form_data, added_data, deleted_data)
        if result.success:
            POSMessageBox.info(self, title='Success', message=result.message)

            self.categories_table.setRowCount(0)
            self.products_table_in_categories.setRowCount(0)
            
            self.clear_category()

            self.show_categories_data()
            self.show_products_data()
        else:
            POSMessageBox.error(self, title='Error', message=result.message)

        self.ui.submit_category_button.setText('Submit')
        self.ui.submit_category_button.clicked.disconnect()
        self.ui.submit_category_button.clicked.connect(self.submit_category)


    def delete_category(self):
        selected_row = self.categories_table.selectedItems()
        if not selected_row:
            POSMessageBox.error(self, title='Error', message="Please select a category to delete")
            return  
        
        category_name = self.ui.category_name_input.text().strip()
        confirm = POSMessageBox.confirm(
                        self, title='Confirm Deletion', 
                        message=f'Are you sure you want to delete {category_name}?')

        if confirm:
            row = selected_row[0].row()
            category_id = self.categories_table.item(row, 0).text()

            result = self.categories_service.delete_category_by_id(category_id)
            if result.success:
                POSMessageBox.info(self, title='Success', message=result.message)

                self.categories_table.setRowCount(0)
                self.products_table_in_categories.setRowCount(0)
                
                self.clear_category()
                
                self.show_categories_data()
                self.show_products_data()

        else:
            POSMessageBox.error(self, title='Error', message=result.message)


    def submit_category(self):
        category_form_data: CategoriesTableModel = self.get_category_form_data()
        if not category_form_data.category_name:
            POSMessageBox.error(self, title='Error', message="Category name is required")
            return
        
        selected_products: set[str] = self.get_selected_products_table_data()

        result = self.categories_service.submit_category(category_form_data, selected_products)
        if result.success:
            POSMessageBox.info(self, title='Success', message=result.message)
            
            self.categories_table.setRowCount(0)
            self.products_table_in_categories.setRowCount(0)

            self.clear_category()

            self.show_categories_data()
            self.show_products_data()

        else:
            POSMessageBox.error(self, title='Error', message=result.message)


    def add_category(self):
        self.clear_category()
        self.ui.submit_category_button.setText("Submit")
        self.toggle_add_edit_categories_and_products(True)
    
    # Overrides
    # ===============
    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        # Refresh the data
        self.show_categories_data()


    def show(self):
        """Override show to ensure data is refreshed"""
        super().show()
        # Refresh the data
        self.show_categories_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        # Refresh the data
        self.show_categories_data()


    # Setters
    # ===============
    def set_categories_table_data(self, data: list[CategoriesTableModel]):
        # Clear the table
        self.categories_table.setRowCount(0)

        for category in data:
            current_row = self.categories_table.rowCount()
            self.categories_table.insertRow(current_row)

            table_items =  [ 
                QtWidgets.QTableWidgetItem(str(category.category_id)),
                QtWidgets.QTableWidgetItem(category.category_name),
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.categories_table.setItem(current_row, col, item)

    
    def set_products_table_data(self, data: list[ProcuctsTableModel], checked_products: set[str]):
        # Clear the table
        self.products_table_in_categories.setRowCount(0)

        for product in data:
            current_row = self.products_table_in_categories.rowCount()
            self.products_table_in_categories.insertRow(current_row)
            sku = product.sku
            checkbox_item = create_checkbox_item(sku, is_editable=True, size=22)
            
            # Checked if product is in checked_products
            is_checked = QtCore.Qt.CheckState.Unchecked
            if sku in checked_products:
                is_checked = QtCore.Qt.CheckState.Checked

            checkbox_item.setCheckState(is_checked)
            
            self.products_table_in_categories.setItem(current_row, 0, checkbox_item)

            table_items =  [ 
                QtWidgets.QTableWidgetItem(str(product.sku)),
                QtWidgets.QTableWidgetItem(product.product_name),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(str(product.price)))),
                QtWidgets.QTableWidgetItem(format_number(str(product.stock))),
                QtWidgets.QTableWidgetItem(product.unit),
                QtWidgets.QTableWidgetItem(product.created_at),
            ]

            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.products_table_in_categories.setItem(current_row, col + 1, item)


    def set_category_form_data(self, data: CategoriesTableModel):
        self.ui.category_id_input.setText(str(data.category_id))
        self.ui.category_name_input.setText(str(data.category_name))

    # Getters
    # ===============
    def get_selected_products_table_data(self) -> set[str]:
        selected_products = set()
        for row in range(self.products_table_in_categories.rowCount()):
            checkbox_item = self.products_table_in_categories.item(row, 0)

            if checkbox_item and checkbox_item.checkState() == QtCore.Qt.CheckState.Checked:
                selected_products.add(checkbox_item.data(QtCore.Qt.ItemDataRole.UserRole))

        return selected_products
    
    
    def get_category_form_data(self) -> CategoriesTableModel:
        category_id = self.ui.category_id_input.text().strip()
        category_name = self.ui.category_name_input.text().strip()
        return CategoriesTableModel(category_id=category_id, category_name=category_name)


    # Shows
    # ===============
    def show_products_data(self):
        # Temporarily disable sorting
        self.products_table_in_categories.setSortingEnabled(False)

        search_text = self.ui.product_filter_input_in_categories.text().strip()
        search_text = search_text.lower() if search_text else None

        products_result = self.categories_service.get_products(search_text)

        self.set_products_table_data(products_result.data, set())

        # Re-enable sorting
        self.products_table_in_categories.setSortingEnabled(True)
           

    def show_categories_data(self):
        # Temporarily disable sorting
        self.categories_table.setSortingEnabled(False)

        search_text = self.ui.category_filter_input.text().strip()
        search_text = search_text.lower() if search_text else None

        categories_result = self.categories_service.get_categories(search_text)

        self.set_categories_table_data(categories_result.data)

        # Re-enable sorting
        self.categories_table.setSortingEnabled(True)


    # Clears
    # ===============
    def clear_category(self):
        self.ui.category_name_input.clear()
        self.ui.category_name_input.setEnabled(True)
        self.ui.product_filter_input_in_categories.clear()
        self.checked_items.clear()
        self.current_category_id = None
        
        # Reset button if it was in update mode
        self.ui.submit_category_button.setText("Submit")
        self.ui.submit_category_button.clicked.disconnect()
        self.ui.submit_category_button.clicked.connect(self.submit_category)
        
        # Refresh the products table to show unchecked boxes
        self.show_products_data()


    # Toggles
    # ===============
    def toggle_add_edit_categories_and_products(self, mode: bool = True):
        self.ui.category_name_label.setEnabled(mode)
        self.ui.category_name_input.setEnabled(mode)
        self.ui.filter_products_table_in_categories.setEnabled(mode)
        self.ui.product_filter_input_in_categories.setEnabled(mode)
        self.ui.products_table_in_categories.setEnabled(mode)
        self.ui.clear_category_button.setEnabled(mode)
        self.ui.submit_category_button.setEnabled(mode)