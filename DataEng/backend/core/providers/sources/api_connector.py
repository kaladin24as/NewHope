"""
API Data Source Connector

Provides connectivity to REST and GraphQL APIs with support for various authentication methods,
retry logic, rate limiting, and pagination.
"""

import os
import time
from typing import Dict, Any, List, Optional
from jinja2 import Environment

from core.interfaces import DataSourceConnector
from core.registry import ProviderRegistry
from core.manifest import ProjectContext, ServiceConnection
from .auth import AuthStrategy, NoAuth, APIKeyAuth, BearerTokenAuth, OAuth2Auth, BasicAuth


class APIConnector(DataSourceConnector):
    """
    Connector for REST and GraphQL APIs.
    
    Features:
    - Multiple authentication strategies
    - Automatic retry with exponential backoff
    - Rate limiting support
    - Pagination handling
    - Schema discovery from OpenAPI specs
    """
    
    def __init__(self, env: Environment):
        super().__init__(env)
        self.auth_strategy: AuthStrategy = NoAuth()
    
    def get_source_type(self) -> str:
        return "api"
    
    def get_auth_strategy(self) -> Dict[str, Any]:
        return {
            "type": self.auth_strategy.get_auth_type(),
            "config": {}
        }
    
    def _create_auth_strategy(self, auth_config: Dict[str, Any]) -> AuthStrategy:
        """
        Factory method to create appropriate auth strategy based on config.
        
        Args:
            auth_config: Authentication configuration
        
        Returns:
            Configured AuthStrategy instance
        """
        auth_type = auth_config.get("type", "none")
        
        if auth_type == "none":
            return NoAuth()
        elif auth_type == "api_key":
            return APIKeyAuth(
                location=auth_config.get("location", "header"),
                key_name=auth_config.get("key_name", "X-API-Key")
            )
        elif auth_type == "bearer":
            return BearerTokenAuth()
        elif auth_type == "oauth2":
            token_url = auth_config.get("token_url")
            if not token_url:
                raise ValueError("OAuth2 requires 'token_url' in auth_config")
            return OAuth2Auth(token_url=token_url)
        elif auth_type == "basic":
            return BasicAuth()
        else:
            raise ValueError(f"Unsupported authentication type: {auth_type}")
    
    def test_connection(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Test connectivity to the API.
        
        Args:
            config: Source configuration containing base_url and auth
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            import requests
            
            base_url = config.get("base_url")
            if not base_url:
                return (False, "Missing 'base_url' in configuration")
            
            # Create auth strategy
            auth_config = config.get("auth", {})
            auth_strategy = self._create_auth_strategy(auth_config)
            
            # Validate auth configuration
            env_prefix = config.get("name", "").upper() + "_"
            is_valid, error_msg = auth_strategy.validate_config(env_prefix)
            if not is_valid:
                return (False, error_msg)
            
            # Prepare request
            request_config = {"headers": {}}
            request_config = auth_strategy.apply_auth(request_config, env_prefix)
            
            # Test connection with a simple GET request
            test_endpoint = config.get("test_endpoint", "/")
            test_url = base_url.rstrip("/") + "/" + test_endpoint.lstrip("/")
            
            response = requests.get(
                test_url,
                headers=request_config.get("headers", {}),
                params=request_config.get("params", {}),
                auth=request_config.get("auth"),
                timeout=10
            )
            
            # Consider 2xx and 401/403 as "connection successful"
            # (401/403 means we reached the API, just auth might need adjustment)
            if response.status_code < 500:
                if response.status_code >= 400:
                    return (True, f"⚠️ Connected but got HTTP {response.status_code}. Check authentication.")
                return (True, None)
            else:
                return (False, f"Server error: HTTP {response.status_code}")
            
        except ImportError:
            return (False, "requests library not installed. Run: pip install requests")
        except requests.exceptions.ConnectionError as e:
            return (False, f"Connection failed: {str(e)}")
        except requests.exceptions.Timeout:
            return (False, "Connection timeout after 10 seconds")
        except Exception as e:
            return (False, f"Error: {str(e)}")
    
    def discover_schema(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Attempt to discover API schema from OpenAPI/Swagger spec.
        
        Args:
            config: Source configuration
        
        Returns:
            Discovered schema or None
        """
        try:
            import requests
            
            base_url = config.get("base_url", "").rstrip("/")
            
            # Common OpenAPI spec locations
            spec_paths = [
                "/openapi.json",
                "/swagger.json",
                "/api-docs",
                "/v3/api-docs",
                "/docs/openapi.json"
            ]
            
            for spec_path in spec_paths:
                try:
                    response = requests.get(f"{base_url}{spec_path}", timeout=5)
                    if response.status_code == 200:
                        spec = response.json()
                        
                        # Extract endpoints from OpenAPI spec
                        endpoints = []
                        paths = spec.get("paths", {})
                        
                        for path, methods in paths.items():
                            for method, details in methods.items():
                                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                                    endpoints.append({
                                        "path": path,
                                        "method": method.upper(),
                                        "summary": details.get("summary", ""),
                                        "description": details.get("description", "")
                                    })
                        
                        return {
                            "spec_url": f"{base_url}{spec_path}",
                            "endpoints": endpoints,
                            "openapi_version": spec.get("openapi") or spec.get("swagger")
                        }
                
                except:
                    continue
            
            return None
            
        except:
            return None
    
    def register_services(self, context: ProjectContext) -> None:
        """
        Register API source as a service in the project context.
        """
        # APIs don't typically expose services, but we register for tracking
        connection = ServiceConnection(
            name="api_source",
            type="api",
            host="external",
            port=0,
            env_prefix="API_",
            capabilities=["data_source", "extraction"],
            extra={}
        )
        context.register_connection(connection)
    
    def get_dependencies(self) -> List[str]:
        """
        API connectors don't have service dependencies.
        """
        return []
    
    def validate_configuration(self, context: ProjectContext) -> tuple[bool, Optional[str]]:
        """
        Validate API source configuration.
        """
        # API sources are independent, no validation needed
        return (True, None)
    
    def get_connection_string(self, context: ProjectContext, target_service: Optional[str] = None) -> Optional[str]:
        """
        Not applicable for API sources.
        """
        return None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """
        Generate DLT-based extraction pipeline for the API source.
        
        Args:
            output_dir: Directory to write generated files
            config: Configuration containing source details
        """
        try:
            source_name = config.get("name", "api_source")
            source_config = config.get("config", {})
            auth_config = config.get("auth", {})
            
            # Get project context if available
            context = config.get("project_context")
            destination = "postgres"  # default
            
            if context:
                destination_service = context.get_service_by_capability("warehouse")
                if not destination_service:
                    destination_service = context.get_service_by_capability("database")
                if destination_service:
                    # Map to DLT destination name
                    storage_provider = context.stack.get("storage", "PostgreSQL")
                    # Simplified mapping
                    if "postgres" in storage_provider.lower():
                        destination = "postgres"
                    elif "bigquery" in storage_provider.lower():
                        destination = "bigquery"
                    elif "snowflake" in storage_provider.lower():
                        destination = "snowflake"
            
            # Generate extraction pipeline using template
            template = self.env.get_template("sources/api_extractor.py.j2")
            content = template.render(
                source={
                    "name": source_name,
                    "config": source_config,
                    "auth": auth_config
                },
                destination=destination,
                dataset_name=config.get("dataset_name", "extracted_data")
            )
            
            # Write pipeline file
            pipeline_file = os.path.join(output_dir, f"{source_name}_pipeline.py")
            with open(pipeline_file, "w") as f:
                f.write(content)
            
            print(f"✅ Generated API extraction pipeline: {pipeline_file}")
            
        except Exception as e:
            print(f"❌ Error generating API connector: {e}")
            raise
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """
        API connectors don't typically need their own Docker service.
        """
        return {}
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """
        Return environment variables template for API authentication.
        """
        # This will be populated based on the specific auth strategy
        return {
            "API_BASE_URL": "https://api.example.com",
            "API_KEY": "your-api-key-here"
        }
    
    def get_extraction_dependencies(self) -> List[str]:
        """
        Python packages needed for API extraction.
        """
        return [
            "requests>=2.31.0",
            "python-dateutil>=2.8.2",
            "tenacity>=8.2.3"  # For retry logic
        ]


# Register the API connector
ProviderRegistry.register("sources", "REST_API", APIConnector)
