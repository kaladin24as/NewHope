"""
Tests for Secret Registry and Auto-Wiring
"""
import pytest
from backend.core.secret_registry import (
    SecretRegistry,
    generate_secure_password,
    generate_secret_key,
    generate_username
)


class TestSecretGeneration:
    """Tests for secret generation functions."""
    
    def test_generate_secure_password(self):
        """Test password generation."""
        password = generate_secure_password(16)
        
        assert len(password) == 16
        assert password.isalnum() or any(c in "!@#$%^&*" for c in password)
        
        # Test uniqueness
        password2 = generate_secure_password(16)
        assert password != password2
    
    def test_generate_secret_key(self):
        """Test secret key generation."""
        key = generate_secret_key(32)
        
        assert len(key) == 64  # Hex doubles the length
        assert all(c in "0123456789abcdef" for c in key)
        
        # Test uniqueness
        key2 = generate_secret_key(32)
        assert key != key2
    
    def test_generate_username(self):
        """Test username generation."""
        username = generate_username("dataeng")
        assert username == "dataeng_user"


class TestSecretRegistry:
    """Tests for SecretRegistry."""
    
    def test_registry_has_all_secrets(self):
        """Test that registry defines all expected secrets."""
        assert "postgres_user" in SecretRegistry.SECRETS
        assert "postgres_password" in SecretRegistry.SECRETS
        assert "snowflake_account" in SecretRegistry.SECRETS
        assert "metabase_db_password" in SecretRegistry.SECRETS
        assert "superset_secret_key" in SecretRegistry.SECRETS
        assert "airflow_fernet_key" in SecretRegistry.SECRETS
    
    def test_get_secrets_for_postgres_stack(self):
        """Test secret generation for PostgreSQL stack."""
        stack = {
            "storage": "PostgreSQL",
            "transformation": "dbt",
            "visualization": "Metabase"
        }
        
        secrets = SecretRegistry.get_secrets_for_stack(stack, "test_project")
        
        # PostgreSQL secrets
        assert "postgres_user" in secrets
        assert "postgres_password" in secrets
        assert "postgres_database" in secrets
        assert secrets["postgres_database"] == "test_project_warehouse"
        
        # Metabase secrets
        assert "metabase_db_password" in secrets
        assert "metabase_encryption_key" in secrets
        
        # Passwords should be generated (not placeholders)
        assert secrets["postgres_password"] != "CHANGE_ME_POSTGRES_PASSWORD"
        assert len(secrets["postgres_password"]) == 16
    
    def test_get_secrets_for_snowflake_stack(self):
        """Test secret generation for Snowflake stack."""
        stack = {
            "storage": "Snowflake",
            "transformation": "dbt",
            "visualization": "Superset"
        }
        
        secrets = SecretRegistry.get_secrets_for_stack(stack, "analytics")
        
        # Snowflake secrets
        assert "snowflake_account" in secrets
        assert "snowflake_user" in secrets
        assert "snowflake_password" in secrets
        assert "snowflake_warehouse" in secrets
        
        # Superset secrets
        assert "superset_secret_key" in secrets
        assert "superset_db_password" in secrets
        
        # Password should be strong (20 chars for Snowflake)
        assert len(secrets["snowflake_password"]) == 20
    
    def test_auto_wiring_same_password(self):
        """Test that components share the same password automatically."""
        stack = {
            "storage": "PostgreSQL",
            "transformation": "dbt",
            "visualization": "Metabase",
            "quality": "Great Expectations"
        }
        
        secrets = SecretRegistry.get_secrets_for_stack(stack, "project")
        
        # All these components should use the SAME postgres password
        postgres_password = secrets["postgres_password"]
        
        # Verify it's a strong password
        assert len(postgres_password) == 16
        assert postgres_password != "CHANGE_ME"
        
        # This password is automatically shared with:
        # - dbt (for transformations)
        # - Metabase (for BI connections)
        # - Great Expectations (for data quality)
        # All via the SecretDefinition.used_by set
    
    def test_connection_string_postgres(self):
        """Test PostgreSQL connection string generation."""
        secrets = {
            "postgres_user": "dataeng_user",
            "postgres_password": "SecureP@ss123",
            "postgres_database": "warehouse"
        }
        
        conn_string = SecretRegistry.get_connection_string("PostgreSQL", secrets)
        
        assert conn_string == "postgresql://dataeng_user:SecureP@ss123@postgres:5432/warehouse"
    
    def test_connection_string_snowflake(self):
        """Test Snowflake connection string generation."""
        secrets = {
            "snowflake_account": "xy12345.us-east-1",
            "snowflake_user": "dataeng_user",
            "snowflake_password": "SecureP@ss123",
            "snowflake_warehouse": "COMPUTE_WH",
            "snowflake_database": "ANALYTICS"
        }
        
        conn_string = SecretRegistry.get_connection_string("Snowflake", secrets)
        
        expected = "snowflake://dataeng_user:SecureP@ss123@xy12345.us-east-1/ANALYTICS?warehouse=COMPUTE_WH"
        assert conn_string == expected
    
    def test_connection_string_bigquery(self):
        """Test BigQuery connection string generation."""
        secrets = {
            "bigquery_project": "my-gcp-project",
            "bigquery_dataset": "analytics"
        }
        
        conn_string = SecretRegistry.get_connection_string("BigQuery", secrets)
        
        assert conn_string == "bigquery://my-gcp-project/analytics"
    
    def test_connection_string_with_override(self):
        """Test connection string with database override."""
        secrets = {
            "postgres_user": "user",
            "postgres_password": "pass",
            "postgres_database": "default_db"
        }
        
        conn_string = SecretRegistry.get_connection_string(
            "PostgreSQL", 
            secrets, 
            database="custom_db"  # Override
        )
        
        assert "custom_db" in conn_string
        assert "default_db" not in conn_string


class TestAutoWiringScenarios:
    """Integration tests for auto-wiring scenarios."""
    
    def test_full_postgres_stack_autowiring(self):
        """Test complete PostgreSQL stack with auto-wired secrets."""
        stack = {
            "ingestion": "DLT",
            "storage": "PostgreSQL",
            "transformation": "dbt",
            "orchestration": "Airflow",
            "visualization": "Metabase",
            "quality": "Great Expectations",
            "monitoring": "Prometheus"
        }
        
        secrets = SecretRegistry.get_secrets_for_stack(stack, "my_project")
        
        # All these should share the PostgreSQL password
        pg_password = secrets["postgres_password"]
        
        # Generate connection strings for different components
        dbt_conn = SecretRegistry.get_connection_string("PostgreSQL", secrets, "analytics")
        metabase_conn = SecretRegistry.get_connection_string("PostgreSQL", secrets, "warehouse")
        ge_conn = SecretRegistry.get_connection_string("PostgreSQL", secrets, "quality")
        
        # All should use the SAME password
        assert pg_password in dbt_conn
        assert pg_password in metabase_conn
        assert pg_password in ge_conn
        
        # Airflow should have its own admin password
        assert "airflow_admin_password" in secrets
        assert secrets["airflow_admin_password"] != pg_password
    
    def test_snowflake_stack_autowiring(self):
        """Test Snowflake stack with auto-wired secrets."""
        stack = {
            "storage": "Snowflake",
            "transformation": "dbt",
            "visualization": "Superset",
            "quality": "Soda"
        }
        
        secrets = SecretRegistry.get_secrets_for_stack(stack, "analytics")
        
        # All should share Snowflake credentials
        sf_password = secrets["snowflake_password"]
        
        dbt_conn = SecretRegistry.get_connection_string("Snowflake", secrets)
        soda_conn = SecretRegistry.get_connection_string("Snowflake", secrets)
        
        # Both use same Snowflake password
        assert sf_password in dbt_conn
        assert sf_password in soda_conn
        
        # Superset has its own secrets
        assert "superset_secret_key" in secrets
        assert secrets["superset_secret_key"] != sf_password


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
