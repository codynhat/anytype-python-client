"""Tests for async client functionality."""
import pytest
import asyncio
from typing import Dict, Any

from anytype_client import AsyncAnytypeClient
from anytype_client.models import (
    Space, Object, ObjectCreate, ObjectType, LayoutType,
    SearchQuery, TagCreate, TagColor, ListCreate
)
from anytype_client.exceptions import APIError
from tests.conftest import assert_valid_id, ObjectTracker


class TestAsyncClientBasics:
    """Test basic async client functionality."""
    
    @pytest.mark.asyncio
    async def test_async_client_context_manager(self, api_key: str):
        """Test that async client works as context manager."""
        async with AsyncAnytypeClient(api_key=api_key) as client:
            assert client.api_key == api_key
    
    @pytest.mark.asyncio
    async def test_async_client_manual_connection(self, api_key: str):
        """Test manual connection management."""
        client = AsyncAnytypeClient(api_key=api_key)
        await client.connect()
        
        # Should be able to make requests
        spaces = await client.list_spaces()
        assert isinstance(spaces, list)
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_async_client_initialization(self, api_key: str):
        """Test async client initialization."""
        client = AsyncAnytypeClient(api_key=api_key)
        assert client.api_key == api_key
        assert client.base_url.endswith("/")
        await client.close()


class TestAsyncSpaceOperations:
    """Test async space operations."""
    
    @pytest.mark.asyncio
    async def test_async_list_spaces(self, async_client: AsyncAnytypeClient):
        """Test listing spaces with async client."""
        spaces = await async_client.list_spaces()
        assert isinstance(spaces, list)
        assert len(spaces) > 0
        
        for space in spaces:
            assert isinstance(space, Space)
            assert_valid_id(space.id)
            assert isinstance(space.name, str)
    
    @pytest.mark.asyncio
    async def test_async_get_space(self, async_client: AsyncAnytypeClient, test_space_id: str):
        """Test getting a specific space with async client."""
        space = await async_client.get_space(test_space_id)
        assert isinstance(space, Space)
        assert space.id == test_space_id
    
    @pytest.mark.asyncio
    async def test_async_get_nonexistent_space(self, async_client: AsyncAnytypeClient):
        """Test getting a nonexistent space with async client."""
        with pytest.raises(APIError):
            await async_client.get_space("nonexistent-space-id")


class TestAsyncObjectOperations:
    """Test async object operations."""
    
    @pytest.mark.asyncio
    async def test_async_create_object(
        self, 
        async_client: AsyncAnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test creating an object with async client."""
        object_data = ObjectCreate(
            name="Async Test Object",
            type=ObjectType.NOTE,
            layout=LayoutType.BASIC,
            space_id=test_space_id,
            properties={"description": "Created with async client"}
        )
        
        created_object = await async_client.create_object(object_data)
        object_tracker.add_object(created_object.id)
        
        assert isinstance(created_object, Object)
        assert_valid_id(created_object.id)
        assert created_object.name == "Async Test Object"
        assert created_object.type == ObjectType.NOTE
    
    @pytest.mark.asyncio
    async def test_async_get_object(
        self, 
        async_client: AsyncAnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test getting an object with async client."""
        # Create object first
        object_data = ObjectCreate(
            name="Async Get Test Object",
            type=ObjectType.NOTE,
            layout=LayoutType.BASIC,
            space_id=test_space_id
        )
        created_object = await async_client.create_object(object_data)
        object_tracker.add_object(created_object.id)
        
        # Get the object
        retrieved_object = await async_client.get_object(created_object.id)
        assert retrieved_object.id == created_object.id
        assert retrieved_object.name == created_object.name
    
    @pytest.mark.asyncio
    async def test_async_update_object(
        self, 
        async_client: AsyncAnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test updating an object with async client."""
        # Create object first
        object_data = ObjectCreate(
            name="Async Update Test Object",
            type=ObjectType.NOTE,
            layout=LayoutType.BASIC,
            space_id=test_space_id
        )
        created_object = await async_client.create_object(object_data)
        object_tracker.add_object(created_object.id)
        
        # Update the object
        updates = {"name": "Updated Async Object"}
        updated_object = await async_client.update_object(created_object.id, updates)
        
        assert updated_object.name == "Updated Async Object"
        assert updated_object.id == created_object.id
    
    @pytest.mark.asyncio
    async def test_async_delete_object(
        self, 
        async_client: AsyncAnytypeClient,
        test_space_id: str
    ):
        """Test deleting an object with async client."""
        # Create object first
        object_data = ObjectCreate(
            name="Async Delete Test Object",
            type=ObjectType.NOTE,
            layout=LayoutType.BASIC,
            space_id=test_space_id
        )
        created_object = await async_client.create_object(object_data)
        
        # Delete the object
        result = await async_client.delete_object(created_object.id)
        assert result is True
        
        # Verify deletion
        with pytest.raises(APIError):
            await async_client.get_object(created_object.id)


class TestAsyncSearchOperations:
    """Test async search operations."""
    
    @pytest.mark.asyncio
    async def test_async_search_objects(
        self, 
        async_client: AsyncAnytypeClient,
        test_space_id: str
    ):
        """Test searching objects with async client."""
        search_query = SearchQuery(
            text="test",
            space_id=test_space_id,
            limit=5
        )
        
        results = await async_client.search_objects(search_query)
        assert isinstance(results, list)
        
        for result in results:
            assert isinstance(result, Object)
            assert_valid_id(result.id)
    
    @pytest.mark.asyncio
    async def test_async_search_by_type(
        self, 
        async_client: AsyncAnytypeClient,
        test_space_id: str
    ):
        """Test searching by object type with async client."""
        search_query = SearchQuery(
            type=ObjectType.NOTE,
            space_id=test_space_id,
            limit=5
        )
        
        results = await async_client.search_objects(search_query)
        assert isinstance(results, list)
        
        for result in results:
            assert result.type == ObjectType.NOTE


class TestAsyncTypeOperations:
    """Test async type operations."""
    
    @pytest.mark.asyncio
    async def test_async_list_types(self, async_client: AsyncAnytypeClient):
        """Test listing types with async client."""
        types = await async_client.list_types()
        assert isinstance(types, list)
        
        if len(types) > 0:
            for type_obj in types:
                assert_valid_id(type_obj.id)
                assert isinstance(type_obj.name, str)
    
    @pytest.mark.asyncio
    async def test_async_get_type(self, async_client: AsyncAnytypeClient):
        """Test getting a specific type with async client."""
        types = await async_client.list_types()
        
        if len(types) > 0:
            first_type = types[0]
            retrieved_type = await async_client.get_type(first_type.id)
            assert retrieved_type.id == first_type.id
            assert retrieved_type.name == first_type.name


class TestAsyncExtendedOperations:
    """Test async operations for extended functionality."""
    
    @pytest.mark.asyncio
    async def test_async_list_operations(
        self, 
        async_client: AsyncAnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test async list operations."""
        # Create a list
        list_data = ListCreate(
            name="Async Test List",
            description="List created with async client",
            space_id=test_space_id
        )
        
        created_list = await async_client.create_list(list_data)
        object_tracker.add_list(created_list.id)
        
        assert created_list.name == "Async Test List"
        assert_valid_id(created_list.id)
        
        # Get the list
        retrieved_list = await async_client.get_list(created_list.id)
        assert retrieved_list.id == created_list.id
        
        # List all lists
        all_lists = await async_client.list_lists(test_space_id)
        assert isinstance(all_lists, list)
        list_ids = [lst.id for lst in all_lists]
        assert created_list.id in list_ids
    
    @pytest.mark.asyncio
    async def test_async_tag_operations(
        self, 
        async_client: AsyncAnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test async tag operations."""
        # Create a tag
        tag_data = TagCreate(
            name="Async Test Tag",
            color=TagColor.PURPLE,
            description="Tag created with async client",
            space_id=test_space_id
        )
        
        created_tag = await async_client.create_tag(tag_data)
        object_tracker.add_tag(created_tag.id)
        
        assert created_tag.name == "Async Test Tag"
        assert created_tag.color == TagColor.PURPLE
        assert_valid_id(created_tag.id)
        
        # Get the tag
        retrieved_tag = await async_client.get_tag(created_tag.id)
        assert retrieved_tag.id == created_tag.id
        
        # List all tags
        all_tags = await async_client.list_tags(test_space_id)
        assert isinstance(all_tags, list)
        tag_ids = [tag.id for tag in all_tags]
        assert created_tag.id in tag_ids
    
    @pytest.mark.asyncio
    async def test_async_member_operations(
        self, 
        async_client: AsyncAnytypeClient,
        test_space_id: str
    ):
        """Test async member operations."""
        # List members
        members = await async_client.list_members(test_space_id)
        assert isinstance(members, list)
        
        # If there are members, test getting one
        if len(members) > 0:
            first_member = members[0]
            retrieved_member = await async_client.get_member(test_space_id, first_member.id)
            assert retrieved_member.id == first_member.id
    
    @pytest.mark.asyncio
    async def test_async_property_operations(
        self, 
        async_client: AsyncAnytypeClient,
        test_space_id: str
    ):
        """Test async property operations."""
        # List properties
        properties = await async_client.list_properties(test_space_id)
        assert isinstance(properties, list)
        
        # Properties might be empty, which is fine
        for prop in properties:
            assert_valid_id(prop.id)
    
    @pytest.mark.asyncio
    async def test_async_template_operations(
        self, 
        async_client: AsyncAnytypeClient,
        test_space_id: str
    ):
        """Test async template operations."""
        # List templates
        templates = await async_client.list_templates(test_space_id)
        assert isinstance(templates, list)
        
        # Templates might be empty, which is fine
        for template in templates:
            assert_valid_id(template.id)


class TestAsyncConcurrency:
    """Test async client concurrency features."""
    
    @pytest.mark.asyncio
    async def test_async_concurrent_requests(
        self, 
        async_client: AsyncAnytypeClient,
        test_space_id: str
    ):
        """Test making concurrent async requests."""
        # Create multiple concurrent requests
        tasks = [
            async_client.list_spaces(),
            async_client.get_space(test_space_id),
            async_client.list_types(),
            async_client.list_lists(test_space_id),
            async_client.list_tags(test_space_id)
        ]
        
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks)
        
        # Verify all results
        spaces, space, types, lists, tags = results
        
        assert isinstance(spaces, list)
        assert space.id == test_space_id
        assert isinstance(types, list)
        assert isinstance(lists, list)
        assert isinstance(tags, list)
    
    @pytest.mark.asyncio
    async def test_async_batch_object_creation(
        self, 
        async_client: AsyncAnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test creating multiple objects concurrently."""
        # Create multiple object creation tasks
        object_tasks = []
        for i in range(3):
            object_data = ObjectCreate(
                name=f"Concurrent Object {i+1}",
                type=ObjectType.NOTE,
                layout=LayoutType.BASIC,
                space_id=test_space_id,
                properties={"index": str(i+1)}
            )
            object_tasks.append(async_client.create_object(object_data))
        
        # Execute all creations concurrently
        created_objects = await asyncio.gather(*object_tasks)
        
        # Track all created objects
        for obj in created_objects:
            object_tracker.add_object(obj.id)
        
        # Verify all objects were created
        assert len(created_objects) == 3
        for i, obj in enumerate(created_objects):
            assert obj.name == f"Concurrent Object {i+1}"
            assert_valid_id(obj.id)


class TestAsyncErrorHandling:
    """Test async client error handling."""
    
    @pytest.mark.asyncio
    async def test_async_api_error(self, async_client: AsyncAnytypeClient):
        """Test that async client properly handles API errors."""
        with pytest.raises(APIError):
            await async_client.get_space("nonexistent-space-id")
    
    @pytest.mark.asyncio
    async def test_async_multiple_errors(self, async_client: AsyncAnytypeClient):
        """Test handling multiple concurrent errors."""
        # Create tasks that will all fail
        error_tasks = [
            async_client.get_space("nonexistent-1"),
            async_client.get_space("nonexistent-2"),
            async_client.get_object("nonexistent-object")
        ]
        
        # All should raise APIError
        results = await asyncio.gather(*error_tasks, return_exceptions=True)
        
        for result in results:
            assert isinstance(result, APIError)
    
    @pytest.mark.asyncio
    async def test_async_mixed_success_error(
        self, 
        async_client: AsyncAnytypeClient,
        test_space_id: str
    ):
        """Test mixing successful and failing requests."""
        tasks = [
            async_client.list_spaces(),  # Should succeed
            async_client.get_space("nonexistent"),  # Should fail
            async_client.get_space(test_space_id),  # Should succeed
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # First should be a list of spaces
        assert isinstance(results[0], list)
        
        # Second should be an APIError
        assert isinstance(results[1], APIError)
        
        # Third should be a Space object
        assert results[2].id == test_space_id


class TestAsyncClientCleanup:
    """Test async client resource cleanup."""
    
    @pytest.mark.asyncio
    async def test_async_client_resource_cleanup(self, api_key: str):
        """Test that async client properly cleans up resources."""
        client = AsyncAnytypeClient(api_key=api_key)
        
        # Connect and make a request
        await client.connect()
        spaces = await client.list_spaces()
        assert isinstance(spaces, list)
        
        # Close should not raise an error
        await client.close()
        
        # Trying to use client after close should reconnect automatically
        spaces2 = await client.list_spaces()
        assert isinstance(spaces2, list)
        
        # Final cleanup
        await client.close()
    
    @pytest.mark.asyncio
    async def test_async_context_manager_cleanup(self, api_key: str):
        """Test that context manager properly cleans up."""
        spaces = None
        
        async with AsyncAnytypeClient(api_key=api_key) as client:
            spaces = await client.list_spaces()
            assert isinstance(spaces, list)
        
        # After context exit, we should still have the data
        assert spaces is not None
        assert isinstance(spaces, list)