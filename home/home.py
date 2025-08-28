from connect_db import DatabaseConnection
from PyQt6 import QtWidgets, uic, QtCore

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
from stock_opname_list.stock_opname_list import StockOpnameListWindow
from reports.sales_per_item_report.sales_per_item_report import SalesPerItemReportWindow
from reports.back_office_sales_report.back_office_sales_report import BackOfficeSalesReportWindow
from reports.cashier_sales_report.cashier_sales_report import CashierSalesReportWindow
from reports.profit_and_loss_report.profit_and_loss_report import ProfitAndLossReportWindow
from reports.daily_sales_report.daily_sales_report import DailySalesReportWindow
from reports.monthly_sales_report.monthly_sales_report import MonthlySalesReportWindow
from backup_restore_database.backup_database import BackupRestoreDatabase
from purchase_return.purchase_return import PurchaseReturnWindow
from purchase_return_list.purchase_return_list import PurchaseReturnListWindow
from sales_return.sales_return import SalesReturnWindow
from sales_return_list.sales_return_list import SalesReturnListWindow

from generals.build import resource_path
from generals.permission_manager import PermissionManager
from generals.language_manager import LanguageManager


class HomeWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Use resource_path for UI files
        ui_file = resource_path('ui/main.ui')
        self.ui = uic.loadUi(ui_file, self)

        # Hide the close button from the title bar
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowType.WindowCloseButtonHint)

        # Flag to allow programmatic closing
        self._allow_close = False

        self.permission_manager = PermissionManager()

        # Set window title
        self.setWindowTitle(self.windowTitle() + ' - ' + self.permission_manager.get_username().title())

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
        self._stock_opname_list_window = None
        self._backup_restore_database = None
        self._sales_per_item_report_window = None
        self._back_office_sales_report_window = None
        self._cashier_sales_report_window = None
        self._daily_sales_report_window = None
        self._monthly_sales_report_window = None
        self._profit_and_loss_report_window = None
        self._purchase_return_window = None
        self._purchase_return_list_window = None
        self._sales_return_window = None
        self._sales_return_list_window = None

        self.language_manager = LanguageManager()
        self.ui.language_combobox.currentTextChanged.connect(self.on_language_combobox_changed)


        # Connect Button to Stacked Widget
        self.ui.master_data_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.master_data_page))
        self.ui.settings_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.settings_page))
        self.ui.transaction_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.transaction_page))
        self.ui.report_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.report_page))
        self.ui.log_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.log_page))
        self.ui.backup_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.backup_page))
        
        # Connect Button to Dialog in Master Data Menu - using property getters
        # Master Data Menu
        self.ui.products_button.clicked.connect(lambda: self.products_dialog.showMaximized())
        self.ui.categories_button.clicked.connect(lambda: self.categories_dialog.showMaximized())
        self.ui.suppliers_button.clicked.connect(lambda: self.suppliers_dialog.showMaximized())
        self.ui.customers_button.clicked.connect(lambda: self.customers_dialog.showMaximized())

        # Transaction Menu
        self.ui.transactions_button.clicked.connect(lambda: self.transactions_dialog.showMaximized())
        self.ui.transactions_list_button.clicked.connect(lambda: self.transactions_list_dialog.showMaximized())
        self.ui.purchasing_button.clicked.connect(lambda: self.purchasing_dialog.showMaximized())
        self.ui.purchasing_list_button.clicked.connect(lambda: self.purchasing_list_dialog.showMaximized())
        self.ui.stock_card_list_button.clicked.connect(lambda: self.stock_card_list_window.showMaximized())
        self.ui.stock_opname_button.clicked.connect(lambda: self.stock_opname_list_window.showMaximized())

        # Settings Menu
        self.ui.role_permissions_button.clicked.connect(lambda: self.role_permissions_dialog.showMaximized())
        self.ui.users_dialog_button.clicked.connect(lambda: self.users_dialog_window.showMaximized())

        # Report Menu
        self.ui.sales_per_item_report_button.clicked.connect(lambda: self.sales_per_item_report_window.showMaximized())
        self.ui.back_office_sales_report_button.clicked.connect(lambda: self.back_office_sales_report_window.showMaximized())
        self.ui.cashier_sales_report_button.clicked.connect(lambda: self.cashier_sales_report_window.showMaximized())
        self.ui.profit_and_loss_report_button.clicked.connect(lambda: self.profit_and_loss_report_window.showMaximized())
        self.ui.daily_sales_report_button.clicked.connect(lambda: self.daily_sales_report_window.showMaximized())
        self.ui.monthly_sales_report_button.clicked.connect(lambda: self.monthly_sales_report_window.showMaximized())

        # Logs Menu
        self.ui.logs_button.clicked.connect(lambda: self.logs_dialog.showMaximized())

        # Purchase Return Menu
        self.ui.purchase_return_button.clicked.connect(lambda: self.purchase_return_window.showMaximized())
        self.ui.purchase_return_list_button.clicked.connect(lambda: self.purchase_return_list_window.showMaximized())

        self.ui.sales_return_button.clicked.connect(lambda: self.sales_return_window.showMaximized())
        self.ui.sales_return_list_button.clicked.connect(lambda: self.sales_return_list_window.showMaximized())

        # Database Menu   
        self.ui.backup_database_button.clicked.connect(lambda: self.backup_restore_database.export_database())  
        self.ui.restore_database_button.clicked.connect(lambda: self.backup_restore_database.import_database())

        self.ui.logout_button.clicked.connect(self.logout)

    
    # Property getters for lazy initialization
    @property
    def products_dialog(self):
        if self._products_dialog is None or not self._products_dialog.isVisible():
            self._products_dialog = ProductsWindow(home_window=self)
            self._products_dialog.showMaximized()
            self.close_programmatically()

        else:
            self._products_dialog.raise_()
            self._products_dialog.activateWindow()
            self._products_dialog.show()

        return self._products_dialog
    

    @property
    def categories_dialog(self):
        if self._categories_dialog is None or not self._categories_dialog.isVisible():
            self._categories_dialog = CategoriesWindow(home_window=self)
            self._categories_dialog.showMaximized()
            self.close_programmatically()

        else:
            self._categories_dialog.raise_()
            self._categories_dialog.activateWindow()
            self._categories_dialog.show()

        return self._categories_dialog
    

    @property
    def suppliers_dialog(self):
        if self._suppliers_dialog is None or not self._suppliers_dialog.isVisible():
            self._suppliers_dialog = SuppliersWindow(home_window=self)
            self._suppliers_dialog.showMaximized()
            self.close_programmatically()

        else:
            self._suppliers_dialog.raise_()
            self._suppliers_dialog.activateWindow()
            self._suppliers_dialog.show()

        return self._suppliers_dialog
    

    @property
    def transactions_dialog(self):
        if self._transactions_dialog is None or not self._transactions_dialog.isVisible():
            self._transactions_dialog = TransactionsWindow(home_window=self)
            self._transactions_dialog.showMaximized()
            self.close_programmatically()

        else:
            self._transactions_dialog.raise_()
            self._transactions_dialog.activateWindow()
            self._transactions_dialog.show()

        return self._transactions_dialog
    

    @property
    def transactions_list_dialog(self):
        if self._transactions_list_dialog is None or not self._transactions_list_dialog.isVisible() :
            self._transactions_list_dialog = TransactionsListWindow(home_window=self)
            self._transactions_list_dialog.showMaximized()
            self.close_programmatically()

        else:
            self._transactions_list_dialog.raise_()
            self._transactions_list_dialog.activateWindow()
            self._transactions_list_dialog.show()

        return self._transactions_list_dialog
    

    @property
    def purchasing_dialog(self):
        if self._purchasing_dialog is None or not self._purchasing_dialog.isVisible():
            self._purchasing_dialog = PurchasingWindow(home_window=self)
            self._purchasing_dialog.showMaximized()
            self.close_programmatically()

        else:
            self._purchasing_dialog.raise_()
            self._purchasing_dialog.activateWindow()
            self._purchasing_dialog.show()

        return self._purchasing_dialog
    

    @property
    def purchasing_list_dialog(self):
        if self._purchasing_list_dialog is None or not self._purchasing_list_dialog.isVisible():
            self._purchasing_list_dialog = PurchasingListWindow(home_window=self)
            self._purchasing_list_dialog.showMaximized()
            self.close_programmatically()

        else:
            self._purchasing_list_dialog.raise_()
            self._purchasing_list_dialog.activateWindow()
            self._purchasing_list_dialog.show()

        return self._purchasing_list_dialog


    @property
    def role_permissions_dialog(self):
        if self._role_permissions_dialog is None or not self._role_permissions_dialog.isVisible():
            self._role_permissions_dialog = RolePermissionsWindow(home_window=self)
            self._role_permissions_dialog.showMaximized()
            self.close_programmatically()

        else:
            self._role_permissions_dialog.raise_()
            self._role_permissions_dialog.activateWindow()
            self._role_permissions_dialog.show()

        return self._role_permissions_dialog


    @property
    def customers_dialog(self):
        if self._customers_dialog is None or not self._customers_dialog.isVisible():
            self._customers_dialog = CustomersWindow(home_window=self)
            self._customers_dialog.showMaximized()
            self.close_programmatically()

        else:
            self._customers_dialog.raise_()
            self._customers_dialog.activateWindow()
            self._customers_dialog.show()

        return self._customers_dialog
    

    @property
    def logs_dialog(self):
        if self._logs_dialog is None or not self._logs_dialog.isVisible():
            self._logs_dialog = LogsWindow(home_window=self)
            self._logs_dialog.showMaximized()
            self.close_programmatically()

        else:
            self._logs_dialog.raise_()
            self._logs_dialog.activateWindow()
            self._logs_dialog.show()

        return self._logs_dialog
    

    @property
    def users_dialog_window(self):
        if self._users_dialog_window is None or not self._users_dialog_window.isVisible():
            self._users_dialog_window = UsersWindow(home_window=self)
            self._users_dialog_window.showMaximized()
            self.close_programmatically()

        else:
            self._users_dialog_window.raise_()
            self._users_dialog_window.activateWindow()
            self._users_dialog_window.show()

        return self._users_dialog_window


    @property
    def stock_card_list_window(self):
        if self._stock_card_list_window is None or not self._stock_card_list_window.isVisible():
            self._stock_card_list_window = StockCardListWindow(home_window=self)
            self._stock_card_list_window.showMaximized()
            self.close_programmatically()

        else:
            self._stock_card_list_window.raise_()
            self._stock_card_list_window.activateWindow()
            self._stock_card_list_window.show()

        return self._stock_card_list_window
        

    @property
    def stock_opname_list_window(self):
        if self._stock_opname_list_window is None or not self._stock_opname_list_window.isVisible():
            self._stock_opname_list_window = StockOpnameListWindow(home_window=self)
            self._stock_opname_list_window.showMaximized()
            self.close_programmatically()

        else:
            self._stock_opname_list_window.raise_()
            self._stock_opname_list_window.activateWindow()
            self._stock_opname_list_window.show()

        return self._stock_opname_list_window


    @property
    def backup_restore_database(self):
        if self._backup_restore_database is None or not self._backup_restore_database.isVisible():
            self._backup_restore_database = BackupRestoreDatabase()

        return self._backup_restore_database


    @property
    def sales_per_item_report_window(self):
        if self._sales_per_item_report_window is None or not self._sales_per_item_report_window.isVisible():
            self._sales_per_item_report_window = SalesPerItemReportWindow(home_window=self)
            self._sales_per_item_report_window.showMaximized()
            self.close_programmatically()

        else:
            self._sales_per_item_report_window.raise_()
            self._sales_per_item_report_window.activateWindow()
            self._sales_per_item_report_window.show()

        return self._sales_per_item_report_window


    @property
    def back_office_sales_report_window(self):
        if self._back_office_sales_report_window is None or not self._back_office_sales_report_window.isVisible():
            self._back_office_sales_report_window = BackOfficeSalesReportWindow(home_window=self)
            self._back_office_sales_report_window.showMaximized()
            self.close_programmatically()

        else:
            self._back_office_sales_report_window.raise_()
            self._back_office_sales_report_window.activateWindow()
            self._back_office_sales_report_window.show()

        return self._back_office_sales_report_window
    

    @property
    def cashier_sales_report_window(self):
        if self._cashier_sales_report_window is None or not self._cashier_sales_report_window.isVisible():
            self._cashier_sales_report_window = CashierSalesReportWindow(home_window=self)
            self._cashier_sales_report_window.showMaximized()
            self.close_programmatically()

        else:
            self._cashier_sales_report_window.raise_()
            self._cashier_sales_report_window.activateWindow()
            self._cashier_sales_report_window.show()


        return self._cashier_sales_report_window


    @property
    def profit_and_loss_report_window(self):
        if self._profit_and_loss_report_window is None or not self._profit_and_loss_report_window.isVisible():
            self._profit_and_loss_report_window = ProfitAndLossReportWindow(home_window=self)
            self._profit_and_loss_report_window.showMaximized()
            self.close_programmatically()

        else:
            self._profit_and_loss_report_window.raise_()
            self._profit_and_loss_report_window.activateWindow()
            self._profit_and_loss_report_window.show()

        return self._profit_and_loss_report_window
    

    @property
    def daily_sales_report_window(self):
        if self._daily_sales_report_window is None or not self._daily_sales_report_window.isVisible():
            self._daily_sales_report_window = DailySalesReportWindow(home_window=self)
            self._daily_sales_report_window.showMaximized()
            self.close_programmatically()

        else:
            self._daily_sales_report_window.raise_()
            self._daily_sales_report_window.activateWindow()
            self._daily_sales_report_window.show()

        return self._daily_sales_report_window


    @property
    def monthly_sales_report_window(self):
        if self._monthly_sales_report_window is None or not self._monthly_sales_report_window.isVisible():
            self._monthly_sales_report_window = MonthlySalesReportWindow(home_window=self)
            self._monthly_sales_report_window.showMaximized()
            self.close_programmatically()

        else:
            self._monthly_sales_report_window.raise_()
            self._monthly_sales_report_window.activateWindow()
            self._monthly_sales_report_window.show()


        return self._monthly_sales_report_window


    @property
    def purchase_return_window(self):
        if self._purchase_return_window is None or not self._purchase_return_window.isVisible():
            self._purchase_return_window = PurchaseReturnWindow(home_window=self)
            self._purchase_return_window.showMaximized()
            self.close_programmatically()

        else:
            self._purchase_return_window.raise_()
            self._purchase_return_window.activateWindow()
            self._purchase_return_window.show()

        return self._purchase_return_window

    
    @property
    def purchase_return_list_window(self):
        if self._purchase_return_list_window is None or not self._purchase_return_list_window.isVisible():
            self._purchase_return_list_window = PurchaseReturnListWindow(home_window=self)
            self._purchase_return_list_window.showMaximized()
            self.close_programmatically()

        else:
            self._purchase_return_list_window.raise_()
            self._purchase_return_list_window.activateWindow()
            self._purchase_return_list_window.show()

        return self._purchase_return_list_window
    

    @property
    def sales_return_window(self):
        if self._sales_return_window is None or not self._sales_return_window.isVisible():
            self._sales_return_window = SalesReturnWindow(home_window=self)
            self._sales_return_window.showMaximized()
            self.close_programmatically()

        else:
            self._sales_return_window.raise_()
            self._sales_return_window.activateWindow()
            self._sales_return_window.show()

        return self._sales_return_window


    @property
    def sales_return_list_window(self):
        if self._sales_return_list_window is None or not self._sales_return_list_window.isVisible():
            self._sales_return_list_window = SalesReturnListWindow(home_window=self)
            self._sales_return_list_window.showMaximized()
            self.close_programmatically()

        else:
            self._sales_return_list_window.raise_()
            self._sales_return_list_window.activateWindow()
            self._sales_return_list_window.show()

        return self._sales_return_list_window


    def on_language_combobox_changed(self, text):
        if text == 'Indonesia':
            self.language_manager.set_language('id')
        elif text == 'English':
            self.language_manager.set_language('en')
            
        self.language_manager.translate_widget_text(self)


    def logout(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()

        self.cursor.close()
        self.db.close()

        # Close all child windows
        for window in QtWidgets.QApplication.topLevelWidgets():
            window.close()

        self.close()


    def close_programmatically(self):
        """Method to allow programmatic closing from other parts of the code"""
        self._allow_close = True
        self.close()


    def closeEvent(self, event):
        """Override closeEvent to allow programmatic closing but prevent UI closing"""
        if self._allow_close:
            event.accept()
        else:
            # Prevent UI-initiated closing (Alt+Tab, taskbar, etc.)
            event.ignore()