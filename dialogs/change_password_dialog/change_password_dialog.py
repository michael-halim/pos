from PyQt6 import QtWidgets, QtCore, uic

from dialogs.change_password_dialog.translations import CHANGE_PASSWORD_DIALOG_TRANSLATIONS

from generals.message_box import POSMessageBox
from generals.build import resource_path
from generals.constants import PERM_C_TRANSACTIONS
from generals.messages import ERR_PERM_C_TRANSACTIONS, PERM_DENIED
from generals.language_manager import LanguageManager
from generals.permission_manager import PermissionManager

class ChangePasswordDialogWindow(QtWidgets.QWidget):
    password_changed = QtCore.pyqtSignal(dict)
    def __init__(self):
        super().__init__()

        self.permission_manager = PermissionManager()
        if not self.permission_manager.has_permission(PERM_C_TRANSACTIONS):
            return
        

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/change_password_dialog.ui'), self)

        # Connect the buttons
        self.ui.close_change_password_button.clicked.connect(lambda: self.close())
        self.ui.submit_change_password_button.clicked.connect(self.change_password)

        # Init Language Manager
        self.language_manager = LanguageManager()
        self.language_manager.add_translations(CHANGE_PASSWORD_DIALOG_TRANSLATIONS)


    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)
        if not self.permission_manager.has_permission(PERM_C_TRANSACTIONS):
            POSMessageBox.error(self, title=PERM_DENIED, message=ERR_PERM_C_TRANSACTIONS)
            self.close()
            return


        # Set window title
        if self.permission_manager.get_username().lower() not in self.windowTitle().lower():
            self.setWindowTitle(self.windowTitle() + ' - ' + self.permission_manager.get_username())

        # Translate Widget Text
        self.language_manager.translate_widget_text(self)


    def show(self):
        """Override show to ensure data is refreshed"""
        super().show()
        if not self.permission_manager.has_permission(PERM_C_TRANSACTIONS):
            self.close()
            return


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()
        if not self.permission_manager.has_permission(PERM_C_TRANSACTIONS):
            self.close()
            return


    def change_password(self):
        old_password = self.ui.old_password_input.text().strip()
        new_password = self.ui.new_password_input.text().strip()

        if new_password == old_password:
            POSMessageBox.warning(self, 'New Password and Old Password cannot be the same')
            return

        self.password_changed.emit({'old_password': old_password, 'new_password': new_password})
        self.close()

