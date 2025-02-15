import os
import sys

def create_module_structure(module_name: str):
    # Base directory structure
    directories = [
        f"{module_name}",
        f"{module_name}/{module_name}_models",
        f"{module_name}/{module_name}_repositories",
        f"{module_name}/{module_name}_services",
    ]
    
    # Files to create
    files = [
        f"{module_name}/{module_name}_models/{module_name}_models.py",
        f"{module_name}/{module_name}_repositories/{module_name}_repositories.py",
        f"{module_name}/{module_name}_services/{module_name}_services.py",
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
class {module_name.capitalize()}Model:
    id: int
    name: str
    description: Optional[str] = None
'''
                elif "repositories" in file_path:
                    content = f'''from typing import List, Optional
from ..{module_name}_models.{module_name}_models import {module_name.capitalize()}Model

class {module_name.capitalize()}Repository:
    def __init__(self):
        pass
        
    def get_all(self) -> List[{module_name.capitalize()}Model]:
        pass
        
    def get_by_id(self, id: int) -> Optional[{module_name.capitalize()}Model]:
        pass
'''
                elif "services" in file_path:
                    content = f'''from typing import List, Optional
from ..{module_name}_models.{module_name}_models import {module_name.capitalize()}Model
from ..{module_name}_repositories.{module_name}_repositories import {module_name.capitalize()}Repository

class {module_name.capitalize()}Service:
    def __init__(self):
        self.repository = {module_name.capitalize()}Repository()
        
    def get_all(self) -> List[{module_name.capitalize()}Model]:
        return self.repository.get_all()
        
    def get_by_id(self, id: int) -> Optional[{module_name.capitalize()}Model]:
        return self.repository.get_by_id(id)
'''
                else:
                    content = f'''from .{module_name}_services.{module_name}_services import {module_name.capitalize()}Service
from .{module_name}_models.{module_name}_models import {module_name.capitalize()}Model

class {module_name.capitalize()}:
    def __init__(self):
        self.service = {module_name.capitalize()}Service()
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