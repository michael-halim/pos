from typing import List, Optional
from datetime import datetime, timedelta
from connect_db import DatabaseConnection

class RolePermissionsRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        
