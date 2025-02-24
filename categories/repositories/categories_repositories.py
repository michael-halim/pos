from typing import List, Optional
from datetime import datetime, timedelta
from connect_db import DatabaseConnection
from response.response_message import ResponseMessage
from categories.models.categories_models import CategoriesTableModel, ProcuctsTableModel


class CategoriesRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        

    def get_categories(self, search_text: str = None):
        try:
            categories_result = []
            if search_text:
                sql = '''SELECT category_id, category_name 
                            FROM categories
                            WHERE category_id LIKE ? OR category_name LIKE ?'''
                
                search_text = f'%{search_text}%'
                categories_result = self.cursor.execute(sql, (search_text, search_text))

            else:
                sql = '''SELECT category_id, category_name FROM categories'''
                categories_result = self.cursor.execute(sql)

            categories = [
                CategoriesTableModel(category_id=r[0], category_name=r[1]) 
                for r in categories_result
            ]

            return ResponseMessage.ok(
                message="Categories fetched successfully!",
                data=categories
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def get_category_by_id(self, category_id: int):
        try: 
            sql = '''SELECT category_id, category_name
                    FROM categories
                    WHERE category_id = ?'''
            
            category_result = self.cursor.execute(sql, (category_id,))
            category = category_result.fetchone()
            category = CategoriesTableModel(category_id=category[0], category_name=category[1])

            return ResponseMessage.ok(
                message="Category fetched successfully!",
                data=category
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def get_products(self, search_text: str = None):
        try:
            products_result = []
            if search_text:
                sql = '''SELECT sku, product_name, price, stock, unit, created_at
                        FROM products
                        WHERE sku LIKE ? OR product_name LIKE ?'''
                
                search_text = f'%{search_text}%'
                products_result = self.cursor.execute(sql, (search_text, search_text))

            else:
                sql = '''SELECT sku, product_name, price, stock, unit, created_at
                        FROM products'''

                products_result = self.cursor.execute(sql)


            products = [
                ProcuctsTableModel(sku=r[0], product_name=r[1], price=r[2], stock=r[3], 
                                   unit=r[4], created_at=r[5]) 
                for r in products_result
            ]

            return ResponseMessage.ok(
                message="Products fetched successfully!",
                data=products
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
        

    def get_selected_products_by_category_id(self, category_id: int):
        try: 
            sql = '''SELECT sku
                    FROM product_categories_detail
                    WHERE category_id = ?'''
            
            products_result = self.cursor.execute(sql, (category_id,))

            products = set(
                r[0] for r in products_result
            )
            
            return ResponseMessage.ok(
                message="Products selected fetched successfully!",
                data=products
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def submit_category(self, data: CategoriesTableModel, products: set[str]):
        try:
            sql = '''INSERT INTO categories (category_name) VALUES (?)'''
            self.cursor.execute(sql, (data.category_name,))
            self.db.commit()
            return ResponseMessage.ok(message="Category submitted successfully!")
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
        
    
    def update_category(self, category_form_data: CategoriesTableModel, added_products: set[str], deleted_products: set[str]):
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            category_id = category_form_data.category_id

            # Update role
            sql = '''UPDATE categories SET category_name = ? WHERE category_id = ?'''
            self.cursor.execute(sql, (category_form_data.category_name, category_id))

            # Delete product categories detail
            for product_id in deleted_products:   
                sql = '''DELETE FROM product_categories_detail WHERE category_id = ? AND sku = ?'''
                self.cursor.execute(sql, (category_id, product_id))

            # Insert new product categories detail
            for product_id in added_products:
                sql = '''INSERT INTO product_categories_detail (category_id, sku) VALUES (?, ?)'''
                self.cursor.execute(sql, (category_id, product_id))      

            # If everything successful, commit the transaction  
            self.db.commit()

            return ResponseMessage.ok(message="Category updated successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to update category: {str(e)}")
        

    def delete_category_by_id(self, category_id: int):
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Delete role permissions
            sql = '''DELETE FROM categories WHERE category_id = ?'''
            self.cursor.execute(sql, (category_id,))

            # Delete role
            sql = '''DELETE FROM product_categories_detail WHERE category_id = ?'''
            self.cursor.execute(sql, (category_id,))

            # If everything successful, commit the transaction  
            self.db.commit()

            return ResponseMessage.ok(message="Category deleted successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to delete category: {str(e)}")