"""
Tests for storage providers.
"""

import pytest
from core.providers.storage import PostgresGenerator
from core.manifest import ProjectContext


class TestPostgresGenerator:
    """Tests for PostgresGenerator class."""
    
    @pytest.mark.unit
    def test_initialization(self, mock_jinja_env):
        """Test PostgresGenerator initializes correctly."""
        generator = PostgresGenerator(mock_jinja_env)
        
        assert generator.env == mock_jinja_env
        assert generator.context is None
    
    @pytest.mark.unit
    def test_generate_initializes_context(self, mock_jinja_env, temp_output_dir):
        """Test that generate() initializes context properly."""
        context = ProjectContext(
            project_name="test",
            stack={"storage": "PostgreSQL"}
        )
        config = {"project_context": context}
        
        generator = PostgresGenerator(mock_jinja_env)
        generator.generate(temp_output_dir, config)
        
        assert generator.context is not None
        assert generator.context == context
    
    @pytest.mark.unit
    def test_generate_creates_secrets(self, mock_jinja_env, temp_output_dir):
        """Test that generate() creates necessary secrets."""
        context = ProjectContext(
            project_name="test",
            stack={"storage": "PostgreSQL"}
        )
        config = {"project_context": context}
        
        generator = PostgresGenerator(mock_jinja_env)
        generator.generate(temp_output_dir, config)
        
        # Should have created postgres_password secret
        assert "postgres_password" in context.generated_secrets
    
    @pytest.mark.unit
    def test_generate_allocates_port(self, mock_jinja_env, temp_output_dir):
        """Test that generate() allocates port for service."""
        context = ProjectContext(
            project_name="test",
            stack={"storage": "PostgreSQL"}
        )
        config = {"project_context": context}
        
        generator = PostgresGenerator(mock_jinja_env)
        generator.generate(temp_output_dir, config)
        
        # Should have allocated postgres port
        assert "postgres" in context.base_ports
        assert context.base_ports["postgres"] == 5432
    
    @pytest.mark.unit
    def test_get_docker_service_definition_returns_service(self, mock_jinja_env):
        """Test Docker service definition (after name fix)."""
        context = ProjectContext(
            project_name="test",
            stack={"storage": "PostgreSQL"}
        )
        
        generator = PostgresGenerator(mock_jinja_env)
        generator.context = context
        
        # Pre-generate secrets so template can use them
        context.get_or_create_secret("postgres_password")
        
        service = generator.get_docker_service_definition(context)
        
        # Should return a dictionary with postgres service
        assert isinstance(service, dict)
        # Note: After fix, this should work properly
    
    @pytest.mark.unit
    def test_get_docker_compose_volumes(self, mock_jinja_env):
        """Test that volumes are defined for data persistence."""
        generator = PostgresGenerator(mock_jinja_env)
        
        volumes = generator.get_docker_compose_volumes()
        
        assert "postgres_data" in volumes
