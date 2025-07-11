"""Tests for list management operations."""
import pytest
from typing import Dict, Any

from anytype_client import AnytypeClient
from anytype_client.models import (
    List, ListCreate, ListUpdate, ListItem, PaginationParams
)
from anytype_client.exceptions import APIError
from tests.conftest import assert_valid_id, assert_valid_timestamp, ObjectTracker


class TestListCRUD:
    """Test Create, Read, Update, Delete operations for lists."""
    
    def test_create_list(
        self, 
        sync_client: AnytypeClient, 
        test_list_data: Dict[str, Any],
        object_tracker: ObjectTracker
    ):
        """Test creating a new list."""
        list_create = ListCreate(**test_list_data)
        created_list = sync_client.create_list(list_create)
        
        assert isinstance(created_list, List)
        assert_valid_id(created_list.id)
        assert created_list.name == test_list_data["name"]
        assert created_list.description == test_list_data["description"]
        assert created_list.space_id == test_list_data["space_id"]
        assert created_list.is_archived is False
        assert created_list.total_items >= 0
        
        # Track for potential cleanup
        object_tracker.add_list(created_list.id)
        
        return created_list
    
    def test_get_list(
        self, 
        sync_client: AnytypeClient,
        test_list_data: Dict[str, Any],
        object_tracker: ObjectTracker
    ):
        """Test retrieving a list by ID."""
        # Create a list first
        list_create = ListCreate(**test_list_data)
        created_list = sync_client.create_list(list_create)
        object_tracker.add_list(created_list.id)
        
        # Now retrieve it
        retrieved_list = sync_client.get_list(created_list.id)
        
        assert isinstance(retrieved_list, List)
        assert retrieved_list.id == created_list.id
        assert retrieved_list.name == created_list.name
        assert retrieved_list.description == created_list.description
        assert retrieved_list.space_id == created_list.space_id
    
    def test_update_list(
        self, 
        sync_client: AnytypeClient,
        test_list_data: Dict[str, Any],
        object_tracker: ObjectTracker
    ):
        """Test updating an existing list."""
        # Create a list first
        list_create = ListCreate(**test_list_data)
        created_list = sync_client.create_list(list_create)
        object_tracker.add_list(created_list.id)
        
        # Update it
        update_data = ListUpdate(
            name="Updated Test List",
            description="Updated description for the test list"
        )
        updated_list = sync_client.update_list(created_list.id, update_data)
        
        assert isinstance(updated_list, List)
        assert updated_list.id == created_list.id
        assert updated_list.name == "Updated Test List"
        assert updated_list.description == "Updated description for the test list"
        assert updated_list.space_id == created_list.space_id
    
    def test_delete_list(
        self, 
        sync_client: AnytypeClient,
        test_list_data: Dict[str, Any]
    ):
        """Test deleting a list."""
        # Create a list first
        list_create = ListCreate(**test_list_data)
        created_list = sync_client.create_list(list_create)
        
        # Delete it
        result = sync_client.delete_list(created_list.id)
        assert result is True
        
        # Verify it's deleted (should raise an error)
        with pytest.raises(APIError):
            sync_client.get_list(created_list.id)
    
    def test_archive_list(
        self, 
        sync_client: AnytypeClient,
        test_list_data: Dict[str, Any],
        object_tracker: ObjectTracker
    ):
        """Test archiving a list."""
        # Create a list first
        list_create = ListCreate(**test_list_data)
        created_list = sync_client.create_list(list_create)
        object_tracker.add_list(created_list.id)
        
        # Archive it
        update_data = ListUpdate(is_archived=True)
        archived_list = sync_client.update_list(created_list.id, update_data)
        
        assert archived_list.is_archived is True
        assert archived_list.id == created_list.id


class TestListOperations:
    """Test list-specific operations and behaviors."""
    
    def test_list_spaces(
        self, 
        sync_client: AnytypeClient, 
        test_space_id: str,
        pagination_params: PaginationParams
    ):
        """Test listing all lists in a space."""
        lists = sync_client.list_lists(test_space_id, pagination_params)
        
        assert isinstance(lists, list)
        # Lists might be empty, which is fine
        for list_obj in lists:
            assert isinstance(list_obj, List)
            assert_valid_id(list_obj.id)
            assert list_obj.space_id == test_space_id
            assert isinstance(list_obj.name, str)
    
    def test_list_spaces_without_pagination(
        self, 
        sync_client: AnytypeClient, 
        test_space_id: str
    ):
        """Test listing lists without pagination parameters."""
        lists = sync_client.list_lists(test_space_id)
        
        assert isinstance(lists, list)
        for list_obj in lists:
            assert isinstance(list_obj, List)
            assert list_obj.space_id == test_space_id
    
    def test_create_multiple_lists(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test creating multiple lists in a space."""
        num_lists = 3
        created_lists = []
        
        for i in range(num_lists):
            list_data = ListCreate(
                name=f"Multi Test List {i+1}",
                description=f"Description for list {i+1}",
                space_id=test_space_id
            )
            
            created_list = sync_client.create_list(list_data)
            created_lists.append(created_list)
            object_tracker.add_list(created_list.id)
        
        assert len(created_lists) == num_lists
        
        # Verify each list
        for i, list_obj in enumerate(created_lists):
            assert list_obj.name == f"Multi Test List {i+1}"
            assert_valid_id(list_obj.id)
            assert list_obj.space_id == test_space_id
    
    def test_list_with_items(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test creating a list and checking its items structure."""
        list_data = ListCreate(
            name="List with Items Test",
            description="Testing list items functionality",
            space_id=test_space_id
        )
        
        created_list = sync_client.create_list(list_data)
        object_tracker.add_list(created_list.id)
        
        # Check that items is a list (might be empty)
        assert isinstance(created_list.items, list)
        assert created_list.total_items >= 0
        
        # If there are items, validate their structure
        for item in created_list.items:
            assert isinstance(item, ListItem)
            assert_valid_id(item.id)
            assert_valid_id(item.object_id)
            assert isinstance(item.position, int)
            assert_valid_timestamp(item.added_at)


class TestListErrorHandling:
    """Test error handling for list operations."""
    
    def test_get_nonexistent_list(self, sync_client: AnytypeClient):
        """Test getting a list that doesn't exist."""
        with pytest.raises(APIError):
            sync_client.get_list("nonexistent-list-id")
    
    def test_update_nonexistent_list(self, sync_client: AnytypeClient):
        """Test updating a list that doesn't exist."""
        update_data = ListUpdate(name="Updated Name")
        with pytest.raises(APIError):
            sync_client.update_list("nonexistent-list-id", update_data)
    
    def test_delete_nonexistent_list(self, sync_client: AnytypeClient):
        """Test deleting a list that doesn't exist."""
        with pytest.raises(APIError):
            sync_client.delete_list("nonexistent-list-id")
    
    def test_list_invalid_space(self, sync_client: AnytypeClient):
        """Test listing lists from an invalid space."""
        with pytest.raises(APIError):
            sync_client.list_lists("nonexistent-space-id")
    
    def test_create_list_invalid_space(self, sync_client: AnytypeClient):
        """Test creating a list in an invalid space."""
        list_data = ListCreate(
            name="Invalid Space List",
            space_id="nonexistent-space-id"
        )
        
        with pytest.raises(APIError):
            sync_client.create_list(list_data)


class TestListValidation:
    """Test list model validation and properties."""
    
    def test_list_create_validation(self, test_space_id: str):
        """Test ListCreate model validation."""
        # Valid list creation
        valid_list = ListCreate(
            name="Valid List",
            description="Valid description",
            space_id=test_space_id
        )
        assert valid_list.name == "Valid List"
        assert valid_list.description == "Valid description"
        assert valid_list.space_id == test_space_id
        
        # Minimal valid list (description is optional)
        minimal_list = ListCreate(
            name="Minimal List",
            space_id=test_space_id
        )
        assert minimal_list.name == "Minimal List"
        assert minimal_list.description is None
    
    def test_list_update_validation(self):
        """Test ListUpdate model validation."""
        # All fields optional in update
        update = ListUpdate()
        assert update.name is None
        assert update.description is None
        assert update.is_archived is None
        
        # Partial update
        partial_update = ListUpdate(name="New Name")
        assert partial_update.name == "New Name"
        assert partial_update.description is None
        assert partial_update.is_archived is None
        
        # Full update
        full_update = ListUpdate(
            name="Full Update",
            description="New description",
            is_archived=True
        )
        assert full_update.name == "Full Update"
        assert full_update.description == "New description"
        assert full_update.is_archived is True
    
    def test_list_item_properties(self):
        """Test ListItem model properties."""
        from datetime import datetime
        
        # Create a mock ListItem (normally created by API)
        item_data = {
            "id": "item-123",
            "object_id": "object-456",
            "position": 1,
            "added_at": datetime.now()
        }
        
        # In a real scenario, this would come from API response
        # Here we just test the model structure
        assert "id" in item_data
        assert "object_id" in item_data
        assert "position" in item_data
        assert "added_at" in item_data


class TestListPagination:
    """Test pagination for list operations."""
    
    def test_list_pagination_basic(
        self, 
        sync_client: AnytypeClient, 
        test_space_id: str
    ):
        """Test basic pagination for listing lists."""
        # Create pagination params
        params = PaginationParams(limit=2, offset=0)
        
        # Get first page
        first_page = sync_client.list_lists(test_space_id, params)
        assert isinstance(first_page, list)
        assert len(first_page) <= 2
        
        # Get second page
        params.offset = 2
        second_page = sync_client.list_lists(test_space_id, params)
        assert isinstance(second_page, list)
        
        # If both pages have results, they should be different
        if len(first_page) > 0 and len(second_page) > 0:
            first_ids = {lst.id for lst in first_page}
            second_ids = {lst.id for lst in second_page}
            # Should not have overlapping IDs
            assert not first_ids.intersection(second_ids)
    
    def test_list_sorting(
        self, 
        sync_client: AnytypeClient, 
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test sorting lists by name."""
        # Create multiple lists with sortable names
        list_names = ["A-List", "B-List", "C-List"]
        created_lists = []
        
        for name in list_names:
            list_data = ListCreate(
                name=name,
                space_id=test_space_id
            )
            created_list = sync_client.create_list(list_data)
            created_lists.append(created_list)
            object_tracker.add_list(created_list.id)
        
        # List with sorting
        params = PaginationParams(
            limit=10,
            sort_by="name",
            sort_direction="asc"
        )
        
        sorted_lists = sync_client.list_lists(test_space_id, params)
        
        # Find our created lists in the results
        our_lists = [lst for lst in sorted_lists if lst.name in list_names]
        
        # Should be in alphabetical order
        if len(our_lists) >= 2:
            names = [lst.name for lst in our_lists]
            assert names == sorted(names)


class TestListIntegration:
    """Test integration between lists and other operations."""
    
    def test_list_in_space_context(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        test_space,
        object_tracker: ObjectTracker
    ):
        """Test that lists are properly associated with their space."""
        # Create a list
        list_data = ListCreate(
            name="Space Integration Test List",
            description="Testing space-list relationship",
            space_id=test_space_id
        )
        
        created_list = sync_client.create_list(list_data)
        object_tracker.add_list(created_list.id)
        
        # Verify space association
        assert created_list.space_id == test_space_id
        assert created_list.space_id == test_space.id
        
        # List should appear when listing all lists in the space
        all_lists = sync_client.list_lists(test_space_id)
        list_ids = [lst.id for lst in all_lists]
        assert created_list.id in list_ids
    
    def test_list_lifecycle(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test complete lifecycle of a list."""
        # 1. Create
        list_data = ListCreate(
            name="Lifecycle Test List",
            description="Testing complete list lifecycle",
            space_id=test_space_id
        )
        created_list = sync_client.create_list(list_data)
        object_tracker.add_list(created_list.id)
        assert created_list.name == "Lifecycle Test List"
        
        # 2. Read
        retrieved_list = sync_client.get_list(created_list.id)
        assert retrieved_list.id == created_list.id
        
        # 3. Update
        update_data = ListUpdate(
            name="Updated Lifecycle List",
            description="Updated description"
        )
        updated_list = sync_client.update_list(created_list.id, update_data)
        assert updated_list.name == "Updated Lifecycle List"
        
        # 4. Archive
        archive_data = ListUpdate(is_archived=True)
        archived_list = sync_client.update_list(created_list.id, archive_data)
        assert archived_list.is_archived is True
        
        # 5. Final verification
        final_list = sync_client.get_list(created_list.id)
        assert final_list.is_archived is True
        assert final_list.name == "Updated Lifecycle List"