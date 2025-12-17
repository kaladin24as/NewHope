"""
Pytest configuration and shared fixtures for AntiGravity tests.

This module contains common fixtures used across all test modules.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from jinja2 import Environment, DictLoader
from typing import Dict, Any

# Add backend to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from core.manifest import ProjectContext
from core.engine import VirtualFileSystem


@pytest.fixture
def mock_jinja_env():
    """
    Provides a mock Jinja2 environment with basic templates.
    
    Returns:
        Jinja2 Environment configured with in-memory templates
    """
    templates = {
        "test.j2": "Hello {{ name }}",
        "config.yml.j2": "port: {{ port }}\nhost: {{ host }}",
    }
    return Environment(loader=DictLoader(templates))


@pytest.fixture
def sample_stack() -> Dict[str, str]:
    """
    Provides a sample complete stack configuration.
    
    Returns:
        Dictionary with all categories populated
    """
    return {
        "ingestion": "DLT",
        "storage": "PostgreSQL",
        "transformation": "dbt",
        "orchestration": "Airflow",
        "infrastructure": "terraform"
    }


@pytest.fixture
def minimal_stack() -> Dict[str, str]:
    """
    Provides a minimal stack with only essential components.
    
    Returns:
        Dictionary with minimal configuration
    """
    return {
        "storage": "PostgreSQL",
        "transformation": "dbt"
    }


@pytest.fixture
def sample_project_context(sample_stack) -> ProjectContext:
    """
    Provides a pre-configured ProjectContext for testing.
    
    Args:
        sample_stack: Sample stack configuration fixture
        
    Returns:
        ProjectContext instance with sample configuration
    """
    return ProjectContext(
        project_name="test_project",
        stack=sample_stack
    )


@pytest.fixture
def empty_vfs() -> VirtualFileSystem:
    """
    Provides an empty VirtualFileSystem instance.
    
    Returns:
        Empty VirtualFileSystem
    """
    return VirtualFileSystem()


@pytest.fixture
def populated_vfs() -> VirtualFileSystem:
    """
    Provides a VirtualFileSystem with sample files.
    
    Returns:
        VirtualFileSystem with test files
    """
    vfs = VirtualFileSystem()
    vfs.add_file("README.md", "# Test Project")
    vfs.add_file("docker-compose.yml", "version: '3.8'")
    vfs.add_file("dags/test_dag.py", "# Airflow DAG")
    return vfs


@pytest.fixture
def temp_output_dir():
    """
    Provides a temporary directory for file generation tests.
    
    Automatically cleaned up after test completion.
    
    Yields:
        Path to temporary directory
    """
    temp_dir = tempfile.mkdtemp(prefix="antigravity_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """
    Provides a mock configuration dictionary for generators.
    
    Returns:
        Dictionary with common configuration
    """
    context = ProjectContext(
        project_name="test_project",
        stack={"storage": "PostgreSQL"}
    )
    return {
        "project_context": context,
        "project_name": "test_project",
        "pipeline_name": "test_pipeline",
        "dataset_name": "test_data"
    }


# Pytest configuration hooks

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (> 1 second)"
    )
