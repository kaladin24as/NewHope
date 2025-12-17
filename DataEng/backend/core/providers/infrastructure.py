"""
Infrastructure as Code provider for Terraform generation.
"""
import os
from typing import Dict, Any
from core.interfaces import ComponentGenerator
from core.manifest import ProjectContext
from core.registry import ProviderRegistry


class TerraformGenerator(ComponentGenerator):
    """
    Generates Terraform configuration files for cloud infrastructure.
    Supports AWS and GCP providers based on stack configuration.
    """
    
    def generate(self, output_dir: str, config: Dict[str, Any]) -> None:
        """Generate Terraform configuration files"""
        context: ProjectContext = config.get("project_context")
        
        # Determine cloud provider from stack (could be explicit or inferred)
        cloud_provider = config.get("cloud_provider", "aws")  # default to AWS
        
        # Create terraform directory
        terraform_dir = os.path.join(output_dir, "terraform")
        os.makedirs(terraform_dir, exist_ok=True)
        
        # Render main.tf
        try:
            template = self.env.get_template("terraform/main.tf.j2")
            
            # Generate secure password for database
            db_password = context.get_or_create_secret("db_password", 32)
            
            content = template.render(
                project_name=context.project_name,
                cloud_provider=cloud_provider,
                db_password=db_password,
                db_user="admin",
                environment="dev",
                aws_region="us-east-1",
                gcp_region="us-central1",
                gcp_project_id=f"{context.project_name}-project"
            )
            
            with open(os.path.join(terraform_dir, "main.tf"), "w") as f:
                f.write(content)
                
            # Create variables.tf for better organization
            variables_tf = """variable "environment" {
  description = "Deployment environment (dev/staging/prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
}
"""
            with open(os.path.join(terraform_dir, "variables.tf"), "w") as f:
                f.write(variables_tf)
                
            # Create outputs.tf
            outputs_tf = """output "storage_bucket_name" {
  description = "Name of the created storage bucket"
  value       = aws_s3_bucket.data_lake.id
}

output "database_endpoint" {
  description = "Database connection endpoint"
  value       = aws_db_instance.metadata_db.endpoint
  sensitive   = true
}
"""
            with open(os.path.join(terraform_dir, "outputs.tf"), "w") as f:
                f.write(outputs_tf)
                
        except Exception as e:
            print(f"Error generating Terraform configuration: {e}")
    
    def get_docker_service_definition(self, context: ProjectContext) -> Dict[str, Any]:
        """
        Returns LocalStack service for local infrastructure testing.
        In production, this would not be needed (real cloud resources used).
        """
        return {
            "localstack": {
                "image": "localstack/localstack:latest",
                "environment": {
                    "SERVICES": "s3,rds",
                    "DEFAULT_REGION": "us-east-1",
                    "DATA_DIR": "/tmp/localstack/data"
                },
                "ports": [
                    "4566:4566"
                ],
                "volumes": [
                    "localstack-data:/tmp/localstack"
                ]
            }
        }
    
    def get_env_vars(self, context: ProjectContext) -> Dict[str, str]:
        """Returns environment variables needed for Terraform"""
        return {
            "AWS_ACCESS_KEY_ID": "your-aws-access-key",
            "AWS_SECRET_ACCESS_KEY": "your-aws-secret-key",
            "AWS_DEFAULT_REGION": "us-east-1",
            "TF_VAR_project_name": context.project_name,
            "TF_VAR_environment": "dev"
        }
    
    def get_requirements(self) -> list[str]:
        """Terraform doesn't need Python dependencies"""
        return []
    
    def get_docker_compose_volumes(self) -> Dict[str, Any]:
        """Returns Docker volumes for LocalStack"""
        return {
            "localstack-data": {}
        }


# Register the provider
ProviderRegistry.register("infrastructure", "terraform", TerraformGenerator)
