"""
Authentication Strategies for Data Source Connectors

Implements various authentication patterns using the Strategy design pattern.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os


class AuthStrategy(ABC):
    """
    Abstract base class for authentication strategies.
    """
    
    @abstractmethod
    def get_auth_type(self) -> str:
        """Returns the authentication type identifier"""
        pass
    
    @abstractmethod
    def apply_auth(self, config: Dict[str, Any], env_prefix: str = "") -> Dict[str, Any]:
        """
        Apply authentication to a request configuration.
        
        Args:
            config: Request configuration (headers, params, etc.)
            env_prefix: Prefix for environment variable lookup
        
        Returns:
            Updated configuration with authentication applied
        """
        pass
    
    @abstractmethod
    def get_required_env_vars(self, env_prefix: str = "") -> Dict[str, str]:
        """
        Get required environment variables for this auth strategy.
        
        Args:
            env_prefix: Prefix for environment variable names
        
        Returns:
            Dictionary of env var names and their descriptions
        """
        pass
    
    def validate_config(self, env_prefix: str = "") -> tuple[bool, Optional[str]]:
        """
        Validate that required environment variables are set.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        required_vars = self.get_required_env_vars(env_prefix)
        missing = []
        
        for var_name in required_vars.keys():
            if not os.getenv(var_name):
                missing.append(var_name)
        
        if missing:
            return (False, f"Missing required environment variables: {', '.join(missing)}")
        
        return (True, None)


class NoAuth(AuthStrategy):
    """No authentication required"""
    
    def get_auth_type(self) -> str:
        return "none"
    
    def apply_auth(self, config: Dict[str, Any], env_prefix: str = "") -> Dict[str, Any]:
        return config
    
    def get_required_env_vars(self, env_prefix: str = "") -> Dict[str, str]:
        return {}


class APIKeyAuth(AuthStrategy):
    """
    API Key authentication (header or query parameter).
    """
    
    def __init__(self, location: str = "header", key_name: str = "X-API-Key"):
        """
        Args:
            location: Where to place the key - "header" or "query"
            key_name: Name of the header or query parameter
        """
        self.location = location
        self.key_name = key_name
    
    def get_auth_type(self) -> str:
        return "api_key"
    
    def apply_auth(self, config: Dict[str, Any], env_prefix: str = "") -> Dict[str, Any]:
        api_key = os.getenv(f"{env_prefix}API_KEY")
        
        if not api_key:
            raise ValueError(f"Missing environment variable: {env_prefix}API_KEY")
        
        if self.location == "header":
            if "headers" not in config:
                config["headers"] = {}
            config["headers"][self.key_name] = api_key
        elif self.location == "query":
            if "params" not in config:
                config["params"] = {}
            config["params"][self.key_name] = api_key
        
        return config
    
    def get_required_env_vars(self, env_prefix: str = "") -> Dict[str, str]:
        return {
            f"{env_prefix}API_KEY": f"API key for authentication (placed in {self.location}: {self.key_name})"
        }


class BearerTokenAuth(AuthStrategy):
    """
    Bearer token authentication (typically JWT).
    """
    
    def get_auth_type(self) -> str:
        return "bearer"
    
    def apply_auth(self, config: Dict[str, Any], env_prefix: str = "") -> Dict[str, Any]:
        token = os.getenv(f"{env_prefix}API_TOKEN")
        
        if not token:
            raise ValueError(f"Missing environment variable: {env_prefix}API_TOKEN")
        
        if "headers" not in config:
            config["headers"] = {}
        
        config["headers"]["Authorization"] = f"Bearer {token}"
        
        return config
    
    def get_required_env_vars(self, env_prefix: str = "") -> Dict[str, str]:
        return {
            f"{env_prefix}API_TOKEN": "Bearer token for authentication"
        }


class BasicAuth(AuthStrategy):
    """
    HTTP Basic Authentication.
    """
    
    def get_auth_type(self) -> str:
        return "basic"
    
    def apply_auth(self, config: Dict[str, Any], env_prefix: str = "") -> Dict[str, Any]:
        username = os.getenv(f"{env_prefix}USERNAME")
        password = os.getenv(f"{env_prefix}PASSWORD")
        
        if not username or not password:
            raise ValueError(f"Missing environment variables: {env_prefix}USERNAME and/or {env_prefix}PASSWORD")
        
        # For requests library, we can use auth tuple
        config["auth"] = (username, password)
        
        return config
    
    def get_required_env_vars(self, env_prefix: str = "") -> Dict[str, str]:
        return {
            f"{env_prefix}USERNAME": "Username for basic authentication",
            f"{env_prefix}PASSWORD": "Password for basic authentication"
        }


class OAuth2Auth(AuthStrategy):
    """
    OAuth 2.0 Client Credentials flow.
    """
    
    def __init__(self, token_url: str):
        """
        Args:
            token_url: URL to obtain access token
        """
        self.token_url = token_url
        self._cached_token: Optional[str] = None
    
    def get_auth_type(self) -> str:
        return "oauth2"
    
    def _obtain_token(self, client_id: str, client_secret: str) -> str:
        """
        Obtain access token using client credentials flow.
        
        Note: This is a simplified implementation. In production, you'd want:
        - Token caching with expiration
        - Refresh token support
        - Better error handling
        """
        import requests
        
        response = requests.post(
            self.token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret
            },
            timeout=30
        )
        
        response.raise_for_status()
        token_data = response.json()
        
        return token_data.get("access_token")
    
    def apply_auth(self, config: Dict[str, Any], env_prefix: str = "") -> Dict[str, Any]:
        client_id = os.getenv(f"{env_prefix}CLIENT_ID")
        client_secret = os.getenv(f"{env_prefix}CLIENT_SECRET")
        
        if not client_id or not client_secret:
            raise ValueError(f"Missing environment variables: {env_prefix}CLIENT_ID and/or {env_prefix}CLIENT_SECRET")
        
        # Obtain token (in production, cache this)
        if not self._cached_token:
            self._cached_token = self._obtain_token(client_id, client_secret)
        
        if "headers" not in config:
            config["headers"] = {}
        
        config["headers"]["Authorization"] = f"Bearer {self._cached_token}"
        
        return config
    
    def get_required_env_vars(self, env_prefix: str = "") -> Dict[str, str]:
        return {
            f"{env_prefix}CLIENT_ID": "OAuth2 client ID",
            f"{env_prefix}CLIENT_SECRET": "OAuth2 client secret"
        }
