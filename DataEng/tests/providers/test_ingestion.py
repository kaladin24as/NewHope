"""
Tests for ingestion providers.
"""

import pytest
import os
from core.providers.ingestion import DLTGenerator
from core.manifest import ProjectContext


class TestDLTGenerator:
    """Tests for DLTGenerator class."""
    
    @pytest.mark.unit
    def test_initialization(self, mock_jinja_env):
        """Test DLTGenerator initializes correctly."""
        generator = DLTGenerator(mock_jinja_env)
        
        assert generator.env == mock_jinja_env
    
    @pytest.mark.integration
    def test_generate_creates_files(self, mock_jinja_env, temp_output_dir, mock_config):
        """Test that DLT generator creates expected files."""
        generator = DLTGenerator(mock_jinja_env)
        
        # Generate files
        generator.generate(temp_output_dir, mock_config)
        
        # Check for generated files
        expected_files = [
            "ingestion_pipeline.py",
            "Dockerfile.ingestion"
        ]
        
        for filename in expected_files:
            filepath = os.path.join(temp_output_dir, filename)
            assert os.path.exists(filepath), f"Expected file {filename} not found"
    
    @pytest.mark.unit
    def test_get_docker_service_definition(self, mock_jinja_env, sample_project_context):
        """Test Docker service definition for DLT."""
        generator = DLTGenerator(mock_jinja_env)
        
        service = generator.get_docker_service_definition(sample_project_context)
        
        assert "dlt_ingestion" in service
        assert "build" in service["dlt_ingestion"]
        assert "environment" in service["dlt_ingestion"]
    
    @pytest.mark.unit
    def test_get_env_vars(self, mock_jinja_env, sample_project_context):
        """Test environment variables for DLT."""
        generator = DLTGenerator(mock_jinja_env)
        
        env_vars = generator.get_env_vars(sample_project_context)
        
        assert isinstance(env_vars, dict)
        assert len(env_vars) > 0
        # Should have pipeline-related env vars
        assert any("PIPELINE" in key or "DESTINATION" in key for key in env_vars.keys())
    
    @pytest.mark.integration
    def test_generate_adapts_to_storage(self, mock_jinja_env, temp_output_dir):
        """Test that DLT adapts destination based on storage in stack."""
        # Test with PostgreSQL
        context_postgres = ProjectContext(
            project_name="test",
            stack={"storage": "PostgreSQL", "ingestion": "DLT"}
        )
        config_postgres = {"project_context": context_postgres}
        
        generator = DLTGenerator(mock_jinja_env)
        generator.generate(temp_output_dir, config_postgres)
        
        # Verify file was created
        pipeline_file = os.path.join(temp_output_dir, "ingestion_pipeline.py")
        assert os.path.exists(pipeline_file)
