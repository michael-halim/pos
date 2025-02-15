from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QDateEdit
from datetime import datetime

from helper import format_number, add_prefix, remove_non_digit

from dialogs.products_dialog import ProductsDialogWindow

from purchasing.purchasing_services.purchasing_services import PurchasingService
from purchasing.purchasing_models.purchasing_models import PurchasingTableItemModel

from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS, DATE_FORMAT_DDMMYYYY

class PurchasingWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.purchasing_service = PurchasingService()
        # Load the UI file
        self.ui = uic.loadUi('./ui/purchasing.ui', self)

        # Init Dialog
        self.products_dialog = ProductsDialogWindow()
        # self.suppliers_dialog = SuppliersDialogWindow()

        # Init Tables
        self.purchasing_detail_table = self.ui.purchasing_detail_table

        self.purchasing_detail_table.setSortingEnabled(True)

        # Connect the add button to add_transaction method
        self.ui.close_purchasing_button.clicked.connect(lambda: self.close())
        self.ui.clear_data_purchasing_button.clicked.connect(self.clear_data_purchasing)
        self.ui.master_stock_purchasing_button.clicked.connect(self.master_stock_purchasing)
        self.ui.add_purchasing_button.clicked.connect(self.add_purchasing)
        self.ui.find_sku_purchasing_button.clicked.connect(lambda: self.products_dialog.show())
        self.ui.edit_purchasing_button.clicked.connect(self.edit_purchasing)
        self.ui.delete_purchasing_button.clicked.connect(self.delete_purchasing)
        self.ui.submit_puchasing_button.clicked.connect(self.submit_purchasing)

        # Add selected tracking
        self.current_selected_sku = None
        self.cached_qty = {} # key = <sku>_<unit>, value = (unit_value, price)
        self.cached_purchasing_index = {} # key = <sku>_<unit>, value = purchasing_table_index

        # Handle product selected
        self.products_dialog.product_selected.connect(self.handle_product_selected)

        # Connect return pressed signal
        self.ui.sku_purchasing_input.returnPressed.connect(self.on_handle_sku_enter)

        # Set date input
        self.ui.purchasing_date_input.setDate(datetime.now())
        self.ui.invoice_date_purchasing_input.setDate(datetime.now())
        self.ui.invoice_expired_date_purchasing_input.setDate(datetime.now())

        self.ui.purchasing_date_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)
        self.ui.invoice_date_purchasing_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)
        self.ui.invoice_expired_date_purchasing_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)

        self.ui.purchasing_date_input.setButtonSymbols(QDateEdit.ButtonSymbols.NoButtons)
        self.ui.invoice_date_purchasing_input.setButtonSymbols(QDateEdit.ButtonSymbols.NoButtons)
        self.ui.invoice_expired_date_purchasing_input.setButtonSymbols(QDateEdit.ButtonSymbols.NoButtons)

        # Set selection behavior to select entire rows
        self.purchasing_detail_table.setSelectionBehavior(SELECT_ROWS)
        self.purchasing_detail_table.setSelectionMode(SINGLE_SELECTION)
        self.purchasing_history_table.setSelectionBehavior(SELECT_ROWS)
        self.purchasing_history_table.setSelectionMode(SINGLE_SELECTION)

        # Set wholesale transactions table to be read only
        self.purchasing_detail_table.setEditTriggers(NO_EDIT_TRIGGERS)
        self.purchasing_history_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties to resize to contents
        self.purchasing_detail_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.purchasing_detail_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.purchasing_history_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.purchasing_history_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)

    def clear_data_purchasing(self):
        self.ui.sku_purchasing_input.clear()
        self.ui.product_name_purchasing_input.clear()
        self.ui.price_purchasing_input.clear()
        self.ui.stock_purchasing_input.clear()
        self.ui.stock_after_purchasing_input.clear()
        self.ui.qty_purchasing_input.clear()
        self.ui.qty_purchasing_combobox.clear()
        self.ui.discount_rp_purchasing_input.clear()
        self.ui.discount_pct_purchasing_input.clear()
        self.ui.discount_total_purchasing_input.clear()
        self.ui.total_purchasing_input.clear()
        self.ui.remarks_purchasing_input.clear()

    def master_stock_purchasing(self):
        pass

    def add_purchasing(self):
        # Stop temporary sorting
        self.purchasing_detail_table.setSortingEnabled(False)

        try:
            sku: str = self.ui.sku_purchasing_input.text().strip()
            name: str = self.ui.product_name_purchasing_input.text().strip()
            price: str = remove_non_digit(self.ui.price_purchasing_input.text().strip())
            qty: str = remove_non_digit(self.ui.qty_purchasing_input.text().strip())
            unit: str = self.ui.qty_purchasing_combobox.currentText().strip()
            discount_rp: str = remove_non_digit(self.ui.discount_rp_purchasing_input.text()) if self.ui.discount_rp_purchasing_input.text() else '0'
            discount_pct: str = remove_non_digit(self.ui.discount_pct_purchasing_input.text()) if self.ui.discount_pct_purchasing_input.text() else '0'
            amount: str = str(int(price) * int(qty))

            items = [
                PurchasingTableItemModel(
                    sku=sku, product_name=name, price=price,
                    qty=qty, unit=unit, discount_rp=discount_rp, 
                    discount_pct=discount_pct, subtotal=amount
                )
            ]
            
            # Set purchasing table data
            self.set_purchasing_table_data(items)

            # Calculate total purchasing
            total_amount = self.calculate_total_purchasing()
            self.ui.total_purchasing_input.setText(add_prefix(format_number(str(total_amount))))

            self.clear_data_purchasing()
                
        except Exception as e:
            POSMessageBox.error(self, title='Error', message=f"Failed to add purchasing: {str(e)}")

        finally:
            # Re-enable sorting
            self.purchasing_detail_table.setSortingEnabled(True)
            

    def edit_purchasing(self):
        # Get selected row
        selected_rows = self.purchasing_detail_table.selectedItems()
        if selected_rows:
            self.current_selected_sku = selected_rows[0].row()

            self.ui.add_purchasing_button.setText('Update')
            
            # Disconnect existing connections and connect to update function
            self.ui.add_purchasing_button.clicked.disconnect()
            self.ui.add_purchasing_button.clicked.connect(self.update_purchasing)

            # Get sku, unit, unit_value, qty, price, discount_rp, discount_pct, subtotal
            sku = self.purchasing_detail_table.item(self.current_selected_sku, 0).text()
            product_name = self.purchasing_detail_table.item(self.current_selected_sku, 1).text()
            qty = remove_non_digit(self.purchasing_detail_table.item(self.current_selected_sku, 2).text())
            unit = self.purchasing_detail_table.item(self.current_selected_sku, 3).text()
            price = remove_non_digit(self.purchasing_detail_table.item(self.current_selected_sku, 4).text())
            discount_rp = remove_non_digit(self.purchasing_detail_table.item(self.current_selected_sku, 5).text())
            discount_pct = remove_non_digit(self.purchasing_detail_table.item(self.current_selected_sku, 6).text())

            # Put the data into the form
            self.ui.sku_purchasing_input.setText(sku)
            self.ui.product_name_purchasing_input.setText(product_name)
            self.ui.price_purchasing_input.setText(price)
            self.ui.qty_purchasing_input.setText(qty)
            self.ui.qty_purchasing_combobox.setCurrentText(unit)
            self.ui.discount_rp_purchasing_input.setText(discount_rp)
            self.ui.discount_pct_purchasing_input.setText(discount_pct)

            # Make sure only qty is editable
            self.ui.qty_purchasing_input.setReadOnly(False)
            self.ui.price_purchasing_input.setEnabled(False)
            self.ui.discount_rp_purchasing_input.setEnabled(True)
            self.ui.discount_pct_purchasing_input.setEnabled(True)
            self.ui.sku_purchasing_input.setEnabled(True)
            self.ui.product_name_purchasing_input.setEnabled(True)
    
    def update_purchasing(self):
        if self.current_selected_sku is not None:
            try:
                # Get the updated values
                qty = self.ui.qty_purchasing_input.text().strip()
                price = remove_non_digit(self.ui.price_purchasing_input.text())
                
                # Calculate new subtotal
                subtotal = int(price) * int(qty)
                
                # Update the row in the table
                self.purchasing_detail_table.item(self.current_selected_sku, 2).setText(format_number(qty))
                self.purchasing_detail_table.item(self.current_selected_sku, 7).setText(add_prefix(format_number(str(subtotal))))
                
                # Update total amount
                total = self.calculate_total_purchasing()
                self.ui.total_purchasing_input.setText(add_prefix(format_number(str(total))))

                # Reset the form
                self.clear_data_purchasing()
                
                # Reset button and connection
                self.ui.add_purchasing_button.setText('Add')
                self.ui.add_purchasing_button.clicked.disconnect()
                self.ui.add_purchasing_button.clicked.connect(self.add_purchasing)
                
                # Reset selection
                self.current_selected_sku = None
                
                # Re-enable all inputs
                self.ui.sku_purchasing_input.setEnabled(True)
                self.ui.discount_rp_purchasing_input.setEnabled(True)
                self.ui.discount_pct_purchasing_input.setEnabled(True)

            except Exception as e:
                POSMessageBox.error(self, title='Error', message=f"Failed to update purchasing: {str(e)}")


    def delete_purchasing(self):
        selected_rows = self.purchasing_detail_table.selectedItems()
        if not selected_rows:
            POSMessageBox.warning(self, title='Warning', message="Please select a purchasing to delete")
            return

        # Confirm deletion
        confirm = POSMessageBox.confirm(self, title="Confirm Deletion", message="Are you sure you want to delete this purchasing ?")

        if confirm:
            row = selected_rows[0].row()

            # Get the transaction details before deletion
            sku = self.purchasing_detail_table.item(row, 0).text()
            unit = self.purchasing_detail_table.item(row, 3).text()
            subtotal = remove_non_digit(self.purchasing_detail_table.item(row, 7).text())

            # Remove from cached index
            purchasing_index_key = f'{sku}_{unit}'
            if purchasing_index_key in self.cached_purchasing_index:
                del self.cached_purchasing_index[purchasing_index_key]

            # Remove the row from table
            self.purchasing_detail_table.removeRow(row)

            # Update total amount
            total_amount: int = self.calculate_total_purchasing() - int(subtotal)
            self.ui.total_purchasing_input.setText(add_prefix(format_number(str(total_amount))))

    def submit_purchasing(self):
        pass
    
    def calculate_total_purchasing(self) -> int:
        total_amount = 0
        for row in range(self.purchasing_detail_table.rowCount()):
            total_amount += int(remove_non_digit(self.purchasing_detail_table.item(row, 7).text()))
        return total_amount
    

    def handle_product_selected(self, product_data):
        # Clear existing items
        self.ui.qty_purchasing_combobox.clear()

        # Set loading flag
        self.is_loading_combo = True
        sku = product_data['sku']

        product_result = self.purchasing_service.get_product_by_sku(sku)
        if product_result.success and product_result.data:
            # Fill the form fields with selected product data
            self.ui.sku_purchasing_input.setText(sku)
            self.ui.product_name_purchasing_input.setText(product_result.data.product_name)
            self.ui.qty_purchasing_combobox.addItem(product_result.data.unit)

            stock = product_result.data.stock

            self.ui.stock_purchasing_input.setText(format_number(str(stock)))
            self.ui.stock_after_purchasing_input.setText(format_number(str(stock)))

            self.set_product_unit_details(sku)

    def set_purchasing_table_data(self, data: list[PurchasingTableItemModel]):
        for item in data:
            purchasing_index_key = f'{item.sku}_{item.unit}'
            if purchasing_index_key in self.cached_purchasing_index:
                idx = self.cached_purchasing_index[purchasing_index_key]
                price: str = remove_non_digit(self.purchasing_detail_table.item(idx, 4).text())
                updated_qty: int = int(remove_non_digit(self.purchasing_detail_table.item(idx, 2).text())) + int(item.qty)
                updated_amount: int = int(price) * int(updated_qty)

                self.purchasing_detail_table.item(idx, 2).setText(format_number(str(updated_qty)))
                self.purchasing_detail_table.item(idx, 7).setText(add_prefix(format_number(str(updated_amount))))

            else:
                current_row = self.purchasing_detail_table.rowCount()
                self.purchasing_detail_table.insertRow(current_row)

                table_items =  [ 
                    QtWidgets.QTableWidgetItem(item.sku),
                    QtWidgets.QTableWidgetItem(item.product_name),
                    QtWidgets.QTableWidgetItem(format_number(item.qty)),
                    QtWidgets.QTableWidgetItem(item.unit),
                    QtWidgets.QTableWidgetItem(add_prefix(format_number(item.price))),
                    QtWidgets.QTableWidgetItem(add_prefix(format_number(item.discount_rp))),
                    QtWidgets.QTableWidgetItem(add_prefix(format_number(item.discount_pct))),
                    QtWidgets.QTableWidgetItem(add_prefix(format_number(item.subtotal)))
                ]
                
                for col, item in enumerate(table_items):
                    item.setFont(POSFonts.get_font(size=16))
                    self.purchasing_detail_table.setItem(current_row, col, item)

                # Add purchasing index
                self.cached_purchasing_index[purchasing_index_key] = current_row


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

        product_unit_details = self.purchasing_service.get_product_unit_details(sku)
        if product_unit_details.success and product_unit_details.data:
            for pud in product_unit_details.data:
                # key = <sku>_<unit>, value = unit_value
                cache_key = f'{sku}_{pud.unit}'
                self.cached_qty[cache_key] = pud.unit_value
                self.ui.qty_purchasing_combobox.addItem(pud.unit)

    def on_handle_sku_enter(self):
        sku = self.ui.sku_purchasing_input.text().strip().upper()
        if not sku:
            self.clear_data_purchasing()
            return

        # Try to find exact SKU match
        result = self.purchasing_service.get_product_by_sku(sku)
        
        if result.success and result.data:
            # Product found - fill the form
            self.handle_product_selected({'sku' : sku})
            
        else:
            # Product not found - show dialog with filter
            self.products_dialog.set_filter(sku)
            self.products_dialog.show()