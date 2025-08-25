from PyQt6 import QtWidgets, uic

from sales_return.services.sales_return_services import SalesReturnService
from sales_return.models.sales_return_models import SalesReturnModel

from helper import format_number, add_prefix, remove_non_digit
from generals.message_box import POSMessageBox
from generals.build import resource_path
from generals.fonts import POSFonts
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS
)
from generals.messages import (
    ERR, OK, PERM_DENIED
)
from generals.permission_manager import PermissionManager

    
class SalesReturnWindow(QtWidgets.QWidget):
    def __init__(self, home_window: None):
        super().__init__()

        self.home_window = home_window

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/sales_return.ui'), self)

        # Init Services
        self.sales_return_service = SalesReturnService()
