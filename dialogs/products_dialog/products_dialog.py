from PyQt6 import QtWidgets, uic, QtCore

from helper import format_number, add_prefix
from generals.fonts import POSFonts
from generals.build import resource_path
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION
from dialogs.products_dialog.models.products_dialog_models import ProductsDialogModel
from dialogs.products_dialog.services.products_dialog_services import ProductsDialogService    
from datetime import datetime


class ProductsDialogWindow(QtWidgets.QWidget):
    # Add signal to communicate with main window
    product_selected = QtCore.pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()

        # Init Services
        self.products_dialog_service = ProductsDialogService()

        self.ui = uic.loadUi(resource_path('ui/products_dialog.ui'), self)

        # Init Table
        self.products_dialog_table = self.ui.products_dialog_table
        self.products_dialog_table.setSortingEnabled(True)
        
        # Init Button
        self.ui.add_products_dialog_button.clicked.connect(self.send_product_data)
        self.ui.close_products_dialog_button.clicked.connect(lambda: self.close())
        
        # Connect search input to filter function
        self.ui.filter_products_dialog_input.textChanged.connect(self.show_products_data)

        # Set selection behavior to select entire rows
        self.products_dialog_table.setSelectionBehavior(SELECT_ROWS)
        self.products_dialog_table.setSelectionMode(SINGLE_SELECTION)

        # Set table properties
        self.products_dialog_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.products_dialog_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        self.show_products_data()


    # Shows
    # ===============
    def show_products_data(self):
        search_text = self.ui.filter_products_dialog_input.text().strip()
        search_text = search_text.lower() if search_text else None

        products_dialog_result = self.products_dialog_service.get_products(search_text)

        self.set_products_table_data(products_dialog_result.data)


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
    def set_products_table_data(self, data: list[ProductsDialogModel]):
        # Clear the table
        self.products_dialog_table.setRowCount(0)

        for product in data:
            current_row = self.products_dialog_table.rowCount()
            self.products_dialog_table.insertRow(current_row)

            created_at_dt = datetime.strptime(product.created_at, '%Y-%m-%d %H:%M:%S')
            formatted_date = created_at_dt.strftime('%d %b %y %H:%M')

            table_items =  [ 
                QtWidgets.QTableWidgetItem(str(product.sku)),
                QtWidgets.QTableWidgetItem(product.product_name),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(product.price))),
                QtWidgets.QTableWidgetItem(format_number(product.stock)),
                QtWidgets.QTableWidgetItem(product.unit),
                QtWidgets.QTableWidgetItem(formatted_date),
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.products_dialog_table.setItem(current_row, col, item)


    # Signal Handlers
    # ===============
    def send_product_data(self):
        selected_rows = self.products_dialog_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            
            # Create dictionary with product details
            product_data = {
                'sku': self.products_dialog_table.item(row, 0).text(),
            }
            
            # Emit signal with product data
            self.product_selected.emit(product_data)
            self.close()


    def set_filter(self, search_text: str):
        """Pre-fill the search filter"""
        self.ui.filter_products_dialog_input.setText(search_text)
        # Optionally trigger the filter
        self.filter_products()


    def filter_products(self):
        search_text = self.ui.filter_products_dialog_input.text().lower()
        for row in range(self.products_dialog_table.rowCount()):
            match_found = False
            for col in range(self.products_dialog_table.columnCount()):
                item = self.products_dialog_table.item(row, col)
                if item and search_text in item.text().lower():
                    match_found = True
                    break
            self.products_dialog_table.setRowHidden(row, not match_found)
