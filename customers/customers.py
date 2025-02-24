from PyQt6 import QtWidgets, uic

from helper import format_number, add_prefix, remove_non_digit

from customers.services.customers_services import CustomersService
from customers.models.customers_models import CustomersModel
from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS
from generals.build import resource_path

class CustomersWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/customers.ui'), self)

        # Init Services
        self.customer_service = CustomersService()

        # Init Table
        self.customers_table = self.ui.customers_table
        self.customers_table.setSortingEnabled(True)

        # Connect search input to filter function
        self.ui.filter_customers_input.textChanged.connect(self.show_customers_data)

        # Connect button to function
        self.ui.close_customer_button.clicked.connect(lambda: self.close())
        self.ui.add_customer_button.clicked.connect(self.add_customer)
        self.ui.edit_customer_button.clicked.connect(self.edit_customer)
        self.ui.delete_customer_button.clicked.connect(self.delete_customer)
        self.ui.clear_customer_button.clicked.connect(self.clear_customer)
        self.ui.submit_customer_button.clicked.connect(self.submit_customer)

        # Set selection behavior to select entire rows
        self.customers_table.setSelectionBehavior(SELECT_ROWS)
        self.customers_table.setSelectionMode(SINGLE_SELECTION)

        self.customers_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties
        self.customers_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.customers_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        # Show data
        self.show_customers_data()


    def add_customer(self):
        self.clear_customer()
        self.set_enabled_customer_form(True)


    def edit_customer(self):
        selected_row = self.customers_table.selectedItems()
        if not selected_row:
            POSMessageBox.error(self, title='Error', message="Please select a customer to edit")
            return
        
        self.set_enabled_customer_form(True)
        
        # Get customer data from table
        customer_data = self.get_selected_customer_table_data()
        
        self.set_customer_form_data(customer_data)

        self.ui.submit_customer_button.setText('Update')
        self.ui.submit_customer_button.clicked.disconnect()
        self.ui.submit_customer_button.clicked.connect(self.update_customer)


    def update_customer(self):
        customer_form_data = self.get_customer_form_data()
        print(customer_form_data)
        if customer_form_data.customer_name == '' or customer_form_data.customer_phone == '':
            POSMessageBox.error(self, title='Error', message='Customer name and phone are required')
            return
        
        result_customer = self.customer_service.update_customer(customer_form_data)

        if result_customer.success:
            POSMessageBox.info(self, title='Success', message=result_customer.message)

            self.customers_table.setRowCount(0)
            self.set_enabled_customer_form(False)
            self.clear_customer()
            self.show_customers_data()

        else:
            POSMessageBox.error(self, title='Error', message=result_customer.message)


    def delete_customer(self):
        selected_row = self.customers_table.selectedItems()
        if not selected_row:
            POSMessageBox.error(self, title='Error', message="Please select a customer to delete")
            return
        
        confirm = POSMessageBox.confirm(
                        self, title='Confirm Deletion', 
                        message='Are you sure you want to delete this customer ?')

        if confirm:
            row = selected_row[0].row()
            customer_id = self.customers_table.item(row, 0).text()

            result = self.customer_service.delete_customer_by_customer_id(customer_id)
            if result.success:
                POSMessageBox.info(self, title='Success', message=result.message)

                self.customers_table.setRowCount(0)
                self.set_enabled_customer_form(False)
                self.clear_customer()
                self.show_customers_data()

            else:
                POSMessageBox.error(self, title='Error', message=result.message)

    
    def submit_customer(self):
        customer_data = self.get_customer_form_data()

        if customer_data.customer_name == '' or customer_data.customer_phone == '':
            POSMessageBox.error(self, title='Error', message='Customer name and phone are required')
            return
        
        result = self.customer_service.create_customer(customer_data)

        if result.success:
            POSMessageBox.info(self, title='Success', message=result.message)

            self.show_customers_data()
            self.set_enabled_customer_form(False)
            self.clear_customer()

        else:
            POSMessageBox.error(self, title='Error', message=result.message)
        

    # Overrides
    # ===============
    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        # Refresh the data
        self.show_customers_data()


    def show(self):
        """Override show to ensure data is refreshed"""
        super().show()
        # Refresh the data
        self.show_customers_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        # Refresh the data
        self.show_customers_data()


    # Shows
    # ===============
    def show_customers_data(self):
        search_text = self.ui.filter_customers_input.text().strip()
        search_text = search_text.lower() if search_text else None

        customers_result = self.customer_service.get_customers(search_text)

        self.set_customers_table_data(customers_result.data)


    # Setters
    # ===============
    def set_customers_table_data(self, data: list[CustomersModel]):
        # Clear the table
        self.customers_table.setRowCount(0)

        for customer in data:
            current_row = self.customers_table.rowCount()
            self.customers_table.insertRow(current_row)

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
                self.customers_table.setItem(current_row, col, item)


    def set_customer_form_data(self, data: CustomersModel):
        self.ui.customer_id_input.setText(data.customer_id)
        self.ui.customer_name_input.setText(data.customer_name)
        self.ui.customer_phone_input.setText(data.customer_phone)
        self.ui.customer_points_input.setText(format_number(data.customer_points))
        self.ui.customer_number_of_transactions_input.setText(format_number(data.number_of_transactions))
        self.ui.customer_value_transactions_input.setText(add_prefix(format_number(data.transaction_value)))


    def set_enabled_customer_form(self, is_enabled: bool):
        self.ui.customer_name_label.setEnabled(is_enabled)
        self.ui.customer_phone_label.setEnabled(is_enabled)
        self.ui.customer_points_label.setEnabled(is_enabled)
        self.ui.customer_number_of_transactions_label.setEnabled(is_enabled)
        self.ui.customer_value_transactions_label.setEnabled(is_enabled)
        self.ui.customer_name_input.setEnabled(is_enabled)
        self.ui.customer_phone_input.setEnabled(is_enabled)
        self.ui.customer_points_input.setEnabled(is_enabled)
        self.ui.customer_number_of_transactions_input.setEnabled(is_enabled)
        self.ui.customer_value_transactions_input.setEnabled(is_enabled)
        self.ui.clear_customer_button.setEnabled(is_enabled)
        self.ui.submit_customer_button.setEnabled(is_enabled)


    # Getters
    # ===============
    def get_customer_form_data(self) -> CustomersModel:
        customer_id = self.ui.customer_id_input.text().strip() if self.ui.customer_id_input.text().strip() else ''
        customer_points = int(remove_non_digit(self.ui.customer_points_input.text().strip())) if self.ui.customer_points_input.text().strip() else 0
        number_of_transactions = int(remove_non_digit(self.ui.customer_number_of_transactions_input.text().strip())) if self.ui.customer_number_of_transactions_input.text().strip() else 0
        transaction_value = int(remove_non_digit(self.ui.customer_value_transactions_input.text().strip())) if self.ui.customer_value_transactions_input.text().strip() else 0

        return CustomersModel(
            customer_id=customer_id,
            customer_name=self.ui.customer_name_input.text().strip(),
            customer_phone=self.ui.customer_phone_input.text().strip(),
            customer_points=customer_points,
            number_of_transactions=number_of_transactions,
            transaction_value=transaction_value,
        )

    
    def get_selected_customer_table_data(self) -> CustomersModel:
        selected_row = self.customers_table.selectedItems()
        if not selected_row:
            return None
        
        row = selected_row[0].row()
        customer_points = int(remove_non_digit(self.customers_table.item(row, 3).text())) if self.customers_table.item(row, 3).text() else 0
        number_of_transactions = int(remove_non_digit(self.customers_table.item(row, 4).text())) if self.customers_table.item(row, 4).text() else 0
        transaction_value = int(remove_non_digit(self.customers_table.item(row, 5).text())) if self.customers_table.item(row, 5).text() else 0

        return CustomersModel(
            customer_id=self.customers_table.item(row, 0).text(),
            customer_name=self.customers_table.item(row, 1).text(),
            customer_phone=self.customers_table.item(row, 2).text(),
            customer_points=customer_points,
            number_of_transactions=number_of_transactions,
            transaction_value=transaction_value,
        )

    # Clears
    # ===============
    def clear_customer(self):
        self.ui.customer_id_input.clear()
        self.ui.customer_name_input.clear()
        self.ui.customer_phone_input.clear()
        self.ui.customer_points_input.clear()
        self.ui.customer_number_of_transactions_input.clear()
        self.ui.customer_value_transactions_input.clear()

        self.ui.submit_customer_button.setText('Submit')
        self.ui.submit_customer_button.clicked.disconnect()
        self.ui.submit_customer_button.clicked.connect(self.submit_customer)
