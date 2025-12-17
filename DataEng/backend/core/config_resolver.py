"""
Configuration resolver for managing dependencies and auto-wiring between providers.
Handles dependency resolution, configuration mapping, and automatic wiring of components.
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict
import networkx as nx  # For topological sorting


class DependencyResolver:
    """
    Resolves dependencies between components and determines generation order.
    Uses topological sorting to ensure components are generated in the correct sequence.
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.component_dependencies: Dict[str, List[str]] = {}
    
    def add_component(self, component_id: str, dependencies: List[str]) -> None:
        """
        Add a component and its dependencies to the resolver.
        
        Args:
            component_id: Unique identifier for the component (e.g., "storage:PostgreSQL")
            dependencies: List of dependency specifications
        """
        self.component_dependencies[component_id] = dependencies
        
        # Add node to graph
        self.graph.add_node(component_id)
        
        # Add edges for dependencies
        for dep in dependencies:
            # Dependencies can be:
            # 1. "category:provider" (specific provider)
            # 2. "capability" (any provider with this capability)
            # For now, we'll handle this during resolution
            pass
    
    def resolve(
        self,
        available_components: Dict[str, Any],
        context: Any
    ) -> Tuple[List[str], List[str]]:
        """
        Resolve dependencies and return generation order.
        
        Args:
            available_components: Dict mapping component_id to generator instance
            context: ProjectContext for capability lookup
        
        Returns:
            Tuple of (ordered_component_ids, errors)
            - ordered_component_ids: List in topological order
            - errors: List of error messages
        """
        errors = []
        
        # Build dependency graph
        for component_id, dependencies in self.component_dependencies.items():
            for dep_spec in dependencies:
                resolved_dep = self._resolve_dependency(
                    dep_spec,
                    available_components,
                    context
                )
                
                if resolved_dep:
                    # Add edge: dependency -> component
                    self.graph.add_edge(resolved_dep, component_id)
                else:
                    errors.append(
                        f"Component '{component_id}' requires '{dep_spec}' but it's not available"
                    )
        
        # Check for cycles
        if not nx.is_directed_acyclic_graph(self.graph):
            cycles = list(nx.simple_cycles(self.graph))
            errors.append(f"Circular dependencies detected: {cycles}")
            return [], errors
        
        # Perform topological sort
        try:
            ordered = list(nx.topological_sort(self.graph))
            # Filter to only include components that were actually added
            ordered = [c for c in ordered if c in available_components]
            return ordered, errors
        except nx.NetworkXError as e:
            errors.append(f"Failed to resolve dependencies: {str(e)}")
            return [], errors
    
    def _resolve_dependency(
        self,
        dep_spec: str,
        available_components: Dict[str, Any],
        context: Any
    ) -> Optional[str]:
        """
        Resolve a dependency specification to a concrete component.
        
        Args:
            dep_spec: Dependency specification (e.g., "database", "storage:PostgreSQL")
            available_components: Available component instances
            context: ProjectContext
        
        Returns:
            Component ID or None if not found
        """
        # Case 1: Specific provider (category:provider)
        if ":" in dep_spec:
            if dep_spec in available_components:
                return dep_spec
            return None
        
        # Case 2: Capability-based dependency
        # Look for any component that provides this capability
        service = context.get_service_by_capability(dep_spec)
        if service:
            # Map service type back to component ID
            # This is a simplification; in practice, we'd need better mapping
            for comp_id in available_components:
                if service.type in comp_id.lower():
                    return comp_id
        
        return None


class ConfigurationMapper:
    """
    Maps configurations between different providers.
    Handles translation of settings when components interact.
    """
    
    # Mapping of database types to their connection adapters
    DATABASE_ADAPTERS = {
        "PostgreSQL": {
            "dlt_destination": "postgres",
            "dbt_adapter": "postgres",
            "sqlalchemy_driver": "postgresql+psycopg2"
        },
        "Snowflake": {
            "dlt_destination": "snowflake",
            "dbt_adapter": "snowflake",
            "sqlalchemy_driver": "snowflake"
        },
        "BigQuery": {
            "dlt_destination": "bigquery",
            "dbt_adapter": "bigquery",
            "sqlalchemy_driver": "bigquery"
        },
        "DuckDB": {
            "dlt_destination": "duckdb",
            "dbt_adapter": "duckdb",
            "sqlalchemy_driver": "duckdb"
        },
        "Redshift": {
            "dlt_destination": "redshift",
            "dbt_adapter": "redshift",
            "sqlalchemy_driver": "redshift+psycopg2"
        }
    }
    
    @staticmethod
    def get_adapter(storage_provider: str, tool: str) -> Optional[str]:
        """
        Get the appropriate adapter name for a tool given a storage provider.
        
        Args:
            storage_provider: Name of the storage provider (e.g., "PostgreSQL")
            tool: Tool that needs the adapter (e.g., "dlt", "dbt")
        
        Returns:
            Adapter name or None if not found
        """
        provider_config = ConfigurationMapper.DATABASE_ADAPTERS.get(storage_provider)
        if not provider_config:
            return None
        
        # Map tool to adapter key
        adapter_key_map = {
            "dlt": "dlt_destination",
            "DLT": "dlt_destination",
            "dbt": "dbt_adapter",
            "sqlalchemy": "sqlalchemy_driver"
        }
        
        adapter_key = adapter_key_map.get(tool)
        if not adapter_key:
            return None
        
        return provider_config.get(adapter_key)
    
    @staticmethod
    def get_required_packages(storage_provider: str, tool: str) -> List[str]:
        """
        Get Python packages required for a specific tool-storage combination.
        
        Args:
            storage_provider: Name of the storage provider
            tool: Tool name
        
        Returns:
            List of required Python packages
        """
        packages = []
        
        # DLT packages
        if tool.upper() == "DLT":
            adapter = ConfigurationMapper.get_adapter(storage_provider, "dlt")
            if adapter:
                packages.append(f"dlt[{adapter}]")
        
        # dbt packages
        elif tool.lower() == "dbt":
            adapter = ConfigurationMapper.get_adapter(storage_provider, "dbt")
            if adapter:
                packages.append(f"dbt-{adapter}")
        
        return packages
    
    @staticmethod
    def map_env_vars(
        from_service: str,
        to_format: str,
        context: Any
    ) -> Dict[str, str]:
        """
        Map environment variables from one service to another format.
        
        Args:
            from_service: Source service name
            to_format: Target format (e.g., "airflow_conn", "dbt_profile")
            context: ProjectContext
        
        Returns:
            Dictionary of mapped environment variables
        """
        service = context.get_connection(from_service)
        if not service:
            return {}
        
        env_vars = {}
        
        # Airflow connection format
        if to_format == "airflow_conn":
            conn_str = service.get_connection_string(context)
            if conn_str:
                # Airflow connection ID format
                conn_id = from_service.replace("_", "").lower()
                env_vars[f"AIRFLOW_CONN_{conn_id.upper()}"] = conn_str
        
        # dbt profile format
        elif to_format == "dbt_profile":
            env_vars.update({
                "DBT_HOST": service.host,
                "DBT_PORT": str(service.port),
                "DBT_USER": service.credentials.get("username", ""),
                "DBT_PASSWORD": service.credentials.get("password", ""),
                "DBT_DATABASE": service.extra.get("db_name", "")
            })
        
        return env_vars


class AutoWiring:
    """
    Automatically wires components together based on their capabilities and requirements.
    """
    
    @staticmethod
    def wire_ingestion_to_storage(
        ingestion_generator: Any,
        context: Any
    ) -> Dict[str, Any]:
        """
        Wire ingestion component to available storage.
        
        Args:
            ingestion_generator: The ingestion generator instance
            context: ProjectContext
        
        Returns:
            Configuration dictionary for the ingestion component
        """
        config = {}
        
        # Find a database/warehouse for ingestion to write to
        db_service = context.get_service_by_capability("warehouse")
        if not db_service:
            db_service = context.get_service_by_capability("database")
        
        if db_service:
            config["destination_type"] = db_service.type
            config["destination_connection"] = db_service.get_connection_string(context)
            config["destination_host"] = db_service.host
            config["destination_port"] = db_service.port
        
        return config
    
    @staticmethod
    def wire_transformation_to_storage(
        transformation_generator: Any,
        context: Any
    ) -> Dict[str, Any]:
        """
        Wire transformation component to available storage.
        
        Args:
            transformation_generator: The transformation generator instance
            context: ProjectContext
        
        Returns:
            Configuration dictionary for the transformation component
        """
        config = {}
        
        # Find warehouse or database
        warehouse = context.get_service_by_capability("warehouse")
        if warehouse:
            config["target_type"] = warehouse.type
            config["target_connection"] = warehouse.get_connection_string(context)
            config["target_host"] = warehouse.host
            config["target_port"] = warehouse.port
            config["target_database"] = warehouse.extra.get("db_name", "warehouse")
            config["target_user"] = warehouse.credentials.get("username", "")
            config["target_password"] = warehouse.credentials.get("password", "")
        
        return config
    
    @staticmethod
    def wire_orchestration_to_all(
        orchestration_generator: Any,
        context: Any
    ) -> Dict[str, Any]:
        """
        Wire orchestration component to all available services.
        Orchestration typically needs to know about all other components.
        
        Args:
            orchestration_generator: The orchestration generator instance
            context: ProjectContext
        
        Returns:
            Configuration dictionary with all service connections
        """
        config = {
            "connections": {}
        }
        
        # Add all registered connections
        for conn in context.connections:
            conn_info = {
                "type": conn.type,
                "host": conn.host,
                "port": conn.port,
                "connection_string": conn.get_connection_string(context),
                "capabilities": conn.capabilities
            }
            config["connections"][conn.name] = conn_info
        
        return config
    
    @staticmethod
    def auto_wire_component(
        component: Any,
        category: str,
        context: Any
    ) -> Dict[str, Any]:
        """
        Automatically wire a component based on its category.
        
        Args:
            component: The generator instance
            category: Component category (ingestion, transformation, orchestration, etc.)
            context: ProjectContext
        
        Returns:
            Configuration dictionary
        """
        if category == "ingestion":
            return AutoWiring.wire_ingestion_to_storage(component, context)
        elif category == "transformation":
            return AutoWiring.wire_transformation_to_storage(component, context)
        elif category == "orchestration":
            return AutoWiring.wire_orchestration_to_all(component, context)
        
        return {}
