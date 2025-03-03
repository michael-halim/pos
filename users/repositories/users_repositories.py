from connect_db import DatabaseConnection
from datetime import datetime
import hashlib
import random
import string

from response.response_message import ResponseMessage
from users.models.users_models import UsersTableItemModel, UsersFormModel, RolesModel

class UsersRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        

    def get_users(self, search_text: str = None):
        try:
            users_result = []
            if search_text:
                sql = '''SELECT u.user_id, u.username, u.role_id, r.role_name, u.is_active, u.created_at 
                            FROM users u
                            JOIN roles r ON u.role_id = r.role_id
                            WHERE u.user_id LIKE ? OR u.username LIKE ? OR u.role_id LIKE ? OR r.role_name LIKE ? OR u.is_active LIKE ?'''
                
                search_text = f'%{search_text}%'
                users_result = self.cursor.execute(sql, (search_text, search_text, search_text, search_text))
            else:
                sql = '''SELECT u.user_id, u.username, u.role_id, r.role_name, u.is_active, u.created_at 
                            FROM users u
                            JOIN roles r ON u.role_id = r.role_id'''
                users_result = self.cursor.execute(sql)

            users = [
                UsersTableItemModel(user_id=r[0], username=r[1], role_id=r[2], role_name=r[3], 
                           is_active=r[4], created_at=r[5]) 
                for r in users_result
            ]

            return ResponseMessage.ok(
                message="Users fetched successfully!",
                data=users
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def get_user_by_id(self, user_id: str):
        try:    
            sql = '''SELECT u.user_id, u.username, u.role_id, r.role_name, u.is_active, u.created_at 
                        FROM users u
                        JOIN roles r ON u.role_id = r.role_id
                        WHERE u.user_id = ?
                        LIMIT 1'''
            
            self.cursor.execute(sql, (user_id,))

            user = self.cursor.fetchone()
            if user:
                user_data = UsersTableItemModel(user_id=user[0], username=user[1], role_id=user[2], role_name=user[3], is_active=user[4], created_at=user[5]) 
                return ResponseMessage.ok(message="User fetched successfully!", data=user_data)
            
            else:
                return ResponseMessage.fail(message="User not found!")
        

        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def set_user_status(self, user_id: str, status: bool):
        try:    
            self.cursor.execute('BEGIN TRANSACTION')

            status = 1 if status else 0
            self.cursor.execute('UPDATE users SET is_active = ? WHERE user_id = ?', (status, user_id))

            self.db.commit()
            
            return ResponseMessage.ok(message="User status updated successfully!")
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def submit_user(self, user_data: UsersFormModel):   
        try:
            self.cursor.execute('BEGIN TRANSACTION')
            
            # Hash the password
            salt = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
            hashed_password = hashlib.sha512(user_data.password.encode()).hexdigest()
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = '''INSERT INTO users (username, password_hash, user_salt, role_id, created_at) VALUES (?, ?, ?, ?, ?)'''

            self.cursor.execute(sql, (user_data.username, hashed_password, salt, user_data.role_id, today))

            self.db.commit()

            return ResponseMessage.ok(message="User created successfully!")

        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def update_user(self, user_data: UsersFormModel):
        try:
            self.cursor.execute('BEGIN TRANSACTION')

            sql = '''UPDATE users 
                        SET role_id = ? 
                        WHERE user_id = ?'''
            
            self.cursor.execute(sql, (user_data.role_id, user_data.user_id))

            self.db.commit()

            return ResponseMessage.ok(message="User updated successfully!")

        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def delete_user(self, user_id: int):
        try:
            self.cursor.execute('BEGIN TRANSACTION')

            sql = 'DELETE FROM users WHERE user_id = ?'
            
            self.cursor.execute(sql, (user_id,))

            self.db.commit()

            return ResponseMessage.ok(message="User deleted successfully!")

        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def get_role_by_id(self, role_id: int): 
        try:
            sql = '''SELECT role_id, role_name FROM roles WHERE role_id = ?'''
            self.cursor.execute(sql, (role_id,))
            role = self.cursor.fetchone()

            if role:
                role_data = RolesModel(role_id=role[0], role_name=role[1])
                return ResponseMessage.ok(message="Role fetched successfully!", data=role_data)
            
            else:
                return ResponseMessage.fail(message="Role not found!")
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
            
            
