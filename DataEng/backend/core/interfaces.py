from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class ComponentGenerator(ABC):
    """
    Abstract base class for all component generators (Ingestion, Storage, etc.)
    """
    
    def __init__(self, env: Any):
        self.env = env

    @abstractmethod
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """
        Generates the component files in the output directory.
        
        Args:
            output_dir (str): The base directory where the project is being generated.
            config (Dict[str, Any]): Configuration specific to this component.
        """
        pass

    @abstractmethod
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """
        Returns the Docker Compose service configuration for this component.
        
        Args:
            context (ProjectContext): The global project context.
        """
        pass

    @abstractmethod
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """
        Returns the environment variables required by this component.
        
        Args:
            context (ProjectContext): The global project context.
        """
        pass

    def get_requirements(self) -> List[str]:
        """
        Returns the Python dependencies required by this component.
        Override this method to list dependencies.
        """
        return []

    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        """
        Returns the Docker Compose volumes required by this component.
        """
        return {}
    
    def register_services(self, context: Any) -> None:
        """
        Register services that this component provides into the ProjectContext.
        This allows other components to discover and use these services.
        
        Args:
            context (ProjectContext): The global project context.
        
        Example:
            context.register_connection(ServiceConnection(
                name="postgres_prod",
                type="postgres",
                host="postgres",
                port=5432,
                env_prefix="DB_",
                capabilities=["database", "sql", "warehouse"],
                extra={"db_name": "warehouse"}
            ))
        """
        pass
    
    def get_dependencies(self) -> List[str]:
        """
        Declare what services/capabilities this component depends on.
        
        Returns:
            List of dependency specifications in format:
            - "category:provider" (e.g., "storage:PostgreSQL")
            - "capability:name" (e.g., "database", "message_queue")
        
        Example:
            return ["database", "storage:any"]  # Needs any database and storage
        """
        return []
    
    def validate_configuration(self, context: Any) -> tuple[bool, Optional[str]]:
        """
        Validate that this component can be generated with the current configuration.
        
        Args:
            context (ProjectContext): The global project context.
        
        Returns:
            Tuple of (is_valid, error_message).
            If valid, returns (True, None).
            If invalid, returns (False, "error description").
        
        Example:
            if not context.get_service_by_capability("database"):
                return (False, "This component requires a database")
            return (True, None)
        """
        return (True, None)
    
    def get_connection_string(self, context: Any, target_service: Optional[str] = None) -> Optional[str]:
        """
        Generate a connection string for this component or to connect to it.
        
        Args:
            context (ProjectContext): The global project context.
            target_service: Optional name of specific service to connect to.
        
        Returns:
            Connection string or None if not applicable.
        
        Example:
            # PostgreSQL generator:
            password = context.get_or_create_secret("postgres_password")
            return f"postgresql://postgres:{password}@postgres:5432/warehouse"
        """
        return None


class DataSourceConnector(ComponentGenerator):
    """
    Abstract base class for all data source connectors (APIs, databases, files, streams).
    
    Data source connectors are responsible for:
    - Connecting to external data sources
    - Authenticating with the source
    - Discovering available data structures
    - Generating extraction pipeline code
    """
    
    @abstractmethod
    def get_source_type(self) -> str:
        """
        Returns the type of data source this connector handles.
        
        Returns:
            One of: "api", "database", "file", "stream"
        """
        pass
    
    @abstractmethod
    def get_auth_strategy(self) -> Dict[str, Any]:
        """
        Returns the authentication configuration for this source.
        
        Returns:
            Dictionary containing authentication details:
            {
                "type": "api_key" | "oauth2" | "bearer" | "basic" | "none",
                "config": {...}  # Auth-specific configuration
            }
        """
        pass
    
    def test_connection(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Test connectivity to the data source.
        
        Args:
            config: Configuration for this specific source instance
        
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
            If successful, returns (True, None)
            If failed, returns (False, "error description")
        
        Example:
            try:
                response = requests.get(base_url, headers=auth_headers, timeout=10)
                response.raise_for_status()
                return (True, None)
            except Exception as e:
                return (False, f"Connection failed: {str(e)}")
        """
        # Default implementation - can be overridden
        return (True, None)
    
    def discover_schema(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Auto-discover available data structures from the source.
        
        Args:
            config: Configuration for this specific source instance
        
        Returns:
            Dictionary containing discovered schema information, or None if not supported.
            Format depends on source type:
            - API: {"endpoints": [...], "models": {...}}
            - Database: {"tables": [...], "columns": {...}}
            - File: {"files": [...], "schema": {...}}
        
        Example:
            # For REST API with OpenAPI spec:
            return {
                "endpoints": [
                    {"path": "/users", "method": "GET", "response_schema": {...}},
                    {"path": "/orders", "method": "GET", "response_schema": {...}}
                ]
            }
        """
        return None
    
    def get_extraction_dependencies(self) -> List[str]:
        """
        Returns Python package dependencies needed for extraction.
        
        Returns:
            List of pip-installable package names
        
        Example:
            return ["requests", "python-dateutil", "retry"]
        """
        return []
