from PyQt6 import QtWidgets, uic, QtCore, QtGui
from datetime import datetime
import math

from dialogs.products_dialog.models.products_dialog_models import ProductsDialogModel
from dialogs.products_dialog.services.products_dialog_services import ProductsDialogService

from helper import format_number, add_prefix
from generals.fonts import POSFonts
from generals.message_box import POSMessageBox
from generals.build import resource_path
from generals.constants import (
    RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS,
    PERM_R_PRODUCTS
) 
from generals.messages import ( 
    ERR, ERR_PERM_R_PRODUCTS, PERM_DENIED
)
from dialogs.products_dialog.translations import PRODUCTS_DIALOG_TRANSLATIONS
from generals.language_manager import LanguageManager
from generals.permission_manager import PermissionManager


class ProductsDialogWindow(QtWidgets.QWidget):
    # Add signal to communicate with main window
    product_selected = QtCore.pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_R_PRODUCTS):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_R_PRODUCTS)
            self.close()
            return
        
        # Init Services
        self.products_dialog_service = ProductsDialogService()

        self.ui = uic.loadUi(resource_path('ui/products_dialog.ui'), self)

        # Init Table
        self.products_dialog_table = self.ui.products_dialog_table
        
        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(PRODUCTS_DIALOG_TRANSLATIONS)

        # Init Button
        self.ui.add_products_dialog_button.clicked.connect(self.send_product_data)
        self.ui.close_products_dialog_button.clicked.connect(lambda: self.close())
        
        self.ui.filter_products_dialog_input.returnPressed.connect(self.show_products_data)

        # Connect search input to filter function
        self.ui.data_per_page_combobox.currentTextChanged.connect(self.show_products_data)
        
        self.ui.find_products_button.clicked.connect(self.show_products_data)
        
        self.ui.first_page_button.clicked.connect(self.on_first_page_clicked)
        self.ui.previous_page_button.clicked.connect(self.on_previous_page_clicked)
        self.ui.next_page_button.clicked.connect(self.on_next_page_clicked)
        self.ui.last_page_button.clicked.connect(self.on_last_page_clicked)

        # Set selection behavior to select entire rows
        self.products_dialog_table.setSelectionBehavior(SELECT_ROWS)
        self.products_dialog_table.setSelectionMode(SINGLE_SELECTION)

        # Set table to be read only
        self.products_dialog_table.setEditTriggers(NO_EDIT_TRIGGERS)
    
        # Set table properties
        self.products_dialog_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.products_dialog_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        self.current_page = 1
        self.total_pages = 1
        self.total_all_products = 0

    
    # Overrides
    # ===============
    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        if not self.permission_manager.has_permission(PERM_R_PRODUCTS):
            self.close()
            return
        
        
        # Set window title
        if self.permission_manager.get_username().lower() not in self.windowTitle().lower():
            self.setWindowTitle(self.windowTitle() + ' - ' + self.permission_manager.get_username())

        self.language_manager.translate_widget_text(self)

        self.products_dialog_headers = ['SKU', 'Product Name', 'Price', 'Stock', 'Unit', 'Created At']
        if self.language_manager.get_current_language() == 'id':
            self.products_dialog_headers = ['Kode Barang', 'Nama Produk', 'Harga', 'Stok', 'Satuan', 'Tanggal Dibuat']

        self.language_manager.translate_table_headers(self.products_dialog_table, self.products_dialog_headers)

        self.ui.filter_products_dialog_input.setFocus()

        # Refresh the data
        self.show_products_data()


    def show(self):
        """Override show to ensure data is refreshed"""
        super().show()
        if not self.permission_manager.has_permission(PERM_R_PRODUCTS):
            self.close()
            return
        
        # Refresh the data
        self.show_products_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_R_PRODUCTS):
            self.close()
            return
        
        # Refresh the data
        self.show_products_data()


    # Shows
    # ===============
    def show_products_data(self):
        self.products_dialog_table.setSortingEnabled(False)

        search_text = self.ui.filter_products_dialog_input.text().strip()
        search_text = search_text.lower() if search_text else None

        limit = int(self.ui.data_per_page_combobox.currentText())
        offset = (self.current_page - 1) * limit

        products_dialog_result = self.products_dialog_service.get_products(search_text, limit, offset)

        if not products_dialog_result.success:
            POSMessageBox.error(self, title=ERR, message=products_dialog_result.message)
            return

        self.set_products_table_data(products_dialog_result.data['products'])

        self.total_count = products_dialog_result.data['total_count']
        self.ui.current_page_button.setText(str(self.current_page))

        self.total_pages = math.ceil(self.total_count / limit)

        self.ui.showing_products_label.setText(f'Showing {offset + 1} - {offset + limit} of {self.total_count} products')


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

        self.products_dialog_table.setSortingEnabled(True)


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
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Down:
            if self.products_dialog_table.rowCount() > 0 and not self.products_dialog_table.selectedItems():
                self.products_dialog_table.selectRow(0)
                self.products_dialog_table.setFocus()
                event.accept()
                return
            
        elif event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            if self.products_dialog_table.selectedItems():
                self.send_product_data()
                event.accept()
                return

        # Let the parent class handle other keys
        super().keyPressEvent(event)


    def on_first_page_clicked(self):
        self.current_page = 1
        self.show_products_data()


    def on_previous_page_clicked(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.show_products_data()


    def on_next_page_clicked(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.show_products_data()


    def on_last_page_clicked(self):
        self.current_page = self.total_pages
        self.show_products_data()
