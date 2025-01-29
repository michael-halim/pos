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
        self.ui.edit_supplier_button.clicked.connect(self.edit_supplier)
        # self.ui.delete_supplier_button.clicked.connect(self.delete_supplier)
        # self.ui.close_supplier_button.clicked.connect(lambda: self.close())
        # self.ui.clear_supplier_button.clicked.connect(self.clear_supplier)
        self.ui.submit_supplier_button.clicked.connect(self.submit_supplier)

        # Connect search input to filter function
        self.ui.supplier_filter_input.textChanged.connect(self.show_suppliers_data)
        
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
        self.current_supplier_id = None

    def add_supplier(self):
        self.clear_supplier()
        self.ui.submit_supplier_button.setText("Submit Supplier")
        self.toggle_add_edit_suppliers(True)

    def show_suppliers_data(self):
        # Temporarily disable sorting
        self.suppliers_table.setSortingEnabled(False)
        
        # Clear the table
        self.suppliers_table.setRowCount(0)

        # Get search text if any
        search_text = self.ui.supplier_filter_input.text().strip()

        # Modify SQL query to include search filter
        sql = '''SELECT supplier_id, supplier_name, supplier_address, supplier_phone, supplier_city, supplier_remarks 
                FROM suppliers 
                WHERE supplier_name LIKE ? OR supplier_address LIKE ? OR supplier_phone LIKE ? OR supplier_city LIKE ? OR supplier_remarks LIKE ?'''
        
        # If no search text, show all suppliers 
        if not search_text:
            sql = 'SELECT supplier_id, supplier_name, supplier_address, supplier_phone, supplier_city, supplier_remarks FROM suppliers'
            self.cursor.execute(sql)
        else:
            # Add wildcards for LIKE query
            search_pattern = f"%{search_text}%"
            self.cursor.execute(sql, (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern))

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

    def submit_supplier(self):
        supplier_name = self.ui.supplier_name_input.text().strip()
        supplier_address = self.ui.supplier_address_input.text().strip()
        supplier_phone_number = self.ui.supplier_phone_number_input.text().strip()
        supplier_city = self.ui.supplier_city_input.text().strip()
        supplier_remarks = self.ui.supplier_remarks_input.text().strip()

        if not supplier_name:
            QtWidgets.QMessageBox.warning(self, "Error", "Supplier name is required")
            return
        
        try:
            self.cursor.execute('BEGIN TRANSACTION')

            # Insert supplier and get the ID
            self.cursor.execute('INSERT INTO suppliers (supplier_name, supplier_address, supplier_phone, supplier_city, supplier_remarks) VALUES (?, ?, ?, ?, ?)', 
                                (supplier_name, supplier_address, supplier_phone_number, supplier_city, supplier_remarks))
            
            self.db.commit()
            
            # Reset UI
            self.clear_supplier()
            self.show_suppliers_data()

        except Exception as e:
            self.db.rollback()
            print(f"Error: {e}")

    def edit_supplier(self):
        pass
