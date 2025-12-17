import os
from typing import Dict, Any, List, Optional
from jinja2 import Environment
from core.interfaces import ComponentGenerator
from core.registry import ProviderRegistry
from core.manifest import ProjectContext, ServiceConnection

class DLTGenerator(ComponentGenerator):
    def register_services(self, context: ProjectContext) -> None:
        """
        Register DLT as an ingestion service.
        """
        # DLT doesn't expose a service, but we could register it for documentation
        connection = ServiceConnection(
            name="dlt_ingestion",
            type="dlt",
            host="localhost",
            port=0,
            env_prefix="DLT_",
            capabilities=["ingestion"],
            extra={}
        )
        context.register_connection(connection)
    
    def get_dependencies(self) -> List[str]:
        """
        DLT needs a warehouse or database to write to.
        """
        return ["warehouse", "database"]
    
    def validate_configuration(self, context: ProjectContext) -> tuple[bool, Optional[str]]:
        """
        Validate that DLT has a destination to write to.
        """
        warehouse = context.get_service_by_capability("warehouse")
        database = context.get_service_by_capability("database")
        
        if not warehouse and not database:
            return (False, "DLT requires a warehouse or database destination")
        
        return (True, None)
    
    def get_connection_string(self, context: ProjectContext, target_service: Optional[str] = None) -> Optional[str]:
        """
        Get connection string to the destination warehouse.
        """
        warehouse = context.get_service_by_capability("warehouse")
        if warehouse:
            return warehouse.get_connection_string(context)
        return None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        context = config.get("project_context")
        
        # Auto-discover destination from registered services
        destination = "postgres"  # default fallback
        destination_service = context.get_service_by_capability("warehouse") if context else None
        if not destination_service and context:
            destination_service = context.get_service_by_capability("database")
        
        if destination_service:
            # Use ConfigurationMapper to get the correct adapter name
            storage_provider = context.stack.get("storage", "PostgreSQL")
            destination = ConfigurationMapper.get_adapter(storage_provider, "dlt") or "postgres"
                
        try:
            # 1. Generate Pipeline Script
            template = self.env.get_template("ingestion/dlt_pipeline.py.j2")
            content = template.render(
                pipeline_name=config.get("pipeline_name", "my_dlt_pipeline"),
                destination=destination,
                dataset_name=config.get("dataset_name", "my_data")
            )
            with open(os.path.join(output_dir, "ingestion_pipeline.py"), "w") as f:
                f.write(content)
                
            # 2. Generate Dockerfile for Ingestion
            dockerfile_content = """
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install python dependencies
RUN pip install dlt[postgres]  # basic default, should be dynamic based on destination

COPY ingestion_pipeline.py .

CMD ["python", "ingestion_pipeline.py"]
"""
            with open(os.path.join(output_dir, "Dockerfile.ingestion"), "w") as f:
                f.write(dockerfile_content.strip())
            
        except Exception as e:
            print(f"Error rendering ingestion (DLT): {e}")

    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """
        Returns the Docker Service definition for DLT.
        """
        service_name = "dlt_ingestion"
        return {
            service_name: {
                "build": {
                    "context": ".",
                    "dockerfile": "Dockerfile.ingestion"
                },
                "environment": self.get_env_vars(context),
                "networks": ["antigravity_net"]
            }
        }

    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """
        Returns environment variables needed for DLT.
        """
        return {
            "DESTINATION__POSTGRES__CREDENTIALS": "postgresql://user:password@postgres:5432/db", # Example default
            "PIPELINE_NAME": "antigravity_pipeline"
        }

ProviderRegistry.register("ingestion", "DLT", DLTGenerator)
