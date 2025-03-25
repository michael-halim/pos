from connect_db import DatabaseConnection
import json
from datetime import datetime

from role_permissions.models.role_permissions_models import RolesModel, PermissionsModel

from response.response_message import ResponseMessage
from generals.constants import PERM_U_PERMISSIONS,  PERM_R_PERMISSIONS, PERM_C_PERMISSIONS, PERM_D_PERMISSIONS
from generals.messages import ERR_PERM_U_PERMISSIONS, ERR_PERM_D_PERMISSIONS, ERR_PERM_R_PERMISSIONS, ERR_PERM_C_PERMISSIONS
from generals.permission_manager import PermissionManager

class RolePermissionsRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()


    def get_roles(self, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_PERMISSIONS):
            return ResponseMessage.fail(message=ERR_PERM_R_PERMISSIONS)
        
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
        if not self.permission_manager.has_permission(PERM_R_PERMISSIONS):
            return ResponseMessage.fail(message=ERR_PERM_R_PERMISSIONS)
        
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
        if not self.permission_manager.has_permission(PERM_R_PERMISSIONS):
            return ResponseMessage.fail(message=ERR_PERM_R_PERMISSIONS)
        
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
        if not self.permission_manager.has_permission(PERM_C_PERMISSIONS):
            return ResponseMessage.fail(message=ERR_PERM_C_PERMISSIONS)
        
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
            
            # Set permissions
            self.permission_manager.set_permissions(selected_permissions)


            # Insert Log
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_data = {
                'role_id': role_id,
                'role_name': roles_form_data.role_name,
                'role_description': roles_form_data.role_description,
                'permissions': list(selected_permissions)
            }

            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)''' 
            
            self.cursor.execute(sql, (f'Role#{role_id}: {roles_form_data.role_name} submitted', f'Role#{role_id}: {roles_form_data.role_name} submitted successfully!', 'C', 
                                        None, json.dumps(new_data), today, self.permission_manager.get_user_id()))


            # If everything successful, commit the transaction
            self.db.commit()
            
            return ResponseMessage.ok(message="Role submitted successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to submit role: {str(e)}")


    def update_role_permissions(self, roles_form_data: RolesModel, added_permissions: set[str], deleted_permissions: set[str]):
        if not self.permission_manager.has_permission(PERM_U_PERMISSIONS):
            return ResponseMessage.fail(message=ERR_PERM_U_PERMISSIONS)
        
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            role_id = roles_form_data.role_id

            # Get permissions name
            added_and_deleted_permissions = added_permissions + deleted_permissions

            # Create the correct number of placeholders for the IN clause
            placeholders = ','.join('?' * len(added_and_deleted_permissions))

            sql = f'''SELECT permission_id, permission_name FROM permissions WHERE permission_id IN ({placeholders})'''
            self.cursor.execute(sql, added_and_deleted_permissions)
           
            permissions_result = self.cursor.fetchall()

            permissions_map = {}
            old_permissions_name = []
            old_permissions_id = []
            for r in permissions_result:
                permissions_map[r[0]] = r[1]
                old_permissions_id.append(r[0])
                old_permissions_name.append(r[1])
            
            # Get Old Role Data
            sql = '''SELECT role_name, role_description
                    FROM roles 
                    WHERE role_id = ?
                    LIMIT 1'''
            self.cursor.execute(sql, (role_id,))
            roles_result = self.cursor.fetchone()

            old_data = {
                'role_id': role_id,
                'role_name': roles_result[0],
                'role_description': roles_result[1],
                'old_permissions_id': old_permissions_id,
                'old_permissions_name': old_permissions_name
            }


            # Update role
            sql = '''UPDATE roles SET role_name = ?, role_description = ? WHERE role_id = ?'''
            self.cursor.execute(sql, (roles_form_data.role_name, roles_form_data.role_description, role_id))


            # Delete role permissions
            deleted_permissions_id = []
            for permission_id in deleted_permissions:   
                sql = '''DELETE FROM role_permissions WHERE role_id = ? AND permission_id = ?'''
                self.cursor.execute(sql, (role_id, permission_id))
                deleted_permissions_id.append(permission_id)


            # Insert new role permissions
            added_permissions_id = []
            for permission_id in added_permissions:
                sql = '''INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)'''
                self.cursor.execute(sql, (role_id, permission_id))      
                added_permissions_id.append(permission_id)


            # Set permissions in permission manager
            sql = 'SELECT rp.permission_id FROM role_permissions rp WHERE rp.role_id = ?'
            permissions_result = self.cursor.execute(sql, (role_id,))

            self.permission_manager.set_permissions(set(r[0] for r in permissions_result))
            
            # Insert Log
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_data = {
                'role_id': role_id,
                'role_name': roles_form_data.role_name,
                'role_description': roles_form_data.role_description,
                'deleted_permissions_id': deleted_permissions_id,
                'deleted_permissions_name': [permissions_map[x] for x in deleted_permissions_id],
                'added_permissions_id': added_permissions_id,
                'added_permissions_name': [permissions_map[x] for x in added_permissions_id]
            }

            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)''' 
            

            self.cursor.execute(sql, (f'Role#{role_id}: {roles_form_data.role_name} updated', f'Role#{role_id}: {roles_form_data.role_name} updated successfully!', 'U', 
                                        json.dumps(old_data), json.dumps(new_data), today, self.permission_manager.get_user_id()))
            

            # If everything successful, commit the transaction  
            self.db.commit()

            return ResponseMessage.ok(message="Role updated successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to update role: {str(e)}")
        
        
    def delete_role_permissions_by_role_id(self, role_id: int):
        if not self.permission_manager.has_permission(PERM_D_PERMISSIONS):
            return ResponseMessage.fail(message=ERR_PERM_D_PERMISSIONS)
        
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get Old Role Data
            sql = '''SELECT role_name, role_description
                    FROM roles 
                    WHERE role_id = ?
                    LIMIT 1'''
            self.cursor.execute(sql, (role_id,))
            roles_result = self.cursor.fetchone()

            # Get Old Permissions Data
            sql = '''SELECT permission_id, permission_name FROM permissions WHERE permission_id IN (?)'''
            self.cursor.execute(sql, (role_id,))
            permissions_result = self.cursor.fetchall()

            old_permissions_id = []
            old_permissions_name = []
            for r in permissions_result:
                old_permissions_id.append(r[0])
                old_permissions_name.append(r[1])

            old_data = {
                'role_id': role_id,
                'role_name': roles_result[0],
                'role_description': roles_result[1],
                'old_permissions_id': old_permissions_id,
                'old_permissions_name': old_permissions_name
            }

            # Delete role permissions
            sql = '''DELETE FROM role_permissions WHERE role_id = ?'''
            self.cursor.execute(sql, (role_id,))

            # Delete role
            sql = '''DELETE FROM roles WHERE role_id = ?'''
            self.cursor.execute(sql, (role_id,))

            # Set permissions in permission manager
            sql = 'SELECT rp.permission_id FROM role_permissions rp WHERE rp.role_id = ?'
            permissions_result = self.cursor.execute(sql, (role_id,))

            self.permission_manager.set_permissions(set(r[0] for r in permissions_result))
            
            # Insert Log
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)''' 
            
            self.cursor.execute(sql, (f'Role#{role_id}: {roles_result[0]} deleted', f'Role#{role_id}: {roles_result[0]} deleted successfully!', 'D', 
                                        json.dumps(old_data), None, today, self.permission_manager.get_user_id()))

            # If everything successful, commit the transaction  
            self.db.commit()

            return ResponseMessage.ok(message="Role deleted successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to delete role: {str(e)}")
