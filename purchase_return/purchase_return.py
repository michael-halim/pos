from PyQt6 import QtWidgets, uic, QtCore
from datetime import datetime

from dialogs.suppliers_dialog.suppliers_dialog import SuppliersDialogWindow
from dialogs.products_dialog.products_dialog import ProductsDialogWindow

from purchase_return.services.purchase_return_services import PurchaseReturnService
from purchase_return.models.purchase_return_models import PurchaseReturnModel, DetailPurchaseReturnModel

from helper import format_number, add_prefix, remove_non_digit
from generals.message_box import POSMessageBox
from generals.build import resource_path
from generals.fonts import POSFonts
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS,
    PERM_C_PURCHASE_RETURN, PERM_U_PURCHASE_RETURN,
    DATE_FORMAT_DDMMYYYY, DATE_EDIT_NO_BUTTONS
)
from generals.messages import (
    ERR, OK, PERM_DENIED, WARNING, CONFIRM,
    ERR_PERM_C_PURCHASE_RETURN,
    ERR_PERM_U_PURCHASE_RETURN,
)
from purchase_return.translations import PURCHASE_RETURN_TRANSLATIONS
from generals.permission_manager import PermissionManager
from generals.language_manager import LanguageManager


class PurchaseReturnWindow(QtWidgets.QWidget):
    def __init__(self, home_window: None):
        super().__init__()

        self.home_window = home_window

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_C_PURCHASE_RETURN):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_C_PURCHASE_RETURN)
            self.close()
            return
        
        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/purchase_return.ui'), self)

        # Init Services
        self.purchase_return_service = PurchaseReturnService()

        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(PURCHASE_RETURN_TRANSLATIONS)

        # Init Dialog
        self.suppliers_dialog = SuppliersDialogWindow()
        self.products_dialog = ProductsDialogWindow()

        # Init Tables
        self.detail_purchase_return_table = self.ui.detail_purchase_return_table

        # Connect the add button to add_transaction method
        self.ui.close_purchase_return_button.clicked.connect(lambda: self.close())
        self.ui.clear_data_purchase_return_button.clicked.connect(self.clear_data_purchase_return)
        self.ui.add_purchase_return_button.clicked.connect(self.add_detail_purchase_return)
        self.ui.edit_purchase_return_button.clicked.connect(self.edit_detail_purchase_return)
        self.ui.delete_purchase_return_button.clicked.connect(self.delete_detail_purchase_return)
        self.ui.submit_purchase_return_button.clicked.connect(self.submit_purchase_return)
        
        self.ui.find_supplier_in_purchase_return_button.clicked.connect(lambda: self.suppliers_dialog.show())
        self.ui.find_sku_purchase_return_button.clicked.connect(lambda: self.products_dialog.show())

        # Add selected tracking
        self.cached_qty = {} # key = <sku>_<unit>, value = (unit_value, price)
        self.cached_purchase_return_index = {} # key = <sku>_<unit>, value = purchase_return_table_index

        # Handle supplier selected
        self.suppliers_dialog.supplier_selected.connect(self.handle_supplier_selected)

        # Handle product selected
        self.products_dialog.product_selected.connect(self.handle_product_selected)

        # Listeners
        # ===========

        # Supplier in purchase return input
        self.ui.supplier_in_purchase_return_input.returnPressed.connect(self.on_handle_supplier_enter)

        # Connect qty combobox to update qty input
        self.ui.qty_purchase_return_combobox.currentTextChanged.connect(self.on_qty_purchase_return_combobox_changed)

        # Connect qty input to update stock after input
        self.ui.qty_purchase_return_input.textChanged.connect(self.on_qty_purchase_return_input_changed)

        # Connect return pressed signal
        self.ui.sku_purchase_return_input.returnPressed.connect(self.on_handle_sku_enter)

        # Connect price input event listener
        self.ui.price_purchase_return_input.textChanged.connect(self.on_price_purchase_return_input_changed)

        # Set date input
        self.ui.purchase_return_date_input.setDate(datetime.now())

        # UX For Shortcut
        # =================
        # Set focus to supplier input
        self.ui.supplier_in_purchase_return_input.setFocus()

        # Connect price input event listener
        self.ui.price_purchase_return_input.installEventFilter(self)

        # Connect qty input event listener
        self.ui.qty_purchase_return_input.installEventFilter(self)

        # Connect combobox activated signal
        self.ui.qty_purchase_return_combobox.activated.connect(self.on_unit_selected)

        self.ui.purchase_return_date_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)
        self.ui.purchase_return_date_input.setButtonSymbols(DATE_EDIT_NO_BUTTONS)


        # Set selection behavior to select entire rows
        self.detail_purchase_return_table.setSelectionBehavior(SELECT_ROWS)
        self.detail_purchase_return_table.setSelectionMode(SINGLE_SELECTION)

        # Set wholesale transactions table to be read only
        self.detail_purchase_return_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties to resize to contents
        self.detail_purchase_return_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.detail_purchase_return_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)


    # Overrides
    # ===============
    def showMaximized(self):
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_C_PURCHASE_RETURN):
            self.close()
            return

        # Set window title
        if self.permission_manager.get_username().lower() not in self.windowTitle().lower():
            self.setWindowTitle(self.windowTitle() + ' - ' + self.permission_manager.get_username())


        # Translate widget text and update table headers
        self.language_manager.translate_widget_text(self)

        self.purchase_return_headers = ['SKU', 'Product Name', 'Qty', 'Unit', 'Unit Value', 'Price', 'Subtotal']
        if self.language_manager.get_current_language() == 'id':
            self.purchase_return_headers = ['Kode Barang', 'Nama Produk', 'Qty', 'Satuan', 'Nilai Satuan', 'Harga', 'Subtotal']

        self.language_manager.translate_table_headers(self.ui.detail_purchase_return_table, self.purchase_return_headers)


    def add_detail_purchase_return(self):
        # Stop temporary sorting
        self.detail_purchase_return_table.setSortingEnabled(False)
        try:
            purchase_return_form_data = self.get_purchase_return_form_data()

            items = [ purchase_return_form_data ]

            # Set purchase return table data
            self.set_purchase_return_table_data(items)

            # Calculate total purchase return
            total_amount = self.calculate_total_purchase_return()
            self.ui.total_purchase_return_input.setText(add_prefix(format_number(str(total_amount))))

            # Clear data
            self.clear_data_purchase_return()
                
        except Exception as e:
            POSMessageBox.error(self, title=ERR, message=f"Failed to add purchase return: {str(e)}")

        finally:
            # Re-enable sorting
            self.detail_purchase_return_table.setSortingEnabled(True)


    def edit_detail_purchase_return(self):
        # Get selected row
        selected_rows = self.detail_purchase_return_table.selectedItems()
        if not selected_rows:
            POSMessageBox.warning(self, title=WARNING, message="Please select a purchase return to edit")
            return

        self.current_selected_sku = selected_rows[0].row()

        # Disconnect existing connections and connect to update function
        self.ui.add_purchase_return_button.setText('Update')
        self.ui.add_purchase_return_button.clicked.disconnect()
        self.ui.add_purchase_return_button.clicked.connect(self.update_detail_purchase_return)

        # Get Selected Purchase Return Table Data
        purchase_return_table_data: DetailPurchaseReturnModel = self.get_selected_purchase_return_table_data()

        self.set_purchase_return_form_data(purchase_return_table_data)

        # Set focus to qty input
        self.ui.qty_purchase_return_input.setFocus()
        
        # Set Combobox to current unit and disable it
        if self.ui.qty_purchase_return_combobox.findText(purchase_return_table_data.unit) == -1:
            self.ui.qty_purchase_return_combobox.addItem(purchase_return_table_data.unit)

        self.ui.qty_purchase_return_combobox.setCurrentText(purchase_return_table_data.unit)
        self.ui.qty_purchase_return_combobox.setEnabled(False)
        
        # Make sure only qty is editable
        self.ui.price_purchase_return_input.setEnabled(True)
        self.ui.sku_purchase_return_input.setEnabled(False)
        self.ui.product_name_purchase_return_input.setEnabled(False)


    def update_detail_purchase_return(self):
        if self.current_selected_sku is not None:
            try:
                # Get the updated values
                qty = self.ui.qty_purchase_return_input.text().strip()
                price = remove_non_digit(self.ui.price_purchase_return_input.text())

                # Calculate new subtotal
                subtotal = int(price) * int(qty)
                
                # Update the row in the table
                self.detail_purchase_return_table.item(self.current_selected_sku, 2).setText(format_number(qty))
                self.detail_purchase_return_table.item(self.current_selected_sku, 5).setText(add_prefix(format_number(str(price))))
                self.detail_purchase_return_table.item(self.current_selected_sku, 6).setText(add_prefix(format_number(str(subtotal))))
                
                # Update total amount
                total_amount = self.calculate_total_purchase_return()
                self.ui.total_purchase_return_input.setText(add_prefix(format_number(str(total_amount))))

                # Reset the form
                self.clear_data_purchase_return()
                
                # Reset button and connection

                self.ui.add_purchase_return_button.setText('Add')
                self.ui.add_purchase_return_button.clicked.disconnect()
                self.ui.add_purchase_return_button.clicked.connect(self.add_detail_purchase_return)
                
                # Reset selection
                self.current_selected_sku = None
                
                # Re-enable all inputs
                self.ui.sku_purchase_return_input.setEnabled(True)
                self.ui.price_purchase_return_input.setEnabled(True)

            except Exception as e:
                POSMessageBox.error(self, title=ERR, message=f"Failed to update purchase return: {str(e)}")


    def delete_detail_purchase_return(self):
        selected_rows = self.detail_purchase_return_table.selectedItems()
        if not selected_rows:
            POSMessageBox.warning(self, title=WARNING, message="Please select a purchase return to delete")
            return

        # Confirm deletion
        confirm = POSMessageBox.confirm(self, title=CONFIRM, message="Are you sure you want to delete this purchase return ?")

        if confirm:
            row = selected_rows[0].row()

            # Get the transaction details before deletion
            sku = self.detail_purchase_return_table.item(row, 0).text()
            unit = self.detail_purchase_return_table.item(row, 3).text()

            # Remove from cached index
            purchase_return_index_key = f'{sku}_{unit}'
            if purchase_return_index_key in self.cached_purchase_return_index:
                del self.cached_purchase_return_index[purchase_return_index_key]

            # Remove the row from table
            self.detail_purchase_return_table.removeRow(row)

            # Update total amount
            total_amount: int = self.calculate_total_purchase_return()
            self.ui.total_purchase_return_input.setText(add_prefix(format_number(str(total_amount))))


    def submit_purchase_return(self):
        if not self.permission_manager.has_permission(PERM_C_PURCHASE_RETURN):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_C_PURCHASE_RETURN)
            return

        # Get detail purchase return from purchase return table
        detail_purchase_return_data: list[DetailPurchaseReturnModel] = self.get_detail_purchase_return()
        if len(detail_purchase_return_data) == 0:
            POSMessageBox.error(self, title=ERR, message="No purchase return to submit")
            return

        # Create purchase return id
        purchase_return_id: str = self.purchase_return_service.create_purchase_return_id()
        for detail in detail_purchase_return_data:
            detail.purchase_return_id = purchase_return_id

        # Calculate total amount
        total_amount: int = self.calculate_total_purchase_return()

        # Get Purchase Return Data
        purchase_return_remarks: str = self.ui.remarks_purchase_return_input.toPlainText().strip()
        supplier_id: str = self.ui.supplier_in_purchase_return_input.text().strip()


        # Create purchase return data
        purchase_return_data: PurchaseReturnModel = PurchaseReturnModel(
            purchase_return_id = purchase_return_id,
            supplier_id = supplier_id,
            purchase_return_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_amount = total_amount ,
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            created_by = self.permission_manager.get_user_id(),
            purchase_return_remarks = purchase_return_remarks,
            updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            updated_by = self.permission_manager.get_user_id()
        )

        # Submit purchase return
        result = self.purchase_return_service.submit_purchase_return(purchase_return_data, detail_purchase_return_data)
        if result.success:
            POSMessageBox.info(self, title=OK, message=result.message)
            
            # Clear the purchase return table and total
            self.clear_purchase_return()

        else:
            POSMessageBox.error(self, title=ERR, message=result.message)


    def update_purchase_return(self):
        if not self.permission_manager.has_permission(PERM_U_PURCHASE_RETURN):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_U_PURCHASE_RETURN)
            return

        # Get detail purchase return from purchase return table
        detail_purchase_return_data: list[DetailPurchaseReturnModel] = self.get_detail_purchase_return()
        if len(detail_purchase_return_data) == 0:
            POSMessageBox.error(self, title=ERR, message="No purchase return to update")
            return

        # Create purchase return id
        purchase_return_id: str = self.ui.purchase_return_id_input.text().strip()

        # Calculate total amount and total discount
        total_amount: int = self.calculate_total_purchase_return()

        # Get Purchase Return Data
        purchase_return_remarks: str = self.ui.remarks_purchase_return_input.toPlainText().strip()
        supplier_id: str = self.ui.supplier_in_purchase_return_input.text().strip()


        # Create purchase return data
        purchase_return_data: PurchaseReturnModel = PurchaseReturnModel(
            purchase_return_id = purchase_return_id,
            supplier_id = supplier_id,
            purchase_return_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_amount = total_amount,
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            created_by = self.permission_manager.get_user_id(),
            purchase_return_remarks = purchase_return_remarks,
            updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            updated_by = self.permission_manager.get_user_id()
        )

        # Get added, updated, and deleted detail purchase return
        added_detail_purchase_return, updated_detail_purchase_return, deleted_detail_purchase_return = self.get_added_updated_deleted_detail_purchase_return(purchase_return_id, detail_purchase_return_data)

        # Update purchase return
        result = self.purchase_return_service.update_purchase_return(purchase_return_data, added_detail_purchase_return, updated_detail_purchase_return, deleted_detail_purchase_return)
        if result.success:
            POSMessageBox.info(self, title=OK, message=result.message)
            
            # Clear the purchase return table and total
            self.clear_purchase_return()

        else:
            POSMessageBox.error(self, title=ERR, message=result.message)

    
    # Setters
    # ===============
    def set_purchase_return_table_data(self, data: list[DetailPurchaseReturnModel]):
        for item in data:
            purchase_return_index_key = f'{item.sku}_{item.unit}'
            if purchase_return_index_key in self.cached_purchase_return_index:
                idx = self.cached_purchase_return_index[purchase_return_index_key]
                price: str = remove_non_digit(self.detail_purchase_return_table.item(idx, 5).text())
                updated_qty: int = int(remove_non_digit(self.detail_purchase_return_table.item(idx, 2).text())) + int(item.qty)
                updated_amount: int = int(price) * int(updated_qty)

                self.detail_purchase_return_table.item(idx, 2).setText(format_number(str(updated_qty)))
                self.detail_purchase_return_table.item(idx, 6).setText(add_prefix(format_number(str(updated_amount))))

            else:
                current_row = self.detail_purchase_return_table.rowCount()
                self.detail_purchase_return_table.insertRow(current_row)

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
                    self.detail_purchase_return_table.setItem(current_row, col, item)

                # Add purchase return index
                self.cached_purchase_return_index[purchase_return_index_key] = current_row

        self.detail_purchase_return_table.setSortingEnabled(True)


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

        product_unit_details = self.purchase_return_service.get_product_unit_details(sku)
        if product_unit_details.success and product_unit_details.data:
            for pud in product_unit_details.data:
                # key = <sku>_<unit>, value = unit_value
                cache_key = f'{sku}_{pud.unit}'
                self.cached_qty[cache_key] = pud.unit_value
                self.ui.qty_purchase_return_combobox.addItem(pud.unit)


    def set_purchase_return_form_data(self, data: DetailPurchaseReturnModel):
        self.ui.sku_purchase_return_input.setText(data.sku)
        self.ui.product_name_purchase_return_input.setText(data.product_name)
        self.ui.price_purchase_return_input.setText(data.price)
        self.ui.qty_purchase_return_input.setText(data.qty)
        self.ui.qty_purchase_return_combobox.setCurrentText(data.unit)
        self.ui.unit_value_purchase_return_input.setText(format_number(data.unit_value))


    def set_purchase_return_by_id(self, purchase_return_id: str):
        self.clear_purchase_return()

        self.ui.purchase_return_id_input.setText(purchase_return_id)

        purchase_return_result = self.purchase_return_service.get_purchase_return_by_id(purchase_return_id)
        detail_purchase_return_result = self.purchase_return_service.get_detail_purchase_return_by_id(purchase_return_id)

        if not purchase_return_result.success:
            POSMessageBox.error(self, title=ERR, message=purchase_return_result.message)
            return

        if not detail_purchase_return_result.success:
            POSMessageBox.error(self, title=ERR, message=detail_purchase_return_result.message)
            return
        

        # Set Purchase Return Data
        self.ui.supplier_in_purchase_return_input.setText(str(purchase_return_result.data.supplier_id))
        self.on_handle_supplier_enter()

        self.ui.total_purchase_return_input.setText(add_prefix(format_number(str(purchase_return_result.data.total_amount))))
        self.ui.remarks_purchase_return_input.setText(str(purchase_return_result.data.purchase_return_remarks))

        # Set Detail Purchase Return Data
        self.set_purchase_return_table_data(detail_purchase_return_result.data)

        self.is_loading_combo = False

        # Change Submit Button to Update Button
        self.ui.submit_purchase_return_button.setText('Update')
        self.ui.submit_purchase_return_button.clicked.disconnect()
        self.ui.submit_purchase_return_button.clicked.connect(self.update_purchase_return)


    # Getters
    # ===============
    def get_total_qty_in_purchase_return(self, sku: str):
        total_qty = 0
        for row in range(self.detail_purchase_return_table.rowCount()):
            if self.detail_purchase_return_table.item(row, 0).text() == sku:
                qty_in_purchase_return = remove_non_digit(self.detail_purchase_return_table.item(row, 2).text())
                unit_value_in_purchase_return = remove_non_digit(self.detail_purchase_return_table.item(row, 4).text())
                total_qty += int(qty_in_purchase_return) * int(unit_value_in_purchase_return)

        return total_qty


    def get_purchase_return_form_data(self) -> DetailPurchaseReturnModel:
        sku: str = self.ui.sku_purchase_return_input.text().strip()
        name: str = self.ui.product_name_purchase_return_input.text().strip()
        price: str = remove_non_digit(self.ui.price_purchase_return_input.text().strip())
        qty: str = remove_non_digit(self.ui.qty_purchase_return_input.text().strip())
        unit: str = self.ui.qty_purchase_return_combobox.currentText().strip()
        unit_value: str = self.cached_qty[f'{sku}_{unit}']
        amount = (int(price) * int(qty))

        return DetailPurchaseReturnModel(
            purchase_return_id = '',
            sku = sku,
            product_name = name,
            price = int(price),
            qty = int(qty),
            unit = unit,
            unit_value = int(unit_value),
            subtotal = int(amount)
        )
    

    def get_detail_purchase_return(self) -> list[DetailPurchaseReturnModel]:
        '''
            Returns detail_purchase_return
            
            detail_purchase_return data is all the details from purchase return table
        '''
        detail_purchase_return: list[DetailPurchaseReturnModel] = []
        for row in range(self.detail_purchase_return_table.rowCount()):
            sku = self.detail_purchase_return_table.item(row, 0).text()
            product_name = self.detail_purchase_return_table.item(row, 1).text()
            qty = remove_non_digit(self.detail_purchase_return_table.item(row, 2).text())
            unit = self.detail_purchase_return_table.item(row, 3).text()
            unit_value = remove_non_digit(self.detail_purchase_return_table.item(row, 4).text())
            price = remove_non_digit(self.detail_purchase_return_table.item(row, 5).text())
            subtotal = remove_non_digit(self.detail_purchase_return_table.item(row, 6).text())

            detail_purchase_return.append(
                DetailPurchaseReturnModel(
                    purchase_return_id = '',
                    sku = sku,
                    product_name = product_name,
                    price = price,
                    qty = qty,
                    unit = unit,
                    unit_value = unit_value,
                    subtotal = subtotal,
                )
            )
            
        return detail_purchase_return

    def get_selected_purchase_return_table_data(self) -> DetailPurchaseReturnModel:
        selected_rows = self.detail_purchase_return_table.selectedItems()
        if not selected_rows:
            return None

        row = selected_rows[0].row()
        purchase_return_id = self.ui.purchase_return_id_input.text().strip() if self.ui.purchase_return_id_input.text().strip() else ''
        sku = self.detail_purchase_return_table.item(row, 0).text()
        product_name = self.detail_purchase_return_table.item(row, 1).text()
        qty = remove_non_digit(self.detail_purchase_return_table.item(row, 2).text())
        unit = self.detail_purchase_return_table.item(row, 3).text()
        unit_value = remove_non_digit(self.detail_purchase_return_table.item(row, 4).text())
        price = remove_non_digit(self.detail_purchase_return_table.item(row, 5).text())
        subtotal = remove_non_digit(self.detail_purchase_return_table.item(row, 6).text())

        return DetailPurchaseReturnModel(purchase_return_id=purchase_return_id, sku=sku, 
                    product_name=product_name, price=price, qty=qty, unit=unit, 
                    unit_value=unit_value, subtotal=subtotal)
    

    def get_added_updated_deleted_detail_purchase_return(self, purchase_return_id: str, detail_purchase_return_data: list[DetailPurchaseReturnModel]):
        added_detail_purchase_return: list[DetailPurchaseReturnModel] = []
        updated_detail_purchase_return: list[DetailPurchaseReturnModel] = []
        deleted_detail_purchase_return: list[DetailPurchaseReturnModel] = []

        if purchase_return_id == '':
            purchase_return_id = self.ui.purchase_return_id_input.text().strip()

        # old_dpr_result is the detail purchase return of the old purchase return
        old_dpr_result = self.purchase_return_service.get_detail_purchase_return_by_id(purchase_return_id)
        if not old_dpr_result.success:
            return (added_detail_purchase_return, updated_detail_purchase_return, deleted_detail_purchase_return)

        # Get Set of Old Detail Purchase Return        
        set_of_old_dpr: set[tuple[str, str]] = set()
        map_of_old_dpr: dict[tuple[str, str], DetailPurchaseReturnModel] = {}
        for dpr in old_dpr_result.data:
            set_of_old_dpr.add((dpr.sku, dpr.unit))
            map_of_old_dpr[(dpr.sku, dpr.unit)] = dpr

        # Get Set of New Detail Purchase Return and Get Added and Updated Detail Purchase Return
        set_of_new_dpr: set[tuple[str, str]] = set()
        for dpr in detail_purchase_return_data:
            dpr.purchase_return_id = purchase_return_id
            if (dpr.sku, dpr.unit) in set_of_old_dpr: # If the new DPR is in the old DPR, then it is an updated DPR
                updated_detail_purchase_return.append(dpr)

            elif (dpr.sku, dpr.unit) not in set_of_old_dpr: # If the new DPR not in the old DPR, then it is an added DPR
                added_detail_purchase_return.append(dpr)

            set_of_new_dpr.add((dpr.sku, dpr.unit))

        # Get Deleted Detail Purchase Return
        for old_dpr in set_of_old_dpr:
            if old_dpr not in set_of_new_dpr:
                # If the old DPR not in the new DPR, then it is a deleted DPR
                deleted_detail_purchase_return.append(map_of_old_dpr[old_dpr])

        return (added_detail_purchase_return, updated_detail_purchase_return, deleted_detail_purchase_return)
    

    # Signal Handlers
    # ===============
    def handle_supplier_selected(self, supplier_data):
        supplier_id = supplier_data['supplier_id']
        supplier_result = self.purchase_return_service.get_supplier_by_id(supplier_id)
        if supplier_result.success and supplier_result.data:
            self.ui.supplier_in_purchase_return_input.setText(supplier_id)
            self.ui.supplier_name_in_purchase_return_input.setText(supplier_result.data.supplier_name)

        self.ui.sku_purchase_return_input.setFocus()


    def handle_product_selected(self, product_data):
        # Clear existing items
        self.ui.qty_purchase_return_combobox.clear()

        # Set loading flag
        self.is_loading_combo = True
        sku = product_data['sku']

        product_result = self.purchase_return_service.get_product_by_sku(sku)
        if product_result.success and product_result.data:
            # Fill the form fields with selected product data
            self.ui.sku_purchase_return_input.setText(sku)
            self.ui.product_name_purchase_return_input.setText(product_result.data.product_name)
            self.ui.qty_purchase_return_combobox.addItem(product_result.data.unit)
            self.ui.unit_value_purchase_return_input.setText('1')

            # Cache the unit value
            cache_key = f'{sku}_{product_result.data.unit}'
            self.cached_qty[cache_key] = 1

            # Set product unit details
            self.set_product_unit_details(sku)

            # Set stock
            stock = product_result.data.stock
            self.ui.stock_purchase_return_input.setText(format_number(str(stock)))
            self.ui.stock_after_purchase_return_input.setText(format_number(str(stock)))

            # Set color based on stock level
            if stock < 0:   
                self.ui.stock_purchase_return_input.setText(f'-{format_number(str(stock))}')
                self.ui.stock_after_purchase_return_input.setText(f'-{format_number(str(stock))}')
                self.ui.stock_purchase_return_input.setStyleSheet('color: red;')
                self.ui.stock_after_purchase_return_input.setStyleSheet('color: red;')

            
            # Set focus to price input
            self.ui.price_purchase_return_input.setFocus()

        # Reset loading flag
        self.is_loading_combo = False


    # Calculate
    # ===============
    def calculate_stock_after_purchase_return(self, sku: str, unit: str):
        cache_key = f'{sku}_{unit}'
        if cache_key in self.cached_qty:
            # Get initial stock
            product_result = self.purchase_return_service.get_product_by_sku(sku)
            initial_stock = 0
            if product_result.success and product_result.data:
                initial_stock = product_result.data.stock

            self.ui.stock_purchase_return_input.setText(format_number(str(initial_stock)))
            self.ui.stock_purchase_return_input.setStyleSheet('color: black;')

            if initial_stock < 0:
                self.ui.stock_purchase_return_input.setText(f'-{format_number(str(abs(initial_stock)))}')
                self.ui.stock_purchase_return_input.setStyleSheet('color: red;')

            # Get total qty in purchase return table for this sku and unit
            total_qty_in_purchase_return = self.get_total_qty_in_purchase_return(sku)
            
            # Calculate and display stock after purchase return
            stock_after = initial_stock - total_qty_in_purchase_return
            
            # Set color based on stock level
            self.ui.stock_after_purchase_return_input.setText(format_number(str(stock_after)))
            self.ui.stock_after_purchase_return_input.setStyleSheet('color: black;')

            if stock_after < 0:
                self.ui.stock_after_purchase_return_input.setText(f'-{format_number(str(abs(stock_after)))}')
                self.ui.stock_after_purchase_return_input.setStyleSheet('color: red;')



    def calculate_total_purchase_return(self):
        total_amount = 0
        for row in range(self.detail_purchase_return_table.rowCount()):
            total_amount += int(remove_non_digit(self.detail_purchase_return_table.item(row, 6).text()))
        return total_amount


    # Clears
    # ===============
    def clear_purchase_return(self):
        # Reset button text to Submit
        self.ui.submit_purchase_return_button.setText('Submit')
        self.ui.submit_purchase_return_button.clicked.disconnect()
        self.ui.submit_purchase_return_button.clicked.connect(self.submit_purchase_return)
        self.ui.purchase_return_id_input.setText('')

        # Remove All Items from Purchase Return Table
        self.detail_purchase_return_table.setRowCount(0)
        self.ui.total_purchase_return_input.setText(add_prefix('0'))
        self.cached_purchase_return_index = {}
        self.cached_qty = {}
        self.ui.supplier_in_purchase_return_input.clear()
        self.ui.supplier_name_in_purchase_return_input.clear()
        self.clear_data_purchase_return()


    def clear_data_purchase_return(self):
        self.ui.sku_purchase_return_input.clear()
        self.ui.product_name_purchase_return_input.clear()
        self.ui.qty_purchase_return_input.clear()
        self.ui.qty_purchase_return_combobox.clear()
        self.ui.unit_value_purchase_return_input.clear()
        self.ui.price_purchase_return_input.clear()
        self.ui.stock_purchase_return_input.clear()
        self.ui.stock_after_purchase_return_input.clear()
        self.ui.remarks_purchase_return_input.clear()


    # Event Filters
    # ===============
    def eventFilter(self, obj, event):
        # If price input is focused and key pressed is Enter it automatically set focus to qty input
        if obj == self.ui.price_purchase_return_input and event.type() == QtCore.QEvent.Type.KeyPress:
            key = event.key()

            # Check for Enter
            if key in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
                text = remove_non_digit(self.ui.price_purchase_return_input.text().strip())
              
                if text != '' and text.isdigit():
                    # If add button text is update, update the detail purchase return
                    button_text = self.ui.add_purchase_return_button.text().strip().lower()
                    if button_text == 'update':
                        self.update_detail_purchase_return()
                        self.ui.sku_purchase_return_input.setFocus()

                    else:
                        # Set focus to qty input
                        self.ui.qty_purchase_return_input.setFocus()

                else:
                    self.ui.price_purchase_return_input.clear()

                return True # prevent further processing
            
            if key == QtCore.Qt.Key.Key_Up:
                self.ui.sku_purchase_return_input.setFocus()
                return True # prevent further processing


        # If qty input is focused and key pressed is Enter it automatically show the unit combobox or update
        if obj == self.ui.qty_purchase_return_input and event.type() == QtCore.QEvent.Type.KeyPress:
            key = event.key()

            # Check for Enter
            if key in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
                text = remove_non_digit(self.ui.qty_purchase_return_input.text().strip())
                if text != '' and text.isdigit():
                    # If add button text is update, update the detail transaction
                    button_text = self.ui.add_purchase_return_button.text().strip().lower()
                    if button_text == 'update':
                        self.update_detail_purchase_return()
                        self.ui.sku_purchase_return_input.setFocus()

                    else:
                        # Show the unit combobox if is insert mode
                        self.ui.qty_purchase_return_combobox.showPopup()

                else:
                    self.ui.qty_purchase_return_input.clear()

                return True # prevent further processing
            
            if key == QtCore.Qt.Key.Key_Up:
                self.ui.price_purchase_return_input.setFocus()
                return True # prevent further processing


        return super().eventFilter(obj, event)
    

    def keyPressEvent(self, event):
        if (event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier) and event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            button_text = self.ui.submit_purchase_return_button.text().strip().lower()
            if button_text == 'update':
                self.update_purchase_return()
                return
            
            self.submit_purchase_return()
            return
        
        super().keyPressEvent(event)


    def closeEvent(self, event):
        """Override closeEvent to show home window when window is closed"""
        if self.home_window:
            self.home_window.show()
            self.home_window.raise_()
            self.home_window.activateWindow()
            
        event.accept()


    def on_handle_supplier_enter(self):
        supplier_text = self.ui.supplier_in_purchase_return_input.text().strip()

         # Try to find exact SKU match
        result = self.purchase_return_service.get_supplier_by_id(supplier_text)
        if result.success and result.data:
            # Supplier found - fill the form
            self.handle_supplier_selected({'supplier_id' : supplier_text})
            
            # Set focus to sku input
            self.ui.sku_purchase_return_input.setFocus()

        else:
            # Supplier not found - show dialog with filter
            self.suppliers_dialog.set_filter(supplier_text)
            self.suppliers_dialog.show()
    


    # Event Listeners
    # ===============
    def on_handle_sku_enter(self):
        sku = self.ui.sku_purchase_return_input.text().strip().upper()
        if not sku:
            self.clear_data_purchase_return()
            return

        # Try to find exact SKU match
        result = self.purchase_return_service.get_product_by_sku(sku)
        if result.success and result.data:
            # Product found - fill the form
            self.handle_product_selected({'sku' : sku})
            
            # Set focus to price input
            self.ui.price_purchase_return_input.setFocus()

        else:
            # Product not found - show dialog with filter
            self.products_dialog.set_filter(sku)
            self.products_dialog.show()


    def on_price_purchase_return_input_changed(self):
        # Disconnect price input event listener
        self.ui.price_purchase_return_input.textChanged.disconnect()

        # Update price input
        price = remove_non_digit(self.ui.price_purchase_return_input.text().strip()) if remove_non_digit(self.ui.price_purchase_return_input.text().strip()) != '' else '0'
        self.ui.price_purchase_return_input.setText(add_prefix(format_number(str(int(price)))))

        # Reconnect price input event listener
        self.ui.price_purchase_return_input.textChanged.connect(self.on_price_purchase_return_input_changed)


    def on_qty_purchase_return_combobox_changed(self, text):
        # Skip if we're loading items
        if self.is_loading_combo:
            return
            
        sku = self.ui.sku_purchase_return_input.text().strip()
        cache_key = f'{sku}_{text}'
        if cache_key in self.cached_qty:
            unit_value: str = str(self.cached_qty[cache_key])
            self.ui.unit_value_purchase_return_input.setText(format_number(unit_value))
            
            # Calculate stock after existing transactions for new unit
            self.calculate_stock_after_purchase_return(sku, text)

        # Update qty on input changed
        self.on_qty_purchase_return_input_changed()


    def on_qty_purchase_return_input_changed(self):
        sku = self.ui.sku_purchase_return_input.text().strip()
        unit = self.ui.qty_purchase_return_combobox.currentText()
        unit_value = remove_non_digit(self.ui.unit_value_purchase_return_input.text())
        qty = remove_non_digit(self.ui.qty_purchase_return_input.text()) if self.ui.qty_purchase_return_input.text() else '0'
        stock = self.ui.stock_purchase_return_input.text().replace('.', '').strip()

        if qty == '' or stock == '':
            self.ui.stock_after_purchase_return_input.setStyleSheet('color: black;')
            self.calculate_stock_after_purchase_return(sku, unit)
            return
        
        total_qty_in_purchase_return = self.get_total_qty_in_purchase_return(sku)

        qty_after_transaction = int(stock) - (int(qty) * int(unit_value)) - total_qty_in_purchase_return
        self.ui.stock_after_purchase_return_input.setText(format_number(str(qty_after_transaction)))
    
        self.ui.stock_after_purchase_return_input.setStyleSheet('color: black;')
        if qty_after_transaction < 0:
            # add negative sign to stock after purchase return
            self.ui.stock_after_purchase_return_input.setText(f'-{format_number(str(qty_after_transaction))}')
            self.ui.stock_after_purchase_return_input.setStyleSheet('color: red;')


    def on_unit_selected(self):
        qty_text = self.ui.qty_purchase_return_input.text()
        # Only proceed if qty is a valid number and not empty
        if qty_text.isdigit() and int(qty_text) > 0:
            self.add_detail_purchase_return()
            self.ui.sku_purchase_return_input.setFocus()