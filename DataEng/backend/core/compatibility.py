"""
Compatibility matrix and validation for provider combinations.
Ensures selected providers can work together and suggests alternatives when incompatible.
"""

from typing import Dict, List, Tuple, Set, Optional
from enum import Enum


class CompatibilityLevel(str, Enum):
    """Level of compatibility between two providers."""
    FULLY_COMPATIBLE = "fully_compatible"
    COMPATIBLE_WITH_CONFIG = "compatible_with_config"
    LIMITED_COMPATIBILITY = "limited_compatibility"
    INCOMPATIBLE = "incompatible"


class ProviderCompatibility:
    """
    Defines compatibility rules between different providers.
    Used to validate stack combinations and suggest fixes.
    """
    
    # Define which storage providers are compatible with which ingestion tools
    INGESTION_STORAGE_COMPATIBILITY = {
        "DLT": {
            "compatible": ["PostgreSQL", "Snowflake", "DuckDB", "BigQuery", "Redshift"],
            "incompatible": [],
            "notes": {
                "PostgreSQL": "Requires dlt[postgres] package",
                "Snowflake": "Requires dlt[snowflake] package",
                "BigQuery": "Requires dlt[bigquery] package"
            }
        },
        "Airbyte": {
            "compatible": ["PostgreSQL", "Snowflake", "BigQuery", "Redshift", "MongoDB"],
            "incompatible": [],
            "notes": {
                "any": "Airbyte supports most destinations via connectors"
            }
        },
        "Kafka": {
            "compatible": ["PostgreSQL", "Snowflake", "BigQuery", "MongoDB"],
            "incompatible": [],
            "notes": {
                "any": "Requires Kafka Connect or custom consumer"
            }
        }
    }
    
    # Define which storage providers are compatible with which transformation tools
    TRANSFORMATION_STORAGE_COMPATIBILITY = {
        "dbt": {
            "compatible": ["PostgreSQL", "Snowflake", "BigQuery", "Redshift", "DuckDB"],
            "incompatible": ["MongoDB"],  # dbt doesn't support NoSQL
            "notes": {
                "PostgreSQL": "Requires dbt-postgres adapter",
                "Snowflake": "Requires dbt-snowflake adapter",
                "BigQuery": "Requires dbt-bigquery adapter",
                "MongoDB": "dbt requires SQL database"
            }
        },
        "Spark": {
            "compatible": ["PostgreSQL", "Snowflake", "BigQuery", "MongoDB", "DuckDB"],
            "incompatible": [],
            "notes": {
                "any": "Spark can read/write most data sources via connectors"
            }
        }
    }
    
    # Define which storage providers are compatible with which orchestration tools
    ORCHESTRATION_STORAGE_COMPATIBILITY = {
        "Airflow": {
            "compatible": ["PostgreSQL", "Snowflake", "BigQuery", "Redshift", "MongoDB", "DuckDB"],
            "incompatible": [],
            "notes": {
                "PostgreSQL": "Can use as metadata DB and data warehouse"
            }
        },
        "Prefect": {
            "compatible": ["PostgreSQL", "Snowflake", "BigQuery", "Redshift", "MongoDB", "DuckDB"],
            "incompatible": [],
            "notes": {}
        },
        "Dagster": {
            "compatible": ["PostgreSQL", "Snowflake", "BigQuery", "Redshift", "MongoDB", "DuckDB"],
            "incompatible": [],
            "notes": {}
        },
        "Mage": {
            "compatible": ["PostgreSQL", "Snowflake", "BigQuery", "Redshift", "DuckDB"],
            "incompatible": [],
            "notes": {}
        }
    }
    
    # Required dependencies for provider combinations
    PROVIDER_DEPENDENCIES = {
        ("ingestion:DLT", "storage:PostgreSQL"): ["dlt[postgres]"],
        ("ingestion:DLT", "storage:Snowflake"): ["dlt[snowflake]"],
        ("ingestion:DLT", "storage:BigQuery"): ["dlt[bigquery]"],
        ("transformation:dbt", "storage:PostgreSQL"): ["dbt-postgres"],
        ("transformation:dbt", "storage:Snowflake"): ["dbt-snowflake"],
        ("transformation:dbt", "storage:BigQuery"): ["dbt-bigquery"],
        ("transformation:dbt", "storage:Redshift"): ["dbt-redshift"],
        ("transformation:dbt", "storage:DuckDB"): ["dbt-duckdb"],
        ("transformation:Spark", "storage:PostgreSQL"): ["pyspark", "psycopg2-binary"],
        ("transformation:Spark", "storage:BigQuery"): ["pyspark", "google-cloud-bigquery"],
    }
    
    @staticmethod
    def check_compatibility(
        category1: str,
        provider1: str,
        category2: str,
        provider2: str
    ) -> Tuple[CompatibilityLevel, Optional[str]]:
        """
        Check if two providers are compatible.
        
        Args:
            category1: First provider category (e.g., "ingestion")
            provider1: First provider name (e.g., "DLT")
            category2: Second provider category (e.g., "storage")
            provider2: Second provider name (e.g., "PostgreSQL")
        
        Returns:
            Tuple of (compatibility_level, note)
        """
        # Check ingestion-storage compatibility
        if category1 == "ingestion" and category2 == "storage":
            return ProviderCompatibility._check_ingestion_storage(provider1, provider2)
        
        # Check transformation-storage compatibility
        elif category1 == "transformation" and category2 == "storage":
            return ProviderCompatibility._check_transformation_storage(provider1, provider2)
        
        # Check orchestration-storage compatibility
        elif category1 == "orchestration" and category2 == "storage":
            return ProviderCompatibility._check_orchestration_storage(provider1, provider2)
        
        # Default: assume compatible
        return (CompatibilityLevel.FULLY_COMPATIBLE, None)
    
    @staticmethod
    def _check_ingestion_storage(ingestion: str, storage: str) -> Tuple[CompatibilityLevel, Optional[str]]:
        """Check ingestion-storage compatibility."""
        compat_info = ProviderCompatibility.INGESTION_STORAGE_COMPATIBILITY.get(ingestion)
        if not compat_info:
            return (CompatibilityLevel.FULLY_COMPATIBLE, None)
        
        if storage in compat_info["incompatible"]:
            note = compat_info["notes"].get(storage, "Incompatible combination")
            return (CompatibilityLevel.INCOMPATIBLE, note)
        
        if storage in compat_info["compatible"]:
            note = compat_info["notes"].get(storage)
            if note:
                return (CompatibilityLevel.COMPATIBLE_WITH_CONFIG, note)
            return (CompatibilityLevel.FULLY_COMPATIBLE, None)
        
        return (CompatibilityLevel.LIMITED_COMPATIBILITY, "Compatibility not verified")
    
    @staticmethod
    def _check_transformation_storage(transformation: str, storage: str) -> Tuple[CompatibilityLevel, Optional[str]]:
        """Check transformation-storage compatibility."""
        compat_info = ProviderCompatibility.TRANSFORMATION_STORAGE_COMPATIBILITY.get(transformation)
        if not compat_info:
            return (CompatibilityLevel.FULLY_COMPATIBLE, None)
        
        if storage in compat_info["incompatible"]:
            note = compat_info["notes"].get(storage, "Incompatible combination")
            return (CompatibilityLevel.INCOMPATIBLE, note)
        
        if storage in compat_info["compatible"]:
            note = compat_info["notes"].get(storage)
            if note:
                return (CompatibilityLevel.COMPATIBLE_WITH_CONFIG, note)
            return (CompatibilityLevel.FULLY_COMPATIBLE, None)
        
        return (CompatibilityLevel.LIMITED_COMPATIBILITY, "Compatibility not verified")
    
    @staticmethod
    def _check_orchestration_storage(orchestration: str, storage: str) -> Tuple[CompatibilityLevel, Optional[str]]:
        """Check orchestration-storage compatibility."""
        compat_info = ProviderCompatibility.ORCHESTRATION_STORAGE_COMPATIBILITY.get(orchestration)
        if not compat_info:
            return (CompatibilityLevel.FULLY_COMPATIBLE, None)
        
        if storage in compat_info["compatible"]:
            note = compat_info["notes"].get(storage)
            if note:
                return (CompatibilityLevel.COMPATIBLE_WITH_CONFIG, note)
            return (CompatibilityLevel.FULLY_COMPATIBLE, None)
        
        return (CompatibilityLevel.LIMITED_COMPATIBILITY, "Compatibility not verified")
    
    @staticmethod
    def get_required_packages(
        category1: str,
        provider1: str,
        category2: str,
        provider2: str
    ) -> List[str]:
        """
        Get required packages for a provider combination.
        
        Args:
            category1: First provider category
            provider1: First provider name
            category2: Second provider category
            provider2: Second provider name
        
        Returns:
            List of required Python packages
        """
        key1 = (f"{category1}:{provider1}", f"{category2}:{provider2}")
        key2 = (f"{category2}:{provider2}", f"{category1}:{provider1}")
        
        packages = ProviderCompatibility.PROVIDER_DEPENDENCIES.get(key1, [])
        if not packages:
            packages = ProviderCompatibility.PROVIDER_DEPENDENCIES.get(key2, [])
        
        return packages


class StackValidator:
    """
    Validates entire technology stack for compatibility.
    """
    
    @staticmethod
    def validate_stack(stack: Dict[str, str]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a complete technology stack.
        
        Args:
            stack: Dictionary mapping category to provider name
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        categories = list(stack.keys())
        providers = list(stack.values())
        
        # Check pairwise compatibility
        for i in range(len(categories)):
            for j in range(i + 1, len(categories)):
                cat1, prov1 = categories[i], providers[i]
                cat2, prov2 = categories[j], providers[j]
                
                if not prov1 or not prov2:
                    continue
                
                level, note = ProviderCompatibility.check_compatibility(
                    cat1, prov1, cat2, prov2
                )
                
                if level == CompatibilityLevel.INCOMPATIBLE:
                    errors.append(
                        f"Incompatible combination: {cat1}:{prov1} + {cat2}:{prov2}. {note}"
                    )
                elif level == CompatibilityLevel.COMPATIBLE_WITH_CONFIG:
                    warnings.append(
                        f"{cat1}:{prov1} + {cat2}:{prov2}: {note}"
                    )
                elif level == CompatibilityLevel.LIMITED_COMPATIBILITY:
                    warnings.append(
                        f"{cat1}:{prov1} + {cat2}:{prov2}: {note}"
                    )
        
        # Special validations
        # dbt requires a storage layer
        if stack.get("transformation") == "dbt" and not stack.get("storage"):
            errors.append("dbt requires a storage/warehouse provider")
        
        # Ingestion requires storage
        if stack.get("ingestion") and not stack.get("storage"):
            warnings.append("Ingestion tools typically require a storage destination")
        
        is_valid = len(errors) == 0
        return (is_valid, errors, warnings)
    
    @staticmethod
    def suggest_alternatives(
        stack: Dict[str, str],
        incompatible_category: str
    ) -> List[str]:
        """
        Suggest alternative providers when there's an incompatibility.
        
        Args:
            stack: Current stack configuration
            incompatible_category: Category that has incompatibility
        
        Returns:
            List of suggested alternative providers
        """
        suggestions = []
        
        # If transformation is dbt and storage is NoSQL, suggest SQL databases
        if incompatible_category == "storage":
            if stack.get("transformation") == "dbt":
                suggestions = ["PostgreSQL", "Snowflake", "BigQuery", "Redshift"]
        
        # If storage is MongoDB and transformation wants SQL, suggest Spark
        elif incompatible_category == "transformation":
            if stack.get("storage") == "MongoDB":
                suggestions = ["Spark"]
        
        return suggestions
    
    @staticmethod
    def get_all_required_packages(stack: Dict[str, str]) -> List[str]:
        """
        Get all required packages for the entire stack.
        
        Args:
            stack: Technology stack configuration
        
        Returns:
            Consolidated list of required Python packages
        """
        all_packages = set()
        
        categories = list(stack.keys())
        providers = list(stack.values())
        
        # Check all pairs
        for i in range(len(categories)):
            for j in range(i + 1, len(categories)):
                cat1, prov1 = categories[i], providers[i]
                cat2, prov2 = categories[j], providers[j]
                
                if not prov1 or not prov2:
                    continue
                
                packages = ProviderCompatibility.get_required_packages(
                    cat1, prov1, cat2, prov2
                )
                all_packages.update(packages)
        
        return sorted(list(all_packages))
