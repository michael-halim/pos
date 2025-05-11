from PyQt6 import QtWidgets
import sys
from login.login import LoginWindow

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
