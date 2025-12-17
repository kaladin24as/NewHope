"""
Cloud Deployment Support - Base Classes
========================================

Foundation for deploying AntiGravity projects to cloud providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class DeploymentStatus(Enum):
    """Deployment status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLBACK = "rollback"


@dataclass
class DeploymentResult:
    """Result of a deployment operation"""
    status: Deployment Status
    message: str
    endpoints: Dict[str, str]
    resources: Dict[str, str]
    errors: List[str]
    
    def is_success(self) -> bool:
        return self.status == DeploymentStatus.SUCCESS


class CloudDeployer(ABC):
    """
    Abstract base class for cloud deployers.
    
    Each cloud provider (AWS, GCP, Azure) implements this interface.
    """
    
    def __init__(self, project_path: Path, environment: str = "prod"):
        """
        Initialize deployer.
        
        Args:
            project_path: Path to AntiGravity project
            environment: Target environment (dev/staging/prod)
        """
        self.project_path = Path(project_path)
        self.environment = environment
        
        if not self.project_path.exists():
            raise FileNotFoundError(f"Project not found: {project_path}")
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """Validate cloud credentials are configured"""
        pass
    
    @abstractmethod
    def deploy(self, **kwargs) -> DeploymentResult:
        """Deploy the project to cloud"""
        pass
    
    @abstractmethod
    def destroy(self) -> DeploymentResult:
        """Destroy deployed resources"""
        pass
    
    @abstractmethod
    def status(self) -> Dict:
        """Get deployment status"""
        pass
    
    def _load_project_config(self) -> Dict:
        """Load project configuration"""
        from core.updater import ProjectMetadata
        return ProjectMetadata.read(self.project_path)
