from connect_db import DatabaseConnection

class SeedData:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()

    def create_products_table(self):
        sql = '''CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            sku VARCHAR(20) UNIQUE NOT NULL,
            product_name VARCHAR(120) NOT NULL,
            cost_price INT(10) NULL,
            price INT(10) NOT NULL,
            remarks TEXT NOT NULL DEFAULT '',
            stock INT(10) NOT NULL DEFAULT 0
        );'''

        self.cursor.execute(sql)

        sql_insert = '''INSERT INTO products (sku, product_name, cost_price, price, stock, remarks) 
                    VALUES 
                    ('SKU001', 'Product One', 1000, 1500, 50, 'Best seller'),
                    ('SKU002', 'Product Two', 2000, 2500, 30, 'Limited stock'),
                    ('SKU003', 'Product Three', NULL, 3000, 20, 'New arrival'); '''
        
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
            product_id INT NOT NULL,
            category_id INT NOT NULL
        );'''

        self.cursor.execute(sql)

        sql_insert = '''INSERT INTO product_categories_detail (product_id, category_id) 
                            VALUES 
                            (1, 1),
                            (2, 2),
                            (3, 3);'''
        
        self.cursor.execute(sql_insert)

    def drop_all_tables(self):
        self.cursor.execute('DROP TABLE IF EXISTS product_categories_detail')
        self.cursor.execute('DROP TABLE IF EXISTS products')
        self.cursor.execute('DROP TABLE IF EXISTS categories')

    def seed_all(self):
        """Run all seed functions in order."""
        self.drop_all_tables()
        
        self.create_products_table()
        self.create_categories_table()
        self.create_product_categories_detail_table()

        self.db.commit()
        self.db.close()


if __name__ == "__main__":
    seeder = SeedData()
    seeder.seed_all()
