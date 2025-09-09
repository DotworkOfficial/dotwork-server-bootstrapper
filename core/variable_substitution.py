import os
import re
import shutil
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, Template as JinjaTemplate

class VariableSubstitution:
    def __init__(self):
        self.placeholder_pattern = re.compile(r'\{\{\s*(\w+)\s*\}\}')
        self.jinja_env = Environment(
            loader=FileSystemLoader('.'),
            autoescape=False
        )
    
    def process_file(self, source_path: str, dest_path: str, variables: Dict[str, Any]):
        try:
            # Try to read as text file for variable substitution
            with open(source_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if file contains placeholders
            if self.placeholder_pattern.search(content):
                # Process with Jinja2 for more advanced templating
                template = self.jinja_env.from_string(content)
                processed_content = template.render(**variables)
                
                with open(dest_path, 'w', encoding='utf-8') as f:
                    f.write(processed_content)
            else:
                # No placeholders, just copy the file
                with open(dest_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
        except UnicodeDecodeError:
            # Binary file, just copy it
            shutil.copy2(source_path, dest_path)
        except Exception as e:
            # Fallback to simple copy
            print(f"Warning: Could not process {source_path}: {e}")
            shutil.copy2(source_path, dest_path)
    
    def find_placeholders_in_file(self, file_path: str) -> list:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return list(set(self.placeholder_pattern.findall(content)))
        except (UnicodeDecodeError, IOError):
            return []
    
    def find_all_placeholders(self, directory: str) -> Dict[str, list]:
        placeholders = {}
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory)
                
                file_placeholders = self.find_placeholders_in_file(file_path)
                if file_placeholders:
                    placeholders[relative_path] = file_placeholders
        
        return placeholders
    
    def get_all_unique_placeholders(self, directory: str) -> list:
        all_placeholders = set()
        placeholders_by_file = self.find_all_placeholders(directory)
        
        for file_placeholders in placeholders_by_file.values():
            all_placeholders.update(file_placeholders)
        
        return sorted(list(all_placeholders))