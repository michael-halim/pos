from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import pyqtSignal

from helper import format_number, add_prefix, remove_non_digit

from generals.message_box import POSMessageBox
from generals.build import resource_path
from generals.constants import PERM_C_TRANSACTIONS
from generals.messages import ERR_PERM_C_TRANSACTIONS, PERM_DENIED
from dialogs.payment_transactions_dialog.translations import PAYMENT_TRANSACTIONS_DIALOG_TRANSLATIONS
from generals.language_manager import LanguageManager
from generals.permission_manager import PermissionManager

class PaymentTransactionsDialogWindow(QtWidgets.QWidget):
    transactions_submitted = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_C_TRANSACTIONS):
            return

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/payment_transactions_dialog.ui'), self)

        # Connect buttons
        self.ui.close_payment_transaction_dialog_button.clicked.connect(lambda: self.close())
        self.ui.submit_payment_transcations_button.clicked.connect(self.submit_payment_transactions)

        # Connect text changed
        self.ui.payment_transaction_input.textChanged.connect(self.on_payment_transaction_input_changed)

        # Handle enter on payment input
        self.ui.payment_transaction_input.returnPressed.connect(self.submit_payment_transactions)

        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(PAYMENT_TRANSACTIONS_DIALOG_TRANSLATIONS)


    # Overrides
    # ===============
    def showEvent(self, event):
        super().showEvent(event)
        if not self.permission_manager.has_permission(PERM_C_TRANSACTIONS):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_C_TRANSACTIONS)
            self.close()
            return

        # Set window title
        if self.permission_manager.get_username().lower() not in self.windowTitle().lower():
            self.setWindowTitle(self.windowTitle() + ' - ' + self.permission_manager.get_username())

        self.language_manager.translate_widget_text(self)


    def show(self):
        super().show()
        if not self.permission_manager.has_permission(PERM_C_TRANSACTIONS):
            self.close()
            return
        

    def showMaximized(self):
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_C_TRANSACTIONS):
            self.close()
            return


    def submit_payment_transactions(self):
        payment_rp: str = remove_non_digit(self.ui.payment_transaction_input.text())
        if payment_rp == '':
            POSMessageBox.error(self, title='Error', message="Payment cannot be empty")
        
        total_amount: str = remove_non_digit(self.ui.total_transaction_input.text())

        # Calculate payment change
        payment_change: int = int(total_amount) - int(payment_rp)
        if payment_change > 0:
            POSMessageBox.error(self, title='Error', message="Payment cannot be less than total amount")
            return
        
        
        self.ui.payment_transaction_input.clear()
        self.transactions_submitted.emit({'payment_amount': payment_rp, 'payment_change': payment_change})
        self.close()


    def set_payment(self, total_amount: int):
        self.ui.total_transaction_input.setText(add_prefix(format_number(str(total_amount))))
        self.ui.payment_change_transaction_input.setText(add_prefix(format_number(str(total_amount))))


    def on_payment_transaction_input_changed(self):
        self.ui.payment_transaction_input.textChanged.disconnect()

        # Format payment input
        payment_rp = remove_non_digit(self.ui.payment_transaction_input.text().strip()) if remove_non_digit(self.ui.payment_transaction_input.text().strip()) != '' else '0'

        self.ui.payment_transaction_input.setText(add_prefix(format_number(str(int(payment_rp)))))
        self.ui.payment_transaction_input.textChanged.connect(self.on_payment_transaction_input_changed)

        total_amount = remove_non_digit(self.ui.total_transaction_input.text())
        if payment_rp == '':
            POSMessageBox.error(self, title='Error', message="Payment cannot be empty")
            return
        
        payment_change = int(total_amount) - int(payment_rp)

        self.ui.payment_change_transaction_input.setText(add_prefix(format_number(str(payment_change))))
        if payment_change > 0:
            self.ui.payment_change_transaction_input.setText('- ' + add_prefix(format_number(str(abs(payment_change)))))
            