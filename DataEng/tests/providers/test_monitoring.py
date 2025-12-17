"""
Tests for Monitoring providers (Phase 3)
"""
import pytest
import os
import json
from jinja2 import Environment, FileSystemLoader


@pytest.fixture
def jinja_env():
    """Create Jinja2 environment for template loading."""
    template_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "backend", "templates"
    )
    return Environment(loader=FileSystemLoader(template_dir))


class TestMonitoringTemplates:
    """Tests for monitoring Jinja2 templates."""
    
    def test_prometheus_compose_template_exists(self):
        """Test Prometheus compose template exists."""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "backend", "templates", "monitoring", "prometheus_compose.yml.j2"
        )
        assert os.path.exists(template_path), "Prometheus compose template not found"
    
    def test_prometheus_config_template_exists(self):
        """Test Prometheus config template exists."""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "backend", "templates", "monitoring", "prometheus_config.yml.j2"
        )
        assert os.path.exists(template_path), "Prometheus config template not found"
    
    def test_grafana_dashboard_template_exists(self):
        """Test Grafana dashboard template exists."""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "backend", "templates", "monitoring", "grafana_monitoring_dashboard.json.j2"
        )
        assert os.path.exists(template_path), "Grafana dashboard template not found"
    
    def test_prometheus_alerts_template_exists(self):
        """Test Prometheus alerts template exists."""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "backend", "templates", "monitoring", "prometheus_alerts.yml.j2"
        )
        assert os.path.exists(template_path), "Prometheus alerts template not found"
    
    def test_prometheus_compose_syntax(self, jinja_env):
        """Test Prometheus compose template has valid syntax."""
        try:
            template = jinja_env.get_template("monitoring/prometheus_compose.yml.j2")
            assert template is not None
            
            rendered = template.render(
                project_name="test",
                ports={"prometheus": 9090, "alertmanager": 9093},
                stack={"storage": "PostgreSQL"},
                secrets={}
            )
            assert "prometheus:" in rendered
            assert "alertmanager:" in rendered
            assert "node_exporter:" in rendered
            assert "cadvisor:" in rendered
        except Exception as e:
            pytest.fail(f"Prometheus compose template error: {e}")
    
    def test_prometheus_config_syntax(self, jinja_env):
        """Test Prometheus config template has valid syntax."""
        try:
            template = jinja_env.get_template("monitoring/prometheus_config.yml.j2")
            assert template is not None
            
            rendered = template.render(
                project_name="test",
                stack={"storage": "PostgreSQL", "orchestration": "Airflow"},
                secrets={"airflow_admin_password": "test"}
            )
            assert "global:" in rendered
            assert "scrape_configs:" in rendered
            assert "job_name:" in rendered
        except Exception as e:
            pytest.fail(f"Prometheus config template error:{e}")
    
    def test_grafana_dashboard_syntax(self, jinja_env):
        """Test Grafana dashboard template has valid syntax and JSON."""
        try:
            template = jinja_env.get_template("monitoring/grafana_monitoring_dashboard.json.j2")
            assert template is not None
            
            rendered = template.render(
                project_name="test_monitoring",
                stack={"storage": "PostgreSQL"}
            )
            
            # Verify it's valid JSON
            dashboard_json = json.loads(rendered)
            assert "panels" in dashboard_json
            assert "title" in dashboard_json
            assert dashboard_json["title"] == "test_monitoring - Infrastructure Monitoring"
        except json.JSONDecodeError as e:
            pytest.fail(f"Grafana dashboard is not valid JSON: {e}")
        except Exception as e:
            pytest.fail(f"Grafana dashboard template error: {e}")
    
    def test_prometheus_alerts_syntax(self, jinja_env):
        """Test Prometheus alerts template has valid syntax."""
        try:
            template = jinja_env.get_template("monitoring/prometheus_alerts.yml.j2")
            assert template is not None
            
            rendered = template.render(
                project_name="test",
                stack={"storage": "PostgreSQL", "orchestration": "Airflow"}
            )
            assert "groups:" in rendered
            assert "alert:" in rendered
            assert "expr:" in rendered
        except Exception as e:
            pytest.fail(f"Prometheus alerts template error: {e}")
    
    def test_prometheus_conditional_exporters(self, jinja_env):
        """Test Prometheus compose includes conditional exporters."""
        template = jinja_env.get_template("monitoring/prometheus_compose.yml.j2")
        
        # With PostgreSQL
        with_postgres = template.render(
            project_name="test",
            ports={"prometheus": 9090, "alertmanager": 9093},
            stack={"storage": "PostgreSQL"},
            secrets={"postgres_user": "u", "postgres_password": "p"}
        )
        assert "postgres_exporter:" in with_postgres
        
        # Without PostgreSQL
        without_postgres = template.render(
            project_name="test",
            ports={"prometheus": 9090, "alertmanager": 9093},
            stack={"storage": "Snowflake"},
            secrets={}
        )
        assert "postgres_exporter:" not in without_postgres
    
    def test_prometheus_scrape_configs_dynamic(self, jinja_env):
        """Test Prometheus config has dynamic scrape targets."""
        template = jinja_env.get_template("monitoring/prometheus_config.yml.j2")
        
        rendered = template.render(
            project_name="test",
            stack={
                "storage": "PostgreSQL",
                "orchestration": "Airflow",
                "visualization": "Grafana"
            },
            secrets={"airflow_admin_password": "test"}
        )
        
        # Check conditional jobs exist
        assert "job_name: 'postgres'" in rendered
        assert "job_name: 'airflow'" in rendered
        assert "job_name: 'grafana'" in rendered
    
    def test_prometheus_alerts_comprehensive(self, jinja_env):
        """Test Prometheus alerts include all critical alerts."""
        template = jinja_env.get_template("monitoring/prometheus_alerts.yml.j2")
        
        rendered = template.render(
            project_name="test",
            stack={"storage": "PostgreSQL", "orchestration": "Airflow"}
        )
        
        # Infrastructure alerts
        assert "HighCPUUsage" in rendered
        assert "HighMemoryUsage" in rendered
        assert "ContainerDown" in rendered
        
        # PostgreSQL alerts
        assert "PostgreSQLDown" in rendered or "PostgreSQL" in rendered
        
        # Airflow alerts (conditional)
        assert "AirflowSchedulerDown" in rendered or "Airflow" in rendered
        
        # Data pipeline alerts
        assert "DataPipelineStale" in rendered or "DataQualityFailure" in rendered
        
        # Disk space
        assert "DiskSpace" in rendered
    
    def test_grafana_dashboard_panels(self, jinja_env):
        """Test Grafana dashboard has required panels."""
        template = jinja_env.get_template("monitoring/grafana_monitoring_dashboard.json.j2")
        
        rendered = template.render(
            project_name="test",
            stack={"storage": "PostgreSQL"}
        )
        
        dashboard = json.loads(rendered)
        panels = dashboard["panels"]
        
        assert len(panels) >= 2, "Dashboard should have at least 2 panels"
        
        # Check for CPU and Memory panels
        panel_titles = [p["title"] for p in panels]
        assert any("CPU" in title for title in panel_titles)
        assert any("Memory" in title for title in panel_titles)
