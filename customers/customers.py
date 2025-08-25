from PyQt6 import QtWidgets, uic, QtCore

from customers.services.customers_services import CustomersService
from customers.models.customers_models import CustomersModel

from helper import format_number, add_prefix, remove_non_digit
from generals.message_box import POSMessageBox
from generals.build import resource_path
from generals.fonts import POSFonts
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS,
    PERM_R_CUSTOMERS, PERM_C_CUSTOMERS, PERM_U_CUSTOMERS, PERM_D_CUSTOMERS,
) 
from generals.messages import (
    ERR, OK, ERR_PERM_R_CUSTOMERS, ERR_PERM_C_CUSTOMERS, ERR_PERM_U_CUSTOMERS, ERR_PERM_D_CUSTOMERS,
    PERM_DENIED
)
from customers.translations import CUSTOMERS_TRANSLATIONS
from generals.permission_manager import PermissionManager
from generals.language_manager import LanguageManager


class CustomersWindow(QtWidgets.QWidget):
    def __init__(self, home_window=None):
        super().__init__()

        # Reference to home window
        self.home_window = home_window

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_R_CUSTOMERS):
            return

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/customers.ui'), self)

        # Setup permissions
        self.setup_permissions()
        
        # Init Services
        self.customer_service = CustomersService()

        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(CUSTOMERS_TRANSLATIONS)

        # Init Table
        self.customers_table = self.ui.customers_table

        # Connect search input to filter function
        self.ui.filter_customers_input.textChanged.connect(self.show_customers_data)

        # Connect button to function
        self.ui.close_customer_button.clicked.connect(lambda: self.close())
        self.ui.add_customer_button.clicked.connect(self.add_customer)
        self.ui.edit_customer_button.clicked.connect(self.edit_customer)
        self.ui.delete_customer_button.clicked.connect(self.delete_customer)
        self.ui.clear_customer_button.clicked.connect(self.clear_customer)
        self.ui.submit_customer_button.clicked.connect(self.submit_customer)

        # Event Filter
        self.ui.customer_name_input.installEventFilter(self)
        self.ui.customer_phone_input.installEventFilter(self)

        # Set selection behavior to select entire rows
        self.customers_table.setSelectionBehavior(SELECT_ROWS)
        self.customers_table.setSelectionMode(SINGLE_SELECTION)

        self.customers_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties
        self.customers_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.customers_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

        # Show data
        self.show_customers_data()



    # Overrides
    # ===============
    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        if not self.permission_manager.has_permission(PERM_R_CUSTOMERS):    
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_R_CUSTOMERS)
            self.close()
            return
        
        # Set window title
        if self.permission_manager.get_username().lower() not in self.windowTitle().lower():
            self.setWindowTitle(self.windowTitle() + ' - ' + self.permission_manager.get_username())


        # Translate Widget Text
        self.language_manager.translate_widget_text(self)

        self.customer_headers = ['Id', 'Name', 'Phone', 'Points', 'Tx (#)', 'Tx (Rp.)']
        if self.language_manager.get_current_language() == 'id':
            self.customer_headers = ['Id', 'Nama', 'Nomor', 'Poin', 'Transaksi (#)', 'Transaksi (Rp.)']

        self.language_manager.translate_table_headers(self.customers_table, self.customer_headers)

        # Refresh the data
        self.show_customers_data()


    def show(self):
        """Override show to ensure data is refreshed"""
        super().show()
        if not self.permission_manager.has_permission(PERM_R_CUSTOMERS):
            self.close()
            return
        
        # Refresh the data
        self.show_customers_data()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_R_CUSTOMERS):
            self.close()
            return
        
        # Refresh the data
        self.show_customers_data()


    def add_customer(self):
        if not self.permission_manager.has_permission(PERM_C_CUSTOMERS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_C_CUSTOMERS)
            return

        # Clear the form
        self.clear_customer()

        # Enable the form
        self.set_enabled_customer_form(True)

        # Set focus to customer name input
        self.ui.customer_name_input.setFocus()


    def edit_customer(self):
        if not self.permission_manager.has_permission(PERM_U_CUSTOMERS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_U_CUSTOMERS)
            return

        selected_row = self.customers_table.selectedItems()
        if not selected_row:
            POSMessageBox.error(self, title=ERR, message="Please select a customer to edit")
            return
        
        self.set_enabled_customer_form(True)
        
        # Get customer data from table
        customer_data = self.get_selected_customer_table_data()
        
        self.set_customer_form_data(customer_data)

        self.ui.submit_customer_button.setText('Update')
        self.ui.submit_customer_button.clicked.disconnect()
        self.ui.submit_customer_button.clicked.connect(self.update_customer)


    def update_customer(self):
        if not self.permission_manager.has_permission(PERM_U_CUSTOMERS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_U_CUSTOMERS)
            return

        customer_form_data = self.get_customer_form_data()
        if customer_form_data.customer_name == '' or customer_form_data.customer_phone == '':
            POSMessageBox.error(self, title=ERR, message='Customer name and phone are required')
            return
        
        result_customer = self.customer_service.update_customer(customer_form_data)

        if result_customer.success:
            POSMessageBox.info(self, title=OK, message=result_customer.message)

            self.customers_table.setRowCount(0)
            self.set_enabled_customer_form(False)
            self.clear_customer()
            self.show_customers_data()

        else:
            POSMessageBox.error(self, title=ERR, message=result_customer.message)


    def delete_customer(self):
        if not self.permission_manager.has_permission(PERM_D_CUSTOMERS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_D_CUSTOMERS)
            return

        selected_row = self.customers_table.selectedItems()
        if not selected_row:
            POSMessageBox.error(self, title=ERR, message="Please select a customer to delete")
            return
        
        confirm = POSMessageBox.confirm(
                        self, title='Confirm Deletion', 
                        message='Are you sure you want to delete this customer ?')

        if confirm:
            row = selected_row[0].row()
            customer_id = self.customers_table.item(row, 0).text()

            result = self.customer_service.delete_customer_by_customer_id(customer_id)
            if result.success:
                POSMessageBox.info(self, title=OK, message=result.message)

                self.customers_table.setRowCount(0)
                self.set_enabled_customer_form(False)
                self.clear_customer()
                self.show_customers_data()

            else:
                POSMessageBox.error(self, title=ERR, message=result.message)

    
    def submit_customer(self):
        if not self.permission_manager.has_permission(PERM_C_CUSTOMERS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_C_CUSTOMERS)
            return

        customer_data = self.get_customer_form_data()

        if customer_data.customer_name == '' or customer_data.customer_phone == '':
            POSMessageBox.error(self, title=ERR, message='Customer name and phone are required')
            return
        
        if not customer_data.customer_phone.isdigit():
            POSMessageBox.error(self, title=ERR, message='Phone number must be a number')
            return
        
        result = self.customer_service.create_customer(customer_data)

        if result.success:
            POSMessageBox.info(self, title=OK, message=result.message)

            self.show_customers_data()
            self.set_enabled_customer_form(False)
            self.clear_customer()

        else:
            POSMessageBox.error(self, title=ERR, message=result.message)
        

    
    # Shows
    # ===============
    def show_customers_data(self):
        if not self.permission_manager.has_permission(PERM_R_CUSTOMERS):
            return

        self.customers_table.setSortingEnabled(False)

        search_text = self.ui.filter_customers_input.text().strip()
        search_text = search_text.lower() if search_text else None

        customers_result = self.customer_service.get_customers(search_text)

        if not customers_result.success:
            POSMessageBox.error(self, title=ERR, message=customers_result.message)
            return

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
        
        self.customers_table.setSortingEnabled(True)


    def set_customer_form_data(self, data: CustomersModel):
        self.ui.customer_id_input.setText(data.customer_id)
        self.ui.customer_name_input.setText(data.customer_name)
        self.ui.customer_phone_input.setText(data.customer_phone)


    def set_enabled_customer_form(self, is_enabled: bool):
        self.ui.customer_name_label.setEnabled(is_enabled)
        self.ui.customer_phone_label.setEnabled(is_enabled)
        self.ui.customer_name_input.setEnabled(is_enabled)
        self.ui.customer_phone_input.setEnabled(is_enabled)
        self.ui.clear_customer_button.setEnabled(is_enabled)
        self.ui.submit_customer_button.setEnabled(is_enabled)


    # Getters
    # ===============
    def get_customer_form_data(self) -> CustomersModel:
        customer_id = self.ui.customer_id_input.text().strip() if self.ui.customer_id_input.text().strip() else ''

        return CustomersModel(
            customer_id=customer_id,
            customer_name=self.ui.customer_name_input.text().strip().upper(),
            customer_phone=self.ui.customer_phone_input.text().strip(),
            customer_points=0,
            number_of_transactions=0,
            transaction_value=0,
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

        self.ui.submit_customer_button.setText('Submit')
        self.ui.submit_customer_button.clicked.disconnect()
        self.ui.submit_customer_button.clicked.connect(self.submit_customer)


    # Setup Permissions
    # ===============
    def setup_permissions(self):
        self.ui.add_customer_button.setVisible(
            self.permission_manager.has_permission(PERM_C_CUSTOMERS)
        )
        self.ui.edit_customer_button.setVisible(
            self.permission_manager.has_permission(PERM_U_CUSTOMERS)
        )
        self.ui.delete_customer_button.setVisible(
            self.permission_manager.has_permission(PERM_D_CUSTOMERS))
    


    # Event Filters
    # ===============
    def eventFilter(self, obj, event):
        # If customer name input is focused and key pressed is Enter it focus to customer phone input
        if obj == self.ui.customer_name_input and event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
                self.ui.customer_phone_input.setFocus()


        # If customer phone input is focused and key pressed is Enter it submit the form
        if obj == self.ui.customer_phone_input and event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
                self.submit_customer()


        return super().eventFilter(obj, event)


    def closeEvent(self, event):
        """Override closeEvent to show home window when customers window is closed"""
        if self.home_window:
            self.home_window.show()
            self.home_window.raise_()
            self.home_window.activateWindow()
            
        event.accept()