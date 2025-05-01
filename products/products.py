from PyQt6 import QtWidgets, uic, QtGui, QtCore

from products.services.products_services import ProductsService
from products.models.products_models import ProductsModel

from dialogs.master_stock_dialog.master_stock_dialog import MasterStockDialogWindow
from dialogs.import_products_dialog.import_products_dialog import ImportProductsDialogWindow
from dialogs.stock_card_dialog.stock_card_dialog import StockCardDialogWindow

from helper import format_number, add_prefix
from generals.build import resource_path
from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS,
    PERM_R_PRODUCTS, PERM_C_PRODUCTS, PERM_U_PRODUCTS, PERM_D_PRODUCTS, PERM_I_PRODUCTS,
    PERM_R_STOCK_CARD,
) 
from generals.messages import (
    ERR, OK, ERR_PERM_R_PRODUCTS, ERR_PERM_C_PRODUCTS, ERR_PERM_U_PRODUCTS, ERR_PERM_D_PRODUCTS,
    ERR_PERM_I_PRODUCTS, ERR_PERM_R_STOCK_CARD, PERM_DENIED
)
from products.translations import PRODUCTS_TRANSLATIONS
from generals.permission_manager import PermissionManager
from generals.language_manager import LanguageManager


class ProductsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Flag to track if data has been loaded
        self.data_loaded = False

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_R_PRODUCTS):
            return
        
        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/products.ui'), self)
        
        # Setup permissions
        self.setup_permissions()

        # Setup language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(PRODUCTS_TRANSLATIONS)
        
        # Init Services
        self.products_service = ProductsService()

        # Init Dialogs
        self.master_stock_dialog = MasterStockDialogWindow()    
        self.import_products_dialog = ImportProductsDialogWindow()
        self.stock_card_dialog = StockCardDialogWindow()

        # Init Button
        self.ui.add_products_button.clicked.connect(self.add_products)
        self.ui.edit_products_button.clicked.connect(self.edit_products)
        self.ui.delete_products_button.clicked.connect(self.delete_products)
        self.ui.import_products_button.clicked.connect(self.import_products)
        self.ui.stock_card_products_button.clicked.connect(self.stock_card_products)

        self.ui.close_products_button.clicked.connect(lambda: self.close())
        
        # Connect search input to filter function
        self.ui.filter_products_input.textChanged.connect(self.show_products_data)

        # Set selection behavior to select entire rows
        self.ui.products_table.setSelectionBehavior(SELECT_ROWS)
        self.ui.products_table.setSelectionMode(SINGLE_SELECTION)

        self.ui.products_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties
        self.ui.products_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.ui.products_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)



    # Overrides
    # ===============
    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        if not self.permission_manager.has_permission(PERM_R_PRODUCTS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_PRODUCTS)
            self.close()
            return
        
        # Translate widget text and update table headers
        self.language_manager.translate_widget_text(self)
        
        self.product_headers = ['SKU', 'Product Name', 'Cost Price', 'Price', 'Stock', 'Unit', 'Remarks']
        if self.language_manager.get_current_language() == 'id':
            self.product_headers = ['Kode Barang', 'Nama Produk', 'Harga Beli', 'Harga Jual', 'Stok', 'Satuan', 'Keterangan']

        self.language_manager.translate_table_headers(self.ui.products_table, self.product_headers)

        # Only refresh data if it hasn't been loaded yet or if we need to refresh
        if not self.data_loaded:
            self.show_products_data()
            self.data_loaded = True
            

    def show(self):
        """Override show to ensure data is refreshed"""
        super().show()
        if not self.permission_manager.has_permission(PERM_R_PRODUCTS):
            self.close()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_R_PRODUCTS):
            self.close()
        


    # Setters
    # ===============
    def set_products_table_data(self, data: list[ProductsModel]):
        # Clear the table
        self.products_table.setRowCount(0)

        for product in data:
            current_row = self.products_table.rowCount()
            self.products_table.insertRow(current_row)

            # Change stock color if negative
            stock = QtWidgets.QTableWidgetItem(str(product.stock))
            if product.stock < 0:
                stock = QtWidgets.QTableWidgetItem(f'-{format_number(str(product.stock))}')
                stock.setForeground(QtGui.QColor(255, 0, 0))

            table_items =  [ 
                QtWidgets.QTableWidgetItem(str(product.sku)),
                QtWidgets.QTableWidgetItem(product.product_name),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(str(product.cost_price)))),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(str(product.price)))),
                stock,
                QtWidgets.QTableWidgetItem(product.unit),
                QtWidgets.QTableWidgetItem(product.remarks),
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.products_table.setItem(current_row, col, item)

        self.products_table.setSortingEnabled(True)


    # Shows
    # ===============
    def show_products_data(self):
        """Load and display products data"""
        if not self.permission_manager.has_permission(PERM_R_PRODUCTS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_PRODUCTS)
            self.close()
            return
        
        self.products_table.setSortingEnabled(False)

        search_text = self.ui.filter_products_input.text().strip()
        search_text = search_text.upper() if search_text else None

        products_result = self.products_service.get_products(search_text)

        if not products_result.success:
            POSMessageBox.error(self, title=ERR, message=products_result.message)
            return

        self.set_products_table_data(products_result.data)
        
        # Mark data as loaded
        self.data_loaded = True


    def import_products(self):
        """Show the import products dialog and refresh data when closed"""
        if not self.permission_manager.has_permission(PERM_I_PRODUCTS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_I_PRODUCTS)
            return

        self.import_products_dialog.show()

        # Set data_loaded to False so it will refresh when this window is shown again
        self.data_loaded = False


    def add_products(self):
        """Show the add products dialog and refresh data when closed"""
        if not self.permission_manager.has_permission(PERM_C_PRODUCTS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_C_PRODUCTS)
            return

        self.master_stock_dialog.clear_master_stock_form()
        self.master_stock_dialog.show()
        # Set data_loaded to False so it will refresh when this window is shown again
        self.data_loaded = False


    def edit_products(self):
        """Show the edit products dialog and refresh data when closed"""
        if not self.permission_manager.has_permission(PERM_U_PRODUCTS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_U_PRODUCTS)
            return

        selected_rows = self.products_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            sku = self.products_table.item(row, 0).text()
            self.master_stock_dialog.set_master_stock_form_by_sku(sku)
            self.master_stock_dialog.show()

            # Set data_loaded to False so it will refresh when this window is shown again
            self.data_loaded = False
        else:
            POSMessageBox.warning(self, title=ERR, message="Please select a product to edit")


    def stock_card_products(self):
        """Show the stock card products dialog"""
        if not self.permission_manager.has_permission(PERM_R_STOCK_CARD):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_STOCK_CARD)
            return

        selected_rows = self.products_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            sku = self.products_table.item(row, 0).text().strip()
            self.stock_card_dialog.show_stock_card_data(sku)
            self.stock_card_dialog.show()
        
        else:
            POSMessageBox.warning(self, title=ERR, message="Please select a product to view stock card")
        

    def delete_products(self):
        """Delete a product"""
        if not self.permission_manager.has_permission(PERM_D_PRODUCTS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_D_PRODUCTS)
            return

        selected_rows = self.products_table.selectedItems()
        if not selected_rows:
            POSMessageBox.warning(self, title=ERR, message="Please select a product to delete")
            return
        
        row = selected_rows[0].row()
        sku = self.products_table.item(row, 0).text()

        confirm = POSMessageBox.confirm(
                    self, title='Confirm Deletion', 
                    message=f'Are you sure you want to delete {sku} ?')

        if confirm:
            result = self.products_service.delete_products_by_sku(sku)
            if result.success:
                POSMessageBox.info(self, title=OK, message=result.message)

                # Just refresh the data directly
                self.data_loaded = False
                self.show_products_data()

            else:
                POSMessageBox.error(self, title=ERR, message=result.message)


    # Setup Permissions
    # ===============
    def setup_permissions(self):
        """Set up UI elements based on user permissions"""
        # Hide/show buttons based on permissions
        self.ui.add_products_button.setVisible(
            self.permission_manager.has_permission(PERM_C_PRODUCTS)
        )
        self.ui.edit_products_button.setVisible(
            self.permission_manager.has_permission(PERM_U_PRODUCTS)
        )
        self.ui.delete_products_button.setVisible(
            self.permission_manager.has_permission(PERM_D_PRODUCTS)
        )
        self.ui.import_products_button.setVisible(
            self.permission_manager.has_permission(PERM_I_PRODUCTS)
        )


    # Event Filters
    # ===============
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Down:
            if self.products_table.rowCount() > 0 and not self.products_table.selectedItems():
                self.products_table.selectRow(0)
                self.products_table.setFocus()
                event.accept()
                return
            

        # Let the parent class handle other keys
        super().keyPressEvent(event)