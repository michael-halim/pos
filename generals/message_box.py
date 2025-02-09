from PyQt6.QtWidgets import QMessageBox

class POSMessageBox:
    @staticmethod
    def info(parent, message: str, title: str = "Success"):
        QMessageBox.information(parent, title, message)

    @staticmethod
    def error(parent, message: str, title: str = "Error"):
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def warning(parent, message: str, title: str = "Warning"):
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def confirm(parent, message: str, title: str = "Confirm") -> bool:
        reply = QMessageBox.question(
            parent, 
            title, 
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes