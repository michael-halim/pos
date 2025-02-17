from PyQt6 import QtWidgets, uic, QtGui, QtCore
from connect_db import DatabaseConnection

from helper import format_number, add_prefix, remove_non_digit

from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS

from dialogs.suppliers_dialog.suppliers_dialog import SuppliersDialogWindow
from dialogs.master_stock_dialog.services.master_stock_dialog_services import MasterStockDialogService
from dialogs.price_unit_dialog.price_unit_dialog import PriceUnitDialogWindow

class MasterStockDialogWindow(QtWidgets.QWidget):
    # Add signal to communicate with main window
    supplier_selected = QtCore.pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()

        self.ui = uic.loadUi('./ui/master_stock.ui', self)

        # Init Dialog
        self.suppliers_dialog = SuppliersDialogWindow()
        self.price_unit_dialog = PriceUnitDialogWindow()
        # Init Services
        self.master_stock_dialog_service = MasterStockDialogService()

        # Init Table
        self.purchasing_history_in_master_stock_table = self.ui.purchasing_history_in_master_stock_table
        self.purchasing_history_in_master_stock_table.setSortingEnabled(True)
        
        # Init Button
        self.ui.find_sku_master_stock_button.clicked.connect(self.find_sku)
        self.ui.find_category_master_stock_button.clicked.connect(self.find_category)
        self.ui.find_supplier_master_stock_button.clicked.connect(lambda: self.suppliers_dialog.show())

        
        self.ui.price_unit_master_stock_button.clicked.connect(lambda: self.price_unit_dialog.show())
        # self.ui.discount_master_stock_button.clicked.connect(self.discount_master_stock_button)
        # self.ui.delete_master_stock_button.clicked.connect(self.delete_master_stock_button)
        # self.ui.submit_master_stock_button.clicked.connect(self.submit_master_stock_button)
        # self.ui.create_new_master_stock_button.clicked.connect(self.create_new_master_stock_button)
        
        self.ui.close_master_stock_button.clicked.connect(lambda: self.close())


        # Set selection behavior to select entire rows
        self.purchasing_history_in_master_stock_table.setSelectionBehavior(SELECT_ROWS)
        self.purchasing_history_in_master_stock_table.setSelectionMode(SINGLE_SELECTION)

        self.purchasing_history_in_master_stock_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties
        self.purchasing_history_in_master_stock_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.purchasing_history_in_master_stock_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

       
    def find_sku(self):
        pass
    
    def find_category(self):
        pass
    
    # def showEvent(self, event):
    #     """Override showEvent to refresh data when window is shown"""
    #     super().showEvent(event)
    #     # Reset the current selection
    #     self.current_selected_supplier = None
    #     # Refresh the data
    #     self.show_suppliers_data()


    # def show(self):
    #     """Override show to ensure data is refreshed"""
    #     super().show()
    #     # Reset the current selection
    #     self.current_selected_supplier = None
    #     # Refresh the data
    #     self.show_suppliers_data()


    # def showMaximized(self):
    #     """Override showMaximized to ensure data is refreshed"""
    #     super().showMaximized()
    #     # Reset the current selection
    #     self.current_selected_supplier = None
    #     # Refresh the data
    #     self.show_suppliers_data()


    # def show_suppliers_data(self):
    #     # Temporarily disable sorting
    #     self.suppliers_table.setSortingEnabled(False)
        
    #     # Clear the table
    #     self.suppliers_table.setRowCount(0)

    #     # Get search text if any    
    #     search_text: str = self.ui.filter_suppliers_dialog_input.text().strip()

    #     # Get suppliers
    #     suppliers_result = self.suppliers_dialog_service.get_suppliers(search_text)
        
    #     # Set Suppliers to table
    #     self.set_suppliers_table_data(suppliers_result.data)

    #     # Enable sorting
    #     self.suppliers_table.setSortingEnabled(True)

    # def set_suppliers_table_data(self, data: list[SupplierModel]):
    #     for supplier in data:
    #         current_row = self.suppliers_table.rowCount()
    #         self.suppliers_table.insertRow(current_row)

    #         table_items =  [ 
    #             QtWidgets.QTableWidgetItem(str(supplier.supplier_id)),
    #             QtWidgets.QTableWidgetItem(supplier.supplier_name),
    #             QtWidgets.QTableWidgetItem(supplier.supplier_address),
    #             QtWidgets.QTableWidgetItem(supplier.supplier_phone),
    #             QtWidgets.QTableWidgetItem(supplier.supplier_city),
    #             QtWidgets.QTableWidgetItem(supplier.supplier_remarks),
    #         ]
            
    #         for col, item in enumerate(table_items):
    #             item.setFont(POSFonts.get_font(size=16))
    #             self.suppliers_table.setItem(current_row, col, item)


    # def send_supplier_data(self):
    #     selected_rows = self.suppliers_table.selectedItems()
    #     if selected_rows:
    #         row = selected_rows[0].row()
            
    #         # Create dictionary with product details
    #         supplier_data = {
    #             'supplier_id': self.suppliers_table.item(row, 0).text(),
    #         }
            
    #         # Emit signal with product data
    #         self.supplier_selected.emit(supplier_data)
    #         self.close()


    # def set_filter(self, search_text: str):
    #     """Pre-fill the search filter"""
    #     self.ui.filter_suppliers_dialog_input.setText(search_text)

    #     # Optionally trigger the filter
    #     self.show_suppliers_data()