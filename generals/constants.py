from PyQt6.QtWidgets import QHeaderView, QAbstractItemView, QTableWidget
from PyQt6.QtWidgets import QDateEdit


RESIZE_TO_CONTENTS = QHeaderView.ResizeMode.ResizeToContents
RESIZE_MODE_INTERACTIVE = QHeaderView.ResizeMode.Interactive
RESIZE_MODE_FIXED = QHeaderView.ResizeMode.Fixed
SELECT_ROWS = QAbstractItemView.SelectionBehavior.SelectRows
SINGLE_SELECTION = QAbstractItemView.SelectionMode.SingleSelection
NO_EDIT_TRIGGERS = QTableWidget.EditTrigger.NoEditTriggers
DATE_EDIT_NO_BUTTONS = QDateEdit.ButtonSymbols.NoButtons

# Backoffice and Cashier
BACKOFFICE_ID = 1
CASHIER_ID = 2

DATE_FORMAT_DDMMYYYY = "dd/MM/yyyy"
TAX_TABLE_KEY = '= TAX ='

# Permissions
PERM_C_PRODUCTS = 'create_products'
PERM_R_PRODUCTS = 'read_products'
PERM_U_PRODUCTS = 'update_products'
PERM_D_PRODUCTS = 'delete_products'
PERM_I_PRODUCTS = 'import_products'
PERM_E_PRODUCTS = 'export_products'

PERM_C_CATEGORIES = 'create_categories'
PERM_R_CATEGORIES = 'read_categories'
PERM_U_CATEGORIES = 'update_categories'
PERM_D_CATEGORIES = 'delete_categories'

PERM_C_SUPPLIERS = 'create_suppliers'
PERM_R_SUPPLIERS = 'read_suppliers'
PERM_U_SUPPLIERS = 'update_suppliers'
PERM_D_SUPPLIERS = 'delete_suppliers'

PERM_C_TRANSACTIONS = 'create_transactions'
PERM_R_TRANSACTIONS = 'read_transactions'
PERM_U_TRANSACTIONS = 'update_transactions'
PERM_D_TRANSACTIONS = 'delete_transactions'

PERM_C_PENDING_TRANSACTIONS = 'create_pending_transactions'
PERM_R_PENDING_TRANSACTIONS = 'read_pending_transactions'
PERM_A_PENDING_TRANSACTIONS = 'apply_pending_transactions'

PERM_C_PURCHASING = 'create_purchasing'
PERM_R_PURCHASING = 'read_purchasing'
PERM_U_PURCHASING = 'update_purchasing'
PERM_D_PURCHASING = 'delete_purchasing'

PERM_C_CUSTOMERS = 'create_customers'
PERM_R_CUSTOMERS = 'read_customers'
PERM_U_CUSTOMERS = 'update_customers'
PERM_D_CUSTOMERS = 'delete_customers'

PERM_C_USERS = 'create_users'
PERM_R_USERS = 'read_users'
PERM_U_USERS = 'update_users'
PERM_D_USERS = 'delete_users'

PERM_C_ROLES = 'create_roles'
PERM_R_ROLES = 'read_roles'
PERM_U_ROLES = 'update_roles'
PERM_D_ROLES = 'delete_roles'

PERM_C_PERMISSIONS = 'create_permissions'
PERM_R_PERMISSIONS = 'read_permissions'
PERM_U_PERMISSIONS = 'update_permissions'
PERM_D_PERMISSIONS = 'delete_permissions'

PERM_C_LOGS = 'create_logs'
PERM_R_LOGS = 'read_logs'
PERM_U_LOGS = 'update_logs'
PERM_D_LOGS = 'delete_logs'

PERM_R_STOCK_CARD = 'read_stock_card'

PERM_C_STOCK_OPNAME = 'create_stock_opname'
PERM_R_STOCK_OPNAME = 'read_stock_opname'
PERM_U_STOCK_OPNAME = 'update_stock_opname'
PERM_D_STOCK_OPNAME = 'delete_stock_opname'
PERM_E_STOCK_OPNAME = 'export_stock_opname'

PERM_R_BACK_OFFICE_SALES_REPORT = 'read_back_office_sales_report'
PERM_R_CASHIER_SALES_REPORT = 'read_cashier_sales_report'
PERM_R_PROFIT_AND_LOSS_REPORT = 'read_profit_and_loss_report'
PERM_R_SALES_PER_ITEM_REPORT = 'read_sales_per_item_report'
PERM_R_MONTHLY_SALES_REPORT = 'read_monthly_sales_report'
PERM_R_DAILY_SALES_REPORT = 'read_daily_sales_report'

PERM_C_PURCHASE_RETURN = 'create_purchase_return'
PERM_R_PURCHASE_RETURN = 'read_purchase_return'
PERM_U_PURCHASE_RETURN = 'update_purchase_return'
PERM_D_PURCHASE_RETURN = 'delete_purchase_return'

PERM_C_SALES_RETURN = 'create_sales_return'
PERM_R_SALES_RETURN = 'read_sales_return'
PERM_U_SALES_RETURN = 'update_sales_return'
PERM_D_SALES_RETURN = 'delete_sales_return'

PERM_B_DATABASE = 'backup_database'
PERM_R_DATABASE = 'restore_database'
