"""
AntiGravity CLI - Interactive Data Project Generator
=====================================================

A beautiful terminal interface for generating data engineering projects.

Usage:
    python cli.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich import print as rprint
from rich.markdown import Markdown

from core.engine import TemplateEngine
from core.registry import ProviderRegistry
from core.profiles import ConfigurationProfile

# Initialize rich console
console = Console()


def print_banner():
    """Display welcome banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     █████╗ ███╗   ██╗████████╗██╗ ██████╗ ██████╗  █████╗    ║
    ║    ██╔══██╗████╗  ██║╚══██╔══╝██║██╔════╝ ██╔══██╗██╔══██╗   ║
    ║    ███████║██╔██╗ ██║   ██║   ██║██║  ███╗██████╔╝███████║   ║
    ║    ██╔══██║██║╚██╗██║   ██║   ██║██║   ██║██╔══██╗██╔══██║   ║
    ║    ██║  ██║██║ ╚████║   ██║   ██║╚██████╔╝██║  ██║██║  ██║   ║
    ║    ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ║
    ║                                                               ║
    ║            🚀 Data Project Generator - CLI Edition           ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")
    console.print(
        "\n[yellow]Welcome to AntiGravity![/yellow] Generate production-ready data projects in seconds.\n"
    )


def get_available_providers():
    """Get all registered providers by category"""
    try:
        # Import all providers to trigger registration
        from core.providers import ingestion, storage, transformation, orchestration, infrastructure
        
        return ProviderRegistry.get_all_providers()
    except Exception as e:
        console.print(f"[red]Error loading providers: {e}[/red]")
        return {}


def select_from_menu(category: str, options: list) -> str:
    """Display menu and get user selection"""
    
    if not options:
        console.print(f"[yellow]No providers available for {category}[/yellow]")
        return None
    
    # Display options
    console.print(f"\n[bold cyan]Select {category.upper()}:[/bold cyan]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=6)
    table.add_column("Option", style="cyan")
    
    for idx, option in enumerate(options, 1):
        table.add_row(str(idx), option)
    
    table.add_row(str(len(options) + 1), "[dim]Skip (None)[/dim]")
    
    console.print(table)
    
    # Get user choice
    while True:
        choice = IntPrompt.ask(
            f"Choose {category}",
            default=1,
            show_default=True
        )
        
        if 1 <= choice <= len(options):
            selected = options[choice - 1]
            console.print(f"[green]✓[/green] Selected: {selected}\n")
            return selected
        elif choice == len(options) + 1:
            console.print(f"[yellow]⊘[/yellow] Skipping {category}\n")
            return None
        else:
            console.print("[red]Invalid choice, try again[/red]")


def display_configuration_summary(project_name: str, stack: dict):
    """Display selected configuration in a beautiful table"""
    
    console.print("\n" + "=" * 70)
    console.print("[bold green]Project Configuration Summary[/bold green]", justify="center")
    console.print("=" * 70 + "\n")
    
    # Project info
    info_table = Table(show_header=False, box=None)
    info_table.add_column("Key", style="bold cyan", width=20)
    info_table.add_column("Value", style="yellow")
    
    info_table.add_row("Project Name", project_name)
    console.print(info_table)
    
    # Stack configuration
    console.print("\n[bold cyan]Technology Stack:[/bold cyan]\n")
    
    stack_table = Table(show_header=True, header_style="bold magenta")
    stack_table.add_column("Category", style="cyan", width=20)
    stack_table.add_column("Tool", style="green")
    
    for category, tool in stack.items():
        if tool:
            stack_table.add_row(category.capitalize(), tool)
        else:
            stack_table.add_row(category.capitalize(), "[dim]None[/dim]")
    
    console.print(stack_table)
    console.print("\n" + "=" * 70 + "\n")


def display_generated_files(vfs):
    """Display generated files in a tree structure"""
    
    console.print("\n[bold green]✓ Generated Files:[/bold green]\n")
    
    # Build file tree
    tree = Tree("📁 [bold cyan]" + "Your Project" + "[/bold cyan]")
    
    files = vfs.list_files()
    
    # Group files by directory
    dirs = {}
    for file_path in sorted(files):
        parts = Path(file_path).parts
        
        if len(parts) == 1:
            # Root file
            tree.add(f"📄 {parts[0]}")
        else:
            # File in subdirectory
            dir_name = parts[0]
            if dir_name not in dirs:
                dirs[dir_name] = tree.add(f"📁 [cyan]{dir_name}[/cyan]")
            
            # Add file to directory
            file_name = "/".join(parts[1:])
            
            if "." in file_name:
                # It's a file
                dirs[dir_name].add(f"📄 {file_name}")
            else:
                # It's a subdirectory
                sub_tree = dirs[dir_name].add(f"📁 [cyan]{file_name}[/cyan]")
    
    console.print(tree)
    console.print(f"\n[green]Total: {len(files)} files generated[/green]\n")


def main():
    """Main CLI application"""
    
    try:
        # Display banner
        print_banner()
        
        # Ask if user wants to load a profile/preset
        console.print("\n[bold cyan]🎯 Quick Start Options:[/bold cyan]")
        
        use_profile = Confirm.ask(
            "Would you like to load a preset or saved profile?",
            default=False
        )
        
        stack = {}
        
        if use_profile:
            # Show available presets and profiles
            all_profiles = ConfigurationProfile.list_profiles(include_presets=True)
            presets = ConfigurationProfile.get_preset_names()
            
            console.print("\n[bold green]Available Presets:[/bold green]")
            preset_table = Table(show_header=True, header_style="bold magenta")
            preset_table.add_column("#", style="dim", width=6)
            preset_table.add_column("Name", style="cyan")
            preset_table.add_column("Description", style="white")
            
            for idx, preset_name in enumerate(presets, 1):
                preset = ConfigurationProfile.load(preset_name)
                preset_table.add_row(str(idx), preset.name, preset.description[:50])
            
            console.print(preset_table)
            
            choice = IntPrompt.ask(
                "Select preset (or 0 for custom)",
                default=1
            )
            
            if 1 <= choice <= len(presets):
                selected_preset = presets[choice - 1]
                profile = ConfigurationProfile.load(selected_preset)
                stack = profile.stack.copy()
                console.print(f"\n[green]✓[/green] Loaded preset: [yellow]{profile.name}[/yellow]")
                console.print(f"[dim]{profile.description}[/dim]\n")
        
        # Get project name
        project_name = Prompt.ask(
            "[bold cyan]Enter project name[/bold cyan]",
            default="my_data_project"
        )
        
        # Validate project name
        if not project_name.replace("_", "").replace("-", "").isalnum():
            console.print("[red]Project name can only contain letters, numbers, dashes, and underscores[/red]")
            return
        
        console.print(f"\n[green]✓[/green] Project name: [yellow]{project_name}[/yellow]")
        
        # Get available providers
        console.print("\n[dim]Loading available tools...[/dim]")
        providers = get_available_providers()
        
        if not providers:
            console.print("[red]No providers found. Please check your installation.[/red]")
            return
        
        # Build stack configuration (or customize loaded profile)
        if not stack or Confirm.ask("\nCustomize stack?", default=False):
            # Select ingestion tool
            if providers.get("ingestion"):
                current = stack.get("ingestion")
                if current:
                    console.print(f"[dim]Current: {current}[/dim]")
                stack["ingestion"] = select_from_menu("Ingestion", providers["ingestion"])
            
            # Select storage
            if providers.get("storage"):
                current = stack.get("storage")
                if current:
                    console.print(f"[dim]Current: {current}[/dim]")
                stack["storage"] = select_from_menu("Storage", providers["storage"])
            
            # Select transformation
            if providers.get("transformation"):
                current = stack.get("transformation")
                if current:
                    console.print(f"[dim]Current: {current}[/dim]")
                stack["transformation"] = select_from_menu("Transformation", providers["transformation"])
            
            # Select orchestration
            if providers.get("orchestration"):
                current = stack.get("orchestration")
                if current:
                    console.print(f"[dim]Current: {current}[/dim]")
                stack["orchestration"] = select_from_menu("Orchestration", providers["orchestration"])
            
            # Select infrastructure
            if providers.get("infrastructure"):
                current = stack.get("infrastructure")
                if current:
                    console.print(f"[dim]Current: {current}[/dim]")
                stack["infrastructure"] = select_from_menu("Infrastructure (IaC)", providers["infrastructure"])
        
        # Display summary
        display_configuration_summary(project_name, stack)
        
        # Ask if user wants to save this configuration
        if Confirm.ask("\n[cyan]Save this configuration as a profile?[/cyan]", default=False):
            profile_name = Prompt.ask("Profile name", default=project_name + "_profile")
            profile_desc = Prompt.ask("Description (optional)", default="")
            
            try:
                ConfigurationProfile.save(
                    name=profile_name,
                    stack=stack,
                    description=profile_desc
                )
                console.print(f"[green]✓[/green] Profile '{profile_name}' saved!\n")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not save profile: {e}[/yellow]\n")
        
        # Confirm generation
        if not Confirm.ask("[bold yellow]Proceed with project generation?[/bold yellow]", default=True):
            console.print("[red]Cancelled[/red]")
            return
        
        # Generate project
        console.print("\n[bold green]Generating project...[/bold green]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Generating files...", total=None)
            
            # Initialize template engine
            engine = TemplateEngine()
            
            # Generate project to VFS
            import uuid
            project_id = str(uuid.uuid4())
            vfs = engine.generate(project_name, stack, project_id)
            
            progress.update(task, description="Writing files to disk...")
            
            # Write to disk
            output_dir = Path.cwd() / "generated_projects" / project_name
            vfs.flush(str(output_dir))
            
            progress.update(task, description="[green]✓ Complete![/green]")
        
        # Display generated files
        display_generated_files(vfs)
        
        # Success message
        success_panel = Panel(
            f"""[bold green]✨ Project generated successfully![/bold green]

[cyan]Location:[/cyan] {output_dir.absolute()}

[yellow]Next steps:[/yellow]
1. Navigate to project: [cyan]cd {output_dir}[/cyan]
2. Review the generated files
3. Copy .env.example to .env and configure credentials
4. Run [cyan]docker-compose up[/cyan] to start services
5. Start building! 🚀

For documentation, check the README.md file.""",
            border_style="green",
            padding=(1, 2)
        )
        
        console.print(success_panel)
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
