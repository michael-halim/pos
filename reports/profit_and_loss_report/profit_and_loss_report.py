from PyQt6 import QtWidgets, uic

from helper import format_number, add_prefix, remove_non_digit
from generals.message_box import POSMessageBox
from generals.fonts import POSFonts
from generals.constants import RESIZE_TO_CONTENTS, SELECT_ROWS, SINGLE_SELECTION, NO_EDIT_TRIGGERS
from generals.build import resource_path

from reports.profit_and_loss_report.services.profit_and_loss_report_services import ProfitAndLossReportService
from reports.profit_and_loss_report.models.profit_and_loss_report_models import ProfitAndLossReportModel

class ProfitAndLossReportWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/profit_and_loss_report.ui'), self)

        # Init Services
        self.profit_and_loss_report_service = ProfitAndLossReportService()
