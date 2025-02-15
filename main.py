import sys
from PyQt6 import QtWidgets, uic, QtGui, QtCore

from products import ProductsWindow
from categories import CategoriesWindow
from suppliers import SuppliersWindow
from transactions.transactions import TransactionsWindow
from transactions_list.transactions_list import TransactionsListWindow
from purchasing.purchasing import PurchasingWindow

from connect_db import DatabaseConnection
class POS(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        # Load the main ui file
        self.ui = uic.loadUi("./ui/main.ui", self)

        self.products_dialog = ProductsWindow()
        self.categories_dialog = CategoriesWindow()
        self.suppliers_dialog = SuppliersWindow()
        self.transactions_dialog = TransactionsWindow()
        self.transactions_list_dialog = TransactionsListWindow()
        self.purchasing_dialog = PurchasingWindow()

        # Connect Button to Stacked Widget
        self.ui.master_data_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.master_data_page))
        self.ui.settings_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.settings_page))
        self.ui.transaction_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.transaction_page))
        self.ui.report_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.report_page))
        self.ui.log_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.log_page))
        self.ui.import_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.import_page))
        self.ui.export_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.export_page))
        self.ui.backup_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.backup_page))
        
        # Connect Button to Dialog in Master Data Menu
        self.ui.products_button.clicked.connect(lambda: self.products_dialog.showMaximized())
        self.ui.categories_button.clicked.connect(lambda: self.categories_dialog.showMaximized())
        self.ui.suppliers_button.clicked.connect(lambda: self.suppliers_dialog.showMaximized())
        self.ui.transactions_button.clicked.connect(lambda: self.transactions_dialog.showMaximized())
        self.ui.transactions_list_button.clicked.connect(lambda: self.transactions_list_dialog.showMaximized())
        self.ui.purchasing_button.clicked.connect(lambda: self.purchasing_dialog.showMaximized())

        # TODO: Add an input for user to input suppliers in their products
        # TODO: Change the UI button, or layout to form layout to make it beautiful

        
    def closeEvent(self, event):

        # Close database connection
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()

        self.cursor.close()
        self.db.close()

        # Close all child windows
        for window in QtWidgets.QApplication.topLevelWidgets():
            window.close()

        event.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = POS()
    window.showMaximized()
    sys.exit(app.exec())