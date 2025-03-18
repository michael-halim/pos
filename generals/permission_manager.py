from typing import List, Set

class PermissionManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize empty permissions set
            cls._instance._permissions = set()
            cls._instance._role_id = None
            cls._instance._username = None
            cls._instance._user_id = None
        return cls._instance

    
    def set_permissions(self, permissions: set[str]):
        """Set user permissions"""
        self._permissions = permissions
        

    def set_username(self, username: str):
        """Set username"""
        self._username = username

    
    def set_user_id(self, user_id: int):
        """Set user id"""
        self._user_id = user_id


    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in self._permissions
    

    def get_permissions(self) -> Set[str]:
        """Get all permissions"""
        return self._permissions


    def get_username(self) -> str:
        """Get username"""
        return self._username
    

    def get_user_id(self) -> int:
        """Get user id"""
        return self._user_id


    def clear_permissions(self):
        """Clear all permissions (e.g., on logout)"""
        self._permissions.clear()
        self._role_id = None
        self._username = None
        self._user_id = None