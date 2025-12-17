"""
Configuration Profiles System
==============================

Allows users to save, load, and share stack configurations.
Includes built-in presets for common patterns.
"""

from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class StackProfile:
    """Represents a saved stack configuration"""
    name: str
    description: str
    stack: Dict[str, str]
    created_at: str
    updated_at: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'StackProfile':
        """Create from dictionary"""
        return cls(**data)


class ConfigurationProfile:
    """
    Manage configuration profiles for AntiGravity stacks.
    
    Profiles are stored in ~/.antigravity/profiles/
    """
    
    PROFILES_DIR = Path.home() / ".antigravity" / "profiles"
    
    # Built-in presets
    PRESETS = {
        "modern_data_stack": StackProfile(
            name="modern_data_stack",
            description="Modern Data Stack with cloud-native tools",
            stack={
                "ingestion": "Airbyte",
                "storage": "Snowflake",
                "transformation": "dbt",
                "orchestration": "Prefect",
                "visualization": "Superset",
                "quality": "Great Expectations"
            },
            created_at=datetime.now().isoformat(),
            author="AntiGravity",
            tags=["cloud", "enterprise", "modern"]
        ),
        
        "analytics_starter": StackProfile(
            name="analytics_starter",
            description="Simple analytics stack for beginners",
            stack={
                "ingestion": "DLT",
                "storage": "PostgreSQL",
                "transformation": "dbt",
                "orchestration": "Airflow"
            },
            created_at=datetime.now().isoformat(),
            author="AntiGravity",
            tags=["beginner", "local", "analytics"]
        ),
        
        "streaming_platform": StackProfile(
            name="streaming_platform",
            description="Real-time streaming data platform",
            stack={
                "ingestion": "Kafka",
                "storage": "MongoDB",
                "transformation": "Spark",
                "orchestration": "Dagster",
                "monitoring": "Prometheus",
                "visualization": "Grafana"
            },
            created_at=datetime.now().isoformat(),
            author="AntiGravity",
            tags=["streaming", "real-time", "advanced"]
        ),
        
        "ml_platform": StackProfile(
            name="ml_platform",
            description="MLOps platform with experiment tracking",
            stack={
                "ingestion": "DLT",
                "storage": "PostgreSQL",
                "transformation": "Spark",
                "orchestration": "Airflow",
                "monitoring": "Prometheus"
            },
            created_at=datetime.now().isoformat(),
            author="AntiGravity",
            tags=["ml", "mlops", "advanced"]
        ),
        
        "data_lakehouse": StackProfile(
            name="data_lakehouse",
            description="Data lakehouse architecture with DuckDB",
            stack={
                "ingestion": "Airbyte",
                "storage": "DuckDB",
                "transformation": "dbt",
                "orchestration": "Dagster",
                "visualization": "Metabase"
            },
            created_at=datetime.now().isoformat(),
            author="AntiGravity",
            tags=["lakehouse", "duckdb", "modern"]
        )
    }
    
    @classmethod
    def _ensure_profile_dir(cls):
        """Create profiles directory if it doesn't exist"""
        cls.PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def save(
        cls, 
        name: str, 
        stack: Dict[str, str], 
        description: str = "",
        author: Optional[str] = None,
        tags: Optional[List[str]] = None,
        overwrite: bool = False
    ) -> StackProfile:
        """
        Save a configuration profile.
        
        Args:
            name: Profile name (alphanumeric + underscores)
            stack: Stack configuration dict
            description: Human-readable description
            author: Optional author name
            tags: Optional tags for categorization
            overwrite: If True, overwrite existing profile
        
        Returns:
            Created StackProfile
        
        Raises:
            ValueError: If profile exists and overwrite=False
        """
        cls._ensure_profile_dir()
        
        profile_path = cls.PROFILES_DIR / f"{name}.json"
        
        if profile_path.exists() and not overwrite:
            raise ValueError(f"Profile '{name}' already exists. Use overwrite=True to replace.")
        
        # Load existing profile if updating
        if profile_path.exists():
            existing = cls.load(name)
            profile = StackProfile(
                name=name,
                description=description or existing.description,
                stack=stack,
                created_at=existing.created_at,
                updated_at=datetime.now().isoformat(),
                author=author or existing.author,
                tags=tags or existing.tags
            )
        else:
            profile = StackProfile(
                name=name,
                description=description,
                stack=stack,
                created_at=datetime.now().isoformat(),
                author=author,
                tags=tags
            )
        
        with open(profile_path, 'w') as f:
            json.dump(profile.to_dict(), f, indent=2)
        
        return profile
    
    @classmethod
    def load(cls, name: str) -> StackProfile:
        """
        Load a configuration profile.
        
        Args:
            name: Profile name
        
        Returns:
            StackProfile
        
        Raises:
            FileNotFoundError: If profile doesn't exist
        """
        # Check built-in presets first
        if name in cls.PRESETS:
            return cls.PRESETS[name]
        
        profile_path = cls.PROFILES_DIR / f"{name}.json"
        
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile '{name}' not found")
        
        with open(profile_path) as f:
            data = json.load(f)
            return StackProfile.from_dict(data)
    
    @classmethod
    def delete(cls, name: str) -> bool:
        """
        Delete a configuration profile.
        
        Args:
            name: Profile name
        
        Returns:
            True if deleted, False if not found
        
        Raises:
            ValueError: If trying to delete built-in preset
        """
        if name in cls.PRESETS:
            raise ValueError(f"Cannot delete built-in preset '{name}'")
        
        profile_path = cls.PROFILES_DIR / f"{name}.json"
        
        if profile_path.exists():
            profile_path.unlink()
            return True
        
        return False
    
    @classmethod
    def list_profiles(cls, include_presets: bool = True) -> List[str]:
        """
        List all available profiles.
        
        Args:
            include_presets: If True, include built-in presets
        
        Returns:
            List of profile names
        """
        profiles = []
        
        if include_presets:
            profiles.extend(cls.PRESETS.keys())
        
        if cls.PROFILES_DIR.exists():
            user_profiles = [p.stem for p in cls.PROFILES_DIR.glob("*.json")]
            profiles.extend(user_profiles)
        
        return sorted(set(profiles))
    
    @classmethod
    def list_detailed(cls, include_presets: bool = True) -> List[StackProfile]:
        """
        List all profiles with full details.
        
        Args:
            include_presets: If True, include built-in presets
        
        Returns:
            List of StackProfile objects
        """
        profile_names = cls.list_profiles(include_presets=include_presets)
        return [cls.load(name) for name in profile_names]
    
    @classmethod
    def search(cls, query: str = "", tags: Optional[List[str]] = None) -> List[StackProfile]:
        """
        Search profiles by name, description, or tags.
        
        Args:
            query: Search query (matches name or description)
            tags: Filter by tags
        
        Returns:
            List of matching StackProfiles
        """
        all_profiles = cls.list_detailed(include_presets=True)
        results = []
        
        for profile in all_profiles:
            # Check query match
            query_match = (
                not query or
                query.lower() in profile.name.lower() or
                query.lower() in profile.description.lower()
            )
            
            # Check tags match
            tags_match = (
                not tags or
                (profile.tags and any(tag in profile.tags for tag in tags))
            )
            
            if query_match and tags_match:
                results.append(profile)
        
        return results
    
    @classmethod
    def export_profile(cls, name: str, output_path: Path) -> None:
        """
        Export a profile to a file.
        
        Args:
            name: Profile name
            output_path: Path to export to
        """
        profile = cls.load(name)
        
        with open(output_path, 'w') as f:
            json.dump(profile.to_dict(), f, indent=2)
    
    @classmethod
    def import_profile(cls, input_path: Path, overwrite: bool = False) -> StackProfile:
        """
        Import a profile from a file.
        
        Args:
            input_path: Path to import from
            overwrite: If True, overwrite existing profile
        
        Returns:
            Imported StackProfile
        """
        with open(input_path) as f:
            data = json.load(f)
            profile = StackProfile.from_dict(data)
        
        return cls.save(
            name=profile.name,
            stack=profile.stack,
            description=profile.description,
            author=profile.author,
            tags=profile.tags,
            overwrite=overwrite
        )
    
    @classmethod
    def get_preset_names(cls) -> List[str]:
        """Get list of built-in preset names"""
        return list(cls.PRESETS.keys())
    
    @classmethod
    def is_preset(cls, name: str) -> bool:
        """Check if a profile is a built-in preset"""
        return name in cls.PRESETS
