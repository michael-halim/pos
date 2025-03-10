from PyQt6 import QtWidgets, uic

from home.home import HomeWindow
from login.services.login_services import LoginService

from generals.message_box import POSMessageBox
from generals.build import resource_path

class LoginWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/login.ui'), self)

        # Init Services
        self.login_service = LoginService()

        # Connect Button to Stacked Widget
        self.ui.submit_login_button.clicked.connect(self.login)

        # Handle Enter Key
        self.ui.username_input.returnPressed.connect(lambda: self.ui.password_input.setFocus())
        self.ui.password_input.returnPressed.connect(self.login)


    def login(self):
        username = self.ui.username_input.text()
        password = self.ui.password_input.text()

        response = self.login_service.login(username, password)

        if response.success:
            self.home_window = HomeWindow()
            self.home_window.showMaximized()
            self.close()

        else:
            POSMessageBox.warning(self, title="Login Failed", message=response.message)