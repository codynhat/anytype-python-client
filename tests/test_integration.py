"""Integration tests that exercise the complete API workflow."""
import pytest
import asyncio
from typing import Dict, Any

from anytype_client import AnytypeClient, AsyncAnytypeClient
from anytype_client.models import (
    ObjectCreate, ObjectType, LayoutType, SearchQuery, PaginationParams,
    TagCreate, TagColor, ListCreate, PropertyCreate, RelationFormat,
    TemplateCreate, TemplateType
)
from tests.conftest import assert_valid_id, ObjectTracker


class TestCompleteWorkflow:
    """Test a complete workflow using multiple API operations."""
    
    def test_content_creation_workflow(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test a complete content creation workflow."""
        # 1. Create a tag for categorization
        tag_data = TagCreate(
            name="Integration Test",
            color=TagColor.GREEN,
            description="Tag for integration testing",
            space_id=test_space_id
        )
        created_tag = sync_client.create_tag(tag_data)
        object_tracker.add_tag(created_tag.id)
        
        # 2. Create a property for metadata
        property_data = PropertyCreate(
            name="Test Priority",
            description="Priority level for test objects",
            format=RelationFormat.SHORT_TEXT,
            space_id=test_space_id
        )
        created_property = sync_client.create_property(property_data)
        object_tracker.add_property(created_property.id)
        
        # 3. Create a template
        template_data = TemplateCreate(
            name="Integration Test Template",
            description="Template for integration testing",
            template_type=TemplateType.PAGE,
            space_id=test_space_id,
            content={
                "sections": ["Introduction", "Main Content", "Conclusion"],
                "default_tags": [created_tag.name],
                "default_properties": {"priority": "high"}
            }
        )
        created_template = sync_client.create_template(template_data)
        object_tracker.add_template(created_template.id)
        
        # 4. Create a list to organize objects
        list_data = ListCreate(
            name="Integration Test List",
            description="List for organizing test objects",
            space_id=test_space_id
        )
        created_list = sync_client.create_list(list_data)
        object_tracker.add_list(created_list.id)
        
        # 5. Create multiple related objects
        objects = []
        for i in range(3):
            object_data = ObjectCreate(
                name=f"Integration Test Object {i+1}",
                type=ObjectType.NOTE,
                layout=LayoutType.BASIC,
                space_id=test_space_id,
                properties={
                    "description": f"Object {i+1} for integration testing",
                    "priority": "high",
                    "category": "integration-test"
                },
                icon_emoji="📝"
            )
            created_object = sync_client.create_object(object_data)
            objects.append(created_object)
            object_tracker.add_object(created_object.id)
        
        # 6. Search for our created objects
        search_query = SearchQuery(
            text="Integration Test Object",
            space_id=test_space_id,
            limit=10
        )
        search_results = sync_client.search_objects(search_query)
        
        # Verify our objects are found
        result_ids = {obj.id for obj in search_results}
        for obj in objects:
            assert obj.id in result_ids
        
        # 7. Update one of the objects
        updated_object = sync_client.update_object(
            objects[0].id,
            {
                "name": "Updated Integration Test Object 1",
                "properties": {"status": "completed"}
            }
        )
        assert updated_object.name == "Updated Integration Test Object 1"
        
        # 8. Verify all components exist
        assert created_tag.name == "Integration Test"
        assert created_property.name == "Test Priority"
        assert created_template.name == "Integration Test Template"
        assert created_list.name == "Integration Test List"
        assert len(objects) == 3
    
    def test_space_exploration_workflow(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str
    ):
        """Test exploring a space and its contents."""
        # 1. Get space details
        space = sync_client.get_space(test_space_id)
        assert space.name == "ClientTestSpace"
        
        # 2. List all content types in the space
        all_lists = sync_client.list_lists(test_space_id)
        all_tags = sync_client.list_tags(test_space_id)
        all_properties = sync_client.list_properties(test_space_id)
        all_templates = sync_client.list_templates(test_space_id)
        all_members = sync_client.list_members(test_space_id)
        
        # 3. Verify we can access all content types
        assert isinstance(all_lists, list)
        assert isinstance(all_tags, list)
        assert isinstance(all_properties, list)
        assert isinstance(all_templates, list)
        assert isinstance(all_members, list)
        
        # 4. Search across all object types
        search_query = SearchQuery(space_id=test_space_id, limit=20)
        all_objects = sync_client.search_objects(search_query)
        assert isinstance(all_objects, list)
        
        # 5. Get available types
        available_types = sync_client.list_types()
        assert isinstance(available_types, list)
        
        # Verify space consistency
        assert space.id == test_space_id
    
    def test_pagination_workflow(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test pagination across different operations."""
        # Create multiple items to test pagination
        num_items = 5
        
        # Create tags
        for i in range(num_items):
            tag_data = TagCreate(
                name=f"Pagination Tag {i+1}",
                color=TagColor.BLUE,
                space_id=test_space_id
            )
            created_tag = sync_client.create_tag(tag_data)
            object_tracker.add_tag(created_tag.id)
        
        # Test pagination with small page size
        params = PaginationParams(limit=2, offset=0, sort_by="name", sort_direction="asc")
        
        # Paginate through tags
        first_page = sync_client.list_tags(test_space_id, params)
        assert len(first_page) <= 2
        
        params.offset = 2
        second_page = sync_client.list_tags(test_space_id, params)
        assert len(second_page) <= 2
        
        # Verify no overlap
        if len(first_page) > 0 and len(second_page) > 0:
            first_ids = {tag.id for tag in first_page}
            second_ids = {tag.id for tag in second_page}
            assert not first_ids.intersection(second_ids)


class TestAsyncIntegration:
    """Test integration workflows with async client."""
    
    @pytest.mark.asyncio
    async def test_async_complete_workflow(
        self, 
        async_client: AsyncAnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test complete workflow with async client."""
        # 1. Create content concurrently
        tag_task = async_client.create_tag(TagCreate(
            name="Async Integration Tag",
            color=TagColor.PURPLE,
            space_id=test_space_id
        ))
        
        list_task = async_client.create_list(ListCreate(
            name="Async Integration List",
            space_id=test_space_id
        ))
        
        # Execute creations concurrently
        created_tag, created_list = await asyncio.gather(tag_task, list_task)
        object_tracker.add_tag(created_tag.id)
        object_tracker.add_list(created_list.id)
        
        # 2. Create objects referencing the tag and list
        object_tasks = []
        for i in range(3):
            object_data = ObjectCreate(
                name=f"Async Object {i+1}",
                type=ObjectType.NOTE,
                layout=LayoutType.BASIC,
                space_id=test_space_id,
                properties={"async_test": True, "index": i+1}
            )
            object_tasks.append(async_client.create_object(object_data))
        
        created_objects = await asyncio.gather(*object_tasks)
        for obj in created_objects:
            object_tracker.add_object(obj.id)
        
        # 3. Concurrent read operations
        read_tasks = [
            async_client.get_tag(created_tag.id),
            async_client.get_list(created_list.id),
            async_client.search_objects(SearchQuery(
                text="Async Object",
                space_id=test_space_id,
                limit=5
            ))
        ]
        
        tag, list_obj, search_results = await asyncio.gather(*read_tasks)
        
        # Verify results
        assert tag.id == created_tag.id
        assert list_obj.id == created_list.id
        assert len(search_results) >= 3  # Should find our async objects
        
        # 4. Concurrent updates
        update_tasks = []
        for i, obj in enumerate(created_objects):
            updates = {"name": f"Updated Async Object {i+1}"}
            update_tasks.append(async_client.update_object(obj.id, updates))
        
        updated_objects = await asyncio.gather(*update_tasks)
        
        for i, obj in enumerate(updated_objects):
            assert obj.name == f"Updated Async Object {i+1}"
    
    @pytest.mark.asyncio
    async def test_async_error_resilience(
        self, 
        async_client: AsyncAnytypeClient,
        test_space_id: str
    ):
        """Test that async operations are resilient to individual failures."""
        # Mix of valid and invalid operations
        tasks = [
            async_client.list_spaces(),  # Valid
            async_client.get_space("invalid-id"),  # Invalid
            async_client.list_tags(test_space_id),  # Valid
            async_client.get_tag("invalid-tag-id"),  # Invalid
            async_client.list_types(),  # Valid
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should have mix of results and exceptions
        assert isinstance(results[0], list)  # Spaces
        assert isinstance(results[1], Exception)  # Invalid space
        assert isinstance(results[2], list)  # Tags
        assert isinstance(results[3], Exception)  # Invalid tag
        assert isinstance(results[4], list)  # Types


class TestPerformanceCharacteristics:
    """Test performance characteristics of the client."""
    
    def test_batch_operations_performance(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test performance of batch operations."""
        import time
        
        # Time object creation
        start_time = time.time()
        objects = []
        for i in range(10):
            object_data = ObjectCreate(
                name=f"Performance Test Object {i+1}",
                type=ObjectType.NOTE,
                layout=LayoutType.BASIC,
                space_id=test_space_id,
                properties={"batch_test": True, "index": i+1}
            )
            created_object = sync_client.create_object(object_data)
            objects.append(created_object)
            object_tracker.add_object(created_object.id)
        
        creation_time = time.time() - start_time
        
        # Time batch retrieval
        start_time = time.time()
        for obj in objects:
            retrieved = sync_client.get_object(obj.id)
            assert retrieved.id == obj.id
        
        retrieval_time = time.time() - start_time
        
        # Basic performance assertions (these are loose bounds)
        assert creation_time < 30.0  # Should create 10 objects in under 30 seconds
        assert retrieval_time < 20.0  # Should retrieve 10 objects in under 20 seconds
        
        print(f"Created 10 objects in {creation_time:.2f}s")
        print(f"Retrieved 10 objects in {retrieval_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_async_performance_advantage(
        self, 
        async_client: AsyncAnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test that async operations show performance benefits for concurrent work."""
        import time
        
        # Time concurrent async operations
        start_time = time.time()
        
        # Create multiple objects concurrently
        object_tasks = []
        for i in range(5):
            object_data = ObjectCreate(
                name=f"Async Performance Object {i+1}",
                type=ObjectType.NOTE,
                layout=LayoutType.BASIC,
                space_id=test_space_id,
                properties={"async_perf_test": True}
            )
            object_tasks.append(async_client.create_object(object_data))
        
        created_objects = await asyncio.gather(*object_tasks)
        for obj in created_objects:
            object_tracker.add_object(obj.id)
        
        async_time = time.time() - start_time
        
        # Async operations should be reasonably fast
        assert async_time < 15.0  # Should create 5 objects concurrently in under 15 seconds
        assert len(created_objects) == 5
        
        print(f"Created 5 objects concurrently in {async_time:.2f}s")


class TestErrorRecovery:
    """Test error recovery and resilience."""
    
    def test_partial_failure_recovery(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test recovery from partial failures in batch operations."""
        successful_operations = 0
        failed_operations = 0
        
        # Attempt operations that might partially fail
        test_operations = [
            ("valid_tag", TagCreate(name="Valid Tag", space_id=test_space_id)),
            ("valid_list", ListCreate(name="Valid List", space_id=test_space_id)),
        ]
        
        results = {}
        for name, data in test_operations:
            try:
                if isinstance(data, TagCreate):
                    result = sync_client.create_tag(data)
                    object_tracker.add_tag(result.id)
                elif isinstance(data, ListCreate):
                    result = sync_client.create_list(data)
                    object_tracker.add_list(result.id)
                
                results[name] = result
                successful_operations += 1
            except Exception as e:
                results[name] = e
                failed_operations += 1
        
        # Should have some successful operations
        assert successful_operations > 0
        
        # Verify successful operations created valid objects
        for name, result in results.items():
            if not isinstance(result, Exception):
                assert_valid_id(result.id)
    
    def test_connection_resilience(self, sync_client: AnytypeClient):
        """Test client resilience to connection issues."""
        # This test verifies the client can handle basic errors gracefully
        # In a real environment, you might test network timeouts, etc.
        
        # Test with various invalid requests
        invalid_requests = [
            lambda: sync_client.get_space("definitely-invalid-id"),
            lambda: sync_client.get_object("definitely-invalid-object-id"),
            lambda: sync_client.get_tag("definitely-invalid-tag-id"),
        ]
        
        for request in invalid_requests:
            try:
                request()
                assert False, "Should have raised an exception"
            except Exception as e:
                # Should be a proper API error, not a connection error
                assert hasattr(e, '__class__')
                assert "API" in str(type(e)) or "Error" in str(type(e))


class TestDataConsistency:
    """Test data consistency across operations."""
    
    def test_crud_consistency(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test that CRUD operations maintain data consistency."""
        # Create an object with specific data
        original_data = ObjectCreate(
            name="Consistency Test Object",
            type=ObjectType.NOTE,
            layout=LayoutType.BASIC,
            space_id=test_space_id,
            properties={
                "test_field": "original_value",
                "number_field": 42,
                "boolean_field": True
            }
        )
        
        # Create
        created = sync_client.create_object(original_data)
        object_tracker.add_object(created.id)
        
        # Read and verify
        retrieved = sync_client.get_object(created.id)
        assert retrieved.id == created.id
        assert retrieved.name == original_data.name
        assert retrieved.type == original_data.type
        
        # Update
        updates = {
            "name": "Updated Consistency Test Object",
            "properties": {"test_field": "updated_value", "new_field": "added"}
        }
        updated = sync_client.update_object(created.id, updates)
        assert updated.name == "Updated Consistency Test Object"
        
        # Verify update persisted
        re_retrieved = sync_client.get_object(created.id)
        assert re_retrieved.name == "Updated Consistency Test Object"
        assert re_retrieved.id == created.id
    
    def test_search_consistency(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test that search results are consistent with object state."""
        # Create a uniquely named object
        unique_name = "SearchConsistencyTest"
        object_data = ObjectCreate(
            name=unique_name,
            type=ObjectType.NOTE,
            layout=LayoutType.BASIC,
            space_id=test_space_id,
            properties={"searchable": True}
        )
        
        created = sync_client.create_object(object_data)
        object_tracker.add_object(created.id)
        
        # Search for the object
        search_query = SearchQuery(
            text=unique_name,
            space_id=test_space_id,
            limit=10
        )
        
        search_results = sync_client.search_objects(search_query)
        
        # Object should be found in search
        found_object = None
        for result in search_results:
            if result.id == created.id:
                found_object = result
                break
        
        assert found_object is not None, f"Object with name '{unique_name}' not found in search"
        assert found_object.name == unique_name
        assert found_object.id == created.id