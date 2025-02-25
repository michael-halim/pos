from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QDateEdit
from datetime import datetime

from helper import format_number, add_prefix, remove_non_digit

from transactions.pending_transactions import PendingTransactionsWindow

from transactions.services.transaction_service import TransactionService

from transactions.models.transactions_models import TransactionTableItemModel, PendingTransactionModel, TransactionModel, DetailTransactionModel
from transactions.models.wholesale_models import WholesaleTableModel

from dialogs.products_dialog.products_dialog import ProductsDialogWindow
from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS
from generals.build import resource_path

class TransactionsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/transactions.ui'), self)

        # Init Services
        self.transaction_service = TransactionService()

        # Init Dialog
        self.products_in_transaction_dialog = ProductsDialogWindow()
        self.pending_transactions_dialog = PendingTransactionsWindow()


        # Connect the product_selected signal to handle_product_selected method
        self.products_in_transaction_dialog.product_selected.connect(self.handle_product_selected)
        self.pending_transactions_dialog.pending_transaction_selected.connect(self.handle_pending_transaction_selected)

        # Connect Filter Transactions
        self.ui.filter_transaction_input.textChanged.connect(self.filter_transactions)

        # Init Tables
        self.transactions_table = self.ui.transactions_table
        self.history_transactions_table = self.ui.history_transactions_table
        self.wholesale_transactions_table = self.ui.wholesale_transactions_table

        self.transactions_table.setSortingEnabled(True)
        self.history_transactions_table.setSortingEnabled(True)
        self.wholesale_transactions_table.setSortingEnabled(True)

        # Connect the add button to add_transaction method
        self.ui.clear_data_transaction_button.clicked.connect(self.clear_data_transaction)
        self.ui.clear_transaction_button.clicked.connect(self.clear_transaction)
        self.ui.add_transaction_button.clicked.connect(self.add_transaction)
        self.ui.find_sku_transaction_button.clicked.connect(lambda: self.products_in_transaction_dialog.show())
        self.ui.edit_transaction_button.clicked.connect(self.edit_transaction)
        self.ui.delete_transaction_button.clicked.connect(self.delete_transaction)
        self.ui.submit_transaction_button.clicked.connect(self.submit_transaction)
        self.ui.pending_transaction_button.clicked.connect(self.create_pending_transaction)
        self.ui.open_pending_transaction_button.clicked.connect(lambda: self.pending_transactions_dialog.showMaximized())
        
        # Set date input
        self.ui.date_transaction_input.setDate(datetime.now())
        self.ui.date_transaction_input.setDisplayFormat("dd/MM/yyyy")

        # Add 2 items to payment method combobox
        self.ui.payment_method_transaction_combobox.addItems(['Cash', 'Transfer'])

        # Add selected tracking
        self.current_selected_sku = None
        self.cached_qty = {} # key = <sku>_<unit>, value = (unit_value, price)
        self.cached_transaction_index = {} # key = <sku>_<unit>, value = transaction_table_index

        # Add a flag to track if we're loading items
        self.is_loading_combo = False

    
        # Event Listeners
        #====================
        # Connect discount radio button to update discount rp input
        self.ui.discount_pct_transaction_radio_button.toggled.connect(self.on_discount_transaction_radio_button_toggled)
        self.ui.discount_rp_per_item_transaction_radio_button.toggled.connect(self.on_discount_transaction_radio_button_toggled)
        self.ui.discount_rp_total_transaction_radio_button.toggled.connect(self.on_discount_transaction_radio_button_toggled)

        # Listen to discount pct input, price input, and qty input to update discount rp input
        self.ui.discount_pct_transaction_input_2.textChanged.connect(self.on_calculate_discount_rp)
        self.ui.discount_rp_per_item_transaction_input.textChanged.connect(self.on_calculate_discount_rp)
        self.ui.discount_rp_total_transaction_input.textChanged.connect(self.on_calculate_discount_rp)

        # Connect Tax Add, Remove
        self.ui.add_tax_transaction_button.clicked.connect(self.add_tax_transaction)
        self.ui.remove_tax_transaction_button.clicked.connect(self.remove_tax_transaction)

        # Connect table selection
        self.transactions_table.itemSelectionChanged.connect(self.on_transaction_selected)
        
        # Connect qty combobox to update qty input
        self.ui.qty_transaction_combobox.currentTextChanged.connect(self.on_qty_transaction_combobox_changed)

        # Connect qty input to update stock after input
        self.ui.qty_transaction_input.textChanged.connect(self.on_qty_transaction_input_changed)

        # Connect payment input to update payment change
        self.ui.payment_transaction_input.textChanged.connect(self.on_payment_transaction_input_changed)

        # Connect tax input to update tax rp input
        self.ui.tax_pct_transaction_input.textChanged.connect(self.on_tax_transaction_input_changed)

        # Connect return pressed signal
        self.ui.sku_transaction_input.returnPressed.connect(self.on_handle_sku_enter)

        # Set selection behavior to select entire rows
        self.transactions_table.setSelectionBehavior(SELECT_ROWS)
        self.transactions_table.setSelectionMode(SINGLE_SELECTION)
        self.wholesale_transactions_table.setSelectionBehavior(SELECT_ROWS)
        self.wholesale_transactions_table.setSelectionMode(SINGLE_SELECTION)
        self.history_transactions_table.setSelectionBehavior(SELECT_ROWS)
        self.history_transactions_table.setSelectionMode(SINGLE_SELECTION)

        # Set wholesale transactions table to be read only
        self.transactions_table.setEditTriggers(NO_EDIT_TRIGGERS)
        self.wholesale_transactions_table.setEditTriggers(NO_EDIT_TRIGGERS)
        self.history_transactions_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties to resize to contents
        self.transactions_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.transactions_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.wholesale_transactions_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.wholesale_transactions_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.history_transactions_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.history_transactions_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)


    def add_tax_transaction(self):
        self.ui.tax_pct_transaction_input.setEnabled(False)
        self.ui.tax_pct_transaction_input.setClearButtonEnabled(False)
        tax_rp = self.ui.tax_rp_transaction_input.text()

        table_item =  TransactionTableItemModel(
                sku = '=== TAX ===',
                product_name = '=== TAX ===',
                price = 0,
                qty = 0,
                unit = '=== TAX ===',
                unit_value = 0,
                discount_rp = 0,
                discount_rp_per_item = 0,
                discount_pct = 0,
                subtotal = tax_rp,
            )
        self.set_transactions_table_data([table_item])
        
        # Update total amount
        subtotal = self.calculate_total_transactions()
        self.ui.total_transaction_input.setText(add_prefix(format_number(str(subtotal))))

        # Update payment change
        self.ui.payment_change_transaction_input.setText(add_prefix(format_number(str(subtotal))))


    def remove_tax_transaction(self):
        if self.ui.tax_pct_transaction_input.isEnabled():
            return
        

        self.ui.tax_pct_transaction_input.setEnabled(True)
        self.ui.tax_pct_transaction_input.setClearButtonEnabled(True)

        # Remove from cached index
        transaction_index_key = f'=== TAX ===_=== TAX ==='
        if transaction_index_key in self.cached_transaction_index:
            del self.cached_transaction_index[transaction_index_key]
            
        self.transactions_table.removeRow(self.transactions_table.rowCount() - 1)
        
        subtotal = self.calculate_total_transactions()
        self.ui.total_transaction_input.setText(add_prefix(format_number(str(subtotal))))
        self.ui.payment_change_transaction_input.setText(add_prefix(format_number(str(subtotal))))


    def show_history_transactions_data(self):
        pass
    
    
    def show_wholesale_transactions_data(self, sku: str):
        self.clear_wholesale_transactions_data()
        
        # Get wholesale transactions from cached qty
        wholesale_transactions_data: list[WholesaleTableModel] = []
        for key in self.cached_qty:
            if key.split('_')[0] == sku:
                wholesale_transactions_data.append(WholesaleTableModel(
                    unit=key.split('_')[1],
                    unit_value=self.cached_qty[key][0],
                    price=self.cached_qty[key][1]
                ))

        self.set_wholesale_transactions_table_data(wholesale_transactions_data)
    

    def add_transaction(self):
        # Stop temporary sorting
        self.transactions_table.setSortingEnabled(False)

        try:
            transaction_form_data: TransactionTableItemModel = self.get_transactions_form_data()
            
            self.set_transactions_table_data([transaction_form_data])
                
            # Update total amount
            total_amount = self.calculate_total_transactions()
            self.ui.total_transaction_input.setText(add_prefix(format_number(str(total_amount))))

            # Update total discount
            total_discount = self.calculate_total_discount()
            self.ui.total_discount_transaction_input.setText(add_prefix(format_number(str(total_discount))))

            # Update payment change
            self.set_payment_change_transaction_input(total_amount, is_color_red=True)

            # Clear data transaction
            self.clear_data_transaction()

            # After adding new row, reapply filter if there's any
            self.filter_transactions()

        except Exception as e:
            POSMessageBox.error(self, title='Error', message=f"Failed to add transaction: {str(e)}")

        finally:
            # Re-enable sorting
            self.transactions_table.setSortingEnabled(True)
            self.clear_wholesale_transactions_data()


    def edit_transaction(self):
        # Get selected row
        selected_rows = self.transactions_table.selectedItems()
        if selected_rows:
            self.current_selected_sku = selected_rows[0].row()

            # Disconnect existing connections and connect to update function
            self.ui.add_transaction_button.setText('Update')
            self.ui.add_transaction_button.clicked.disconnect()
            self.ui.add_transaction_button.clicked.connect(self.update_transaction)

            # Get Selected Transaction Table Data
            transaction_table_data: TransactionTableItemModel = self.get_selected_transaction_table_data()
            
            self.set_transaction_form_data(transaction_table_data)

            # Make sure only qty is editable
            self.ui.qty_transaction_input.setReadOnly(False)
            self.ui.sku_transaction_input.setEnabled(False)
            self.ui.price_transaction_input.setEnabled(False)
            self.ui.product_name_transaction_input.setEnabled(False)
            self.ui.unit_value_transaction_input.setEnabled(False)
            self.ui.discount_rp_transaction_input.setEnabled(False)
            self.ui.discount_pct_transaction_input.setEnabled(False)


    def update_transaction(self):
        if self.current_selected_sku is not None:
            try:
                # Get the updated values
                transaction_form_data: TransactionTableItemModel = self.get_transactions_form_data()
                
                # Calculate new subtotal | subtotal = (price * qty) - discount_rp
                subtotal = int(int(transaction_form_data.price) * int(transaction_form_data.qty)) - int(transaction_form_data.discount_rp)
                
                # Update the row in the table
                self.transactions_table.item(self.current_selected_sku, 3).setText(format_number(transaction_form_data.qty))
                self.transactions_table.item(self.current_selected_sku, 6).setText(add_prefix(format_number(str(transaction_form_data.discount_pct))))
                self.transactions_table.item(self.current_selected_sku, 7).setText(add_prefix(format_number(str(transaction_form_data.discount_rp_per_item))))
                self.transactions_table.item(self.current_selected_sku, 8).setText(add_prefix(format_number(str(transaction_form_data.discount_rp))))
                self.transactions_table.item(self.current_selected_sku, 9).setText(add_prefix(format_number(str(subtotal))))
                
                # Update total amount
                total = self.calculate_total_transactions()
                self.ui.total_transaction_input.setText(add_prefix(format_number(str(total))))

                # Update total discount
                total_discount = self.calculate_total_discount()
                self.ui.total_discount_transaction_input.setText(add_prefix(format_number(str(total_discount))))

                # Update payment change
                self.set_payment_change_transaction_input(total, is_color_red=True)

                # Reset the form
                self.clear_data_transaction()
                
                # Reset button and connection
                self.ui.add_transaction_button.setText('Add')
                self.ui.add_transaction_button.clicked.disconnect()
                self.ui.add_transaction_button.clicked.connect(self.add_transaction)
                
                # Reset selection
                self.current_selected_sku = None
                
                # Re-enable all inputs
                self.ui.sku_transaction_input.setEnabled(True)
                self.ui.discount_rp_transaction_input.setEnabled(True)
                self.ui.discount_pct_transaction_input.setEnabled(True)

                # Clear wholesale transactions data
                self.clear_wholesale_transactions_data()
                
            except Exception as e:
                POSMessageBox.error(self, title='Error', message=f"Failed to update transaction: {str(e)}")


    def delete_transaction(self):
        selected_rows = self.transactions_table.selectedItems()
        if not selected_rows:
            POSMessageBox.warning(self, title='Warning', message="Please select a transaction to delete")
            return

        # Confirm deletion
        confirm = POSMessageBox.confirm(self, title="Confirm Deletion", 
                                        message="Are you sure you want to delete this transaction ?")

        if confirm:
            row = selected_rows[0].row()

            # Get the transaction details before deletion
            transaction_form_data: TransactionTableItemModel = self.get_selected_transaction_table_data()
            sku = transaction_form_data.sku
            unit = transaction_form_data.unit
            subtotal = transaction_form_data.subtotal
            discount_rp = transaction_form_data.discount_rp

            # Remove from cached index
            transaction_index_key = f'{sku}_{unit}'
            if transaction_index_key in self.cached_transaction_index:
                del self.cached_transaction_index[transaction_index_key]


            # Update total amount
            total_amount: int = self.calculate_total_transactions() - int(subtotal)
            self.ui.total_transaction_input.setText(add_prefix(format_number(str(total_amount))))

            # Update total discount
            total_discount = self.calculate_total_discount() - int(discount_rp)
            self.ui.total_discount_transaction_input.setText(add_prefix(format_number(str(total_discount))))

            # Remove the row from table
            self.transactions_table.removeRow(row)

            # Update payment change if payment exists
            payment_rp: str = remove_non_digit(self.ui.payment_transaction_input.text()) if self.ui.payment_transaction_input.text().strip() else '0'
            if payment_rp:
                payment_change: int = int(total_amount) - int(payment_rp)

                # Set color red if payment change is less than 0
                is_color_red = True if payment_change > 0 else False
                self.set_payment_change_transaction_input(payment_change, is_color_red=is_color_red)


    def submit_transaction(self):
        # Get payment amount
        payment_rp: str = remove_non_digit(self.ui.payment_transaction_input.text())
        if payment_rp == '':
            POSMessageBox.error(self, title='Error', message="Payment cannot be empty")
            return
        
        # Get detail transactions from transactions table
        detail_transactions_data: list[DetailTransactionModel] = self.get_detail_transactions()
        if len(detail_transactions_data) == 0:
            POSMessageBox.error(self, title='Error', message="No transactions to submit")
            return

        # Create transaction id
        transaction_id: str = self.transaction_service.create_transaction_id()
        for detail in detail_transactions_data:
            detail.transaction_id = transaction_id

        # Calculate total amount
        total_amount: int = self.calculate_total_transactions()

        # Calculate payment change
        payment_change: int = total_amount - int(payment_rp)
        if payment_change > 0:
            POSMessageBox.error(self, title='Error', message="Payment cannot be less than total amount")
            return

        
        # Create transaction data
        transaction_data: TransactionModel = TransactionModel(
            transaction_id = transaction_id,
            total_amount = total_amount,
            payment_amount = payment_rp,
            payment_change = payment_change,
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            payment_method = self.ui.payment_method_transaction_combobox.currentText(),
            payment_remarks = self.ui.remarks_transaction_input.toPlainText().strip(),
        )

        # Submit transaction
        result = self.transaction_service.submit_transaction(transaction_data, detail_transactions_data)
        if result.success:
            POSMessageBox.info(self, title='Success', message=result.message)
            
            # Clear the transactions table and total
            self.clear_transaction()

        else:
            POSMessageBox.error(self, title='Error', message=result.message)


    def create_pending_transaction(self):
        transaction_id: str = self.transaction_service.create_transaction_id(is_pending=True)

        # Get detail transactions from transactions table
        detail_transactions_data: list[DetailTransactionModel] = self.get_detail_transactions()
        for detail in detail_transactions_data:
            detail.transaction_id = transaction_id

        if len(detail_transactions_data) == 0:
            POSMessageBox.error(self, title='Error', message="No transactions to submit")
            return

        # Calculate total amount
        total_amount: int = self.calculate_total_transactions()

        # Create pending transaction data
        pending_transaction_data: PendingTransactionModel = PendingTransactionModel(
            transaction_id = transaction_id,
            total_amount = total_amount,
            discount_transaction_id = 1,
            discount_amount = 0,
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            payment_remarks = self.ui.remarks_transaction_input.toPlainText().strip()
        )

        result = self.transaction_service.create_pending_transaction(pending_transaction_data, detail_transactions_data)
        if result.success:
            POSMessageBox.info(self, "Success", result.message)
        else:
            POSMessageBox.error(self, "Error", result.message)

        # Clear the transactions table and total
        self.clear_transaction()

    
    def filter_transactions(self):
        search_text = self.ui.filter_transaction_input.text().lower()
        
        # Show all rows if search text is empty
        if not search_text:
            for row in range(self.transactions_table.rowCount()):
                self.transactions_table.setRowHidden(row, False)
            return
        
        # Iterate through all rows
        for row in range(self.transactions_table.rowCount()):
            match_found = False
            
            # Search through all columns in the row
            for col in range(self.transactions_table.columnCount()):
                item = self.transactions_table.item(row, col)
                if item and search_text in item.text().lower():
                    match_found = True
                    break
            
            # Hide/show row based on whether match was found
            self.transactions_table.setRowHidden(row, not match_found)


    # Signal Handlers
    #================
    def handle_pending_transaction_selected(self, pending_transaction_data):
        result = self.transaction_service.get_pending_transactions_by_transaction_id(pending_transaction_data['transaction_id'])
        if result['message'].success == False:
            POSMessageBox.error(self, "Error", result['message'].message)
            return


        # Put the data into transactions table
        self.set_transactions_table_data(result['data'])

        # Calculate total transactions
        subtotal = self.calculate_total_transactions()

        # Update total transactions
        self.ui.total_transaction_input.setText(add_prefix(format_number(str(subtotal))))
        
        # Update payment change
        self.set_payment_change_transaction_input(subtotal, is_color_red=True)


    def handle_product_selected(self, product_data):
        # Clear existing items
        self.ui.qty_transaction_combobox.clear()

        # Set loading flag
        self.is_loading_combo = True
        sku = product_data['sku']
        product_result = self.transaction_service.get_product_by_sku(sku)
        if product_result['success']:
            # Fill the form fields with selected product data
            self.ui.sku_transaction_input.setText(sku)
            self.ui.product_name_transaction_input.setText(product_result['data'].product_name)
            self.ui.price_transaction_input.setText(add_prefix(format_number(str(product_result['data'].price))))
            self.ui.qty_transaction_combobox.addItem(product_result['data'].unit)
            self.ui.unit_value_transaction_input.setText('1')

            cache_key = f'{sku}_{product_result["data"].unit}'
            self.cached_qty[cache_key] = (1, product_result['data'].price)

            # Set product unit details
            self.set_product_unit_details(sku)

            # Set stock 
            stock = product_result['data'].stock
            self.ui.stock_transaction_input.setText(format_number(str(stock)))
            self.ui.stock_after_transaction_input.setText(format_number(str(stock)))

            if stock < 0:   
                self.ui.stock_transaction_input.setText(f'-{format_number(str(stock))}')
                self.ui.stock_after_transaction_input.setText(f'-{format_number(str(stock))}')
                self.ui.stock_transaction_input.setStyleSheet('color: red;')
                self.ui.stock_after_transaction_input.setStyleSheet('color: red;')
        
        # Show wholesale transactions data
        self.show_wholesale_transactions_data(sku)

        # Trigger qty input changed event
        self.on_qty_transaction_input_changed()

        # Reset loading flag
        self.is_loading_combo = False


    # Calculate
    #==========
    def calculate_total_transactions(self) -> int:
        total_amount = 0
        for row in range(self.transactions_table.rowCount()):
            total_amount += int(remove_non_digit(self.transactions_table.item(row, 9).text()))
        return total_amount


    def calculate_total_discount(self) -> int:
        total_discount = 0
        for row in range(self.transactions_table.rowCount()):
            total_discount += int(remove_non_digit(self.transactions_table.item(row, 8).text()))
        return total_discount


    def calculate_stock_after_transactions(self, sku: str, unit: str):
        cache_key = f'{sku}_{unit}'
        if cache_key in self.cached_qty:
            # Get initial stock
            initial_stock = self.transaction_service.get_product_by_sku(sku)['data'].stock

            self.ui.stock_transaction_input.setStyleSheet('color: black;')
            self.ui.stock_transaction_input.setText(format_number(str(initial_stock)))

            if initial_stock < 0:
                self.ui.stock_transaction_input.setText(f'-{format_number(str(abs(initial_stock)))}')
                self.ui.stock_transaction_input.setStyleSheet('color: red;')
            

            # Get total qty in transaction table for this sku and unit
            total_qty_in_transactions = self.get_total_qty_in_transactions(sku)
            
            # Calculate and display stock after transactions
            stock_after = initial_stock - total_qty_in_transactions
            
            # Set color based on stock level
            self.ui.stock_after_transaction_input.setText(format_number(str(stock_after)))
            self.ui.stock_after_transaction_input.setStyleSheet('color: black;')

            if stock_after < 0:
                self.ui.stock_after_transaction_input.setText(f'-{format_number(str(abs(stock_after)))}')
                self.ui.stock_after_transaction_input.setStyleSheet('color: red;')


    # Clear Inputs
    #==========
    def clear_wholesale_transactions_data(self):
        self.wholesale_transactions_table.setRowCount(0)


    def clear_transaction(self):
        # Remove All Items from Transactions Table
        self.transactions_table.setRowCount(0)
        self.ui.total_transaction_input.setText(add_prefix('0'))
        self.ui.payment_change_transaction_input.setText(add_prefix('0'))
        self.cached_transaction_index = {}
        self.cached_qty = {}
        self.current_selected_sku = None
        self.clear_data_transaction()


    def clear_data_transaction(self):
        self.ui.sku_transaction_input.clear()
        self.ui.product_name_transaction_input.clear()
        self.ui.price_transaction_input.clear()
        self.ui.stock_transaction_input.clear()
        self.ui.stock_after_transaction_input.clear()
        self.ui.unit_value_transaction_input.clear()
        self.ui.qty_transaction_input.clear()
        self.ui.qty_transaction_combobox.clear()
        self.ui.discount_rp_transaction_input.clear()
        self.ui.discount_pct_transaction_input.clear()
        self.ui.payment_transaction_input.clear()
        self.ui.discount_pct_transaction_input_2.clear()
        self.ui.discount_rp_per_item_transaction_input.clear()
        self.ui.discount_rp_total_transaction_input.clear()
        self.clear_wholesale_transactions_data()
    

    # Getters
    #==========
    def get_detail_transactions(self) -> list[DetailTransactionModel]:
        '''
            Returns detail_transactions
            
            detail_transactions data is all the details from transactions table
        '''
        detail_transactions: list[DetailTransactionModel] = []
        for row in range(self.transactions_table.rowCount()):
            sku = self.transactions_table.item(row, 0).text()
            price = remove_non_digit(self.transactions_table.item(row, 2).text())
            qty = remove_non_digit(self.transactions_table.item(row, 3).text())
            unit = self.transactions_table.item(row, 4).text()
            unit_value = self.transactions_table.item(row, 5).text()
            discount_rp = remove_non_digit(self.transactions_table.item(row, 6).text())
            discount_pct = remove_non_digit(self.transactions_table.item(row, 7).text())
            subtotal = remove_non_digit(self.transactions_table.item(row, 8).text())

            detail_transactions.append(
                DetailTransactionModel(
                    transaction_id= '',
                    sku = sku,
                    price = price,
                    qty = qty,
                    unit = unit,
                    unit_value = unit_value,
                    discount = discount_rp,
                    subtotal = subtotal,
                )
            )
            
        return detail_transactions


    def get_transactions_form_data(self) -> TransactionTableItemModel:
        price: int = remove_non_digit(self.ui.price_transaction_input.text()) if self.ui.price_transaction_input.text().strip() else 0
        qty: int = remove_non_digit(self.ui.qty_transaction_input.text()) if self.ui.qty_transaction_input.text().strip() else 0
        disc_pct: int = remove_non_digit(self.ui.discount_pct_transaction_input_2.text()) if self.ui.discount_pct_transaction_input_2.text().strip() else 0
        disc_rp_per_item: int = remove_non_digit(self.ui.discount_rp_per_item_transaction_input.text()) if self.ui.discount_rp_per_item_transaction_input.text().strip() else 0
        disc_rp: int = remove_non_digit(self.ui.discount_rp_total_transaction_input.text()) if self.ui.discount_rp_total_transaction_input.text().strip() else 0
        
        # Calculate subtotal
        subtotal = int(int(price) * int(qty)) - int(disc_rp)

        return TransactionTableItemModel(
            sku = self.ui.sku_transaction_input.text().strip(),
            product_name = self.ui.product_name_transaction_input.text().strip(),
            unit = self.ui.qty_transaction_combobox.currentText().strip(),
            unit_value = remove_non_digit(self.ui.unit_value_transaction_input.text()),
            qty = qty,
            price = price,
            discount_rp = disc_rp,
            discount_pct = disc_pct,
            discount_rp_per_item = disc_rp_per_item,
            subtotal = subtotal,
        )
    

    def get_selected_transaction_table_data(self) -> TransactionTableItemModel:
        selected_rows = self.transactions_table.selectedItems()
        if not selected_rows:
            return None

        row = selected_rows[0].row()
        sku = self.transactions_table.item(row, 0).text()
        product_name = self.transactions_table.item(row, 1).text()
        price = remove_non_digit(self.transactions_table.item(row, 2).text())
        qty = remove_non_digit(self.transactions_table.item(row, 3).text())
        unit = self.transactions_table.item(row, 4).text()
        unit_value = remove_non_digit(self.transactions_table.item(row, 5).text())
        discount_pct = remove_non_digit(self.transactions_table.item(row, 6).text())
        discount_rp_per_item = remove_non_digit(self.transactions_table.item(row, 7).text())
        discount_rp = remove_non_digit(self.transactions_table.item(row, 8).text())
        subtotal = remove_non_digit(self.transactions_table.item(row, 9).text())

        return TransactionTableItemModel(sku=sku, product_name=product_name, unit=unit, 
                    unit_value=unit_value, qty=qty, price=price, discount_rp=discount_rp, 
                    discount_pct=discount_pct, discount_rp_per_item=discount_rp_per_item, subtotal=subtotal)


    def get_total_qty_in_transactions(self, sku: str) -> int:
        total_qty = 0
        for row in range(self.transactions_table.rowCount()):
            if self.transactions_table.item(row, 0).text() == sku:
                qty_in_transaction = remove_non_digit(self.transactions_table.item(row, 3).text())
                unit_value_in_transaction = remove_non_digit(self.transactions_table.item(row, 5).text())
                total_qty += int(qty_in_transaction) * int(unit_value_in_transaction)

        return total_qty
    

    # Setters
    #==========
    def set_transactions_table_data(self, data: list[TransactionTableItemModel]) -> None:
        '''
            Set data into transactions table
            Set the index of the transaction in the cached_transaction_index
            
        '''
        # SKU, Product_Name, Price, Qty, Unit, Unit_Value, Discount Pct, Discount Per Item, Discount_Rp, Subtotal
        #  0         1         2     3     4       5           6                  7             8           9

        for item in data:
            transaction_index_key = f'{item.sku}_{item.unit}'
            if transaction_index_key in self.cached_transaction_index:
                idx = self.cached_transaction_index[transaction_index_key]
                price: str = remove_non_digit(self.transactions_table.item(idx, 2).text())
                updated_qty: int = int(remove_non_digit(self.transactions_table.item(idx, 3).text())) + int(item.qty)
                updated_amount: int = int(price) * int(updated_qty)

                self.transactions_table.item(idx, 3).setText(format_number(str(updated_qty)))
                self.transactions_table.item(idx, 8).setText(add_prefix(format_number(str(updated_amount))))

            else:
                current_row = self.transactions_table.rowCount()
                self.transactions_table.insertRow(current_row)

                table_items =  [ 
                    QtWidgets.QTableWidgetItem(item.sku),
                    QtWidgets.QTableWidgetItem(item.product_name),
                    QtWidgets.QTableWidgetItem(add_prefix(format_number(item.price))),
                    QtWidgets.QTableWidgetItem(format_number(item.qty)),
                    QtWidgets.QTableWidgetItem(item.unit),
                    QtWidgets.QTableWidgetItem(format_number(item.unit_value)),
                    QtWidgets.QTableWidgetItem(format_number(item.discount_pct)),
                    QtWidgets.QTableWidgetItem(add_prefix(format_number(item.discount_rp_per_item))),
                    QtWidgets.QTableWidgetItem(add_prefix(format_number(item.discount_rp))),
                    QtWidgets.QTableWidgetItem(add_prefix(format_number(item.subtotal)))
                ]
                
                for col, item in enumerate(table_items):
                    item.setFont(POSFonts.get_font(size=16))
                    self.transactions_table.setItem(current_row, col, item)

                # Add transaction index
                self.cached_transaction_index[transaction_index_key] = current_row


    def set_product_unit_details(self, sku: str):
        '''
            Set the product unit into combobox

            sku and unit is the unique key, and the value is (unit_value, price)
            behind the scene the sku and unit is stored using dictionary called cached_qty
            Example: 
            
            ```cache_key = 'SKU001'
            cached_qty = {
                'SKU001_pcs' : (1, 10000),  #(pcs unit value is 1, price is 10.000)
                'SKU001_kodi' : (20, 100000), #(kodi unit value is 20, price is 100.000)
            }
            ```
        '''

        product_unit_details = self.transaction_service.get_product_unit_details(sku)
        for pud in product_unit_details:
            # key = <sku>_<unit>, value = (unit_value, price)
            cache_key = f'{sku}_{pud.unit}'
            self.cached_qty[cache_key] = (pud.unit_value, pud.price)
            self.ui.qty_transaction_combobox.addItem(pud.unit)


    def set_payment_change_transaction_input(self, total_amount: int, is_color_red: bool = True):
        self.ui.payment_change_transaction_input.setText(add_prefix(format_number(str(total_amount))))
        self.ui.payment_change_transaction_input.setStyleSheet('color: black;')
        if is_color_red:
            self.ui.payment_change_transaction_input.setStyleSheet('color: red;')
            

    def set_wholesale_transactions_table_data(self, data: list[WholesaleTableModel]) -> None:
        for item in data:
            if item.unit_value == 1:
                continue

            current_row = self.wholesale_transactions_table.rowCount()
            self.wholesale_transactions_table.insertRow(current_row)

            # Set table items
            table_items = [
                QtWidgets.QTableWidgetItem(item.unit),
                QtWidgets.QTableWidgetItem(format_number(item.unit_value)),
                QtWidgets.QTableWidgetItem(add_prefix(format_number(item.price)))
            ]

            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.wholesale_transactions_table.setItem(current_row, col, item)


    def set_transaction_form_data(self, data: TransactionTableItemModel):
        self.ui.sku_transaction_input.setText(data.sku)
        self.ui.product_name_transaction_input.setText(data.product_name)
        self.ui.price_transaction_input.setText(add_prefix(format_number(str(data.price))))
        self.ui.qty_transaction_input.setText(format_number(str(data.qty)))
        self.ui.qty_transaction_combobox.setCurrentText(data.unit)
        self.ui.unit_value_transaction_input.setText(format_number(str(data.unit_value)))
        self.ui.discount_pct_transaction_input_2.setText(str(data.discount_pct))
        self.ui.discount_rp_per_item_transaction_input.setText(str(data.discount_rp_per_item))
        self.ui.discount_rp_total_transaction_input.setText(str(data.discount_rp))



    # Event Listeners
    #====================
    def on_qty_transaction_input_changed(self):
        sku = self.ui.sku_transaction_input.text().strip()
        unit = self.ui.qty_transaction_combobox.currentText()
        unit_value = remove_non_digit(self.ui.unit_value_transaction_input.text())
        qty = remove_non_digit(self.ui.qty_transaction_input.text()) if self.ui.qty_transaction_input.text() else '0'
        stock = self.ui.stock_transaction_input.text().replace('.', '').strip()

        if qty == '' or stock == '':
            self.ui.stock_after_transaction_input.setStyleSheet('color: black;')
            self.calculate_stock_after_transactions(sku, unit)
            return
        
        total_qty_in_transactions = self.get_total_qty_in_transactions(sku)

        qty_after_transaction = int(stock) - (int(qty) * int(unit_value)) - total_qty_in_transactions
        self.ui.stock_after_transaction_input.setText(format_number(str(qty_after_transaction)))

        self.ui.stock_after_transaction_input.setStyleSheet('color: black;')
        if qty_after_transaction < 0:
            # add negative sign to stock after transaction
            self.ui.stock_after_transaction_input.setText(f'-{format_number(str(qty_after_transaction))}')
            self.ui.stock_after_transaction_input.setStyleSheet('color: red;')


    def on_qty_transaction_combobox_changed(self, text):
        # Skip if we're loading items
        if self.is_loading_combo:
            return
            
        sku = self.ui.sku_transaction_input.text().strip()
        cache_key = f'{sku}_{text}'
        if cache_key in self.cached_qty:

            self.ui.unit_value_transaction_input.setText(format_number(str(self.cached_qty[cache_key][0])))
            self.ui.price_transaction_input.setText(add_prefix(format_number(str(self.cached_qty[cache_key][1]))))
            
            # Calculate stock after existing transactions for new unit
            self.calculate_stock_after_transactions(sku, text)

        # Update qty on input changed
        self.on_qty_transaction_input_changed()


    def on_payment_transaction_input_changed(self):
        payment_rp = remove_non_digit(self.ui.payment_transaction_input.text())
        total_amount = remove_non_digit(self.ui.total_transaction_input.text())
        if payment_rp == '':
            self.set_payment_change_transaction_input(total_amount, is_color_red=True)
            return
        
        payment_change = int(total_amount) - int(payment_rp)

        # Set color red if payment change is less than 0
        is_color_red = True if payment_change > 0 else False
        self.set_payment_change_transaction_input(payment_change, is_color_red=is_color_red)


    def on_transaction_selected(self):
        if self.transactions_table.selectedItems():
            self.current_selected_sku = self.transactions_table.selectedItems()[0].row()


    def on_handle_sku_enter(self):
        sku = self.ui.sku_transaction_input.text().strip().upper()
        if not sku:
            self.clear_transaction()
            return

        # Try to find exact SKU match
        result = self.transaction_service.get_product_by_sku(sku)
        
        if result['success']:
            # Product found - fill the form
            self.handle_product_selected({'sku' : sku})
            self.show_wholesale_transactions_data(sku)
            
        else:
            # Product not found - show dialog with filter
            self.products_in_transaction_dialog.set_filter(sku)
            self.products_in_transaction_dialog.show()


    def on_discount_transaction_radio_button_toggled(self):
        if self.ui.discount_pct_transaction_radio_button.isChecked():
            self.ui.discount_pct_transaction_input_2.clear()
            self.ui.discount_pct_transaction_input_2.setEnabled(True)
            self.ui.discount_pct_transaction_input_2.setClearButtonEnabled(True)

            self.ui.discount_rp_per_item_transaction_input.setEnabled(False)
            self.ui.discount_rp_per_item_transaction_input.setText('0')
            self.ui.discount_rp_per_item_transaction_input.setClearButtonEnabled(False)
            
            self.ui.discount_rp_total_transaction_input.setEnabled(False)
            self.ui.discount_rp_total_transaction_input.setText('0')
            self.ui.discount_rp_total_transaction_input.setClearButtonEnabled(False)

        elif self.ui.discount_rp_per_item_transaction_radio_button.isChecked():
            self.ui.discount_rp_per_item_transaction_input.clear()
            self.ui.discount_rp_per_item_transaction_input.setEnabled(True)
            self.ui.discount_rp_per_item_transaction_input.setClearButtonEnabled(True)
            
            self.ui.discount_pct_transaction_input_2.setEnabled(False)
            self.ui.discount_pct_transaction_input_2.setText('0')
            self.ui.discount_pct_transaction_input_2.setClearButtonEnabled(False)

            self.ui.discount_rp_total_transaction_input.setEnabled(False)
            self.ui.discount_rp_total_transaction_input.setText(add_prefix('0'))
            self.ui.discount_rp_total_transaction_input.setClearButtonEnabled(False)

        elif self.ui.discount_rp_total_transaction_radio_button.isChecked():
            self.ui.discount_rp_total_transaction_input.clear()
            self.ui.discount_rp_total_transaction_input.setEnabled(True)
            self.ui.discount_rp_total_transaction_input.setClearButtonEnabled(True)

            self.ui.discount_rp_per_item_transaction_input.setEnabled(False)
            self.ui.discount_rp_per_item_transaction_input.setText('0')
            self.ui.discount_rp_per_item_transaction_input.setClearButtonEnabled(False)

            self.ui.discount_pct_transaction_input_2.setEnabled(False)
            self.ui.discount_pct_transaction_input_2.setText('0')
            self.ui.discount_pct_transaction_input_2.setClearButtonEnabled(False)


    def on_calculate_discount_rp(self):
        if self.ui.discount_rp_total_transaction_radio_button.isChecked():
            return
        
        # Get Form Data
        transaction_form_data: TransactionTableItemModel = self.get_transactions_form_data()
        price = transaction_form_data.price
        qty = transaction_form_data.qty

        discounted_rp = 0
        if self.ui.discount_rp_per_item_transaction_radio_button.isChecked():
            discount_rp_per_item = transaction_form_data.discount_rp_per_item
            discounted_rp = int(qty) * int(discount_rp_per_item)

        elif self.ui.discount_pct_transaction_radio_button.isChecked():
            discount_pct = transaction_form_data.discount_pct
            discounted_rp = int((int(price) * int(qty) * int(discount_pct)) / 100)

        # Calculate Discount Rp
        self.ui.discount_rp_total_transaction_input.setText(add_prefix(format_number(str(discounted_rp))))


    def on_tax_transaction_input_changed(self):
        tax_pct = remove_non_digit(self.ui.tax_pct_transaction_input.text()) if self.ui.tax_pct_transaction_input.text() else 0
        total_amount = self.calculate_total_transactions()

        # Calculate tax rp  
        tax_rp = int(int(total_amount) * int(tax_pct) / 100)
        self.ui.tax_rp_transaction_input.setText(add_prefix(format_number(str(tax_rp))))
