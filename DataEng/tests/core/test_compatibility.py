"""
Tests for Compatibility Matrix and Stack Validator
"""
import pytest
from backend.core.compatibility_matrix import (
    COMPATIBILITY_MATRIX,
    is_compatible,
    get_compatible_providers,
    get_provider_info
)
from backend.core.stack_validator import StackValidator


class TestCompatibilityMatrix:
    """Tests for the compatibility matrix."""
    
    def test_matrix_structure(self):
        """Test that compatibility matrix has expected structure."""
        assert "ingestion" in COMPATIBILITY_MATRIX
        assert "storage" in COMPATIBILITY_MATRIX
        assert "transformation" in COMPATIBILITY_MATRIX
        assert "visualization" in COMPATIBILITY_MATRIX
        assert "quality" in COMPATIBILITY_MATRIX
        assert "monitoring" in COMPATIBILITY_MATRIX
    
    def test_all_providers_defined(self):
        """Test that all known providers are in the matrix."""
        # Ingestion
        assert "DLT" in COMPATIBILITY_MATRIX["ingestion"]
        assert "Airbyte" in COMPATIBILITY_MATRIX["ingestion"]
        assert "Kafka" in COMPATIBILITY_MATRIX["ingestion"]
        
        # Storage
        assert "PostgreSQL" in COMPATIBILITY_MATRIX["storage"]
        assert "Snowflake" in COMPATIBILITY_MATRIX["storage"]
        assert "BigQuery" in COMPATIBILITY_MATRIX["storage"]
        assert "MongoDB" in COMPATIBILITY_MATRIX["storage"]
        
        # Transformation
        assert "dbt" in COMPATIBILITY_MATRIX["transformation"]
        assert "Spark" in COMPATIBILITY_MATRIX["transformation"]
    
    def test_get_provider_info(self):
        """Test getting provider information."""
        postgres_info = get_provider_info("storage", "PostgreSQL")
        assert postgres_info is not None
        assert postgres_info["works_with_all"] is True
        assert "Metabase" in postgres_info["compatible_visualization"]
    
    def test_compatible_pairs(self):
        """Test compatible provider pairs."""
        # PostgreSQL + dbt should be compatible
        assert is_compatible("storage", "PostgreSQL", "transformation", "dbt") is True
        
        # PostgreSQL + Metabase should be compatible
        assert is_compatible("storage", "PostgreSQL", "visualization", "Metabase") is True
        
        # DLT + PostgreSQL should be compatible
        assert is_compatible("ingestion", "DLT", "storage", "PostgreSQL") is True
    
    def test_incompatible_pairs(self):
        """Test incompatible provider pairs."""
        # Kafka + dbt should be incompatible
        assert is_compatible("ingestion", "Kafka", "transformation", "dbt") is False
        
        # MongoDB + dbt should be incompatible
        assert is_compatible("storage", "MongoDB", "transformation", "dbt") is False
        
        # MongoDB + Great Expectations should be incompatible
        assert is_compatible("storage", "MongoDB", "quality", "Great Expectations") is False


class TestStackValidator:
    """Tests for the StackValidator."""
    
    def test_valid_stack_postgres_dbt_metabase(self):
        """Test validation of a valid stack."""
        stack = {
            "ingestion": "DLT",
            "storage": "PostgreSQL",
            "transformation": "dbt",
            "orchestration": "Airflow",
            "visualization": "Metabase",
            "quality": "Great Expectations",
            "monitoring": "Prometheus"
        }
        
        is_valid, errors, warnings = StackValidator.validate_stack(stack)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_invalid_stack_kafka_dbt(self):
        """Test validation catches Kafka + dbt incompatibility."""
        stack = {
            "ingestion": "Kafka",
            "storage": "PostgreSQL",
            "transformation": "dbt"
        }
        
        is_valid, errors, warnings = StackValidator.validate_stack(stack)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Kafka" in err and "dbt" in err for err in errors)
    
    def test_invalid_stack_mongodb_dbt(self):
        """Test validation catches MongoDB + dbt incompatibility."""
        stack = {
            "storage": "MongoDB",
            "transformation": "dbt"
        }
        
        is_valid, errors, warnings = StackValidator.validate_stack(stack)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("MongoDB" in err and "dbt" in err for err in errors)
    
    def test_missing_storage(self):
        """Test validation requires storage."""
        stack = {
            "ingestion": "DLT",
            "transformation": "dbt"
        }
        
        is_valid, errors, warnings = StackValidator.validate_stack(stack)
        
        assert is_valid is False
        assert any("Storage" in err or "storage" in err for err in errors)
    
    def test_visualization_requires_storage(self):
        """Test that visualization requires storage."""
        stack = {
            "visualization": "Metabase"
        }
        
        is_valid, errors, warnings = StackValidator.validate_stack(stack)
        
        assert is_valid is False
        assert any("storage" in err.lower() for err in errors)
    
    def test_cloud_storage_warning(self):
        """Test warning for cloud storage without Terraform."""
        stack = {
            "storage": "Snowflake",
            "transformation": "dbt"
        }
        
        is_valid, errors, warnings = StackValidator.validate_stack(stack)
        
        assert is_valid is True  # Valid but has warning
        assert len(warnings) > 0
        assert any("Terraform" in warn or "cloud" in warn.lower() for warn in warnings)
    
    def test_suggest_compatible_options(self):
        """Test suggesting compatible providers."""
        stack = {
            "storage": "PostgreSQL"
        }
        
        # Should suggest dbt and Spark for transformation
        compatible = StackValidator.suggest_compatible_options(stack, "transformation")
        assert "dbt" in compatible
        assert "Spark" in compatible
    
    def test_suggest_with_mongodb(self):
        """Test suggestions exclude incompatible providers."""
        stack = {
            "storage": "MongoDB"
        }
        
        # Should NOT suggest dbt (incompatible)
        compatible = StackValidator.suggest_compatible_options(stack, "transformation")
        assert "dbt" not in compatible
        assert "Spark" in compatible  # Spark works with MongoDB
    
    def test_get_recommendation(self):
        """Test getting recommendation for a category."""
        stack = {
            "storage": "PostgreSQL"
        }
        
        # Should recommend dbt for SQL storage
        recommendation = StackValidator.get_recommendation(stack, "transformation")
        assert recommendation == "dbt"
        
        # Should recommend Metabase for visualization
        recommendation = StackValidator.get_recommendation(stack, "visualization")
        assert recommendation in ["Metabase", "Superset"]
    
    def test_explain_incompatibility(self):
        """Test explaining why providers are incompatible."""
        explanation = StackValidator.explain_incompatibility(
            "ingestion", "Kafka",
            "transformation", "dbt"
        )
        
        assert "streaming" in explanation.lower() or "batch" in explanation.lower()


class TestIntegration:
    """Integration tests combining validator with matrix."""
    
    def test_complete_data_stack(self):
        """Test a complete, production-ready stack."""
        stack = {
            "ingestion": "DLT",
            "storage": "Snowflake",
            "transformation": "dbt",
            "orchestration": "Airflow",
            "infrastructure": "Terraform",
            "visualization": "Superset",
            "quality": "Great Expectations",
            "monitoring": "Prometheus"
        }
        
        is_valid, errors, warnings = StackValidator.validate_stack(stack)
        
        assert is_valid is True
        assert len(errors) == 0
        # May have warnings about cloud/credentials
    
    def test_streaming_stack(self):
        """Test a streaming-focused stack."""
        stack = {
            "ingestion": "Kafka",
            "storage": "PostgreSQL",
            "transformation": "Spark",  # Correct for streaming
            "orchestration": "Airflow"
        }
        
        is_valid, errors, warnings = StackValidator.validate_stack(stack)
        
        assert is_valid is True
    
    def test_nosql_stack(self):
        """Test a NoSQL-focused stack."""
        stack = {
            "storage": "MongoDB",
            "transformation": "Spark",  # Not dbt
            "visualization": "Superset",
            "quality": "Soda"  # Not Great Expectations
        }
        
        is_valid, errors, warnings = StackValidator.validate_stack(stack)
        
        assert is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
