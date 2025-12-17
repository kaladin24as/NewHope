"""
Data Source CLI Commands
=======================

Command-line interface for managing data sources.

Usage:
    python source_cli.py add       - Add a new data source
    python source_cli.py list      - List all sources
    python source_cli.py test [name] - Test connection
    python source_cli.py remove [name] - Remove a source
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from core.source_manager import SourceManager
from core.manifest import DataSource

console = Console()


def source_add_interactive():
    """Interactive wizard to add a new data source"""
    console.print("\n[bold cyan]➕ Add New Data Source[/bold cyan]\n")
    
    # Get source name
    source_name = Prompt.ask("Source name (unique identifier)", default="my_api_source")
    source_name = source_name.lower().replace(" ", "_")
    
    # Get source type
    console.print("\n[bold]Select source type:[/bold]")
    source_types = ["api", "database", "file", "stream"]
    for idx, stype in enumerate(source_types, 1):
        console.print(f"  {idx}. {stype}")
    
    type_choice = IntPrompt.ask("Choice", default=1)
    source_type = source_types[type_choice - 1]
    
    # Get connector type based on source type
    if source_type == "api":
        connector = "REST_API"
        console.print(f"\n[green]✓[/green] Using connector: {connector}")
        
        # API-specific configuration
        base_url = Prompt.ask("API base URL", default="https://api.example.com")
        test_endpoint = Prompt.ask("Test endpoint (optional)", default="/")
        endpoint_name = Prompt.ask("Main endpoint name", default="data")
        endpoint_path = Prompt.ask("Main endpoint path", default="/data")
        
        # Authentication
        console.print("\n[bold]Select authentication type:[/bold]")
        auth_types = ["none", "api_key", "bearer", "oauth2", "basic"]
        for idx, atype in enumerate(auth_types, 1):
            console.print(f"  {idx}. {atype}")
        
        auth_choice = IntPrompt.ask("Choice", default=1)
        auth_type = auth_types[auth_choice - 1]
        
        auth_config = {"type": auth_type}
        
        if auth_type == "api_key":
            location = Prompt.ask("API key location (header/query)", default="header")
            key_name = Prompt.ask("Key/header name", default="X-API-Key")
            auth_config["location"] = location
            auth_config["key_name"] = key_name
        
        elif auth_type == "oauth2":
            token_url = Prompt.ask("Token URL")
            auth_config["token_url"] = token_url
        
        config = {
            "base_url": base_url,
            "test_endpoint": test_endpoint,
            "endpoint_name": endpoint_name,
            "endpoint": endpoint_path,
            "endpoints": [
                {
                    "name": endpoint_name,
                    "path": endpoint_path,
                    "method": "GET"
                }
            ]
        }
    
    else:
        console.print(f"[yellow]Source type '{source_type}' configuration not yet implemented[/yellow]")
        return
    
    # Schedule
    schedule = Prompt.ask("Cron schedule (or press Enter for default)", default="0 */6 * * *")
    
    # Create data source
    source = DataSource(
        name=source_name,
        type=source_type,
        connector=connector,
        config=config,
        auth_config=auth_config,
        schedule=schedule if schedule else None,
        enabled=True
    )
    
    # Display summary
    console.print("\n[bold green]Source Configuration Summary:[/bold green]")
    table = Table(show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="yellow")
    
    table.add_row("Name", source.name)
    table.add_row("Type", source.type)
    table.add_row("Connector", source.connector)
    table.add_row("Base URL", config.get("base_url", "N/A"))
    table.add_row("Auth", auth_config.get("type", "none"))
    table.add_row("Schedule", source.schedule or "Manual")
    
    console.print(table)
    
    # Confirm
    if not Confirm.ask("\n[bold]Add this source?[/bold]", default=True):
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    # Save source
    try:
        manager = SourceManager()
        manager.add_source(source)
        console.print(f"\n[bold green]✅ Source '{source_name}' added successfully![/bold green]\n")
        
        # Ask if user wants to test connection
        if Confirm.ask("Test connection now?", default=True):
            source_test(source_name)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def source_list():
    """List all configured data sources"""
    console.print("\n[bold cyan]📋 Data Sources[/bold cyan]\n")
    
    try:
        manager = SourceManager()
        sources = manager.list_sources()
        
        if not sources:
            console.print("[yellow]No data sources configured[/yellow]")
            console.print("\nAdd a source with: [cyan]python source_cli.py add[/cyan]\n")
            return
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Name", style="cyan", width=20)
        table.add_column("Type", style="green", width=12)
        table.add_column("Connector", style="blue", width=15)
        table.add_column("Base URL", style="white", width=30)
        table.add_column("Schedule", style="yellow", width=15)
        table.add_column("Status", style="white", width=12)
        
        for idx, source in enumerate(sources, 1):
            status = "✅ Enabled" if source.enabled else "⏸️  Disabled"
            base_url = source.config.get("base_url", "N/A")
            # Truncate long URLs
            if len(base_url) > 28:
                base_url = base_url[:25] + "..."
            
            table.add_row(
                str(idx),
                source.name,
                source.type,
                source.connector,
                base_url,
                source.schedule or "[dim]Manual[/dim]",
                status
            )
        
        console.print(table)
        console.print(f"\n[green]Total: {len(sources)} source(s)[/green]\n")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def source_test(source_name: str = None):
    """Test connection to a data source"""
    console.print("\n[bold cyan]🔌 Test Data Source Connection[/bold cyan]\n")
    
    try:
        manager = SourceManager()
        
        # If no source name provided, list and ask
        if not source_name:
            sources = manager.list_sources()
            if not sources:
                console.print("[yellow]No sources configured[/yellow]")
                return
            
            console.print("Available sources:")
            for idx, source in enumerate(sources, 1):
                console.print(f"  {idx}. {source.name}")
            
            choice = IntPrompt.ask("Select source to test", default=1)
            if 1 <= choice <= len(sources):
                source_name = sources[choice - 1].name
            else:
                console.print("[red]Invalid choice[/red]")
                return
        
        # Test connection
        console.print(f"Testing connection to [cyan]{source_name}[/cyan]...\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Connecting...", total=None)
            success, message = manager.test_source(source_name)
            progress.update(task, description="[green]✓ Complete[/green]")
        
        console.print(f"\n{message}\n")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def source_remove(source_name: str = None):
    """Remove a data source"""
    console.print("\n[bold red]🗑️  Remove Data Source[/bold red]\n")
    
    try:
        manager = SourceManager()
        
        # If no source name provided, list and ask
        if not source_name:
            sources = manager.list_sources()
            if not sources:
                console.print("[yellow]No sources configured[/yellow]")
                return
            
            console.print("Available sources:")
            for idx, source in enumerate(sources, 1):
                console.print(f"  {idx}. {source.name}")
            
            choice = IntPrompt.ask("Select source to remove", default=1)
            if 1 <= choice <= len(sources):
                source_name = sources[choice - 1].name
            else:
                console.print("[red]Invalid choice[/red]")
                return
        
        # Confirm removal
        if not Confirm.ask(f"[bold red]Remove source '{source_name}'?[/bold red]", default=False):
            console.print("[yellow]Cancelled[/yellow]")
            return
        
        # Remove source
        if manager.remove_source(source_name):
            console.print(f"\n[green]✅ Source '{source_name}' removed[/green]\n")
        else:
            console.print(f"\n[yellow]Source '{source_name}' not found[/yellow]\n")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def show_help():
    """Show help message"""
    console.print("""
[bold cyan]Data Source Management CLI[/bold cyan]

[yellow]Commands:[/yellow]
  [cyan]add[/cyan]           Add a new data source (interactive wizard)
  [cyan]list[/cyan]          List all configured data sources
  [cyan]test[/cyan] [name]   Test connection to a data source
  [cyan]remove[/cyan] [name] Remove a data source

[yellow]Examples:[/yellow]
  python source_cli.py add
  python source_cli.py list
  python source_cli.py test my_api
  python source_cli.py remove my_api

[yellow]Environment Variables:[/yellow]
  After adding a source, set the required authentication variables:
  - For API Key: {SOURCE_NAME}_API_KEY
  - For Bearer: {SOURCE_NAME}_API_TOKEN
  - For OAuth2: {SOURCE_NAME}_CLIENT_ID, {SOURCE_NAME}_CLIENT_SECRET
  - For Basic: {SOURCE_NAME}_USERNAME, {SOURCE_NAME}_PASSWORD
""")


def main():
    """Main entry point"""
    try:
        if len(sys.argv) < 2:
            show_help()
            return
        
        command = sys.argv[1].lower()
        
        if command == "add":
            source_add_interactive()
        
        elif command == "list":
            source_list()
        
        elif command == "test":
            source_name = sys.argv[2] if len(sys.argv) > 2 else None
            source_test(source_name)
        
        elif command == "remove":
            source_name = sys.argv[2] if len(sys.argv) > 2 else None
            source_remove(source_name)
        
        elif command in ["help", "-h", "--help"]:
            show_help()
        
        else:
            console.print(f"[red]Unknown command: {command}[/red]")
            show_help()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        sys.exit(0)
    
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
