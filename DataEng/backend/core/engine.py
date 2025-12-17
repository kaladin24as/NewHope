import os
import shutil
import yaml
import zipfile
import io
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any, Optional

from core.registry import ProviderRegistry
from core.manifest import ProjectContext
from core.config_resolver import DependencyResolver, AutoWiring
from core.compatibility import StackValidator
from core.stack_validator import StackValidator as NewStackValidator
from core.secret_registry import SecretRegistry
from core.template_context_builder import TemplateContextBuilder
from core.env_manager import EnvironmentManager
from core.updater import ProjectMetadata


class VirtualFileSystem:
    """
    In-memory file system for generated project files.
    Enables inspection, modification, and flexible output (disk, ZIP, etc.)
    """
    
    def __init__(self):
        self.files: Dict[str, str] = {}  # path -> content mapping
    
    def add_file(self, path: str, content: str) -> None:
        """Add a file to the virtual filesystem"""
        self.files[path] = content
    
    def get_file(self, path: str) -> Optional[str]:
        """Get file content by path"""
        return self.files.get(path)
    
    def list_files(self) -> list[str]:
        """List all file paths in the VFS"""
        return list(self.files.keys())
    
    def flush(self, output_dir: str) -> str:
        """
        Write all files from VFS to disk.
        
        Args:
            output_dir: Base directory to write files to
            
        Returns:
            Path to the output directory
        """
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)
        
        for file_path, content in self.files.items():
            full_path = os.path.join(output_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return output_dir
    
    def to_zip(self, output_path: str) -> str:
        """
        Create a ZIP file from all VFS contents.
        
        Args:
            output_path: Path where the ZIP file should be created
            
        Returns:
            Path to the created ZIP file
        """
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path, content in self.files.items():
                zipf.writestr(file_path, content)
        
        return output_path
    
    def to_bytes_zip(self) -> bytes:
        """
        Create a ZIP file in memory and return as bytes.
        Useful for web downloads.
        
        Returns:
            ZIP file contents as bytes
        """
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path, content in self.files.items():
                zipf.writestr(file_path, content)
        
        return zip_buffer.getvalue()

class TemplateEngine:
    def __init__(self, template_dir: str = "templates"):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.template_dir = os.path.join(base_path, template_dir)
        self.env = Environment(loader=FileSystemLoader(self.template_dir))

    def generate(self, project_name: str, stack: dict, project_id: str) -> VirtualFileSystem:
        """
        Generate project files into a Virtual File System.
        
        Uses a 4-phase approach:
        1. Initialization: Instantiate generators and register services
        2. Validation: Validate configurations and dependencies
        3. Auto-configuration: Wire services together  
        4. Generation: Generate components in topological order
        
        Args:
            project_name: Name of the project
            stack: Dictionary of selected tools by category
            project_id: Unique identifier for this project
            
        Returns:
            VirtualFileSystem containing all generated files
        """
        vfs = VirtualFileSystem()
        
        # Initialize ProjectContext
        context = ProjectContext(project_name=project_name, stack=stack)
        
        # Generate secrets using SecretRegistry (auto-wiring!)
        secrets = SecretRegistry.get_secrets_for_stack(stack, project_name)
        context.secrets = secrets  # Store in context for templates
        
        print(f"\n🚀 Generating project: {project_name}")
        print(f"📦 Stack: {stack}")
        print(f"🔐 Auto-generated {len(secrets)} secret(s) with auto-wiring")
        print("\n" + "="*60)
        
        # ===================================================================
        # PHASE 1: INITIALIZATION - Register Services
        # ===================================================================
        print("\n🔧 PHASE 1: Initialization")
        print("-" * 60)
        
        generators = {}
        dependency_resolver = DependencyResolver()
        
        # Instantiate all generators and register their services
        for category, tool_name in stack.items():
            if not tool_name:
                continue
            
            try:
                component_id = f"{category}:{tool_name}"
                provider_cls = ProviderRegistry.get_provider(category, tool_name)
                generator = provider_cls(self.env)
                generators[component_id] = generator
                
                print(f"  ✓ Loaded {component_id}")
                
                # Register services this component provides
                generator.register_services(context)
                print(f"    → Registered services")
                
                # Add dependencies to resolver
                dependencies = generator.get_dependencies()
                dependency_resolver.add_component(component_id, dependencies)
                if dependencies:
                    print(f"    → Dependencies: {', '.join(dependencies)}")
                
            except ValueError as e:
                print(f"  ⚠ Warning: {e}")
                continue
            except Exception as e:
                print(f"  ❌ Error loading {category}:{tool_name} - {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n  📊 Registered {len(context.connections)} service(s)")
        for conn in context.connections:
            caps = ", ".join(conn.capabilities) if conn.capabilities else "none"
            print(f"    • {conn.name} ({conn.type}) - capabilities: {caps}")
        
        # ===================================================================
        # PHASE 2: VALIDATION
        # ===================================================================
        print("\n🔍 PHASE 2: Validation")
        print("-" * 60)
        
        # Validate stack compatibility using new validator
        is_valid, errors, warnings = NewStackValidator.validate_stack(stack)
        
        print("  🔍 Stack compatibility check...")
        
        if errors:
            print("  ❌ Stack validation errors:")
            for error in errors:
                print(f"     {error}")
            raise ValueError(f"Stack validation failed: {'; '.join(errors)}")
        
        if warnings:
            print("  ⚠ Stack validation warnings:")
            for warning in warnings:
                print(f"     {warning}")
        
        # Validate each component's configuration
        validation_errors = []
        for component_id, generator in generators.items():
            is_valid, error_msg = generator.validate_configuration(context)
            if not is_valid:
                validation_errors.append(f"{component_id}: {error_msg}")
                print(f"  ❌ {component_id}: {error_msg}")
            else:
                print(f"  ✓ {component_id}: Valid")
        
        if validation_errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(validation_errors))
        
        # Validate service connections
        connection_errors = context.validate_connections()
        if connection_errors:
            print("  ⚠ Connection warnings:")
            for error in connection_errors:
                print(f"     {error}")
        
        # Resolve dependencies and get generation order
        ordered_components, dep_errors = dependency_resolver.resolve(generators, context)
        if dep_errors:
            print("  ❌ Dependency resolution errors:")
            for error in dep_errors:
                print(f"     {error}")
            raise ValueError(f"Dependency resolution failed: {'; '.join(dep_errors)}")
        
        print(f"\n  📑 Generation order: {' → '.join(ordered_components)}")
        
        # ===================================================================
        # PHASE 3: AUTO-CONFIGURATION
        # ===================================================================
        print("\n⚙️  PHASE 3: Auto-configuration")
        print("-" * 60)
        
        context.auto_configure_services()
        
        # Auto-wire components based on their categories
        for component_id in ordered_components:
            category = component_id.split(":")[0]
            generator = generators[component_id]
            auto_config = AutoWiring.auto_wire_component(generator, category, context)
            if auto_config:
                print(f"  🔗 Auto-wired {component_id}")
                for key in auto_config.keys():
                    print(f"     • {key}")
        
        # ===================================================================
        # PHASE 4: GENERATION
        # ===================================================================
        print("\n📝 PHASE 4: Generation")
        print("-" * 60)
        
        # Base Docker Compose structure with Network Glue
        docker_compose = {
            "version": "3.8",
            "services": {},
            "volumes": {},
            "networks": {
                "antigravity_net": {
                    "driver": "bridge"
                }
            }
        }

        # 1. Render Base README to VFS
        readme_content = self._render_readme_to_string(project_name, stack)
        if readme_content:
            vfs.add_file("README.md", readme_content)
            print("  ✓ Generated README.md")

        # Track active components for diagram generation
        active_components = []

        # 2. Generate components in topological order
        for component_id in ordered_components:
            category, tool_name = component_id.split(":", 1)
            generator = generators[component_id]
            active_components.append({'category': category, 'name': tool_name})
            
            try:
                print(f"  🔨 Generating {component_id}...")
                
                # Generate component files to VFS
                import tempfile
                with tempfile.TemporaryDirectory() as temp_dir:
                    generator.generate(temp_dir, config={"project_context": context})
                    
                    # Read generated files into VFS
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, temp_dir)
                            with open(file_path, 'r', encoding='utf-8') as f:
                                vfs.add_file(rel_path, f.read())
                
                # Merge Docker Compose services
                services = generator.get_docker_service_definition(context)
                if services:
                    print(f"    → Added {len(services)} Docker service(s)")
                    # Glue: Inject shared network into every service
                    for service_name, service_config in services.items():
                        if "networks" not in service_config:
                            service_config["networks"] = []
                        service_config["networks"].append("antigravity_net")
                        
                    docker_compose["services"].update(services)
                
                # Merge Docker Compose volumes
                volumes = generator.get_docker_compose_volumes()
                if volumes:
                    print(f"    → Added {len(volumes)} volume(s)")
                    docker_compose["volumes"].update(volumes)
                    
                print(f"  ✓ {component_id} completed")
                
            except Exception as e:
                print(f"  ❌ Error generating component {component_id} - {e}")
                import traceback
                traceback.print_exc()
                continue

        # 3. Add docker-compose.yml to VFS
        if docker_compose["services"]:
            compose_content = yaml.dump(docker_compose, default_flow_style=False, sort_keys=False)
            vfs.add_file("docker-compose.yml", compose_content)
            print(f"  ✓ Generated docker-compose.yml with {len(docker_compose['services'])} services")
        
        # 4. Add Makefile to VFS
        makefile_content = self._render_makefile_to_string(project_name, stack)
        if makefile_content:
            vfs.add_file("Makefile", makefile_content)
            print("  ✓ Generated Makefile")
        
        # 5. Add DevContainer configuration to VFS
        devcontainer_content = self._render_devcontainer_to_string(project_name, stack)
        if devcontainer_content:
            vfs.add_file(".devcontainer/devcontainer.json", devcontainer_content)
            print("  ✓ Generated .devcontainer/devcontainer.json")
            
        # 6. Generate Architecture Diagram to VFS
        arch_content = self._generate_architecture_doc_to_string(context, active_components)
        if arch_content:
            vfs.add_file("ARCHITECTURE.md", arch_content)
            print("  ✓ Generated ARCHITECTURE.md")
        
        # 7. Generate multi-environment .env files
        env_files = EnvironmentManager.generate_all_env_files(context)
        for env_name, env_content in env_files.items():
            if env_name == "example":
                vfs.add_file(".env.example", env_content)
            else:
                vfs.add_file(f".env.{env_name}", env_content)
            print(f"  ✓ Generated .env.{env_name if env_name != 'example' else 'example'}")
        
        # 8. Add environment switcher script
        switcher_script = EnvironmentManager.generate_env_switcher_script()
        vfs.add_file("scripts/switch-env.sh", switcher_script)
        print("  ✓ Generated scripts/switch-env.sh")
        
        # 9. Add .gitignore additions
        gitignore_additions = EnvironmentManager.generate_gitignore_additions()
        vfs.add_file(".gitignore", gitignore_additions)
        print("  ✓ Generated .gitignore")
        
        # 10. Add project metadata for future updates
        metadata = ProjectMetadata.create(
            project_name=project_name,
            stack=stack,
            version="1.0.0"
        )
        metadata_content = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
        vfs.add_file(".antigravity.yml", metadata_content)
        print("  ✓ Generated .antigravity.yml (update metadata)")
        
        # ===================================================================
        # SUMMARY
        # ===================================================================
        print("\n" + "="*60)
        print("\n✅ PROJECT GENERATION COMPLETE!")
        print(f"\n📊 Summary:")
        print(f"  • Components generated: {len(active_components)}")
        print(f"  • Services registered: {len(context.connections)}")
        print(f"  • Docker services: {len(docker_compose['services'])}")
        print(f"  • Files generated: {len(vfs.list_files())}")
        print(f"\n🎉 Project '{project_name}' is ready!")
        print("=" * 60 + "\n")

        return vfs

    def _render_readme_to_string(self, project_name: str, stack: dict) -> Optional[str]:
        """Render README template to string"""
        try:
            template = self.env.get_template("common/README.md.j2")
            return template.render(project_name=project_name, stack=stack)
        except Exception as e:
            print(f"Warning: Could not render base README: {e}")
            return None
    
    def _render_makefile_to_string(self, project_name: str, stack: dict) -> Optional[str]:
        """Render Makefile template to string"""
        try:
            template = self.env.get_template("common/Makefile.j2")
            return template.render(project_name=project_name, stack=stack)
        except Exception as e:
            print(f"Warning: Could not render Makefile: {e}")
            return None
    
    def _render_devcontainer_to_string(self, project_name: str, stack: dict) -> Optional[str]:
        """Render devcontainer.json template to string"""
        try:
            template = self.env.get_template("common/devcontainer.json.j2")
            return template.render(project_name=project_name, stack=stack)
        except Exception as e:
            print(f"Warning: Could not render devcontainer.json: {e}")
            return None

    def _generate_architecture_doc_to_string(self, context: ProjectContext, components: list) -> Optional[str]:
        """Generate architecture documentation as string"""
        try:
            from core.utils.diagram import generate_architecture_diagram
            diagram_content = generate_architecture_diagram(context, components)
            
            doc = "# Project Architecture\n\n"
            doc += "This document is automatically generated based on the selected components.\n\n"
            doc += "```mermaid\n"
            doc += diagram_content
            doc += "\n```\n"
            return doc
        except Exception as e:
            print(f"Warning: Could not generate ARCHITECTURE.md: {e}")
            return None
