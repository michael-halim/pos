from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QDateEdit
from datetime import datetime

from helper import format_number, add_prefix, remove_non_digit

from customers.services.customers_services import CustomersService

from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS
from generals.build import resource_path

class CustomersWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/customers.ui'), self)

        # Init Services
        self.customer_service = CustomersService()

        