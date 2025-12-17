"""
Tests for Environment Manager
"""

import pytest
from core.env_manager import EnvironmentManager
from core.manifest import ProjectContext


class TestEnvironmentManager:
    """Test suite for environment manager"""
    
    @pytest.fixture
    def context(self):
        """Create test project context"""
        context = ProjectContext(
            project_name="test_project",
            project_id="test-123",
            base_dir="/app"
        )
        
        # Add some test environment variables
        context.secrets = {
            "postgres_password": "test_pass_123",
            "airflow_secret": "airflow_secret_456"
        }
        
        return context
    
    def test_generate_dev_env(self, context):
        """Test development environment generation"""
        dev_env = EnvironmentManager.generate_dev_env(context)
        
        assert dev_env is not None
        assert "ENVIRONMENT=dev" in dev_env
        assert "DEBUG=true" in dev_env
        assert "LOG_LEVEL=DEBUG" in dev_env
        assert "# Development Environment" in dev_env
    
    def test_generate_staging_env(self, context):
        """Test staging environment generation"""
        staging_env = EnvironmentManager.generate_staging_env(context)
        
        assert staging_env is not None
        assert "ENVIRONMENT=staging" in staging_env
        assert "DEBUG=false" in staging_env
        assert "LOG_LEVEL=INFO" in staging_env
        assert "USE_CLOUD_SECRETS=true" in staging_env
        assert "# Staging Environment" in staging_env
    
    def test_generate_prod_env(self, context):
        """Test production environment generation"""
        prod_env = EnvironmentManager.generate_prod_env(context)
        
        assert prod_env is not None
        assert "ENVIRONMENT=prod" in prod_env
        assert "DEBUG=false" in prod_env
        assert "LOG_LEVEL=WARNING" in prod_env
        assert "USE_CLOUD_SECRETS=true" in prod_env
        assert "ENABLE_MONITORING=true" in prod_env
        assert "⚠️  PRODUCTION ENVIRONMENT" in prod_env
    
    def test_generate_example_env(self, context):
        """Test example .env file generation"""
        example_env = EnvironmentManager.generate_example_env(context)
        
        assert example_env is not None
        assert "CHANGE_ME" in example_env
        assert "# Environment Variables Template" in example_env
        assert "cp .env.example .env.dev" in example_env
    
    def test_generate_all_env_files(self, context):
        """Test generating all environment files at once"""
        env_files = EnvironmentManager.generate_all_env_files(context)
        
        assert "dev" in env_files
        assert "staging" in env_files
        assert "prod" in env_files
        assert "example" in env_files
        
        # All should have content
        assert all(len(content) > 0 for content in env_files.values())
    
    def test_env_switcher_script_generated(self):
        """Test environment switcher script generation"""
        script = EnvironmentManager.generate_env_switcher_script()
        
        assert script is not None
        assert "#!/bin/bash" in script
        assert "dev" in script
        assert "staging" in script
        assert "prod" in script
        assert "docker-compose" in script
    
    def test_gitignore_additions(self):
        """Test gitignore additions"""
        gitignore = EnvironmentManager.generate_gitignore_additions()
        
        assert gitignore is not None
        assert ".env" in gitignore
        assert ".env.dev" in gitignore
        assert ".env.staging" in gitignore
        assert ".env.prod" in gitignore
        assert "!.env.example" in gitignore
    
    def test_environment_documentation(self):
        """Test environment documentation generation"""
        docs = EnvironmentManager.get_environment_documentation()
        
        assert docs is not None
        assert "# Environment Management" in docs
        assert "Development" in docs
        assert "Staging" in docs
        assert "Production" in docs
        assert "switch-env.sh" in docs
    
    def test_env_format_grouping(self):
        """Test that environment variables are grouped by prefix"""
        context = ProjectContext(
            project_name="test",
            project_id="123",
            base_dir="/app"
        )
        
        # Add variables with different prefixes
        vars_dict = {
            "POSTGRES_HOST": "postgres",
            "POSTGRES_PORT": "5432",
            "AIRFLOW_HOST": "airflow",
            "AIRFLOW_PORT": "8080",
            "DEBUG": "true"
        }
        
        formatted = EnvironmentManager._format_env(vars_dict)
        
        # Should have group headers
        assert "# Postgres" in formatted or "# POSTGRES" in formatted.upper()
        assert "# Airflow" in formatted or "# AIRFLOW" in formatted.upper()
    
    def test_secrets_masked_in_example(self, context):
        """Test that secrets are masked as CHANGE_ME in example env"""
        context.secrets = {
            "my_password": "secret123",
            "api_key": "key456",
            "token": "token789"
        }
        
        example = EnvironmentManager.generate_example_env(context)
        
        # Secrets should be masked
        assert "secret123" not in example
        assert "key456" not in example
        assert "token789" not in example
        assert "CHANGE_ME" in example
    
    def test_dev_env_uses_localhost(self, context):
        """Test that dev environment uses localhost for services"""
        dev_env = EnvironmentManager.generate_dev_env(context)
        
        # Dev should prefer local services
        assert "localhost" in dev_env or "postgres" in dev_env  # Docker service names
    
    def test_prod_env_uses_placeholders(self, context):
        """Test that prod environment uses placeholders for cloud resources"""
        prod_env = EnvironmentManager.generate_prod_env(context)
        
        # Prod should use environment variable placeholders
        assert "${" in prod_env or "CHANGE_ME" in prod_env
