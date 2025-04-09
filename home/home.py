from connect_db import DatabaseConnection
from PyQt6 import QtWidgets, uic

from dialogs.roles_dialog.roles_dialog import RolesDialogWindow
from dialogs.categories_dialog.categories_dialog import CategoriesDialogWindow
from dialogs.customers_dialog.customers_dialog import CustomersDialogWindow

from products.products import ProductsWindow
from categories.categories import CategoriesWindow
from suppliers.suppliers import SuppliersWindow
from transactions.transactions import TransactionsWindow
from transactions_list.transactions_list import TransactionsListWindow
from purchasing.purchasing import PurchasingWindow
from purchasing_list.purchasing_list import PurchasingListWindow
from role_permissions.role_permissions import RolePermissionsWindow
from customers.customers import CustomersWindow
from logs.logs import LogsWindow
from users.users import UsersWindow
from stock_card_list.stock_card_list import StockCardListWindow
from stock_opname.stock_opname import StockOpnameWindow

from backup_restore_database.backup_database import BackupRestoreDatabase
from generals.build import resource_path


class HomeWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Use resource_path for UI files
        ui_file = resource_path('ui/main.ui')
        self.ui = uic.loadUi(ui_file, self)

        # Give user permissions
        self.user_permissions = set()

        # Initialize dialog attributes to None - they'll be created only when needed
        self._products_dialog = None
        self._categories_dialog = None
        self._categories_dialog_show = None
        self._suppliers_dialog = None
        self._transactions_dialog = None
        self._transactions_list_dialog = None
        self._purchasing_dialog = None
        self._purchasing_list_dialog = None
        self._roles_dialog = None
        self._role_permissions_dialog = None
        self._customers_dialog = None
        self._logs_dialog = None
        self._customers_dialog_window = None
        self._users_dialog_window = None
        self._stock_card_list_window = None
        self._stock_opname_window = None
        self._backup_restore_database = None
        
        # Connect Button to Stacked Widget
        self.ui.master_data_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.master_data_page))
        self.ui.settings_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.settings_page))
        self.ui.transaction_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.transaction_page))
        self.ui.report_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.report_page))
        self.ui.log_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.log_page))
        self.ui.import_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.import_page))
        self.ui.export_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.export_page))
        self.ui.backup_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.backup_page))
        
        # Connect Button to Dialog in Master Data Menu - using property getters
        self.ui.products_button.clicked.connect(lambda: self.products_dialog.show())
        self.ui.categories_button.clicked.connect(lambda: self.categories_dialog.show())
        self.ui.suppliers_button.clicked.connect(lambda: self.suppliers_dialog.show())
        self.ui.transactions_button.clicked.connect(lambda: self.transactions_dialog.showMaximized())
        self.ui.transactions_list_button.clicked.connect(lambda: self.transactions_list_dialog.showMaximized())
        self.ui.purchasing_button.clicked.connect(lambda: self.purchasing_dialog.showMaximized())
        self.ui.purchasing_list_button.clicked.connect(lambda: self.purchasing_list_dialog.showMaximized())
        self.ui.roles_button.clicked.connect(lambda: self.roles_dialog.show())
        self.ui.role_permissions_button.clicked.connect(lambda: self.role_permissions_dialog.show())
        self.ui.customers_button.clicked.connect(lambda: self.customers_dialog.show())
        self.ui.logs_button.clicked.connect(lambda: self.logs_dialog.show())
        self.ui.customers_dialog_button.clicked.connect(lambda: self.customers_dialog_window.show())
        self.ui.categories_dialog_button.clicked.connect(lambda: self.categories_dialog_show.show())
        self.ui.users_dialog_button.clicked.connect(lambda: self.users_dialog_window.show())
        self.ui.stock_card_list_button.clicked.connect(lambda: self.stock_card_list_window.showMaximized())
        self.ui.stock_opname_button.clicked.connect(lambda: self.stock_opname_window.show())
        self.ui.backup_database_button.clicked.connect(lambda: self.backup_restore_database.export_database())  
        self.ui.restore_database_button.clicked.connect(lambda: self.backup_restore_database.import_database())

        self.ui.logout_button.clicked.connect(lambda: self.close())

    
    # Property getters for lazy initialization
    @property
    def products_dialog(self):
        if self._products_dialog is None:
            self._products_dialog = ProductsWindow()
        return self._products_dialog
    

    @property
    def categories_dialog(self):
        if self._categories_dialog is None:
            self._categories_dialog = CategoriesWindow()
        return self._categories_dialog
    

    @property
    def categories_dialog_show(self):
        if self._categories_dialog_show is None:
            self._categories_dialog_show = CategoriesDialogWindow()
        return self._categories_dialog_show
    

    @property
    def suppliers_dialog(self):
        if self._suppliers_dialog is None:
            self._suppliers_dialog = SuppliersWindow()
        return self._suppliers_dialog
    

    @property
    def transactions_dialog(self):
        if self._transactions_dialog is None:
            self._transactions_dialog = TransactionsWindow()
        return self._transactions_dialog
    

    @property
    def transactions_list_dialog(self):
        if self._transactions_list_dialog is None:
            self._transactions_list_dialog = TransactionsListWindow()
        return self._transactions_list_dialog
    

    @property
    def purchasing_dialog(self):
        if self._purchasing_dialog is None:
            self._purchasing_dialog = PurchasingWindow()
        return self._purchasing_dialog
    

    @property
    def purchasing_list_dialog(self):
        if self._purchasing_list_dialog is None:
            self._purchasing_list_dialog = PurchasingListWindow()
        return self._purchasing_list_dialog
    

    @property
    def roles_dialog(self):
        if self._roles_dialog is None:
            self._roles_dialog = RolesDialogWindow()
        return self._roles_dialog
    

    @property
    def role_permissions_dialog(self):
        if self._role_permissions_dialog is None:
            self._role_permissions_dialog = RolePermissionsWindow()
        return self._role_permissions_dialog
    

    @property
    def customers_dialog(self):
        if self._customers_dialog is None:
            self._customers_dialog = CustomersWindow()
        return self._customers_dialog
    

    @property
    def logs_dialog(self):
        if self._logs_dialog is None:
            self._logs_dialog = LogsWindow()
        return self._logs_dialog
    

    @property
    def customers_dialog_window(self):
        if self._customers_dialog_window is None:
            self._customers_dialog_window = CustomersDialogWindow()
        return self._customers_dialog_window


    @property
    def users_dialog_window(self):
        if self._users_dialog_window is None:
            self._users_dialog_window = UsersWindow()
        return self._users_dialog_window


    @property
    def stock_card_list_window(self):
        if self._stock_card_list_window is None:
            self._stock_card_list_window = StockCardListWindow()
        return self._stock_card_list_window


    @property
    def stock_opname_window(self):
        if self._stock_opname_window is None:
            self._stock_opname_window = StockOpnameWindow()
        return self._stock_opname_window


    @property
    def backup_restore_database(self):
        if self._backup_restore_database is None:
            self._backup_restore_database = BackupRestoreDatabase()
        return self._backup_restore_database


    def get_user_permissions(self) -> set:
        return self.user_permissions
    

    def set_user_permissions(self, permissions: set) -> None:
        self.user_permissions = permissions


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
