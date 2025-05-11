from connect_db import DatabaseConnection
from datetime import datetime
import hashlib
import random
import string
import json

from users.models.users_models import UsersTableItemModel, UsersFormModel, RolesModel

from response.response_message import ResponseMessage
from generals.permission_manager import PermissionManager
from generals.constants import PERM_R_USERS, PERM_C_USERS, PERM_U_USERS, PERM_D_USERS
from generals.messages import ERR_PERM_R_USERS, ERR_PERM_C_USERS, ERR_PERM_U_USERS, ERR_PERM_D_USERS


class UsersRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()


    def get_users(self, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_USERS):
            return ResponseMessage.fail(message=ERR_PERM_R_USERS)

        try:
            users_result = []
            if search_text:
                sql = '''SELECT u.user_id, u.username, u.role_id, r.role_name, u.is_active, u.created_at 
                            FROM users u
                            JOIN roles r ON u.role_id = r.role_id
                            WHERE u.user_id LIKE ? OR u.username LIKE ? OR r.role_name LIKE ?'''
                
                search_text = f'%{search_text}%'
                users_result = self.cursor.execute(sql, (search_text, search_text, search_text))
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
        if not self.permission_manager.has_permission(PERM_R_USERS):
            return ResponseMessage.fail(message=ERR_PERM_R_USERS)

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
        if not self.permission_manager.has_permission(PERM_U_USERS):
            return ResponseMessage.fail(message=ERR_PERM_U_USERS)

        try:    
            self.cursor.execute('BEGIN TRANSACTION')

            status = 1 if status else 0
            self.cursor.execute('UPDATE users SET is_active = ? WHERE user_id = ?', (status, user_id))

            self.db.commit()
            
            return ResponseMessage.ok(message="User status updated successfully!")
        
        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def submit_user(self, user_data: UsersFormModel):   
        if not self.permission_manager.has_permission(PERM_C_USERS):
            return ResponseMessage.fail(message=ERR_PERM_C_USERS)

        try:
            self.cursor.execute('BEGIN TRANSACTION')
            
            # Hash the password
            salt = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
            new_password = salt + user_data.password
            hashed_password = hashlib.sha512(new_password.encode()).hexdigest()

            # Insert User
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = '''INSERT INTO users (username, password_hash, user_salt, role_id, created_at) VALUES (?, ?, ?, ?, ?)'''

            self.cursor.execute(sql, (user_data.username, hashed_password, salt, user_data.role_id, today))

            # Make Json Object
            new_data = {
                'username': user_data.username,
                'role_id': user_data.role_id,
                'role_name': user_data.role_name
            }

            # Insert Log
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            self.cursor.execute(sql, (f'User {user_data.username} created', f'User {user_data.username} created successfully!', 'C', 
                                        None, json.dumps(new_data), today, self.permission_manager.get_user_id()))

            self.db.commit()

            return ResponseMessage.ok(message="User created successfully!")

        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def update_user(self, user_data: UsersFormModel):
        if not self.permission_manager.has_permission(PERM_U_USERS):
            return ResponseMessage.fail(message=ERR_PERM_U_USERS)

        try:
            self.cursor.execute('BEGIN TRANSACTION')

            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Get the old role id and role name
            sql = '''SELECT u.role_id, r.role_name 
                    FROM users u 
                    JOIN roles r ON u.role_id = r.role_id 
                    WHERE u.user_id = ?'''
            
            self.cursor.execute(sql, (user_data.user_id,))
            result = self.cursor.fetchone()
            old_role_id = result[0]
            old_role_name = result[1]
            old_data = {
                'role_id': old_role_id,
                'role_name': old_role_name
            }

            new_data = {
                'role_id': user_data.role_id,
                'role_name': user_data.role_name
            }

            # Update User
            sql = '''UPDATE users 
                        SET role_id = ?,
                        updated_at = ?,
                        updated_by = ?
                        WHERE user_id = ?'''
            
            self.cursor.execute(sql, (user_data.role_id, today, self.permission_manager.get_user_id(), user_data.user_id))

            # Insert Log
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            self.cursor.execute(sql, (f'User {user_data.username} role updated from', 
                                        f'User {user_data.username} role updated from {old_role_name} to {user_data.role_name}', 'U', 
                                        json.dumps(old_data), json.dumps(new_data), today, self.permission_manager.get_user_id()))
            
            self.db.commit()

            return ResponseMessage.ok(message="User updated successfully!")

        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def delete_user(self, user_id: int):
        if not self.permission_manager.has_permission(PERM_D_USERS):
            return ResponseMessage.fail(message=ERR_PERM_D_USERS)

        try:
            self.cursor.execute('BEGIN TRANSACTION')

            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Get the user data
            sql = '''SELECT username, role_id, is_active, created_at, updated_at, updated_by 
                        FROM users 
                        WHERE user_id = ? 
                        LIMIT 1'''
            
            self.cursor.execute(sql, (user_id,))
            result = self.cursor.fetchone()

            # Make Json Object
            user_data = {
                'username': result[0],
                'role_id': result[1],
                'is_active': result[2],
                'created_at': result[3],
                'updated_at': result[4], 
                'updated_by': result[5]
            }

            # Delete User
            sql = 'DELETE FROM users WHERE user_id = ?'
            self.cursor.execute(sql, (user_id,))

            # Insert Log
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            self.cursor.execute(sql, (f'User {result[0]} deleted', f'User {result[0]} deleted successfully!', 'D', 
                                        json.dumps(user_data), None, today, self.permission_manager.get_user_id()))

            self.db.commit()

            return ResponseMessage.ok(message="User deleted successfully!")

        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def get_role_by_id(self, role_id: int): 
        if not self.permission_manager.has_permission(PERM_R_USERS):
            return ResponseMessage.fail(message=ERR_PERM_R_USERS)

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
            
            
    def change_password(self, user_id: int, old_password: str, new_password: str):
        if not self.permission_manager.has_permission(PERM_U_USERS):
            return ResponseMessage.fail(message=ERR_PERM_U_USERS)

        try:
            self.cursor.execute('BEGIN TRANSACTION')
            # Check if old password is correct
            sql = 'SELECT user_salt, password_hash FROM users WHERE user_id = ? LIMIT 1'
            self.cursor.execute(sql, (user_id,))
            user_data = self.cursor.fetchone()

            
            if user_data:
                # Get the salt
                salt, current_password_hash = user_data[0], user_data[1]

                # Hash the old password
                old_password = salt + old_password
                old_password_hash = hashlib.sha512(old_password.encode()).hexdigest()

                # Check if the old password is correct
                if current_password_hash != old_password_hash:
                    return ResponseMessage.fail(message="Old password is incorrect!")
                

                # Generate New Salt
                new_salt = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
                new_password = new_salt + new_password

                # Hash the new password
                hashed_password = hashlib.sha512(new_password.encode()).hexdigest()

                today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Update the password
                sql = '''UPDATE users SET user_salt = ?, password_hash = ?, updated_at = ?, updated_by = ? WHERE user_id = ?'''
                self.cursor.execute(sql, (new_salt, hashed_password, today, self.permission_manager.get_user_id(), user_id))
                
                # Insert Log
                sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                    new_data, created_at, created_by) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)'''
                self.cursor.execute(sql, (f'User {user_id} password changed', f'User {user_id} password changed successfully!', 'U', 
                                            None, None, today, self.permission_manager.get_user_id()))

                self.db.commit()

                return ResponseMessage.ok(message="Password changed successfully!")
            
            else:
                return ResponseMessage.fail(message="User not found!")
        
        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(message=f"Error: {str(e)}")

