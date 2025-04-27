from PyQt6 import QtWidgets, uic, QtCore, QtGui
from datetime import datetime

from dialogs.products_dialog.models.products_dialog_models import ProductsDialogModel
from dialogs.products_dialog.services.products_dialog_services import ProductsDialogService

from helper import format_number, add_prefix
from generals.fonts import POSFonts
from generals.build import resource_path
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS
from dialogs.products_dialog.translations import PRODUCTS_DIALOG_TRANSLATIONS
from generals.language_manager import LanguageManager


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
        
        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(PRODUCTS_DIALOG_TRANSLATIONS)

        # Init Button
        self.ui.add_products_dialog_button.clicked.connect(self.send_product_data)
        self.ui.close_products_dialog_button.clicked.connect(lambda: self.close())
        
        # Connect search input to filter function
        self.ui.filter_products_dialog_input.textChanged.connect(self.show_products_data)
        
        # Simple key press event for the entire dialog
        self.keyPressEvent = self.handle_key_press
        
        # Set selection behavior to select entire rows
        self.products_dialog_table.setSelectionBehavior(SELECT_ROWS)
        self.products_dialog_table.setSelectionMode(SINGLE_SELECTION)

        # Set table to be read only
        self.products_dialog_table.setEditTriggers(NO_EDIT_TRIGGERS)
    
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

        self.language_manager.translate_widget_text(self) 

        self.products_dialog_headers = ['SKU', 'Product Name', 'Price', 'Stock', 'Unit', 'Created At']
        if self.language_manager.get_current_language() == 'id':
            self.products_dialog_headers = ['Kode Barang', 'Nama Produk', 'Harga', 'Stok', 'Satuan', 'Tanggal Dibuat']

        self.language_manager.translate_table_headers(self.products_dialog_table, self.products_dialog_headers)

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

            # Change stock color if negative
            stock = QtWidgets.QTableWidgetItem(str(product.stock))
            if product.stock < 0:
                stock = QtWidgets.QTableWidgetItem(f'-{format_number(str(product.stock))}')
                stock.setForeground(QtGui.QColor(255, 0, 0))

            table_items =  [ 
                QtWidgets.QTableWidgetItem(str(product.sku)),
                QtWidgets.QTableWidgetItem(product.product_name),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(product.price))),
                stock,
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


    # Event Listeners
    # ===============
    def handle_key_press(self, event):
        # Check for Enter key
        if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            # Don't handle Enter if we're in a text field
            if not isinstance(QtWidgets.QApplication.focusWidget(), QtWidgets.QLineEdit):
                # If a row is selected or there are rows, send the data
                if self.products_dialog_table.rowCount() > 0:
                    if not self.products_dialog_table.selectedItems():
                        self.products_dialog_table.selectRow(0)
                    self.send_product_data()
                    return
        
        # Let the parent class handle other keys
        super().keyPressEvent(event)
