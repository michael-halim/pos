from PyQt6 import QtWidgets, QtCore, uic

from generals.message_box import POSMessageBox
from generals.build import resource_path


class ChangePasswordDialogWindow(QtWidgets.QWidget):
    password_changed = QtCore.pyqtSignal(dict)
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/change_password_dialog.ui'), self)

        # Connect the buttons
        self.ui.close_change_password_button.clicked.connect(lambda: self.close())
        self.ui.submit_change_password_button.clicked.connect(self.change_password)


    def showEvent(self, event):
        """Override showEvent to refresh data when window is shown"""
        super().showEvent(event)


    def show(self):
        """Override show to ensure data is refreshed"""
        super().show()


    def showMaximized(self):
        """Override showMaximized to ensure data is refreshed"""
        super().showMaximized()


    def change_password(self):
        old_password = self.ui.old_password_input.text().strip()
        new_password = self.ui.new_password_input.text().strip()

        if new_password == old_password:
            POSMessageBox.warning(self, 'New Password and Old Password cannot be the same')
            return

        self.password_changed.emit({'old_password': old_password, 'new_password': new_password})
        self.close()

