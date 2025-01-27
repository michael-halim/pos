from PyQt6 import QtWidgets, uic, QtGui, QtCore
from connect_db import DatabaseConnection

class SuppliersWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi('./ui/suppliers.ui', self)
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        
        # Init Tables
        self.suppliers_table = self.ui.suppliers_table
        self.suppliers_table.setSortingEnabled(True)

        # Connect Add Supplier Button
        self.ui.add_supplier_button.clicked.connect(self.add_supplier)
        # self.ui.edit_supplier_button.clicked.connect(self.edit_supplier)
        # self.ui.delete_supplier_button.clicked.connect(self.delete_supplier)
        # self.ui.close_supplier_button.clicked.connect(lambda: self.close())
        # self.ui.clear_supplier_button.clicked.connect(self.clear_supplier)
        # self.ui.submit_supplier_button.clicked.connect(self.submit_supplier)

        # Connect search input to filter function
        # self.ui.supplier_filter_input.textChanged.connect(self.show_products_data)
        
        # Add selected supplier tracking
        self.current_supplier_id = None
        
        # Connect table selection
        self.suppliers_table.itemSelectionChanged.connect(self.on_supplier_selected)

        # Set table properties
        self.suppliers_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.suppliers_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        # Show data for both tables
        self.show_suppliers_data()
    
    def toggle_add_edit_suppliers(self, mode: bool = True):
        self.ui.supplier_name_label.setEnabled(mode)
        self.ui.supplier_name_input.setEnabled(mode)
        self.ui.supplier_address_label.setEnabled(mode)
        self.ui.supplier_address_input.setEnabled(mode)
        self.ui.supplier_phone_number_label.setEnabled(mode)
        self.ui.supplier_phone_number_input.setEnabled(mode)
        self.ui.supplier_city_label.setEnabled(mode)
        self.ui.supplier_city_input.setEnabled(mode)
        self.ui.supplier_remarks_label.setEnabled(mode)
        self.ui.supplier_remarks_input.setEnabled(mode)
        self.ui.clear_supplier_button.setEnabled(mode)
        self.ui.submit_supplier_button.setEnabled(mode)

    def clear_supplier(self):
        self.ui.supplier_name_input.clear()
        self.ui.supplier_address_input.clear()
        self.ui.supplier_phone_number_input.clear()
        self.ui.supplier_city_input.clear()
        self.ui.supplier_remarks_input.clear()

    def add_supplier(self):
        self.clear_supplier()
        self.ui.submit_supplier_button.setText("Submit Supplier")
        self.toggle_add_edit_suppliers(True)

    def show_suppliers_data(self):
        self.cursor.execute('SELECT supplier_id, supplier_name, supplier_address, supplier_phone, supplier_city, supplier_remarks FROM suppliers')
        suppliers_result = self.cursor.fetchall()

        self.suppliers_table.setRowCount(len(suppliers_result))
        self.load_suppliers_data(suppliers_result)


    def load_suppliers_data(self, suppliers):
        for row, supplier in enumerate(suppliers):
            for col, value in enumerate(supplier):
                self.suppliers_table.setItem(row, col, QtWidgets.QTableWidgetItem(str(value)))

    def on_supplier_selected(self):
        selected_rows = self.suppliers_table.selectedItems()
        if selected_rows:
            # Get the first selected row
            row = selected_rows[0].row()
            self.current_supplier_id = int(self.suppliers_table.item(row, 0).text())
