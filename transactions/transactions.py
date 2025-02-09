from PyQt6 import QtWidgets, uic
from datetime import datetime

from helper import format_number, add_prefix, remove_non_digit
from transactions.pending_transactions import PendingTransactionsWindow
from transactions.products_in_transactions import ProductsInTransactionWindow
from transactions.services.transaction_service import TransactionService
from transactions.models.transactions_models import TransactionModel, DetailTransactionModel, PendingTransactionModel, PendingDetailTransactionModel

from generals.message_box import POSMessageBox
from generals.fonts import POSFonts

class TransactionsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi('./ui/transactions.ui', self)

        # Init Services
        self.transaction_service = TransactionService()

        # Init Dialog
        self.products_in_transaction_dialog = ProductsInTransactionWindow()
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
        self.ui.check_sku_transaction_button.clicked.connect(self.check_sku)
        self.ui.edit_transaction_button.clicked.connect(self.edit_transaction)
        self.ui.delete_transaction_button.clicked.connect(self.delete_transaction)
        self.ui.submit_transaction_button.clicked.connect(self.submit_transaction)
        self.ui.pending_transaction_button.clicked.connect(self.create_pending_transaction)
        self.ui.open_pending_transaction_button.clicked.connect(lambda: self.pending_transactions_dialog.showMaximized())

        # Add 2 items to payment method combobox
        self.ui.payment_method_transaction_combobox.addItems(['Cash', 'Transfer'])

        # Add selected tracking
        self.current_selected_sku = None
        self.cached_qty = {} # key = <sku>_<unit>, value = (unit_value, stock, price)
        self.cached_transaction_index = {} # key = <sku>_<unit>, value = transaction_table_index

        # Add a flag to track if we're loading items
        self.is_loading_combo = False

    
        # Event Listeners
        #====================

        # Connect table selection
        self.transactions_table.itemSelectionChanged.connect(self.on_transaction_selected)
        
        # Connect qty combobox to update qty input
        self.ui.qty_transaction_combobox.currentTextChanged.connect(self.on_qty_transaction_combobox_changed)

        # Connect qty input to update stock after input
        self.ui.qty_transaction_input.textChanged.connect(self.on_qty_transaction_input_changed)

        # Connect payment input to update payment change
        self.ui.payment_transaction_input.textChanged.connect(self.on_payment_transaction_input_changed)


        # Set selection behavior to select entire rows
        self.transactions_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.transactions_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)


        # Set table properties
        self.transactions_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.transactions_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.wholesale_transactions_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.wholesale_transactions_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.history_transactions_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.history_transactions_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

   
    def show_history_transactions_data(self):
        pass

    def show_wholesale_transactions_data(self):
        pass
    

    def on_payment_transaction_input_changed(self):
        payment_rp = remove_non_digit(self.ui.payment_transaction_input.text())
        total_amount = remove_non_digit(self.ui.total_transaction_input.text())
        if payment_rp == '':
            self.ui.payment_change_transaction_input.setText(add_prefix(format_number(str(total_amount))))
            self.ui.payment_change_transaction_input.setStyleSheet('color: red;')
            return
        
        payment_change = int(total_amount) - int(payment_rp)
        self.ui.payment_change_transaction_input.setText(add_prefix(format_number(str(payment_change))))


        self.ui.payment_change_transaction_input.setStyleSheet('color: red;')

        if payment_change <= 0:
            self.ui.payment_change_transaction_input.setStyleSheet('color: black;')

    def on_transaction_selected(self):
        if self.transactions_table.selectedItems():
            self.current_selected_sku = self.transactions_table.selectedItems()[0].row()



    def clear_transaction(self):
        # Remove All Items from Transactions Table
        self.transactions_table.setRowCount(0)
        self.ui.total_transaction_input.setText(add_prefix('0'))
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
    

    def add_transaction(self):
        # Stop temporary sorting
        self.transactions_table.setSortingEnabled(False)

        try:
            sku: str = self.ui.sku_transaction_input.text().strip()
            name: str = self.ui.product_name_transaction_input.text().strip()
            price: str = remove_non_digit(self.ui.price_transaction_input.text().strip())
            qty: str = remove_non_digit(self.ui.qty_transaction_input.text().strip())
            unit: str = self.ui.qty_transaction_combobox.currentText().strip()
            unit_value: str = remove_non_digit(self.ui.unit_value_transaction_input.text().strip())
            discount_rp: str = remove_non_digit(self.ui.discount_rp_transaction_input.text()) if self.ui.discount_rp_transaction_input.text() else '0'
            discount_pct: str = remove_non_digit(self.ui.discount_pct_transaction_input.text()) if self.ui.discount_pct_transaction_input.text() else '0'
            amount: str = str(int(price) * int(qty))

            # Check transaction index if sku and unit is same
            transaction_index_key = f'{sku}_{unit}'
            if transaction_index_key in self.cached_transaction_index:
                # Update qty, amount
                idx = self.cached_transaction_index[transaction_index_key]
                price: str = remove_non_digit(self.transactions_table.item(idx, 2).text())
                updated_qty: int = int(remove_non_digit(self.transactions_table.item(idx, 3).text())) + int(qty)
                updated_amount: int = int(price) * int(updated_qty)

                self.transactions_table.item(idx, 3).setText(format_number(str(updated_qty)))
                self.transactions_table.item(idx, 8).setText(add_prefix(format_number(str(updated_amount))))

            else:
                current_row = self.transactions_table.rowCount()
                self.transactions_table.insertRow(current_row)

                # Add item to transactions table
                items = [
                    QtWidgets.QTableWidgetItem(value) for value in 
                    [sku, name, add_prefix(format_number(price)), format_number(qty), unit, 
                     unit_value, add_prefix(format_number(discount_rp)), 
                     add_prefix(format_number(discount_pct)), add_prefix(format_number(amount))]
                ]

                for col, item in enumerate(items):
                    item.setFont(POSFonts.get_font(size=16))
                    self.transactions_table.setItem(current_row, col, item)

                # Add transaction index
                self.cached_transaction_index[transaction_index_key] = current_row

                
            # Update total amount
            total_amount = int(remove_non_digit(self.ui.total_transaction_input.text())) + int(amount)
            self.ui.total_transaction_input.setText(add_prefix(format_number(str(total_amount))))

            # Update payment change
            self.ui.payment_change_transaction_input.setText(add_prefix(format_number(str(total_amount))))
            self.ui.payment_change_transaction_input.setStyleSheet('color: red;')

            # Clear data transaction
            self.clear_data_transaction()

            # After adding new row, reapply filter if there's any
            self.filter_transactions()

        except Exception as e:
            POSMessageBox.error(self, title='Error', message=f"Failed to add transaction: {str(e)}")

        finally:
            # Re-enable sorting
            self.transactions_table.setSortingEnabled(True)


    def edit_transaction(self):
        # Get selected row
        selected_rows = self.transactions_table.selectedItems()
        if selected_rows:
            self.current_selected_sku = selected_rows[0].row()

            self.ui.add_transaction_button.setText('Update')
            
            # Disconnect existing connections and connect to update function
            self.ui.add_transaction_button.clicked.disconnect()
            self.ui.add_transaction_button.clicked.connect(self.update_transaction)

            # Get sku, unit, unit_value, qty, price, discount_rp, discount_pct, subtotal
            sku = self.transactions_table.item(self.current_selected_sku, 0).text()
            product_name = self.transactions_table.item(self.current_selected_sku, 1).text()
            unit = self.transactions_table.item(self.current_selected_sku, 4).text()

            unit_value = self.transactions_table.item(self.current_selected_sku, 5).text()
            qty = remove_non_digit(self.transactions_table.item(self.current_selected_sku, 3).text())
            price = remove_non_digit(self.transactions_table.item(self.current_selected_sku, 2).text())
            discount_rp = remove_non_digit(self.transactions_table.item(self.current_selected_sku, 6).text())
            discount_pct = remove_non_digit(self.transactions_table.item(self.current_selected_sku, 7).text())

            # Put the data into the form
            self.ui.sku_transaction_input.setText(sku)
            self.ui.product_name_transaction_input.setText(product_name)
            self.ui.price_transaction_input.setText(price)
            self.ui.qty_transaction_input.setText(qty)
            self.ui.qty_transaction_combobox.setCurrentText(unit)
            self.ui.unit_value_transaction_input.setText(unit_value)
            self.ui.discount_rp_transaction_input.setText(discount_rp)
            self.ui.discount_pct_transaction_input.setText(discount_pct)

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
                qty = self.ui.qty_transaction_input.text().strip()
                price = remove_non_digit(self.ui.price_transaction_input.text())
                
                # Calculate new subtotal
                subtotal = int(price) * int(qty)
                
                # Update the row in the table
                self.transactions_table.item(self.current_selected_sku, 3).setText(format_number(qty))
                self.transactions_table.item(self.current_selected_sku, 8).setText(add_prefix(format_number(str(subtotal))))
                
                # Update total amount
                total = 0
                for row in range(self.transactions_table.rowCount()):
                    total += int(remove_non_digit(self.transactions_table.item(row, 8).text()))
                self.ui.total_transaction_input.setText(add_prefix(format_number(str(total))))
                
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
                
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to update transaction: {str(e)}")

    def delete_transaction(self):
        selected_rows = self.transactions_table.selectedItems()
        if not selected_rows:
            POSMessageBox.warning(self, title='Warning', message="Please select a transaction to delete")
            return

        # Confirm deletion
        confirm = POSMessageBox.confirm(self, title="Confirm Deletion", message="Are you sure you want to delete this transaction ?")

        if confirm:
            row = selected_rows[0].row()

            # Get the transaction details before deletion
            sku = self.transactions_table.item(row, 0).text()
            unit = self.transactions_table.item(row, 4).text()
            subtotal = remove_non_digit(self.transactions_table.item(row, 8).text())

            # Remove from cached index
            transaction_index_key = f'{sku}_{unit}'
            if transaction_index_key in self.cached_transaction_index:
                del self.cached_transaction_index[transaction_index_key]

            # Remove the row from table
            self.transactions_table.removeRow(row)

            # Update total amount
            total_amount = int(remove_non_digit(self.ui.total_transaction_input.text())) - int(subtotal)
            self.ui.total_transaction_input.setText(add_prefix(format_number(str(total_amount))))

            # Update payment change if payment exists
            payment_rp = remove_non_digit(self.ui.payment_transaction_input.text())
            if payment_rp:
                payment_change = int(total_amount) - int(payment_rp)
                self.ui.payment_change_transaction_input.setText(add_prefix(format_number(str(payment_change))))
                if payment_change <= 0:
                    self.ui.payment_change_transaction_input.setStyleSheet('color: black;')
                else:
                    self.ui.payment_change_transaction_input.setStyleSheet('color: red;')

    def submit_transaction(self):
        payment_rp: str = remove_non_digit(self.ui.payment_transaction_input.text())
        if payment_rp == '':
            POSMessageBox.error(self, title='Error', message="Payment cannot be empty")
            return

        transaction_id: str = self.transaction_service.create_transaction_id()
        
        # Get detail transactions from transactions table
        detail_transactions, total_amount = self.get_detail_transactions()

        detail_transactions_data: list[DetailTransactionModel] = []
        for detail_transaction in detail_transactions:
            detail_transactions_data.append(DetailTransactionModel(
                transaction_id = transaction_id,
                sku = detail_transaction['sku'],
                unit = detail_transaction['unit'],
                unit_value = detail_transaction['unit_value'],
                qty = detail_transaction['qty'],
                price = detail_transaction['price'],
                discount_rp = detail_transaction['discount_rp'],
                subtotal = detail_transaction['subtotal']
            ))
        

        payment_change: int = total_amount - int(payment_rp)

        transaction_data: TransactionModel = TransactionModel(
            transaction_id = transaction_id,
            total_amount = total_amount,
            payment_amount = payment_rp,
            payment_change = payment_change,
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            payment_method = self.ui.payment_method_transaction_combobox.currentText(),
            payment_remarks = self.ui.remarks_transaction_input.toPlainText().strip(),
        )

        result = self.transaction_service.submit_transaction(transaction_data, detail_transactions_data)
        if result.success:
            POSMessageBox.info(self, title='Success', message=result.message)
        else:
            POSMessageBox.error(self, title='Error', message=result.message)


        # Clear the transactions table and total
        self.clear_transaction()

 
    def create_pending_transaction(self):
        transaction_id: str = self.transaction_service.create_transaction_id(is_pending=True)

        # Get detail transactions from transactions table
        detail_transactions, total_amount = self.get_detail_transactions()
        pending_detail_transactions_data = []
        for detail_transaction in detail_transactions:
            pending_detail_transactions_data.append(PendingDetailTransactionModel(
                transaction_id = transaction_id,
                sku = detail_transaction['sku'],
                unit = detail_transaction['unit'],
                unit_value = detail_transaction['unit_value'],
                qty = detail_transaction['qty'],
                price = detail_transaction['price'],
                discount = detail_transaction['discount_rp'],   
                subtotal = detail_transaction['subtotal']
            ))


        pending_transaction_data = PendingTransactionModel(
            transaction_id = transaction_id,
            total_amount = total_amount,
            discount_transaction_id = 1,
            discount_amount = 0,
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            payment_remarks = self.ui.remarks_transaction_input.toPlainText().strip()
        )

        result = self.transaction_service.create_pending_transaction(pending_transaction_data, pending_detail_transactions_data)
        if result.success:
            POSMessageBox.information(self, "Success", result.message)
        else:
            POSMessageBox.critical(self, "Error", result.message)

        # Clear the transactions table and total
        self.clear_transaction()

    def handle_product_selected(self, product_data):
         # Fill the form fields with selected product data
        self.ui.sku_transaction_input.setText(product_data['sku'])
        self.ui.product_name_transaction_input.setText(product_data['product_name'])
        self.ui.price_transaction_input.setText(add_prefix(format_number(str(product_data['price']))))
        self.ui.unit_value_transaction_input.setText(format_number(str(product_data['unit_value'])))

        stock = int(product_data['stock'].replace('.', ''))
        self.ui.stock_transaction_input.setText(format_number(str(stock)))
        self.ui.stock_after_transaction_input.setText(format_number(str(stock)))

        if stock < 0:   
            self.ui.stock_transaction_input.setText(f'-{format_number(str(abs(stock)))}')
            self.ui.stock_after_transaction_input.setText(f'-{format_number(str(abs(stock)))}')
            self.ui.stock_transaction_input.setStyleSheet('color: red;')
            self.ui.stock_after_transaction_input.setStyleSheet('color: red;')

        # Set loading flag
        self.is_loading_combo = True
        
        # Clear existing items
        self.ui.qty_transaction_combobox.clear()
        
        # Set product unit details (Combo Box)
        self.set_product_unit_details(product_data['sku'])
       
        # Reset loading flag
        self.is_loading_combo = False
        
        # Set the unit in combobox
        index = self.ui.qty_transaction_combobox.findText(product_data['unit'])
        if index >= 0:
            self.ui.qty_transaction_combobox.setCurrentIndex(index)
            

    def check_sku(self):
        sku = self.ui.sku_transaction_input.text().strip()
        product = self.transaction_service.get_product_by_sku(sku)

        if product:
            self.ui.product_name_transaction_input.setText(product.product_name)
            self.ui.price_transaction_input.setText(add_prefix(format_number(str(product.price))))

            # Set loading flag
            self.is_loading_combo = True
            
            # Clear existing items
            self.ui.qty_transaction_combobox.clear()

            # Set product unit details (Combo Box)
            self.set_product_unit_details(sku)
            
            # Reset loading flag
            self.is_loading_combo = False
            
            # Set the unit in combobox
            self.ui.qty_transaction_combobox.setCurrentIndex(0)
            
            # Calculate stock after existing transactions
            current_unit = self.ui.qty_transaction_combobox.currentText()
            
            self.calculate_stock_after_transactions(sku, current_unit)

        else:
            POSMessageBox.error(self, title='Error', message="Product not found")

    def get_total_qty_in_transactions(self, sku: str, unit: str) -> int:
        total_qty = 0
        for row in range(self.transactions_table.rowCount()):
            if (self.transactions_table.item(row, 0).text() == sku and 
                self.transactions_table.item(row, 4).text() == unit):
                total_qty += int(remove_non_digit(self.transactions_table.item(row, 3).text()))
        return total_qty

    def calculate_stock_after_transactions(self, sku: str, unit: str):
        # Get initial stock
        cache_key = f'{sku}_{unit}'
        if cache_key in self.cached_qty:
            initial_stock = self.cached_qty[cache_key][2]

            self.ui.stock_transaction_input.setStyleSheet('color: black;')
            self.ui.stock_transaction_input.setText(format_number(str(initial_stock)))

            if initial_stock < 0:
                self.ui.stock_transaction_input.setText(f'-{format_number(str(abs(initial_stock)))}')
                self.ui.stock_transaction_input.setStyleSheet('color: red;')
            

            # Get total qty in transaction table for this sku and unit
            total_qty_in_transactions = self.get_total_qty_in_transactions(sku, unit)
            
            # Calculate and display stock after transactions
            stock_after = initial_stock - total_qty_in_transactions
            
            # Set color based on stock level
            self.ui.stock_after_transaction_input.setText(format_number(str(stock_after)))
            self.ui.stock_after_transaction_input.setStyleSheet('color: black;')

            if stock_after < 0:
                self.ui.stock_after_transaction_input.setText(f'-{format_number(str(abs(stock_after)))}')
                self.ui.stock_after_transaction_input.setStyleSheet('color: red;')

    def handle_pending_transaction_selected(self, pending_transaction_data):
        result = self.transaction_service.get_pending_transactions_by_transaction_id(pending_transaction_data['transaction_id'])
        if result['message'].success == False:
            POSMessageBox.critical(self, "Error", result['message'].message)
            return


        # put the data into transactions table
        subtotal = 0
        for result in result['data']:
            current_row = self.transactions_table.rowCount()
            self.transactions_table.insertRow(current_row)
            subtotal += int(result.subtotal)

            items = [
                QtWidgets.QTableWidgetItem(value) for value in 
                [result.sku, result.product_name, add_prefix(format_number(result.price)), 
                 format_number(result.qty), result.unit, format_number(result.unit_value), 
                 add_prefix(format_number(result.discount)), add_prefix(format_number(result.discount)), 
                 add_prefix(format_number(result.subtotal))]
            ]

            for col, item in enumerate(items):
                item.setFont(POSFonts.get_font(size=16))
                self.transactions_table.setItem(current_row, col, item)
        

        self.ui.total_transaction_input.setText(add_prefix(format_number(str(subtotal))))


    def on_qty_transaction_input_changed(self):
        sku = self.ui.sku_transaction_input.text().strip()
        unit = self.ui.qty_transaction_combobox.currentText()
        qty = remove_non_digit(self.ui.qty_transaction_input.text())
        stock = self.ui.stock_transaction_input.text().replace('.', '').strip()

        if qty == '' or stock == '':
            self.ui.stock_after_transaction_input.setStyleSheet('color: black;')
            self.calculate_stock_after_transactions(sku, unit)
            return
        
        total_qty_in_transactions = self.get_total_qty_in_transactions(sku, unit)
        qty_after_transaction = int(stock) - int(qty) - total_qty_in_transactions
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

    def set_product_unit_details(self, sku: str):
        '''
            Set the product unit into combobox

            sku and unit is the unique key, and the value is (unit_value, price, stock)
            behind the scene the sku and unit is stored using dictionary called cached_qty
            Example: 
            
            ```cache_key = 'SKU001'
            cached_qty = {
                'SKU001_pcs' : (1, 10000, 100),  #(pcs unit value is 1, price is 10.000, stock is 100)
                'SKU001_kodi' : (20, 100000, 100), #(kodi unit value is 20, price is 100.000, stock is 100)
            }
            ```

        '''

        product_unit_details = self.transaction_service.get_product_unit_details(sku)
        for pud in product_unit_details:
            # key = <sku>_<unit>, value = (unit_value, price, stock)
            cache_key = f'{sku}_{pud.unit}'
            self.cached_qty[cache_key] = (pud.unit_value, pud.price, pud.stock)
            self.ui.qty_transaction_combobox.addItem(pud.unit)

    def get_detail_transactions(self) -> tuple[list[dict], int]:
        '''
            Returns a tuple of (detail_transactions, total_amount)
            
            detail_transactions data is all the details from transactions table
            total_amount is the total amount of the transactions
        '''
        detail_transactions = []
        total_amount = 0
        for row in range(self.transactions_table.rowCount()):

            sku = self.transactions_table.item(row, 0).text()
            price = remove_non_digit(self.transactions_table.item(row, 2).text())
            qty = remove_non_digit(self.transactions_table.item(row, 3).text())
            unit = self.transactions_table.item(row, 4).text()
            unit_value = self.transactions_table.item(row, 5).text()
            discount_rp = remove_non_digit(self.transactions_table.item(row, 6).text())
            discount_pct = remove_non_digit(self.transactions_table.item(row, 7).text())
            subtotal = remove_non_digit(self.transactions_table.item(row, 8).text())

            total_amount += int(subtotal)

            detail_transactions.append({
                'sku' : sku,
                'price' : price,
                'qty' : qty,
                'unit' : unit,
                'unit_value' : unit_value,
                'discount_rp' : discount_rp,
                'discount_pct' : discount_pct,
                'subtotal' : subtotal,
            })

        return (detail_transactions, total_amount)