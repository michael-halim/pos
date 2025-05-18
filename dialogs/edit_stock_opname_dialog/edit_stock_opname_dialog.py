from PyQt6 import QtWidgets, uic

from dialogs.edit_stock_opname_dialog.services.edit_stock_opname_dialog_services import EditStockOpnameDialogService
from stock_opname.models.stock_opname_models import EditStockOpnameModel

from generals.message_box import POSMessageBox
from generals.build import resource_path
from generals.constants import PERM_U_STOCK_OPNAME
from generals.messages import ERR_PERM_U_STOCK_OPNAME, PERM_DENIED
from dialogs.edit_stock_opname_dialog.translations import EDIT_STOCK_OPNAME_DIALOG_TRANSLATIONS
from generals.language_manager import LanguageManager
from generals.permission_manager import PermissionManager


class EditStockOpnameDialogWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_U_STOCK_OPNAME):
            return

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/edit_stock_opname_dialog.ui'), self)

        # Init Services
        self.edit_stock_opname_dialog_service = EditStockOpnameDialogService()

        # Connect buttons
        self.ui.cancel_stock_opname_button.clicked.connect(lambda: self.close())
        self.ui.edit_stock_opname_button.clicked.connect(self.edit_stock_opname)

        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(EDIT_STOCK_OPNAME_DIALOG_TRANSLATIONS)

        # Translate Widget Text
        self.language_manager.translate_widget_text(self)   


    # Overrides
    # ============
    def showEvent(self, event) -> None:
        super().showEvent(event)

        if not self.permission_manager.has_permission(PERM_U_STOCK_OPNAME):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_U_STOCK_OPNAME)
            self.close()
            return

        # Set window title
        if self.permission_manager.get_username().lower() not in self.windowTitle().lower():
            self.setWindowTitle(self.windowTitle() + ' - ' + self.permission_manager.get_username())


    def show(self):
        super().show()
        if not self.permission_manager.has_permission(PERM_U_STOCK_OPNAME):
            self.close()
            return

    
    def showMaximized(self):
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_U_STOCK_OPNAME):
            self.close()
            return


    def edit_stock_opname(self):
        stock_opname_id = self.ui.stock_opname_id_input.text().strip()
        final_stock = self.ui.final_stock_stock_opname_input.text().strip()

        if final_stock == '':
            POSMessageBox.error(self, title='Error', message="Final stock cannot be empty")
            return
        
        stock_opname_result = self.edit_stock_opname_dialog_service.edit_stock_opname(
            stock_opname_id=stock_opname_id,
            final_stock = final_stock
        )

        if stock_opname_result:
            POSMessageBox.info(self, title='Success', message="Stock opname updated successfully")
            self.clear_stock_opname_data()
            self.close()

        else:
            POSMessageBox.error(self, title='Error', message="Failed to update stock opname")


    # Setters
    # ============
    def set_stock_opname(self, stock_opname_id: str, stock_opname_data: EditStockOpnameModel):
        self.ui.stock_opname_id_input.setText(stock_opname_id)
        self.ui.sku_stock_opname_input.setText(stock_opname_data.sku)
        self.ui.product_name_stock_opname_input.setText(stock_opname_data.product_name)
        self.ui.price_stock_opname_input.setText(stock_opname_data.price)
        self.ui.original_stock_stock_opname_input.setText(stock_opname_data.original_stock)
        self.ui.final_stock_stock_opname_input.setText(stock_opname_data.final_stock)


    # Clears
    # ============
    def clear_stock_opname_data(self):
        self.ui.stock_opname_id_input.clear()
        self.ui.sku_stock_opname_input.clear()
        self.ui.product_name_stock_opname_input.clear()
        self.ui.price_stock_opname_input.clear()
        self.ui.original_stock_stock_opname_input.clear()
        self.ui.final_stock_stock_opname_input.clear()
