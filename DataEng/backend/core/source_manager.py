"""
Source Manager

Provides CRUD operations for managing data source configurations.
Handles loading, saving, and validating source configurations.
"""

import os
import yaml
from typing import List, Optional, Dict, Any
from pathlib import Path

from core.manifest import DataSource
from core.providers.sources import APIConnector


class SourceManager:
    """
    Manages data source configurations with YAML persistence.
    """
    
    def __init__(self, config_path: str = "config/sources.yml"):
        """
        Initialize the source manager.
        
        Args:
            config_path: Path to the sources configuration file
        """
        self.config_path = config_path
        self.sources: List[DataSource] = []
        
        # Ensure config directory exists
        config_dir = os.path.dirname(config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        
        # Load existing sources
        if os.path.exists(config_path):
            self.load_sources()
    
    def load_sources(self) -> None:
        """Load sources from YAML configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data or 'sources' not in data:
                self.sources = []
                return
            
            self.sources = []
            for source_data in data['sources']:
                source = DataSource(
                    name=source_data['name'],
                    type=source_data['type'],
                    connector=source_data['connector'],
                    config=source_data.get('config', {}),
                    auth_config=source_data.get('auth', {}),
                    schedule=source_data.get('schedule'),
                    enabled=source_data.get('enabled', True),
                    metadata=source_data.get('metadata', {})
                )
                self.sources.append(source)
            
            print(f"✅ Loaded {len(self.sources)} data source(s) from {self.config_path}")
        
        except Exception as e:
            print(f"⚠️  Error loading sources: {e}")
            self.sources = []
    
    def save_sources(self) -> None:
        """Save sources to YAML configuration file."""
        try:
            data = {
                'sources': [
                    {
                        'name': source.name,
                        'type': source.type,
                        'connector': source.connector,
                        'config': source.config,
                        'auth': source.auth_config,
                        'schedule': source.schedule,
                        'enabled': source.enabled,
                        'metadata': source.metadata
                    }
                    for source in self.sources
                ]
            }
            
            with open(self.config_path, 'w') as f:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
            
            print(f"✅ Saved {len(self.sources)} data source(s) to {self.config_path}")
        
        except Exception as e:
            print(f"❌ Error saving sources: {e}")
            raise
    
    def add_source(self, source: DataSource) -> None:
        """
        Add a new source and save to file.
        
        Args:
            source: DataSource to add
        
        Raises:
            ValueError: If source with same name already exists
        """
        # Check for duplicates
        if self.get_source(source.name):
            raise ValueError(f"Data source with name '{source.name}' already exists")
        
        self.sources.append(source)
        self.save_sources()
        print(f"✅ Added data source: {source.name}")
    
    def remove_source(self, name: str) -> bool:
        """
        Remove a source by name.
        
        Args:
            name: Name of the source to remove
        
        Returns:
            True if removed, False if not found
        """
        for i, source in enumerate(self.sources):
            if source.name == name:
                self.sources.pop(i)
                self.save_sources()
                print(f"✅ Removed data source: {name}")
                return True
        
        print(f"⚠️  Data source not found: {name}")
        return False
    
    def get_source(self, name: str) -> Optional[DataSource]:
        """
        Get a source by name.
        
        Args:
            name: Name of the source
        
        Returns:
            DataSource if found, None otherwise
        """
        for source in self.sources:
            if source.name == name:
                return source
        return None
    
    def list_sources(self) -> List[DataSource]:
        """
        Get all sources.
        
        Returns:
            List of all DataSources
        """
        return self.sources
    
    def get_sources_by_type(self, source_type: str) -> List[DataSource]:
        """
        Get sources by type.
        
        Args:
            source_type: Type to filter by (api, database, file, stream)
        
        Returns:
            List of matching DataSources
        """
        return [s for s in self.sources if s.type == source_type]
    
    def test_source(self, name: str, env: Any = None) -> tuple[bool, str]:
        """
        Test connection to a data source.
        
        Args:
            name: Name of the source to test
            env: Jinja2 environment (optional, for connector instantiation)
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        source = self.get_source(name)
        if not source:
            return (False, f"Source '{name}' not found")
        
        try:
            # Create appropriate connector based on source type
            if source.connector == "REST_API":
                connector = APIConnector(env) if env else None
                if not connector:
                    # Fallback to direct testing
                    return self._test_api_direct(source)
                
                config = {
                    "name": source.name,
                    "base_url": source.config.get("base_url"),
                    "auth": source.auth_config,
                    "test_endpoint": source.config.get("test_endpoint", "/")
                }
                
                success, error_msg = connector.test_connection(config)
                
                if success:
                    if error_msg:
                        return (True, f"✅ Connected (with warning: {error_msg})")
                    return (True, "✅ Connection successful!")
                else:
                    return (False, f"❌ Connection failed: {error_msg}")
            
            else:
                return (False, f"Testing not implemented for connector: {source.connector}")
        
        except Exception as e:
            return (False, f"❌ Error during test: {str(e)}")
    
    def _test_api_direct(self, source: DataSource) -> tuple[bool, str]:
        """Direct API testing without connector (fallback)."""
        try:
            import requests
            
            base_url = source.config.get("base_url")
            if not base_url:
                return (False, "Missing base_url in configuration")
            
            response = requests.get(base_url, timeout=10)
            
            if response.status_code < 500:
                return (True, f"✅ Connected (HTTP {response.status_code})")
            else:
                return (False, f"Server error: HTTP {response.status_code}")
        
        except Exception as e:
            return (False, f"Connection failed: {str(e)}")
    
    def update_source(self, name: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing source.
        
        Args:
            name: Name of the source to update
            updates: Dictionary of fields to update
        
        Returns:
            True if updated, False if not found
        """
        source = self.get_source(name)
        if not source:
            return False
        
        # Update fields
        for key, value in updates.items():
            if hasattr(source, key):
                setattr(source, key, value)
        
        self.save_sources()
        print(f"✅ Updated data source: {name}")
        return True
    
    def validate_source(self, source: DataSource) -> tuple[bool, Optional[str]]:
        """
        Validate source configuration.
        
        Args:
            source: DataSource to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        if not source.name:
            return (False, "Source name is required")
        
        if not source.type:
            return (False, "Source type is required")
        
        if not source.connector:
            return (False, "Connector type is required")
        
        # Validate type-specific configuration
        if source.type == "api":
            if not source.config.get("base_url"):
                return (False, "API sources require 'base_url' in config")
            
            # Validate auth configuration
            auth_type = source.auth_config.get("type", "none")
            if auth_type not in ["none", "api_key", "bearer", "oauth2", "basic"]:
                return (False, f"Invalid auth type: {auth_type}")
        
        return (True, None)
