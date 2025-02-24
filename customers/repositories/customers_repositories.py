from typing import List, Optional
from datetime import datetime, timedelta
from connect_db import DatabaseConnection
from customers.models.customers_models import CustomersModel
from response.response_message import ResponseMessage

class CustomersRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        

    def get_customers(self, search_text: str = None):
        try:
            customers_result = []
            if search_text:
                sql = '''SELECT customer_id, customer_name, customer_phone, customer_points, number_of_transactions, transaction_value 
                            FROM customers
                            WHERE customer_id LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ? OR 
                                    customer_points LIKE ? OR number_of_transactions LIKE ? OR transaction_value LIKE ?'''
                
                search_text = f'%{search_text}%'
                customers_result = self.cursor.execute(sql, (search_text, search_text, search_text, search_text, search_text, search_text))
            else:
                sql = '''SELECT customer_id, customer_name, customer_phone, customer_points, number_of_transactions, transaction_value 
                            FROM customers'''
                customers_result = self.cursor.execute(sql)

            customers = [
                CustomersModel(customer_id=r[0], customer_name=r[1], customer_phone=r[2], 
                               customer_points=r[3], number_of_transactions=r[4], 
                               transaction_value=r[5]) 
                for r in customers_result
            ]

            return ResponseMessage.ok(
                message="Customers fetched successfully!",
                data=customers
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def get_customer_by_id(self, customer_id: int):
        try: 
            sql = '''SELECT customer_id, customer_name, customer_phone, customer_points, number_of_transactions, transaction_value 
                    FROM customers
                    WHERE customer_id = ?'''
            
            customer_result = self.cursor.execute(sql, (customer_id,))

            customer = [
                CustomersModel(customer_id=r[0], customer_name=r[1], customer_phone=r[2], 
                               customer_points=r[3], number_of_transactions=r[4], 
                               transaction_value=r[5]) 
                for r in customer_result
            ]

            return ResponseMessage.ok(
                message="Customer fetched successfully!",
                data=customer
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def create_customer(self, customer_data: CustomersModel):
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            sql = '''INSERT INTO customers (customer_name, customer_phone, customer_points, number_of_transactions, transaction_value) 
                    VALUES (?, ?, ?, ?, ?)'''
            
            self.cursor.execute(sql, (customer_data.customer_name, customer_data.customer_phone, customer_data.customer_points, 
                                      customer_data.number_of_transactions, customer_data.transaction_value))
            
            # Commit transaction
            self.db.commit()

            return ResponseMessage.ok(
                message="Customer created successfully!",
                data=customer_data
            )       
        
        except Exception as e:
            # Rollback transaction
            self.db.rollback()
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def update_customer(self, customer_data: CustomersModel):
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            sql = '''UPDATE customers 
                    SET customer_name = ?, customer_phone = ?, customer_points = ?, 
                        number_of_transactions = ?, transaction_value = ? 
                    WHERE customer_id = ?'''
            
            self.cursor.execute(sql, (customer_data.customer_name, customer_data.customer_phone, customer_data.customer_points, 
                                      customer_data.number_of_transactions, customer_data.transaction_value, customer_data.customer_id))
            
            # Commit transaction
            self.db.commit()

            return ResponseMessage.ok(message="Customer updated successfully!")     
        
        except Exception as e:
            # Rollback transaction
            self.db.rollback()
            return ResponseMessage.fail(message=f"Error: {str(e)}") 
            
            
    def delete_customer_by_customer_id(self, customer_id: int):
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            sql = '''DELETE FROM customers WHERE customer_id = ?'''
            self.cursor.execute(sql, (customer_id,))

            # Commit transaction
            self.db.commit()

            return ResponseMessage.ok(message="Customer deleted successfully!")
        
        except Exception as e:
            # Rollback transaction
            self.db.rollback()
            return ResponseMessage.fail(message=f"Error: {str(e)}") 
