# Anytype Python Client Test Suite

This comprehensive test suite exercises all functionality of the Anytype Python client, including both synchronous and asynchronous operations across all API endpoints.

## Prerequisites

1. **Anytype Desktop App**: Must be running locally with API enabled
2. **Test Space**: The test suite will automatically set up a test environment
   - For dedicated testing: Create a space named "ClientTestSpace" in your Anytype app
   - For quick testing: Any existing space will work (test environment will be set up automatically)
3. **API Key**: Set the `ANYTYPE_API_KEY` environment variable
4. **Dependencies**: Install test dependencies with `pip install -e .[dev]`

## Quick Start

```bash
# Set your API key
export ANYTYPE_API_KEY=your-api-key-here

# Install dependencies
pip install -e .[dev]

# Check test space configuration
python run_tests.py --space-check

# Run quick tests
python run_tests.py --quick

# Run all tests
python run_tests.py --all
```

## Test Categories

### Core Tests
- **Authentication & Spaces** (`test_auth_and_spaces.py`): Client initialization, authentication, space operations
- **Objects** (`test_objects.py`): Complete CRUD operations for Anytype objects
- **Search & Types** (`test_search_and_types.py`): Search functionality and type management

### Extended API Tests
- **Lists** (`test_lists.py`): List creation, management, and item operations
- **Members** (`test_members.py`): Space member management and roles
- **Properties** (`test_properties.py`): Custom property definitions and formats
- **Tags** (`test_tags.py`): Tag creation, colors, and organization
- **Templates** (`test_templates.py`): Template creation and management

### Client Tests
- **Async Client** (`test_async_client.py`): Asynchronous client operations and concurrency
- **Integration** (`test_integration.py`): End-to-end workflows and performance tests

## Test Runner Options

```bash
# Test categories
python run_tests.py --quick          # Basic functionality only
python run_tests.py --sync           # All synchronous client tests
python run_tests.py --async          # Asynchronous client tests
python run_tests.py --integration    # Integration and workflow tests
python run_tests.py --all            # Complete test suite

# Test options
python run_tests.py --verbose        # Detailed output
python run_tests.py --stop-on-first  # Stop on first failure
python run_tests.py --filter "tag"   # Run tests matching pattern
python run_tests.py --parallel       # Run tests in parallel

# Utility commands
python run_tests.py --space-check    # Verify test space exists
```

## Test Structure

Each test file follows a consistent structure:

```python
class TestOperationCRUD:
    """Test Create, Read, Update, Delete operations."""
    
class TestOperationValidation:
    """Test model validation and properties."""
    
class TestOperationErrorHandling:
    """Test error handling scenarios."""
    
class TestOperationIntegration:
    """Test integration with other operations."""
```

## Test Data Management

- **Fixtures**: Common test data and configurations in `conftest.py`
- **Cleanup**: Object tracker for managing test objects
- **Isolation**: Each test is designed to be independent
- **Space**: Tests use "ClientTestSpace" if available, otherwise automatically set up test environment in existing space
- **Auto-Setup**: Test environment is automatically configured with required test structures

## API Coverage

The test suite provides **comprehensive coverage** of the Anytype API:

| Category | Endpoints | Coverage |
|----------|-----------|----------|
| Authentication | 2/2 | ✅ 100% |
| Spaces | 5/5 | ✅ 100% |
| Objects | 4/4 | ✅ 100% |
| Search | 1/1 | ✅ 100% |
| Types | 2/2 | ✅ 100% |
| Lists | 5/5 | ✅ 100% |
| Members | 5/5 | ✅ 100% |
| Properties | 5/5 | ✅ 100% |
| Tags | 5/5 | ✅ 100% |
| Templates | 5/5 | ✅ 100% |

## Running Individual Tests

```bash
# Run specific test file
pytest tests/test_objects.py

# Run specific test class
pytest tests/test_objects.py::TestObjectCRUD

# Run specific test method
pytest tests/test_objects.py::TestObjectCRUD::test_create_object

# Run with verbose output
pytest tests/test_objects.py -v

# Run async tests
pytest tests/test_async_client.py -v
```

## Error Handling Tests

The test suite includes comprehensive error handling tests:

- Invalid API keys and authentication failures
- Nonexistent resource access (404 errors)
- Invalid parameters and validation errors
- Network timeouts and connection issues
- Concurrent operation conflicts

## Performance Tests

Integration tests include basic performance validation:

- Batch operation timing
- Concurrent async operation benefits
- Search query performance
- Large dataset handling

## Troubleshooting

### Common Issues

1. **"No spaces available"**: Create at least one space in Anytype before running tests
2. **"API key required"**: Set the `ANYTYPE_API_KEY` environment variable
3. **"Connection refused"**: Ensure Anytype desktop app is running
4. **Import errors**: Install dependencies with `pip install -e .[dev]`
5. **"Test environment setup failed"**: Some test structures may fail to create, but tests will continue

### Debug Mode

```bash
# Run with debugger on failures
python run_tests.py --pdb

# Run single test with full output
pytest tests/test_objects.py::TestObjectCRUD::test_create_object -vvv -s
```

### Test Environment

The tests expect:
- Anytype desktop app running on `localhost:31009`
- API version `2025-05-20`
- At least one space accessible with your API key
- Write permissions in the test space
- Automatic test environment setup will create:
  - Test tag for organization
  - Test list for object management
  - Test property for marking test objects

## Contributing

When adding new tests:

1. Follow the existing naming and structure patterns
2. Use the provided fixtures and utilities
3. Include proper error handling tests
4. Test both sync and async variants where applicable
5. Update this README if adding new test categories

## Test Results

Tests generate detailed reports including:
- API response times and performance metrics
- Error handling validation
- Model validation results
- Integration workflow verification

The test suite is designed to be run in CI/CD environments and provides clear success/failure indicators for automated deployment validation.