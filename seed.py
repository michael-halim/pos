from connect_db import DatabaseConnection
import hashlib
import random
import string

class SeedData:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()


    def create_stock_card_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS stock_card (
            sku VARCHAR(20) NOT NULL,
            date DATE NOT NULL,
            time TIME NOT NULL,
            transaction_id VARCHAR(20) NOT NULL,
            stock_in INT(10) NULL,
            stock_out INT(10) NULL,
            running_balance INT(10) NOT NULL
        );'''

        self.cursor.execute(sql)
        
        sql_insert = '''INSERT INTO stock_card (sku, date, time, transaction_id, stock_in, stock_out, running_balance)
                        VALUES 
                        ('SKU001', CURRENT_DATE, CURRENT_TIME, 'PO202502010001', 50, NULL, 50),
                        ('SKU001', CURRENT_DATE, CURRENT_TIME, 'J202502010002', NULL, 10, 40);'''

        self.cursor.execute(sql_insert)


    def create_roles_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS roles (
            role_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            role_name VARCHAR(20) NOT NULL UNIQUE,
            role_description TEXT DEFAULT ''
        );'''

        self.cursor.execute(sql)

        sql_insert = '''INSERT INTO roles (role_name, role_description) 
                        VALUES 
                        ('Admin', 'Administrator'),
                        ('Cashier', 'Cashier'),
                        ('Manager', 'Manager');'''

        self.cursor.execute(sql_insert)


    def create_permissions_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS permissions (
            permission_id VARCHAR(20) NOT NULL,
            permission_name VARCHAR(20) NOT NULL
        );'''

        self.cursor.execute(sql)

        sql_insert = '''INSERT INTO permissions (permission_id, permission_name) 
                        VALUES 
                        ('create_products', 'Create Products'), ('read_products', 'Read Products'), ('update_products', 'Update Products'), ('delete_products', 'Delete Products'), 
                        ('create_categories', 'Create Categories'), ('read_categories', 'Read Categories'), ('update_categories', 'Update Categories'), ('delete_categories', 'Delete Categories'),
                        ('create_suppliers', 'Create Suppliers'), ('read_suppliers', 'Read Suppliers'), ('update_suppliers', 'Update Suppliers'), ('delete_suppliers', 'Delete Suppliers'),
                        ('create_transactions', 'Create Transactions'), ('read_transactions', 'Read Transactions'), ('update_transactions', 'Update Transactions'), ('delete_transactions', 'Delete Transactions'),
                        ('create_purchasing', 'Create Purchasing'), ('read_purchasing', 'Read Purchasing'), ('update_purchasing', 'Update Purchasing'), ('delete_purchasing', 'Delete Purchasing'),
                        ('create_customers', 'Create Customers'), ('read_customers', 'Read Customers'), ('update_customers', 'Update Customers'), ('delete_customers', 'Delete Customers'),
                        ('create_users', 'Create Users'), ('read_users', 'Read Users'), ('update_users', 'Update Users'), ('delete_users', 'Delete Users'),
                        ('create_roles', 'Create Roles'), ('read_roles', 'Read Roles'), ('update_roles', 'Update Roles'), ('delete_roles', 'Delete Roles'),
                        ('create_permissions', 'Create Permissions'), ('read_permissions', 'Read Permissions'), ('update_permissions', 'Update Permissions'), ('delete_permissions', 'Delete Permissions'),
                        ('create_logs', 'Create Logs'), ('read_logs', 'Read Logs'), ('update_logs', 'Update Logs'), ('delete_logs', 'Delete Logs');'''

        self.cursor.execute(sql_insert)


    def create_role_permissions_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS role_permissions (
            role_id INT NOT NULL,
            permission_id VARCHAR(20) NOT NULL
        );'''

        self.cursor.execute(sql)

        sql_insert = '''INSERT INTO role_permissions (role_id, permission_id) 
                        VALUES 
                        (1, 'create_products'), (1, 'read_products'), (1, 'update_products'), (1, 'delete_products'),
                        (1, 'create_categories'), (1, 'read_categories'), (1, 'update_categories'), (1, 'delete_categories'),
                        (1, 'create_suppliers'), (1, 'read_suppliers'), (1, 'update_suppliers'), (1, 'delete_suppliers'),
                        (1, 'create_transactions'), (1, 'read_transactions'), (1, 'update_transactions'), (1, 'delete_transactions'),
                        (1, 'create_purchasing'), (1, 'read_purchasing'), (1, 'update_purchasing'), (1, 'delete_purchasing'),
                        (1, 'create_customers'), (1, 'read_customers'), (1, 'update_customers'), (1, 'delete_customers'),
                        (1, 'create_users'), (1, 'read_users'), (1, 'update_users'), (1, 'delete_users'),
                        (1, 'create_roles'), (1, 'read_roles'), (1, 'update_roles'), (1, 'delete_roles'),
                        (1, 'create_permissions'), (1, 'read_permissions'), (1, 'update_permissions'), (1, 'delete_permissions'),
                        (1, 'create_logs'), (1, 'read_logs'), (1, 'update_logs'), (1, 'delete_logs');'''
        
        self.cursor.execute(sql_insert)


    def create_logs_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            log_name VARCHAR(20) NOT NULL,
            log_description TEXT DEFAULT '',
            log_type VARCHAR(1) NOT NULL,
            old_data TEXT DEFAULT '',
            new_data TEXT DEFAULT '',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by INT NOT NULL
        );'''

        self.cursor.execute(sql)

        sql_insert = '''INSERT INTO logs (log_name, log_description, log_type, old_data, new_data, created_at, created_by) 
                        VALUES 
                        ('Log One', 'Log One Description', 'C', '', 'Create Data', CURRENT_TIMESTAMP, 1),
                        ('Log Two', 'Log Two Description', 'U', 'Old Data Two', 'New Data Two', CURRENT_TIMESTAMP, 1),
                        ('Log Three', 'Log Three Description', 'D', 'Old Data Three', '', CURRENT_TIMESTAMP, 1);'''

        self.cursor.execute(sql_insert)


    def create_users_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            username VARCHAR(20) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            user_salt VARCHAR(255) NOT NULL,
            role_id INT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NULL DEFAULT NULL
        );'''

        self.cursor.execute(sql)
        password = 'admin'
        salt = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
        password = salt + password
        password_hash = hashlib.sha512(password.encode()).hexdigest()

        sql_insert = '''INSERT INTO users (username, password_hash, user_salt, role_id, is_active, created_at, updated_at) 
                        VALUES 
                        (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, NULL);'''

        self.cursor.execute(sql_insert, ('admin', password_hash, salt, 1, True))     


    def create_customers_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            customer_name VARCHAR(50) NOT NULL,
            customer_phone VARCHAR(20) NOT NULL UNIQUE,
            customer_points INT(10) NOT NULL DEFAULT 0,
            number_of_transactions INT(10) NOT NULL DEFAULT 0,
            transaction_value INT(10) NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NULL DEFAULT NULL
        );'''

        self.cursor.execute(sql)

        sql_insert = '''INSERT INTO customers (customer_name, customer_phone, customer_points, number_of_transactions, transaction_value) 
                        VALUES 
                        ('Customer One', '081234567890', 0, 0, 0),
                        ('Customer Two', '081234567891', 0, 0, 0),
                        ('Customer Three', '081234567892', 0, 0, 0);'''
        
        self.cursor.execute(sql_insert)


    def create_purchasing_history_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS purchasing_history (
            purchasing_id VARCHAR(20) NOT NULL,
            supplier_id INT NOT NULL,
            invoice_date DATETIME NOT NULL,
            invoice_number VARCHAR(20) NOT NULL,
            invoice_expired_date DATETIME NOT NULL,
            total_amount INT(10) NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            purchasing_remarks TEXT DEFAULT ''
        );'''

        self.cursor.execute(sql)

        sql_insert = '''INSERT INTO purchasing_history (purchasing_id, supplier_id, invoice_date, invoice_number, invoice_expired_date, total_amount, created_at, purchasing_remarks) 
                        VALUES 
                        ('PO202502010001', 1, CURRENT_TIMESTAMP, 'INV001', CURRENT_TIMESTAMP, 70000, CURRENT_TIMESTAMP, 'Remarks Purchasing One');'''

        self.cursor.execute(sql_insert)


    def create_detail_purchasing_history_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS detail_purchasing_history (
            purchasing_id VARCHAR(20) NOT NULL,
            sku VARCHAR(20) NOT NULL,
            unit VARCHAR(10) NOT NULL,
            qty INT(10) NOT NULL,
            price INT(10) NOT NULL,
            discount_rp INT(10) NOT NULL DEFAULT 0,
            discount_pct INT(10) NOT NULL DEFAULT 0,
            subtotal INT(10) NOT NULL
        );'''

        self.cursor.execute(sql)
        
        sql_insert = '''INSERT INTO detail_purchasing_history (purchasing_id, sku, unit, qty, price, discount_rp, discount_pct, subtotal) 
                        VALUES 
                        ('PO202502010001', 'SKU001', 'PCS', 50, 1000, 0, 0, 50000),
                        ('PO202502010001', 'SKU002', 'PCS', 10, 1000, 0, 0, 10000),
                        ('PO202502010001', 'SKU003', 'PCS', 10, 1000, 0, 0, 10000);'''

        self.cursor.execute(sql_insert)


    def create_detail_transactions_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS detail_transactions (
            transaction_id VARCHAR(20) NOT NULL,
            sku VARCHAR(20) NOT NULL,
            unit VARCHAR(10) NOT NULL,
            unit_value INT(10) NOT NULL,
            qty INT(10) NOT NULL,
            price INT(10) NOT NULL,
            discount_rp INT(10) NOT NULL DEFAULT 0,
            discount_rp_per_item INT(10) NOT NULL DEFAULT 0,
            discount_pct INT(10) NOT NULL DEFAULT 0,
            sub_total INT(10) NOT NULL);'''
        
        self.cursor.execute(sql)
        
        # Add indexes for faster transaction lookups
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_detail_transactions_id ON detail_transactions(transaction_id);')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_detail_transactions_sku ON detail_transactions(sku);')

        sql_insert = '''INSERT INTO detail_transactions (transaction_id, sku, unit, unit_value, qty, price, discount_rp, discount_rp_per_item, discount_pct, sub_total) 
                        VALUES 
                        ('J202502010001', 'SKU001', 'PCS', 1, 10, 1000, 0, 0, 0, 10000),
                        ('J202502010001', 'SKU002', 'PCS', 1, 10, 1000, 0, 0, 0, 10000),
                        ('J202502010001', 'SKU003', 'PCS', 1, 10, 1000, 0, 0, 0, 10000);'''
        
        self.cursor.execute(sql_insert)
        
        sql = '''CREATE TABLE IF NOT EXISTS pending_detail_transactions (
            transaction_id VARCHAR(20) NOT NULL,
            sku VARCHAR(20) NOT NULL,
            unit VARCHAR(10) NOT NULL,
            unit_value INT(10) NOT NULL,
            qty INT(10) NOT NULL,   
            price INT(10) NOT NULL,
            discount_rp INT(10) NOT NULL DEFAULT 0,
            discount_rp_per_item INT(10) NOT NULL DEFAULT 0,
            discount_pct INT(10) NOT NULL DEFAULT 0,
            sub_total INT(10) NOT NULL);'''
        
        self.cursor.execute(sql)
        
        # Add indexes for faster pending transaction lookups
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_pending_detail_transactions_id ON pending_detail_transactions(transaction_id);')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_pending_detail_transactions_sku ON pending_detail_transactions(sku);')

        sql_insert = '''INSERT INTO pending_detail_transactions (transaction_id, sku, unit, unit_value, qty, price, discount_rp, discount_rp_per_item, discount_pct, sub_total) 
                        VALUES 
                        ('P202502010001', 'SKU001', 'PCS', 1, 10, 1000, 0, 0, 0, 10000),
                        ('P202502010001', 'SKU002', 'PCS', 1, 10, 1000, 0, 0, 0, 10000),
                        ('P202502010001', 'SKU003', 'PCS', 1, 10, 1000, 0, 0, 0, 10000),
                        ('P202502010002', 'SKU001', 'KODI', 20, 1, 1000, 0, 0, 0, 10000),
                        ('P202502010002', 'SKU001', 'DUS', 10, 1, 1000, 0, 0, 0, 10000);'''

        
        self.cursor.execute(sql_insert)


    def create_transactions_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS transactions (
            transaction_id VARCHAR(20) PRIMARY KEY NOT NULL,
            customer_id VARCHAR(20),
            total_amount INT(10) NOT NULL,
            payment_method VARCHAR(10) NOT NULL,
            payment_rp INT(10) NOT NULL,
            payment_change INT(10) NOT NULL,
            discount_transaction_id INT(10),
            discount_amount INT(10) NOT NULL DEFAULT 0,
            tax_pct INT(10) NOT NULL DEFAULT 0,
            tax_amount INT(10) NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            payment_remarks TEXT DEFAULT ''
        );'''

        self.cursor.execute(sql)

        sql_insert = '''INSERT INTO transactions (transaction_id, customer_id, total_amount, payment_method, payment_rp, payment_change, 
                                                    discount_transaction_id, discount_amount, tax_pct, tax_amount, 
                                                    created_at, payment_remarks) 
                        VALUES 
                        ('J202502010001', '1', 30000, 'Cash', 30000, 0, 0, 0, 0, 0, CURRENT_TIMESTAMP, 'Remarks One'),
                        ('AB202502010002', '1', 200000, 'Transfer', 200000, 0, 0, 0, 0, 0, CURRENT_TIMESTAMP, 'Remarks Two'),
                        ('AB202502010003', '1', 300000, 'Transfer', 300000, 0, 0, 0, 0, 0, CURRENT_TIMESTAMP, 'Remarks Three');'''

        self.cursor.execute(sql_insert)

        sql = '''CREATE TABLE IF NOT EXISTS pending_transactions (
            transaction_id VARCHAR(20) PRIMARY KEY NOT NULL,
            customer_id VARCHAR(20),
            total_amount INT(10) NOT NULL,
            discount_transaction_id INT(10),
            discount_amount INT(10) NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            payment_remarks TEXT DEFAULT ''
        );'''

        self.cursor.execute(sql)

        sql_insert = '''INSERT INTO pending_transactions (transaction_id, customer_id, total_amount, created_at, payment_remarks) 
                        VALUES 
                        ('P202502010001', '1', 40000, CURRENT_TIMESTAMP, 'Remarks One'),
                        ('P202502010002', '1', 30000, CURRENT_TIMESTAMP, 'Remarks Two'),
                        ('P202502010003', '1', 30000, CURRENT_TIMESTAMP, 'Remarks Three');'''


        self.cursor.execute(sql_insert)


    def create_suppliers_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS suppliers (
                    supplier_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    supplier_name VARCHAR(50) NOT NULL,
                    supplier_address VARCHAR(100) DEFAULT '',
                    supplier_city VARCHAR(100) DEFAULT '',
                    supplier_phone VARCHAR(100) DEFAULT '',
                    supplier_remarks TEXT DEFAULT '' );'''

        self.cursor.execute(sql)

        sql_insert = '''INSERT INTO suppliers (supplier_name, supplier_address, supplier_city, supplier_phone, supplier_remarks) 
                        VALUES 
                        ('Supplier One', 'Address One', 'City One', '081234567890', 'Remarks One'),
                        ('Supplier Two', 'Address Two', 'City Two', '081234567891', 'Remarks Two'),
                        ('Supplier Three', 'Address Three', 'City Three', '081234567892', 'Remarks Three');'''
        
        self.cursor.execute(sql_insert)


    def create_products_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS products (
            sku VARCHAR(20) NOT NULL UNIQUE,
            product_name VARCHAR(120) NOT NULL,
            barcode VARCHAR(20),
            category_id INT(10),
            supplier_id INT(10),
            cost_price INT(10) NULL,
            price INT(10) NOT NULL,
            remarks TEXT NOT NULL DEFAULT '',
            stock INT(10) NOT NULL DEFAULT 0,
            unit VARCHAR(10) NOT NULL DEFAULT '',
            last_price INT(10) NOT NULL DEFAULT 0,
            average_price INT(10) NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NULL DEFAULT NULL,
            PRIMARY KEY (sku)
        );'''

        self.cursor.execute(sql)

        # Add indexes for faster queries
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_product_name ON products(product_name);')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_supplier_id ON products(supplier_id);')
        
        sql_insert = '''INSERT INTO products (sku, product_name, barcode, category_id, supplier_id, cost_price, price, remarks, stock, unit, last_price, average_price, created_at, updated_at) 
                    VALUES 
                    ('SKU001', 'Product One', 'barcode', 1, 1, 1000, 1500, 'Best seller', 40, 'PCS', 1000, 1000, CURRENT_TIMESTAMP, NULL),
                    ('SKU002', 'Product Two', 'barcode', 2, 2, 2000, 2500, 'Limited stock', 30, 'PCS', 0, 0, CURRENT_TIMESTAMP, NULL),
                    ('SKU003', 'Product Three', 'barcode', 3, 3, 3000, 20, 'New arrival', 20, 'PCS', 0, 0, CURRENT_TIMESTAMP, NULL); '''
        
        self.cursor.execute(sql_insert)
    

    def create_units_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS units (
            sku VARCHAR(20) NOT NULL,
            barcode VARCHAR(20),
            unit VARCHAR(10) NOT NULL,
            unit_value INT(10) NOT NULL,
            price INT(10) NOT NULL,
            UNIQUE (sku, unit)
        );'''

        self.cursor.execute(sql)
        
        # Add indexes for faster joins with products
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_units_sku ON units(sku);')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_units_barcode ON units(barcode);')

        sql_insert = '''INSERT INTO units (sku, barcode, unit, unit_value, price) 
                        VALUES 
                        ('SKU001', 'barcode', 'KODI', 20, 28000),
                        ('SKU001', 'barcode', 'DUS', 10, 20000); '''
        
        self.cursor.execute(sql_insert)


    def create_categories_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            category_name VARCHAR(100) NOT NULL
        );'''

        self.cursor.execute(sql)
        
        # Add index for category name searches
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(category_name);')

        sql_insert = '''INSERT INTO categories (category_name) 
                            VALUES 
                            ('Electronics'),
                            ('Clothing'),
                            ('Home Appliances');'''
        
        self.cursor.execute(sql_insert)
        

    def create_product_categories_detail_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS product_categories_detail (
            sku VARCHAR(20) NOT NULL,
            category_id INT NOT NULL
        );'''

        self.cursor.execute(sql)
        
        # Add indexes for faster joins
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_categories_sku ON product_categories_detail(sku);')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_categories_category_id ON product_categories_detail(category_id);')
        self.cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_product_categories_unique ON product_categories_detail(sku, category_id);')

        sql_insert = '''INSERT INTO product_categories_detail (sku, category_id) 
                        VALUES 
                        ('SKU001', 1),
                        ('SKU002', 2),
                        ('SKU003', 3);'''
        
        self.cursor.execute(sql_insert)


    def drop_all_tables(self):
        self.cursor.execute('DROP TABLE IF EXISTS stock_card')
        self.cursor.execute('DROP TABLE IF EXISTS roles')
        self.cursor.execute('DROP TABLE IF EXISTS permissions')
        self.cursor.execute('DROP TABLE IF EXISTS role_permissions')
        self.cursor.execute('DROP TABLE IF EXISTS logs')
        self.cursor.execute('DROP TABLE IF EXISTS users')
        self.cursor.execute('DROP TABLE IF EXISTS customers')
        self.cursor.execute('DROP TABLE IF EXISTS detail_transactions')
        self.cursor.execute('DROP TABLE IF EXISTS pending_detail_transactions')
        self.cursor.execute('DROP TABLE IF EXISTS transactions')
        self.cursor.execute('DROP TABLE IF EXISTS pending_transactions')
        self.cursor.execute('DROP TABLE IF EXISTS suppliers')
        self.cursor.execute('DROP TABLE IF EXISTS detail_purchasing_history')
        self.cursor.execute('DROP TABLE IF EXISTS purchasing_history')
        self.cursor.execute('DROP TABLE IF EXISTS product_categories_detail')
        self.cursor.execute('DROP TABLE IF EXISTS units')
        self.cursor.execute('DROP TABLE IF EXISTS products')
        self.cursor.execute('DROP TABLE IF EXISTS categories')


    def seed_all(self):
        """Run all seed functions in order."""
        self.cursor.execute('BEGIN TRANSACTION')

        self.drop_all_tables()

        self.create_stock_card_table()
        self.create_suppliers_table()
        self.create_purchasing_history_table()
        self.create_detail_purchasing_history_table()
        self.create_products_table()
        self.create_detail_transactions_table()
        self.create_transactions_table()
        self.create_units_table()
        self.create_categories_table()
        self.create_product_categories_detail_table()
        self.create_roles_table()
        self.create_permissions_table()
        self.create_role_permissions_table()
        self.create_logs_table()
        self.create_users_table()
        self.create_customers_table()
        
        self.db.commit()
        self.db.close()


if __name__ == "__main__":
    seeder = SeedData()
    seeder.seed_all()
