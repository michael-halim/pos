from connect_db import DatabaseConnection

class SeedData:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()

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
            discount INT(10) NOT NULL DEFAULT 0,
            sub_total INT(10) NOT NULL);'''
        
        self.cursor.execute(sql)

        sql_insert = '''INSERT INTO detail_transactions (transaction_id, sku, unit, unit_value, qty, price, discount, sub_total) 
                        VALUES 
                        ('J202502010001', 'SKU001', 'PCS', 1, 10, 1000, 0, 10000),
                        ('J202502010001', 'SKU002', 'PCS', 1, 10, 1000, 0, 10000),
                        ('J202502010001', 'SKU003', 'PCS', 1, 10, 1000, 0, 10000);'''
        
        self.cursor.execute(sql_insert)
        
        sql = '''CREATE TABLE IF NOT EXISTS pending_detail_transactions (
            transaction_id VARCHAR(20) NOT NULL,
            sku VARCHAR(20) NOT NULL,
            unit VARCHAR(10) NOT NULL,
            unit_value INT(10) NOT NULL,
            qty INT(10) NOT NULL,
            price INT(10) NOT NULL,
            discount INT(10) NOT NULL DEFAULT 0,
            sub_total INT(10) NOT NULL);'''
        
        self.cursor.execute(sql)

        sql_insert = '''INSERT INTO pending_detail_transactions (transaction_id, sku, unit, unit_value, qty, price, discount, sub_total) 
                        VALUES 
                        ('P202502010001', 'SKU001', 'PCS', 1, 10, 1000, 0, 20000),
                        ('P202502010001', 'SKU002', 'PCS', 1, 10, 1000, 0, 10000),
                        ('P202502010001', 'SKU003', 'PCS', 1, 10, 1000, 0, 10000),
                        ('P202502010002', 'SKU001', 'KODI', 20, 1, 1000, 0, 20000),
                        ('P202502010002', 'SKU001', 'DUS', 10, 1, 1000, 0, 10000);'''

        
        self.cursor.execute(sql_insert)


    def create_transactions_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS transactions (
            transaction_id VARCHAR(20) PRIMARY KEY NOT NULL,
            total_amount INT(10) NOT NULL,
            payment_method VARCHAR(10) NOT NULL,
            payment_rp INT(10) NOT NULL,
            payment_change INT(10) NOT NULL,
            discount_transaction_id INT(10),
            discount_amount INT(10) NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            payment_remarks TEXT DEFAULT ''

        );'''

        self.cursor.execute(sql)

        sql_insert = '''INSERT INTO transactions (transaction_id, total_amount, payment_method, payment_rp, payment_change, created_at, payment_remarks) 
                        VALUES 
                        ('J202502010001', 30000, 'Cash', 30000, 0, CURRENT_TIMESTAMP, 'Remarks One'),
                        ('AB202502010002', 200000, 'Transfer', 200000, 0, CURRENT_TIMESTAMP, 'Remarks Two'),
                        ('AB202502010003', 300000, 'Transfer', 300000, 0, CURRENT_TIMESTAMP, 'Remarks Three');'''

        self.cursor.execute(sql_insert)

        sql = '''CREATE TABLE IF NOT EXISTS pending_transactions (
            transaction_id VARCHAR(20) PRIMARY KEY NOT NULL,
            total_amount INT(10) NOT NULL,
            discount_transaction_id INT(10),
            discount_amount INT(10) NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            payment_remarks TEXT DEFAULT ''
        );'''

        self.cursor.execute(sql)

        sql_insert = '''INSERT INTO pending_transactions (transaction_id, total_amount, created_at, payment_remarks) 
                        VALUES 
                        ('P202502010001', 40000, CURRENT_TIMESTAMP, 'Remarks One'),
                        ('P202502010002', 30000, CURRENT_TIMESTAMP, 'Remarks Two'),
                        ('P202502010003', 30000, CURRENT_TIMESTAMP, 'Remarks Three');'''
        


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
            updated_at DATETIME NULL DEFAULT NULL
        );'''

        self.cursor.execute(sql)

        sql_insert = '''INSERT INTO products (sku, product_name, barcode, category_id, supplier_id, cost_price, price, remarks, stock, unit, last_price, average_price, created_at, updated_at) 
                    VALUES 
                    ('SKU001', 'Product One', 'barcode', 1, 1, 1000, 1500, 'Best seller', 50, 'PCS', 1000, 1000, CURRENT_TIMESTAMP, NULL),
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

        sql_insert = '''INSERT INTO product_categories_detail (sku, category_id) 
                            VALUES 
                            ('SKU001', 1),
                            ('SKU002', 2),
                            ('SKU003', 3);'''
        
        self.cursor.execute(sql_insert)

    def drop_all_tables(self):
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
        self.drop_all_tables()

        self.create_suppliers_table()
        self.create_purchasing_history_table()
        self.create_detail_purchasing_history_table()
        self.create_products_table()
        self.create_detail_transactions_table()
        self.create_transactions_table()
        self.create_units_table()
        self.create_categories_table()
        self.create_product_categories_detail_table()

        self.db.commit()
        self.db.close()


if __name__ == "__main__":
    seeder = SeedData()
    seeder.seed_all()
