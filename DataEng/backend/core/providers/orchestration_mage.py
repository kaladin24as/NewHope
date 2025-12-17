"""
Mage AI orchestration provider
"""
import os
from typing import Dict, Any, Optional
from core.interfaces import ComponentGenerator
from core.registry import ProviderRegistry
from core.manifest import ProjectContext


class MageAIGenerator(ComponentGenerator):
    """Generator for Mage AI modern data pipeline tool."""
    
    def __init__(self, env):
        super().__init__(env)
        self.context: Optional[ProjectContext] = None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """Generate Mage AI project structure."""
        self.context = config.get("project_context")
        if not self.context:
            return
        
        # Assign port
        self.context.get_service_port("mage", 6789)
        
        # Create mage project directory
        mage_dir = os.path.join(output_dir, "mage_project")
        os.makedirs(mage_dir, exist_ok=True)
        
        # Create pipelines directory
        pipelines_dir = os.path.join(mage_dir, "pipelines")
        os.makedirs(pipelines_dir, exist_ok=True)
        
        try:
            # Create example pipeline
            pipeline_config = """blocks:
- all_upstream_blocks_executed: true
  color: null
  configuration: {}
  downstream_blocks:
  - transform_data
  executor_config: null
  executor_type: local_python
  has_callback: false
  name: load_data
  retry_config: null
  status: executed
  timeout: null
  type: data_loader
  upstream_blocks: []
  uuid: load_data

- all_upstream_blocks_executed: true
  color: null
  configuration: {}
  downstream_blocks:
  - export_data
  executor_config: null
  executor_type: local_python
  has_callback: false
  name: transform_data
  retry_config: null
  status: executed
  timeout: null
  type: transformer
  upstream_blocks:
  - load_data
  uuid: transform_data

- all_upstream_blocks_executed: true
  color: null
  configuration: {}
  downstream_blocks: []
  executor_config: null
  executor_type: local_python
  has_callback: false
  name: export_data
  retry_config: null
  status: executed
  timeout: null
  type: data_exporter
  upstream_blocks:
  - transform_data
  uuid: export_data

name: etl_pipeline
type: python
uuid: etl_pipeline
"""
            
            with open(os.path.join(pipelines_dir, "etl_pipeline.yaml"), 'w') as f:
                f.write(pipeline_config)
            
            # Create data loader block
            loader_code = """import pandas as pd

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader

@data_loader
def load_data(*args, **kwargs):
    \"\"\"
    Load data from source.
    \"\"\"
    # Example: Load from CSV
    df = pd.DataFrame({
        'id': range(1, 101),
        'value': range(100, 200),
        'category': ['A', 'B', 'C', 'D', 'E'] * 20
    })
    
    print(f"Loaded {len(df)} records")
    return df
"""
            
            blocks_dir = os.path.join(pipelines_dir, "blocks")
            os.makedirs(blocks_dir, exist_ok=True)
            
            with open(os.path.join(blocks_dir, "load_data.py"), 'w') as f:
                f.write(loader_code)
            
            # Create transformer block
            transformer_code = """import pandas as pd

if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer

@transformer
def transform_data(data, *args, **kwargs):
    \"\"\"
    Transform the data.
    \"\"\"
    df = data.copy()
    
    # Add transformations
    df['value_doubled'] = df['value'] * 2
    df['value_normalized'] = (df['value'] - df['value'].mean()) / df['value'].std()
    
    # Filter
    df = df[df['value'] > 120]
    
    print(f"Transformed to {len(df)} records")
    return df
"""
            
            with open(os.path.join(blocks_dir, "transform_data.py"), 'w') as f:
                f.write(transformer_code)
            
            # Create exporter block
            exporter_code = """import pandas as pd

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter

@data_exporter
def export_data(data, *args, **kwargs):
    \"\"\"
    Export data to destination.
    \"\"\"
    # Example: Save to CSV
    output_path = '/mage_project/output/results.csv'
    data.to_csv(output_path, index=False)
    
    print(f"Exported {len(data)} records to {output_path}")
    return data
"""
            
            with open(os.path.join(blocks_dir, "export_data.py"), 'w') as f:
                f.write(exporter_code)
            
            # Create io_config.yaml for connections
            io_config = """version: 0.1.1
default:
  # PostgreSQL
  POSTGRES_CONNECT_TIMEOUT: 10
  POSTGRES_DBNAME: "{{ env_var('POSTGRES_DB') }}"
  POSTGRES_HOST: "{{ env_var('POSTGRES_HOST') }}"
  POSTGRES_PASSWORD: "{{ env_var('POSTGRES_PASSWORD') }}"
  POSTGRES_PORT: "{{ env_var('POSTGRES_PORT') }}"
  POSTGRES_USER: "{{ env_var('POSTGRES_USER') }}"
"""
            
            with open(os.path.join(mage_dir, "io_config.yaml"), 'w') as f:
                f.write(io_config)
                
        except Exception as e:
            print(f"Error generating Mage project: {e}")
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """Returns Docker service for Mage AI."""
        if not self.context:
            return {}
        
        port = self.context.get_service_port("mage", 6789)
        
        return {
            "mage": {
                "image": "mageai/mageai:latest",
                "ports": [f"{port}:6789"],
                "volumes": [
                    "./mage_project:/home/src/mage_project",
                    "./data:/home/src/data"
                ],
                "environment": {
                    "PROJECT_TYPE": "standalone",
                    "MAGE_DATABASE_CONNECTION_URL": "sqlite:////home/src/mage_project/mage.db"
                },
                "command": [
                    "mage",
                    "start",
                    "mage_project"
                ]
            }
        }
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """Returns environment variables for Mage AI."""
        if not self.context:
            return {}
        
        port = self.context.get_service_port("mage", 6789)
        
        return {
            "MAGE_UI_URL": f"http://localhost:{port}",
            "MAGE_PROJECT_TYPE": "standalone"
        }
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        return {}


# Register provider
ProviderRegistry.register("orchestration", "Mage", MageAIGenerator)
