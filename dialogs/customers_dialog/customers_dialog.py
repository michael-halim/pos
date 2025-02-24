from PyQt6 import QtWidgets, uic, QtCore

from .services.customers_dialog_services import CustomersDialogService
from .models.customers_dialog_models import CustomersDialogModel

from helper import format_number, add_prefix
from generals.fonts import POSFonts
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS
from generals.build import resource_path

class CustomersDialogWindow(QtWidgets.QWidget):
    customer_selected = QtCore.pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.ui = uic.loadUi(resource_path('ui/customers_dialog.ui'), self)

        self.customer_dialog_service = CustomersDialogService()
        # Init Table
        self.customers_dialog_table = self.ui.customers_dialog_table
        self.customers_dialog_table.setSortingEnabled(True)

        # Connect search input to filter function
        self.ui.filter_customers_dialog_input.textChanged.connect(self.show_customers_data)

        # Connect button to function
        self.ui.close_customer_dialog_button.clicked.connect(lambda: self.close())
        self.ui.add_customers_dialog_button.clicked.connect(self.send_customer_data)

        # Set selection behavior to select entire rows
        self.customers_dialog_table.setSelectionBehavior(SELECT_ROWS)
        self.customers_dialog_table.setSelectionMode(SINGLE_SELECTION)

        self.customers_dialog_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties
        self.customers_dialog_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.customers_dialog_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        # Show data
        self.show_customers_data()

    # Shows
    # ===============
    def show_customers_data(self):
        search_text = self.ui.filter_customers_dialog_input.text().strip()
        search_text = search_text.lower() if search_text else None

        customers_result = self.customer_dialog_service.get_customers(search_text)

        self.set_customers_table_data(customers_result.data)


    # Setters
    # ===============
    def set_customers_table_data(self, data: list[CustomersDialogModel]):
        # Clear the table
        self.customers_dialog_table.setRowCount(0)

        for customer in data:
            current_row = self.customers_dialog_table.rowCount()
            self.customers_dialog_table.insertRow(current_row)

            table_items =  [ 
                QtWidgets.QTableWidgetItem(str(customer.customer_id)),
                QtWidgets.QTableWidgetItem(customer.customer_name),
                QtWidgets.QTableWidgetItem(customer.customer_phone),
                QtWidgets.QTableWidgetItem(format_number(customer.customer_points)),
                QtWidgets.QTableWidgetItem(format_number(customer.number_of_transactions)),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(customer.transaction_value))),
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.customers_dialog_table.setItem(current_row, col, item)


    def send_customer_data(self):
        selected_rows = self.customers_dialog_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            
            # Create dictionary with product details
            customer_data = {
                'customer_id': self.customers_dialog_table.item(row, 0).text(),
            }
            
            # Emit signal with product data
            self.customer_selected.emit(customer_data)
            self.close()