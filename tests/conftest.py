"""Pytest configuration and shared fixtures for Anytype client tests."""
import os
import pytest
import asyncio
from typing import Optional, Generator, AsyncGenerator
from dotenv import load_dotenv

from anytype_client import AnytypeClient, AsyncAnytypeClient
from anytype_client.models import Space, PaginationParams, RelationFormat

# Load environment variables from .env file
load_dotenv()

# Test configuration
TEST_SPACE_NAME = "ClientTestSpace"
API_KEY = os.getenv("ANYTYPE_API_KEY")

if not API_KEY:
    pytest.skip("ANYTYPE_API_KEY environment variable not set", allow_module_level=True)


@pytest.fixture(scope="session")
def api_key() -> str:
    """Provide the API key for tests."""
    return API_KEY


@pytest.fixture(scope="session")
def sync_client(api_key: str) -> Generator[AnytypeClient, None, None]:
    """Provide a synchronous Anytype client."""
    with AnytypeClient(api_key=api_key) as client:
        yield client


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def async_client(api_key: str) -> AsyncGenerator[AsyncAnytypeClient, None]:
    """Provide an asynchronous Anytype client."""
    async with AsyncAnytypeClient(api_key=api_key) as client:
        yield client


@pytest.fixture(scope="session")
def test_space(sync_client: AnytypeClient) -> Space:
    """Find or create the ClientTestSpace for all tests."""
    spaces = sync_client.list_spaces()
    
    # Look for existing test space
    for space in spaces:
        if space.name == TEST_SPACE_NAME:
            print(f"✅ Using existing test space: {TEST_SPACE_NAME}")
            return space
    
    # If no test space found, create it
    print(f"📝 Test space '{TEST_SPACE_NAME}' not found, creating it...")
    
    try:
        created_space = create_test_space(sync_client, TEST_SPACE_NAME)
        print(f"✅ Created test space: {TEST_SPACE_NAME}")
        
        # Set up the test environment in the new space
        setup_test_environment(sync_client, created_space.id)
        
        return created_space
        
    except Exception as e:
        print(f"❌ Failed to create test space '{TEST_SPACE_NAME}': {e}")
        pytest.skip(f"Could not create required test space '{TEST_SPACE_NAME}': {e}")


@pytest.fixture(scope="session")
def test_space_id(test_space: Space) -> str:
    """Provide the test space ID."""
    return test_space.id


@pytest.fixture
def pagination_params() -> PaginationParams:
    """Provide default pagination parameters for list operations."""
    return PaginationParams(limit=10, offset=0, sort_by="name", sort_direction="asc")


# Test data factories
@pytest.fixture
def test_object_data(test_space_id: str) -> dict:
    """Provide test data for object creation."""
    return {
        "name": "Test Object",
        "type_key": "page",  # Use 'page' since we confirmed it works
        "space_id": test_space_id
        # Remove properties and layout for now to test minimal case
    }


@pytest.fixture
def test_list_data(test_space_id: str) -> dict:
    """Provide test data for list creation."""
    return {
        "name": "Test List",
        "description": "Test list created by the test suite",
        "space_id": test_space_id
    }


@pytest.fixture
def test_tag_data(test_space_id: str) -> dict:
    """Provide test data for tag creation."""
    return {
        "name": "Test Tag",
        "color": "blue",
        "description": "Test tag created by the test suite",
        "space_id": test_space_id
    }


@pytest.fixture
def test_property_data(test_space_id: str) -> dict:
    """Provide test data for property creation."""
    return {
        "name": "Test Property",
        "description": "Test property created by the test suite",
        "format": RelationFormat.SHORT_TEXT,
        "space_id": test_space_id
    }


@pytest.fixture
def test_template_data(test_space_id: str) -> dict:
    """Provide test data for template creation."""
    return {
        "name": "Test Template",
        "description": "Test template created by the test suite",
        "template_type": "page",
        "space_id": test_space_id,
        "content": {
            "sections": ["Introduction", "Main Content", "Conclusion"]
        }
    }


@pytest.fixture
def test_member_data(test_space_id: str) -> dict:
    """Provide test data for member invitation."""
    return {
        "email": "test@example.com",
        "role": "viewer",
        "space_id": test_space_id
    }


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_objects(sync_client: AnytypeClient, test_space_id: str):
    """Cleanup test objects after each test (if needed)."""
    yield
    # Note: In a real implementation, you might want to cleanup test objects
    # However, for this test suite, we'll let objects accumulate for inspection
    pass


def create_test_space(client: AnytypeClient, space_name: str) -> Space:
    """Create a new test space."""
    from anytype_client.models import SpaceCreate
    
    space_data = SpaceCreate(
        name=space_name,
        description="Dedicated space for running the Anytype Python client test suite",
        icon_emoji="🧪"
    )
    
    return client.create_space(space_data)


def setup_test_environment(client: AnytypeClient, space_id: str) -> None:
    """Set up the test environment in the given space."""
    print(f"🔧 Setting up test environment in space {space_id}...")
    
    try:
        # Create initial test structures that the tests expect
        from anytype_client.models import (
            TagCreate, TagColor, ListCreate, PropertyCreate, 
            RelationFormat, TemplateCreate, TemplateType
        )
        
        # Create a test tag for organization
        test_tag = TagCreate(
            name="Test Suite",
            color=TagColor.BLUE,
            description="Automatically created for test suite",
            space_id=space_id
        )
        
        # Create a test list for organization
        test_list = ListCreate(
            name="Test Objects",
            description="List for organizing test objects",
            space_id=space_id
        )
        
        # Create a test property
        test_property = PropertyCreate(
            name="Test Marker",
            description="Property to mark test objects",
            format=RelationFormat.CHECKBOX,
            space_id=space_id
        )
        
        # Create basic test structures
        try:
            client.create_tag(test_tag)
            print("  ✅ Created test tag")
        except Exception as e:
            print(f"  ⚠️  Test tag creation failed: {e}")
        
        try:
            client.create_list(test_list)
            print("  ✅ Created test list")
        except Exception as e:
            print(f"  ⚠️  Test list creation failed: {e}")
        
        try:
            client.create_property(test_property)
            print("  ✅ Created test property")
        except Exception as e:
            print(f"  ⚠️  Test property creation failed: {e}")
        
        print("  ✅ Test environment setup complete")
        
    except Exception as e:
        print(f"  ⚠️  Test environment setup encountered issues: {e}")
        print("  ℹ️  Tests will continue with basic setup")


# Helper functions for tests
def assert_valid_id(obj_id: str) -> None:
    """Assert that an object ID is valid."""
    assert obj_id is not None
    assert isinstance(obj_id, str)
    assert len(obj_id) > 0


def assert_valid_timestamp(timestamp) -> None:
    """Assert that a timestamp is valid."""
    assert timestamp is not None
    # For datetime objects
    if hasattr(timestamp, 'year'):
        assert timestamp.year > 2020


class ObjectTracker:
    """Helper class to track created test objects for cleanup."""
    
    def __init__(self):
        self.objects = []
        self.lists = []
        self.tags = []
        self.properties = []
        self.templates = []
        self.members = []
    
    def add_object(self, obj_id: str):
        self.objects.append(obj_id)
    
    def add_list(self, list_id: str):
        self.lists.append(list_id)
    
    def add_tag(self, tag_id: str):
        self.tags.append(tag_id)
    
    def add_property(self, property_id: str):
        self.properties.append(property_id)
    
    def add_template(self, template_id: str):
        self.templates.append(template_id)
    
    def add_member(self, member_id: str):
        self.members.append(member_id)


@pytest.fixture
def object_tracker() -> ObjectTracker:
    """Provide an object tracker for test cleanup."""
    return ObjectTracker()