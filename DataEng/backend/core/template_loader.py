"""
Custom Template Support
========================

Allows users to override default templates with custom ones.
Templates are loaded from multiple sources with priority:
1. User templates (~/.antigravity/templates/)
2. Default templates (backend/templates/)
"""

from pathlib import Path
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader, ChoiceLoader
import shutil


class TemplateLoader:
    """
    Multi-source template loader.
    
    Loads templates from user directory first, falls back to defaults.
    """
    
    DEFAULT_TEMPLATES = Path(__file__).parent.parent / "templates"
    USER_TEMPLATES = Path.home() / ".antigravity" / "templates"
    
    def __init__(self, template_dirs: Optional[List[Path]] = None):
        """
        Initialize template loader.
        
        Args:
            template_dirs: Optional list of additional template directories
        """
        self.template_dirs = template_dirs or []
        
        # Priority order: user templates, additional dirs, default templates
        self.all_dirs = [
            self.USER_TEMPLATES,
            *self.template_dirs,
            self.DEFAULT_TEMPLATES
        ]
    
    def get_template_env(self) -> Environment:
        """
        Create Jinja2 environment with multiple loaders.
        
        Returns:
            Jinja2 Environment configured with ChoiceLoader
        """
        loaders = []
        
        for template_dir in self.all_dirs:
            if template_dir.exists():
                loaders.append(FileSystemLoader(str(template_dir)))
        
        if not loaders:
            raise ValueError("No template directories found")
        
        loader = ChoiceLoader(loaders)
        
        return Environment(
            loader=loader,
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    @classmethod
    def override_template(
        cls,
        category: str,
        filename: str,
        source_path: Path
    ) -> Path:
        """
        Override a default template with a custom one.
        
        Args:
            category: Template category (e.g., 'orchestration', 'transformation')
            filename: Template filename
            source_path: Path to the custom template file
        
        Returns:
            Path where template was saved
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source template not found: {source_path}")
        
        # Create user template directory
        target_dir = cls.USER_TEMPLATES / category
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy template
        target_path = target_dir / filename
        shutil.copy2(source_path, target_path)
        
        return target_path
    
    @classmethod
    def reset_template(cls, category: str, filename: str) -> bool:
        """
        Reset a template to default by removing user override.
        
        Args:
            category: Template category
            filename: Template filename
        
        Returns:
            True if reset successful, False if no override existed
        """
        override_path = cls.USER_TEMPLATES / category / filename
        
        if override_path.exists():
            override_path.unlink()
            return True
        
        return False
    
    @classmethod
    def list_overrides(cls) -> List[str]:
        """
        List all user template overrides.
        
        Returns:
            List of template paths that are overridden
        """
        if not cls.USER_TEMPLATES.exists():
            return []
        
        overrides = []
        for category_dir in cls.USER_TEMPLATES.iterdir():
            if category_dir.is_dir():
                for template_file in category_dir.glob("*.j2"):
                    relative_path = template_file.relative_to(cls.USER_TEMPLATES)
                    overrides.append(str(relative_path))
        
        return sorted(overrides)
    
    @classmethod
    def list_default_templates(cls) -> List[str]:
        """
        List all default templates.
        
        Returns:
            List of template paths
        """
        if not cls.DEFAULT_TEMPLATES.exists():
            return []
        
        templates = []
        for template_file in cls.DEFAULT_TEMPLATES.rglob("*.j2"):
            relative_path = template_file.relative_to(cls.DEFAULT_TEMPLATES)
            templates.append(str(relative_path))
        
        return sorted(templates)
    
    @classmethod
    def get_template_info(cls, template_path: str) -> dict:
        """
        Get information about a template.
        
        Args:
            template_path: Relative template path (e.g., 'orchestration/airflow_dag.py.j2')
        
        Returns:
            Dictionary with template information
        """
        default_path = cls.DEFAULT_TEMPLATES / template_path
        user_path = cls.USER_TEMPLATES / template_path
        
        info = {
            "path": template_path,
            "has_default": default_path.exists(),
            "has_override": user_path.exists(),
            "active_source": None,
            "default_path": str(default_path) if default_path.exists() else None,
            "user_path": str(user_path) if user_path.exists() else None
        }
        
        if user_path.exists():
            info["active_source"] = "user"
        elif default_path.exists():
            info["active_source"] = "default"
        
        return info
    
    @classmethod
    def export_template(cls, template_path: str, output_path: Path) -> None:
        """
        Export a template to a file.
        
        Args:
            template_path: Relative template path
            output_path: Where to export the template
        """
        # Find active template
        info = cls.get_template_info(template_path)
        
        if info["active_source"] == "user":
            source = Path(info["user_path"])
        elif info["active_source"] == "default":
            source = Path(info["default_path"])
        else:
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        shutil.copy2(source, output_path)
    
    @classmethod
    def clear_all_overrides(cls) -> int:
        """
        Clear all user template overrides.
        
        Returns:
            Number of templates reset
        """
        if not cls.USER_TEMPLATES.exists():
            return 0
        
        count = 0
        for template_file in cls.USER_TEMPLATES.rglob("*.j2"):
            template_file.unlink()
            count += 1
        
        return count


class TemplateManager:
    """
    High-level template management interface.
    
    Provides convenient methods for template operations.
    """
    
    def __init__(self):
        self.loader = TemplateLoader()
    
    def override(self, template_path: str, custom_template: Path) -> None:
        """
        Override a template with custom version.
        
        Args:
            template_path: Relative path like 'orchestration/airflow_dag.py.j2'
            custom_template: Path to custom template file
        """
        parts = Path(template_path).parts
        
        if len(parts) < 2:
            raise ValueError("Template path must include category and filename")
        
        category = parts[0]
        filename = parts[-1]
        
        TemplateLoader.override_template(category, filename, custom_template)
    
    def reset(self, template_path: str) -> bool:
        """Reset a template to default"""
        parts = Path(template_path).parts
        category = parts[0]
        filename = parts[-1]
        
        return TemplateLoader.reset_template(category, filename)
    
    def list_all(self, include_overrides_only: bool = False) -> List[dict]:
        """
        List all templates with their status.
        
        Args:
            include_overrides_only: If True, only show overridden templates
        
        Returns:
            List of template info dictionaries
        """
        templates = TemplateLoader.list_default_templates()
        overrides =TemplateLoader.list_overrides()
        
        # Combine and deduplicate
        all_templates = sorted(set(templates + overrides))
        
        results = []
        for template_path in all_templates:
            info = TemplateLoader.get_template_info(template_path)
            
            if include_overrides_only and not info["has_override"]:
                continue
            
            results.append(info)
        
        return results
    
    def export(self, template_path: str, output_path: Path) -> None:
        """Export a template"""
        TemplateLoader.export_template(template_path, output_path)
    
    def clear_all(self) -> int:
        """Clear all overrides"""
        return TemplateLoader.clear_all_overrides()
