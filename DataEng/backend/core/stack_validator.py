"""
Stack Validator for AntiGravity DataEng
Validates stack configurations for compatibility and provides suggestions.
"""

from typing import Dict, List, Tuple, Optional
from backend.core.compatibility_matrix import (
    COMPATIBILITY_MATRIX,
    is_compatible,
    get_compatible_providers,
    get_provider_info
)


class StackValidator:
    """Validates stack configurations for compatibility."""
    
    @staticmethod
    def validate_stack(stack: Dict[str, str]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a stack configuration for compatibility.
        
        Args:
            stack: Dictionary mapping category to provider (e.g., {"storage": "PostgreSQL"})
        
        Returns:
            Tuple of (is_valid, errors, warnings)
            - is_valid: True if stack is valid, False if there are blocking errors
            - errors: List of error messages (blocking issues)
            - warnings: List of warning messages (non-blocking concerns)
        """
        errors = []
        warnings = []
        
        # =====================================================================
        # REQUIRED COMPONENTS
        # =====================================================================
        
        if "storage" not in stack:
            errors.append("❌ Storage is required - it's the foundation of any data stack")
        
        # =====================================================================
        # PAIRWISE COMPATIBILITY CHECKS
        # =====================================================================
        
        categories = list(stack.keys())
        for i, cat1 in enumerate(categories):
            for cat2 in categories[i+1:]:
                prov1, prov2 = stack[cat1], stack[cat2]
                
                if not is_compatible(cat1, prov1, cat2, prov2):
                    errors.append(
                        f"❌ {prov1} ({cat1}) is incompatible with {prov2} ({cat2})"
                    )
        
        # =====================================================================
        # SPECIFIC INCOMPATIBILITY CHECKS
        # =====================================================================
        
        # Kafka + dbt incompatibility
        if stack.get("ingestion") == "Kafka" and stack.get("transformation") == "dbt":
            errors.append(
                "❌ Kafka (streaming) is incompatible with dbt (batch). "
                "Use Spark for streaming transformations."
            )
        
        # MongoDB + dbt incompatibility
        if stack.get("storage") == "MongoDB" and stack.get("transformation") == "dbt":
            errors.append(
                "❌ MongoDB (NoSQL) is incompatible with dbt (SQL-only). "
                "Consider using Spark for transformations or Soda for quality."
            )
        
        # MongoDB + Great Expectations incompatibility
        if stack.get("storage") == "MongoDB" and stack.get("quality") == "Great Expectations":
            errors.append(
                "❌ MongoDB is not fully supported by Great Expectations. "
                "Use Soda instead for NoSQL quality checks."
            )
        
        # =====================================================================
        # DEPENDENCY CHECKS
        # =====================================================================
        
        # Visualization requires storage
        if stack.get("visualization") and "storage" not in stack:
            errors.append(
                f"❌ {stack['visualization']} (visualization) requires a storage layer"
            )
        
        # Quality requires storage
        if stack.get("quality") and "storage" not in stack:
            errors.append(
                f"❌ {stack['quality']} (quality) requires a storage layer"
            )
        
        # =====================================================================
        # WARNINGS FOR SUB-OPTIMAL COMBINATIONS
        # =====================================================================
        
        # DuckDB + Enterprise BI warning
        if stack.get("storage") == "DuckDB" and stack.get("visualization") in ["Superset", "Metabase"]:
            warnings.append(
                "⚠️  DuckDB is embedded/local. May not scale for production BI. "
                "Consider PostgreSQL, Snowflake, or BigQuery for production."
            )
        
        # Cloud storage without Terraform
        cloud_storages = ["Snowflake", "BigQuery", "Redshift"]
        if stack.get("storage") in cloud_storages and "infrastructure" not in stack:
            warnings.append(
                f"⚠️  {stack['storage']} is cloud-based. "
                "Consider adding Terraform to provision infrastructure automatically."
            )
        
        # Kafka without Spark
        if stack.get("ingestion") == "Kafka" and stack.get("transformation") != "Spark":
            warnings.append(
                "⚠️  Kafka is streaming-focused. "
                "Consider adding Spark for real-time transformations."
            )
        
        # BigQuery requires service account
        if stack.get("storage") == "BigQuery":
            warnings.append(
                "⚠️  BigQuery requires a service account JSON key. "
                "You'll need to provide this manually."
            )
        
        # Multiple orchestrators
        orchestrators = ["Airflow", "Prefect", "Dagster", "Mage"]
        selected_orchestrators = [o for o in orchestrators if stack.get("orchestration") == o]
        if len(selected_orchestrators) > 1:
            warnings.append(
                "⚠️  Multiple orchestrators selected. "
                "Typically you only need one orchestration tool."
            )
        
        # =====================================================================
        # RETURN VALIDATION RESULT
        # =====================================================================
        
        is_valid = len(errors) == 0
        return (is_valid, errors, warnings)
    
    @staticmethod
    def suggest_compatible_options(stack: Dict[str, str], category: str) -> List[str]:
        """
        Suggest compatible providers for a category based on current stack.
        
        Args:
            stack: Current stack configuration
            category: Category to get suggestions for
        
        Returns:
            List of compatible provider names
        """
        return get_compatible_providers(category, stack)
    
    @staticmethod
    def get_recommendation(stack: Dict[str, str], category: str) -> Optional[str]:
        """
        Get a recommended provider for a category based on current stack.
        
        Args:
            stack: Current stack configuration
            category: Category to get recommendation for
        
        Returns:
            Recommended provider name, or None
        """
        compatible = StackValidator.suggest_compatible_options(stack, category)
        
        if not compatible:
            return None
        
        # Recommendation logic based on stack
        storage = stack.get("storage")
        
        if category == "transformation":
            # If SQL storage, recommend dbt
            if storage in ["PostgreSQL", "Snowflake", "BigQuery", "Redshift", "DuckDB"]:
                return "dbt" if "dbt" in compatible else compatible[0]
            # If MongoDB, recommend Spark
            elif storage == "MongoDB":
                return "Spark" if "Spark" in compatible else compatible[0]
            # If Kafka ingestion, recommend Spark
            elif stack.get("ingestion") == "Kafka":
                return "Spark" if "Spark" in compatible else compatible[0]
        
        elif category == "visualization":
            # For enterprise, recommend Superset
            if storage in ["Snowflake", "BigQuery"]:
                return "Superset" if "Superset" in compatible else compatible[0]
            # For simple, recommend Metabase
            else:
                return "Metabase" if "Metabase" in compatible else compatible[0]
        
        elif category == "quality":
            # SQL -> Great Expectations
            if storage in ["PostgreSQL", "Snowflake", "BigQuery", "Redshift"]:
                return "Great Expectations" if "Great Expectations" in compatible else compatible[0]
            # NoSQL -> Soda
            elif storage == "MongoDB":
                return "Soda" if "Soda" in compatible else compatible[0]
        
        elif category == "orchestration":
            # Default to Airflow (most popular)
            return "Airflow" if "Airflow" in compatible else compatible[0]
        
        # Default: return first compatible option
        return compatible[0] if compatible else None
    
    @staticmethod
    def explain_incompatibility(provider1_cat: str, provider1: str, 
                                provider2_cat: str, provider2: str) -> str:
        """
        Get explanation for why two providers are incompatible.
        
        Returns:
            Human-readable explanation
        """
        info1 = get_provider_info(provider1_cat, provider1)
        info2 = get_provider_info(provider2_cat, provider2)
        
        if not info1 or not info2:
            return "One of the providers is not recognized."
        
        # Check explicit incompatibility
        if provider2 in info1.get("incompatible_with", []):
            warning = info1.get("warning", "")
            return f"{provider1} is incompatible with {provider2}. {warning}"
        
        if provider1 in info2.get("incompatible_with", []):
            warning = info2.get("warning", "")
            return f"{provider2} is incompatible with {provider1}. {warning}"
        
        # Check specific cases
        if provider1 == "Kafka" and provider2 == "dbt":
            return "Kafka is streaming-focused while dbt is batch-oriented. Use Spark for streaming transformations."
        
        if provider1 == "MongoDB" and provider2 == "dbt":
            return "MongoDB is NoSQL while dbt only works with SQL databases."
        
        return "These providers are not compatible based on their technical characteristics."
