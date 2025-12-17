"""
Tests for core.manifest module (ProjectContext).
"""

import pytest
from core.manifest import ProjectContext, ServiceConnection


class TestServiceConnection:
    """Tests for ServiceConnection model."""
    
    @pytest.mark.unit
    def test_service_connection_creation(self):
        """Test creating a ServiceConnection."""
        conn = ServiceConnection(
            name="postgres_prod",
            type="postgres",
            host="localhost",
            port=5432,
            env_prefix="DB_PROD_"
        )
        
        assert conn.name == "postgres_prod"
        assert conn.type == "postgres"
        assert conn.host == "localhost"
        assert conn.port == 5432
        assert conn.env_prefix == "DB_PROD_"
    
    @pytest.mark.unit
    def test_service_connection_with_extra(self):
        """Test ServiceConnection with extra fields."""
        conn = ServiceConnection(
            name="s3_data",
            type="s3",
            env_prefix="S3_",
            extra={"bucket": "my-bucket", "region": "us-east-1"}
        )
        
        assert conn.extra["bucket"] == "my-bucket"
        assert conn.extra["region"] == "us-east-1"


class TestProjectContext:
    """Tests for ProjectContext class."""
    
    @pytest.mark.unit
    def test_initialization(self, sample_stack):
        """Test ProjectContext initialization."""
        context = ProjectContext(
            project_name="test_project",
            stack=sample_stack
        )
        
        assert context.project_name == "test_project"
        assert context.stack == sample_stack
        assert len(context.base_ports) == 0
        assert len(context.generated_secrets) == 0
        assert len(context.connections) == 0
    
    @pytest.mark.unit
    def test_get_or_create_secret_creates_new(self):
        """Test that get_or_create_secret generates a new secret."""
        context = ProjectContext(project_name="test", stack={})
        
        secret = context.get_or_create_secret("db_password")
        
        assert secret is not None
        assert len(secret) > 0
        assert "db_password" in context.generated_secrets
    
    @pytest.mark.unit
    def test_get_or_create_secret_returns_existing(self):
        """Test that get_or_create_secret returns existing secret."""
        context = ProjectContext(project_name="test", stack={})
        
        secret1 = context.get_or_create_secret("db_password")
        secret2 = context.get_or_create_secret("db_password")
        
        assert secret1 == secret2
    
    @pytest.mark.unit
    def test_get_or_create_secret_custom_length(self):
        """Test secret generation with custom length."""
        context = ProjectContext(project_name="test", stack={})
        
        secret = context.get_or_create_secret("api_key", length=32)
        
        # URL-safe base64 encoded secrets are longer than input length
        assert len(secret) >= 32
    
    @pytest.mark.unit
    def test_get_service_port_assigns_default(self):
        """Test that get_service_port assigns default port."""
        context = ProjectContext(project_name="test", stack={})
        
        port = context.get_service_port("postgres", 5432)
        
        assert port == 5432
        assert context.base_ports["postgres"] == 5432
    
    @pytest.mark.unit
    def test_get_service_port_returns_existing(self):
        """Test that get_service_port returns existing assignment."""
        context = ProjectContext(project_name="test", stack={})
        
        port1 = context.get_service_port("postgres", 5432)
        port2 = context.get_service_port("postgres", 9999)  # Different default
        
        assert port1 == port2 == 5432  # Should return original
    
    @pytest.mark.unit
    def test_register_connection(self):
        """Test registering a service connection."""
        context = ProjectContext(project_name="test", stack={})
        
        conn = ServiceConnection(
            name="db_main",
            type="postgres",
            host="postgres",
            port=5432,
            env_prefix="DB_"
        )
        
        context.register_connection(conn)
        
        assert len(context.connections) == 1
        assert context.connections[0].name == "db_main"
    
    @pytest.mark.unit
    def test_get_connection(self):
        """Test retrieving a connection by name."""
        context = ProjectContext(project_name="test", stack={})
        
        conn = ServiceConnection(
            name="cache",
            type="redis",
            env_prefix="CACHE_"
        )
        context.register_connection(conn)
        
        retrieved = context.get_connection("cache")
        
        assert retrieved is not None
        assert retrieved.name == "cache"
        assert retrieved.type == "redis"
    
    @pytest.mark.unit
    def test_get_connection_not_found(self):
        """Test that get_connection returns None for non-existent connection."""
        context = ProjectContext(project_name="test", stack={})
        
        retrieved = context.get_connection("nonexistent")
        
        assert retrieved is None
    
    @pytest.mark.unit
    def test_get_connections_by_type(self):
        """Test retrieving connections by type."""
        context = ProjectContext(project_name="test", stack={})
        
        conn1 = ServiceConnection(name="db1", type="postgres", env_prefix="DB1_")
        conn2 = ServiceConnection(name="db2", type="postgres", env_prefix="DB2_")
        conn3 = ServiceConnection(name="cache", type="redis", env_prefix="CACHE_")
        
        context.register_connection(conn1)
        context.register_connection(conn2)
        context.register_connection(conn3)
        
        postgres_conns = context.get_connections_by_type("postgres")
        
        assert len(postgres_conns) == 2
        assert all(c.type == "postgres" for c in postgres_conns)
    
    @pytest.mark.unit
    def test_get_env_vars(self):
        """Test environment variable generation from connections."""
        context = ProjectContext(project_name="test", stack={})
        
        conn = ServiceConnection(
            name="db",
            type="postgres",
            host="localhost",
            port=5432,
            env_prefix="DB_",
            extra={"user": "admin", "database": "mydb"}
        )
        context.register_connection(conn)
        
        env_vars = context.get_env_vars()
        
        assert env_vars["DB_HOST"] == "localhost"
        assert env_vars["DB_PORT"] == "5432"
        assert env_vars["DB_TYPE"] == "postgres"
        assert env_vars["DB_USER"] == "admin"
        assert env_vars["DB_DATABASE"] == "mydb"
    
    @pytest.mark.unit
    def test_multiple_secrets_unique(self):
        """Test that multiple secrets are unique."""
        context = ProjectContext(project_name="test", stack={})
        
        secret1 = context.get_or_create_secret("password1")
        secret2 = context.get_or_create_secret("password2")
        secret3 = context.get_or_create_secret("password3")
        
        assert secret1 != secret2 != secret3
        assert len(context.generated_secrets) == 3
