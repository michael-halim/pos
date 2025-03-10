import hashlib
from connect_db import DatabaseConnection

from response.response_message import ResponseMessage

class LoginRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        

    def login(self, username: str, password: str):
        try:
            # Get user_id, user_salt, password_hash
            sql = '''SELECT u.user_salt, u.password_hash, u.role_id
                        FROM users u
                        WHERE u.username = ?
                        LIMIT 1'''
            user_result = self.cursor.execute(sql, (username,))

            user = user_result.fetchone()
            
            if user:
                user_salt, password_hash, role_id = user[0], user[1], user[2]
                # Check if the password is correct
                password = user_salt + password
                password_hash_input = hashlib.sha512(password.encode()).hexdigest()

                if password_hash != password_hash_input:
                    return ResponseMessage.fail(message="Invalid username or password!")
                
                # Get user permissions based on role 
                sql = '''SELECT rp.permission_id
                        FROM role_permissions rp
                        WHERE rp.role_id = ?'''
                
                permissions_result = self.cursor.execute(sql, (role_id,))

                permissions = set(p[0] for p in permissions_result)

                return ResponseMessage.ok(message="Login successful!", data=permissions)

  
            return ResponseMessage.fail(message="Invalid username or password!")
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def get_user_id(self, username: str):
        try:
            sql = '''SELECT user_id
                    FROM users
                    WHERE username = ?
                    LIMIT 1'''
            user_result = self.cursor.execute(sql, (username,))

            user = user_result.fetchone()

            if user:
                return ResponseMessage.ok(message="User found!", data=user[0])  
            
            return ResponseMessage.fail(message="User not found!")
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")

