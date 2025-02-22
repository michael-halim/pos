from PyQt6 import QtWidgets, uic, QtCore

from helper import format_number, add_prefix, remove_non_digit

from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS

from dialogs.suppliers_dialog.models.suppliers_dialog_models import SupplierModel
from dialogs.suppliers_dialog.services.suppliers_dialog_services import SuppliersDialogService
from generals.build import resource_path
class SuppliersDialogWindow(QtWidgets.QWidget):
    # Add signal to communicate with main window
    supplier_selected = QtCore.pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()

        self.ui = uic.loadUi(resource_path('ui/suppliers_dialog.ui'), self)

        # Init Services
        self.suppliers_dialog_service = SuppliersDialogService()

        # Init Table
        self.suppliers_table = self.ui.suppliers_table
        self.suppliers_table.setSortingEnabled(True)
        
        # Init Button
        self.ui.close_suppliers_dialog_button.clicked.connect(lambda: self.close())
        self.ui.add_supplier_dialog_button.clicked.connect(self.send_supplier_data)
        
        # Connect search input to filter function
        self.ui.filter_suppliers_dialog_input.textChanged.connect(self.show_suppliers_data)

        # Set selection behavior to select entire rows
        self.suppliers_table.setSelectionBehavior(SELECT_ROWS)
        self.suppliers_table.setSelectionMode(SINGLE_SELECTION)

        self.suppliers_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties
        self.suppliers_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.suppliers_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        # Show data
        self.show_suppliers_data()

    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        # Reset the current selection
        self.current_selected_supplier = None
        # Refresh the data
        self.show_suppliers_data()


    def show(self):
        """Override show to ensure data is refreshed"""
        super().show()
        # Reset the current selection
        self.current_selected_supplier = None
        # Refresh the data
        self.show_suppliers_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        # Reset the current selection
        self.current_selected_supplier = None
        # Refresh the data
        self.show_suppliers_data()


    def show_suppliers_data(self):
        # Temporarily disable sorting
        self.suppliers_table.setSortingEnabled(False)
        
        # Get search text if any    
        search_text: str = self.ui.filter_suppliers_dialog_input.text().strip()

        # Get suppliers
        suppliers_result = self.suppliers_dialog_service.get_suppliers(search_text)
        
        # Set Suppliers to table
        self.set_suppliers_table_data(suppliers_result.data)

        # Enable sorting
        self.suppliers_table.setSortingEnabled(True)

    def set_suppliers_table_data(self, data: list[SupplierModel]):
        # Clear the table
        self.suppliers_table.setRowCount(0)

        for supplier in data:
            current_row = self.suppliers_table.rowCount()
            self.suppliers_table.insertRow(current_row)

            table_items =  [ 
                QtWidgets.QTableWidgetItem(str(supplier.supplier_id)),
                QtWidgets.QTableWidgetItem(supplier.supplier_name),
                QtWidgets.QTableWidgetItem(supplier.supplier_address),
                QtWidgets.QTableWidgetItem(supplier.supplier_phone),
                QtWidgets.QTableWidgetItem(supplier.supplier_city),
                QtWidgets.QTableWidgetItem(supplier.supplier_remarks),
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=16))
                self.suppliers_table.setItem(current_row, col, item)


    def send_supplier_data(self):
        selected_rows = self.suppliers_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            
            # Create dictionary with product details
            supplier_data = {
                'supplier_id': self.suppliers_table.item(row, 0).text(),
            }
            
            # Emit signal with product data
            self.supplier_selected.emit(supplier_data)
            self.close()


    def set_filter(self, search_text: str):
        """Pre-fill the search filter"""
        self.ui.filter_suppliers_dialog_input.setText(search_text)

        # Optionally trigger the filter
        self.show_suppliers_data()