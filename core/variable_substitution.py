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

        self.text_extensions = {
            '.txt', '.yml', '.yaml', '.json', '.properties', '.conf', '.cfg', 
            '.sh', '.bat', '.cmd', '.ps1', '.xml', '.html', '.css', '.js', 
            '.py', '.java', '.cpp', '.c', '.h', '.md', '.ini', '.toml'
        }
    
    def process_file(self, source_path: str, dest_path: str, variables: Dict[str, Any]):
        file_ext = os.path.splitext(source_path)[1].lower()
        
        if file_ext in self.text_extensions:
            try:
                with open(source_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if self.placeholder_pattern.search(content):
                    template = self.jinja_env.from_string(content)
                    processed_content = template.render(**variables)
                    
                    with open(dest_path, 'w', encoding='utf-8') as f:
                        f.write(processed_content)
                else:
                    with open(dest_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
            except UnicodeDecodeError:
                shutil.copy2(source_path, dest_path)
            except Exception as e:
                print(f"Warning: Could not process {source_path}: {e}")
                shutil.copy2(source_path, dest_path)
        else:
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