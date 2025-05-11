from PyQt6.QtWidgets import QMessageBox

from generals.messages import (
    OK, ERR, WARNING, CONFIRM
)

class POSMessageBox:
    @staticmethod
    def info(parent, message: str, title: str = OK):
        QMessageBox.information(parent, title, message)

    @staticmethod
    def error(parent, message: str, title: str = ERR):
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def warning(parent, message: str, title: str = WARNING):
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def confirm(parent, message: str, title: str = CONFIRM) -> bool:
        reply = QMessageBox.question(
            parent, 
            title, 
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes