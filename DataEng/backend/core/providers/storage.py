import os
import yaml
from typing import Dict, Any, Optional, List
from core.interfaces import ComponentGenerator
from core.registry import ProviderRegistry
from core.manifest import ProjectContext, ServiceConnection, ConnectionBuilder

class PostgresGenerator(ComponentGenerator):
    def __init__(self, env):
        super().__init__(env)
        self.context: Optional[ProjectContext] = None

    def register_services(self, context: ProjectContext) -> None:
        """
        Register PostgreSQL service with capabilities.
        """
        self.context = context
        
        # Generate secret and port
        password = context.get_or_create_secret("postgres_password")
        port = context.get_service_port("postgres", 5432)
        
        # Register the PostgreSQL service
        connection = ServiceConnection(
            name="postgres",
            type="postgres",
            host="postgres",
            port=port,
            env_prefix="POSTGRES_",
            capabilities=["database", "sql_database", "warehouse"],
            credentials={
                "username": "postgres",
                "password": password
            },
            extra={
                "db_name": "warehouse"
            }
        )
        
        context.register_connection(connection)
    
    def get_dependencies(self) -> List[str]:
        """
        PostgreSQL has no dependencies - it's typically the foundation.
        """
        return []
    
    def validate_configuration(self, context: ProjectContext) -> tuple[bool, Optional[str]]:
        """
        Validate PostgreSQL configuration.
        """
        # PostgreSQL is self-sufficient
        return (True, None)
    
    def get_connection_string(self, context: ProjectContext, target_service: Optional[str] = None) -> Optional[str]:
        """
        Generate PostgreSQL connection string.
        """
        if not self.context:
            self.context = context
        
        password = self.context.get_or_create_secret("postgres_password")
        port = self.context.get_service_port("postgres", 5432)
        
        return ConnectionBuilder.build_database_url(
            db_type="postgresql",
            host="postgres",
            port=port,
            username="postgres",
            password=password,
            database="warehouse"
        )
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """
        Setup context. We don't write docker-compose.yml here anymore.
        """
        self.context = config.get("project_context")
        # Service registration is now handled by register_services()
        # No need to manually generate secrets/ports here

    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """
        Returns the Docker Compose service configuration for this component.
        
        Args:
            context (ProjectContext): The global project context.
        """
        if not self.context:
            return {}
        
        try:
            template = self.env.get_template("storage/postgres_compose.yml.j2")
            rendered = template.render(
                db_user="postgres",
                db_password=self.context.get_or_create_secret("postgres_password"),
                db_name="warehouse",
                port=self.context.get_service_port("postgres", 5432)
            )
            parsed = yaml.safe_load(rendered)
            return parsed.get("services", {})
        except Exception as e:
            print(f"Error getting postgres service config: {e}")
            return {}
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """
        Returns environment variables required by PostgreSQL.
        
        Args:
            context (ProjectContext): The global project context.
        """
        if not self.context:
            return {}
        
        password = self.context.get_or_create_secret("postgres_password")
        port = self.context.get_service_port("postgres", 5432)
        
        return {
            "POSTGRES_HOST": "postgres",
            "POSTGRES_PORT": str(port),
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": password,
            "POSTGRES_DB": "warehouse"
        }
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        """Returns Docker volumes for data persistence."""
        return {
            "postgres_data": None
        }

ProviderRegistry.register("storage", "PostgreSQL", PostgresGenerator)
