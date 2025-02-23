from typing import List, Optional
from datetime import datetime, timedelta
from connect_db import DatabaseConnection
from response.response_message import ResponseMessage
from role_permissions.models.role_permissions_models import RolesModel, PermissionsModel

class RolePermissionsRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        

    def get_roles(self, search_text: str = None):
        try:
            roles_result = []
            if search_text:
                sql = '''SELECT role_id, role_name, role_description 
                            FROM roles
                            WHERE role_id LIKE ? OR role_name LIKE ? OR role_description LIKE ?'''
                
                search_text = f'%{search_text}%'
                roles_result = self.cursor.execute(sql, (search_text, search_text, search_text))
            else:
                sql = '''SELECT role_id, role_name, role_description FROM roles'''
                roles_result = self.cursor.execute(sql)

            roles = [
                RolesModel(role_id=r[0], role_name=r[1], role_description=r[2]) 
                for r in roles_result
            ]

            return ResponseMessage.ok(
                message="Roles fetched successfully!",
                data=roles
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
    

    def get_permissions(self):
        try:
            sql = '''SELECT permission_id, permission_name FROM permissions'''
            permissions_result = self.cursor.execute(sql)
            
            permissions = [
                PermissionsModel(permission_id=r[0], permission_name=r[1])
                for r in permissions_result
            ]

            return ResponseMessage.ok(
                message="Permissions fetched successfully!",
                data=permissions
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def get_permissions_by_role_id(self, role_id: int):
        try: 
            sql = '''SELECT rp.permission_id
                    FROM role_permissions rp
                    WHERE rp.role_id = ?'''
            
            permissions_result = self.cursor.execute(sql, (role_id,))

            allowed_permissions = set(
                r[0] for r in permissions_result
            )

            return ResponseMessage.ok(
                message="Permissions fetched successfully!",
                data=allowed_permissions
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
        

    def submit_role_permissions(self, roles_form_data: RolesModel, selected_permissions: set[str]):
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Insert role
            sql = '''INSERT INTO roles (role_name, role_description) VALUES (?, ?)'''
            
            self.cursor.execute(sql, (roles_form_data.role_name, roles_form_data.role_description))
            
            role_id = self.cursor.lastrowid

            # Insert role permissions
            for permission_id in selected_permissions:
                sql = '''INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)'''
                self.cursor.execute(sql, (role_id, permission_id))
                
            # If everything successful, commit the transaction
            self.db.commit()
            
            return ResponseMessage.ok(message="Role submitted successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to submit role: {str(e)}")


    def update_role_permissions(self, roles_form_data: RolesModel, added_permissions: set[str], deleted_permissions: set[str]):
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            role_id = roles_form_data.role_id

            # Update role
            sql = '''UPDATE roles SET role_name = ?, role_description = ? WHERE role_id = ?'''
            self.cursor.execute(sql, (roles_form_data.role_name, roles_form_data.role_description, role_id))

            # Delete role permissions
            for permission_id in deleted_permissions:   
                sql = '''DELETE FROM role_permissions WHERE role_id = ? AND permission_id = ?'''
                self.cursor.execute(sql, (role_id, permission_id))

            # Insert new role permissions
            for permission_id in added_permissions:
                sql = '''INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)'''
                self.cursor.execute(sql, (role_id, permission_id))      

            # If everything successful, commit the transaction  
            self.db.commit()

            return ResponseMessage.ok(message="Role updated successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to update role: {str(e)}")
        
        
    def delete_role_permissions_by_role_id(self, role_id: int):
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Delete role permissions
            sql = '''DELETE FROM role_permissions WHERE role_id = ?'''
            self.cursor.execute(sql, (role_id,))

            # Delete role
            sql = '''DELETE FROM roles WHERE role_id = ?'''
            self.cursor.execute(sql, (role_id,))

            # If everything successful, commit the transaction  
            self.db.commit()

            return ResponseMessage.ok(message="Role deleted successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to delete role: {str(e)}")
