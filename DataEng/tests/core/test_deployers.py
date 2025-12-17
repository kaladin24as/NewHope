"""
Tests for Cloud Deployers
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from core.deployers.base import CloudDeployer, Deployment Result, DeploymentStatus
from core.updater import ProjectMetadata


class MockCloudDeployer(CloudDeployer):
    """Mock deployer for testing"""
    
    def validate_credentials(self) -> bool:
        return True
    
    def deploy(self, **kwargs) -> DeploymentResult:
        return DeploymentResult(
            status=DeploymentStatus.SUCCESS,
            message="Mock deployment",
            endpoints={"app": "http://mock"},
            resources={"cluster": "mock-cluster"},
            errors=[]
        )
    
    def destroy(self) -> DeploymentResult:
        return DeploymentResult(
            status=DeploymentStatus.SUCCESS,
            message="Mock destroyed",
            endpoints={},
            resources={},
            errors=[]
        )
    
    def status(self) -> dict:
        return {"status": "running"}


class TestDeploymentResult:
    """Test DeploymentResult class"""
    
    def test_is_success_true(self):
        result = DeploymentResult(
            status=DeploymentStatus.SUCCESS,
            message="Success",
            endpoints={},
            resources={},
            errors=[]
        )
        assert result.is_success() is True
    
    def test_is_success_false(self):
        result = DeploymentResult(
            status=DeploymentStatus.FAILED,
            message="Failed",
            endpoints={},
            resources={},
            errors=["error1"]
        )
        assert result.is_success() is False


class TestCloudDeployer:
    """Test CloudDeployer base class"""
    
    @pytest.fixture
    def sample_project(self):
        """Create a sample project for testing"""
        from core.engine import TemplateEngine
        import uuid
        
        temp_dir = Path(tempfile.mkdtemp(prefix="deploy_test_"))
        
        # Generate project
        engine = TemplateEngine()
        stack = {"storage": "PostgreSQL"}
        vfs = engine.generate("test_project", stack, str(uuid.uuid4()))
        vfs.flush(str(temp_dir))
        
        yield temp_dir
        
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_init_valid_project(self, sample_project):
        """Test initialization with valid project"""
        deployer = MockCloudDeployer(sample_project, "prod")
        
        assert deployer.project_path == sample_project
        assert deployer.environment == "prod"
    
    def test_init_invalid_project(self):
        """Test initialization with invalid project"""
        with pytest.raises(FileNotFoundError):
            MockCloudDeployer(Path("/nonexistent/path"), "prod")
    
    def test_load_project_config(self, sample_project):
        """Test loading project configuration"""
        deployer = MockCloudDeployer(sample_project, "prod")
        
        config = deployer._load_project_config()
        
        assert "project" in config
        assert "antigravity" in config
        assert config["project"]["name"] == "test_project"
    
    def test_validate_credentials(self, sample_project):
        """Test credential validation"""
        deployer = MockCloudDeployer(sample_project, "prod")
        
        assert deployer.validate_credentials() is True
    
    def test_deploy(self, sample_project):
        """Test deployment"""
        deployer = MockCloudDeployer(sample_project, "prod")
        
        result = deployer.deploy()
        
        assert result.is_success()
        assert "app" in result.endpoints
    
    def test_destroy(self, sample_project):
        """Test resource destruction"""
        deployer = MockCloudDeployer(sample_project, "prod")
        
        result = deployer.destroy()
        
        assert result.is_success()
    
    def test_status(self, sample_project):
        """Test status check"""
        deployer = MockCloudDeployer(sample_project, "prod")
        
        status = deployer.status()
        
        assert status["status"] == "running"


class TestAWSDeployer:
    """Test AWS deployer (mocked)"""
    
    def test_import_aws_deployer(self):
        """Test importing AWS deployer"""
        try:
            from core.deployers.aws_deployer import AWSDeployer
            assert AWSDeployer is not None
        except ImportError as e:
            # boto3 might not be installed
            assert "boto3" in str(e)


class TestGCPDeployer:
    """Test GCP deployer (mocked)"""
    
    def test_import_gcp_deployer(self):
        """Test importing GCP deployer"""
        try:
            from core.deployers.gcp_deployer import GCPDeployer
            assert GCPDeployer is not None
        except ImportError as e:
            # google-cloud might not be installed
            assert "google" in str(e).lower()


class TestAzureDeployer:
    """Test Azure deployer (mocked)"""
    
    def test_import_azure_deployer(self):
        """Test importing Azure deployer"""
        try:
            from core.deployers.azure_deployer import AzureDeployer
            assert AzureDeployer is not None
        except ImportError as e:
            # azure-mgmt might not be installed
            assert "azure" in str(e).lower()
