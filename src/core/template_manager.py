"""Template directory scanning and metadata extraction."""

import os
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)

TEMPLATE_EXTENSIONS = {".xlsx", ".docx"}


@dataclass
class TemplateInfo:
    """Metadata for a discovered template file."""
    name: str           # Display name (e.g. "Key In COA - Assay")
    path: str           # Absolute file path
    extension: str      # ".xlsx" or ".docx"
    category: str       # "COA", "Allergen", "Flow Chart", "Document"

    @property
    def display_name(self) -> str:
        return f"{self.name} ({self.extension.upper().lstrip('.')})"


def _categorize(name: str) -> str:
    """Infer template category from filename."""
    lower = name.lower()
    if "coa" in lower or "key in" in lower:
        return "COA"
    if "allergen" in lower:
        return "Allergen"
    if "flow" in lower:
        return "Flow Chart"
    return "Document"


def scan_templates(template_dir: str) -> list[TemplateInfo]:
    """Scan a directory for template files and return sorted TemplateInfo list."""
    templates: list[TemplateInfo] = []

    if not os.path.isdir(template_dir):
        log.warning("[TemplateManager] Directory not found: %s", template_dir)
        return templates

    for fname in os.listdir(template_dir):
        _, ext = os.path.splitext(fname)
        if ext.lower() not in TEMPLATE_EXTENSIONS:
            continue
        # Skip temporary/lock files
        if fname.startswith("~$") or fname.startswith("."):
            continue

        name = os.path.splitext(fname)[0].strip(" -")
        fpath = os.path.join(template_dir, fname)
        templates.append(TemplateInfo(
            name=name,
            path=fpath,
            extension=ext.lower(),
            category=_categorize(name),
        ))

    # Sort: COA first, then by name
    category_order = {"COA": 0, "Allergen": 1, "Flow Chart": 2, "Document": 3}
    templates.sort(key=lambda t: (category_order.get(t.category, 9), t.name))

    log.info("[TemplateManager] Found %d templates in %s", len(templates), template_dir)
    return templates
