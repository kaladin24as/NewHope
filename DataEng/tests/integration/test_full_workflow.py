"""
End-to-End Integration Tests
=============================

Tests the complete workflow from project generation to validation.
"""

import pytest
import uuid
import yaml
import tempfile
import shutil
from pathlib import Path
from core.engine import TemplateEngine, VirtualFileSystem
from core.registry import ProviderRegistry
from core.manifest import ProjectContext


class TestFullWorkflow:
    """Integration tests for complete project generation workflow"""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory"""
        temp_dir = tempfile.mkdtemp(prefix="antigravity_test_")
        yield Path(temp_dir)
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def engine(self):
        """Get template engine instance"""
        return TemplateEngine()
    
    def test_minimal_stack_generation(self, engine):
        """Test generating a minimal stack (storage only)"""
        project_name = "minimal_test"
        stack = {
            "storage": "PostgreSQL"
        }
        
        vfs = engine.generate(project_name, stack, str(uuid.uuid4()))
        
        # Verify VFS contains files
        files = vfs.list_files()
        assert len(files) > 0, "No files generated"
        
        # Verify critical files exist
        assert "docker-compose.yml" in files
        assert "README.md" in files
        assert ".env.example" in files
    
    def test_full_stack_generation(self, engine):
        """Test generating a complete stack"""
        project_name = "full_stack_test"
        stack = {
            "ingestion": "DLT",
            "storage": "PostgreSQL",
            "transformation": "dbt",
            "orchestration": "Airflow",
            "infrastructure": "terraform"
        }
        
        vfs = engine.generate(project_name, stack, str(uuid.uuid4()))
        
        files = vfs.list_files()
        
        # Verify component-specific files
        assert any("dlt" in f.lower() or "ingestion" in f.lower() for f in files), \
            "DLT files not found"
        assert any("dbt" in f.lower() for f in files), \
            "dbt files not found"
        assert any("dag" in f.lower() or "airflow" in f.lower() for f in files), \
            "Airflow files not found"
        assert any("terraform" in f.lower() or ".tf" in f for f in files), \
            "Terraform files not found"
    
    def test_docker_compose_is_valid_yaml(self, engine):
        """Test that generated docker-compose.yml is valid YAML"""
        stack = {
            "storage": "PostgreSQL",
            "orchestration": "Airflow"
        }
        
        vfs = engine.generate("yaml_test", stack, str(uuid.uuid4()))
        
        compose_content = vfs.get_file("docker-compose.yml")
        assert compose_content is not None
        
        # Parse as YAML - should not raise
        try:
            parsed = yaml.safe_load(compose_content)
            assert parsed is not None
            assert "services" in parsed or "version" in parsed
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in docker-compose.yml: {e}")
    
    def test_env_file_contains_required_vars(self, engine):
        """Test that .env.example contains all required variables"""
        stack = {
            "storage": "PostgreSQL",
            "orchestration": "Airflow"
        }
        
        vfs = engine.generate("env_test", stack, str(uuid.uuid4()))
        
        env_content = vfs.get_file(".env.example")
        assert env_content is not None
        
        # Should contain database variables
        assert "POSTGRES" in env_content
        assert "PASSWORD" in env_content or "PWD" in env_content
        
        # Should contain Airflow variables
        assert "AIRFLOW" in env_content
    
    def test_generated_files_written_to_disk(self, engine, temp_output_dir):
        """Test writing generated files to disk"""
        stack = {"storage": "PostgreSQL"}
        
        vfs = engine.generate("disk_test", stack, str(uuid.uuid4()))
        
        output_path = temp_output_dir / "disk_test"
        vfs.flush(str(output_path))
        
        # Verify files exist on disk
        assert output_path.exists()
        assert (output_path / "docker-compose.yml").exists()
        assert (output_path / "README.md").exists()
    
    def test_vfs_to_zip_creation(self, engine, temp_output_dir):
        """Test creating ZIP file from VFS"""
        stack = {"storage": "PostgreSQL"}
        
        vfs = engine.generate("zip_test", stack, str(uuid.uuid4()))
        
        zip_path = temp_output_dir / "project.zip"
        vfs.to_zip(str(zip_path))
        
        assert zip_path.exists()
        assert zip_path.stat().st_size > 0
    
    def test_vfs_in_memory_zip(self, engine):
        """Test creating in-memory ZIP"""
        stack = {"storage": "PostgreSQL"}
        
        vfs = engine.generate("memory_zip_test", stack, str(uuid.uuid4()))
        
        zip_bytes = vfs.to_bytes_zip()
        
        assert zip_bytes is not None
        assert len(zip_bytes) > 0
        assert zip_bytes[:4] == b'PK\x03\x04'  # ZIP magic number
    
    def test_multiple_providers_same_category(self, engine):
        """Test handling multiple storage options (should pick one)"""
        # Note: Current implementation supports one per category
        # This test verifies graceful handling
        stack = {
            "storage": "PostgreSQL"  # Only one at a time
        }
        
        vfs = engine.generate("multi_test", stack, str(uuid.uuid4()))
        files = vfs.list_files()
        
        assert len(files) > 0
    
    def test_architecture_diagram_generated(self, engine):
        """Test that ARCHITECTURE.md is generated with Mermaid diagram"""
        stack = {
            "ingestion": "DLT",
            "storage": "PostgreSQL",
            "transformation": "dbt"
        }
        
        vfs = engine.generate("arch_test", stack, str(uuid.uuid4()))
        
        arch_content = vfs.get_file("ARCHITECTURE.md")
        assert arch_content is not None
        assert "mermaid" in arch_content.lower() or "graph" in arch_content.lower()
        assert "DLT" in arch_content or "dlt" in arch_content.lower()
        assert "PostgreSQL" in arch_content or "postgres" in arch_content.lower()
    
    def test_readme_contains_project_name(self, engine):
        """Test that README contains the project name"""
        project_name = "my_unique_project_123"
        stack = {"storage": "PostgreSQL"}
        
        vfs = engine.generate(project_name, stack, str(uuid.uuid4()))
        
        readme = vfs.get_file("README.md")
        assert readme is not None
        assert project_name in readme
    
    def test_makefile_generated_with_commands(self, engine):
        """Test that Makefile is generated with useful commands"""
        stack = {
            "storage": "PostgreSQL",
            "orchestration": "Airflow"
        }
        
        vfs = engine.generate("makefile_test", stack, str(uuid.uuid4()))
        
        makefile = vfs.get_file("Makefile")
        assert makefile is not None
        
        # Should have common commands
        assert "up" in makefile.lower() or "start" in makefile.lower()
        assert "down" in makefile.lower() or "stop" in makefile.lower()


class TestProviderIntegration:
    """Test provider integration and registration"""
    
    def test_all_providers_registered(self):
        """Verify all providers are properly registered"""
        from core.providers import (
            ingestion, storage, transformation, 
            orchestration, infrastructure,
            visualization, quality, monitoring
        )
        
        providers = ProviderRegistry.get_all_providers()
        
        # Should have all 8 categories
        assert "ingestion" in providers
        assert "storage" in providers
        assert "transformation" in providers
        assert "orchestration" in providers
        assert "infrastructure" in providers
        assert "visualization" in providers
        assert "quality" in providers
        assert "monitoring" in providers
        
        # Should have multiple providers per category
        assert len(providers["storage"]) >= 3  # PostgreSQL, Snowflake, DuckDB, etc.
        assert len(providers["orchestration"]) >= 2  # Airflow, Prefect, etc.
    
    def test_provider_can_be_instantiated(self):
        """Test that providers can be instantiated"""
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path
        
        template_dir = Path(__file__).parent.parent.parent / "backend" / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        
        # Get PostgreSQL provider
        postgres_cls = ProviderRegistry.get_provider("storage", "PostgreSQL")
        postgres = postgres_cls(env)
        
        assert postgres is not None
        
        # Should have required methods
        assert hasattr(postgres, "generate")
        assert hasattr(postgres, "get_docker_service_definition")
        assert hasattr(postgres, "get_env_vars")
    
    def test_provider_generates_docker_service(self):
        """Test that provider generates valid Docker service definition"""
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path
        from core.manifest import ProjectContext
        
        template_dir = Path(__file__).parent.parent.parent / "backend" / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        
        postgres_cls = ProviderRegistry.get_provider("storage", "PostgreSQL")
        postgres = postgres_cls(env)
        
        context = ProjectContext(
            project_name="test",
            project_id=str(uuid.uuid4()),
            base_dir="/tmp/test"
        )
        
        service_def = postgres.get_docker_service_definition(context)
        
        assert service_def is not None
        assert isinstance(service_def, dict)
        
        # Should have service configuration
        if service_def:  # Some providers return empty dict
            service_name = list(service_def.keys())[0]
            service_config = service_def[service_name]
            
            assert "image" in service_config or "build" in service_config


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_provider_name(self, ):
        """Test handling of invalid provider name"""
        with pytest.raises(ValueError):
            ProviderRegistry.get_provider("storage", "NonExistentDB")
    
    def test_invalid_category(self):
        """Test handling of invalid category"""
        with pytest.raises(ValueError):
            ProviderRegistry.get_provider("invalid_category", "PostgreSQL")
    
    def test_empty_stack(self):
        """Test generation with empty stack"""
        engine = TemplateEngine()
        
        # Should still generate basic project structure
        vfs = engine.generate("empty_test", {}, str(uuid.uuid4()))
        
        files = vfs.list_files()
        # Should at least have README and basic files
        assert len(files) > 0
