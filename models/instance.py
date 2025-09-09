import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class ServerInstance:
    name: str
    template_name: str
    path: str
    variables: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'template_name': self.template_name,
            'path': self.path,
            'variables': self.variables,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'version': self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServerInstance':
        return cls(
            name=data['name'],
            template_name=data['template_name'],
            path=data['path'],
            variables=data.get('variables', {}),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat())),
            version=data.get('version', '1.0.0')
        )
    
    def save_metadata(self):
        metadata_file = os.path.join(self.path, '.dotwork_instance.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_path(cls, instance_path: str) -> Optional['ServerInstance']:
        metadata_file = os.path.join(instance_path, '.dotwork_instance.json')
        if not os.path.exists(metadata_file):
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None