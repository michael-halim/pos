from PyQt6 import QtWidgets, uic, QtCore
from datetime import datetime

from dialogs.pending_transactions_dialog.pending_transactions_dialog import PendingTransactionsDialogWindow
from dialogs.pending_transactions_dialog.models.pending_transactions_dialog_models import PendingTransactionModel
from dialogs.products_dialog.products_dialog import ProductsDialogWindow
from dialogs.customers_dialog.customers_dialog import CustomersDialogWindow
from dialogs.payment_transactions_dialog.payment_transactions_dialog import PaymentTransactionsDialogWindow

from transactions.services.transaction_service import TransactionService
from transactions.models.transactions_models import (
    TransactionTableItemModel, TransactionModel, DetailTransactionModel, PurchasingHistoryTableItemModel, 
    WholesaleTableModel, TransactionHistoryTableModel
)

from printers.printer_service import PrinterService
from helper import format_number, add_prefix, remove_non_digit
from generals.build import resource_path
from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS,
    TAX_TABLE_KEY, PERM_C_TRANSACTIONS, PERM_U_TRANSACTIONS,
    PERM_R_PENDING_TRANSACTIONS, DATE_FORMAT_DDMMYYYY
) 
from generals.messages import ( 
    ERR, OK, WARNING, ERR_PERM_C_TRANSACTIONS, ERR_PERM_U_TRANSACTIONS, 
    ERR_PERM_R_PENDING_TRANSACTIONS, PERM_DENIED
)
from transactions.translations import TRANSACTIONS_TRANSLATIONS
from generals.language_manager import LanguageManager
from generals.permission_manager import PermissionManager


class TransactionsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        
        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_C_TRANSACTIONS):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_C_TRANSACTIONS)
            self.close()
            return

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/transactions.ui'), self)

        # Init Services
        self.transaction_service = TransactionService()

        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(TRANSACTIONS_TRANSLATIONS)

        # Init Dialog
        self.products_dialog = ProductsDialogWindow()
        self.customers_dialog = CustomersDialogWindow()

        if self.permission_manager.has_permission(PERM_C_TRANSACTIONS):
            self.payment_transactions_dialog = PaymentTransactionsDialogWindow()

            # Handle payment transactions from dialog
            self.payment_transactions_dialog.transactions_submitted.connect(self.handle_submit_transactions)


        # Only show pending transactions dialog if user has permission
        if self.permission_manager.has_permission(PERM_R_PENDING_TRANSACTIONS):
            self.pending_transactions_dialog = PendingTransactionsDialogWindow()
            
            # Handle pending transactions from dialog
            self.pending_transactions_dialog.pending_transaction_selected.connect(self.handle_pending_transaction_selected)
        

        # Handle product selected from dialog
        self.products_dialog.product_selected.connect(self.handle_product_selected)

        # Handle customer selected from dialog
        self.customers_dialog.customer_selected.connect(self.handle_customer_selected)

        # Connect Filter Transactions
        self.ui.filter_transaction_input.textChanged.connect(self.filter_transactions)

        # Init Tables
        self.transactions_table = self.ui.transactions_table
        self.purchase_history_table = self.ui.purchase_history_table
        self.wholesale_transactions_table = self.ui.wholesale_transactions_table

        # Connect the add button to add_transaction method
        self.ui.clear_data_transaction_button.clicked.connect(self.clear_data_transaction)
        self.ui.clear_transaction_button.clicked.connect(self.clear_transaction)
        self.ui.add_transaction_button.clicked.connect(self.add_detail_transaction)
        self.ui.find_sku_transaction_button.clicked.connect(lambda: self.products_dialog.show())
        self.ui.edit_transaction_button.clicked.connect(self.edit_detail_transaction)
        self.ui.delete_transaction_button.clicked.connect(self.delete_detail_transaction)
        self.ui.submit_transaction_button.clicked.connect(self.trigger_submit_payment_transactions)
        self.ui.pending_transaction_button.clicked.connect(self.create_pending_transaction)
        self.ui.open_pending_transaction_button.clicked.connect(self.open_pending_transaction_dialog)
        self.ui.find_customer_transaction_button.clicked.connect(lambda: self.customers_dialog.show())

        # Set date input
        self.ui.date_transaction_input.setDate(datetime.now())
        self.ui.date_transaction_input.setDisplayFormat(DATE_FORMAT_DDMMYYYY)

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
        self.ui.discount_pct_transaction_input.textChanged.connect(self.on_calculate_discount_rp)
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

        # Connect tax input to update tax rp input
        self.ui.tax_pct_transaction_input.textChanged.connect(self.on_tax_transaction_input_changed)

        # Connect return pressed signal
        self.ui.sku_transaction_input.returnPressed.connect(self.on_handle_sku_enter)

        # Connect customer id input to update customer name input
        self.ui.customer_id_transaction_input.returnPressed.connect(self.on_handle_customer_enter)

        # UX For Shortcut
        # =================

        # Set focus to customer input
        self.ui.customer_id_transaction_input.setFocus()

        self.ui.qty_transaction_input.installEventFilter(self)

        # Connect combobox activated signal
        self.ui.qty_transaction_combobox.activated.connect(self.on_unit_selected)


        # Set selection behavior to select entire rows
        self.transactions_table.setSelectionBehavior(SELECT_ROWS)
        self.transactions_table.setSelectionMode(SINGLE_SELECTION)
        self.wholesale_transactions_table.setSelectionBehavior(SELECT_ROWS)
        self.wholesale_transactions_table.setSelectionMode(SINGLE_SELECTION)
        self.purchase_history_table.setSelectionBehavior(SELECT_ROWS)
        self.purchase_history_table.setSelectionMode(SINGLE_SELECTION)
        self.transaction_history_table.setSelectionBehavior(SELECT_ROWS)
        self.transaction_history_table.setSelectionMode(SINGLE_SELECTION)


        # Set wholesale transactions table to be read only
        self.transactions_table.setEditTriggers(NO_EDIT_TRIGGERS)
        self.wholesale_transactions_table.setEditTriggers(NO_EDIT_TRIGGERS)
        self.purchase_history_table.setEditTriggers(NO_EDIT_TRIGGERS)
        self.transaction_history_table.setEditTriggers(NO_EDIT_TRIGGERS)

        # Set table properties to resize to contents
        self.transactions_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.transactions_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.wholesale_transactions_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.wholesale_transactions_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.purchase_history_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.purchase_history_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.transaction_history_table.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        self.transaction_history_table.verticalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)


    # Overrides
    #====================
    def showMaximized(self):
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_C_TRANSACTIONS):
            self.close()
            return

        # Set window title
        if self.permission_manager.get_username().lower() not in self.windowTitle().lower():
            self.setWindowTitle(self.windowTitle() + ' - ' + self.permission_manager.get_username())

        # Translate widget text and update table headers
        self.language_manager.translate_widget_text(self)

        self.transaction_headers = ['SKU', 'Name', 'Price', 'Qty', 'Unit', 'Unit Value', 'Disc (%)', 'Disc Per Item (Rp)', 'Disc (Rp)', 'Subtotal']
        self.wholesale_transaction_headers = ['Unit', 'Unit Value', 'Price']
        self.transaction_history_headers = ['Date', 'Qty', 'Unit']
        self.purchase_history_headers = ['Date', 'Qty', 'Unit']
        if self.language_manager.get_current_language() == 'id':    
            self.transaction_headers = ['Kode Barang', 'Nama', 'Harga', 'Qty', 'Satuan', 'Nilai Satuan', 'Disk (%)', 'Disk Per Item (Rp)', 'Disk (Rp)', 'Subtotal']
            self.wholesale_transaction_headers = ['Satuan', 'Nilai Satuan', 'Harga']
            self.transaction_history_headers = ['Tanggal', 'Qty', 'Satuan']
            self.purchase_history_headers = ['Tanggal', 'Qty', 'Satuan']

        self.language_manager.translate_table_headers(self.ui.transactions_table, self.transaction_headers)
        self.language_manager.translate_table_headers(self.ui.wholesale_transactions_table, self.wholesale_transaction_headers)
        self.language_manager.translate_table_headers(self.ui.transaction_history_table, self.transaction_history_headers)
        self.language_manager.translate_table_headers(self.ui.purchase_history_table, self.purchase_history_headers)


    def add_tax_transaction(self):
        self.ui.tax_pct_transaction_input.setEnabled(False)
        self.ui.tax_pct_transaction_input.setClearButtonEnabled(False)
        tax_rp = self.ui.tax_rp_transaction_input.text()

        table_item =  TransactionTableItemModel(
                sku = TAX_TABLE_KEY,
                product_name = TAX_TABLE_KEY,
                price = 0,
                qty = 0,
                unit = TAX_TABLE_KEY,
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


    def remove_tax_transaction(self):
        if self.ui.tax_pct_transaction_input.isEnabled():
            return
        

        self.ui.tax_pct_transaction_input.setEnabled(True)
        self.ui.tax_pct_transaction_input.setClearButtonEnabled(True)

        # Remove from cached index
        transaction_index_key = f'{TAX_TABLE_KEY}_{TAX_TABLE_KEY}'
        if transaction_index_key in self.cached_transaction_index:
            del self.cached_transaction_index[transaction_index_key]
            
        self.transactions_table.removeRow(self.transactions_table.rowCount() - 1)
        
        subtotal = self.calculate_total_transactions()
        self.ui.total_transaction_input.setText(add_prefix(format_number(str(subtotal))))


    def add_detail_transaction(self):
        # Stop temporary sorting
        self.transactions_table.setSortingEnabled(False)
        transaction_form_data: TransactionTableItemModel = self.get_transactions_form_data()
        if transaction_form_data.sku == '' or transaction_form_data.price == '' or transaction_form_data.product_name == '' \
            or transaction_form_data.unit == '' or transaction_form_data.qty == '' or int(transaction_form_data.qty) <= 0:
            POSMessageBox.error(self, title=ERR, message="Please select a product and enter quantity minimum 1")
            return


        try:
            
            self.set_transactions_table_data([transaction_form_data])
                
            # Update total amount
            total_amount = self.calculate_total_transactions()
            self.ui.total_transaction_input.setText(add_prefix(format_number(str(total_amount))))

            # Update total discount
            total_discount = self.calculate_total_discount()
            self.ui.total_discount_transaction_input.setText(add_prefix(format_number(str(total_discount))))

            # Clear data transaction
            self.clear_data_transaction()

            # After adding new row, reapply filter if there's any
            self.filter_transactions()

            # Scroll to the bottom of the table
            self.transactions_table.scrollToBottom()

            # Scroll to the rightmost column in the last row
            model = self.transactions_table.model()
            row_count = model.rowCount()
            col_count = model.columnCount()
            if row_count > 0 and col_count > 0:
                index = model.index(row_count - 1, col_count - 1)
                self.transactions_table.scrollTo(index)


        except Exception as e:
            POSMessageBox.error(self, title=ERR, message=f"Failed to add transaction: {str(e)}")

        finally:
            # Re-enable sorting
            self.transactions_table.setSortingEnabled(True)
            self.clear_purchasing_history_data()
            self.clear_transaction_history_data()
            self.clear_wholesale_transactions_data()


    def edit_detail_transaction(self):
        # Get selected row
        selected_rows = self.transactions_table.selectedItems()
        if selected_rows:
            self.current_selected_sku = selected_rows[0].row()
            if self.transactions_table.item(self.current_selected_sku, 0).text() == TAX_TABLE_KEY:
                POSMessageBox.error(self, title=ERR, message="Tax can only be removed or added")
                return

            # Disconnect existing connections and connect to update function
            self.ui.add_transaction_button.setText('Update')
            self.ui.add_transaction_button.clicked.disconnect()
            self.ui.add_transaction_button.clicked.connect(self.update_detail_transaction)

            # Get Selected Transaction Table Data
            transaction_table_data: TransactionTableItemModel = self.get_selected_transaction_table_data()
            
            self.set_transaction_form_data(transaction_table_data)

            # Set focus to qty input
            self.ui.qty_transaction_input.setFocus()

            # Set Combobox to current unit and disable it
            unit = transaction_table_data.unit
            if self.ui.qty_transaction_combobox.findText(unit) == -1:
                self.ui.qty_transaction_combobox.addItem(unit)

            self.ui.qty_transaction_combobox.setCurrentText(unit)
            self.ui.qty_transaction_combobox.setEnabled(False)

            # Make sure only qty is editable
            self.ui.qty_transaction_input.setReadOnly(False)
            self.ui.sku_transaction_input.setEnabled(False)
            self.ui.price_transaction_input.setEnabled(False)
            self.ui.product_name_transaction_input.setEnabled(False)
            self.ui.unit_value_transaction_input.setEnabled(False)


    def update_detail_transaction(self):
        if self.current_selected_sku is not None:
            try:
                # Get the updated values
                transaction_form_data: TransactionTableItemModel = self.get_transactions_form_data()
                
                # Calculate new subtotal | subtotal = (price * qty) - discount_rp
                subtotal = int(int(transaction_form_data.price) * int(transaction_form_data.qty)) - int(transaction_form_data.discount_rp)
                
                # Update the row in the table
                self.transactions_table.item(self.current_selected_sku, 3).setText(format_number(transaction_form_data.qty))
                self.transactions_table.item(self.current_selected_sku, 6).setText(format_number(str(transaction_form_data.discount_pct)))
                self.transactions_table.item(self.current_selected_sku, 7).setText(add_prefix(format_number(str(transaction_form_data.discount_rp_per_item))))
                self.transactions_table.item(self.current_selected_sku, 8).setText(add_prefix(format_number(str(transaction_form_data.discount_rp))))
                self.transactions_table.item(self.current_selected_sku, 9).setText(add_prefix(format_number(str(subtotal))))
                
                # Update total amount
                total = self.calculate_total_transactions()
                self.ui.total_transaction_input.setText(add_prefix(format_number(str(total))))

                # Update total discount
                total_discount = self.calculate_total_discount()
                self.ui.total_discount_transaction_input.setText(add_prefix(format_number(str(total_discount))))

                # Re-calculate tax if any
                if not self.ui.tax_pct_transaction_input.isEnabled():
                    self.remove_tax_transaction()
                    self.on_tax_transaction_input_changed()
                    self.add_tax_transaction()


                # Reset the form
                self.clear_data_transaction()
                
                # Reset button and connection
                self.ui.add_transaction_button.setText('Add')
                self.ui.add_transaction_button.clicked.disconnect()
                self.ui.add_transaction_button.clicked.connect(self.add_detail_transaction)
                
                # Reset selection
                self.current_selected_sku = None
                
                # Re-enable all inputs
                self.ui.sku_transaction_input.setEnabled(True)
                self.ui.qty_transaction_combobox.setEnabled(True)

                # Clear wholesale, purchasing history and transaction history data
                self.clear_wholesale_transactions_data()
                self.clear_purchasing_history_data()
                self.clear_transaction_history_data()
                
            except Exception as e:
                POSMessageBox.error(self, title=ERR, message=f"Failed to update transaction: {str(e)}")


    def delete_detail_transaction(self):
        selected_rows = self.transactions_table.selectedItems()
        if not selected_rows:
            POSMessageBox.warning(self, title=WARNING, message="Please select a transaction to delete")
            return


        if self.transactions_table.item(selected_rows[0].row(), 0).text() == TAX_TABLE_KEY:
            POSMessageBox.error(self, title=ERR, message="Tax can only be removed or added")
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

            # Remove from cached index
            transaction_index_key = f'{sku}_{unit}'
            if transaction_index_key in self.cached_transaction_index:
                del self.cached_transaction_index[transaction_index_key]

            # Remove the row from table
            self.transactions_table.removeRow(row)

            # Update total amount
            total_amount: int = self.calculate_total_transactions()
            self.ui.total_transaction_input.setText(add_prefix(format_number(str(total_amount))))

            # Update total discount
            total_discount = self.calculate_total_discount()
            self.ui.total_discount_transaction_input.setText(add_prefix(format_number(str(total_discount))))

            # Re-calculate tax if any
            if not self.ui.tax_pct_transaction_input.isEnabled():
                self.remove_tax_transaction()
                self.on_tax_transaction_input_changed()
                self.add_tax_transaction()  

            
    def trigger_submit_payment_transactions(self):
        # Get detail transactions from transactions table
        detail_transactions_data: list[DetailTransactionModel] = self.get_detail_transactions()
        if len(detail_transactions_data) == 0:
            POSMessageBox.error(self, title=ERR, message="No transactions to submit")
            return
        
        total_amount: int = self.calculate_total_transactions()
        self.payment_transactions_dialog.set_payment(total_amount)
        self.payment_transactions_dialog.show()


    def open_pending_transaction_dialog(self):
        if not self.permission_manager.has_permission(PERM_R_PENDING_TRANSACTIONS):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_R_PENDING_TRANSACTIONS)
            return
        
        self.pending_transactions_dialog.showMaximized()


    def submit_transaction(self, payment_amount: int, payment_change: int):
        
        if not self.permission_manager.has_permission(PERM_C_TRANSACTIONS):
            POSMessageBox.error(self, title=ERR_PERM_C_TRANSACTIONS, message=ERR_PERM_C_TRANSACTIONS)
            return
        
        # Get detail transactions from transactions table
        detail_transactions_data: list[DetailTransactionModel] = self.get_detail_transactions()

        # Create transaction id
        transaction_id: str = self.transaction_service.create_transaction_id(is_pending=False)
        for detail in detail_transactions_data:
            detail.transaction_id = transaction_id

        # Calculate total amount
        total_amount: int = self.calculate_total_transactions()

        # Calculate total discount
        total_discount: int = self.calculate_total_discount()

        customer_id: str = self.ui.customer_id_transaction_input.text().strip() if self.ui.customer_id_transaction_input.text().strip() else None

        # Create transaction data
        transaction_data: TransactionModel = TransactionModel(
            customer_id = customer_id,
            transaction_id = transaction_id,
            total_amount = total_amount,
            total_discount = total_discount,
            payment_method = self.ui.payment_method_transaction_combobox.currentText(),
            payment_amount = payment_amount,
            payment_change = payment_change,
            payment_remarks = self.ui.remarks_transaction_input.toPlainText().strip(),
            tax_pct = self.ui.tax_pct_transaction_input.text(),
            tax_amount = self.ui.tax_rp_transaction_input.text(),
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        )

        # Submit transaction
        result = self.transaction_service.submit_transaction(transaction_data, detail_transactions_data)
        if result.success:
            POSMessageBox.info(self, title=OK, message=result.message)
            
            # Print Transactions to POS Machine
            detail_transactions_table: list[TransactionTableItemModel] = self.get_detail_transactions_table()
            self.print_transactions(transaction_data, detail_transactions_table)

            # Clear the transactions table and total
            self.clear_transaction()

            # Set focus to customer input
            self.ui.customer_id_transaction_input.setFocus()

        else:
            POSMessageBox.error(self, title=ERR, message=result.message)


    def handle_submit_transactions(self, data: dict):
        submit_text = self.ui.submit_transaction_button.text().strip().lower()
        transaction_id = self.ui.transaction_id_transaction_input.text().strip()

        if submit_text == 'update' and transaction_id != '':
            self.update_transaction(payment_amount=data['payment_amount'], payment_change=data['payment_change'])
        else:
            self.submit_transaction(payment_amount=data['payment_amount'], payment_change=data['payment_change'])


    def update_transaction(self, payment_amount: int, payment_change: int):
        if not self.permission_manager.has_permission(PERM_U_TRANSACTIONS):
            POSMessageBox.error(self, title=ERR_PERM_U_TRANSACTIONS, message=ERR_PERM_U_TRANSACTIONS)
            return
        
        # Get detail transactions from transactions table
        detail_transactions_data: list[DetailTransactionModel] = self.get_detail_transactions()
        if len(detail_transactions_data) == 0:
            POSMessageBox.error(self, title=ERR, message="No transactions to submit")
            return

        # Create transaction id
        transaction_id: str = self.ui.transaction_id_transaction_input.text().strip()

        # Calculate total amount
        total_amount: int = self.calculate_total_transactions()

        # Calculate total discount
        total_discount: int = self.calculate_total_discount()

        customer_id: str = self.ui.customer_id_transaction_input.text().strip() if self.ui.customer_id_transaction_input.text().strip() else None

        # Create transaction data
        transaction_data: TransactionModel = TransactionModel(
            customer_id = customer_id,
            transaction_id = transaction_id,
            total_amount = total_amount,
            total_discount = total_discount,
            payment_method = self.ui.payment_method_transaction_combobox.currentText(),
            payment_amount = payment_amount,
            payment_change = payment_change,
            payment_remarks = self.ui.remarks_transaction_input.toPlainText().strip(),
            tax_pct = self.ui.tax_pct_transaction_input.text(),
            tax_amount = self.ui.tax_rp_transaction_input.text(),
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        )

        added_detail_transactions, updated_detail_transactions, deleted_detail_transactions = self.get_added_updated_deleted_detail_transactions(transaction_id, detail_transactions_data)

        # Submit transaction
        result = self.transaction_service.update_transaction(transaction_data, 
                                                             added_detail_transactions, 
                                                             updated_detail_transactions, 
                                                             deleted_detail_transactions)
        if result.success:
            POSMessageBox.info(self, title=OK, message=result.message)
            
            # Clear the transactions table and total
            self.clear_transaction()

            self.ui.submit_transaction_button.setText('Submit')
            self.ui.submit_transaction_button.clicked.disconnect()
            self.ui.submit_transaction_button.clicked.connect(self.submit_transaction)

        else:
            POSMessageBox.error(self, title=ERR, message=result.message)
        


    def create_pending_transaction(self):
        transaction_id: str = self.transaction_service.create_transaction_id(is_pending=True)
        customer_id: str = self.ui.customer_id_transaction_input.text().strip() if self.ui.customer_id_transaction_input.text().strip() else None
        
        # Get detail transactions from transactions table
        detail_transactions_data: list[DetailTransactionModel] = self.get_detail_transactions()
        for detail in detail_transactions_data:
            detail.transaction_id = transaction_id

        if len(detail_transactions_data) == 0:
            POSMessageBox.error(self, title=ERR, message="No transactions to submit")
            return

        # Calculate total amount
        total_amount: int = self.calculate_total_transactions()

        # Calculate total discount
        total_discount: int = self.calculate_total_discount()

        # Create pending transaction data
        pending_transaction_data: PendingTransactionModel = PendingTransactionModel(
            transaction_id = transaction_id,
            customer_id = customer_id,
            total_amount = total_amount,
            discount_transaction_id = 1,
            discount_amount = total_discount,
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            payment_remarks = self.ui.remarks_transaction_input.toPlainText().strip()
        )

        result = self.transaction_service.create_pending_transaction(pending_transaction_data, detail_transactions_data)
        if result.success:
            POSMessageBox.info(self, title="Success", message=result.message)
            
            # Clear the transactions table and total
            self.clear_transaction()

        else:
            POSMessageBox.error(self, title="Error", message=result.message)

    
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


    # Shows
    #================
    def show_purchasing_history_data(self, sku: str):
        self.clear_purchasing_history_data()


        if sku == '':
            sku = self.ui.sku_transaction_input.text().strip()
        
        result = self.transaction_service.get_purchasing_history_by_sku(sku)

        if result.success and result.data:
            self.set_purchasing_history_table_data(result.data)
    
    
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
    

    def show_transaction_history_data(self, sku: str):
        self.clear_transaction_history_data()

        if sku == '':
            sku = self.ui.sku_transaction_input.text().strip()

        result = self.transaction_service.get_transaction_history_by_sku(sku)
        if result.success and result.data:
            self.set_transaction_history_table_data(result.data)


    # Signal Handlers
    #================
    def handle_pending_transaction_selected(self, pending_transaction_data):
        # Get pending transaction data
        result_pending_transaction = self.transaction_service.get_pending_transactions_by_id(pending_transaction_data['transaction_id'])
        if result_pending_transaction.success == False:
            POSMessageBox.error(self, title="Error", message=result_pending_transaction.message)
            return
        
        # Get pending transaction details
        result_pending_details = self.transaction_service.get_pending_transactions_details_by_id(pending_transaction_data['transaction_id'])
        if result_pending_details.success == False:
            POSMessageBox.error(self, title="Error", message=result_pending_details.message)
            return

        # Get customer data
        result_customer = self.transaction_service.get_customer_by_id(result_pending_transaction.data.customer_id)
        if result_customer.success == False:
            POSMessageBox.error(self, title="Error", message=result_customer.message)
            return


        # Set customer data
        self.ui.customer_id_transaction_input.setText(result_pending_transaction.data.customer_id)
        self.ui.customer_name_transaction_input.setText(result_customer.data)

        # Put the data into transactions table
        self.set_transactions_table_data(result_pending_details.data)

        # Calculate total transactions
        subtotal = self.calculate_total_transactions()
        self.ui.total_transaction_input.setText(add_prefix(format_number(str(subtotal))))

        # Calculate total discount
        total_discount = self.calculate_total_discount()
        self.ui.total_discount_transaction_input.setText(add_prefix(format_number(str(total_discount))))


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
        
        # Show wholesale, purchasing history and transaction history data
        self.show_wholesale_transactions_data(sku)
        self.show_purchasing_history_data(sku)
        self.show_transaction_history_data(sku)

        # Trigger qty input changed event
        self.on_qty_transaction_input_changed()

        # Set focus to qty input
        self.ui.qty_transaction_input.setFocus()

        # Reset loading flag
        self.is_loading_combo = False


    def handle_customer_selected(self, customer_data):
        self.ui.customer_id_transaction_input.setText(customer_data['customer_id'])
        result = self.transaction_service.get_customer_by_id(customer_data['customer_id'])
        if result.success:
            self.ui.customer_name_transaction_input.setText(result.data)

        # Set focus to sku input
        self.ui.sku_transaction_input.setFocus()
        

    # Getters
    #==========
    def get_detail_transactions(self) -> list[DetailTransactionModel]:
        '''
            Returns detail_transactions
            
            detail_transactions data is all the details from transactions table
        '''
        detail_transactions: list[DetailTransactionModel] = []
        for row in range(self.transactions_table.rowCount()):
            if self.transactions_table.item(row, 0).text() == TAX_TABLE_KEY:
                continue

            sku = self.transactions_table.item(row, 0).text()
            price = remove_non_digit(self.transactions_table.item(row, 2).text())
            qty = remove_non_digit(self.transactions_table.item(row, 3).text())
            unit = self.transactions_table.item(row, 4).text()
            unit_value = self.transactions_table.item(row, 5).text()
            discount_pct = remove_non_digit(self.transactions_table.item(row, 6).text())
            discount_rp_per_item = remove_non_digit(self.transactions_table.item(row, 7).text())
            discount_rp = remove_non_digit(self.transactions_table.item(row, 8).text())
            subtotal = remove_non_digit(self.transactions_table.item(row, 9).text())

            detail_transactions.append(
                DetailTransactionModel(
                    transaction_id= '',
                    sku = sku,
                    price = price,
                    qty = qty,
                    unit = unit,
                    unit_value = unit_value,
                    discount_rp = discount_rp,
                    discount_rp_per_item = discount_rp_per_item,
                    discount_pct = discount_pct,
                    subtotal = subtotal,
                )
            )
            
        return detail_transactions

    
    def get_detail_transactions_table(self) -> list[TransactionTableItemModel]:
        detail_transactions_table: list[TransactionTableItemModel] = []
        for row in range(self.transactions_table.rowCount()):
            if self.transactions_table.item(row, 0).text() == TAX_TABLE_KEY:
                continue

            detail_transactions_table.append(TransactionTableItemModel(
                sku = self.transactions_table.item(row, 0).text(),
                product_name = self.transactions_table.item(row, 1).text(),
                price = self.transactions_table.item(row, 2).text(),
                qty = self.transactions_table.item(row, 3).text(),
                unit = self.transactions_table.item(row, 4).text(),
                unit_value = self.transactions_table.item(row, 5).text(),
                discount_pct = self.transactions_table.item(row, 6).text(),
                discount_rp_per_item = self.transactions_table.item(row, 7).text(),
                discount_rp = self.transactions_table.item(row, 8).text(),
                subtotal = self.transactions_table.item(row, 9).text(),
            ))

        return detail_transactions_table
    

    def get_transactions_form_data(self) -> TransactionTableItemModel:
        price: int = remove_non_digit(self.ui.price_transaction_input.text()) if self.ui.price_transaction_input.text().strip() else 0
        qty: int = remove_non_digit(self.ui.qty_transaction_input.text()) if self.ui.qty_transaction_input.text().strip() else 0
        disc_pct: int = remove_non_digit(self.ui.discount_pct_transaction_input.text()) if self.ui.discount_pct_transaction_input.text().strip() else 0
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
    

    def get_added_updated_deleted_detail_transactions(self, transaction_id: str, detail_transactions_data: list[DetailTransactionModel]) -> tuple[list[DetailTransactionModel], list[DetailTransactionModel], list[DetailTransactionModel]]:
        '''
            Added -> The New DT not in the old DT

            Updated -> The Old DT in the new DT

            Deleted -> The Old DT not in the new DT

            Returns: (added_dt, updated_dt, deleted_dt)
        '''
        
        added_detail_transactions: list[DetailTransactionModel] = []
        updated_detail_transactions: list[DetailTransactionModel] = []
        deleted_detail_transactions: list[DetailTransactionModel] = []

        if transaction_id == '':
            transaction_id = self.ui.transaction_id_transaction_input.text().strip()

        # old_dt_result is the detail transactions of the old transaction
        old_dt_result = self.transaction_service.get_detail_transactions_by_id(transaction_id)
        if not old_dt_result.success:
            return (added_detail_transactions, updated_detail_transactions, deleted_detail_transactions)

        # Get Set of Old Detail Transaction        
        set_of_old_dt: set[tuple[str, str]] = set()
        map_of_old_dt: dict[tuple[str, str], DetailTransactionModel] = {}
        for dt in old_dt_result.data:
            set_of_old_dt.add((dt.sku, dt.unit))
            map_of_old_dt[(dt.sku, dt.unit)] = dt

        # Get Set of New Detail Transaction and Get Added and Updated Detail Transaction
        set_of_new_dt: set[tuple[str, str]] = set()
        for dt in detail_transactions_data:
            dt.transaction_id = transaction_id
            if (dt.sku, dt.unit) in set_of_old_dt: # If the new DT is in the old DT, then it is an updated DT
                updated_detail_transactions.append(dt)

            elif (dt.sku, dt.unit) not in set_of_old_dt: # If the new DT not in the old DT, then it is an added DT
                added_detail_transactions.append(dt)

            set_of_new_dt.add((dt.sku, dt.unit))

        # Get Deleted Detail Transaction
        for old_dt in set_of_old_dt:
            if old_dt not in set_of_new_dt:
                # If the old DT not in the new DT, then it is a deleted DT
                deleted_detail_transactions.append(map_of_old_dt[old_dt])


        return (added_detail_transactions, updated_detail_transactions, deleted_detail_transactions)


    # Setters
    #==========
    def set_transactions_by_id(self, transaction_id: str):
        self.clear_transaction()

        self.ui.transaction_id_transaction_input.setText(transaction_id)

        transactions_result = self.transaction_service.get_transactions_by_id(transaction_id)
        detail_transactions_result = self.transaction_service.get_detail_transactions_by_id(transaction_id)
        if not transactions_result.success:
            POSMessageBox.error(self, title=ERR, message=transactions_result.message)
            return


        if not detail_transactions_result.success:
            POSMessageBox.error(self, title=ERR, message=detail_transactions_result.message)
            return
        

        # Set Transactions Data
        self.ui.customer_id_transaction_input.setText(transactions_result.data.customer_id)
        self.on_handle_customer_enter()

        self.ui.total_transaction_input.setText(add_prefix(format_number(str(transactions_result.data.total_amount))))
        self.ui.total_discount_transaction_input.setText(add_prefix(format_number(str(transactions_result.data.total_discount))))
        self.ui.tax_pct_transaction_input.setText(str(transactions_result.data.tax_pct))
        self.ui.tax_rp_transaction_input.setText(add_prefix(format_number(str(transactions_result.data.tax_amount))))

        self.ui.payment_method_transaction_combobox.setCurrentText(transactions_result.data.payment_method)
        self.ui.remarks_transaction_input.setText(transactions_result.data.payment_remarks)

        # Set Detail Transactions Data
        self.set_transactions_table_data(detail_transactions_result.data)

        # Change Submit Button to Update Button
        self.ui.submit_transaction_button.setText('Update')


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
                self.transactions_table.item(idx, 9).setText(add_prefix(format_number(str(updated_amount))))

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
                    item.setFont(POSFonts.get_font(size=12))
                    self.transactions_table.setItem(current_row, col, item)

                # Add transaction index
                self.cached_transaction_index[transaction_index_key] = current_row
        
        self.transactions_table.setSortingEnabled(True)


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

        self.wholesale_transactions_table.setSortingEnabled(True)


    def set_transaction_form_data(self, data: TransactionTableItemModel):
        self.ui.sku_transaction_input.setText(data.sku)
        self.ui.product_name_transaction_input.setText(data.product_name)
        self.ui.price_transaction_input.setText(add_prefix(format_number(str(data.price))))
        self.ui.qty_transaction_input.setText(format_number(str(data.qty)))
        self.ui.qty_transaction_combobox.setCurrentText(data.unit)
        self.ui.unit_value_transaction_input.setText(format_number(str(data.unit_value)))
        self.ui.discount_pct_transaction_input.setText(str(data.discount_pct))
        self.ui.discount_rp_per_item_transaction_input.setText(str(data.discount_rp_per_item))
        self.ui.discount_rp_total_transaction_input.setText(str(data.discount_rp))
    

    def set_purchasing_history_table_data(self, data: list[PurchasingHistoryTableItemModel]):
        # Clear Purchasing History Table
        self.purchase_history_table.setRowCount(0)

        for purchasing_history in data:
            current_row = self.purchase_history_table.rowCount()
            self.purchase_history_table.insertRow(current_row)

            # Convert created_at string to datetime and format
            created_at_dt = datetime.strptime(purchasing_history.created_at, '%Y-%m-%d %H:%M:%S')
            formatted_date = created_at_dt.strftime('%d %b %y %H:%M')

            table_items =  [ 
                QtWidgets.QTableWidgetItem(formatted_date),
                QtWidgets.QTableWidgetItem(format_number(purchasing_history.qty)),
                QtWidgets.QTableWidgetItem(purchasing_history.unit),
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.purchase_history_table.setItem(current_row, col, item)

        self.purchase_history_table.setSortingEnabled(True)


    def set_transaction_history_table_data(self, data: list[TransactionHistoryTableModel]):
        # Clear Purchasing History Table
        self.transaction_history_table.setRowCount(0)

        for transaction_history in data:
            current_row = self.transaction_history_table.rowCount()
            self.transaction_history_table.insertRow(current_row)

            # Convert created_at string to datetime and format
            created_at_dt = datetime.strptime(transaction_history.created_at, '%Y-%m-%d %H:%M:%S')
            formatted_date = created_at_dt.strftime('%d %b %y %H:%M')

            table_items =  [ 
                QtWidgets.QTableWidgetItem(formatted_date),
                QtWidgets.QTableWidgetItem(format_number(transaction_history.qty)),
                QtWidgets.QTableWidgetItem(transaction_history.unit),
            ]
            
            for col, item in enumerate(table_items):
                item.setFont(POSFonts.get_font(size=12))
                self.transaction_history_table.setItem(current_row, col, item)

        self.transaction_history_table.setSortingEnabled(True)  


    # Event Listeners
    #====================
    def on_qty_transaction_input_changed(self):
        if '-' in self.ui.qty_transaction_input.text():
            POSMessageBox.error(self, title=ERR, message="Quantity cannot be negative")
            self.ui.qty_transaction_input.clear()
            return

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


    def on_transaction_selected(self):
        if self.transactions_table.selectedItems():
            self.current_selected_sku = self.transactions_table.selectedItems()[0].row()


    def on_handle_sku_enter(self):
        sku = self.ui.sku_transaction_input.text().strip().upper()
        if not sku:
            self.clear_data_transaction()
            return

        # Try to find exact SKU match
        result = self.transaction_service.get_product_by_sku(sku)
        
        if result['success']:
            # Product found - fill the form
            self.handle_product_selected({'sku' : sku})
            self.show_wholesale_transactions_data(sku)
            self.show_purchasing_history_data(sku)
            self.show_transaction_history_data(sku)

        else:
            # Product not found - show dialog with filter
            self.products_dialog.set_filter(sku)
            self.products_dialog.show()


    def on_discount_transaction_radio_button_toggled(self):
        if self.ui.discount_pct_transaction_radio_button.isChecked():
            self.ui.discount_pct_transaction_input.clear()
            self.ui.discount_pct_transaction_input.setEnabled(True)
            self.ui.discount_pct_transaction_input.setClearButtonEnabled(True)

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
            
            self.ui.discount_pct_transaction_input.setEnabled(False)
            self.ui.discount_pct_transaction_input.setText('0')
            self.ui.discount_pct_transaction_input.setClearButtonEnabled(False)

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

            self.ui.discount_pct_transaction_input.setEnabled(False)
            self.ui.discount_pct_transaction_input.setText('0')
            self.ui.discount_pct_transaction_input.setClearButtonEnabled(False)


    def on_calculate_discount_rp(self):
        if '-' in self.ui.discount_rp_total_transaction_input.text() or \
            '-' in self.ui.discount_rp_per_item_transaction_input.text() or \
                '-' in self.ui.discount_pct_transaction_input.text():
            POSMessageBox.error(self, title=ERR, message="Discount cannot be negative")
            self.ui.discount_rp_total_transaction_input.clear()
            self.ui.discount_rp_per_item_transaction_input.clear()
            self.ui.discount_pct_transaction_input.clear()
            return
        
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


    def on_handle_customer_enter(self):
        customer_id = self.ui.customer_id_transaction_input.text().strip().upper()
        if not customer_id:
            return

        # Try to find exact customer match
        result = self.transaction_service.get_customer_by_id(customer_id)

        if result.success and result.data:
            # Customer found - fill the form
            self.ui.customer_name_transaction_input.setText(result.data)

            # Set focus to sku input
            self.ui.sku_transaction_input.setFocus()
            
        else:
            # Customer not found - show dialog with filter
            self.customers_dialog.set_filter(customer_id)
            self.customers_dialog.show()


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


    def clear_purchasing_history_data(self):
        self.purchase_history_table.setRowCount(0)


    def clear_transaction_history_data(self):
        self.transaction_history_table.setRowCount(0)


    def clear_transaction(self):
        # Remove All Items from Transactions Table
        self.transactions_table.setRowCount(0)
        self.ui.total_transaction_input.setText(add_prefix('0'))
        self.ui.total_discount_transaction_input.setText(add_prefix('0'))
        self.cached_transaction_index = {}
        self.cached_qty = {}
        self.current_selected_sku = None
        self.ui.customer_id_transaction_input.clear()
        self.ui.customer_name_transaction_input.clear()
        self.ui.tax_pct_transaction_input.clear()
        self.ui.tax_rp_transaction_input.clear()
        self.ui.remarks_transaction_input.clear()
        self.ui.transaction_id_transaction_input.clear()
        self.ui.submit_transaction_button.setText('Submit')
        self.ui.submit_transaction_button.clicked.disconnect()
        self.ui.submit_transaction_button.clicked.connect(self.trigger_submit_payment_transactions)
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
        self.ui.discount_pct_transaction_input.clear()
        self.ui.discount_rp_per_item_transaction_input.clear()
        self.ui.discount_rp_total_transaction_input.clear()
        self.clear_wholesale_transactions_data()
        self.clear_purchasing_history_data()
        self.clear_transaction_history_data()
    

    # Direct printing without preview
    # ===============
    def print_transactions(self, transaction_data: TransactionModel, detail_transactions_data: list[TransactionTableItemModel]):
        """Print the current transactions data directly without preview"""
        customer_result = self.transaction_service.get_customer_by_id(self.ui.customer_id_transaction_input.text().strip())
        customer_name = None
        if customer_result.success and customer_result.data:
            customer_name = customer_result.data
            
        printer_service = PrinterService()
        # printer_service.print_receipt(transaction_data=transaction_data, detail_transactions=detail_transactions, customer_name=customer_name)
        printer_service.show_preview(transaction_data=transaction_data, detail_transactions=detail_transactions_data, customer_name=customer_name)        


    # Event Filter
    # ===============
    def eventFilter(self, obj, event):
        # If qty input is focused and key pressed is Enter it automatically show the unit combobox or update
        if obj == self.ui.qty_transaction_input and event.type() == QtCore.QEvent.Type.KeyPress:
            key = event.key()

            # Check for Enter
            if key in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
                text = self.ui.qty_transaction_input.text()
                if text.isdigit():
                    # If add button text is update, update the detail transaction
                    button_text = self.ui.add_transaction_button.text().strip().lower()
                    if button_text == 'update':
                        self.update_detail_transaction()
                        self.ui.sku_transaction_input.setFocus()

                    else:
                        # Show the unit combobox if is insert mode
                        self.ui.qty_transaction_combobox.showPopup()

                else:
                    self.ui.qty_transaction_input.clear()

                return True # prevent further processing
            
            if key == QtCore.Qt.Key.Key_Up:
                self.ui.sku_transaction_input.setFocus()
                return True # prevent further processing


        return super().eventFilter(obj, event)


    def keyPressEvent(self, event):
        if (event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier) and event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            self.trigger_submit_payment_transactions()
            return
            
        super().keyPressEvent(event)


    def on_unit_selected(self, index):
        qty_text = self.ui.qty_transaction_input.text()
        # Only proceed if qty is a valid number and not empty
        if qty_text.isdigit() and int(qty_text) > 0:
            self.add_detail_transaction()
            self.ui.sku_transaction_input.setFocus()
        