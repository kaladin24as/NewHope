"""
Tests for Project Updater
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import yaml
from core.updater import ProjectUpdater, ProjectMetadata, UpdatePlan
from core.engine import TemplateEngine
import uuid


class TestProjectMetadata:
    """Test project metadata management"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory"""
        temp_dir = Path(tempfile.mkdtemp(prefix="test_project_"))
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_create_metadata(self):
        """Test metadata creation"""
        metadata = ProjectMetadata.create(
            project_name="test_project",
            stack={"storage": "PostgreSQL", "orchestration": "Airflow"}
        )
        
        assert metadata["project"]["name"] == "test_project"
        assert metadata["project"]["stack"]["storage"] == "PostgreSQL"
        assert metadata["antigravity"]["version"] is not None
        assert metadata["antigravity"]["generated_at"] is not None
    
    def test_write_and_read_metadata(self, temp_project_dir):
        """Test writing and reading metadata"""
        metadata = ProjectMetadata.create(
            project_name="test_project",
            stack={"storage": "PostgreSQL"}
        )
        
        ProjectMetadata.write(temp_project_dir, metadata)
        
        metadata_file = temp_project_dir / ".antigravity.yml"
        assert metadata_file.exists()
        
        loaded = ProjectMetadata.read(temp_project_dir)
        assert loaded["project"]["name"] == "test_project"
        assert loaded["project"]["stack"]["storage"] == "PostgreSQL"
    
    def test_update_metadata(self, temp_project_dir):
        """Test updating metadata"""metadata = ProjectMetadata.create(
            project_name="test_project",
            stack={"storage": "PostgreSQL"}
        )
        
        ProjectMetadata.write(temp_project_dir, metadata)
        
        # Update stack
        ProjectMetadata.update(
            temp_project_dir,
            **{"project.stack": {"storage": "Snowflake", "orchestration": "Airflow"}}
        )
        
        updated = ProjectMetadata.read(temp_project_dir)
        assert updated["project"]["stack"]["storage"] == "Snowflake"
        assert updated["project"]["stack"]["orchestration"] == "Airflow"
        assert updated["antigravity"]["last_updated"] is not None
    
    def test_read_nonexistent_metadata(self, temp_project_dir):
        """Test reading metadata from non-AntiGravity project"""
        with pytest.raises(FileNotFoundError):
            ProjectMetadata.read(temp_project_dir)


class TestUpdatePlan:
    """Test update plan functionality"""
    
    def test_empty_plan_has_no_changes(self):
        """Test that empty plan reports no changes"""
        plan = UpdatePlan()
        assert not plan.has_changes()
    
    def test_plan_with_additions(self):
        """Test plan with file additions"""
        plan = UpdatePlan(add_files=["file1.txt", "file2.txt"])
        assert plan.has_changes()
    
    def test_plan_with_updates(self):
        """Test plan with file updates"""
        from core.updater import FileChange
        plan = UpdatePlan(update_files=[
            FileChange(path="file1.txt", change_type="update")
        ])
        assert plan.has_changes()


class TestProjectUpdater:
    """Test project updater"""
    
    @pytest.fixture
    def sample_project(self):
        """Create a sample project for testing"""
        temp_dir = Path(tempfile.mkdtemp(prefix="antigravity_test_"))
        
        # Generate initial project
        engine = TemplateEngine()
        stack = {"storage": "PostgreSQL", "orchestration": "Airflow"}
        vfs = engine.generate("test_project", stack, str(uuid.uuid4()))
        vfs.flush(str(temp_dir))
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_is_antigravity_project(self, sample_project):
        """Test detecting AntiGravity projects"""
        assert ProjectUpdater.is_antigravity_project(sample_project)
        
        # Non-AntiGravity directory
        temp_dir = Path(tempfile.mkdtemp())
        assert not ProjectUpdater.is_antigravity_project(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_load_existing_project(self, sample_project):
        """Test loading an existing project"""
        updater = ProjectUpdater(sample_project)
        
        assert updater.metadata is not None
        assert updater.current_stack is not None
        assert "storage" in updater.current_stack
    
    def test_analyze_no_changes(self, sample_project):
        """Test analyzing when there are no changes"""
        updater = ProjectUpdater(sample_project)
        plan = updater.analyze_changes(updater.current_stack)
        
        assert not plan.has_changes()
    
    def test_analyze_add_provider(self, sample_project):
        """Test analyzing when adding a provider"""
        updater = ProjectUpdater(sample_project)
        
        new_stack = updater.current_stack.copy()
        new_stack["transformation"] = "dbt"
        
        plan = updater.analyze_changes(new_stack)
        
        assert plan.has_changes()
        assert "transformation/dbt" in plan.add_files
    
    def test_analyze_remove_provider(self, sample_project):
        """Test analyzing when removing a provider"""
        updater = ProjectUpdater(sample_project)
        
        new_stack = updater.current_stack.copy()
        del new_stack["orchestration"]
        
        plan = updater.analyze_changes(new_stack)
        
        assert plan.has_changes()
        assert "orchestration/Airflow" in plan.remove_files
    
    def test_analyze_replace_provider(self, sample_project):
        """Test analyzing when replacing a provider"""
        updater = ProjectUpdater(sample_project)
        
        new_stack = updater.current_stack.copy()
        new_stack["storage"] = "Snowflake"
        
        plan = updater.analyze_changes(new_stack)
        
        assert plan.has_changes()
        assert "storage/PostgreSQL" in plan.remove_files
        assert "storage/Snowflake" in plan.add_files
    
    def test_update_noninteractive(self, sample_project):
        """Test updating project in non-interactive mode"""
        updater = ProjectUpdater(sample_project)
        
        # Add dbt
        new_stack = updater.current_stack.copy()
        new_stack["transformation"] = "dbt"
        
        plan = updater.update(new_stack=new_stack, interactive=False)
        
        assert plan.has_changes()
        
        # Verify metadata was updated
        updated_metadata = ProjectMetadata.read(sample_project)
        assert "transformation" in updated_metadata["project"]["stack"]
        assert updated_metadata["project"]["stack"]["transformation"] == "dbt"
    
    def test_update_with_add_providers(self, sample_project):
        """Test updating by adding specific providers"""
        updater = ProjectUpdater(sample_project)
        
        plan = updater.update(
            add_providers=[("transformation", "dbt"), ("infrastructure", "terraform")],
            interactive=False
        )
        
        assert plan.has_changes()
        
        # Check metadata
        metadata = ProjectMetadata.read(sample_project)
        assert metadata["project"]["stack"]["transformation"] == "dbt"
        assert metadata["project"]["stack"]["infrastructure"] == "terraform"
    
    def test_update_with_remove_providers(self, sample_project):
        """Test updating by removing providers"""
        updater = ProjectUpdater(sample_project)
        
        plan = updater.update(
            remove_providers=["orchestration"],
            interactive=False
        )
        
        assert plan.has_changes()
        
        # Check metadata
        metadata = ProjectMetadata.read(sample_project)
        assert "orchestration" not in metadata["project"]["stack"]
    
    def test_updater_invalid_project(self):
        """Test updater with invalid project path"""
        with pytest.raises(FileNotFoundError):
            ProjectUpdater(Path("/nonexistent/path"))
    
    def test_updater_non_antigravity_project(self):
        """Test updater with non-AntiGravity project"""
        temp_dir = Path(tempfile.mkdtemp())
        
        with pytest.raises(ValueError):
            ProjectUpdater(temp_dir)
        
        shutil.rmtree(temp_dir)
