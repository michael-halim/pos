from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QDateEdit
from datetime import datetime

from helper import format_number, add_prefix, remove_non_digit

from transactions.pending_transactions import PendingTransactionsWindow
from transactions.products_in_transactions import ProductsInTransactionWindow

from transactions.services.transaction_service import TransactionService

from transactions.models.transactions_models import TransactionTableItemModel, PendingTransactionModel, TransactionModel, DetailTransactionModel
from transactions.models.wholesale_models import WholesaleTableModel

from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS
from generals.build import resource_path

class RolesDialogWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/roles_dialog.ui'), self)

    