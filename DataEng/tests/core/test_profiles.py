"""
Tests for Configuration Profiles System
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from core.profiles import ConfigurationProfile, StackProfile


class TestConfigurationProfile:
    """Test suite for configuration profiles"""
    
    @pytest.fixture
    def temp_profiles_dir(self, monkeypatch):
        """Create temporary profiles directory"""
        temp_dir = Path(tempfile.mkdtemp(prefix="antigravity_profiles_"))
        monkeypatch.setattr(ConfigurationProfile, "PROFILESDIR", temp_dir)
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_save_and_load_profile(self, temp_profiles_dir):
        """Test saving and loading a profile"""
        stack = {
            "ingestion": "DLT",
           "storage": "PostgreSQL",
            "transformation": "dbt"
        }
        
        profile = ConfigurationProfile.save(
            name="test_profile",
            stack=stack,
            description="Test profile"
        )
        
        assert profile.name == "test_profile"
        assert profile.stack == stack
        
        # Load it back
        loaded = ConfigurationProfile.load("test_profile")
        assert loaded.name == "test_profile"
        assert loaded.stack == stack
    
    def test_list_profiles(self, temp_profiles_dir):
        """Test listing profiles"""
        # Save a few profiles
        ConfigurationProfile.save("profile1", {"storage": "PostgreSQL"}, "First")
        ConfigurationProfile.save("profile2", {"storage": "Snowflake"}, "Second")
        
        profiles = ConfigurationProfile.list_profiles(include_presets=False)
        
        assert "profile1" in profiles
        assert "profile2" in profiles
    
    def test_builtin_presets_exist(self):
        """Test that built-in presets are available"""
        presets = ConfigurationProfile.get_preset_names()
        
        assert "modern_data_stack" in presets
        assert "analytics_starter" in presets
        assert "streaming_platform" in presets
        assert "ml_platform" in presets
        assert "data_lakehouse" in presets
    
    def test_load_builtin_preset(self):
        """Test loading a built-in preset"""
        preset = ConfigurationProfile.load("modern_data_stack")
        
        assert preset.name == "modern_data_stack"
        assert "ingestion" in preset.stack
        assert "storage" in preset.stack
        assert preset.description != ""
    
    def test_cannot_delete_preset(self):
        """Test that built-in presets cannot be deleted"""
        with pytest.raises(ValueError):
            ConfigurationProfile.delete("modern_data_stack")
    
    def test_delete_user_profile(self, temp_profiles_dir):
        """Test deleting a user profile"""
        ConfigurationProfile.save("deleteme", {"storage": "PostgreSQL"}, "To delete")
        
        assert ConfigurationProfile.delete("deleteme") is True
        
        with pytest.raises(FileNotFoundError):
            ConfigurationProfile.load("deleteme")
    
    def test_overwrite_profile(self, temp_profiles_dir):
        """Test overwriting an existing profile"""
        ConfigurationProfile.save("overwrite_test", {"storage": "PostgreSQL"}, "Original")
        
        # Should fail without overwrite=True
        with pytest.raises(ValueError):
            ConfigurationProfile.save("overwrite_test", {"storage": "Snowflake"}, "Updated")
        
        # Should succeed with overwrite=True
        updated = ConfigurationProfile.save(
            "overwrite_test",
            {"storage": "Snowflake"},
            "Updated",
            overwrite=True
        )
        
        assert updated.stack["storage"] == "Snowflake"
        assert updated.description == "Updated"
    
    def test_profile_with_tags(self, temp_profiles_dir):
        """Test saving and loading profile with tags"""
        profile = ConfigurationProfile.save(
            "tagged",
            {"storage": "PostgreSQL"},
            "Tagged profile",
            tags=["test", "postgres", "local"]
        )
        
        assert profile.tags == ["test", "postgres", "local"]
        
        loaded = ConfigurationProfile.load("tagged")
        assert loaded.tags == ["test", "postgres", "local"]
    
    def test_search_by_query(self, temp_profiles_dir):
        """Test searching profiles by query"""
        ConfigurationProfile.save("pg_local", {"storage": "PostgreSQL"}, "Local PostgreSQL")
        ConfigurationProfile.save("sf_cloud", {"storage": "Snowflake"}, "Cloud Snowflake")
        
        results = ConfigurationProfile.search(query="postgres")
        
        assert len(results) == 1
        assert results[0].name == "pg_local"
    
    def test_search_by_tags(self, temp_profiles_dir):
        """Test searching profiles by tags"""
        ConfigurationProfile.save("p1", {"storage": "PostgreSQL"}, "First", tags=["local", "sql"])
        ConfigurationProfile.save("p2", {"storage": "MongoDB"}, "Second", tags=["local", "nosql"])
        ConfigurationProfile.save("p3", {"storage": "Snowflake"}, "Third", tags=["cloud", "sql"])
        
        results = ConfigurationProfile.search(tags=["cloud"])
        
        assert len(results) == 1
        assert results[0].name == "p3"
    
    def test_export_and_import_profile(self, temp_profiles_dir, tmp_path):
        """Test exporting and importing profiles"""
        # Create and save a profile
        ConfigurationProfile.save(
            "export_test",
            {"storage": "PostgreSQL", "orchestration": "Airflow"},
            "Export test profile",
            tags=["test"]
        )
        
        # Export it
        export_path = tmp_path / "exported_profile.json"
        ConfigurationProfile.export_profile("export_test", export_path)
        
        assert export_path.exists()
        
        # Delete original
        ConfigurationProfile.delete("export_test")
        
        # Import it back
        imported = ConfigurationProfile.import_profile(export_path)
        
        assert imported.name == "export_test"
        assert imported.stack["storage"] == "PostgreSQL"
        assert imported.tags == ["test"]
    
    def test_list_detailed(self, temp_profiles_dir):
        """Test listing profiles with full details"""
        ConfigurationProfile.save("detailed1", {"storage": "PostgreSQL"}, "First")
        ConfigurationProfile.save("detailed2", {"storage": "Snowflake"}, "Second")
        
        profiles = ConfigurationProfile.list_detailed(include_presets=False)
        
        assert len(profiles) >= 2
        assert all(isinstance(p, StackProfile) for p in profiles)
    
    def test_is_preset(self):
        """Test checking if profile is a preset"""
        assert ConfigurationProfile.is_preset("modern_data_stack") is True
        assert ConfigurationProfile.is_preset("analytics_starter") is True
        assert ConfigurationProfile.is_preset("nonexistent") is False
    
    def test_profile_timestamps(self, temp_profiles_dir):
        """Test profile creation and update timestamps"""
        profile = ConfigurationProfile.save("timestamp_test", {"storage": "PostgreSQL"}, "Test")
        
        assert profile.created_at is not None
        assert profile.updated_at is None
        
        # Update it
        updated = ConfigurationProfile.save(
            "timestamp_test",
            {"storage": "Snowflake"},
            "Updated",
            overwrite=True
        )
        
        assert updated.created_at == profile.created_at
        assert updated.updated_at is not None
        assert updated.updated_at != updated.created_at
