"""
Template context builder for dynamic template rendering.
Provides utilities and helpers for Jinja2 templates to access service connections
and generate configuration dynamically.
"""

from typing import Dict, Any, Optional
from jinja2 import Environment


class TemplateContextBuilder:
    """
    Builds context dictionaries for template rendering with dynamic service information.
    """
    
    @staticmethod
    def build_context(
        project_context: Any,
        component_category: str,
        component_name: str,
        base_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build a complete template context for rendering.
        
        Args:
            project_context: ProjectContext instance
            component_category: Category of the component being generated
            component_name: Name of the component
            base_config: Base configuration dictionary
        
        Returns:
            Complete context dictionary for template rendering
        """
        context = base_config.copy() if base_config else {}
        
        # Add project basics
        context["project_name"] = project_context.project_name
        context["stack"] = project_context.stack
        
        # Add service discovery helpers
        context["services"] = TemplateContextBuilder._build_services_context(project_context)
        
        # Add connection helpers
        context["get_connection"] = lambda name: project_context.get_connection(name)
        context["get_service_by_capability"] = lambda cap: project_context.get_service_by_capability(cap)
        
        # Add connection string helpers
        context["get_connection_string"] = lambda service_name: (
            TemplateContextBuilder._get_connection_string_helper(project_context, service_name)
        )
        
        # Add environment variables
        context["env_vars"] = project_context.get_env_vars()
        
        # Add secrets
        context["secrets"] = project_context.generated_secrets
        
        # Add ports
        context["ports"] = project_context.base_ports
        
        return context
    
    @staticmethod
    def _build_services_context(project_context: Any) -> Dict[str, Any]:
        """
        Build a services context with all registered connections.
        
        Args:
            project_context: ProjectContext instance
        
        Returns:
            Dictionary with service information organized by type and capability
        """
        services = {
            "all": [],
            "by_type": {},
            "by_capability": {}
        }
        
        for conn in project_context.connections:
            # Add to all services
            service_info = {
                "name": conn.name,
                "type": conn.type,
                "host": conn.host,
                "port": conn.port,
                "capabilities": conn.capabilities,
                "connection_string": conn.get_connection_string(project_context)
            }
            services["all"].append(service_info)
            
            # Organize by type
            if conn.type not in services["by_type"]:
                services["by_type"][conn.type] = []
            services["by_type"][conn.type].append(service_info)
            
            # Organize by capability
            for cap in conn.capabilities:
                if cap not in services["by_capability"]:
                    services["by_capability"][cap] = []
                services["by_capability"][cap].append(service_info)
        
        return services
    
    @staticmethod
    def _get_connection_string_helper(
        project_context: Any,
        service_name: str
    ) -> Optional[str]:
        """
        Helper to get connection string for a service by name.
        
        Args:
            project_context: ProjectContext instance
            service_name: Name of the service
        
        Returns:
            Connection string or None
        """
        conn = project_context.get_connection(service_name)
        if conn:
            return conn.get_connection_string(project_context)
        return None
    
    @staticmethod
    def add_jinja_filters(env: Environment) -> None:
        """
        Add custom Jinja2 filters for template rendering.
        
        Args:
            env: Jinja2 Environment instance
        """
        
        def filter_connection_string(service: Dict[str, Any]) -> str:
            """Filter to get connection string from service dict."""
            return service.get("connection_string", "")
        
        def filter_env_var_name(service_name: str, var_name: str) -> str:
            """Filter to generate environment variable name."""
            return f"{service_name.upper().replace('-', '_')}_{var_name.upper()}"
        
        def filter_docker_service_name(component_name: str) -> str:
            """Filter to generate Docker service name."""
            return component_name.lower().replace(" ", "_").replace("-", "_")
        
        def filter_safe_name(name: str) -> str:
            """Filter to make a name safe for use in code."""
            return name.lower().replace(" ", "_").replace("-", "_")
        
        # Add filters to environment
        env.filters["connection_string"] = filter_connection_string
        env.filters["env_var_name"] = filter_env_var_name
        env.filters["docker_service_name"] = filter_docker_service_name
        env.filters["safe_name"] = filter_safe_name
    
    @staticmethod
    def build_docker_compose_env(
        project_context: Any,
        service_name: str
    ) -> Dict[str, str]:
        """
        Build environment variables for a Docker Compose service.
        
        Args:
            project_context: ProjectContext instance
            service_name: Name of the service
        
        Returns:
            Dictionary of environment variables
        """
        env_vars = {}
        
        # Add connection information for all registered services
        for conn in project_context.connections:
            prefix = conn.env_prefix
            env_vars[f"{prefix}HOST"] = conn.host
            env_vars[f"{prefix}PORT"] = str(conn.port)
            env_vars[f"{prefix}TYPE"] = conn.type
            
            # Add credentials
            for key, val in conn.credentials.items():
                env_vars[f"{prefix}{key.upper()}"] = str(val)
            
            # Add extra fields
            for key, val in conn.extra.items():
                env_vars[f"{prefix}{key.upper()}"] = str(val)
        
        return env_vars
    
    @staticmethod
    def build_requirements_txt(
        project_context: Any,
        generators: Dict[str, Any]
    ) -> str:
        """
        Build a consolidated requirements.txt content.
        
        Args:
            project_context: ProjectContext instance
            generators: Dictionary of generator instances
        
        Returns:
            requirements.txt file content as string
        """
        all_requirements = set()
        
        # Collect requirements from all generators
        for generator in generators.values():
            if hasattr(generator, 'get_requirements'):
                reqs = generator.get_requirements()
                all_requirements.update(reqs)
        
        # Sort and format
        requirements_list = sorted(list(all_requirements))
        return "\n".join(requirements_list) + "\n"
    
    @staticmethod
    def build_env_file(project_context: Any) -> str:
        """
        Build a .env file content with all environment variables.
        
        Args:
            project_context: ProjectContext instance
        
        Returns:
            .env file content as string
        """
        lines = [
            "# Auto-generated environment file",
            f"# Project: {project_context.project_name}",
            "",
            "# Secrets",
        ]
        
        for key, val in project_context.generated_secrets.items():
            lines.append(f"{key.upper()}={val}")
        
        lines.extend(["", "# Service Connections", ""])
        
        env_vars = project_context.get_env_vars()
        for key, val in sorted(env_vars.items()):
            lines.append(f"{key}={val}")
        
        return "\n".join(lines) + "\n"
