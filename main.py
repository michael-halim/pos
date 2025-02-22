import os
import sys
from PyQt6 import QtWidgets, uic, QtGui, QtCore

from products import ProductsWindow
from categories import CategoriesWindow
from suppliers import SuppliersWindow
from transactions.transactions import TransactionsWindow
from transactions_list.transactions_list import TransactionsListWindow
from purchasing.purchasing import PurchasingWindow
from purchasing_list.purchasing_list import PurchasingListWindow
from dialogs.roles_dialog.roles_dialog import RolesDialogWindow
from role_permissions.role_permissions import RolePermissionsWindow
from customers.customers import CustomersWindow
from logs.logs import LogsWindow

from generals.build import resource_path
from connect_db import DatabaseConnection

class POS(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Use resource_path for UI files
        ui_file = resource_path('ui/main.ui')
        self.ui = uic.loadUi(ui_file, self)

        self.products_dialog = ProductsWindow()
        self.categories_dialog = CategoriesWindow()
        self.suppliers_dialog = SuppliersWindow()
        self.transactions_dialog = TransactionsWindow()
        self.transactions_list_dialog = TransactionsListWindow()
        self.purchasing_dialog = PurchasingWindow()
        self.purchasing_list_dialog = PurchasingListWindow()
        self.roles_dialog = RolesDialogWindow()
        self.role_permissions_dialog = RolePermissionsWindow()
        self.customers_dialog = CustomersWindow()
        self.logs_dialog = LogsWindow()

        # Use resource_path for database
        self.db_path = resource_path('database/pos.db')
        
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
        self.ui.purchasing_list_button.clicked.connect(lambda: self.purchasing_list_dialog.showMaximized())
        self.ui.roles_button.clicked.connect(lambda: self.roles_dialog.showMaximized())
        self.ui.role_permissions_button.clicked.connect(lambda: self.role_permissions_dialog.showMaximized())
        self.ui.customers_button.clicked.connect(lambda: self.customers_dialog.showMaximized())
        self.ui.logs_button.clicked.connect(lambda: self.logs_dialog.showMaximized())
        
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