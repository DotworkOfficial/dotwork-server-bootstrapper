from dataclasses import dataclass, field
from typing import Dict, Any, List

from models.template import Template

# TODO: create status, reason enum
@dataclass
class FileResult:
    path: str
    status: str          # Replaced | Skipped | Created | Unchanged | Error
    reason: str          # e.g., "same-hash", "ignore-rule", "user-skip", "permission-denied"
    template: str        # template name or ID
    variables_used: Dict[str, Any]

@dataclass
class ProvisionResult:
    template: Template
    is_dry_run: bool
    processed_files: List[FileResult]


