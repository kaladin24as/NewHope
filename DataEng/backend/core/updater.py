"""
Project Update Mechanism
=========================

Allows updating existing AntiGravity projects with new providers or configurations
while preserving user modifications.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import yaml
from difflib import unified_diff
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table
from rich.panel import Panel

console = Console()


@dataclass
class FileChange:
    """Represents a change to a file"""
    path: str
    change_type: str  # 'add', 'update', 'delete', 'skip'
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    reason: Optional[str] = None


@dataclass
class UpdatePlan:
    """Plan for updating a project"""
    add_files: List[str] = field(default_factory=list)
    update_files: List[FileChange] = field(default_factory=list)
    remove_files: List[str] = field(default_factory=list)
    skip_files: List[str] = field(default_factory=list)
    
    def has_changes(self) -> bool:
        """Check if there are any changes"""
        return bool(
            self.add_files or 
            self.update_files or 
            self.remove_files
        )


class ProjectMetadata:
    """
    Manages .antigravity.yml metadata file.
    
    This file stores project generation metadata to enable updates.
    """
    
    METADATA_FILE = ".antigravity.yml"
    
    @staticmethod
    def create(
        project_name: str,
        stack: Dict[str, str],
        version: str = "1.0.0",
        generated_at: Optional[str] = None
    ) -> Dict:
        """
        Create metadata dictionary.
        
        Args:
            project_name: Name of the project
            stack: Stack configuration
            version: AntiGravity version
            generated_at: Timestamp (auto-generated if not provided)
        
        Returns:
            Metadata dictionary ready to write
        """
        return {
            "antigravity": {
                "version": version,
                "generated_at": generated_at or datetime.now().isoformat(),
                "last_updated": None
            },
            "project": {
                "name": project_name,
                "stack": stack
            },
            "custom_files": [],  # User-added files
            "modified_files": []  # User-modified generated files
        }
    
    @staticmethod
    def write(project_path: Path, metadata: Dict) -> None:
        """Write metadata to .antigravity.yml"""
        metadata_path = project_path / ProjectMetadata.METADATA_FILE
        
        with open(metadata_path, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
    
    @staticmethod
    def read(project_path: Path) -> Dict:
        """Read metadata from .antigravity.yml"""
        metadata_path = project_path / ProjectMetadata.METADATA_FILE
        
        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Not an AntiGravity project: {ProjectMetadata.METADATA_FILE} not found"
            )
        
        with open(metadata_path) as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def update(project_path: Path, **updates) -> None:
        """Update specific fields in metadata"""
        metadata = ProjectMetadata.read(project_path)
        
        # Update timestamp
        metadata["antigravity"]["last_updated"] = datetime.now().isoformat()
        
        # Apply updates
        for key, value in updates.items():
            if "." in key:
                # Nested key like "project.stack"
                parts = key.split(".")
                current = metadata
                for part in parts[:-1]:
                    current = current[part]
                current[parts[-1]] = value
            else:
                metadata[key] = value
        
        ProjectMetadata.write(project_path, metadata)


class ProjectUpdater:
    """
    Update existing AntiGravity projects.
    
    Handles:
    - Adding new providers
    - Removing providers
    - Updating configurations
    - Detecting user modifications
    - Generating update plans
    - Applying changes selectively
    """
    
    def __init__(self, project_path: Path):
        """
        Initialize updater for a project.
        
        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path)
        
        if not self.project_path.exists():
            raise FileNotFoundError(f"Project not found: {project_path}")
        
        # Load project metadata
        try:
            self.metadata = ProjectMetadata.read(self.project_path)
        except FileNotFoundError:
            raise ValueError(
                f"Not an AntiGravity project. Missing {ProjectMetadata.METADATA_FILE}"
            )
        
        self.current_stack = self.metadata["project"]["stack"]
    
    def analyze_changes(self, new_stack: Dict[str, str]) -> UpdatePlan:
        """
        Analyze what would change with the new stack.
        
        Args:
            new_stack: New stack configuration
        
        Returns:
            UpdatePlan with all detected changes
        """
        plan = UpdatePlan()
        
        # Detect added providers
        for category, provider in new_stack.items():
            if category not in self.current_stack or self.current_stack[category] != provider:
                if provider:
                    plan.add_files.append(f"{category}/{provider}")
        
        # Detect removed providers
        for category, provider in self.current_stack.items():
            if category not in new_stack or new_stack[category] != provider:
                if provider:
                    plan.remove_files.append(f"{category}/{provider}")
        
        return plan
    
    def update(
        self, 
        new_stack: Optional[Dict[str, str]] = None,
        add_providers: Optional[List[Tuple[str, str]]] = None,
        remove_providers: Optional[List[str]] = None,
        interactive: bool = True
    ) -> UpdatePlan:
        """
        Update the project.
        
        Args:
            new_stack: Complete new stack configuration
            add_providers: List of (category, provider) tuples to add
            remove_providers: List of categories to remove
            interactive: If True, ask for confirmation before changes
        
        Returns:
            UpdatePlan that was executed
        """
        # Determine target stack
        target_stack = self.current_stack.copy()
        
        if new_stack:
            target_stack = new_stack
        elif add_providers:
            for category, provider in add_providers:
                target_stack[category] = provider
        elif remove_providers:
            for category in remove_providers:
                target_stack.pop(category, None)
        
        # Generate update plan
        plan = self.analyze_changes(target_stack)
        
        if not plan.has_changes():
            console.print("[yellow]No changes detected.[/yellow]")
            return plan
        
        # Display plan
        self._display_update_plan(plan)
        
        # Confirm with user if interactive
        if interactive:
            if not Confirm.ask("\n[bold cyan]Proceed with update?[/bold cyan]", default=True):
                console.print("[red]Update cancelled.[/red]")
                return plan
        
        # Execute update
        self._execute_update(plan, target_stack)
        
        # Update metadata
        ProjectMetadata.update(
            self.project_path,
            **{"project.stack": target_stack}
        )
        
        console.print("\n[bold green]✓ Project updated successfully![/bold green]")
        
        return plan
    
    def _display_update_plan(self, plan: UpdatePlan) -> None:
        """Display update plan in a nice table"""
        console.print("\n[bold cyan]📋 Update Plan[/bold cyan]")
        console.print("=" * 60)
        
        if plan.add_files:
            console.print("\n[bold green]➕ Components to Add:[/bold green]")
            for component in plan.add_files:
                console.print(f"  • {component}")
        
        if plan.remove_files:
            console.print("\n[bold red]➖ Components to Remove:[/bold red]")
            for component in plan.remove_files:
                console.print(f"  • {component}")
        
        if plan.update_files:
            console.print("\n[bold yellow]📝 Files to Update:[/bold yellow]")
            for change in plan.update_files:
                console.print(f"  • {change.path} ({change.reason})")
        
        if plan.skip_files:
            console.print("\n[bold dim]⊘ Files to Skip:[/bold dim]")
            for file_path in plan.skip_files:
                console.print(f"  • {file_path}")
    
    def _execute_update(self, plan: UpdatePlan, target_stack: Dict[str, str]) -> None:
        """Execute the update plan"""
        from core.engine import TemplateEngine
        import tempfile
        import uuid
        
        # Generate new project in temp directory
        console.print("\n[dim]Generating updated project...[/dim]")
        
        engine = TemplateEngine()
        vfs = engine.generate(
            self.metadata["project"]["name"],
            target_stack,
            str(uuid.uuid4())
        )
        
        # Add new files
        for file_path in vfs.list_files():
            full_path = self.project_path / file_path
            
            if not full_path.exists():
                # New file - add it
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(vfs.get_file(file_path))
                console.print(f"  [green]✓[/green] Added: {file_path}")
    
    def show_diff(self, file_path: str) -> None:
        """Show diff for a specific file"""
        # This would compare current file with what would be generated
        pass
    
    @staticmethod
    def is_antigravity_project(path: Path) -> bool:
        """Check if a directory is an AntiGravity project"""
        return (path / ProjectMetadata.METADATA_FILE).exists()


def update_project_cli(project_path: str, **kwargs) -> None:
    """
    CLI wrapper for updating a project.
    
    Args:
        project_path: Path to the project
        **kwargs: Additional arguments for updater
    """
    try:
        updater = ProjectUpdater(Path(project_path))
        updater.update(**kwargs)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise
