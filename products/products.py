from PyQt6 import QtWidgets, uic, QtGui, QtCore
from generals.build import resource_path
from .services.products_services import ProductsService
from dialogs.master_stock_dialog.master_stock_dialog import MasterStockDialogWindow
from helper import format_number, add_prefix, remove_non_digit

from .models.products_models import ProductsModel
from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS

class ProductsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/products.ui'), self)

        # Init Services
        self.products_service = ProductsService()

        # Init Dialogs
        self.master_stock_dialog = MasterStockDialogWindow()    

        # Init Table
        self.products_table = self.ui.products_table
        self.products_table.setSortingEnabled(True)
        
        # Init Button
        self.ui.add_products_button.clicked.connect(self.add_products)
        self.ui.edit_products_button.clicked.connect(self.edit_products)
        self.ui.delete_products_button.clicked.connect(self.delete_products)
        self.ui.close_products_button.clicked.connect(lambda: self.close())
        
        # Connect search input to filter function
        self.ui.filter_products_input.textChanged.connect(self.show_products_data)

        
        # Set selection behavior to select entire rows
        self.products_table.setSelectionBehavior(SELECT_ROWS)
        self.products_table.setSelectionMode(SINGLE_SELECTION)

        self.products_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties
        self.products_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.products_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        
        self.show_products_data()


    # Overrides
    # ===============
    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)

        # Refresh the data
        self.show_products_data()


    def show(self):
        """Override show to ensure data is refreshed"""
        super().show()
        # Refresh the data

        self.show_products_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()

        # Refresh the data
        self.show_products_data()


    # Setters
    # ===============
    def set_products_table_data(self, data: list[ProductsModel]):
        # Clear the table
        self.products_table.setRowCount(0)

        for product in data:
            current_row = self.products_table.rowCount()
            self.products_table.insertRow(current_row)

            table_items =  [ 
                QtWidgets.QTableWidgetItem(str(product.sku)),
                QtWidgets.QTableWidgetItem(product.product_name),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(str(product.cost_price)))),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(str(product.price)))),
                QtWidgets.QTableWidgetItem(format_number(str(product.stock))),
                QtWidgets.QTableWidgetItem(product.unit),
                QtWidgets.QTableWidgetItem(product.remarks),
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.products_table.setItem(current_row, col, item)

    # Shows
    # ===============
    def show_products_data(self):
        search_text = self.ui.filter_products_input.text().strip()
        search_text = search_text.lower() if search_text else None

        products_result = self.products_service.get_products(search_text)

        self.set_products_table_data(products_result.data)


    def add_products(self):
        self.master_stock_dialog.clear_master_stock_form()
        self.master_stock_dialog.show()


    def edit_products(self):
        selected_rows = self.products_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            sku = self.products_table.item(row, 0).text()
            self.master_stock_dialog.set_master_stock_form_by_sku(sku)
            self.master_stock_dialog.show()

        else:
            POSMessageBox.warning(self, "Error", "Please select a product to edit")


    def delete_products(self):
        selected_rows = self.products_table.selectedItems()
        if not selected_rows:
            POSMessageBox.warning(self, "Error", "Please select a product to delete")
            return
        
        row = selected_rows[0].row()
        sku = self.products_table.item(row, 0).text()

        confirm = POSMessageBox.confirm(
                    self, title='Confirm Deletion', 
                    message=f'Are you sure you want to delete {sku} ?')

        if confirm:
            result = self.products_service.delete_products_by_sku(sku)
            if result.success:
                POSMessageBox.info(self, title='Success', message=result.message)

                self.products_table.setRowCount(0)
                self.show_products_data()

        else:
            POSMessageBox.error(self, title='Error', message=result.message)