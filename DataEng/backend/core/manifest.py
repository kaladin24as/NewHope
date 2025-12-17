from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum
import secrets

class ServiceCapability(str, Enum):
    """
    Standard capabilities that services can provide.
    Used for service discovery and auto-wiring.
    """
    DATABASE = "database"
    SQL_DATABASE = "sql_database"
    NOSQL_DATABASE = "nosql_database"
    WAREHOUSE = "warehouse"
    MESSAGE_QUEUE = "message_queue"
    STREAM_PROCESSING = "stream_processing"
    OBJECT_STORAGE = "object_storage"
    ORCHESTRATOR = "orchestrator"
    TRANSFORMATION = "transformation"
    INGESTION = "ingestion"
    VISUALIZATION = "visualization"
    MONITORING = "monitoring"
    QUALITY = "quality"

class ServiceConnection(BaseModel):
    """
    Represents a connection to a service (database, storage, etc.)
    Used for cross-component communication and environment variable generation.
    """
    name: str = Field(..., description="Service name (e.g., 'postgres_prod', 's3_data')")
    type: str = Field(..., description="Service type (postgres, snowflake, s3, gcs, etc.)")
    host: str = Field(default="localhost", description="Service hostname")
    port: int = Field(default=0, description="Service port")
    env_prefix: str = Field(..., description="Environment variable prefix (e.g., 'DB_PROD_')")
    capabilities: List[str] = Field(default_factory=list, description="Capabilities this service provides")
    credentials: Dict[str, str] = Field(default_factory=dict, description="Service credentials (username, password, token, etc.)")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Additional service-specific config")
    
    def has_capability(self, capability: str) -> bool:
        """Check if this service has a specific capability."""
        return capability in self.capabilities
    
    def get_connection_string(self, context: Optional[Any] = None) -> Optional[str]:
        """
        Generate a connection string for this service.
        
        Args:
            context: Optional ProjectContext for accessing secrets.
        
        Returns:
            Connection string or None if cannot be generated.
        """
        # PostgreSQL, MySQL, etc.
        if self.type in ["postgres", "postgresql", "mysql"]:
            user = self.credentials.get("username", "user")
            password = self.credentials.get("password", "password")
            db_name = self.extra.get("db_name", "db")
            return f"{self.type}://{user}:{password}@{self.host}:{self.port}/{db_name}"
        
        # Snowflake
        elif self.type == "snowflake":
            account = self.extra.get("account", "")
            warehouse = self.extra.get("warehouse", "")
            database = self.extra.get("database", "")
            user = self.credentials.get("username", "")
            password = self.credentials.get("password", "")
            return f"snowflake://{user}:{password}@{account}/{database}?warehouse={warehouse}"
        
        # BigQuery
        elif self.type == "bigquery":
            project = self.extra.get("project", "")
            dataset = self.extra.get("dataset", "")
            return f"bigquery://{project}/{dataset}"
        
        # Redis
        elif self.type == "redis":
            password = self.credentials.get("password", "")
            if password:
                return f"redis://:{password}@{self.host}:{self.port}"
            return f"redis://{self.host}:{self.port}"
        
        # MongoDB
        elif self.type == "mongodb":
            user = self.credentials.get("username", "")
            password = self.credentials.get("password", "")
            db_name = self.extra.get("db_name", "admin")
            if user and password:
                return f"mongodb://{user}:{password}@{self.host}:{self.port}/{db_name}"
            return f"mongodb://{self.host}:{self.port}/{db_name}"
        
        return None

class DataSource(BaseModel):
    """
    Represents an external data source to extract data from.
    Used for automatic pipeline generation.
    """
    name: str = Field(..., description="Unique identifier for this data source")
    type: str = Field(..., description="Source type: api, database, file, stream")
    connector: str = Field(..., description="Connector implementation: REST_API, PostgreSQL, S3, etc.")
    config: Dict[str, Any] = Field(default_factory=dict, description="Source-specific configuration")
    auth_config: Dict[str, Any] = Field(default_factory=dict, description="Authentication configuration")
    schedule: Optional[str] = Field(None, description="Cron schedule for extraction (e.g., '0 */6 * * *')")
    enabled: bool = Field(True, description="Whether this source is active")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata (schema, endpoints, etc.)")

class ProjectContext(BaseModel):
    """
    Stores global project configuration and state to be shared among generators.
    Provides secrets, port management, and inter-service connectivity.
    """
    project_name: str = Field(..., description="Name of the project being generated")
    base_ports: Dict[str, int] = Field(default_factory=dict, description="Map of service names to assigned ports")
    generated_secrets: Dict[str, str] = Field(default_factory=dict, description="Map of secret keys to generated values")
    
    # Store the full stack selection
    stack: Dict[str, str] = Field(default_factory=dict, description="Selected technology stack")
    
    # Store generated secrets for the stack
    secrets: Dict[str, str] = Field(default_factory=dict, description="Generated secrets for the stack components")
    
    # Service connections for inter-component communication
    connections: List[ServiceConnection] = Field(default_factory=list, description="Registered service connections")
    
    # Data sources for extraction
    data_sources: List[DataSource] = Field(default_factory=list, description="Configured data sources")
    
    # Store arbitrary extra state if needed
    extra: Dict[str, Any] = Field(default_factory=dict)
    
    def get_or_create_secret(self, key: str, length: int = 16) -> str:
        """
        Returns an existing secret for the given key, or generates a new one.
        """
        if key not in self.generated_secrets:
            self.generated_secrets[key] = secrets.token_urlsafe(length)
        return self.generated_secrets[key]

    def get_service_port(self, service_name: str, default: int) -> int:
        """
        Returns the port for a service.
        TODO: specific logic to avoid collisions could be added here.
        """
        if service_name not in self.base_ports:
            self.base_ports[service_name] = default
        return self.base_ports[service_name]
    
    def register_connection(self, conn: ServiceConnection) -> None:
        """
        Register a service connection for cross-component access.
        Example: Airflow can discover Postgres connection registered by Storage generator.
        """
        self.connections.append(conn)
    
    def get_connection(self, name: str) -> Optional[ServiceConnection]:
        """
        Retrieve a registered connection by name.
        Returns None if not found.
        """
        for conn in self.connections:
            if conn.name == name:
                return conn
        return None
    
    def get_connections_by_type(self, service_type: str) -> List[ServiceConnection]:
        """
        Get all connections of a specific type.
        Example: get_connections_by_type('postgres') returns all Postgres DBs.
        """
        return [conn for conn in self.connections if conn.type == service_type]
    
    def get_env_vars(self) -> Dict[str, str]:
        """
        Generate environment variables from all registered connections.
        Format: {ENV_PREFIX}HOST, {ENV_PREFIX}PORT, etc.
        """
        env_vars = {}
        for conn in self.connections:
            prefix = conn.env_prefix
            env_vars[f"{prefix}HOST"] = conn.host
            env_vars[f"{prefix}PORT"] = str(conn.port)
            env_vars[f"{prefix}TYPE"] = conn.type
            
            # Add extra vars
            for key, val in conn.extra.items():
                env_vars[f"{prefix}{key.upper()}"] = str(val)
            
            # Add credentials as env vars
            for cred_key, cred_val in conn.credentials.items():
                env_vars[f"{prefix}{cred_key.upper()}"] = str(cred_val)
        
        return env_vars
    
    def get_service_by_capability(self, capability: str) -> Optional[ServiceConnection]:
        """
        Find the first service that has the specified capability.
        
        Args:
            capability: The capability to search for (e.g., "database", "warehouse").
        
        Returns:
            ServiceConnection if found, None otherwise.
        
        Example:
            db_service = context.get_service_by_capability("database")
            if db_service:
                conn_str = db_service.get_connection_string(context)
        """
        for conn in self.connections:
            if conn.has_capability(capability):
                return conn
        return None
    
    def get_all_services_by_capability(self, capability: str) -> List[ServiceConnection]:
        """
        Find all services that have the specified capability.
        
        Args:
            capability: The capability to search for.
        
        Returns:
            List of ServiceConnections.
        """
        return [conn for conn in self.connections if conn.has_capability(capability)]
    
    def auto_configure_services(self) -> None:
        """
        Automatically configure service connections based on selected stack.
        This is called after all generators have registered their services.
        """
        # This method can be used to perform post-registration configuration
        # For example, linking services together, validating connections, etc.
        pass
    
    def validate_connections(self) -> List[str]:
        """
        Validate that all required service connections are available.
        
        Returns:
            List of error messages. Empty list if all connections are valid.
        """
        errors = []
        
        # Check for duplicate service names
        names = [conn.name for conn in self.connections]
        duplicates = set([name for name in names if names.count(name) > 1])
        if duplicates:
            errors.append(f"Duplicate service names: {', '.join(duplicates)}")
        
        # Check for port conflicts
        ports_used = {}
        for conn in self.connections:
            if conn.port > 0:
                if conn.port in ports_used:
                    errors.append(
                        f"Port conflict: {conn.name} and {ports_used[conn.port]} "
                        f"both trying to use port {conn.port}"
                    )
                else:
                    ports_used[conn.port] = conn.name
        
        return errors
    
    def add_data_source(self, source: DataSource) -> None:
        """
        Add a data source to the project.
        
        Args:
            source: DataSource configuration
        """
        # Check for duplicate names
        existing = self.get_data_source(source.name)
        if existing:
            raise ValueError(f"Data source with name '{source.name}' already exists")
        
        self.data_sources.append(source)
    
    def get_data_source(self, name: str) -> Optional[DataSource]:
        """
        Get a data source by name.
        
        Args:
            name: Name of the data source
        
        Returns:
            DataSource if found, None otherwise
        """
        for source in self.data_sources:
            if source.name == name:
                return source
        return None
    
    def get_data_sources_by_type(self, source_type: str) -> List[DataSource]:
        """
        Get all data sources of a specific type.
        
        Args:
            source_type: Type of source (api, database, file, stream)
        
        Returns:
            List of matching DataSources
        """
        return [source for source in self.data_sources if source.type == source_type]
    
    def remove_data_source(self, name: str) -> bool:
        """
        Remove a data source by name.
        
        Args:
            name: Name of the data source to remove
        
        Returns:
            True if removed, False if not found
        """
        for i, source in enumerate(self.data_sources):
            if source.name == name:
                self.data_sources.pop(i)
                return True
        return False


class ConnectionBuilder:
    """
    Utility class for building connection strings and configurations.
    Provides a consistent interface for generating connections across different services.
    """
    
    @staticmethod
    def build_database_url(
        db_type: str,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        **kwargs
    ) -> str:
        """
        Build a standard database URL.
        
        Args:
            db_type: Type of database (postgres, mysql, etc.)
            host: Database host
            port: Database port
            username: Database username
            password: Database password
            database: Database name
            **kwargs: Additional parameters (e.g., schema, warehouse)
        
        Returns:
            Database URL string.
        """
        base_url = f"{db_type}://{username}:{password}@{host}:{port}/{database}"
        
        # Add query parameters if provided
        if kwargs:
            params = "&".join([f"{k}={v}" for k, v in kwargs.items()])
            base_url = f"{base_url}?{params}"
        
        return base_url
    
    @staticmethod
    def build_object_storage_config(
        provider: str,
        bucket: str,
        region: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Build object storage configuration.
        
        Args:
            provider: Storage provider (s3, gcs, azure)
            bucket: Bucket/container name
            region: Region (for cloud providers)
            access_key: Access key/client ID
            secret_key: Secret key/client secret
            **kwargs: Additional provider-specific config
        
        Returns:
            Configuration dictionary.
        """
        config = {
            "provider": provider,
            "bucket": bucket,
        }
        
        if region:
            config["region"] = region
        if access_key:
            config["access_key"] = access_key
        if secret_key:
            config["secret_key"] = secret_key
        
        config.update(kwargs)
        return config
    
    @staticmethod
    def build_message_queue_url(
        mq_type: str,
        host: str,
        port: int,
        username: Optional[str] = None,
        password: Optional[str] = None,
        vhost: str = "/",
        **kwargs
    ) -> str:
        """
        Build message queue connection URL.
        
        Args:
            mq_type: Type of message queue (amqp, kafka, redis)
            host: MQ host
            port: MQ port
            username: Username (if applicable)
            password: Password (if applicable)
            vhost: Virtual host (for AMQP)
            **kwargs: Additional parameters
        
        Returns:
            Message queue URL.
        """
        if mq_type in ["amqp", "rabbitmq"]:
            if username and password:
                return f"amqp://{username}:{password}@{host}:{port}{vhost}"
            return f"amqp://{host}:{port}{vhost}"
        
        elif mq_type == "kafka":
            return f"{host}:{port}"
        
        elif mq_type == "redis":
            if password:
                return f"redis://:{password}@{host}:{port}"
            return f"redis://{host}:{port}"
        
        return f"{mq_type}://{host}:{port}"
