import os
import sys

def create_module_structure(module_name: str):
    # Base directory structure
    directories = [
        f"{module_name}",
        f"{module_name}/models",
        f"{module_name}/repositories",
        f"{module_name}/services",
    ]
    
    # Files to create
    files = [
        f"{module_name}/models/{module_name}_models.py",
        f"{module_name}/repositories/{module_name}_repositories.py",
        f"{module_name}/services/{module_name}_services.py",
        f"{module_name}/translations.py",
        f"{module_name}/{module_name}.py",
    ]
    
    # Create directories
    for directory in directories:
        try:
            os.makedirs(directory)
            print(f"Created directory: {directory}")
        except FileExistsError:
            print(f"Directory already exists: {directory}")
    
    # Create files with basic template content
    for file_path in files:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                # Get the base filename without extension
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # Create appropriate template based on file type
                if "models" in file_path:
                    content = f'''from dataclasses import dataclass
from typing import Optional

@dataclass
class {module_name.replace('_', ' ').title().replace(' ', '')}Model:
    id: int
    name: str
    description: Optional[str] = None
'''
                elif "repositories" in file_path:
                    content = f'''from connect_db import DatabaseConnection
from typing import List
from response.response_message import ResponseMessage
from {module_name}.models.{module_name}_models import {module_name.replace('_', ' ').title().replace(' ', '')}Model
from generals.permission_manager import PermissionManager

class {module_name.replace('_', ' ').title().replace(' ', '')}Repository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()
        
'''
                elif "services" in file_path:
                    content = f'''from typing import List, Optional
from {module_name}.repositories.{module_name}_repositories import {module_name.replace('_', ' ').title().replace(' ', '')}Repository
from generals.permission_manager import PermissionManager


class {module_name.replace('_', ' ').title().replace(' ', '')}Service:
    def __init__(self):
        self.repository = {module_name.replace('_', ' ').title().replace(' ', '')}Repository()
        self.permission_manager = PermissionManager()
'''
                elif "translations" in file_path:
                    content = f'''{module_name.upper()}_TRANSLATIONS = {{
    'en': {{
    }},

    'id': {{
    }}
}}
'''

                else:
                    content = f'''from PyQt6 import QtWidgets, uic

from {module_name}.services.{module_name}_services import {module_name.replace('_', ' ').title().replace(' ', '')}Service
from {module_name}.models.{module_name}_models import {module_name.replace('_', ' ').title().replace(' ', '')}Model

from helper import format_number, add_prefix, remove_non_digit
from generals.message_box import POSMessageBox
from generals.build import resource_path
from generals.fonts import POSFonts
from generals.constants import (
    SELECT_ROWS, SINGLE_SELECTION, 
    NO_EDIT_TRIGGERS, RESIZE_TO_CONTENTS
)
from generals.messages import (
    ERR, OK, PERM_DENIED
)
from generals.permission_manager import PermissionManager


class {module_name.replace('_', ' ').title().replace(' ', '')}Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        self.ui = uic.loadUi(resource_path('ui/{module_name}.ui'), self)

        # Init Services
        self.{module_name}_service = {module_name.replace('_', ' ').title().replace(' ', '')}Service()
'''
                
                f.write(content)
            print(f"Created file: {file_path}")
        else:
            print(f"File already exists: {file_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_module.py <module_name>")
        sys.exit(1)
        
    module_name = sys.argv[1].lower()
    create_module_structure(module_name) 