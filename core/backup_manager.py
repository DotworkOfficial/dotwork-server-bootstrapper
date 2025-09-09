import os
import shutil
import zipfile
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from models.instance import ServerInstance
from utils.logger import get_logger

class BackupManager:
    def __init__(self, backup_dir: str = "backups", max_backups: int = 5):
        self.backup_dir = backup_dir
        self.max_backups = max_backups
        self.logger = get_logger()
        
        # Ensure backup directory exists
        os.makedirs(backup_dir, exist_ok=True)
    
    def create_backup(self, instance: ServerInstance, description: str = "") -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{instance.name}_{timestamp}.zip"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(instance.path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, instance.path)
                        zipf.write(file_path, arcname)
                
                # Add backup metadata
                backup_info = {
                    "instance_name": instance.name,
                    "template_name": instance.template_name,
                    "backup_date": timestamp,
                    "description": description,
                    "original_path": instance.path
                }
                
                import json
                zipf.writestr("backup_info.json", json.dumps(backup_info, indent=2))
            
            self.logger.info(f"Backup created: {backup_path}")
            
            # Clean up old backups
            self._cleanup_old_backups(instance.name)
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            if os.path.exists(backup_path):
                os.remove(backup_path)
            raise e
    
    def restore_backup(self, backup_path: str, restore_path: str = None) -> ServerInstance:
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Read backup info
                backup_info = None
                if "backup_info.json" in zipf.namelist():
                    import json
                    backup_info = json.loads(zipf.read("backup_info.json").decode('utf-8'))
                
                # Determine restore path
                if restore_path is None:
                    if backup_info and "original_path" in backup_info:
                        restore_path = backup_info["original_path"]
                    else:
                        # Generate new path
                        backup_filename = os.path.basename(backup_path)
                        instance_name = backup_filename.replace('.zip', '')
                        restore_path = os.path.join("instances", instance_name)
                
                # Create restore directory
                os.makedirs(restore_path, exist_ok=True)
                
                # Extract files
                for member in zipf.namelist():
                    if member != "backup_info.json":  # Skip metadata file
                        zipf.extract(member, restore_path)
                
                # Load instance metadata
                instance = ServerInstance.load_from_path(restore_path)
                if instance is None and backup_info:
                    # Create instance metadata from backup info
                    instance = ServerInstance(
                        name=backup_info["instance_name"],
                        template_name=backup_info["template_name"],
                        path=restore_path
                    )
                    instance.save_metadata()
                
                self.logger.info(f"Backup restored to: {restore_path}")
                return instance
                
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            raise e
    
    def list_backups(self, instance_name: str = None) -> List[dict]:
        backups = []
        
        for backup_file in os.listdir(self.backup_dir):
            if backup_file.endswith('.zip'):
                if instance_name is None or backup_file.startswith(f"{instance_name}_"):
                    backup_path = os.path.join(self.backup_dir, backup_file)
                    
                    try:
                        with zipfile.ZipFile(backup_path, 'r') as zipf:
                            backup_info = {"filename": backup_file, "path": backup_path}
                            
                            if "backup_info.json" in zipf.namelist():
                                import json
                                metadata = json.loads(zipf.read("backup_info.json").decode('utf-8'))
                                backup_info.update(metadata)
                            else:
                                # Parse from filename
                                parts = backup_file.replace('.zip', '').split('_')
                                if len(parts) >= 3:
                                    backup_info["instance_name"] = '_'.join(parts[:-2])
                                    backup_info["backup_date"] = '_'.join(parts[-2:])
                            
                            # Add file stats
                            stat = os.stat(backup_path)
                            backup_info["size"] = stat.st_size
                            backup_info["created"] = datetime.fromtimestamp(stat.st_ctime)
                            
                            backups.append(backup_info)
                            
                    except Exception as e:
                        self.logger.warning(f"Could not read backup info from {backup_file}: {e}")
        
        # Sort by creation date, newest first
        backups.sort(key=lambda x: x.get("created", datetime.min), reverse=True)
        return backups
    
    def delete_backup(self, backup_path: str):
        if os.path.exists(backup_path):
            os.remove(backup_path)
            self.logger.info(f"Backup deleted: {backup_path}")
        else:
            self.logger.warning(f"Backup file not found: {backup_path}")
    
    def _cleanup_old_backups(self, instance_name: str):
        backups = self.list_backups(instance_name)
        
        if len(backups) > self.max_backups:
            # Remove oldest backups
            backups_to_remove = backups[self.max_backups:]
            for backup in backups_to_remove:
                self.delete_backup(backup["path"])
                self.logger.info(f"Cleaned up old backup: {backup['filename']}")
    
    def get_backup_size(self, instance_name: str = None) -> int:
        total_size = 0
        backups = self.list_backups(instance_name)
        
        for backup in backups:
            total_size += backup.get("size", 0)
        
        return total_size