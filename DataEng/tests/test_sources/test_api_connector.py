"""
Tests for Data Source Connectors
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from core.providers.sources.auth import (
    NoAuth, APIKeyAuth, BearerTokenAuth, BasicAuth, OAuth2Auth
)


class TestAuthStrategies:
    """Test authentication strategies"""
    
    def test_no_auth(self):
        """Test NoAuth strategy"""
        auth = NoAuth()
        
        assert auth.get_auth_type() == "none"
        
        config = {"headers": {}}
        result = auth.apply_auth(config)
        
        assert result == {"headers": {}}
        assert len(auth.get_required_env_vars()) == 0
    
    def test_api_key_auth_header(self):
        """Test API Key authentication in header"""
        auth = APIKeyAuth(location="header", key_name="X-API-Key")
        
        assert auth.get_auth_type() == "api_key"
        
        required_vars = auth.get_required_env_vars("TEST_")
        assert "TEST_API_KEY" in required_vars
    
    def test_api_key_auth_query(self):
        """Test API Key authentication in query parameter"""
        auth = APIKeyAuth(location="query", key_name="api_key")
        
        assert auth.get_auth_type() == "api_key"
        
        # Note: actual application would require env var set
        # This just tests structure
        required_vars = auth.get_required_env_vars("TEST_")
        assert "TEST_API_KEY" in required_vars
    
    def test_bearer_token_auth(self):
        """Test Bearer token authentication"""
        auth = BearerTokenAuth()
        
        assert auth.get_auth_type() == "bearer"
        
        required_vars = auth.get_required_env_vars("TEST_")
        assert "TEST_API_TOKEN" in required_vars
    
    def test_basic_auth(self):
        """Test Basic authentication"""
        auth = BasicAuth()
        
        assert auth.get_auth_type() == "basic"
        
        required_vars = auth.get_required_env_vars("TEST_")
        assert "TEST_USERNAME" in required_vars
        assert "TEST_PASSWORD" in required_vars
    
    def test_oauth2_auth(self):
        """Test OAuth2 authentication"""
        auth = OAuth2Auth(token_url="https://oauth.example.com/token")
        
        assert auth.get_auth_type() == "oauth2"
        
        required_vars = auth.get_required_env_vars("TEST_")
        assert "TEST_CLIENT_ID" in required_vars
        assert "TEST_CLIENT_SECRET" in required_vars


class TestAPIConnector:
    """Test API Connector"""
    
    def test_api_connector_init(self):
        """Test APIConnector initialization"""
        from core.providers.sources.api_connector import APIConnector
        from jinja2 import Environment, FileSystemLoader
        
        env = Environment(loader=FileSystemLoader("backend/templates"))
        connector = APIConnector(env)
        
        assert connector.get_source_type() == "api"
    
    def test_create_auth_strategy(self):
        """Test auth strategy factory"""
        from core.providers.sources.api_connector import APIConnector
        from jinja2 import Environment, FileSystemLoader
        
        env = Environment(loader=FileSystemLoader("backend/templates"))
        connector = APIConnector(env)
        
        # Test creating NoAuth
        auth = connector._create_auth_strategy({"type": "none"})
        assert isinstance(auth, NoAuth)
        
        # Test creating API Key auth
        auth = connector._create_auth_strategy({
            "type": "api_key",
            "location": "header",
            "key_name": "X-API-Key"
        })
        assert isinstance(auth, APIKeyAuth)
        
        # Test creating Bearer auth
        auth = connector._create_auth_strategy({"type": "bearer"})
        assert isinstance(auth, BearerTokenAuth)
    
    def test_extraction_dependencies(self):
        """Test extraction dependencies"""
        from core.providers.sources.api_connector import APIConnector
        from jinja2 import Environment, FileSystemLoader
        
        env = Environment(loader=FileSystemLoader("backend/templates"))
        connector = APIConnector(env)
        
        deps = connector.get_extraction_dependencies()
        
        assert "requests" in str(deps)
        assert any("requests" in dep for dep in deps)


class TestSourceManager:
    """Test SourceManager"""
    
    def test_source_manager_init(self, tmp_path):
        """Test SourceManager initialization"""
        from core.source_manager import SourceManager
        
        config_path = tmp_path / "sources.yml"
        manager = SourceManager(str(config_path))
        
        assert manager.config_path == str(config_path)
        assert isinstance(manager.sources, list)
    
    def test_add_and_get_source(self, tmp_path):
        """Test adding and retrieving sources"""
        from core.source_manager import SourceManager
        from core.manifest import DataSource
        
        config_path = tmp_path / "sources.yml"
        manager = SourceManager(str(config_path))
        
        source = DataSource(
            name="test_api",
            type="api",
            connector="REST_API",
            config={"base_url": "https://api.example.com"},
            auth_config={"type": "none"}
        )
        
        manager.add_source(source)
        
        # Retrieve source
        retrieved = manager.get_source("test_api")
        assert retrieved is not None
        assert retrieved.name == "test_api"
        assert retrieved.type == "api"
    
    def test_list_sources(self, tmp_path):
        """Test listing sources"""
        from core.source_manager import SourceManager
        from core.manifest import DataSource
        
        config_path = tmp_path / "sources.yml"
        manager = SourceManager(str(config_path))
        
        # Add multiple sources
        for i in range(3):
            source = DataSource(
                name=f"test_api_{i}",
                type="api",
                connector="REST_API",
                config={"base_url": f"https://api.example.com/{i}"},
                auth_config={"type": "none"}
            )
            manager.add_source(source)
        
        sources = manager.list_sources()
        assert len(sources) == 3
    
    def test_remove_source(self, tmp_path):
        """Test removing sources"""
        from core.source_manager import SourceManager
        from core.manifest import DataSource
        
        config_path = tmp_path / "sources.yml"
        manager = SourceManager(str(config_path))
        
        source = DataSource(
            name="test_api",
            type="api",
            connector="REST_API",
            config={"base_url": "https://api.example.com"},
            auth_config={"type": "none"}
        )
        
        manager.add_source(source)
        assert len(manager.list_sources()) == 1
        
        manager.remove_source("test_api")
        assert len(manager.list_sources()) == 0
    
    def test_validate_source(self, tmp_path):
        """Test source validation"""
        from core.source_manager import SourceManager
        from core.manifest import DataSource
        
        config_path = tmp_path / "sources.yml"
        manager = SourceManager(str(config_path))
        
        # Valid source
        valid_source = DataSource(
            name="test_api",
            type="api",
            connector="REST_API",
            config={"base_url": "https://api.example.com"},
            auth_config={"type": "none"}
        )
        
        is_valid, error = manager.validate_source(valid_source)
        assert is_valid is True
        assert error is None
        
        # Invalid source (missing base_url)
        invalid_source = DataSource(
            name="test_api",
            type="api",
            connector="REST_API",
            config={},
            auth_config={"type": "none"}
        )
        
        is_valid, error = manager.validate_source(invalid_source)
        assert is_valid is False
        assert "base_url" in error


class TestDataSourceModel:
    """Test DataSource Pydantic model"""
    
    def test_data_source_creation(self):
        """Test creating DataSource instance"""
        from core.manifest import DataSource
        
        source = DataSource(
            name="test_api",
            type="api",
            connector="REST_API",
            config={"base_url": "https://api.example.com"},
            auth_config={"type": "api_key", "location": "header"},
            schedule="0 */6 * * *",
            enabled=True
        )
        
        assert source.name == "test_api"
        assert source.type == "api"
        assert source.connector == "REST_API"
        assert source.schedule == "0 */6 * * *"
        assert source.enabled is True
    
    def test_data_source_defaults(self):
        """Test DataSource default values"""
        from core.manifest import DataSource
        
        source = DataSource(
            name="test",
            type="api",
            connector="REST_API"
        )
        
        assert source.enabled is True
        assert source.config == {}
        assert source.auth_config == {}
        assert source.metadata == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
