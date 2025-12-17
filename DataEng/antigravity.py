"""
AntiGravity: End-to-End Data Platform Generator
Python-Native TUI Interface using Textual

Run: python antigravity.py
"""

import sys
import os
from pathlib import Path

# Ensure backend is visible
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Button, Label, RadioSet, RadioButton, Static, Input, Log
from textual.screen import Screen
from textual.binding import Binding

from core.registry import ProviderRegistry
from core.engine import TemplateEngine


def load_providers():
    """Import provider modules to ensure registration"""
    try:
        # Explicit imports to trigger provider registration
        import core.providers.ingestion
        import core.providers.storage
        import core.providers.transformation
        import core.providers.orchestration
        import core.providers.infrastructure
    except ImportError as e:
        print(f"Warning: Could not import providers: {e}")


class ProjectGeneratorApp(App):
    """AntiGravity Project Generator - Textual TUI"""
    
    CSS = """
    /* TRON STYLE - RED & BLACK NEON THEME */
    
    Screen {
        layout: grid;
        grid-size: 2;
        grid-columns: 1fr 1fr;
        background: #0a0a0a;
    }
    
    .sidebar {
        height: 100%;
        width: 100%;
        border-right: thick #ff0000;
        padding: 1;
        background: #000000;
        border-style: solid;
    }
    
    .main {
        height: 100%;
        padding: 1;
        background: #0a0a0a;
    }
    
    .section {
        border: heavy #ff0000;
        padding: 1;
        margin-bottom: 1;
        height: auto;
        background: #1a0000;
        border-style: solid;
    }
    
    .section-title {
        width: 100%;
        text-align: center;
        background: #ff0000;
        color: #000000;
        padding: 1;
        margin-bottom: 1;
        text-style: bold;
    }
    
    Button {
        width: 100%;
        margin-top: 1;
        background: #ff0000;
        color: #000000;
        border: tall #ff3333;
        text-style: bold;
    }
    
    Button:hover {
        background: #ff3333;
        color: #ffffff;
        border: tall #ff6666;
    }
    
    #log_view {
        height: 100%;
        border: tall #ff0000;
        background: #000000;
        color: #ff6666;
        scrollbar-color: #ff0000;
        scrollbar-background: #1a0000;
    }
    
    #status_bar {
        padding: 1;
        background: #1a0000;
        color: #ff3333;
        border-top: solid #ff0000;
    }
    
    Input {
        margin-bottom: 1;
        background: #000000;
        border: tall #ff0000;
    }
    
    Input:focus {
        background: #1a0000;
        border: tall #ff3333;
    }
    
    RadioSet {
        height: auto;
        background: #0a0a0a;
    }
    
    RadioButton {
        background: #1a0000;
        color: #ff6666;
    }
    
    RadioButton:hover {
        background: #2a0000;
        color: #ff3333;
    }
    
    Header {
        background: #ff0000;
        color: #000000;
        text-style: bold;
    }
    
    Footer {
        background: #1a0000;
        color: #ff3333;
    }
    
    Label {
        color: #ff6666;
    }
    
    Static {
        color: #ff9999;
    }
    """

    TITLE = "🚀 AntiGravity: Data Platform Generator"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("g", "generate", "Generate"),
    ]
    
    def on_mount(self) -> None:
        """Called when app is mounted - load providers"""
        load_providers()
        log = self.query_one("#log_view", Log)
        log.write_line("✓ Providers loaded successfully")
        log.write_line("👉 Configure your stack and press 'Generate' (or 'g')")

    def compose(self) -> ComposeResult:
        """Create the UI layout"""
        yield Header(show_clock=True)
        
        # Left Column: Configuration
        with ScrollableContainer(classes="sidebar"):
            yield Label("🔧 Project Configuration", classes="section-title")
            yield Input(
                placeholder="Project Name (e.g., data-lakehouse)",
                id="project_name",
                value="antigravity-project"
            )
            
            providers = ProviderRegistry.get_all_providers()
            
            for category, tools in providers.items():
                if not tools:
                    continue
                    
                # Category Section
                with Container(classes="section"):
                    yield Label(f"📦 {category.upper()}", classes="section-title")
                    with RadioSet(id=f"radio_{category}"):
                        yield RadioButton(
                            "None (Skip)", 
                            value="None", 
                            id=f"{category}_none"
                        )
                        for tool in tools:
                            yield RadioButton(
                                tool, 
                                value=tool, 
                                id=f"{category}_{tool}"
                            )
            
            yield Button("⚡ GENERATE PLATFORM", id="btn_generate", variant="success")

        # Right Column: Logs and Status
        with Container(classes="main"):
            yield Label("📜 Execution Logs", classes="section-title")
            yield Log(id="log_view", highlight=True, auto_scroll=True)
            yield Static(
                "Waiting for configuration...", 
                id="status_bar"
            )

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        if event.button.id == "btn_generate":
            self.run_generation()

    def action_generate(self) -> None:
        """Keyboard shortcut for generation"""
        self.run_generation()

    def run_generation(self):
        """Execute project generation workflow"""
        log = self.query_one("#log_view", Log)
        name_input = self.query_one("#project_name", Input)
        status_bar = self.query_one("#status_bar", Static)
        
        project_name = name_input.value.strip() or "antigravity-project"
        
        log.write_line("─" * 60)
        log.write_line(f"🚀 Starting generation for: [bold cyan]{project_name}[/]")
        log.write_line("─" * 60)
        
        # Build stack from selected options
        stack = {}
        providers = ProviderRegistry.get_all_providers()
        
        for cat in providers.keys():
            try:
                radio = self.query_one(f"#radio_{cat}", RadioSet)
                if radio.pressed_button:
                    val = radio.pressed_button.label.plain
                    stack[cat] = val if val != "None (Skip)" else None
                else:
                    stack[cat] = None
            except Exception:
                stack[cat] = None
        
        log.write_line(f"📊 Selected stack:")
        for k, v in stack.items():
            if v:
                log.write_line(f"  • {k}: [green]{v}[/]")
            else:
                log.write_line(f"  • {k}: [dim]skipped[/]")
        
        try:
            # Generate unique project ID
            import uuid
            project_id = str(uuid.uuid4())[:8]
            
            # Invoke Template Engine
            engine = TemplateEngine()
            
            log.write_line("")
            log.write_line("🔧 Rendering templates...")
            status_bar.update("Rendering templates...")
            
            vfs = engine.generate(project_name, stack, project_id)
            
            log.write_line(f"✓ Generated {len(vfs.list_files())} files")
            
            # Write to disk
            output_path = os.path.join(
                os.getcwd(), 
                "generated_projects", 
                project_name
            )
            
            log.write_line(f"💾 Writing files to: {output_path}")
            vfs.flush(output_path)
            
            log.write_line("")
            log.write_line(f"[bold green]✅ SUCCESS![/]")
            log.write_line(f"[bold green]Project generated at:[/] {output_path}")
            log.write_line("")
            log.write_line("📌 Next steps:")
            log.write_line(f"  cd {output_path}")
            log.write_line("  make up      # Start infrastructure")
            log.write_line("  make logs    # View logs")
            log.write_line("─" * 60)
            
            status_bar.update(f"✅ Generated: {output_path}")
            
        except Exception as e:
            log.write_line("")
            log.write_line(f"[bold red]❌ ERROR:[/] {str(e)}")
            log.write_line("")
            
            import traceback
            log.write_line("[dim]Traceback:[/]")
            for line in traceback.format_exc().split('\n'):
                log.write_line(line)
            
            status_bar.update(f"❌ Generation failed: {str(e)}")


if __name__ == "__main__":
    app = ProjectGeneratorApp()
    app.run()
