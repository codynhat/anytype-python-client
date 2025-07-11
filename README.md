# Anytype Python Client

A modern, comprehensive Python client library for the [Anytype](https://anytype.io/) API. This library provides both synchronous and asynchronous interfaces for interacting with Anytype's knowledge management platform.

## Features

- 🔄 **Full API Coverage**: Complete implementation of all 10 Anytype API categories
- 🚀 **Sync & Async**: Both synchronous and asynchronous client implementations
- 📝 **Type Safety**: Fully typed with Pydantic models for all API entities
- 🎯 **Easy to Use**: Intuitive Python interface with comprehensive error handling
- 🧪 **Well Tested**: Extensive test suite with 100+ tests covering all functionality
- 📚 **Rich Documentation**: Complete API reference and usage examples

## Supported API Operations

### Core Features
- **Authentication**: Challenge-based API key creation and management
- **Spaces**: Workspace creation, management, and organization
- **Objects**: Full CRUD operations for Anytype objects (pages, notes, etc.)
- **Search**: Powerful search capabilities with filters and pagination
- **Types**: Custom object type definitions and management

### Advanced Features
- **Lists**: Create and manage lists with item positioning
- **Members**: Space member management with role-based permissions
- **Properties**: Custom property definitions with various formats
- **Tags**: Organize content with colored tags and descriptions
- **Templates**: Reusable templates for objects and pages

## Installation

### From PyPI (when published)
```bash
pip install anytype-client
```

### For Development

This project uses [Poetry](https://python-poetry.org/) for dependency management:

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Clone and set up the project
git clone https://github.com/beaucronin/anytype-python-client.git
cd anytype-python-client

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### Alternative: pip install for development
```bash
pip install -e .[dev]
```

## Quick Start

### Prerequisites

1. **Anytype Desktop App**: Make sure you have the Anytype desktop application running locally
2. **API Access**: The client connects to `http://localhost:31009/v1/` by default

### Basic Usage

```python
from anytype_client import AnytypeClient
from anytype_client.models import ObjectCreate, SpaceCreate

# Initialize the client
client = AnytypeClient(api_key="your-api-key")

# Or use environment variable ANYTYPE_API_KEY
client = AnytypeClient()

# List all spaces
spaces = client.list_spaces()
print(f"Found {len(spaces)} spaces")

# Create a new object
object_data = ObjectCreate(
    name="My First Note",
    type_key="page",
    space_id=spaces[0].id
)
new_object = client.create_object(spaces[0].id, object_data)
print(f"Created object: {new_object.name}")
```

### Asynchronous Usage

```python
import asyncio
from anytype_client import AsyncAnytypeClient

async def main():
    async with AsyncAnytypeClient(api_key="your-api-key") as client:
        spaces = await client.list_spaces()
        print(f"Found {len(spaces)} spaces")

asyncio.run(main())
```

### Interactive Authentication

```python
from anytype_client import AnytypeClient

def authenticate():
    with AnytypeClient() as client:
        # Create authentication challenge
        challenge = client.create_auth_challenge("My App")
        
        print(f"Enter this code in Anytype: {challenge.challenge_id}")
        verification_code = input("Enter verification code: ")
        
        # Get API key
        api_key = client.create_api_key(challenge.challenge_id, verification_code)
        return api_key.key

# Save for future use
api_key = authenticate()
```

## Advanced Examples

### Working with Objects

```python
from anytype_client.models import ObjectCreate, ObjectUpdate, LayoutType

# Create a structured object
object_data = ObjectCreate(
    name="Project Plan",
    type_key="page",
    layout=LayoutType.BASIC,
    space_id=space_id,
    properties=[
        {"key": "status", "value": "In Progress"},
        {"key": "priority", "value": "High"}
    ]
)

obj = client.create_object(space_id, object_data)

# Update the object
update_data = ObjectUpdate(
    name="Updated Project Plan",
    properties={"status": "Completed"}
)
updated_obj = client.update_object(space_id, obj.id, update_data)
```

### Search and Filtering

```python
from anytype_client.models import SearchQuery, ObjectType

# Search for specific objects
search_query = SearchQuery(
    text="project",
    type=ObjectType.NOTE,
    space_id=space_id,
    filters=[
        {"property": "status", "condition": "equal", "value": "active"}
    ],
    limit=10
)

results = client.search_objects(search_query)
```

### Managing Properties

```python
from anytype_client.models import PropertyCreate, RelationFormat

# Create a custom property
property_data = PropertyCreate(
    name="Project Status",
    description="Current status of the project",
    format=RelationFormat.SELECT,
    space_id=space_id
)

property_obj = client.create_property(property_data)
```

### Working with Lists

```python
from anytype_client.models import ListCreate

# Create a new list
list_data = ListCreate(
    name="Reading List",
    description="Books to read this year",
    space_id=space_id
)

reading_list = client.create_list(list_data)

# Add items to the list
client.add_list_item(space_id, reading_list.id, {
    "object_id": book_object_id,
    "position": 0
})
```

### Managing Team Members

```python
from anytype_client.models import MemberInvite, MemberRole

# Invite a team member
invite = MemberInvite(
    email="colleague@example.com",
    role=MemberRole.EDITOR,
    space_id=space_id
)

member = client.invite_member(invite)
```

## Configuration

### Environment Variables

- `ANYTYPE_API_KEY`: Your Anytype API key
- `ANYTYPE_BASE_URL`: Custom API base URL (default: `http://localhost:31009/v1/`)

### Client Configuration

```python
client = AnytypeClient(
    api_key="your-key",
    base_url="http://localhost:31009/v1/",
    timeout=30.0
)
```

## Error Handling

The client provides specific exception types for different error conditions:

```python
from anytype_client.exceptions import (
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError
)

try:
    obj = client.get_object(space_id, object_id)
except AuthenticationError:
    print("Invalid API key")
except NotFoundError:
    print("Object not found")
except ValidationError as e:
    print(f"Invalid data: {e}")
```

## Models and Types

All API responses are parsed into strongly-typed Pydantic models:

```python
from anytype_client.models import (
    Space, Object, Property, List, Member, Tag, Template,
    SpaceCreate, ObjectCreate, PropertyCreate,
    PaginationParams, SearchQuery
)

# All models provide IDE autocompletion and type checking
space: Space = client.get_space(space_id)
print(space.name)          # ✅ Type-safe
print(space.created_date)  # ✅ datetime object
print(space.network_id)    # ✅ String
```

## Development

### Running Tests

```bash
# With Poetry (recommended)
poetry install
poetry run python run_tests.py --all

# Run specific test categories
poetry run python run_tests.py --quick
poetry run pytest tests/test_objects.py -v

# Or activate shell first
poetry shell
python run_tests.py --all
pytest tests/test_objects.py -v
```

### Code Quality

```bash
# With Poetry
poetry run black anytype_client/
poetry run isort anytype_client/
poetry run mypy anytype_client/
poetry run ruff check anytype_client/

# Or with activated shell
poetry shell
black anytype_client/
isort anytype_client/
mypy anytype_client/
ruff check anytype_client/
```

### Test Environment

The test suite automatically creates and manages a dedicated `ClientTestSpace` for testing. Make sure your Anytype desktop app is running before executing tests.

## API Reference

### Core Classes

- **`AnytypeClient`**: Synchronous client for API operations
- **`AsyncAnytypeClient`**: Asynchronous client for API operations
- **`Space`**: Represents an Anytype workspace
- **`Object`**: Represents any Anytype object (page, note, etc.)
- **`Property`**: Custom property definitions
- **`List`**: Organized collections of objects
- **`Member`**: Space member with role-based permissions
- **`Tag`**: Organizational tags with colors
- **`Template`**: Reusable object templates

### Authentication Flow

1. **Create Challenge**: `client.create_auth_challenge(app_name)`
2. **User Verification**: User enters code in Anytype app
3. **Exchange Code**: `client.create_api_key(challenge_id, verification_code)`
4. **Store Key**: Save API key for future use

### API Endpoints

The client implements all official Anytype API endpoints:

- `/v1/auth/challenge` - Authentication challenges
- `/v1/spaces/` - Space management
- `/v1/spaces/{space_id}/objects` - Object operations
- `/v1/search` - Global search
- `/v1/spaces/{space_id}/types` - Type definitions
- `/v1/spaces/{space_id}/lists` - List management
- `/v1/spaces/{space_id}/members` - Member management
- `/v1/spaces/{space_id}/properties` - Property definitions
- `/v1/spaces/{space_id}/tags` - Tag management
- `/v1/spaces/{space_id}/templates` - Template management

## Architecture

### Layered Design

- **Client Layer**: HTTP client with authentication and error handling
- **Model Layer**: Pydantic models for type safety and validation
- **Exception Layer**: Structured error hierarchy for different failure modes

### Key Features

- **Space-Scoped Operations**: Most operations are scoped to specific spaces
- **Flexible Response Parsing**: Handles various API response formats
- **Backward Compatibility**: Maintains compatibility with legacy field names
- **Pagination Support**: Built-in pagination for list operations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Official Documentation

- **Anytype API Reference**: https://developers.anytype.io/docs/reference/
- **Anytype Website**: https://anytype.io/
- **Anytype Desktop App**: Required for local API access

## Development Notes

**⚠️ AI-Generated Code**: This library was generated using [Claude Code](https://claude.ai/code) and has been thoroughly tested with a comprehensive test suite (100+ tests). While the code has been validated against the actual Anytype API, please note:

- **Use in Production**: Exercise appropriate caution when using in production environments
- **API Changes**: The Anytype API is evolving; some features may change or break
- **Testing Recommended**: Always test thoroughly in your specific use case
- **Community Contributions**: Bug reports, improvements, and human review are especially welcome

The test suite validates all major functionality against a real Anytype instance, but real-world usage may reveal edge cases not covered in testing.

## Support

- **Issues**: Report bugs and request features on GitHub
- **Discussions**: Community discussions and questions
- **Documentation**: Complete API reference and examples
- **Human Review**: Code review and contributions from human developers are encouraged

## Disclaimer

This is an unofficial client library for Anytype, not officially endorsed by Any Association. The library interfaces with Anytype's local API and has been tested extensively, but users should validate functionality for their specific use cases.

---

*This client library is designed to work with Anytype's local API server. Make sure you have the Anytype desktop application running before using this client.*