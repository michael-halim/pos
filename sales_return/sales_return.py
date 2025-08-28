from PyQt6 import QtWidgets, uic, QtCore
from datetime import datetime

from dialogs.customers_dialog.customers_dialog import CustomersDialogWindow
from dialogs.products_dialog.products_dialog import ProductsDialogWindow

from sales_return.services.sales_return_services import SalesReturnService
from sales_return.models.sales_return_models import SalesReturnModel, DetailSalesReturnModel

from helper import format_number, add_prefix, remove_non_digit
from generals.message_box import POSMessageBox
from generals.build import resource_path
from generals.fonts import POSFonts
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS,
    PERM_C_SALES_RETURN, PERM_U_SALES_RETURN,
    DATE_FORMAT_DDMMYYYY, DATE_EDIT_NO_BUTTONS
)
from generals.messages import (
    ERR, OK, PERM_DENIED, WARNING, CONFIRM,
    ERR_PERM_C_SALES_RETURN,
    ERR_PERM_U_SALES_RETURN,
)
from sales_return.translations import SALES_RETURN_TRANSLATIONS
from generals.language_manager import LanguageManager
from generals.permission_manager import PermissionManager


class SalesReturnWindow(QtWidgets.QWidget):
    def __init__(self, home_window: None):
        super().__init__()

        self.home_window = home_window

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_C_SALES_RETURN):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_C_SALES_RETURN)
            self.close()
            return
        
        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/sales_return.ui'), self)

        # Init Services
        self.sales_return_service = SalesReturnService()

        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(SALES_RETURN_TRANSLATIONS)

        # Init Dialog
        self.products_dialog = ProductsDialogWindow()
        self.customers_dialog = CustomersDialogWindow()

        # Init Tables
        self.detail_sales_return_table = self.ui.detail_sales_return_table

        # Connect the add button to add_transaction method
        self.ui.close_sales_return_button.clicked.connect(lambda: self.close())
        self.ui.clear_data_sales_return_button.clicked.connect(self.clear_data_sales_return)
        self.ui.add_sales_return_button.clicked.connect(self.add_detail_sales_return)
        self.ui.edit_sales_return_button.clicked.connect(self.edit_detail_sales_return)
        self.ui.delete_sales_return_button.clicked.connect(self.delete_detail_sales_return)
        self.ui.submit_sales_return_button.clicked.connect(self.submit_sales_return)
        self.ui.clear_sales_return_button.clicked.connect(self.clear_sales_return)

        self.ui.find_customer_in_sales_return_button.clicked.connect(lambda: self.customers_dialog.show())
        self.ui.find_sku_sales_return_button.clicked.connect(lambda: self.products_dialog.show())

        # Add selected tracking
        self.cached_qty = {} # key = <sku>_<unit>, value = (unit_value, price)
        self.cached_sales_return_index = {} # key = <sku>_<unit>, value = sales_return_table_index

        # Handle customer selected
        self.customers_dialog.customer_selected.connect(self.handle_customer_selected)

        # Handle product selected
        self.products_dialog.product_selected.connect(self.handle_product_selected)

        # Listeners
        # ===========

        # Customer in sales return input
        self.ui.customer_in_sales_return_input.returnPressed.connect(self.on_handle_customer_enter)

        # Connect qty combobox to update qty input
        self.ui.qty_sales_return_combobox.currentTextChanged.connect(self.on_qty_sales_return_combobox_changed)

        # Connect qty input to update stock after input
        self.ui.qty_sales_return_input.textChanged.connect(self.on_qty_sales_return_input_changed)

        # Connect return pressed signal
        self.ui.sku_sales_return_input.returnPressed.connect(self.on_handle_sku_enter)

        # Connect price input event listener
        self.ui.price_sales_return_input.textChanged.connect(self.on_price_sales_return_input_changed)

        # Set date input
        self.ui.sales_return_date_input.setDate(datetime.now())

        # UX For Shortcut
        # =================
        # Set focus to customer input
        self.ui.customer_in_sales_return_input.setFocus()

        # Connect price input event listener
        self.ui.price_sales_return_input.installEventFilter(self)

        # Connect qty input event listener
        self.ui.qty_sales_return_input.installEventFilter(self)

        # Connect combobox activated signal
        self.ui.qty_sales_return_combobox.activated.connect(self.on_unit_selected)

        self.ui.sales_return_date_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)
        self.ui.sales_return_date_input.setButtonSymbols(DATE_EDIT_NO_BUTTONS)


        # Set selection behavior to select entire rows
        self.detail_sales_return_table.setSelectionBehavior(SELECT_ROWS)
        self.detail_sales_return_table.setSelectionMode(SINGLE_SELECTION)

        # Set wholesale transactions table to be read only
        self.detail_sales_return_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties to resize to contents
        self.detail_sales_return_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.detail_sales_return_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)


    # Overrides
    # ===============
    def showMaximized(self):
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_C_SALES_RETURN):
            self.close()
            return

        # Set window title
        if self.permission_manager.get_username().lower() not in self.windowTitle().lower():
            self.setWindowTitle(self.windowTitle() + ' - ' + self.permission_manager.get_username())


        # Translate widget text and update table headers
        self.language_manager.translate_widget_text(self)

        self.sales_return_headers = ['SKU', 'Product Name', 'Qty', 'Unit', 'Unit Value', 'Price', 'Subtotal']
        if self.language_manager.get_current_language() == 'id':
            self.sales_return_headers = ['Kode Barang', 'Nama Produk', 'Qty', 'Satuan', 'Nilai Satuan', 'Harga', 'Subtotal']

        self.language_manager.translate_table_headers(self.ui.detail_sales_return_table, self.sales_return_headers)


    def add_detail_sales_return(self):
        # Stop temporary sorting
        self.detail_sales_return_table.setSortingEnabled(False)
        try:
            sales_return_form_data = self.get_sales_return_form_data()

            items = [ sales_return_form_data ]

            # Set sales return table data
            self.set_sales_return_table_data(items)

            # Calculate total sales return
            total_amount = self.calculate_total_sales_return()
            self.ui.total_sales_return_input.setText(add_prefix(format_number(str(total_amount))))

            # Clear data
            self.clear_data_sales_return()
                
        except Exception as e:
            POSMessageBox.error(self, title=ERR, message=f"Failed to add sales return: {str(e)}")

        finally:
            # Re-enable sorting
            self.detail_sales_return_table.setSortingEnabled(True)


    def edit_detail_sales_return(self):
        # Get selected row
        selected_rows = self.detail_sales_return_table.selectedItems()
        if not selected_rows:
            POSMessageBox.warning(self, title=WARNING, message="Please select a sales return to edit")
            return

        self.current_selected_sku = selected_rows[0].row()

        # Disconnect existing connections and connect to update function
        self.ui.add_sales_return_button.setText('Update')
        self.ui.add_sales_return_button.clicked.disconnect()
        self.ui.add_sales_return_button.clicked.connect(self.update_detail_sales_return)

        # Get Selected Sales Return Table Data
        sales_return_table_data: DetailSalesReturnModel = self.get_selected_sales_return_table_data()

        self.set_sales_return_form_data(sales_return_table_data)

        # Set focus to qty input
        self.ui.qty_sales_return_input.setFocus()
        
        # Set Combobox to current unit and disable it
        if self.ui.qty_sales_return_combobox.findText(sales_return_table_data.unit) == -1:
            self.ui.qty_sales_return_combobox.addItem(sales_return_table_data.unit)

        self.ui.qty_sales_return_combobox.setCurrentText(sales_return_table_data.unit)
        self.ui.qty_sales_return_combobox.setEnabled(False)
        
        # Make sure only qty is editable
        self.ui.price_sales_return_input.setEnabled(True)
        self.ui.sku_sales_return_input.setEnabled(False)
        self.ui.product_name_sales_return_input.setEnabled(False)


    def update_detail_sales_return(self):
        if self.current_selected_sku is not None:
            try:
                # Get the updated values
                qty = self.ui.qty_sales_return_input.text().strip()
                price = remove_non_digit(self.ui.price_sales_return_input.text())

                # Calculate new subtotal
                subtotal = int(price) * int(qty)
                
                # Update the row in the table
                self.detail_sales_return_table.item(self.current_selected_sku, 2).setText(format_number(qty))
                self.detail_sales_return_table.item(self.current_selected_sku, 5).setText(add_prefix(format_number(str(price))))
                self.detail_sales_return_table.item(self.current_selected_sku, 6).setText(add_prefix(format_number(str(subtotal))))
                
                # Update total amount
                total_amount = self.calculate_total_sales_return()
                self.ui.total_sales_return_input.setText(add_prefix(format_number(str(total_amount))))

                # Reset the form
                self.clear_data_sales_return()
                
                # Reset button and connection
                self.ui.add_sales_return_button.setText('Add')
                self.ui.add_sales_return_button.clicked.disconnect()
                self.ui.add_sales_return_button.clicked.connect(self.add_detail_sales_return)
                
                # Reset selection
                self.current_selected_sku = None
                
                # Re-enable all inputs
                self.ui.sku_sales_return_input.setEnabled(True)
                self.ui.price_sales_return_input.setEnabled(True)

            except Exception as e:
                POSMessageBox.error(self, title=ERR, message=f"Failed to update sales return: {str(e)}")


    def delete_detail_sales_return(self):
        selected_rows = self.detail_sales_return_table.selectedItems()
        if not selected_rows:
            POSMessageBox.warning(self, title=WARNING, message="Please select a sales return to delete")
            return

        # Confirm deletion
        confirm = POSMessageBox.confirm(self, title=CONFIRM, message="Are you sure you want to delete this sales return ?")

        if confirm:
            row = selected_rows[0].row()

            # Get the transaction details before deletion
            sku = self.detail_sales_return_table.item(row, 0).text()
            unit = self.detail_sales_return_table.item(row, 3).text()

            # Remove from cached index
            sales_return_index_key = f'{sku}_{unit}'
            if sales_return_index_key in self.cached_sales_return_index:
                del self.cached_sales_return_index[sales_return_index_key]

            # Remove the row from table
            self.detail_sales_return_table.removeRow(row)

            # Update total amount
            total_amount: int = self.calculate_total_sales_return()
            self.ui.total_sales_return_input.setText(add_prefix(format_number(str(total_amount))))


    def submit_sales_return(self):
        if not self.permission_manager.has_permission(PERM_C_SALES_RETURN):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_C_SALES_RETURN)
            return

        # Get detail sales return from sales return table
        detail_sales_return_data: list[DetailSalesReturnModel] = self.get_detail_sales_return()
        if len(detail_sales_return_data) == 0:
            POSMessageBox.error(self, title=ERR, message="No sales return to submit")
            return

        # Create sales return id
        sales_return_id: str = self.sales_return_service.create_sales_return_id()
        for detail in detail_sales_return_data:
            detail.sales_return_id = sales_return_id

        # Calculate total amount
        total_amount: int = self.calculate_total_sales_return()

        # Get Sales Return Data
        sales_return_remarks: str = self.ui.remarks_sales_return_input.toPlainText().strip()
        customer_id: str = self.ui.customer_in_sales_return_input.text().strip()


        # Create sales return data
        sales_return_data: SalesReturnModel = SalesReturnModel(
            sales_return_id = sales_return_id,
            customer_id = customer_id,
            sales_return_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_amount = total_amount ,
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            created_by = self.permission_manager.get_user_id(),
            sales_return_remarks = sales_return_remarks,
            updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            updated_by = self.permission_manager.get_user_id()
        )

        # Submit sales return
        result = self.sales_return_service.submit_sales_return(sales_return_data, detail_sales_return_data)
        if result.success:
            POSMessageBox.info(self, title=OK, message=result.message)
            
            # Clear the sales return table and total
            self.clear_sales_return()

        else:
            POSMessageBox.error(self, title=ERR, message=result.message)


    def update_sales_return(self):
        if not self.permission_manager.has_permission(PERM_U_SALES_RETURN):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_U_SALES_RETURN)
            return

        # Get detail sales return from sales return table
        detail_sales_return_data: list[DetailSalesReturnModel] = self.get_detail_sales_return()
        if len(detail_sales_return_data) == 0:
            POSMessageBox.error(self, title=ERR, message="No sales return to update")
            return

        # Create sales return id
        sales_return_id: str = self.ui.sales_return_id_input.text().strip()

        # Calculate total amount and total discount
        total_amount: int = self.calculate_total_sales_return()

        # Get Sales Return Data
        sales_return_remarks: str = self.ui.remarks_sales_return_input.toPlainText().strip()
        customer_id: str = self.ui.customer_in_sales_return_input.text().strip()


        # Create sales return data
        sales_return_data: SalesReturnModel = SalesReturnModel(
            sales_return_id = sales_return_id,
            customer_id = customer_id,
            sales_return_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_amount = total_amount,
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            created_by = self.permission_manager.get_user_id(),
            sales_return_remarks = sales_return_remarks,
            updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            updated_by = self.permission_manager.get_user_id()
        )

        # Get added, updated, and deleted detail sales return
        added_detail_sales_return, updated_detail_sales_return, deleted_detail_sales_return = self.get_added_updated_deleted_detail_sales_return(sales_return_id, detail_sales_return_data)

        # Update sales return
        result = self.sales_return_service.update_sales_return(sales_return_data, added_detail_sales_return, updated_detail_sales_return, deleted_detail_sales_return)
        if result.success:
            POSMessageBox.info(self, title=OK, message=result.message)
            
            # Clear the sales return table and total
            self.clear_sales_return()

        else:
            POSMessageBox.error(self, title=ERR, message=result.message)

    
    # Setters
    # ===============
    def set_sales_return_table_data(self, data: list[DetailSalesReturnModel]):
        for item in data:
            sales_return_index_key = f'{item.sku}_{item.unit}'
            if sales_return_index_key in self.cached_sales_return_index:
                idx = self.cached_sales_return_index[sales_return_index_key]
                price: str = remove_non_digit(self.detail_sales_return_table.item(idx, 5).text())
                updated_qty: int = int(remove_non_digit(self.detail_sales_return_table.item(idx, 2).text())) + int(item.qty)
                updated_amount: int = int(price) * int(updated_qty)

                self.detail_sales_return_table.item(idx, 2).setText(format_number(str(updated_qty)))
                self.detail_sales_return_table.item(idx, 6).setText(add_prefix(format_number(str(updated_amount))))

            else:
                current_row = self.detail_sales_return_table.rowCount()
                self.detail_sales_return_table.insertRow(current_row)

                table_items =  [ 
                    QtWidgets.QTableWidgetItem(item.sku),
                    QtWidgets.QTableWidgetItem(item.product_name),
                    QtWidgets.QTableWidgetItem(format_number(item.qty)),
                    QtWidgets.QTableWidgetItem(item.unit),
                    QtWidgets.QTableWidgetItem(format_number(item.unit_value)),
                    QtWidgets.QTableWidgetItem(add_prefix(format_number(item.price))),
                    QtWidgets.QTableWidgetItem(add_prefix(format_number(item.subtotal)))
                ]
                
                for col, item in enumerate(table_items):
                    item.setFont(POSFonts.get_font(size=12))
                    self.detail_sales_return_table.setItem(current_row, col, item)

                # Add sales return index
                self.cached_sales_return_index[sales_return_index_key] = current_row

        self.detail_sales_return_table.setSortingEnabled(True)


    def set_product_unit_details(self, sku: str):
        '''
            Set the product unit into combobox

            sku and unit is the unique key, and the value is unit_value
            behind the scene the sku and unit is stored using dictionary called cached_qty
            Example: 
            
            ```cache_key = 'SKU001'
            cached_qty = {
                'SKU001_pcs' : 1,  #(pcs unit value is 1)
                'SKU001_kodi' : 20, #(kodi unit value is 20)
            }
            ```
        '''

        product_unit_details = self.sales_return_service.get_product_unit_details(sku)
        if product_unit_details.success and product_unit_details.data:
            for pud in product_unit_details.data:
                # key = <sku>_<unit>, value = unit_value
                cache_key = f'{sku}_{pud.unit}'
                self.cached_qty[cache_key] = pud.unit_value
                self.ui.qty_sales_return_combobox.addItem(pud.unit)


    def set_sales_return_form_data(self, data: DetailSalesReturnModel):
        self.ui.sku_sales_return_input.setText(data.sku)
        self.ui.product_name_sales_return_input.setText(data.product_name)
        self.ui.price_sales_return_input.setText(data.price)
        self.ui.qty_sales_return_input.setText(data.qty)
        self.ui.qty_sales_return_combobox.setCurrentText(data.unit)
        self.ui.unit_value_sales_return_input.setText(format_number(data.unit_value))


    def set_sales_return_by_id(self, sales_return_id: str):
        self.clear_sales_return()

        self.ui.sales_return_id_input.setText(sales_return_id)

        sales_return_result = self.sales_return_service.get_sales_return_by_id(sales_return_id)
        detail_sales_return_result = self.sales_return_service.get_detail_sales_return_by_id(sales_return_id)

        if not sales_return_result.success:
            POSMessageBox.error(self, title=ERR, message=sales_return_result.message)
            return

        if not detail_sales_return_result.success:
            POSMessageBox.error(self, title=ERR, message=detail_sales_return_result.message)
            return
        

        # Set Sales Return Data
        self.ui.customer_in_sales_return_input.setText(str(sales_return_result.data.customer_id))
        self.on_handle_customer_enter()

        self.ui.total_sales_return_input.setText(add_prefix(format_number(str(sales_return_result.data.total_amount))))
        self.ui.remarks_sales_return_input.setText(str(sales_return_result.data.sales_return_remarks))

        # Set Detail Sales Return Data
        self.set_sales_return_table_data(detail_sales_return_result.data)

        self.is_loading_combo = False

        # Change Submit Button to Update Button
        self.ui.submit_sales_return_button.setText('Update')
        self.ui.submit_sales_return_button.clicked.disconnect()
        self.ui.submit_sales_return_button.clicked.connect(self.update_sales_return)


    # Getters
    # ===============
    def get_total_qty_in_sales_return(self, sku: str):
        total_qty = 0
        for row in range(self.detail_sales_return_table.rowCount()):
            if self.detail_sales_return_table.item(row, 0).text() == sku:
                qty_in_sales_return = remove_non_digit(self.detail_sales_return_table.item(row, 2).text())
                unit_value_in_sales_return = remove_non_digit(self.detail_sales_return_table.item(row, 4).text())
                total_qty += int(qty_in_sales_return) * int(unit_value_in_sales_return)

        return total_qty


    def get_sales_return_form_data(self) -> DetailSalesReturnModel:
        sku: str = self.ui.sku_sales_return_input.text().strip()
        name: str = self.ui.product_name_sales_return_input.text().strip()
        price: str = remove_non_digit(self.ui.price_sales_return_input.text().strip())
        qty: str = remove_non_digit(self.ui.qty_sales_return_input.text().strip())
        unit: str = self.ui.qty_sales_return_combobox.currentText().strip()
        unit_value: str = self.cached_qty[f'{sku}_{unit}']
        amount = (int(price) * int(qty))

        return DetailSalesReturnModel(
            sales_return_id = '',
            sku = sku,
            product_name = name,
            price = int(price),
            qty = int(qty),
            unit = unit,
            unit_value = int(unit_value),
            subtotal = int(amount)
        )
    

    def get_detail_sales_return(self) -> list[DetailSalesReturnModel]:
        '''
            Returns detail_sales_return
            
            detail_sales_return data is all the details from sales return table
        '''
        detail_sales_return: list[DetailSalesReturnModel] = []
        for row in range(self.detail_sales_return_table.rowCount()):
            sku = self.detail_sales_return_table.item(row, 0).text()
            product_name = self.detail_sales_return_table.item(row, 1).text()
            qty = remove_non_digit(self.detail_sales_return_table.item(row, 2).text())
            unit = self.detail_sales_return_table.item(row, 3).text()
            unit_value = remove_non_digit(self.detail_sales_return_table.item(row, 4).text())
            price = remove_non_digit(self.detail_sales_return_table.item(row, 5).text())
            subtotal = remove_non_digit(self.detail_sales_return_table.item(row, 6).text())

            detail_sales_return.append(
                DetailSalesReturnModel(
                    sales_return_id = '',
                    sku = sku,
                    product_name = product_name,
                    price = price,
                    qty = qty,
                    unit = unit,
                    unit_value = unit_value,
                    subtotal = subtotal,
                )
            )
            
        return detail_sales_return

    def get_selected_sales_return_table_data(self) -> DetailSalesReturnModel:
        selected_rows = self.detail_sales_return_table.selectedItems()
        if not selected_rows:
            return None

        row = selected_rows[0].row()
        sales_return_id = self.ui.sales_return_id_input.text().strip() if self.ui.sales_return_id_input.text().strip() else ''
        sku = self.detail_sales_return_table.item(row, 0).text()
        product_name = self.detail_sales_return_table.item(row, 1).text()
        qty = remove_non_digit(self.detail_sales_return_table.item(row, 2).text())
        unit = self.detail_sales_return_table.item(row, 3).text()
        unit_value = remove_non_digit(self.detail_sales_return_table.item(row, 4).text())
        price = remove_non_digit(self.detail_sales_return_table.item(row, 5).text())
        subtotal = remove_non_digit(self.detail_sales_return_table.item(row, 6).text())

        return DetailSalesReturnModel(sales_return_id=sales_return_id, sku=sku, 
                    product_name=product_name, price=price, qty=qty, unit=unit, 
                    unit_value=unit_value, subtotal=subtotal)
    

    def get_added_updated_deleted_detail_sales_return(self, sales_return_id: str, detail_sales_return_data: list[DetailSalesReturnModel]):
        added_detail_sales_return: list[DetailSalesReturnModel] = []
        updated_detail_sales_return: list[DetailSalesReturnModel] = []
        deleted_detail_sales_return: list[DetailSalesReturnModel] = []

        if sales_return_id == '':
            sales_return_id = self.ui.sales_return_id_input.text().strip()

        # old_dsr_result is the detail sales return of the old sales return
        old_dsr_result = self.sales_return_service.get_detail_sales_return_by_id(sales_return_id)
        if not old_dsr_result.success:
            return (added_detail_sales_return, updated_detail_sales_return, deleted_detail_sales_return)

        # Get Set of Old Detail Sales Return        
        set_of_old_dsr: set[tuple[str, str]] = set()
        map_of_old_dsr: dict[tuple[str, str], DetailSalesReturnModel] = {}
        for dsr in old_dsr_result.data:
            set_of_old_dsr.add((dsr.sku, dsr.unit))
            map_of_old_dsr[(dsr.sku, dsr.unit)] = dsr

        # Get Set of New Detail Sales Return and Get Added and Updated Detail Sales Return
        set_of_new_dsr: set[tuple[str, str]] = set()
        for dsr in detail_sales_return_data:
            dsr.sales_return_id = sales_return_id
            if (dsr.sku, dsr.unit) in set_of_old_dsr: # If the new DSR is in the old DSR, then it is an updated DSR
                updated_detail_sales_return.append(dsr)

            elif (dsr.sku, dsr.unit) not in set_of_old_dsr: # If the new DSR not in the old DSR, then it is an added DSR
                added_detail_sales_return.append(dsr)

            set_of_new_dsr.add((dsr.sku, dsr.unit))

        # Get Deleted Detail Sales Return
        for old_dsr in set_of_old_dsr:
            if old_dsr not in set_of_new_dsr:
                # If the old DSR not in the new DSR, then it is a deleted DSR
                deleted_detail_sales_return.append(map_of_old_dsr[old_dsr])

        return (added_detail_sales_return, updated_detail_sales_return, deleted_detail_sales_return)
    

    # Signal Handlers
    # ===============
    def handle_customer_selected(self, customer_data):
        customer_id = customer_data['customer_id']
        customer_result = self.sales_return_service.get_customer_by_id(customer_id)
        if customer_result.success and customer_result.data:
            self.ui.customer_in_sales_return_input.setText(customer_id)
            self.ui.customer_name_in_sales_return_input.setText(customer_result.data.customer_name)

        self.ui.sku_sales_return_input.setFocus()


    def handle_product_selected(self, product_data):
        # Clear existing items
        self.ui.qty_sales_return_combobox.clear()

        # Set loading flag
        self.is_loading_combo = True
        sku = product_data['sku']

        product_result = self.sales_return_service.get_product_by_sku(sku)
        if product_result.success and product_result.data:
            # Fill the form fields with selected product data
            self.ui.sku_sales_return_input.setText(sku)
            self.ui.product_name_sales_return_input.setText(product_result.data.product_name)
            self.ui.qty_sales_return_combobox.addItem(product_result.data.unit)
            self.ui.unit_value_sales_return_input.setText('1')

            # Cache the unit value
            cache_key = f'{sku}_{product_result.data.unit}'
            self.cached_qty[cache_key] = 1

            # Set product unit details
            self.set_product_unit_details(sku)

            # Set stock
            stock = product_result.data.stock
            self.ui.stock_sales_return_input.setText(format_number(str(stock)))
            self.ui.stock_after_sales_return_input.setText(format_number(str(stock)))

            # Set color based on stock level
            if stock < 0:   
                self.ui.stock_sales_return_input.setText(f'-{format_number(str(stock))}')
                self.ui.stock_after_sales_return_input.setText(f'-{format_number(str(stock))}')
                self.ui.stock_sales_return_input.setStyleSheet('color: red;')
                self.ui.stock_after_sales_return_input.setStyleSheet('color: red;')

            
            # Set focus to price input
            self.ui.price_sales_return_input.setFocus()

        # Reset loading flag
        self.is_loading_combo = False


    # Calculate
    # ===============
    def calculate_stock_after_sales_return(self, sku: str, unit: str):
        cache_key = f'{sku}_{unit}'
        if cache_key in self.cached_qty:
            # Get initial stock
            product_result = self.sales_return_service.get_product_by_sku(sku)
            initial_stock = 0
            if product_result.success and product_result.data:
                initial_stock = product_result.data.stock

            self.ui.stock_sales_return_input.setText(format_number(str(initial_stock)))
            self.ui.stock_sales_return_input.setStyleSheet('color: black;')

            if initial_stock < 0:
                self.ui.stock_sales_return_input.setText(f'-{format_number(str(abs(initial_stock)))}')
                self.ui.stock_sales_return_input.setStyleSheet('color: red;')

            # Get total qty in sales return table for this sku and unit
            total_qty_in_sales_return = self.get_total_qty_in_sales_return(sku)
            
            # Calculate and display stock after sales return
            stock_after = initial_stock - total_qty_in_sales_return
            
            # Set color based on stock level
            self.ui.stock_after_sales_return_input.setText(format_number(str(stock_after)))
            self.ui.stock_after_sales_return_input.setStyleSheet('color: black;')

            if stock_after < 0:
                self.ui.stock_after_sales_return_input.setText(f'-{format_number(str(abs(stock_after)))}')
                self.ui.stock_after_sales_return_input.setStyleSheet('color: red;')



    def calculate_total_sales_return(self):
        total_amount = 0
        for row in range(self.detail_sales_return_table.rowCount()):
            total_amount += int(remove_non_digit(self.detail_sales_return_table.item(row, 6).text()))
        return total_amount


    # Clears
    # ===============
    def clear_sales_return(self):
        # Reset button text to Submit
        self.ui.submit_sales_return_button.setText('Submit')
        self.ui.submit_sales_return_button.clicked.disconnect()
        self.ui.submit_sales_return_button.clicked.connect(self.submit_sales_return)
        self.ui.sales_return_id_input.setText('')

        # Remove All Items from Sales Return Table
        self.detail_sales_return_table.setRowCount(0)
        self.ui.total_sales_return_input.setText(add_prefix('0'))
        self.cached_sales_return_index = {}
        self.cached_qty = {}
        self.ui.customer_in_sales_return_input.clear()
        self.ui.customer_name_in_sales_return_input.clear()
        self.clear_data_sales_return()


    def clear_data_sales_return(self):
        self.ui.sku_sales_return_input.clear()
        self.ui.product_name_sales_return_input.clear()
        self.ui.qty_sales_return_input.clear()
        self.ui.qty_sales_return_combobox.clear()
        self.ui.unit_value_sales_return_input.clear()
        self.ui.price_sales_return_input.clear()
        self.ui.stock_sales_return_input.clear()
        self.ui.stock_after_sales_return_input.clear()
        self.ui.remarks_sales_return_input.clear()


    # Event Filters
    # ===============
    def eventFilter(self, obj, event):
        # If price input is focused and key pressed is Enter it automatically set focus to qty input
        if obj == self.ui.price_sales_return_input and event.type() == QtCore.QEvent.Type.KeyPress:
            key = event.key()

            # Check for Enter
            if key in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
                text = remove_non_digit(self.ui.price_sales_return_input.text().strip())
              
                if text != '' and text.isdigit():
                    # If add button text is update, update the detail sales return
                    button_text = self.ui.add_sales_return_button.text().strip().lower()
                    if button_text == 'update':
                        self.update_detail_sales_return()
                        self.ui.sku_sales_return_input.setFocus()

                    else:
                        # Set focus to qty input
                        self.ui.qty_sales_return_input.setFocus()

                else:
                    self.ui.price_sales_return_input.clear()

                return True # prevent further processing
            
            if key == QtCore.Qt.Key.Key_Up:
                self.ui.sku_sales_return_input.setFocus()
                return True # prevent further processing


        # If qty input is focused and key pressed is Enter it automatically show the unit combobox or update
        if obj == self.ui.qty_sales_return_input and event.type() == QtCore.QEvent.Type.KeyPress:
            key = event.key()

            # Check for Enter
            if key in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
                text = remove_non_digit(self.ui.qty_sales_return_input.text().strip())
                if text != '' and text.isdigit():
                    # If add button text is update, update the detail transaction
                    button_text = self.ui.add_sales_return_button.text().strip().lower()
                    if button_text == 'update':
                        self.update_detail_sales_return()
                        self.ui.sku_sales_return_input.setFocus()

                    else:
                        # Show the unit combobox if is insert mode
                        self.ui.qty_sales_return_combobox.showPopup()

                else:
                    self.ui.qty_sales_return_input.clear()

                return True # prevent further processing
            
            if key == QtCore.Qt.Key.Key_Up:
                self.ui.price_sales_return_input.setFocus()
                return True # prevent further processing


        return super().eventFilter(obj, event)
    

    def keyPressEvent(self, event):
        if (event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier) and event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            button_text = self.ui.submit_sales_return_button.text().strip().lower()
            if button_text == 'update':
                self.update_sales_return()
                return
            
            self.submit_sales_return()
            return
        
        super().keyPressEvent(event)


    def closeEvent(self, event):
        """Override closeEvent to show home window when window is closed"""
        if self.home_window:
            self.home_window.show()
            self.home_window.raise_()
            self.home_window.activateWindow()
            
        event.accept()


    def on_handle_customer_enter(self):
        customer_text = self.ui.customer_in_sales_return_input.text().strip()

         # Try to find exact SKU match
        result = self.sales_return_service.get_customer_by_id(customer_text)
        if result.success and result.data:
            # Customer found - fill the form
            self.handle_customer_selected({'customer_id' : customer_text})
            
            # Set focus to sku input
            self.ui.sku_sales_return_input.setFocus()

        else:
            # Customer not found - show dialog with filter
            self.customers_dialog.set_filter(customer_text)
            self.customers_dialog.show()
    


    # Event Listeners
    # ===============
    def on_handle_sku_enter(self):
        sku = self.ui.sku_sales_return_input.text().strip().upper()
        if not sku:
            self.clear_data_sales_return()
            return

        # Try to find exact SKU match
        result = self.sales_return_service.get_product_by_sku(sku)
        if result.success and result.data:
            # Product found - fill the form
            self.handle_product_selected({'sku' : sku})
            
            # Set focus to price input
            self.ui.price_sales_return_input.setFocus()

        else:
            # Product not found - show dialog with filter
            self.products_dialog.set_filter(sku)
            self.products_dialog.show()


    def on_price_sales_return_input_changed(self):
        # Disconnect price input event listener
        self.ui.price_sales_return_input.textChanged.disconnect()

        # Update price input
        price = remove_non_digit(self.ui.price_sales_return_input.text().strip()) if remove_non_digit(self.ui.price_sales_return_input.text().strip()) != '' else '0'
        self.ui.price_sales_return_input.setText(add_prefix(format_number(str(int(price)))))

        # Reconnect price input event listener
        self.ui.price_sales_return_input.textChanged.connect(self.on_price_sales_return_input_changed)


    def on_qty_sales_return_combobox_changed(self, text):
        # Skip if we're loading items
        if self.is_loading_combo:
            return
            
        sku = self.ui.sku_sales_return_input.text().strip()
        cache_key = f'{sku}_{text}'
        if cache_key in self.cached_qty:
            unit_value: str = str(self.cached_qty[cache_key])
            self.ui.unit_value_sales_return_input.setText(format_number(unit_value))
            
            # Calculate stock after existing transactions for new unit
            self.calculate_stock_after_sales_return(sku, text)

        # Update qty on input changed
        self.on_qty_sales_return_input_changed()


    def on_qty_sales_return_input_changed(self):
        sku = self.ui.sku_sales_return_input.text().strip()
        unit = self.ui.qty_sales_return_combobox.currentText()
        unit_value = remove_non_digit(self.ui.unit_value_sales_return_input.text())
        qty = remove_non_digit(self.ui.qty_sales_return_input.text()) if self.ui.qty_sales_return_input.text() else '0'
        stock = self.ui.stock_sales_return_input.text().replace('.', '').strip()

        if qty == '' or stock == '':
            self.ui.stock_after_sales_return_input.setStyleSheet('color: black;')
            self.calculate_stock_after_sales_return(sku, unit)
            return
        
        total_qty_in_sales_return = self.get_total_qty_in_sales_return(sku)

        qty_after_transaction = int(stock) + (int(qty) * int(unit_value)) + total_qty_in_sales_return
        self.ui.stock_after_sales_return_input.setText(format_number(str(qty_after_transaction)))
    
        self.ui.stock_after_sales_return_input.setStyleSheet('color: black;')
        if qty_after_transaction < 0:
            # add negative sign to stock after sales return
            self.ui.stock_after_sales_return_input.setText(f'-{format_number(str(qty_after_transaction))}')
            self.ui.stock_after_sales_return_input.setStyleSheet('color: red;')


    def on_unit_selected(self):
        qty_text = self.ui.qty_sales_return_input.text()
        # Only proceed if qty is a valid number and not empty
        if qty_text.isdigit() and int(qty_text) > 0:
            self.add_detail_sales_return()
            self.ui.sku_sales_return_input.setFocus()