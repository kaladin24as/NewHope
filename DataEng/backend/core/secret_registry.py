"""
Secret Registry for AntiGravity DataEng
Centralized management of secrets with automatic interconnection between components.
"""

import secrets
import string
from typing import Dict, Set, Optional, Callable, List
from dataclasses import dataclass, field


# =============================================================================
# SECRET GENERATION UTILITIES
# =============================================================================

def generate_secure_password(length: int = 16) -> str:
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_secret_key(length: int = 32) -> str:
    """Generate a secret key (hex format)."""
    return secrets.token_hex(length)


def generate_username(base: str = "dataeng") -> str:
    """Generate a username."""
    return f"{base}_user"


# =============================================================================
# SECRET DEFINITION
# =============================================================================

@dataclass
class SecretDefinition:
    """Definition of a secret with its usages and generation function."""
    name: str
    description: str
    generated_by: str  # Which provider generates it
    used_by: Set[str] = field(default_factory=set)  # Which providers use it
    generation_function: Optional[Callable[[], str]] = None
    default_value: Optional[str] = None


# =============================================================================
# SECRET REGISTRY
# =============================================================================

class SecretRegistry:
    """Central registry for all secrets and their interconnections."""
    
    # All secrets defined across all providers
    SECRETS = {
        # =====================================================================
        # POSTGRESQL SECRETS
        # =====================================================================
        "postgres_user": SecretDefinition(
            name="postgres_user",
            description="PostgreSQL username",
            generated_by="PostgreSQL",
            used_by={"dbt", "Metabase", "Superset", "Grafana", "Great Expectations", "Soda", "Airflow", "DLT"},
            generation_function=lambda: generate_username("dataeng")
        ),
        "postgres_password": SecretDefinition(
            name="postgres_password",
            description="PostgreSQL password",
            generated_by="PostgreSQL",
            used_by={"dbt", "Metabase", "Superset", "Grafana", "Great Expectations", "Soda", "Airflow", "DLT"},
            generation_function=lambda: generate_secure_password(16)
        ),
        "postgres_database": SecretDefinition(
            name="postgres_database",
            description="PostgreSQL database name",
            generated_by="PostgreSQL",
            used_by={"dbt", "Metabase", "Superset", "Great Expectations", "Soda", "Airflow"},
            default_value="warehouse"
        ),
        
        # =====================================================================
        # SNOWFLAKE SECRETS
        # =====================================================================
        "snowflake_account": SecretDefinition(
            name="snowflake_account",
            description="Snowflake account identifier",
            generated_by="Snowflake",
            used_by={"dbt", "Metabase", "Superset", "Great Expectations", "Soda"},
            default_value="CHANGE_ME_ACCOUNT"
        ),
        "snowflake_user": SecretDefinition(
            name="snowflake_user",
            description="Snowflake username",
            generated_by="Snowflake",
            used_by={"dbt", "Metabase", "Superset", "Great Expectations", "Soda"},
            generation_function=lambda: generate_username("dataeng")
        ),
        "snowflake_password": SecretDefinition(
            name="snowflake_password",
            description="Snowflake password",
            generated_by="Snowflake",
            used_by={"dbt", "Metabase", "Superset", "Great Expectations", "Soda"},
            generation_function=lambda: generate_secure_password(20)
        ),
        "snowflake_warehouse": SecretDefinition(
            name="snowflake_warehouse",
            description="Snowflake warehouse",
            generated_by="Snowflake",
            used_by={"dbt", "Metabase", "Superset", "Great Expectations", "Soda"},
            default_value="COMPUTE_WH"
        ),
        "snowflake_database": SecretDefinition(
            name="snowflake_database",
            description="Snowflake database",
            generated_by="Snowflake",
            used_by={"dbt", "Metabase", "Superset", "Great Expectations", "Soda"},
            default_value="ANALYTICS"
        ),
        "snowflake_role": SecretDefinition(
            name="snowflake_role",
            description="Snowflake role",
            generated_by="Snowflake",
            used_by={"dbt", "Soda"},
            default_value="SYSADMIN"
        ),
        
        # =====================================================================
        # BIGQUERY SECRETS
        # =====================================================================
        "bigquery_project": SecretDefinition(
            name="bigquery_project",
            description="GCP project ID",
            generated_by="BigQuery",
            used_by={"dbt", "Metabase", "Superset", "Great Expectations", "Soda"},
            default_value="CHANGE_ME_PROJECT_ID"
        ),
        "bigquery_dataset": SecretDefinition(
            name="bigquery_dataset",
            description="BigQuery dataset",
            generated_by="BigQuery",
            used_by={"dbt", "Metabase", "Superset", "Great Expectations", "Soda"},
            default_value="analytics"
        ),
        
        # =====================================================================
        # REDSHIFT SECRETS
        # =====================================================================
        "redshift_host": SecretDefinition(
            name="redshift_host",
            description="Redshift cluster endpoint",
            generated_by="Redshift",
            used_by={"dbt", "Metabase", "Superset", "Great Expectations", "Soda"},
            default_value="CHANGE_ME_REDSHIFT_HOST"
        ),
        "redshift_user": SecretDefinition(
            name="redshift_user",
            description="Redshift username",
            generated_by="Redshift",
            used_by={"dbt", "Metabase", "Superset", "Great Expectations", "Soda"},
            generation_function=lambda: generate_username("dataeng")
        ),
        "redshift_password": SecretDefinition(
            name="redshift_password",
            description="Redshift password",
            generated_by="Redshift",
            used_by={"dbt", "Metabase", "Superset", "Great Expectations", "Soda"},
            generation_function=lambda: generate_secure_password(16)
        ),
        "redshift_database": SecretDefinition(
            name="redshift_database",
            description="Redshift database",
            generated_by="Redshift",
            used_by={"dbt", "Metabase", "Superset", "Great Expectations", "Soda"},
            default_value="analytics"
        ),
        
        # =====================================================================
        # MONGODB SECRETS
        # =====================================================================
        "mongodb_user": SecretDefinition(
            name="mongodb_user",
            description="MongoDB username",
            generated_by="MongoDB",
            used_by={"Soda", "Superset", "Prometheus"},
            generation_function=lambda: generate_username("dataeng")
        ),
        "mongodb_password": SecretDefinition(
            name="mongodb_password",
            description="MongoDB password",
            generated_by="MongoDB",
            used_by={"Soda", "Superset", "Prometheus"},
            generation_function=lambda: generate_secure_password(16)
        ),
        
        # =====================================================================
        # AIRFLOW SECRETS
        # =====================================================================
        "airflow_admin_password": SecretDefinition(
            name="airflow_admin_password",
            description="Airflow admin password",
            generated_by="Airflow",
            used_by={"Prometheus"},  # For metrics scraping
            generation_function=lambda: generate_secure_password(16)
        ),
        "airflow_fernet_key": SecretDefinition(
            name="airflow_fernet_key",
            description="Airflow Fernet encryption key",
            generated_by="Airflow",
            used_by=set(),
            generation_function=lambda: generate_secret_key(32)
        ),
        
        # =====================================================================
        # METABASE SECRETS
        # =====================================================================
        "metabase_db_password": SecretDefinition(
            name="metabase_db_password",
            description="Metabase metadata DB password",
            generated_by="Metabase",
            used_by=set(),
            generation_function=lambda: generate_secure_password(16)
        ),
        "metabase_encryption_key": SecretDefinition(
            name="metabase_encryption_key",
            description="Metabase encryption secret",
            generated_by="Metabase",
            used_by=set(),
            generation_function=lambda: generate_secret_key(32)
        ),
        
        # =====================================================================
        # SUPERSET SECRETS
        # =====================================================================
        "superset_secret_key": SecretDefinition(
            name="superset_secret_key",
            description="Superset Flask secret key",
            generated_by="Superset",
            used_by=set(),
            generation_function=lambda: generate_secret_key(32)
        ),
        "superset_db_password": SecretDefinition(
            name="superset_db_password",
            description="Superset metadata DB password",
            generated_by="Superset",
            used_by=set(),
            generation_function=lambda: generate_secure_password(16)
        ),
        "superset_admin_password": SecretDefinition(
            name="superset_admin_password",
            description="Superset admin user password",
            generated_by="Superset",
            used_by=set(),
            generation_function=lambda: generate_secure_password(12)
        ),
        
        # =====================================================================
        # GRAFANA SECRETS
        # =====================================================================
        "grafana_admin_password": SecretDefinition(
            name="grafana_admin_password",
            description="Grafana admin password",
            generated_by="Grafana",
            used_by=set(),
            generation_function=lambda: generate_secure_password(12)
        ),
    }
    
    @classmethod
    def get_secrets_for_stack(cls, stack: Dict[str, str], project_name: str) -> Dict[str, str]:
        """
        Generate all required secrets for a given stack configuration.
        Auto-wires secrets between components based on the registry.
        
        Args:
            stack: Stack configuration (e.g., {"storage": "PostgreSQL", ...})
            project_name: Project name for customization
        
        Returns:
            Dictionary of all required secrets
        """
        secrets_dict = {}
        
        # Identify which providers are active
        active_providers = set(stack.values())
        
        # Generate secrets for each active provider
        for secret_name, secret_def in cls.SECRETS.items():
            # Check if this secret is needed
            if secret_def.generated_by in active_providers or \
               any(user in active_providers for user in secret_def.used_by):
                
                # Generate the secret
                if secret_def.generation_function:
                    secrets_dict[secret_name] = secret_def.generation_function()
                elif secret_def.default_value:
                    secrets_dict[secret_name] = secret_def.default_value
                else:
                    # Fallback
                    secrets_dict[secret_name] = f"CHANGE_ME_{secret_name.upper()}"
        
        # Add project-specific customizations
        if "postgres_database" in secrets_dict:
            secrets_dict["postgres_database"] = f"{project_name}_warehouse"
        
        return secrets_dict
    
    @classmethod
    def get_connection_string(cls, storage_type: str, secrets: Dict[str, str], 
                             database: Optional[str] = None) -> str:
        """
        Generate connection string based on storage type.
        Used by visualization, quality, and transformation tools.
        
        Args:
            storage_type: Type of storage (PostgreSQL, Snowflake, etc.)
            secrets: Dictionary of secrets
            database: Optional database name override
        
        Returns:
            Connection string for the storage
        """
        if storage_type == "PostgreSQL":
            user = secrets.get("postgres_user", "postgres")
            password = secrets.get("postgres_password", "password")
            db = database or secrets.get("postgres_database", "warehouse")
            return f"postgresql://{user}:{password}@postgres:5432/{db}"
        
        elif storage_type == "Snowflake":
            account = secrets.get("snowflake_account", "ACCOUNT")
            user = secrets.get("snowflake_user", "user")
            password = secrets.get("snowflake_password", "password")
            warehouse = secrets.get("snowflake_warehouse", "COMPUTE_WH")
            db = database or secrets.get("snowflake_database", "ANALYTICS")
            return f"snowflake://{user}:{password}@{account}/{db}?warehouse={warehouse}"
        
        elif storage_type == "BigQuery":
            project = secrets.get("bigquery_project", "project")
            dataset = database or secrets.get("bigquery_dataset", "analytics")
            return f"bigquery://{project}/{dataset}"
        
        elif storage_type == "Redshift":
            host = secrets.get("redshift_host", "redshift-cluster.region.redshift.amazonaws.com")
            user = secrets.get("redshift_user", "user")
            password = secrets.get("redshift_password", "password")
            db = database or secrets.get("redshift_database", "analytics")
            return f"redshift+psycopg2://{user}:{password}@{host}:5439/{db}"
        
        elif storage_type == "DuckDB":
            db = database or "analytics"
            return f"duckdb:////data/{db}.duckdb"
        
        elif storage_type == "MongoDB":
            user = secrets.get("mongodb_user", "user")
            password = secrets.get("mongodb_password", "password")
            db = database or "analytics"
            return f"mongodb://{user}:{password}@mongodb:27017/{db}"
        
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
    
    @classmethod
    def get_required_secrets(cls, provider: str) -> List[str]:
        """
        Get list of secrets required by a specific provider.
        
        Args:
            provider: Provider name
        
        Returns:
            List of secret names
        """
        required = []
        for secret_name, secret_def in cls.SECRETS.items():
            if secret_def.generated_by == provider or provider in secret_def.used_by:
                required.append(secret_name)
        return required
