"""Tests for tag management operations."""
import pytest
from typing import Dict, Any

from anytype_client import AnytypeClient
from anytype_client.models import (
    Tag, TagCreate, TagUpdate, TagColor, PaginationParams
)
from anytype_client.exceptions import APIError
from tests.conftest import assert_valid_id, ObjectTracker


class TestTagCRUD:
    """Test Create, Read, Update, Delete operations for tags."""
    
    def test_create_tag(
        self, 
        sync_client: AnytypeClient, 
        test_tag_data: Dict[str, Any],
        object_tracker: ObjectTracker
    ):
        """Test creating a new tag."""
        tag_create = TagCreate(**test_tag_data)
        created_tag = sync_client.create_tag(tag_create)
        
        assert isinstance(created_tag, Tag)
        assert_valid_id(created_tag.id)
        assert created_tag.name == test_tag_data["name"]
        assert created_tag.color == TagColor(test_tag_data["color"])
        assert created_tag.description == test_tag_data["description"]
        assert created_tag.is_archived is False
        assert created_tag.usage_count >= 0
        
        # Track for potential cleanup
        object_tracker.add_tag(created_tag.id)
        
        return created_tag
    
    def test_get_tag(
        self, 
        sync_client: AnytypeClient,
        test_tag_data: Dict[str, Any],
        object_tracker: ObjectTracker
    ):
        """Test retrieving a tag by ID."""
        # Create a tag first
        tag_create = TagCreate(**test_tag_data)
        created_tag = sync_client.create_tag(tag_create)
        object_tracker.add_tag(created_tag.id)
        
        # Now retrieve it
        retrieved_tag = sync_client.get_tag(created_tag.id)
        
        assert isinstance(retrieved_tag, Tag)
        assert retrieved_tag.id == created_tag.id
        assert retrieved_tag.name == created_tag.name
        assert retrieved_tag.color == created_tag.color
        assert retrieved_tag.description == created_tag.description
    
    def test_update_tag(
        self, 
        sync_client: AnytypeClient,
        test_tag_data: Dict[str, Any],
        object_tracker: ObjectTracker
    ):
        """Test updating an existing tag."""
        # Create a tag first
        tag_create = TagCreate(**test_tag_data)
        created_tag = sync_client.create_tag(tag_create)
        object_tracker.add_tag(created_tag.id)
        
        # Update it
        update_data = TagUpdate(
            name="Updated Test Tag",
            color=TagColor.RED,
            description="Updated description for the test tag"
        )
        updated_tag = sync_client.update_tag(created_tag.id, update_data)
        
        assert isinstance(updated_tag, Tag)
        assert updated_tag.id == created_tag.id
        assert updated_tag.name == "Updated Test Tag"
        assert updated_tag.color == TagColor.RED
        assert updated_tag.description == "Updated description for the test tag"
    
    def test_delete_tag(
        self, 
        sync_client: AnytypeClient,
        test_tag_data: Dict[str, Any]
    ):
        """Test deleting a tag."""
        # Create a tag first
        tag_create = TagCreate(**test_tag_data)
        created_tag = sync_client.create_tag(tag_create)
        
        # Delete it
        result = sync_client.delete_tag(created_tag.id)
        assert result is True
        
        # Verify it's deleted (should raise an error)
        with pytest.raises(APIError):
            sync_client.get_tag(created_tag.id)
    
    def test_archive_tag(
        self, 
        sync_client: AnytypeClient,
        test_tag_data: Dict[str, Any],
        object_tracker: ObjectTracker
    ):
        """Test archiving a tag."""
        # Create a tag first
        tag_create = TagCreate(**test_tag_data)
        created_tag = sync_client.create_tag(tag_create)
        object_tracker.add_tag(created_tag.id)
        
        # Archive it
        update_data = TagUpdate(is_archived=True)
        archived_tag = sync_client.update_tag(created_tag.id, update_data)
        
        assert archived_tag.is_archived is True
        assert archived_tag.id == created_tag.id


class TestTagColors:
    """Test tag color functionality."""
    
    def test_tag_color_enum(self):
        """Test TagColor enum values."""
        colors = [
            TagColor.RED,
            TagColor.ORANGE,
            TagColor.YELLOW,
            TagColor.GREEN,
            TagColor.BLUE,
            TagColor.PURPLE,
            TagColor.PINK,
            TagColor.GREY
        ]
        
        for color in colors:
            assert isinstance(color, TagColor)
            assert isinstance(color.value, str)
        
        # Test enum can be created from string
        assert TagColor("red") == TagColor.RED
        assert TagColor("blue") == TagColor.BLUE
        assert TagColor("grey") == TagColor.GREY
    
    def test_create_tags_with_different_colors(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test creating tags with different colors."""
        colors = [TagColor.RED, TagColor.GREEN, TagColor.BLUE, TagColor.PURPLE]
        
        for color in colors:
            tag_data = TagCreate(
                name=f"Test {color.value.title()} Tag",
                color=color,
                description=f"Testing {color.value} color",
                space_id=test_space_id
            )
            
            created_tag = sync_client.create_tag(tag_data)
            object_tracker.add_tag(created_tag.id)
            
            assert created_tag.color == color
            assert created_tag.name == f"Test {color.value.title()} Tag"
    
    def test_default_tag_color(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test that tags default to grey color when not specified."""
        tag_data = TagCreate(
            name="Default Color Tag",
            space_id=test_space_id
        )
        
        created_tag = sync_client.create_tag(tag_data)
        object_tracker.add_tag(created_tag.id)
        
        assert created_tag.color == TagColor.GREY  # Default color
        assert created_tag.name == "Default Color Tag"


class TestTagOperations:
    """Test tag-specific operations and behaviors."""
    
    def test_list_tags(
        self, 
        sync_client: AnytypeClient, 
        test_space_id: str,
        pagination_params: PaginationParams
    ):
        """Test listing all tags in a space."""
        tags = sync_client.list_tags(test_space_id, pagination_params)
        
        assert isinstance(tags, list)
        # Tags might be empty, which is fine
        for tag in tags:
            assert isinstance(tag, Tag)
            assert_valid_id(tag.id)
            assert isinstance(tag.name, str)
            assert isinstance(tag.color, TagColor)
    
    def test_list_tags_without_pagination(
        self, 
        sync_client: AnytypeClient, 
        test_space_id: str
    ):
        """Test listing tags without pagination parameters."""
        tags = sync_client.list_tags(test_space_id)
        
        assert isinstance(tags, list)
        for tag in tags:
            assert isinstance(tag, Tag)
    
    def test_create_multiple_tags(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test creating multiple tags in a space."""
        tag_names = ["Priority", "Category", "Status", "Project"]
        tag_colors = [TagColor.RED, TagColor.BLUE, TagColor.GREEN, TagColor.PURPLE]
        created_tags = []
        
        for name, color in zip(tag_names, tag_colors):
            tag_data = TagCreate(
                name=name,
                color=color,
                description=f"Tag for {name.lower()}",
                space_id=test_space_id
            )
            
            created_tag = sync_client.create_tag(tag_data)
            created_tags.append(created_tag)
            object_tracker.add_tag(created_tag.id)
        
        assert len(created_tags) == len(tag_names)
        
        # Verify each tag
        for i, tag in enumerate(created_tags):
            assert tag.name == tag_names[i]
            assert tag.color == tag_colors[i]
            assert_valid_id(tag.id)
    
    def test_tag_usage_count(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test that tags track usage count."""
        tag_data = TagCreate(
            name="Usage Count Test Tag",
            color=TagColor.YELLOW,
            description="Testing usage count functionality",
            space_id=test_space_id
        )
        
        created_tag = sync_client.create_tag(tag_data)
        object_tracker.add_tag(created_tag.id)
        
        # Initially, usage count should be 0 or low
        assert created_tag.usage_count >= 0
        assert isinstance(created_tag.usage_count, int)


class TestTagValidation:
    """Test tag model validation and properties."""
    
    def test_tag_create_validation(self, test_space_id: str):
        """Test TagCreate model validation."""
        # Valid tag creation
        valid_tag = TagCreate(
            name="Valid Tag",
            color=TagColor.BLUE,
            description="Valid description",
            space_id=test_space_id
        )
        assert valid_tag.name == "Valid Tag"
        assert valid_tag.color == TagColor.BLUE
        assert valid_tag.description == "Valid description"
        assert valid_tag.space_id == test_space_id
        
        # Minimal valid tag (color defaults to grey)
        minimal_tag = TagCreate(
            name="Minimal Tag",
            space_id=test_space_id
        )
        assert minimal_tag.name == "Minimal Tag"
        assert minimal_tag.color == TagColor.GREY  # Default
        assert minimal_tag.description is None
    
    def test_tag_update_validation(self):
        """Test TagUpdate model validation."""
        # All fields optional in update
        update = TagUpdate()
        assert update.name is None
        assert update.color is None
        assert update.description is None
        assert update.is_archived is None
        
        # Partial update
        partial_update = TagUpdate(name="New Name")
        assert partial_update.name == "New Name"
        assert partial_update.color is None
        
        # Full update
        full_update = TagUpdate(
            name="Full Update",
            color=TagColor.PINK,
            description="New description",
            is_archived=True
        )
        assert full_update.name == "Full Update"
        assert full_update.color == TagColor.PINK
        assert full_update.description == "New description"
        assert full_update.is_archived is True
    
    def test_tag_properties(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test that tags have expected properties."""
        tag_data = TagCreate(
            name="Properties Test Tag",
            color=TagColor.GREEN,
            description="Testing tag properties",
            space_id=test_space_id
        )
        
        created_tag = sync_client.create_tag(tag_data)
        object_tracker.add_tag(created_tag.id)
        
        # Required properties
        assert hasattr(created_tag, 'id')
        assert hasattr(created_tag, 'name')
        assert hasattr(created_tag, 'color')
        assert hasattr(created_tag, 'usage_count')
        assert hasattr(created_tag, 'is_archived')
        
        # Optional properties
        assert hasattr(created_tag, 'description')
        
        # Validate types
        assert_valid_id(created_tag.id)
        assert isinstance(created_tag.name, str)
        assert isinstance(created_tag.color, TagColor)
        assert isinstance(created_tag.usage_count, int)
        assert isinstance(created_tag.is_archived, bool)


class TestTagErrorHandling:
    """Test error handling for tag operations."""
    
    def test_get_nonexistent_tag(self, sync_client: AnytypeClient):
        """Test getting a tag that doesn't exist."""
        with pytest.raises(APIError):
            sync_client.get_tag("nonexistent-tag-id")
    
    def test_update_nonexistent_tag(self, sync_client: AnytypeClient):
        """Test updating a tag that doesn't exist."""
        update_data = TagUpdate(name="Updated Name")
        with pytest.raises(APIError):
            sync_client.update_tag("nonexistent-tag-id", update_data)
    
    def test_delete_nonexistent_tag(self, sync_client: AnytypeClient):
        """Test deleting a tag that doesn't exist."""
        with pytest.raises(APIError):
            sync_client.delete_tag("nonexistent-tag-id")
    
    def test_list_tags_invalid_space(self, sync_client: AnytypeClient):
        """Test listing tags from an invalid space."""
        with pytest.raises(APIError):
            sync_client.list_tags("nonexistent-space-id")
    
    def test_create_tag_invalid_space(self, sync_client: AnytypeClient):
        """Test creating a tag in an invalid space."""
        tag_data = TagCreate(
            name="Invalid Space Tag",
            space_id="nonexistent-space-id"
        )
        
        with pytest.raises(APIError):
            sync_client.create_tag(tag_data)


class TestTagPagination:
    """Test pagination for tag operations."""
    
    def test_tag_pagination_basic(
        self, 
        sync_client: AnytypeClient, 
        test_space_id: str
    ):
        """Test basic pagination for listing tags."""
        # Create pagination params
        params = PaginationParams(limit=2, offset=0)
        
        # Get first page
        first_page = sync_client.list_tags(test_space_id, params)
        assert isinstance(first_page, list)
        assert len(first_page) <= 2
        
        # Get second page
        params.offset = 2
        second_page = sync_client.list_tags(test_space_id, params)
        assert isinstance(second_page, list)
        
        # If both pages have results, they should be different
        if len(first_page) > 0 and len(second_page) > 0:
            first_ids = {tag.id for tag in first_page}
            second_ids = {tag.id for tag in second_page}
            # Should not have overlapping IDs
            assert not first_ids.intersection(second_ids)
    
    def test_tag_sorting(
        self, 
        sync_client: AnytypeClient, 
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test sorting tags by name."""
        # Create multiple tags with sortable names
        tag_names = ["Alpha Tag", "Beta Tag", "Gamma Tag"]
        created_tags = []
        
        for name in tag_names:
            tag_data = TagCreate(
                name=name,
                color=TagColor.BLUE,
                space_id=test_space_id
            )
            created_tag = sync_client.create_tag(tag_data)
            created_tags.append(created_tag)
            object_tracker.add_tag(created_tag.id)
        
        # List with sorting
        params = PaginationParams(
            limit=10,
            sort_by="name",
            sort_direction="asc"
        )
        
        sorted_tags = sync_client.list_tags(test_space_id, params)
        
        # Find our created tags in the results
        our_tags = [tag for tag in sorted_tags if tag.name in tag_names]
        
        # Should be in alphabetical order
        if len(our_tags) >= 2:
            names = [tag.name for tag in our_tags]
            assert names == sorted(names)


class TestTagIntegration:
    """Test integration between tags and other operations."""
    
    def test_tag_in_space_context(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        test_space,
        object_tracker: ObjectTracker
    ):
        """Test that tags are properly associated with their space."""
        # Create a tag
        tag_data = TagCreate(
            name="Space Integration Test Tag",
            color=TagColor.ORANGE,
            description="Testing space-tag relationship",
            space_id=test_space_id
        )
        
        created_tag = sync_client.create_tag(tag_data)
        object_tracker.add_tag(created_tag.id)
        
        # Verify the tag was created
        assert_valid_id(created_tag.id)
        
        # Tag should appear when listing all tags in the space
        all_tags = sync_client.list_tags(test_space_id)
        tag_ids = [tag.id for tag in all_tags]
        assert created_tag.id in tag_ids
    
    def test_tag_lifecycle(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test complete lifecycle of a tag."""
        # 1. Create
        tag_data = TagCreate(
            name="Lifecycle Test Tag",
            color=TagColor.PURPLE,
            description="Testing complete tag lifecycle",
            space_id=test_space_id
        )
        created_tag = sync_client.create_tag(tag_data)
        object_tracker.add_tag(created_tag.id)
        assert created_tag.name == "Lifecycle Test Tag"
        assert created_tag.color == TagColor.PURPLE
        
        # 2. Read
        retrieved_tag = sync_client.get_tag(created_tag.id)
        assert retrieved_tag.id == created_tag.id
        
        # 3. Update
        update_data = TagUpdate(
            name="Updated Lifecycle Tag",
            color=TagColor.PINK,
            description="Updated description"
        )
        updated_tag = sync_client.update_tag(created_tag.id, update_data)
        assert updated_tag.name == "Updated Lifecycle Tag"
        assert updated_tag.color == TagColor.PINK
        
        # 4. Archive
        archive_data = TagUpdate(is_archived=True)
        archived_tag = sync_client.update_tag(created_tag.id, archive_data)
        assert archived_tag.is_archived is True
        
        # 5. Final verification
        final_tag = sync_client.get_tag(created_tag.id)
        assert final_tag.is_archived is True
        assert final_tag.name == "Updated Lifecycle Tag"
        assert final_tag.color == TagColor.PINK
    
    def test_tag_color_consistency(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test that tag colors remain consistent across operations."""
        # Test each color
        for color in [TagColor.RED, TagColor.GREEN, TagColor.BLUE]:
            tag_data = TagCreate(
                name=f"Color Test {color.value}",
                color=color,
                space_id=test_space_id
            )
            
            # Create tag
            created_tag = sync_client.create_tag(tag_data)
            object_tracker.add_tag(created_tag.id)
            assert created_tag.color == color
            
            # Retrieve tag
            retrieved_tag = sync_client.get_tag(created_tag.id)
            assert retrieved_tag.color == color
            
            # Update tag (keep same color)
            update_data = TagUpdate(description=f"Updated {color.value} tag")
            updated_tag = sync_client.update_tag(created_tag.id, update_data)
            assert updated_tag.color == color  # Should remain unchanged