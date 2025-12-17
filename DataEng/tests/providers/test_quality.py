"""
Tests for Data Quality providers (Phase 3)
"""
import pytest
import os
from jinja2 import Environment, FileSystemLoader


@pytest.fixture
def jinja_env():
    """Create Jinja2 environment for template loading."""
    template_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "backend", "templates"
    )
    return Environment(loader=FileSystemLoader(template_dir))


class TestQualityTemplates:
    """Tests for data quality Jinja2 templates."""
    
    def test_great_expectations_config_template_exists(self):
        """Test Great Expectations config template exists."""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "backend", "templates", "quality", "great_expectations_config.yml.j2"
        )
        assert os.path.exists(template_path), "Great Expectations config template not found"
    
    def test_great_expectations_suite_template_exists(self):
        """Test Great Expectations suite template exists."""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "backend", "templates", "quality", "great_expectations_suite.py.j2"
        )
        assert os.path.exists(template_path), "Great Expectations suite template not found"
    
    def test_soda_checks_template_exists(self):
        """Test Soda checks template exists."""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "backend", "templates", "quality", "soda_checks.yml.j2"
        )
        assert os.path.exists(template_path), "Soda checks template not found"
    
    def test_great_expectations_config_syntax(self, jinja_env):
        """Test Great Expectations config template has valid syntax."""
        try:
            template = jinja_env.get_template("quality/great_expectations_config.yml.j2")
            assert template is not None
            
            # Test rendering with sample context
            rendered = template.render(
                project_name="test_project",
                stack={"storage": "PostgreSQL"},
                secrets={"postgres_user": "test", "postgres_password": "test"}
            )
            assert "config_version: 3.0" in rendered
            assert "datasources:" in rendered
        except Exception as e:
            pytest.fail(f"Great Expectations config template error: {e}")
    
    def test_great_expectations_suite_syntax(self, jinja_env):
        """Test Great Expectations suite template has valid syntax."""
        try:
            template = jinja_env.get_template("quality/great_expectations_suite.py.j2")
            assert template is not None
            
            rendered = template.render(project_name="test_project")
            assert "import great_expectations" in rendered
            assert "def create_expectation_suite" in rendered
        except Exception as e:
            pytest.fail(f"Great Expectations suite template error: {e}")
    
    def test_soda_checks_syntax(self, jinja_env):
        """Test Soda checks template has valid syntax."""
        try:
            template = jinja_env.get_template("quality/soda_checks.yml.j2")
            assert template is not None
            
            # Test rendering with PostgreSQL
            rendered = template.render(
                project_name="test_project",
                stack={"storage": "PostgreSQL"},
                secrets={"postgres_user": "test", "postgres_password": "test"}
            )
            assert "data_source" in rendered
            assert "checks for" in rendered
        except Exception as e:
            pytest.fail(f"Soda checks template error: {e}")
    
    def test_great_expectations_multi_storage_support(self, jinja_env):
        """Test GE config supports multiple storage backends."""
        template = jinja_env.get_template("quality/great_expectations_config.yml.j2")
        
        # Test PostgreSQL
        postgres_render = template.render(
            project_name="test",
            stack={"storage": "PostgreSQL"},
            secrets={"postgres_user": "u", "postgres_password": "p"}
        )
        assert "postgresql://" in postgres_render
        
        # Test Snowflake
        snowflake_render = template.render(
            project_name="test",
            stack={"storage": "Snowflake"},
            secrets={
                "snowflake_user": "u",
                "snowflake_password": "p",
                "snowflake_account": "acc",
                "snowflake_warehouse": "wh"
            }
        )
        assert "snowflake://" in snowflake_render
        
        # Test BigQuery
        bigquery_render = template.render(
            project_name="test",
            stack={"storage": "BigQuery"},
            secrets={"bigquery_project": "proj"}
        )
        assert "bigquery://" in bigquery_render
    
    def test_soda_checks_completeness(self, jinja_env):
        """Test Soda checks template includes all check types."""
        template = jinja_env.get_template("quality/soda_checks.yml.j2")
        rendered = template.render(
            project_name="test",
            stack={"storage": "PostgreSQL"},
            secrets={"postgres_user": "u", "postgres_password": "p"}
        )
        
        # Verify main check categories exist
        assert "row_count" in rendered
        assert "missing_count" in rendered
        assert "duplicate_count" in rendered
        assert "anomaly_score" in rendered or "anomaly_detector" in rendered
        assert "failed rows:" in rendered
