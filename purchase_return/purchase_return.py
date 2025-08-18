from PyQt6 import QtWidgets, uic

from purchase_return.services.purchase_return_services import PurchaseReturnService
from purchase_return.models.purchase_return_models import PurchaseReturnModel

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


class PurchaseReturnWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/purchase_return.ui'), self)

        # Init Services
        self.purchase_return_service = PurchaseReturnService()
