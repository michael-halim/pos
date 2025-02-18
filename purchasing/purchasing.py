from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QDateEdit
from datetime import datetime

from helper import format_number, add_prefix, remove_non_digit

from dialogs.products_dialog import ProductsDialogWindow

from purchasing.services.purchasing_services import PurchasingService
from purchasing.models.purchasing_models import PurchasingTableItemModel, DetailPurchasingModel, PurchasingModel, PurchasingHistoryTableItemModel

from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS, DATE_FORMAT_DDMMYYYY, DATE_EDIT_NO_BUTTONS

from dialogs.suppliers_dialog.suppliers_dialog import SuppliersDialogWindow
from dialogs.master_stock_dialog.master_stock_dialog import MasterStockDialogWindow
from dialogs.price_unit_dialog.price_unit_dialog import PriceUnitDialogWindow

class PurchasingWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.purchasing_service = PurchasingService()

        # Load the UI file
        self.ui = uic.loadUi('./ui/purchasing.ui', self)

        # Init Dialog
        self.products_dialog = ProductsDialogWindow()
        self.suppliers_dialog = SuppliersDialogWindow()
        self.master_stock_dialog = MasterStockDialogWindow()
        self.price_unit_dialog = PriceUnitDialogWindow()

        # Init Tables
        self.purchasing_detail_table = self.ui.purchasing_detail_table

        self.purchasing_detail_table.setSortingEnabled(True)

        # Connect the add button to add_transaction method
        self.ui.close_purchasing_button.clicked.connect(lambda: self.close())
        self.ui.clear_data_purchasing_button.clicked.connect(self.clear_data_purchasing)
        self.ui.master_stock_purchasing_button.clicked.connect(self.master_stock_purchasing)
        self.ui.add_purchasing_button.clicked.connect(self.add_purchasing)
        self.ui.edit_purchasing_button.clicked.connect(self.edit_purchasing)
        self.ui.delete_purchasing_button.clicked.connect(self.delete_purchasing)
        self.ui.submit_puchasing_button.clicked.connect(self.submit_purchasing)
        
        self.ui.find_sku_purchasing_button.clicked.connect(lambda: self.products_dialog.show())
        self.ui.master_stock_purchasing_button.clicked.connect(self.show_master_stock_dialog)
        self.ui.price_unit_purchasing_button.clicked.connect(self.show_price_unit_dialog)
        self.ui.find_supplier_in_purchasing_button.clicked.connect(lambda: self.suppliers_dialog.show())

        # Add selected tracking
        self.current_selected_sku = None
        self.cached_qty = {} # key = <sku>_<unit>, value = (unit_value, price)
        self.cached_purchasing_index = {} # key = <sku>_<unit>, value = purchasing_table_index

        # Handle product selected
        self.products_dialog.product_selected.connect(self.handle_product_selected)

        # Handle supplier selected
        self.suppliers_dialog.supplier_selected.connect(self.handle_supplier_selected)

        # Listeners
        # ===========

        # Supplier in purchasing input
        self.ui.supplier_in_purchasing_input.returnPressed.connect(self.on_handle_supplier_enter)

        # Connect qty combobox to update qty input
        self.ui.qty_purchasing_combobox.currentTextChanged.connect(self.on_qty_purchasing_combobox_changed)

        # Connect qty input to update stock after input
        self.ui.qty_purchasing_input.textChanged.connect(self.on_qty_purchasing_input_changed)

        # Connect return pressed signal
        self.ui.sku_purchasing_input.returnPressed.connect(self.on_handle_sku_enter)

        # Set date input
        self.ui.purchasing_date_input.setDate(datetime.now())
        self.ui.invoice_date_purchasing_input.setDate(datetime.now())
        self.ui.invoice_expired_date_purchasing_input.setDate(datetime.now())

        self.ui.purchasing_date_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)
        self.ui.invoice_date_purchasing_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)
        self.ui.invoice_expired_date_purchasing_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)

        self.ui.purchasing_date_input.setButtonSymbols(DATE_EDIT_NO_BUTTONS)
        self.ui.invoice_date_purchasing_input.setButtonSymbols(DATE_EDIT_NO_BUTTONS)
        self.ui.invoice_expired_date_purchasing_input.setButtonSymbols(DATE_EDIT_NO_BUTTONS)

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


    def show_master_stock_dialog(self):
        sku = self.ui.sku_purchasing_input.text().strip()
        if not sku:
            return
        
        self.master_stock_dialog.set_master_stock_form_by_sku(sku)
        self.master_stock_dialog.show()


    def show_purchasing_history(self):
        sku = self.ui.sku_purchasing_input.text().strip()
        if not sku:
            return
        
        purchasing_history_result = self.purchasing_service.get_purchasing_history_by_sku(sku)
        if purchasing_history_result.success and purchasing_history_result.data:
            self.set_purchasing_history_table_data(purchasing_history_result.data)


    def show_price_unit_dialog(self):
        sku = self.ui.sku_purchasing_input.text().strip()
        if not sku:
            return
        
        self.price_unit_dialog.set_price_unit_form_by_sku(sku)
        self.price_unit_dialog.show()


    def clear_purchasing(self):
        # Remove All Items from Purchasing Table
        self.purchasing_detail_table.setRowCount(0)
        self.ui.total_purchasing_input.setText(add_prefix('0'))
        self.cached_purchasing_index = {}
        self.cached_qty = {}
        self.current_selected_sku = None
        self.clear_data_purchasing()


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
            unit_value: str = self.cached_qty[f'{sku}_{unit}']
            discount_rp: int = int(remove_non_digit(self.ui.discount_rp_purchasing_input.text())) if self.ui.discount_rp_purchasing_input.text() else 0
            discount_pct: str = remove_non_digit(self.ui.discount_pct_purchasing_input.text()) if self.ui.discount_pct_purchasing_input.text() else '0'
            amount: str = str(int(price) * int(qty)) - int(discount_rp)

            items = [
                PurchasingTableItemModel(
                    sku=sku, product_name=name, price=price,
                    qty=qty, unit=unit, unit_value=unit_value, discount_rp=discount_rp, 
                    discount_pct=discount_pct, subtotal=amount
                )
            ]

            # Set purchasing table data
            self.set_purchasing_table_data(items)

            # Calculate total purchasing
            total_amount = self.calculate_total_purchasing()
            self.ui.total_purchasing_input.setText(add_prefix(format_number(str(total_amount))))

            # Calculate total discount
            total_discount = self.calculate_total_discount()
            self.ui.discount_total_purchasing_input.setText(add_prefix(format_number(str(total_discount))))

            # Clear data
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
            self.ui.price_purchasing_input.setEnabled(True)
            self.ui.discount_rp_purchasing_input.setEnabled(True)
            self.ui.discount_pct_purchasing_input.setEnabled(True)
            self.ui.sku_purchasing_input.setEnabled(False)
            self.ui.product_name_purchasing_input.setEnabled(False)
    

    def update_purchasing(self):
        if self.current_selected_sku is not None:
            try:
                # Get the updated values
                qty = self.ui.qty_purchasing_input.text().strip()
                price = remove_non_digit(self.ui.price_purchasing_input.text())
                discount_rp = remove_non_digit(self.ui.discount_rp_purchasing_input.text())
                discount_pct = remove_non_digit(self.ui.discount_pct_purchasing_input.text())

                # Calculate new subtotal
                subtotal = (int(price) * int(qty)) - int(discount_rp)
                
                # Update the row in the table
                self.purchasing_detail_table.item(self.current_selected_sku, 2).setText(format_number(qty))
                self.purchasing_detail_table.item(self.current_selected_sku, 6).setText(add_prefix(format_number(str(discount_rp))))
                self.purchasing_detail_table.item(self.current_selected_sku, 7).setText(add_prefix(format_number(str(discount_pct))))

                
                # Update total amount
                total_amount = self.calculate_total_purchasing()
                self.ui.total_purchasing_input.setText(add_prefix(format_number(str(total_amount))))

                # Calculate total discount
                total_discount = self.calculate_total_discount()
                self.ui.discount_total_purchasing_input.setText(add_prefix(format_number(str(total_discount))))

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
            total_amount: int = self.calculate_total_purchasing()
            self.ui.total_purchasing_input.setText(add_prefix(format_number(str(total_amount))))

            # Update total discount
            total_discount = self.calculate_total_discount()
            self.ui.discount_total_purchasing_input.setText(add_prefix(format_number(str(total_discount))))


    def submit_purchasing(self):
        # Get detail purchasing from purchasing table
        detail_purchasing_data: list[DetailPurchasingModel] = self.get_detail_purchasing()
        if len(detail_purchasing_data) == 0:
            POSMessageBox.error(self, title='Error', message="No purchasing to submit")
            return

        # Create purchasing id
        purchasing_id: str = self.purchasing_service.create_purchasing_id()
        for detail in detail_purchasing_data:
            detail.purchasing_id = purchasing_id

        # Calculate total amount
        total_amount: int = self.calculate_total_purchasing()
        total_discount: int = self.calculate_total_discount()
        
        # Get Purchasing Data
        invoice_number: str = self.ui.invoice_number_purchasing_input.text().strip()
        purhcasing_remarks: str = self.ui.remarks_purchasing_input.toPlainText().strip()
        supplier_id: str = self.ui.supplier_in_purchasing_input.text().strip()


        # Create purchasing data
        purchasing_data: PurchasingModel = PurchasingModel(
            purchasing_id = purchasing_id,
            supplier_id = supplier_id,
            invoice_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            invoice_number = invoice_number,
            invoice_expired_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            purchasing_remarks = purhcasing_remarks,
            total_amount = total_amount,
        )

        # Submit purchasing
        result = self.purchasing_service.submit_purchasing(purchasing_data, detail_purchasing_data)
        if result.success:
            POSMessageBox.info(self, title='Success', message=result.message)
            
            # Clear the purchasing table and total
            self.clear_purchasing()

            # Clear purchasing history table
            self.purchasing_history_table.setRowCount(0)

        else:
            POSMessageBox.error(self, title='Error', message=result.message)
    

    def calculate_total_purchasing(self) -> int:
        total_amount = 0
        for row in range(self.purchasing_detail_table.rowCount()):
            subtotal = remove_non_digit(self.purchasing_detail_table.item(row, 8).text())
            discount_rp = remove_non_digit(self.purchasing_detail_table.item(row, 6).text())
            total_amount += int(subtotal) - int(discount_rp)
        return total_amount
    

    def calculate_total_discount(self) -> int:
        total_discount = 0
        for row in range(self.purchasing_detail_table.rowCount()):
            discount_rp = remove_non_digit(self.purchasing_detail_table.item(row, 6).text())
            total_discount += int(discount_rp)
        return total_discount


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
            self.ui.unit_value_purchasing_input.setText('1')

            # Cache the unit value
            cache_key = f'{sku}_{product_result.data.unit}'
            self.cached_qty[cache_key] = 1

            # Set product unit details
            self.set_product_unit_details(sku)

            # Set stock
            stock = product_result.data.stock
            self.ui.stock_purchasing_input.setText(format_number(str(stock)))
            self.ui.stock_after_purchasing_input.setText(format_number(str(stock)))

            # Set color based on stock level
            if stock < 0:   
                self.ui.stock_purchasing_input.setText(f'-{format_number(str(stock))}')
                self.ui.stock_after_purchasing_input.setText(f'-{format_number(str(stock))}')
                self.ui.stock_purchasing_input.setStyleSheet('color: red;')
                self.ui.stock_after_purchasing_input.setStyleSheet('color: red;')

            # Show purchasing history
            self.show_purchasing_history()

            # Enable price unit button
            self.ui.price_unit_purchasing_button.setEnabled(True)

        # Reset loading flag
        self.is_loading_combo = False


    def handle_supplier_selected(self, supplier_data):
        supplier_id = supplier_data['supplier_id']
        supplier_result = self.purchasing_service.get_supplier_by_id(supplier_id)
        if supplier_result.success and supplier_result.data:
            self.ui.supplier_in_purchasing_input.setText(supplier_id)
            self.ui.supplier_name_in_purchasing_input.setText(supplier_result.data.supplier_name)


    def set_purchasing_history_table_data(self, data: list[PurchasingHistoryTableItemModel]):
        # Clear purchasing history table
        self.purchasing_history_table.setRowCount(0)

        for purchasing_history in data:
            current_row = self.purchasing_history_table.rowCount()
            self.purchasing_history_table.insertRow(current_row)

            table_items =  [ 
                QtWidgets.QTableWidgetItem(purchasing_history.created_at),
                QtWidgets.QTableWidgetItem(purchasing_history.supplier_name),
                QtWidgets.QTableWidgetItem(format_number(purchasing_history.qty)),
                QtWidgets.QTableWidgetItem(purchasing_history.unit),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(purchasing_history.price))),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(purchasing_history.subtotal)))
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=14))
                self.purchasing_history_table.setItem(current_row, col, item)


    def set_purchasing_table_data(self, data: list[PurchasingTableItemModel]):
        for item in data:
            purchasing_index_key = f'{item.sku}_{item.unit}'
            if purchasing_index_key in self.cached_purchasing_index:
                idx = self.cached_purchasing_index[purchasing_index_key]
                price: str = remove_non_digit(self.purchasing_detail_table.item(idx, 5).text())
                updated_qty: int = int(remove_non_digit(self.purchasing_detail_table.item(idx, 2).text())) + int(item.qty)
                updated_amount: int = int(price) * int(updated_qty)

                self.purchasing_detail_table.item(idx, 2).setText(format_number(str(updated_qty)))
                self.purchasing_detail_table.item(idx, 8).setText(add_prefix(format_number(str(updated_amount))))

            else:
                current_row = self.purchasing_detail_table.rowCount()
                self.purchasing_detail_table.insertRow(current_row)

                table_items =  [ 
                    QtWidgets.QTableWidgetItem(item.sku),
                    QtWidgets.QTableWidgetItem(item.product_name),
                    QtWidgets.QTableWidgetItem(format_number(item.qty)),
                    QtWidgets.QTableWidgetItem(item.unit),
                    QtWidgets.QTableWidgetItem(format_number(item.unit_value)),
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


    def calculate_stock_after_purchasing(self, sku: str, unit: str):
        cache_key = f'{sku}_{unit}'
        if cache_key in self.cached_qty:
            # Get initial stock
            product_result = self.purchasing_service.get_product_by_sku(sku)
            initial_stock = 0
            if product_result.success and product_result.data:
                initial_stock = product_result.data.stock

            self.ui.stock_purchasing_input.setText(format_number(str(initial_stock)))
            self.ui.stock_purchasing_input.setStyleSheet('color: black;')

            if initial_stock < 0:
                self.ui.stock_purchasing_input.setText(f'-{format_number(str(abs(initial_stock)))}')
                self.ui.stock_purchasing_input.setStyleSheet('color: red;')

            # Get total qty in purchasing table for this sku and unit
            total_qty_in_purchasing = self.get_total_qty_in_purchasing(sku)
            
            # Calculate and display stock after purchasing
            stock_after = initial_stock - total_qty_in_purchasing
            
            # Set color based on stock level
            self.ui.stock_after_purchasing_input.setText(format_number(str(stock_after)))
            self.ui.stock_after_purchasing_input.setStyleSheet('color: black;')

            if stock_after < 0:
                self.ui.stock_after_purchasing_input.setText(f'-{format_number(str(abs(stock_after)))}')
                self.ui.stock_after_purchasing_input.setStyleSheet('color: red;')


    def get_purchasing_history(self) -> list[PurchasingHistoryTableItemModel]:
        sku = self.ui.sku_purchasing_input.text().strip()
        if not sku:
            return []

        purchasing_history_result = self.purchasing_service.get_purchasing_history_by_sku(sku)
        if purchasing_history_result.success and purchasing_history_result.data:
            return purchasing_history_result.data

        return []


    def get_total_qty_in_purchasing(self, sku: str) -> int:
        total_qty = 0
        for row in range(self.purchasing_detail_table.rowCount()):
            if self.purchasing_detail_table.item(row, 0).text() == sku:
                qty_in_purchasing = remove_non_digit(self.purchasing_detail_table.item(row, 2).text())
                unit_value_in_purchasing = remove_non_digit(self.purchasing_detail_table.item(row, 4).text())
                total_qty += int(qty_in_purchasing) * int(unit_value_in_purchasing)

        return total_qty
    

    def get_detail_purchasing(self) -> list[DetailPurchasingModel]:
        '''
            Returns detail_purchasing
            
            detail_purchasing data is all the details from purchasing table
        '''
        detail_purchasing: list[DetailPurchasingModel] = []
        for row in range(self.purchasing_detail_table.rowCount()):
            sku = self.purchasing_detail_table.item(row, 0).text()
            qty = remove_non_digit(self.purchasing_detail_table.item(row, 2).text())
            unit = self.purchasing_detail_table.item(row, 3).text()
            unit_value = remove_non_digit(self.purchasing_detail_table.item(row, 4).text())
            price = remove_non_digit(self.purchasing_detail_table.item(row, 5).text())
            discount_rp = remove_non_digit(self.purchasing_detail_table.item(row, 6).text())
            discount_pct = remove_non_digit(self.purchasing_detail_table.item(row, 7).text())
            subtotal = remove_non_digit(self.purchasing_detail_table.item(row, 8).text())

            detail_purchasing.append(
                DetailPurchasingModel(
                    purchasing_id = '',
                    sku = sku,
                    price = price,
                    qty = qty,
                    unit = unit,
                    unit_value = unit_value,
                    discount_rp = discount_rp,
                    discount_pct = discount_pct,
                    subtotal = subtotal,
                )
            )
            
        return detail_purchasing


    def get_supplier_by_id(self, supplier_id: str):
        supplier_result = self.purchasing_service.get_supplier_by_id(supplier_id)
        if supplier_result.success and supplier_result.data:
            return supplier_result.data

        return None


    def on_qty_purchasing_input_changed(self):
        sku = self.ui.sku_purchasing_input.text().strip()
        unit = self.ui.qty_purchasing_combobox.currentText()
        unit_value = remove_non_digit(self.ui.unit_value_purchasing_input.text())
        qty = remove_non_digit(self.ui.qty_purchasing_input.text()) if self.ui.qty_purchasing_input.text() else '0'
        stock = self.ui.stock_purchasing_input.text().replace('.', '').strip()

        if qty == '' or stock == '':
            self.ui.stock_after_purchasing_input.setStyleSheet('color: black;')
            self.calculate_stock_after_purchasing(sku, unit)
            return
        
        total_qty_in_purchasing = self.get_total_qty_in_purchasing(sku)

        qty_after_transaction = int(stock) + (int(qty) * int(unit_value)) + total_qty_in_purchasing
        self.ui.stock_after_purchasing_input.setText(format_number(str(qty_after_transaction)))
    
        self.ui.stock_after_purchasing_input.setStyleSheet('color: black;')
        if qty_after_transaction < 0:
            # add negative sign to stock after purchasing
            self.ui.stock_after_purchasing_input.setText(f'-{format_number(str(qty_after_transaction))}')
            self.ui.stock_after_purchasing_input.setStyleSheet('color: red;')


    def on_qty_purchasing_combobox_changed(self, text):
        # Skip if we're loading items
        if self.is_loading_combo:
            return
            
        sku = self.ui.sku_purchasing_input.text().strip()
        cache_key = f'{sku}_{text}'
        if cache_key in self.cached_qty:
            unit_value: str = str(self.cached_qty[cache_key])
            self.ui.unit_value_purchasing_input.setText(format_number(unit_value))
            
            # Calculate stock after existing transactions for new unit
            self.calculate_stock_after_purchasing(sku, text)

        # Update qty on input changed
        self.on_qty_purchasing_input_changed()


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


    def on_handle_supplier_enter(self):
        supplier_text = self.ui.supplier_in_purchasing_input.text().strip()

         # Try to find exact SKU match
        result = self.purchasing_service.get_supplier_by_id(supplier_text)
        if result.success and result.data:
            # Supplier found - fill the form
            self.handle_supplier_selected({'supplier_id' : supplier_text})
            
        else:
            # Supplier not found - show dialog with filter
            self.suppliers_dialog.set_filter(supplier_text)
            self.suppliers_dialog.show()