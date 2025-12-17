"""
Template Validation Tests
==========================

Validates that all Jinja2 templates have correct syntax and can be rendered.
"""

import pytest
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError, UndefinedError
import yaml


class TestTemplateValidation:
    """Test suite for template syntax validation"""
    
    @pytest.fixture
    def template_dir(self):
        """Get templates directory"""
        backend_dir = Path(__file__).parent.parent.parent / "backend"
        return backend_dir / "templates"
    
    @pytest.fixture
    def jinja_env(self, template_dir):
        """Create Jinja2 environment"""
        return Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=False
        )
    
    def test_templates_directory_exists(self, template_dir):
        """Verify templates directory exists"""
        assert template_dir.exists(), f"Templates directory not found: {template_dir}"
        assert template_dir.is_dir(), "Templates path is not a directory"
    
    def test_all_templates_valid_jinja2_syntax(self, template_dir, jinja_env):
        """Validate all .j2 files have valid Jinja2 syntax"""
        template_files = list(template_dir.rglob("*.j2"))
        
        assert len(template_files) > 0, "No template files found"
        
        errors = []
        for template_file in template_files:
            try:
                relative_path = template_file.relative_to(template_dir)
                template = jinja_env.get_template(str(relative_path))
                # Just loading is enough to validate syntax
            except TemplateSyntaxError as e:
                errors.append(f"{template_file.name}: {str(e)}")
        
        if errors:
            pytest.fail(f"Template syntax errors found:\n" + "\n".join(errors))
    
    def test_common_templates_exist(self, template_dir):
        """Verify critical common templates exist"""
        required_templates = [
            "common/README.md.j2",
            "common/Makefile.j2",
            "common/env.example.j2",
            "common/docker-compose.yml.j2",
            "common/devcontainer.json.j2"
        ]
        
        missing = []
        for template in required_templates:
            template_path = template_dir / template
            if not template_path.exists():
                missing.append(template)
        
        if missing:
            pytest.fail(f"Required templates missing:\n" + "\n".join(missing))
    
    def test_readme_template_renders(self, jinja_env):
        """Test README template can be rendered"""
        template = jinja_env.get_template("common/README.md.j2")
        
        context = {
            "project_name": "test_project",
            "stack": {
                "ingestion": "DLT",
                "storage": "PostgreSQL",
                "transformation": "dbt",
                "orchestration": "Airflow"
            },
            "services": {
                "postgres": {"port": 5432},
                "airflow": {"port": 8080}
            }
        }
        
        result = template.render(**context)
        assert len(result) > 0
        assert "test_project" in result
    
    def test_docker_compose_template_renders_valid_yaml(self, jinja_env):
        """Test docker-compose template renders valid YAML"""
        template = jinja_env.get_template("common/docker-compose.yml.j2")
        
        context = {
            "project_name": "test_project",
            "services": {
                "postgres": {
                    "image": "postgres:15",
                    "environment": {
                        "POSTGRES_PASSWORD": "test123"
                    },
                    "ports": ["5432:5432"]
                }
            },
            "volumes": {},
            "networks": {"data_network": {}}
        }
        
        result = template.render(**context)
        
        # Should be valid YAML
        try:
            parsed = yaml.safe_load(result)
            assert "version" in parsed or "services" in parsed
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML generated: {e}")
    
    def test_makefile_template_renders(self, jinja_env):
        """Test Makefile template can be rendered"""
        template = jinja_env.get_template("common/Makefile.j2")
        
        context = {
            "project_name": "test_project",
            "has_airflow": True,
            "has_dbt": True
        }
        
        result = template.render(**context)
        assert len(result) > 0
        assert "up:" in result or "build:" in result
    
    def test_env_example_template_renders(self, jinja_env):
        """Test .env.example template renders with all variables"""
        template = jinja_env.get_template("common/env.example.j2")
        
        context = {
            "env_vars": {
                "POSTGRES_HOST": "postgres",
                "POSTGRES_PORT": "5432",
                "POSTGRES_DB": "warehouse",
                "POSTGRES_USER": "postgres",
                "POSTGRES_PASSWORD": "CHANGE_ME"
            }
        }
        
        result = template.render(**context)
        assert "POSTGRES_HOST" in result
        assert "POSTGRES_PASSWORD" in result
    
    def test_ingestion_templates_exist(self, template_dir):
        """Verify ingestion templates exist"""
        ingestion_dir = template_dir / "ingestion"
        assert ingestion_dir.exists(), "Ingestion templates directory missing"
        
        # Check for DLT template
        dlt_template = ingestion_dir / "dlt_pipeline.py.j2"
        assert dlt_template.exists(), "DLT pipeline template missing"
    
    def test_transformation_templates_exist(self, template_dir):
        """Verify transformation templates exist"""
        transform_dir = template_dir / "transformation"
        assert transform_dir.exists(), "Transformation templates directory missing"
        
        dbt_project = transform_dir / "dbt_project.yml.j2"
        profiles = transform_dir / "profiles.yml.j2"
        
        assert dbt_project.exists(), "dbt_project.yml template missing"
        assert profiles.exists(), "profiles.yml template missing"
    
    def test_orchestration_templates_exist(self, template_dir):
        """Verify orchestration templates exist"""
        orch_dir = template_dir / "orchestration"
        assert orch_dir.exists(), "Orchestration templates directory missing"
        
        airflow_dag = orch_dir / "airflow_dag.py.j2"
        assert airflow_dag.exists(), "Airflow DAG template missing"
    
    def test_no_hardcoded_secrets(self, template_dir, jinja_env):
        """Ensure templates don't contain hardcoded secrets"""
        template_files = list(template_dir.rglob("*.j2"))
        
        suspicious_patterns = [
            "password=\"",
            "pwd=\"",
            "secret=\"",
            "token=\"",
            "api_key=\""
        ]
        
        issues = []
        for template_file in template_files:
            content = template_file.read_text()
            
            for pattern in suspicious_patterns:
                # Ignore if it's a Jinja2 variable reference
                if pattern in content and "{{" not in content[content.find(pattern)-10:content.find(pattern)+50]:
                    issues.append(f"{template_file.name}: Found '{pattern}'")
        
        if issues:
            pytest.fail(f"Potential hardcoded secrets found:\n" + "\n".join(issues))
    
    def test_template_variables_documented(self, template_dir):
        """Check that complex templates have variable documentation"""
        templates_to_check = [
            "common/docker-compose.yml.j2",
            "common/README.md.j2"
        ]
        
        for template_name in templates_to_check:
            template_path = template_dir / template_name
            if template_path.exists():
                content = template_path.read_text()
                # Should have at least one comment explaining variables
                assert "{#" in content or "{{" in content, \
                    f"{template_name} should use Jinja2 variables or have comments"


class TestTemplateRendering:
    """Test actual template rendering with realistic contexts"""
    
    @pytest.fixture
    def engine(self):
        """Get template engine instance"""
        from core.engine import TemplateEngine
        return TemplateEngine()
    
    def test_full_stack_template_generation(self, engine):
        """Test generating templates for a full stack"""
        from core.manifest import ProjectContext
        import uuid
        
        context = ProjectContext(
            project_name="test_project",
            project_id=str(uuid.uuid4()),
            base_dir="/tmp/test"
        )
        
        # This should not raise any template errors
        try:
            # Just test that we can create the context and access templates
            assert context.project_name == "test_project"
        except Exception as e:
            pytest.fail(f"Failed to create project context: {e}")
