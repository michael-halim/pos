from connect_db import DatabaseConnection
from PyQt6 import QtWidgets, uic

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
from reports.sales_per_item_report.sales_per_item_report import SalesPerItemReportWindow
from reports.back_office_sales_report.back_office_sales_report import BackOfficeSalesReportWindow
from reports.cashier_sales_report.cashier_sales_report import CashierSalesReportWindow
from reports.profit_and_loss_report.profit_and_loss_report import ProfitAndLossReportWindow

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
        self._suppliers_dialog = None
        self._transactions_dialog = None
        self._transactions_list_dialog = None
        self._purchasing_dialog = None
        self._purchasing_list_dialog = None
        self._role_permissions_dialog = None
        self._customers_dialog = None
        self._logs_dialog = None
        self._users_dialog_window = None
        self._stock_card_list_window = None
        self._stock_opname_window = None
        self._backup_restore_database = None
        self._sales_per_item_report_window = None
        self._back_office_sales_report_window = None
        self._cashier_sales_report_window = None
        self._profit_and_loss_report_window = None

        # Connect Button to Stacked Widget
        self.ui.master_data_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.master_data_page))
        self.ui.settings_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.settings_page))
        self.ui.transaction_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.transaction_page))
        self.ui.report_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.report_page))
        self.ui.log_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.log_page))
        self.ui.backup_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.backup_page))
        
        # Connect Button to Dialog in Master Data Menu - using property getters
        self.ui.products_button.clicked.connect(lambda: self.products_dialog.show())
        self.ui.categories_button.clicked.connect(lambda: self.categories_dialog.show())
        self.ui.suppliers_button.clicked.connect(lambda: self.suppliers_dialog.show())
        self.ui.transactions_button.clicked.connect(lambda: self.transactions_dialog.showMaximized())
        self.ui.transactions_list_button.clicked.connect(lambda: self.transactions_list_dialog.showMaximized())
        self.ui.purchasing_button.clicked.connect(lambda: self.purchasing_dialog.showMaximized())
        self.ui.purchasing_list_button.clicked.connect(lambda: self.purchasing_list_dialog.showMaximized())
        self.ui.role_permissions_button.clicked.connect(lambda: self.role_permissions_dialog.show())
        self.ui.customers_button.clicked.connect(lambda: self.customers_dialog.show())
        self.ui.logs_button.clicked.connect(lambda: self.logs_dialog.show())
        self.ui.users_dialog_button.clicked.connect(lambda: self.users_dialog_window.show())
        self.ui.stock_card_list_button.clicked.connect(lambda: self.stock_card_list_window.showMaximized())
        self.ui.stock_opname_button.clicked.connect(lambda: self.stock_opname_window.show())
        c = SalesPerItemReportWindow()
        self.ui.sales_per_item_report_button.clicked.connect(lambda: c.showMaximized())

        a = BackOfficeSalesReportWindow()
        b = CashierSalesReportWindow()
        self.ui.back_office_sales_report_button.clicked.connect(lambda: a.showMaximized())
        self.ui.cashier_sales_report_button.clicked.connect(lambda: b.showMaximized())
        self.ui.profit_and_loss_report_button.clicked.connect(lambda: self.profit_and_loss_report_window.showMaximized())
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


    @property
    def sales_per_item_report_window(self):
        if self._sales_per_item_report_window is None:
            self._sales_per_item_report_window = SalesPerItemReportWindow()
        return self._sales_per_item_report_window


    @property
    def back_office_sales_report_window(self):
        if self._back_office_sales_report_window is None:
            self._back_office_sales_report_window = BackOfficeSalesReportWindow()
        return self._back_office_sales_report_window
    

    @property
    def cashier_sales_report_window(self):
        if self._cashier_sales_report_window is None:
            self._cashier_sales_report_window = CashierSalesReportWindow()
        return self._cashier_sales_report_window
    

    @property
    def profit_and_loss_report_window(self):
        if self._profit_and_loss_report_window is None:
            self._profit_and_loss_report_window = ProfitAndLossReportWindow()
        return self._profit_and_loss_report_window
    
    

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
