import os
from typing import Dict, Any, List, Optional
from core.interfaces import ComponentGenerator
from core.registry import ProviderRegistry
from core.manifest import ProjectContext, ServiceConnection
from core.config_resolver import ConfigurationMapper

class DbtGenerator(ComponentGenerator):
    def register_services(self, context: ProjectContext) -> None:
        """
        Register dbt as a transformation service.
        """
        connection = ServiceConnection(
            name="dbt_transformation",
            type="dbt",
            host="localhost",
            port=0,
            env_prefix="DBT_",
            capabilities=["transformation"],
            extra={}
        )
        context.register_connection(connection)
    
    def get_dependencies(self) -> List[str]:
        """
        dbt needs a SQL database to run transformations.
        """
        return ["sql_database", "warehouse"]
    
    def validate_configuration(self, context: ProjectContext) -> tuple[bool, Optional[str]]:
        """
        Validate that dbt has a compatible database.
        """
        db_service = context.get_service_by_capability("sql_database")
        if not db_service:
            db_service = context.get_service_by_capability("warehouse")
        
        if not db_service:
            return (False, "dbt requires a SQL database or warehouse")
        
        # Check if the database type is supported by dbt
        supported_types = ["postgres", "postgresql", "snowflake", "bigquery", "redshift", "duckdb"]
        if db_service.type.lower() not in supported_types:
            return (False, f"dbt does not support {db_service.type}. Supported: {', '.join(supported_types)}")
        
        return (True, None)
    
    def get_connection_string(self, context: ProjectContext, target_service: Optional[str] = None) -> Optional[str]:
        """
        Get connection string to the target database.
        """
        db_service = context.get_service_by_capability("warehouse")
        if not db_service:
            db_service = context.get_service_by_capability("sql_database")
        
        if db_service:
            return db_service.get_connection_string(context)
        return None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        try:
            # Create dbt project structure
            dbt_dir = os.path.join(output_dir, "dbt_project")
            os.makedirs(dbt_dir, exist_ok=True)
            
            # Render dbt_project.yml
            template = self.env.get_template("transformation/dbt_project.yml.j2")
            content = template.render(project_name=config.get("project_name", "my_project"))
            with open(os.path.join(dbt_dir, "dbt_project.yml"), "w") as f:
                f.write(content)
                
            # Create standard dbt folders
            for folder in ["models", "seeds", "tests", "analyses", "macros", "snapshots"]:
                os.makedirs(os.path.join(dbt_dir, folder), exist_ok=True)
        except Exception as e:
            print(f"Error rendering transformation (dbt): {e}")
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """
        Returns Docker service definition for dbt.
        
        Note: dbt typically runs as part of orchestration (e.g., in Airflow),
        not as a standalone service. Return empty dict.
        
        Args:
            context (ProjectContext): The global project context.
        """
        return {}
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """
        Returns environment variables needed for dbt.
        
        Args:
            context (ProjectContext): The global project context.
        """
        # dbt needs database connection info, which it gets from profiles.yml
        # But we can provide some generic env vars
        env_vars = {}
        
        # If PostgreSQL is in the stack, provide connection details
        if context and context.stack.get("storage") == "PostgreSQL":
            password = context.get_or_create_secret("postgres_password")
            port = context.get_service_port("postgres", 5432)
            
            env_vars.update({
                "DBT_PROFILES_DIR": "/dbt_project",
                "DBT_TARGET": "dev",
                "DBT_DB_HOST": "postgres",
                "DBT_DB_PORT": str(port),
                "DBT_DB_USER": "postgres",
                "DBT_DB_PASSWORD": password,
                "DBT_DB_NAME": "warehouse"
            })
        
        return env_vars

ProviderRegistry.register("transformation", "dbt", DbtGenerator)
