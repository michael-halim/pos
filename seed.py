from connect_db import DatabaseConnection

class SeedData:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()

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
            sku VARCHAR(20) NOT NULL,
            product_name VARCHAR(120) NOT NULL,
            cost_price INT(10) NULL,
            price INT(10) NOT NULL,
            remarks TEXT NOT NULL DEFAULT '',
            stock INT(10) NOT NULL DEFAULT 0,
            unit VARCHAR(10) NOT NULL DEFAULT '',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NULL DEFAULT NULL,
            UNIQUE (sku, unit)
        );'''

        self.cursor.execute(sql)

        sql_insert = '''INSERT INTO products (sku, product_name, cost_price, price, stock, remarks, unit, created_at, updated_at) 
                    VALUES 
                    ('SKU001', 'Product One', 1000, 1500, 50, 'Best seller', 'pcs', CURRENT_TIMESTAMP, NULL),
                    ('SKU002', 'Product Two', 2000, 2500, 30, 'Limited stock', 'pcs', CURRENT_TIMESTAMP, NULL),
                    ('SKU003', 'Product Three', NULL, 3000, 20, 'New arrival', 'pcs', CURRENT_TIMESTAMP, NULL); '''
        
        self.cursor.execute(sql_insert)
    
    def create_units_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS units (
            sku VARCHAR(20) NOT NULL,
            unit VARCHAR(10) NOT NULL,
            unit_value INT(10) NOT NULL
        );'''

        self.cursor.execute(sql)

        sql_insert = '''INSERT INTO units (sku, unit, unit_value) 
                        VALUES 
                        ('SKU001', 'pcs', 1),
                        ('SKU002', 'pcs', 1),
                        ('SKU003', 'pcs', 1); '''
        
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
        self.cursor.execute('DROP TABLE IF EXISTS suppliers')
        self.cursor.execute('DROP TABLE IF EXISTS product_categories_detail')
        self.cursor.execute('DROP TABLE IF EXISTS products')
        self.cursor.execute('DROP TABLE IF EXISTS categories')

    def seed_all(self):
        """Run all seed functions in order."""
        self.drop_all_tables()

        self.create_suppliers_table()
        self.create_products_table()
        self.create_units_table()
        self.create_categories_table()
        self.create_product_categories_detail_table()

        self.db.commit()
        self.db.close()


if __name__ == "__main__":
    seeder = SeedData()
    seeder.seed_all()
