"""Tests for authentication and space operations."""
import pytest
from unittest.mock import patch, MagicMock

from anytype_client import AnytypeClient
from anytype_client.models import Space, AuthChallenge, APIKey
from anytype_client.exceptions import AuthenticationError, UnauthorizedError, APIError
from tests.conftest import assert_valid_id, assert_valid_timestamp


class TestAuthentication:
    """Test authentication-related functionality."""
    
    def test_client_initialization_with_api_key(self, api_key: str):
        """Test that client can be initialized with API key."""
        client = AnytypeClient(api_key=api_key)
        assert client.api_key == api_key
        assert client.base_url.endswith("/")
    
    def test_client_initialization_without_api_key(self):
        """Test that client raises error without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="API key is required"):
                AnytypeClient()
    
    def test_client_context_manager(self, api_key: str):
        """Test that client works as context manager."""
        with AnytypeClient(api_key=api_key) as client:
            assert client.api_key == api_key
    
    @pytest.mark.skip("Requires manual interaction - enable for manual testing")
    def test_create_auth_challenge(self, sync_client: AnytypeClient):
        """Test creating an authentication challenge."""
        challenge = sync_client.create_auth_challenge("Test App")
        assert isinstance(challenge, AuthChallenge)
        assert_valid_id(challenge.challenge_id)
        assert_valid_timestamp(challenge.expires_at)
    
    @pytest.mark.skip("Requires manual interaction - enable for manual testing")
    def test_create_api_key(self, sync_client: AnytypeClient):
        """Test creating an API key from challenge."""
        # This would require a real challenge and verification code
        # In practice, this should be tested manually
        pass


class TestSpaceOperations:
    """Test space-related operations."""
    
    def test_list_spaces(self, sync_client: AnytypeClient):
        """Test listing all spaces."""
        spaces = sync_client.list_spaces()
        assert isinstance(spaces, list)
        assert len(spaces) > 0
        
        for space in spaces:
            assert isinstance(space, Space)
            assert_valid_id(space.id)
            assert isinstance(space.name, str)
            assert len(space.name) > 0
    
    def test_get_specific_space(self, sync_client: AnytypeClient, test_space: Space):
        """Test getting a specific space by ID."""
        space = sync_client.get_space(test_space.id)
        assert isinstance(space, Space)
        assert space.id == test_space.id
        assert space.name == test_space.name
    
    def test_get_nonexistent_space(self, sync_client: AnytypeClient):
        """Test getting a space that doesn't exist."""
        with pytest.raises(APIError):
            sync_client.get_space("nonexistent-space-id")
    
    def test_test_space_exists(self, test_space: Space):
        """Test that our test space exists and has correct name."""
        assert test_space.name == "ClientTestSpace"
        assert_valid_id(test_space.id)
    
    def test_space_properties(self, test_space: Space):
        """Test that space has expected properties."""
        assert hasattr(test_space, 'name')
        assert hasattr(test_space, 'id')
        assert hasattr(test_space, 'description')
        assert hasattr(test_space, 'gateway_url')
        assert hasattr(test_space, 'network_id')
        
        # Test backward compatibility properties
        if hasattr(test_space, 'icon'):
            icon_emoji = test_space.icon_emoji
            icon_image = test_space.icon_image
            # These should be either None or valid values
            if icon_emoji:
                assert len(icon_emoji) <= 2  # Simple emoji check
            if icon_image:
                assert icon_image.startswith(('http://', 'https://'))


class TestErrorHandling:
    """Test error handling for authentication and space operations."""
    
    def test_invalid_api_key(self):
        """Test behavior with invalid API key."""
        with AnytypeClient(api_key="invalid-key") as client:
            with pytest.raises(UnauthorizedError):
                client.list_spaces()
    
    def test_network_timeout(self, api_key: str):
        """Test handling of network timeouts."""
        client = AnytypeClient(api_key=api_key, timeout=0.001)  # Very short timeout
        with client:
            with pytest.raises(APIError):
                client.list_spaces()
    
    def test_client_headers(self, sync_client: AnytypeClient):
        """Test that client sets correct headers."""
        headers = sync_client._get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
        assert "X-Anytype-Version" in headers
        assert headers["X-Anytype-Version"] == "2025-05-20"


class TestClientConfiguration:
    """Test client configuration options."""
    
    def test_custom_base_url(self, api_key: str):
        """Test client with custom base URL."""
        custom_url = "http://localhost:8080/api/v1/"
        client = AnytypeClient(api_key=api_key, base_url=custom_url)
        assert client.base_url == custom_url
    
    def test_custom_timeout(self, api_key: str):
        """Test client with custom timeout."""
        custom_timeout = 60.0
        client = AnytypeClient(api_key=api_key, timeout=custom_timeout)
        assert client.timeout == custom_timeout
    
    def test_additional_client_kwargs(self, api_key: str):
        """Test client with additional HTTP client arguments."""
        client = AnytypeClient(
            api_key=api_key,
            follow_redirects=True,
            verify=False
        )
        # The kwargs should be stored for later use
        assert "follow_redirects" in client._client_kwargs
        assert "verify" in client._client_kwargs