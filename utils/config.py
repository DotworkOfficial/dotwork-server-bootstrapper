import os
import json
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class AppConfig:
    templates_dir: str = "templates"
    instances_dir: str = "instances"
    default_output_dir: str = "instances"
    auto_backup: bool = True
    backup_dir: str = "backups"
    max_backups: int = 5
    log_level: str = "INFO"
    
    @classmethod
    def load(cls, config_file: str = "config.yml") -> 'AppConfig':
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    if config_file.endswith('.json'):
                        data = json.load(f)
                    else:
                        data = yaml.safe_load(f) or {}
                
                return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})
            except Exception as e:
                print(f"Error loading config: {e}")
        
        return cls()
    
    def save(self, config_file: str = "config.yml"):
        try:
            data = asdict(self)
            
            # Ensure directories exist
            os.makedirs(os.path.dirname(config_file) if os.path.dirname(config_file) else '.', exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                if config_file.endswith('.json'):
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
                    
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def ensure_directories(self):
        for dir_path in [self.templates_dir, self.instances_dir, self.backup_dir]:
            os.makedirs(dir_path, exist_ok=True)

class ConfigManager:
    def __init__(self, config_file: str = "config.yml"):
        self.config_file = config_file
        self.config = AppConfig.load(config_file)
        
    def get_config(self) -> AppConfig:
        return self.config
    
    def update_config(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save_config()
    
    def save_config(self):
        self.config.save(self.config_file)
    
    def reset_to_defaults(self):
        self.config = AppConfig()
        self.save_config()