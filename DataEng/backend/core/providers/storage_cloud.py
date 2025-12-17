"""
Additional storage providers: BigQuery, Redshift, MongoDB
"""
import os
import json
from typing import Dict, Any, Optional
from core.interfaces import ComponentGenerator
from core.registry import ProviderRegistry
from core.manifest import ProjectContext


class BigQueryGenerator(ComponentGenerator):
    """Generator for Google BigQuery data warehouse."""
    
    def __init__(self, env):
        super().__init__(env)
        self.context: Optional[ProjectContext] = None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """Generate BigQuery configuration files."""
        self.context = config.get("project_context")
        if not self.context:
            return
        
        # Create bigquery config directory
        bq_dir = os.path.join(output_dir, "config", "bigquery")
        os.makedirs(bq_dir, exist_ok=True)
        
        try:
            # Create service account key template (user needs to replace)
            service_account_template = {
                "type": "service_account",
                "project_id": "YOUR_PROJECT_ID",
                "private_key_id": "YOUR_PRIVATE_KEY_ID",
                "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
                "client_email": "YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com",
                "client_id": "YOUR_CLIENT_ID",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
            }
            
            key_path = os.path.join(bq_dir, "service-account-key.json.template")
            with open(key_path, 'w') as f:
                json.dump(service_account_template, f, indent=2)
            
            # Create README with setup instructions
            readme = """# BigQuery Setup

## Prerequisites
1. Google Cloud Project with BigQuery API enabled
2. Service Account with BigQuery permissions
3. Downloaded service account JSON key

## Setup Instructions

1. **Create Service Account:**
   ```bash
   gcloud iam service-accounts create bigquery-service-account \\
     --display-name="BigQuery Service Account"
   ```

2. **Grant Permissions:**
   ```bash
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \\
     --member="serviceAccount:bigquery-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com" \\
     --role="roles/bigquery.admin"
   ```

3. **Download Key:**
   ```bash
   gcloud iam service-accounts keys create service-account-key.json \\
     --iam-account=bigquery-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

4. **Set Environment Variable:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="config/bigquery/service-account-key.json"
   ```

## Usage with dbt
Your dbt profiles.yml will use this service account automatically.

## Documentation
https://cloud.google.com/bigquery/docs
"""
            with open(os.path.join(bq_dir, "README.md"), 'w') as f:
                f.write(readme)
                
        except Exception as e:
            print(f"Error generating BigQuery config: {e}")
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """BigQuery is cloud-based, no Docker service needed."""
        return {}
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """Returns environment variables for BigQuery."""
        return {
            "GOOGLE_APPLICATION_CREDENTIALS": "/config/bigquery/service-account-key.json",
            "GOOGLE_CLOUD_PROJECT": "YOUR_PROJECT_ID",
            "BIGQUERY_DATASET": "analytics",
            "BIGQUERY_LOCATION": "US"
        }
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        return {}


class RedshiftGenerator(ComponentGenerator):
    """Generator for Amazon Redshift data warehouse."""
    
    def __init__(self, env):
        super().__init__(env)
        self.context: Optional[ProjectContext] = None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """Generate Redshift configuration files."""
        self.context = config.get("project_context")
        if not self.context:
            return
        
        # Generate secret for password
        self.context.get_or_create_secret("redshift_password")
        
        # Create redshift config directory
        rs_dir = os.path.join(output_dir, "config", "redshift")
        os.makedirs(rs_dir, exist_ok=True)
        
        try:
            # Create connection config
            connection_config = f"""# Redshift Connection Configuration

host: YOUR_CLUSTER.REGION.redshift.amazonaws.com
port: 5439
database: analytics
user: admin
password: {self.context.get_or_create_secret("redshift_password")}
schema: public

# SSL Configuration
sslmode: require

# Connection Pool Settings
min_pool_size: 1
max_pool_size: 10
"""
            
            config_path = os.path.join(rs_dir, "connection.conf")
            with open(config_path, 'w') as f:
                f.write(connection_config)
                
        except Exception as e:
            print(f"Error generating Redshift config: {e}")
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """Redshift is cloud-based, no Docker service needed."""
        return {}
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """Returns environment variables for Redshift."""
        if not self.context:
            return {}
        
        password = self.context.get_or_create_secret("redshift_password")
        
        return {
            "REDSHIFT_HOST": "YOUR_CLUSTER.REGION.redshift.amazonaws.com",
            "REDSHIFT_PORT": "5439",
            "REDSHIFT_DATABASE": "analytics",
            "REDSHIFT_USER": "admin",
            "REDSHIFT_PASSWORD": password,
            "REDSHIFT_SCHEMA": "public"
        }
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        return {}


class MongoDBGenerator(ComponentGenerator):
    """Generator for MongoDB NoSQL database."""
    
    def __init__(self, env):
        super().__init__(env)
        self.context: Optional[ProjectContext] = None
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """Generate MongoDB initialization scripts."""
        self.context = config.get("project_context")
        if not self.context:
            return
        
        # Generate secrets
        self.context.get_or_create_secret("mongo_root_password")
        self.context.get_or_create_secret("mongo_user_password")
        self.context.get_service_port("mongodb", 27017)
        
        # Create init script directory
        mongo_dir = os.path.join(output_dir, "config", "mongodb")
        os.makedirs(mongo_dir, exist_ok=True)
        
        try:
            # Create initialization script
            init_script = """// MongoDB Initialization Script

// Switch to analytics database
db = db.getSiblingDB('analytics');

// Create collections
db.createCollection('raw_data');
db.createCollection('processed_data');
db.createCollection('metadata');

// Create indexes
db.raw_data.createIndex({ "timestamp": 1 });
db.processed_data.createIndex({ "id": 1 }, { unique: true });

print('MongoDB initialization complete!');
"""
            
            script_path = os.path.join(mongo_dir, "init-mongo.js")
            with open(script_path, 'w') as f:
                f.write(init_script)
                
        except Exception as e:
            print(f"Error generating MongoDB init script: {e}")
    
    def get_docker_service_definition(self, context: Any) -> Dict[str, Any]:
        """Returns Docker service for MongoDB."""
        if not self.context:
            return {}
        
        port = self.context.get_service_port("mongodb", 27017)
        root_password = self.context.get_or_create_secret("mongo_root_password")
        user_password = self.context.get_or_create_secret("mongo_user_password")
        
        return {
            "mongodb": {
                "image": "mongo:7",
                "ports": [f"{port}:27017"],
                "environment": {
                    "MONGO_INITDB_ROOT_USERNAME": "root",
                    "MONGO_INITDB_ROOT_PASSWORD": root_password,
                    "MONGO_INITDB_DATABASE": "analytics"
                },
                "volumes": [
                    "mongodb_data:/data/db",
                    "./config/mongodb/init-mongo.js:/docker-entrypoint-initdb.d/init-mongo.js:ro"
                ]
            }
        }
    
    def get_env_vars(self, context: Any) -> Dict[str, str]:
        """Returns environment variables for MongoDB."""
        if not self.context:
            return {}
        
        port = self.context.get_service_port("mongodb", 27017)
        root_password = self.context.get_or_create_secret("mongo_root_password")
        
        return {
            "MONGO_HOST": "mongodb",
            "MONGO_PORT": str(port),
            "MONGO_DATABASE": "analytics",
            "MONGO_USERNAME": "root",
            "MONGO_PASSWORD": root_password,
            "MONGO_CONNECTION_STRING": f"mongodb://root:{root_password}@mongodb:{port}/analytics"
        }
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        return {"mongodb_data": None}


# Register providers
ProviderRegistry.register("storage", "BigQuery", BigQueryGenerator)
ProviderRegistry.register("storage", "Redshift", RedshiftGenerator)
ProviderRegistry.register("storage", "MongoDB", MongoDBGenerator)
