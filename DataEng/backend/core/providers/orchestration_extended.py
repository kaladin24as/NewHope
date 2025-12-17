"""
Additional orchestration providers: Prefect and Dagster
"""
import os
import yaml
from typing import Dict, Any, Optional
from core.interfaces import ComponentGenerator
from core.registry import ProviderRegistry
from core.manifest import ProjectContext


class PrefectGenerator(ComponentGenerator):
    """Generator for Prefect modern workflow orchestration."""
    
    def __init__(self, env):
        super().__init__(env)
        self.context: Optional[ProjectContext] = None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """Generate Prefect workflow files."""
        self.context = config.get("project_context")
        if not self.context:
            return
        
        # Create flows directory
        flows_dir = os.path.join(output_dir, "flows")
        os.makedirs(flows_dir, exist_ok=True)
        
        try:
            # Create example Prefect flow
            example_flow = """
from prefect import flow, task
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@task(retries=3, retry_delay_seconds=60)
def extract_data():
    \"\"\"Extract data from source.\"\"\"
    logger.info("Extracting data...")
    # Add your extraction logic here
    return {"status": "success", "records": 100}


@task
def transform_data(data: dict):
    \"\"\"Transform extracted data.\"\"\"
    logger.info(f"Transforming {data['records']} records...")
    # Add your transformation logic here
    return data


@task
def load_data(data: dict):
    \"\"\"Load data to destination.\"\"\"
    logger.info("Loading data to warehouse...")
    # Add your loading logic here
    return data


@flow(name="ETL Pipeline", log_prints=True)
def etl_pipeline():
    \"\"\"Main ETL pipeline flow.\"\"\"
    data = extract_data()
    transformed = transform_data(data)
    result = load_data(transformed)
    return result


if __name__ == "__main__":
    etl_pipeline()
"""
            
            flow_path = os.path.join(flows_dir, "etl_pipeline.py")
            with open(flow_path, 'w') as f:
                f.write(example_flow)
            
            # Create prefect.yaml deployment config
            prefect_config = """
# Prefect deployment configuration
name: {{ project_name }}
version: 1.0.0

# Work pool configuration
work_pool:
  name: default-agent-pool
  
# Storage for flow code
storage: local

# Schedule (optional)
# schedule:
#   interval: 3600  # Every hour
#   timezone: UTC
"""
            config_path = os.path.join(output_dir, "prefect.yaml")
            with open(config_path, 'w') as f:
                f.write(prefect_config)
                
        except Exception as e:
            print(f"Error generating Prefect flows: {e}")
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """Returns Docker service for Prefect server."""
        if not self.context:
            return {}
        
        port = self.context.get_service_port("prefect", 4200)
        
        return {
            "prefect-server": {
                "image": "prefecthq/prefect:2-python3.11",
                "ports": [f"{port}:4200"],
                "command": "prefect server start --host 0.0.0.0",
                "environment": {
                    "PREFECT_UI_URL": f"http://localhost:{port}/api",
                    "PREFECT_API_URL": f"http://localhost:{port}/api",
                    "PREFECT_SERVER_API_HOST": "0.0.0.0"
                },
                "volumes": ["prefect_data:/root/.prefect"]
            },
            "prefect-agent": {
                "image": "prefecthq/prefect:2-python3.11",
                "command": "prefect agent start -q default",
                "environment": {
                    "PREFECT_API_URL": "http://prefect-server:4200/api"
                },
                "volumes": [
                    "./flows:/flows",
                    "./data:/data"
                ],
                "depends_on": ["prefect-server"]
            }
        }
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """Returns environment variables for Prefect."""
        if not self.context:
            return {}
        
        port = self.context.get_service_port("prefect", 4200)
        
        return {
            "PREFECT_API_URL": f"http://localhost:{port}/api",
            "PREFECT_UI_URL": f"http://localhost:{port}"
        }
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        return {"prefect_data": None}


class DagsterGenerator(ComponentGenerator):
    """Generator for Dagster data orchestrator."""
    
    def __init__(self, env):
        super().__init__(env)
        self.context: Optional[ProjectContext] = None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """Generate Dagster project structure."""
        self.context = config.get("project_context")
        if not self.context:
            return
        
        # Create dagster project directory
        dagster_dir = os.path.join(output_dir, "dagster_project")
        os.makedirs(dagster_dir, exist_ok=True)
        
        try:
            # Create example Dagster pipeline
            pipeline_code = """
from dagster import asset, Definitions, AssetMaterialization
import pandas as pd


@asset(group_name="ingestion")
def raw_data():
    \"\"\"Extract raw data from source.\"\"\"
    # Simulated data extraction
    data = pd.DataFrame({
        'id': range(1, 101),
        'value': range(100, 200)
    })
    return data


@asset(group_name="transformation", deps=[raw_data])
def transformed_data(raw_data):
    \"\"\"Transform raw data.\"\"\"
    # Add transformations
    transformed = raw_data.copy()
    transformed['value_doubled'] = transformed['value'] * 2
    return transformed


@asset(group_name="analytics", deps=[transformed_data])
def analytics_output(transformed_data):
    \"\"\"Generate analytics output.\"\"\"
    summary = {
        'total_records': len(transformed_data),
        'avg_value': transformed_data['value'].mean()
    }
    return summary


# Define the Dagster job
defs = Definitions(
    assets=[raw_data, transformed_data, analytics_output],
)
"""
            
            pipeline_path = os.path.join(dagster_dir, "assets.py")
            with open(pipeline_path, 'w') as f:
                f.write(pipeline_code)
            
            # Create workspace.yaml
            workspace_config = """
load_from:
  - python_file: assets.py
"""
            workspace_path = os.path.join(dagster_dir, "workspace.yaml")
            with open(workspace_path, 'w') as f:
                f.write(workspace_config)
                
        except Exception as e:
            print(f"Error generating Dagster project: {e}")
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """Returns Docker services for Dagster."""
        if not self.context:
            return {}
        
        port = self.context.get_service_port("dagster", 3000)
        
        return {
            "dagster-webserver": {
                "image": "dagster/dagster-webserver:latest",
                "ports": [f"{port}:3000"],
                "environment": {
                    "DAGSTER_HOME": "/opt/dagster/dagster_home"
                },
                "volumes": [
                    "./dagster_project:/opt/dagster/app",
                    "dagster_home:/opt/dagster/dagster_home"
                ],
                "command": [
                    "dagster-webserver",
                    "-h", "0.0.0.0",
                    "-p", "3000",
                    "-w", "/opt/dagster/app/workspace.yaml"
                ]
            },
            "dagster-daemon": {
                "image": "dagster/dagster-daemon:latest",
                "environment": {
                    "DAGSTER_HOME": "/opt/dagster/dagster_home"
                },
                "volumes": [
                    "./dagster_project:/opt/dagster/app",
                    "dagster_home:/opt/dagster/dagster_home"
                ],
                "command": [
                    "dagster-daemon",
                    "run"
                ]
            }
        }
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """Returns environment variables for Dagster."""
        if not self.context:
            return {}
        
        port = self.context.get_service_port("dagster", 3000)
        
        return {
            "DAGSTER_HOME": "/opt/dagster/dagster_home",
            "DAGSTER_UI_URL": f"http://localhost:{port}"
        }
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        return {"dagster_home": None}


# Register providers
ProviderRegistry.register("orchestration", "Prefect", PrefectGenerator)
ProviderRegistry.register("orchestration", "Dagster", DagsterGenerator)
