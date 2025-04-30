from PyQt6 import QtWidgets, uic

from dialogs.price_unit_dialog.services.price_unit_dialog_services import PriceUnitDialogService
from dialogs.price_unit_dialog.models.price_unit_dialog_models import PriceUnitTableItemModel, PriceUnitsModel

from helper import format_number, add_prefix, remove_non_digit
from generals.build import resource_path
from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import (
    RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS,
    PERM_C_PRODUCTS, PERM_U_PRODUCTS, PERM_D_PRODUCTS, PERM_R_PRODUCTS
)
from generals.messages import (
    ERR, OK, WARNING, CONFIRM, ERR_PERM_C_PRODUCTS, ERR_PERM_U_PRODUCTS, 
    ERR_PERM_D_PRODUCTS, ERR_PERM_R_PRODUCTS, PERM_DENIED
)
from dialogs.price_unit_dialog.translations import PRICE_UNIT_DIALOG_TRANSLATIONS
from generals.language_manager import LanguageManager
from generals.permission_manager import PermissionManager


class PriceUnitDialogWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_R_PRODUCTS):
            return

        self.ui = uic.loadUi(resource_path('ui/price_unit.ui'), self)

        # Init Services
        self.price_unit_dialog_service = PriceUnitDialogService()

        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(PRICE_UNIT_DIALOG_TRANSLATIONS)

        # Init Table
        self.price_unit_table = self.ui.price_unit_table
        
        
        # Init Button
        self.ui.delete_price_unit_button.clicked.connect(self.delete_price_unit)
        self.ui.edit_price_unit_button.clicked.connect(self.edit_price_unit)
        self.ui.create_new_price_unit_button.clicked.connect(self.create_new_price_unit_form)
        self.ui.clear_data_price_unit_button.clicked.connect(self.clear_price_unit_form)
        self.ui.submit_price_unit_button.clicked.connect(self.submit_price_unit)
        self.ui.close_price_unit_button.clicked.connect(lambda: self.close())

        self.ui.unit_value_price_unit_input.textChanged.connect(self.on_number_input_changed)
        self.ui.price_price_unit_input.textChanged.connect(self.on_number_input_changed)

        # Set selection behavior to select entire rows
        self.price_unit_table.setSelectionBehavior(SELECT_ROWS)
        self.price_unit_table.setSelectionMode(SINGLE_SELECTION)

        self.price_unit_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties
        self.price_unit_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.price_unit_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
    


    # Overrides
    # ===============
    def showEvent(self, event):
        super().showEvent(event)

        if not self.permission_manager.has_permission(PERM_R_PRODUCTS):
            POSMessageBox.warning(self, title=PERM_DENIED, message=ERR_PERM_R_PRODUCTS)
            self.close()
            return

        self.language_manager.translate_widget_text(self)

        self.price_unit_headers = ['Unit', 'Barcode', 'Unit Value', 'Price']
        if self.language_manager.get_current_language() == 'id':
            self.price_unit_headers = ['Satuan', 'Barcode', 'Nilai Satuan', 'Harga']

        self.language_manager.translate_table_headers(self.price_unit_table, self.price_unit_headers)


    def create_new_price_unit_form(self):
        self.clear_price_unit_form()
        self.set_enabled_form(True)


    def submit_price_unit(self):
        if not self.permission_manager.has_permission(PERM_C_PRODUCTS):
            POSMessageBox.error(self, title=ERR, message=ERR_PERM_C_PRODUCTS)
            return

        # Get data from table
        price_unit_data = self.get_price_unit_form_data()

        if price_unit_data is None or price_unit_data.unit == '' or price_unit_data.unit_value == '' or price_unit_data.price == '':
            POSMessageBox.error(self, title=ERR, message='Please fill all the fields')
            return
        
        if int(price_unit_data.unit_value) <= 0:
            POSMessageBox.error(self, title=ERR, message='Unit value cannot be 0 or lower than 0')
            return
        

        if int(price_unit_data.price) <= 0:
            POSMessageBox.error(self, title=ERR, message='Price cannot be 0 or lower than 0')
            return


        sku = self.ui.sku_price_unit_input.text().strip()
     
        price_unit_table_item = PriceUnitsModel(
            sku=sku,
            unit=price_unit_data.unit.upper(),
            barcode=price_unit_data.barcode,
            unit_value=price_unit_data.unit_value,
            price=price_unit_data.price
        )

        # Submit data
        result = self.price_unit_dialog_service.submit_price_unit(price_unit_table_item)

        if result.success:
            POSMessageBox.info(self, title=OK, message=result.message)

            # Clear price unit form
            self.clear_price_unit_form()
          
            # Set price unit table
            sku = self.ui.sku_price_unit_input.text().strip()
            self.set_price_unit_form_by_sku(sku)
            
        else:
            POSMessageBox.error(self, title=ERR, message=result.message)
    

    def edit_price_unit(self):
        # Get selected row
        selected_row = self.price_unit_table.selectedItems()
        if selected_row:
            # Get price unit data from table
            price_unit_data = self.get_selected_price_unit()

            # Set data to form
            self.set_price_unit_form_data(price_unit_data)

            # Enable form unless unit
            self.set_enabled_form(True)
            self.ui.unit_price_unit_input.setEnabled(False)
            self.ui.unit_price_unit_input.setClearButtonEnabled(False)

            # Change button text
            self.ui.submit_price_unit_button.setText('Update')
            self.ui.submit_price_unit_button.disconnect()
            self.ui.submit_price_unit_button.clicked.connect(self.update_price_unit)


    def update_price_unit(self):
        if not self.permission_manager.has_permission(PERM_U_PRODUCTS):
            POSMessageBox.error(self, title=ERR, message=ERR_PERM_U_PRODUCTS)
            return

        # Get data from table
        price_unit_data = self.get_price_unit_form_data()

        if price_unit_data is None or price_unit_data.unit == '' or price_unit_data.unit_value == '' or price_unit_data.price == '':
            POSMessageBox.error(self, title=ERR, message='Please fill all the fields')
            return
        
        sku = self.ui.sku_price_unit_input.text().strip()
     
        price_unit_table_item = PriceUnitsModel(
            sku=sku,
            unit=price_unit_data.unit.upper(),
            barcode=price_unit_data.barcode,
            unit_value=price_unit_data.unit_value,
            price=price_unit_data.price
        )

        # Update Price Unit
        update_price_unit_result = self.price_unit_dialog_service.update_price_unit(price_unit_table_item)

        if update_price_unit_result.success:
            POSMessageBox.info(self, title=OK, message=update_price_unit_result.message)

            # Clear price unit form
            self.clear_price_unit_form()
          
            # Set price unit table
            sku = self.ui.sku_price_unit_input.text().strip()
            self.set_price_unit_form_by_sku(sku)

            # Enable unit input and its behavior
            self.ui.unit_price_unit_input.setEnabled(True)
            self.ui.unit_price_unit_input.setClearButtonEnabled(True)
            
        else:
            POSMessageBox.error(self, title=ERR, message=update_price_unit_result.message)


    def delete_price_unit(self):
        if not self.permission_manager.has_permission(PERM_D_PRODUCTS):
            POSMessageBox.error(self, title=ERR, message=ERR_PERM_D_PRODUCTS)
            return

        selected_rows = self.price_unit_table.selectedItems()
        if not selected_rows:
            POSMessageBox.warning(self, title=WARNING, message="Please select a price unit to delete")
            return

        row = selected_rows[0].row()
        sku = self.ui.sku_price_unit_input.text().strip()
        unit = self.price_unit_table.item(row, 0).text()

        # Confirm deletion
        confirm = POSMessageBox.confirm(
                        self, title=CONFIRM, 
                        message=f'Are you sure you want to delete {unit} from {sku} ?')

        if confirm:
            delete_price_unit_result = self.price_unit_dialog_service.delete_price_unit_by_sku_and_unit(sku, unit)

            if delete_price_unit_result.success:
                POSMessageBox.info(self, title=OK, message=delete_price_unit_result.message)

                # Remove the row from table
                self.price_unit_table.removeRow(row)

                # Clear price unit form
                self.clear_price_unit_form()
            
                # Set price unit table
                self.set_price_unit_form_by_sku(sku)

            else:
                POSMessageBox.error(self, title=ERR, message=delete_price_unit_result.message)


    # Setters
    # ===============
    def set_price_unit_table(self, data: list[PriceUnitTableItemModel]):
        self.price_unit_table.setRowCount(0)

        for price_unit in data:
            current_row = self.price_unit_table.rowCount()
            self.price_unit_table.insertRow(current_row)

            table_items =  [ 
                QtWidgets.QTableWidgetItem(price_unit.unit),
                QtWidgets.QTableWidgetItem(price_unit.barcode),
                QtWidgets.QTableWidgetItem(format_number(price_unit.unit_value)),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(price_unit.price))),
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.price_unit_table.setItem(current_row, col, item)

        self.price_unit_table.setSortingEnabled(True)


    def set_price_unit_form_by_sku(self, sku: str):
        self.clear_price_unit_form()

        product_result = self.price_unit_dialog_service.get_product_by_sku(sku)  
        if product_result.success and product_result.data:
            self.price_unit_table.setSortingEnabled(False)

            self.ui.sku_price_unit_input.setText(sku)
            self.ui.product_name_price_unit_input.setText(product_result.data.product_name)
            price_unit_table_items = [
                PriceUnitTableItemModel(
                    unit=product_result.data.unit,
                    barcode=product_result.data.barcode,
                    unit_value=1,
                    price=product_result.data.price
                )
            ]

            product_unit_result = self.price_unit_dialog_service.get_product_units_by_sku(sku)

            if product_unit_result.success and product_unit_result.data:
                price_unit_table_items.extend(product_unit_result.data)


            # Set Price Unit Table
            self.set_price_unit_table(price_unit_table_items)


    def set_price_unit_form_data(self, data: PriceUnitTableItemModel):
        self.ui.unit_price_unit_input.setText(data.unit)
        self.ui.barcode_price_unit_input.setText(data.barcode)
        self.ui.unit_value_price_unit_input.setText(format_number(str(data.unit_value)))
        self.ui.price_price_unit_input.setText(add_prefix(format_number(str(data.price))))


    def set_enabled_form(self, enabled: bool = True):
        self.ui.unit_price_unit_input.setEnabled(enabled)
        self.ui.barcode_price_unit_input.setEnabled(enabled)
        self.ui.unit_value_price_unit_input.setEnabled(enabled)
        self.ui.price_price_unit_input.setEnabled(enabled)
        self.ui.clear_data_price_unit_button.setEnabled(enabled)
        self.ui.submit_price_unit_button.setEnabled(enabled)

    
    # Getters
    # ===============
    def get_price_unit_form_data(self) -> PriceUnitTableItemModel | None:
        unit = self.ui.unit_price_unit_input.text().strip().upper()
        barcode = self.ui.barcode_price_unit_input.text().strip()
        unit_value = remove_non_digit(self.ui.unit_value_price_unit_input.text().strip())
        price = remove_non_digit(self.ui.price_price_unit_input.text())
        
        if unit == '' or unit_value == '' or price == '':
            return None

        return PriceUnitTableItemModel(
            unit=unit,
            barcode=barcode,
            unit_value=unit_value,
            price=price
        )


    def get_selected_price_unit(self) -> PriceUnitTableItemModel | None:
        selected_row = self.price_unit_table.selectedItems()
        if selected_row:
            current_selected_unit = selected_row[0].row()
            unit = self.price_unit_table.item(current_selected_unit, 0).text()
            barcode = self.price_unit_table.item(current_selected_unit, 1).text()
            unit_value = self.price_unit_table.item(current_selected_unit, 2).text()
            price = self.price_unit_table.item(current_selected_unit, 3).text()

            return PriceUnitTableItemModel(
                unit=unit,
                barcode=barcode,
                unit_value=unit_value,
                price=price
            )
        
        return None


    # Events Listeners
    # ===============
    def on_number_input_changed(self):
        self.ui.unit_value_price_unit_input.textChanged.disconnect()
        self.ui.price_price_unit_input.textChanged.disconnect()

        unit_value = remove_non_digit(self.ui.unit_value_price_unit_input.text().strip()) if remove_non_digit(self.ui.unit_value_price_unit_input.text().strip()) != '' else '0'
        price = remove_non_digit(self.ui.price_price_unit_input.text()) if remove_non_digit(self.ui.price_price_unit_input.text()) != '' else '0'

        self.ui.unit_value_price_unit_input.setText(format_number(str(int(unit_value))))
        self.ui.price_price_unit_input.setText(add_prefix(format_number(str(int(price)))))

        self.ui.unit_value_price_unit_input.textChanged.connect(self.on_number_input_changed)
        self.ui.price_price_unit_input.textChanged.connect(self.on_number_input_changed)


    # Clears
    # ===============
    def clear_price_unit_form(self):
        self.ui.unit_price_unit_input.clear()
        self.ui.barcode_price_unit_input.clear()
        self.ui.unit_value_price_unit_input.clear()
        self.ui.price_price_unit_input.clear()
       
        # Reset button text and submit button
        self.ui.submit_price_unit_button.setText('Submit')
        self.ui.submit_price_unit_button.disconnect()
        self.ui.submit_price_unit_button.clicked.connect(self.submit_price_unit)
