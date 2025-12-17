"""
Tests for Visualization providers (Phase 3)
"""
import pytest
import os
from core.providers.visualization import (
    MetabaseGenerator,
    SupersetGenerator,
    GrafanaGenerator
)
from core.manifest import ProjectContext
from jinja2 import Environment, FileSystemLoader


@pytest.fixture
def project_context():
    """Create a test ProjectContext."""
    return ProjectContext(
        project_name="test_viz_project",
        base_port=3000
    )


@pytest.fixture
def jinja_env():
    """Create Jinja2 environment for template loading."""
    template_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "backend", "templates"
    )
    return Environment(loader=FileSystemLoader(template_dir))


class TestMetabaseGenerator:
    """Tests for Metabase generator."""
    
    def test_initialization(self, jinja_env):
        """Test Metabase generator initializes correctly."""
        generator = MetabaseGenerator(jinja_env)
        assert generator is not None
        assert generator.env == jinja_env
    
    def test_get_docker_service_definition(self, jinja_env, project_context):
        """Test Metabase Docker service definition."""
        generator = MetabaseGenerator(jinja_env)
        generator.context = project_context
        
        services = generator.get_docker_service_definition(project_context)
        
        assert "metabase" in services
        assert "metabase-db" in services
        assert services["metabase"]["image"] == "metabase/metabase:latest"
        assert len(services["metabase"]["ports"]) > 0
    
    def test_get_env_vars(self, jinja_env, project_context):
        """Test Metabase environment variables."""
        generator = MetabaseGenerator(jinja_env)
        generator.context = project_context
        
        env_vars = generator.get_env_vars(project_context)
        
        assert "METABASE_URL" in env_vars
        assert "localhost" in env_vars["METABASE_URL"]
    
    def test_get_docker_compose_volumes(self, jinja_env):
        """Test Metabase volumes."""
        generator = MetabaseGenerator(jinja_env)
        volumes = generator.get_docker_compose_volumes()
        
        assert "metabase_data" in volumes
        assert "metabase_db" in volumes


class TestSupersetGenerator:
    """Tests for Apache Superset generator."""
    
    def test_initialization(self, jinja_env):
        """Test Superset generator initializes correctly."""
        generator = SupersetGenerator(jinja_env)
        assert generator is not None
    
    def test_get_docker_service_definition(self, jinja_env, project_context):
        """Test Superset Docker service definition."""
        generator = SupersetGenerator(jinja_env)
        generator.context = project_context
        
        services = generator.get_docker_service_definition(project_context)
        
        assert "superset" in services
        assert services["superset"]["image"] == "apache/superset:latest"
        assert "superset_data" in services["superset"]["volumes"][0]
    
    def test_get_env_vars(self, jinja_env, project_context):
        """Test Superset environment variables."""
        generator = SupersetGenerator(jinja_env)
        generator.context = project_context
        
        env_vars = generator.get_env_vars(project_context)
        
        assert "SUPERSET_URL" in env_vars
        assert "SUPERSET_USERNAME" in env_vars
        assert "SUPERSET_PASSWORD" in env_vars


class TestGrafanaGenerator:
    """Tests for Grafana generator."""
    
    def test_initialization(self, jinja_env):
        """Test Grafana generator initializes correctly."""
        generator = GrafanaGenerator(jinja_env)
        assert generator is not None
    
    def test_get_docker_service_definition(self, jinja_env, project_context):
        """Test Grafana Docker service definition."""
        generator = GrafanaGenerator(jinja_env)
        generator.context = project_context
        
        services = generator.get_docker_service_definition(project_context)
        
        assert "grafana" in services
        assert services["grafana"]["image"] == "grafana/grafana:latest"
        assert "GF_SECURITY_ADMIN_USER" in services["grafana"]["environment"]
    
    def test_get_env_vars(self, jinja_env, project_context):
        """Test Grafana environment variables."""
        generator = GrafanaGenerator(jinja_env)
        generator.context = project_context
        
        env_vars = generator.get_env_vars(project_context)
        
        assert "GRAFANA_URL" in env_vars
        assert "GRAFANA_USERNAME" in env_vars
        assert "GRAFANA_PASSWORD" in env_vars
    
    def test_get_docker_compose_volumes(self, jinja_env):
        """Test Grafana volumes."""
        generator = GrafanaGenerator(jinja_env)
        volumes = generator.get_docker_compose_volumes()
        
        assert "grafana_data" in volumes


class TestVisualizationTemplates:
    """Tests for visualization Jinja2 templates."""
    
    def test_metabase_template_exists(self):
        """Test Metabase template file exists."""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "backend", "templates", "visualization", "metabase_compose.yml.j2"
        )
        assert os.path.exists(template_path), "Metabase template not found"
    
    def test_superset_template_exists(self):
        """Test Superset template file exists."""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "backend", "templates", "visualization", "superset_compose.yml.j2"
        )
        assert os.path.exists(template_path), "Superset template not found"
    
    def test_grafana_template_exists(self):
        """Test Grafana template file exists."""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "backend", "templates", "visualization", "grafana_compose.yml.j2"
        )
        assert os.path.exists(template_path), "Grafana template not found"
    
    def test_metabase_template_syntax(self, jinja_env):
        """Test Metabase template has valid Jinja2 syntax."""
        try:
            template = jinja_env.get_template("visualization/metabase_compose.yml.j2")
            assert template is not None
        except Exception as e:
            pytest.fail(f"Metabase template syntax error: {e}")
    
    def test_superset_template_syntax(self, jinja_env):
        """Test Superset template has valid Jinja2 syntax."""
        try:
            template = jinja_env.get_template("visualization/superset_compose.yml.j2")
            assert template is not None
        except Exception as e:
            pytest.fail(f"Superset template syntax error: {e}")
    
    def test_grafana_template_syntax(self, jinja_env):
        """Test Grafana template has valid Jinja2 syntax."""
        try:
            template = jinja_env.get_template("visualization/grafana_compose.yml.j2")
            assert template is not None
        except Exception as e:
            pytest.fail(f"Grafana template syntax error: {e}")
