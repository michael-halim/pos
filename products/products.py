from PyQt6 import QtWidgets, uic, QtGui

from products.services.products_services import ProductsService
from products.models.products_models import ProductsModel

from dialogs.master_stock_dialog.master_stock_dialog import MasterStockDialogWindow
from dialogs.import_products_dialog.import_products_dialog import ImportProductsDialogWindow
from dialogs.stock_card_dialog.stock_card_dialog import StockCardDialogWindow

from helper import format_number, add_prefix
from generals.build import resource_path
from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS
from generals.permission_manager import PermissionManager

class ProductsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.permission_manager = PermissionManager()
        
        # Set up button visibility based on permissions
        # self.setup_permissions()

        # Flag to track if data has been loaded
        self.data_loaded = False

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/products.ui'), self)

        # Init Services
        self.products_service = ProductsService()

        # Init Dialogs
        self.master_stock_dialog = MasterStockDialogWindow()    
        self.import_products_dialog = ImportProductsDialogWindow()
        self.stock_card_dialog = StockCardDialogWindow()

        # Init Table
        self.products_table = self.ui.products_table
        self.products_table.setSortingEnabled(True)
        
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
        self.products_table.setSelectionBehavior(SELECT_ROWS)
        self.products_table.setSelectionMode(SINGLE_SELECTION)

        self.products_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties
        self.products_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.products_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        
        

    # Overrides
    # ===============
    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)

        # Only refresh data if it hasn't been loaded yet or if we need to refresh
        if not self.data_loaded:
            self.show_products_data()
            self.data_loaded = True


    def show(self):
        """Override show to ensure data is refreshed"""
        super().show()
        # We'll let showEvent handle the data loading


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        # We'll let showEvent handle the data loading


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

    # Shows
    # ===============
    def show_products_data(self):
        """Load and display products data"""
        search_text = self.ui.filter_products_input.text().strip()
        search_text = search_text.lower() if search_text else None

        products_result = self.products_service.get_products(search_text)

        self.set_products_table_data(products_result.data)
        
        # Mark data as loaded
        self.data_loaded = True


    def import_products(self):
        """Show the import products dialog and refresh data when closed"""
        self.import_products_dialog.show()
        # Set data_loaded to False so it will refresh when this window is shown again
        self.data_loaded = False


    def add_products(self):
        """Show the add products dialog and refresh data when closed"""
        self.master_stock_dialog.clear_master_stock_form()
        self.master_stock_dialog.show()
        # Set data_loaded to False so it will refresh when this window is shown again
        self.data_loaded = False


    def edit_products(self):
        """Show the edit products dialog and refresh data when closed"""
        selected_rows = self.products_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            sku = self.products_table.item(row, 0).text()
            self.master_stock_dialog.set_master_stock_form_by_sku(sku)
            self.master_stock_dialog.show()
            # Set data_loaded to False so it will refresh when this window is shown again
            self.data_loaded = False
        else:
            POSMessageBox.warning(self, "Error", "Please select a product to edit")



    def stock_card_products(self):
        """Show the stock card products dialog"""
        selected_rows = self.products_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            sku = self.products_table.item(row, 0).text().strip()
            self.stock_card_dialog.show_stock_card_data(sku)
            self.stock_card_dialog.show()
        
        else:
            POSMessageBox.warning(self, title="Error", message="Please select a product to view stock card")
        


    def delete_products(self):
        """Delete a product"""
        # Check permission before allowing action
        if not self.permission_manager.has_permission('delete_products'):
            QtWidgets.QMessageBox.warning(
                self, 
                "Permission Denied",
                "You don't have permission to delete products"
            )
            return
            
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

                # Just refresh the data directly
                self.data_loaded = False
                self.show_products_data()

            else:
                POSMessageBox.error(self, title='Error', message=result.message)

    # def setup_permissions(self):
    #     """Set up UI elements based on user permissions"""
    #     # Hide/show buttons based on permissions
    #     self.ui.add_products_button.setVisible(
    #         self.permission_manager.has_permission('create_products')
    #     )
    #     self.ui.edit_products_button.setVisible(
    #         self.permission_manager.has_permission('update_products')
    #     )
    #     self.ui.delete_products_button.setVisible(
    #         self.permission_manager.has_permission('delete_products')
    #     )