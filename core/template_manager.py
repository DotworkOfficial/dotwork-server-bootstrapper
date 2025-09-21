import hashlib
import os
import shutil
from datetime import datetime
from typing import List, Dict, Any

from core.backup_manager import BackupManager
from core.variable_substitution import VariableSubstitution
from models.instance import ServerInstance
from models.result import ProvisionResult, FileResult
from models.template import Template
from utils.config import ConfigManager


def __file_to_md5(filepath) -> str:
    hash_md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


def _check_equals(src_filepath, dest_filepath):
    return __file_to_md5(src_filepath) == __file_to_md5(dest_filepath)


class TemplateManager:

    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = templates_dir
        self.substitution = VariableSubstitution()
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        self.backup_manager = BackupManager(self.config.backup_dir, self.config.max_backups)

    def discover_templates(self) -> List[Template]:
        templates = []

        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
            return templates

        for item in os.listdir(self.templates_dir):
            template_path = os.path.join(self.templates_dir, item)
            if os.path.isdir(template_path):
                try:
                    template = Template.from_directory(template_path)
                    templates.append(template)
                except Exception as e:
                    print(f"Failed to load template from {template_path}: {e}")

        return templates

    def get_template_by_name(self, name: str) -> Template:
        templates = self.discover_templates()
        for template in templates:
            if template.name == name:
                return template
        raise ValueError(f"Template '{name}' not found")

    def create_instance(self, template: Template, instance_name: str,
                        output_dir: str, variables: Dict[str, Any]) -> ServerInstance:
        instance_path = os.path.join(output_dir, instance_name)

        if os.path.exists(instance_path):
            raise ValueError(f"Instance directory already exists: {instance_path}")

        # Create instance directory
        os.makedirs(instance_path, exist_ok=True)

        try:
            # Copy template files and substitute variables
            self._copy_template_files(template, instance_path, variables)

            # Create instance metadata
            instance = ServerInstance(
                name=instance_name,
                template_name=template.name,
                path=instance_path,
                variables=variables
            )

            instance.save_metadata()
            return instance

        except Exception as e:
            # Cleanup on failure
            if os.path.exists(instance_path):
                shutil.rmtree(instance_path)
            raise e

    def _copy_template_files(self, template: Template, instance_path: str, variables: Dict[str, Any]):
        for root, dirs, files in os.walk(template.path):
            # Skip template config files
            if 'template.yml' in files:
                files.remove('template.yml')
            if 'template.yaml' in files:
                files.remove('template.yaml')
            
            # Create directory structure
            relative_root = os.path.relpath(root, template.path)
            if relative_root != '.':
                target_dir = os.path.join(instance_path, relative_root)
                os.makedirs(target_dir, exist_ok=True)

            # Copy and process files
            for file in files:
                src_file = os.path.join(root, file)
                relative_path = os.path.relpath(src_file, template.path)
                dest_file = os.path.join(instance_path, relative_path)

                # Ensure destination directory exists
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)

                # Process file content with variable substitution
                self.substitution.process_file(src_file, dest_file, variables)

    def update_instance_from_template(self, instance: ServerInstance, is_dry_run: bool = False) -> ProvisionResult:
        template = self.get_template_by_name(instance.template_name)

        if self.config.auto_backup and not is_dry_run:
            try:
                backup_path = self.backup_manager.create_backup(
                    instance,
                    f"Auto backup before template update to {template.name} v{template.version}"
                )
                print(f"Backup created: {backup_path}")
            except Exception as e:
                print(f"Warning: Failed to create backup: {e}")

        processed_files: List[FileResult] = []
        for root, dirs, files in os.walk(template.path):
            if 'template.yml' in files:
                files.remove('template.yml')
            if 'template.yaml' in files:
                files.remove('template.yaml')

            relative_root = os.path.relpath(root, template.path)
            if relative_root != '.':
                target_dir = os.path.join(instance.path, relative_root)
                os.makedirs(target_dir, exist_ok=True)

            for file in files:
                src_file = os.path.join(root, file)
                relative_path = os.path.relpath(src_file, template.path)
                dest_file = os.path.join(instance.path, relative_path)

                if os.path.exists(dest_file) and _check_equals(src_file, dest_file):
                    processed_files.append(
                        FileResult(
                            path=dest_file,
                            status="Unchanged",
                            reason="same-hash",
                            template=template.name,
                            variables_used={}
                        )
                    )
                    continue

                if is_dry_run:
                    processed_files.append(
                        FileResult(
                            path=dest_file,
                            status="Skipped",
                            reason="dry-run",
                            template=template.name,
                            variables_used={}
                        )
                    )
                    continue

                self.substitution.process_file(src_file, dest_file, instance.variables)
                processed_files.append(
                    FileResult(
                        path=dest_file,
                        status="Replaced",
                        reason="success",
                        template=template.name,
                        variables_used={}
                    )
                )

        instance.updated_at = datetime.now()
        instance.save_metadata()

        return ProvisionResult(
            template=template,
            is_dry_run=is_dry_run,
            processed_files=processed_files,
        )

    def validate_variables(self, template: Template, variables: Dict[str, Any]) -> List[str]:
        errors = []

        for var in template.variables:
            if var.required and var.name not in variables:
                errors.append(f"Required variable '{var.name}' is missing")

            if var.name in variables:
                value = variables[var.name]
                if var.type == 'int':
                    try:
                        int(value)
                    except (ValueError, TypeError):
                        errors.append(f"Variable '{var.name}' must be an integer")
                elif var.type == 'port':
                    try:
                        port = int(value)
                        if not (1 <= port <= 65535):
                            errors.append(f"Variable '{var.name}' must be a valid port (1-65535)")
                    except (ValueError, TypeError):
                        errors.append(f"Variable '{var.name}' must be a valid port number")

        return errors
