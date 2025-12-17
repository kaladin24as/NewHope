"""
Additional ingestion providers: Airbyte
"""
import os
from typing import Dict, Any, Optional
from core.interfaces import ComponentGenerator
from core.registry import ProviderRegistry
from core.manifest import ProjectContext


class AirbyteGenerator(ComponentGenerator):
    """Generator for Airbyte open-source ELT platform."""
    
    def __init__(self, env):
        super().__init__(env)
        self.context: Optional[ProjectContext] = None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """
        Generate Airbyte configuration files.
        
        Airbyte runs as Docker containers with a web UI.
        """
        self.context = config.get("project_context")
        if not self.context:
            return
        
        # Assign ports
        self.context.get_service_port("airbyte-webapp", 8000)
        self.context.get_service_port("airbyte-server", 8001)
        
        # Create airbyte config directory
        airbyte_dir = os.path.join(output_dir, "config", "airbyte")
        os.makedirs(airbyte_dir, exist_ok=True)
        
        try:
            # Create a README with setup instructions
            readme = """# Airbyte Setup

## Quick Start

1. Start Airbyte:
   ```bash
   docker-compose up airbyte-webapp airbyte-server airbyte-worker
   ```

2. Access UI: http://localhost:8000

3. Default credentials:
   - Username: airbyte
   - Password: password

## Configure Connections

1. Add Source (e.g., PostgreSQL, API, CSV)
2. Add Destination (e.g., Snowflake, BigQuery, Data Lake)
3. Create Connection and schedule sync

## Documentation

- Official Docs: https://docs.airbyte.com
- Connector Catalog: https://docs.airbyte.com/integrations
"""
            
            readme_path = os.path.join(airbyte_dir, "README.md")
            with open(readme_path, 'w') as f:
                f.write(readme)
                
        except Exception as e:
            print(f"Error generating Airbyte setup: {e}")
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """Returns Docker Compose services for Airbyte stack."""
        if not self.context:
            return {}
        
        webapp_port = self.context.get_service_port("airbyte-webapp", 8000)
        server_port = self.context.get_service_port("airbyte-server", 8001)
        
        return {
            "airbyte-db": {
                "image": "airbyte/db:latest",
                "environment": {
                    "POSTGRES_USER": "airbyte",
                    "POSTGRES_PASSWORD": "airbyte",
                    "POSTGRES_DB": "airbyte"
                },
                "volumes": ["airbyte_db:/var/lib/postgresql/data"]
            },
            "airbyte-server": {
                "image": "airbyte/server:latest",
                "ports": [f"{server_port}:8001"],
                "environment": {
                    "DATABASE_USER": "airbyte",
                    "DATABASE_PASSWORD": "airbyte",
                    "DATABASE_DB": "airbyte",
                    "DATABASE_URL": "jdbc:postgresql://airbyte-db:5432/airbyte",
                    "CONFIG_ROOT": "/data",
                    "WORKSPACE_ROOT": "/tmp/workspace"
                },
                "volumes": [
                    "airbyte_data:/data",
                    "airbyte_workspace:/tmp/workspace"
                ],
                "depends_on": ["airbyte-db"]
            },
            "airbyte-webapp": {
                "image": "airbyte/webapp:latest",
                "ports": [f"{webapp_port}:80"],
                "environment": {
                    "AIRBYTE_SERVER_HOST": "airbyte-server",
                    "AIRBYTE_SERVER_PORT": "8001"
                },
                "depends_on": ["airbyte-server"]
            },
            "airbyte-worker": {
                "image": "airbyte/worker:latest",
                "environment": {
                    "DATABASE_USER": "airbyte",
                    "DATABASE_PASSWORD": "airbyte",
                    "DATABASE_URL": "jdbc:postgresql://airbyte-db:5432/airbyte",
                    "CONFIG_ROOT": "/data",
                    "WORKSPACE_ROOT": "/tmp/workspace",
                    "LOCAL_ROOT": "/tmp/airbyte_local"
                },
                "volumes": [
                    "airbyte_data:/data",
                    "airbyte_workspace:/tmp/workspace",
                    "/var/run/docker.sock:/var/run/docker.sock"
                ],
                "depends_on": ["airbyte-server"]
            }
        }
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """Returns environment variables for Airbyte."""
        if not self.context:
            return {}
        
        webapp_port = self.context.get_service_port("airbyte-webapp", 8000)
        
        return {
            "AIRBYTE_URL": f"http://localhost:{webapp_port}",
            "AIRBYTE_USERNAME": "airbyte",
            "AIRBYTE_PASSWORD": "password"
        }
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        """Returns Docker volumes for Airbyte data persistence."""
        return {
            "airbyte_db": None,
            "airbyte_data": None,
            "airbyte_workspace": None
        }


# Register provider
ProviderRegistry.register("ingestion", "Airbyte", AirbyteGenerator)
