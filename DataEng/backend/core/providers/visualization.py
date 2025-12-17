"""
BI and Visualization providers: Metabase, Superset, Grafana
"""
import os
from typing import Dict, Any, Optional
from core.interfaces import ComponentGenerator
from core.registry import ProviderRegistry
from core.manifest import ProjectContext


class MetabaseGenerator(ComponentGenerator):
    """Generator for Metabase BI tool."""
    
    def __init__(self, env):
        super().__init__(env)
        self.context: Optional[ProjectContext] = None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """Generate Metabase configuration."""
        self.context = config.get("project_context")
        if not self.context:
            return
        
        # Assign port
        self.context.get_service_port("metabase", 3000)
        
        # Create metabase directory
        mb_dir = os.path.join(output_dir, "metabase")
        os.makedirs(mb_dir, exist_ok=True)
        
        try:
            # Create setup guide
            readme = """# Metabase Setup

## Quick Start

1. Start Metabase:
   ```bash
   docker-compose up metabase
   ```

2. Access UI: http://localhost:3000

3. Initial Setup:
   - Create admin account
   - Add database connection
   - Start creating dashboards

## Connect to Data Warehouse

### PostgreSQL
- Host: `postgres`
- Port: `5432`
- Database: `warehouse`
- User: `postgres`
- Password: (check .env file)

### Snowflake
- Account: YOUR_ACCOUNT
- Database: ANALYTICS
- Warehouse: COMPUTE_WH

## Features
- Self-service analytics
- SQL editor
- Interactive dashboards
- Automated reports
- Email scheduling

## Documentation
https://www.metabase.com/docs/latest/
"""
            
            with open(os.path.join(mb_dir, "README.md"), 'w') as f:
                f.write(readme)
                
        except Exception as e:
            print(f"Error generating Metabase setup: {e}")
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """Returns Docker service for Metabase."""
        if not self.context:
            return {}
        
        port = self.context.get_service_port("metabase", 3000)
        
        return {
            "metabase": {
                "image": "metabase/metabase:latest",
                "ports": [f"{port}:3000"],
                "environment": {
                    "MB_DB_TYPE": "postgres",
                    "MB_DB_DBNAME": "metabase",
                    "MB_DB_PORT": "5432",
                    "MB_DB_USER": "metabase",
                    "MB_DB_PASS": "metabase",
                    "MB_DB_HOST": "metabase-db"
                },
                "volumes": ["metabase_data:/metabase-data"],
                "depends_on": ["metabase-db"]
            },
            "metabase-db": {
                "image": "postgres:15",
                "environment": {
                    "POSTGRES_DB": "metabase",
                    "POSTGRES_USER": "metabase",
                    "POSTGRES_PASSWORD": "metabase"
                },
                "volumes": ["metabase_db:/var/lib/postgresql/data"]
            }
        }
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """Returns environment variables for Metabase."""
        if not self.context:
            return {}
        
        port = self.context.get_service_port("metabase", 3000)
        
        return {
            "METABASE_URL": f"http://localhost:{port}"
        }
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        return {
            "metabase_data": None,
            "metabase_db": None
        }


class SupersetGenerator(ComponentGenerator):
    """Generator for Apache Superset BI platform."""
    
    def __init__(self, env):
        super().__init__(env)
        self.context: Optional[ProjectContext] = None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """Generate Superset configuration."""
        self.context = config.get("project_context")
        if not self.context:
            return
        
        # Assign port
        self.context.get_service_port("superset", 8088)
        
        # Create superset directory
        ss_dir = os.path.join(output_dir, "superset")
        os.makedirs(ss_dir, exist_ok=True)
        
        try:
            # Create initialization script
            init_script = """#!/bin/bash
# Superset initialization script

# Create admin user
superset fab create-admin \\
    --username admin \\
    --firstname Admin \\
    --lastname User \\
    --email admin@example.com \\
    --password admin

# Initialize database
superset db upgrade

# Load examples (optional)
# superset load_examples

# Create default roles
superset init

echo "Superset initialized successfully!"
"""
            
            with open(os.path.join(ss_dir, "init_superset.sh"), 'w') as f:
                f.write(init_script)
                
        except Exception as e:
            print(f"Error generating Superset setup: {e}")
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """Returns Docker service for Superset."""
        if not self.context:
            return {}
        
        port = self.context.get_service_port("superset", 8088)
        
        return {
            "superset": {
                "image": "apache/superset:latest",
                "ports": [f"{port}:8088"],
                "environment": {
                    "SUPERSET_SECRET_KEY": "your-secret-key-here",
                    "SUPERSET_CONFIG_PATH": "/app/superset_config.py"
                },
                "volumes": [
                    "superset_data:/app/superset_home",
                    "./superset/init_superset.sh:/app/docker/init.sh"
                ],
                "command": ["/bin/sh", "-c", "/app/docker/init.sh && gunicorn -b 0.0.0.0:8088 superset.app:create_app()"]
            }
        }
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """Returns environment variables for Superset."""
        if not self.context:
            return {}
        
        port = self.context.get_service_port("superset", 8088)
        
        return {
            "SUPERSET_URL": f"http://localhost:{port}",
            "SUPERSET_USERNAME": "admin",
            "SUPERSET_PASSWORD": "admin"
        }
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        return {"superset_data": None}


class GrafanaGenerator(ComponentGenerator):
    """Generator for Grafana (primarily for data visualization)."""
    
    def __init__(self, env):
        super().__init__(env)
        self.context: Optional[ProjectContext] = None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """Generate Grafana configuration."""
        self.context = config.get("project_context")
        if not self.context:
            return
        
        # Assign port
        self.context.get_service_port("grafana", 3001)
        
        # Create grafana directory
        grafana_dir = os.path.join(output_dir, "grafana")
        os.makedirs(grafana_dir, exist_ok=True)
        dashboards_dir = os.path.join(grafana_dir, "dashboards")
        os.makedirs(dashboards_dir, exist_ok=True)
        
        try:
            # Create datasource configuration
            datasource_config = """apiVersion: 1

datasources:
  - name: PostgreSQL
    type: postgres
    url: postgres:5432
    database: warehouse
    user: postgres
    secureJsonData:
      password: 'password'
    jsonData:
      sslmode: 'disable'
      postgresVersion: 1500
"""
            
            with open(os.path.join(grafana_dir, "datasources.yml"), 'w') as f:
                f.write(datasource_config)
            
            # Create dashboard provisioning config
            dashboard_config = """apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /etc/grafana/dashboards
"""
            
            with open(os.path.join(grafana_dir, "dashboards.yml"), 'w') as f:
                f.write(dashboard_config)
                
        except Exception as e:
            print(f"Error generating Grafana setup: {e}")
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """Returns Docker service for Grafana."""
        if not self.context:
            return {}
        
        port = self.context.get_service_port("grafana", 3001)
        
        return {
            "grafana": {
                "image": "grafana/grafana:latest",
                "ports": [f"{port}:3000"],
                "environment": {
                    "GF_SECURITY_ADMIN_USER": "admin",
                    "GF_SECURITY_ADMIN_PASSWORD": "admin",
                    "GF_INSTALL_PLUGINS": "grafana-piechart-panel"
                },
                "volumes": [
                    "grafana_data:/var/lib/grafana",
                    "./grafana/datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml",
                    "./grafana/dashboards.yml:/etc/grafana/provisioning/dashboards/dashboards.yml",
                    "./grafana/dashboards:/etc/grafana/dashboards"
                ]
            }
        }
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """Returns environment variables for Grafana."""
        if not self.context:
            return {}
        
        port = self.context.get_service_port("grafana", 3001)
        
        return {
            "GRAFANA_URL": f"http://localhost:{port}",
            "GRAFANA_USERNAME": "admin",
            "GRAFANA_PASSWORD": "admin"
        }
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        return {"grafana_data": None}


# Register providers
ProviderRegistry.register("visualization", "Metabase", MetabaseGenerator)
ProviderRegistry.register("visualization", "Superset", SupersetGenerator)
ProviderRegistry.register("visualization", "Grafana", GrafanaGenerator)
