"""
Environment Manager
===================

Manages generation of environment-specific configuration files.
Generates .env files for dev, staging, and production environments.
"""

from typing import Dict, Optional, List
from pathlib import Path
from core.manifest import ProjectContext


class EnvironmentManager:
    """
    Generate environment-specific configuration files.
    
    Creates separate .env files for different deployment environments
    with appropriate settings for each.
    """
    
    ENVIRONMENTS = ["dev", "staging", "prod"]
    
    @staticmethod
    def generate_all_env_files(context: ProjectContext) -> Dict[str, str]:
        """
        Generate environment files for all environments.
        
        Args:
            context: Project context with base configuration
        
        Returns:
            Dict mapping environment names to file contents
        """
        env_files = {}
        
        # Generate for each environment
        env_files["dev"] = EnvironmentManager.generate_dev_env(context)
        env_files["staging"] = EnvironmentManager.generate_staging_env(context)
        env_files["prod"] = EnvironmentManager.generate_prod_env(context)
        env_files["example"] = EnvironmentManager.generate_example_env(context)
        
        return env_files
    
    @staticmethod
    def generate_dev_env(context: ProjectContext) -> str:
        """
        Generate development environment configuration.
        
        Dev environment assumptions:
        - Local Docker containers
        - Debug mode enabled
        - Verbose logging
        - Localhost networking
        """
        base_vars = context.get_env_vars()
        
        dev_vars = {
            **base_vars,
            "ENVIRONMENT": "dev",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG",
            "ENABLE_PROFILING": "true",
            
            # Override any cloud hostnames to local
            **{
                k: "localhost" if "HOST" in k and k not in ["POSTGRES_HOST", "MONGO_HOST"] else v
                for k, v in base_vars.items()
            }
        }
        
        # Add dev-specific comments
        header = [
            "# Development Environment Configuration",
            "# =====================================",
            "# This file is for LOCAL DEVELOPMENT with Docker Compose",
            "# All services run on localhost",
            "",
            "# NEVER commit this file with real credentials!",
            ""
        ]
        
        return EnvironmentManager._format_env(dev_vars, header)
    
    @staticmethod
    def generate_staging_env(context: ProjectContext) -> str:
        """
        Generate staging environment configuration.
        
        Staging environment assumptions:
        - Cloud-hosted services
        - Limited debug output
        - Uses secrets manager for sensitive data
        - Similar to production but with more monitoring
        """
        base_vars = context.get_env_vars()
        
        staging_vars = {
            **base_vars,
            "ENVIRONMENT": "staging",
            "DEBUG": "false",
            "LOG_LEVEL": "INFO",
            "USE_CLOUD_SECRETS": "true",
            "ENABLE_MONITORING": "true",
            
            # Use placeholders for cloud resources
            **{
                k: f"${{{k}}}" if "HOST" in k or "ENDPOINT" in k else v
                for k, v in base_vars.items()
                if k not in ["ENVIRONMENT", "DEBUG", "LOG_LEVEL"]
            }
        }
        
        header = [
            "# Staging Environment Configuration",
            "# ==================================",
            "# This file is for STAGING deployment",
            "# Secrets should be injected via AWS Secrets Manager or similar",
            "",
            "# Variables with ${...} syntax should be replaced by your CI/CD",
            "# or secrets management system",
            ""
        ]
        
        return EnvironmentManager._format_env(staging_vars, header)
    
    @staticmethod
    def generate_prod_env(context: ProjectContext) -> str:
        """
        Generate production environment configuration.
        
        Production environment assumptions:
        - Fully cloud-hosted
        - No debug output
        - Warning-level logging only
        - All secrets from secrets manager
        - Monitoring and alerting enabled
        """
        base_vars = context.get_env_vars()
        
        prod_vars = {
            **base_vars,
            "ENVIRONMENT": "prod",
            "DEBUG": "false",
            "LOG_LEVEL": "WARNING",
            "USE_CLOUD_SECRETS": "true",
            "ENABLE_MONITORING": "true",
            "ENABLE_ALERTING": "true",
            "ENABLE_BACKUP": "true",
            
            # Use environment variable placeholders
            **{
                k: f"${{{k}}}" if k.endswith(("PASSWORD", "SECRET", "KEY", "TOKEN")) else v
                for k, v in base_vars.items()
                if k not in ["ENVIRONMENT", "DEBUG", "LOG_LEVEL"]
            }
        }
        
        header = [
            "# Production Environment Configuration",
            "# =====================================",
            "# ⚠️  PRODUCTION ENVIRONMENT - HANDLE WITH CARE",
            "",
            "# ALL secrets MUST be managed via AWS Secrets Manager,",
            "# GCP Secret Manager, or Azure Key Vault",
            "",
            "# This file should ONLY contain non-sensitive configuration",
            "# Service endpoints and hostnames should be injected by infrastructure",
            ""
        ]
        
        return EnvironmentManager._format_env(prod_vars, header)
    
    @staticmethod
    def generate_example_env(context: ProjectContext) -> str:
        """
        Generate example .env file for documentation.
        
        This is the user-facing template that gets committed to Git.
        """
        base_vars = context.get_env_vars()
        
        # Replace sensitive values with CHANGE_ME
        example_vars = {
            k: "CHANGE_ME" if k.endswith(("PASSWORD", "SECRET", "KEY", "TOKEN")) else v
            for k, v in base_vars.items()
        }
        
        header = [
            "# Environment Variables Template",
            "# ===============================",
            "# Copy this file to .env and update with your values",
            "",
            "# For local development:",
            "#   cp .env.example .env.dev",
            "",
            "# For staging:",
            "#   cp .env.example .env.staging",
            "",
            "# For production:",
            "#   cp .env.example .env.prod",
            "",
            "# ⚠️  NEVER commit .env files with real credentials!",
            ""
        ]
        
        return EnvironmentManager._format_env(example_vars, header)
    
    @staticmethod
    def _format_env(vars_dict: Dict[str, str], header: Optional[List[str]] = None) -> str:
        """
        Format environment variables as KEY=VALUE lines.
        
        Args:
            vars_dict: Dictionary of environment variables
            header: Optional header comments
        
        Returns:
            Formatted .env file content
        """
        lines = []
        
        # Add header if provided
        if header:
            lines.extend(header)
        
        # Group variables by prefix for better organization
        grouped = {}
        for key, value in sorted(vars_dict.items()):
            prefix = key.split("_")[0] if "_" in key else "OTHER"
            if prefix not in grouped:
                grouped[prefix] = []
            grouped[prefix].append((key, value))
        
        # Write groups with separators
        for group_name, group_vars in sorted(grouped.items()):
            if group_name != "OTHER":
                lines.append(f"# {group_name.title()} Configuration")
                lines.append("")
            
            for key, value in group_vars:
                # Handle multi-line values
                if "\n" in str(value):
                    value = value.replace("\n", "\\n")
                
                lines.append(f"{key}={value}")
            
            lines.append("")  # Blank line between groups
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_env_switcher_script() -> str:
        """
        Generate a helper script for switching between environments.
        
        Returns:
            Shell script content
        """
        return """#!/bin/bash
# Environment Switcher
# ====================
# Switch between dev, staging, and prod environments

set -e

ENVIRONMENTS=("dev" "staging" "prod")

function show_usage() {
    echo "Usage: $0 <environment>"
    echo ""
    echo "Environments:"
    echo "  dev      - Local development"
    echo "  staging  - Staging environment"
    echo "  prod     - Production environment"
    echo ""
    echo "Example: $0 dev"
}

if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

ENV=$1

# Validate environment
if [[ ! " ${ENVIRONMENTS[@]} " =~ " ${ENV} " ]]; then
    echo "❌ Invalid environment: $ENV"
    show_usage
    exit 1
fi

# Check if env file exists
if [ ! -f ".env.$ENV" ]; then
    echo "❌ Environment file not found: .env.$ENV"
    exit 1
fi

# Backup current .env if it exists
if [ -f ".env" ]; then
    cp .env .env.backup
    echo "📦 Backed up current .env to .env.backup"
fi

# Switch environment
cp ".env.$ENV" .env
echo "✅ Switched to $ENV environment"
echo ""
echo "Active configuration: .env.$ENV"
echo "Services will use this environment on next start."
echo ""
echo "To apply changes:"
echo "  docker-compose down"
echo "  docker-compose up -d"
"""
    
    @staticmethod
    def generate_gitignore_additions() -> str:
        """
        Generate recommended .gitignore entries for env files.
        
        Returns:
            .gitignore content to append
        """
        return """
# Environment files (DO NOT COMMIT)
.env
.env.dev
.env.staging
.env.prod
.env.local
.env.backup

# Only commit the template
!.env.example
"""
    
    @staticmethod
    def get_environment_documentation() -> str:
        """
        Generate documentation about environment management.
        
        Returns:
            Markdown documentation
        """
        return """# Environment Management

This project supports multiple environments with separate configurations.

## Available Environments

### Development (`.env.dev`)
- Local Docker containers
- Debug mode enabled
- Verbose logging
- Use: `./scripts/switch-env.sh dev`

### Staging (`.env.staging`)
- Cloud-hosted services
- Production-like setup
- Uses secrets manager
- Use: `./scripts/switch-env.sh staging`

### Production (`.env.prod`)
- Full production configuration
- All secrets from secrets manager
- Monitoring and alerting enabled
- Use: `./scripts/switch-env.sh prod`

## Quick Start

1. **Copy example environment:**
   ```bash
   cp .env.example .env.dev
   ```

2. **Update with your values:**
   ```bash
   nano .env.dev
   ```

3. **Switch to environment:**
   ```bash
   ./scripts/switch-env.sh dev
   ```

4. **Start services:**
   ```bash
   docker-compose up -d
   ```

## Security Best Practices

- ✅ **NEVER** commit `.env`, `.env.dev`, `.env.staging`, or `.env.prod`
- ✅ **ONLY** commit `.env.example` with placeholder values
- ✅ Use secrets managers (AWS Secrets Manager, etc.) for production
- ✅ Rotate credentials regularly
- ✅ Use different credentials for each environment

## CI/CD Integration

In your CI/CD pipeline, inject environment variables via:
- **GitHub Actions:** Repository secrets
- **GitLab CI:** CI/CD variables
- **AWS:** Secrets Manager + Parameter Store
- **GCP:** Secret Manager
- **Azure:** Key Vault
"""
