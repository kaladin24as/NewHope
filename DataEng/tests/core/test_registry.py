"""
Tests for core.registry module (ProviderRegistry).
"""

import pytest
from core.registry import ProviderRegistry
from core.interfaces import ComponentGenerator
from typing import Dict, Any


class MockProvider(ComponentGenerator):
    """Mock provider for testing."""
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        pass
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        return {}
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        return {}


class TestProviderRegistry:
    """Tests for ProviderRegistry class."""
    
    @pytest.mark.unit
    def test_registry_has_categories(self):
        """Test that registry initializes with expected categories."""
        categories = ProviderRegistry._registry.keys()
        
        assert "ingestion" in categories
        assert "storage" in categories
        assert "transformation" in categories
        assert "orchestration" in categories
        assert "infrastructure" in categories
    
    @pytest.mark.unit
    def test_register_provider(self):
        """Test registering a new provider."""
        # Note: This modifies global registry, so use unique name
        ProviderRegistry.register("storage", "TestStorage", MockProvider)
        
        provider_cls = ProviderRegistry.get_provider("storage", "TestStorage")
        
        assert provider_cls == MockProvider
    
    @pytest.mark.unit
    def test_register_invalid_category_raises_error(self):
        """Test that registering to invalid category raises ValueError."""
        with pytest.raises(ValueError, match="Invalid category"):
            ProviderRegistry.register("invalid_category", "Test", MockProvider)
    
    @pytest.mark.unit
    def test_get_provider_not_found_raises_error(self):
        """Test that getting non-existent provider raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            ProviderRegistry.get_provider("storage", "NonExistentProvider")
    
    @pytest.mark.unit
    def test_get_all_providers(self):
        """Test getting all registered providers."""
        providers = ProviderRegistry.get_all_providers()
        
        assert isinstance(providers, dict)
        assert "ingestion" in providers
        assert "storage" in providers
        
        # Check that lists contain strings (provider names)
        assert all(isinstance(providers[cat], list) for cat in providers)
    
    @pytest.mark.unit
    def test_get_all_providers_includes_registered(self):
        """Test that get_all_providers includes registered providers."""
        # Import providers to trigger registration
        from core.providers import ingestion, storage, transformation, orchestration, infrastructure
        
        providers = ProviderRegistry.get_all_providers()
        
        # Check for known providers
        assert "DLT" in providers["ingestion"]
        assert "PostgreSQL" in providers["storage"]
        assert "dbt" in providers["transformation"]
        assert "Airflow" in providers["orchestration"]
        assert "terraform" in providers["infrastructure"]
