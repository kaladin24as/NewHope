"""
Tests for Custom Template Support
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from core.template_loader import TemplateLoader, TemplateManager


class TestTemplateLoader:
    """Test template loader functionality"""
    
    @pytest.fixture
    def temp_user_templates(self, monkeypatch):
        """Create temporary user templates directory"""
        temp_dir = Path(tempfile.mkdtemp(prefix="user_templates_"))
        monkeypatch.setattr(TemplateLoader, "USER_TEMPLATES", temp_dir)
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_get_template_env(self):
        """Test creating Jinja2 environment"""
        loader = TemplateLoader()
        env = loader.get_template_env()
        
        assert env is not None
        assert env.loader is not None
    
    def test_override_template(self, temp_user_templates, tmp_path):
        """Test overriding a template"""
        # Create a custom template
        custom_template = tmp_path / "custom_dag.py.j2"
        custom_template.write_text("# Custom Airflow DAG\nprint('custom')")
        
        # Override
        result_path = TemplateLoader.override_template(
            "orchestration",
            "airflow_dag.py.j2",
            custom_template
        )
        
        assert result_path.exists()
        assert "Custom Airflow DAG" in result_path.read_text()
    
    def test_reset_template(self, temp_user_templates, tmp_path):
        """Test resetting a template to default"""
        # First create an override
        custom_template = tmp_path / "custom.j2"
        custom_template.write_text("custom content")
        
        TemplateLoader.override_template("common", "test.j2", custom_template)
        
        # Reset it
        assert TemplateLoader.reset_template("common", "test.j2") is True
        
        # Try resetting non-existent override
        assert TemplateLoader.reset_template("common", "nonexistent.j2") is False
    
    def test_list_overrides(self, temp_user_templates, tmp_path):
        """Test listing user overrides"""
        # Create some overrides
        for i in range(3):
            custom = tmp_path / f"custom{i}.j2"
            custom.write_text(f"content {i}")
            TemplateLoader.override_template("test", f"template{i}.j2", custom)
        
        overrides = TemplateLoader.list_overrides()
        
        assert len(overrides) == 3
        assert any("template0.j2" in o for o in overrides)
    
    def test_get_template_info_default_only(self):
        """Test getting info for default template"""
        info = TemplateLoader.get_template_info("common/README.md.j2")
        
        assert info["has_default"] is True
        assert info["active_source"] == "default"
    
    def test_get_template_info_with_override(self, temp_user_templates, tmp_path):
        """Test getting info for overridden template"""
        custom = tmp_path / "custom.j2"
        custom.write_text("override")
        TemplateLoader.override_template("common", "README.md.j2", custom)
        
        info = TemplateLoader.get_template_info("common/README.md.j2")
        
        assert info["has_default"] is True
        assert info["has_override"] is True
        assert info["active_source"] == "user"
    
    def test_export_template(self, tmp_path):
        """Test exporting a template"""
        output_file = tmp_path / "exported.j2"
        
        TemplateLoader.export_template("common/README.md.j2", output_file)
        
        assert output_file.exists()
        assert len(output_file.read_text()) > 0
    
    def test_clear_all_overrides(self, temp_user_templates, tmp_path):
        """Test clearing all overrides"""
        # Create overrides
        for i in range(5):
            custom = tmp_path / f"custom{i}.j2"
            custom.write_text(f"content {i}")
            TemplateLoader.override_template("test", f"template{i}.j2", custom)
        
        count = TemplateLoader.clear_all_overrides()
        
        assert count == 5
assert len(TemplateLoader.list_overrides()) == 0


class TestTemplateManager:
    """Test template manager high-level interface"""
    
    @pytest.fixture
    def manager(self, monkeypatch):
        """Create template manager with temp user directory"""
        temp_dir = Path(tempfile.mkdtemp(prefix="manager_templates_"))
        monkeypatch.setattr(TemplateLoader, "USER_TEMPLATES", temp_dir)
        
        manager = TemplateManager()
        yield manager
        
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_override_template(self, manager, tmp_path):
        """Test overriding via manager"""
        custom = tmp_path / "custom.j2"
        custom.write_text("custom content")
        
        manager.override("orchestration/airflow_dag.py.j2", custom)
        
        overrides = TemplateLoader.list_overrides()
        assert any("airflow_dag.py.j2" in o for o in overrides)
    
    def test_reset_template(self, manager, tmp_path):
        """Test resetting via manager"""
        custom = tmp_path / "custom.j2"
        custom.write_text("custom")
        
        manager.override("common/test.j2", custom)
        assert manager.reset("common/test.j2") is True
    
    def test_list_all_templates(self, manager):
        """Test listing all templates"""
        templates = manager.list_all()
        
        assert len(templates) > 0
        assert all("path" in t for t in templates)
        assert all("has_default" in t for t in templates)
    
    def test_list_overrides_only(self, manager, tmp_path):
        """Test listing only overridden templates"""
        # Create an override
        custom = tmp_path / "custom.j2"
        custom.write_text("custom")
        manager.override("test/template.j2", custom)
        
        overrides = manager.list_all(include_overrides_only=True)
        
        assert len(overrides) > 0
        assert all(t["has_override"] for t in overrides)
    
    def test_export_template(self, manager, tmp_path):
        """Test exporting via manager"""
        output = tmp_path / "exported.j2"
        
        manager.export("common/README.md.j2", output)
        
        assert output.exists()
    
    def test_clear_all(self, manager, tmp_path):
        """Test clearing all via manager"""
        # Create overrides
        for i in range(3):
            custom = tmp_path / f"custom{i}.j2"
            custom.write_text(f"content {i}")
            manager.override(f"test/template{i}.j2", custom)
        
        count = manager.clear_all()
        assert count == 3
