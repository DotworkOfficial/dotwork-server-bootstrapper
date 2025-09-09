import os
import yaml
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class TemplateVariable:
    name: str
    type: str
    description: str
    default_value: Any = None
    required: bool = True
    validation_rule: Optional[str] = None

@dataclass
class Template:
    name: str
    path: str
    description: str
    variables: List[TemplateVariable] = field(default_factory=list)
    version: str = "1.0.0"
    
    @classmethod
    def from_directory(cls, template_path: str) -> 'Template':
        if not os.path.exists(template_path):
            raise ValueError(f"Template directory not found: {template_path}")
        
        config_file = os.path.join(template_path, "template.yml")
        if not os.path.exists(config_file):
            config_file = os.path.join(template_path, "template.yaml")
        
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        else:
            # Create default config if none exists
            config = {
                'name': os.path.basename(template_path),
                'description': f"Template for {os.path.basename(template_path)}",
                'variables': []
            }
        
        template = cls(
            name=config.get('name', os.path.basename(template_path)),
            path=template_path,
            description=config.get('description', ''),
            version=config.get('version', '1.0.0')
        )
        
        # Parse variables
        for var_config in config.get('variables', []):
            variable = TemplateVariable(
                name=var_config['name'],
                type=var_config.get('type', 'string'),
                description=var_config.get('description', ''),
                default_value=var_config.get('default'),
                required=var_config.get('required', True),
                validation_rule=var_config.get('validation')
            )
            template.variables.append(variable)
        
        return template
    
    def get_files(self) -> List[str]:
        files = []
        for root, dirs, filenames in os.walk(self.path):
            # Skip template config files
            if 'template.yml' in filenames:
                filenames.remove('template.yml')
            if 'template.yaml' in filenames:
                filenames.remove('template.yaml')
            
            for filename in filenames:
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, self.path)
                files.append(relative_path)
        
        return files