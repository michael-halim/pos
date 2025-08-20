from PyQt6 import QtWidgets, uic

from sales_return_list.services.sales_return_list_services import SalesReturnListService
from sales_return_list.models.sales_return_list_models import SalesReturnListModel

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


class SalesReturnListWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/sales_return_list.ui'), self)

        # Init Services
        self.sales_return_list_service = SalesReturnListService()
