"""
Additional storage providers: Snowflake and DuckDB
"""
import os
import yaml
from typing import Dict, Any, Optional
from core.interfaces import ComponentGenerator
from core.registry import ProviderRegistry
from core.manifest import ProjectContext


class SnowflakeGenerator(ComponentGenerator):
    """Generator for Snowflake data warehouse."""
    
    def __init__(self, env):
        super().__init__(env)
        self.context: Optional[ProjectContext] = None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """
        Generate Snowflake configuration files.
        
        Note: Snowflake is cloud-based, no Docker container needed.
        We generate connection configs and dbt profiles.
        """
        self.context = config.get("project_context")
        if not self.context:
            return
        
        # Generate secrets for Snowflake
        self.context.get_or_create_secret("snowflake_password")
        
        # Create snowflake config directory
        sf_dir = os.path.join(output_dir, "config", "snowflake")
        os.makedirs(sf_dir, exist_ok=True)
        
        try:
            # Render connection config template
            template = self.env.get_template("storage/snowflake_connection.yml.j2")
            content = template.render(
                account="YOUR_ACCOUNT",  # User needs to replace
                user="YOUR_USER",
                password=self.context.get_or_create_secret("snowflake_password"),
                warehouse="COMPUTE_WH",
                database="ANALYTICS",
                schema="PUBLIC"
            )
            
            config_path = os.path.join(sf_dir, "connection.yml")
            with open(config_path, 'w') as f:
                f.write(content)
                
        except Exception as e:
            print(f"Error generating Snowflake config: {e}")
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """
        Snowflake is cloud-based, no Docker service needed.
        """
        return {}
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """Returns environment variables for Snowflake connection."""
        if not self.context:
            return {}
        
        password = self.context.get_or_create_secret("snowflake_password")
        
        return {
            "SNOWFLAKE_ACCOUNT": "YOUR_ACCOUNT",
            "SNOWFLAKE_USER": "YOUR_USER",
            "SNOWFLAKE_PASSWORD": password,
            "SNOWFLAKE_WAREHOUSE": "COMPUTE_WH",
            "SNOWFLAKE_DATABASE": "ANALYTICS",
            "SNOWFLAKE_SCHEMA": "PUBLIC",
            "SNOWFLAKE_ROLE": "ACCOUNTADMIN"
        }
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        """No volumes needed for cloud-based Snowflake."""
        return {}


class DuckDBGenerator(ComponentGenerator):
    """Generator for DuckDB embedded database."""
    
    def __init__(self, env):
        super().__init__(env)
        self.context: Optional[ProjectContext] = None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """
        Generate DuckDB configuration.
        
        DuckDB is embedded, runs in-process with application.
        """
        self.context = config.get("project_context")
        if not self.context:
            return
        
        # Create duckdb directory
        db_dir = os.path.join(output_dir, "data", "duckdb")
        os.makedirs(db_dir, exist_ok=True)
        
        try:
            # Create a simple Python script for DuckDB initialization
            init_script = """
import duckdb

# Connect to DuckDB (creates file if doesn't exist)
conn = duckdb.connect('data/duckdb/analytics.db')

# Create example schema
conn.execute(\"\"\"
    CREATE SCHEMA IF NOT EXISTS staging;
    CREATE SCHEMA IF NOT EXISTS analytics;
\"\"\")

print("DuckDB initialized successfully!")
conn.close()
"""
            
            script_path = os.path.join(output_dir, "init_duckdb.py")
            with open(script_path, 'w') as f:
                f.write(init_script)
                
        except Exception as e:
            print(f"Error generating DuckDB setup: {e}")
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """
        DuckDB runs embedded, but we can provide a service for running queries.
        """
        return {
            "duckdb": {
                "image": "python:3.11-slim",
                "working_dir": "/app",
                "volumes": [
                    "./data/duckdb:/app/data/duckdb",
                    "./init_duckdb.py:/app/init_duckdb.py"
                ],
                "command": "tail -f /dev/null",  # Keep container running
                "environment": self.get_env_vars(context)
            }
        }
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """Returns environment variables for DuckDB."""
        return {
            "DUCKDB_DATABASE_PATH": "/app/data/duckdb/analytics.db",
            "DUCKDB_MEMORY_LIMIT": "4GB",
            "DUCKDB_THREADS": "4"
        }
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        """Volumes for DuckDB data persistence."""
        return {
            "duckdb_data": None
        }


# Register providers
ProviderRegistry.register("storage", "Snowflake", SnowflakeGenerator)
ProviderRegistry.register("storage", "DuckDB", DuckDBGenerator)
