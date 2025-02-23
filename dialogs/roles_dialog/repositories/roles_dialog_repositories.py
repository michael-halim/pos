from connect_db import DatabaseConnection
from response.response_message import ResponseMessage
from dialogs.roles_dialog.models.roles_dialog_models import RolesModel, PermissionsModel    

class RolesDialogRepository:
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

