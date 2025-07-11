"""Tests for template management operations."""
import pytest
from typing import Dict, Any

from anytype_client import AnytypeClient
from anytype_client.models import (
    Template, TemplateCreate, TemplateUpdate, TemplateType, ObjectType, PaginationParams
)
from anytype_client.exceptions import APIError
from tests.conftest import assert_valid_id, ObjectTracker


class TestTemplateCRUD:
    """Test Create, Read, Update, Delete operations for templates."""
    
    def test_create_template(
        self, 
        sync_client: AnytypeClient, 
        test_template_data: Dict[str, Any],
        object_tracker: ObjectTracker
    ):
        """Test creating a new template."""
        template_create = TemplateCreate(**test_template_data)
        created_template = sync_client.create_template(template_create)
        
        assert isinstance(created_template, Template)
        assert_valid_id(created_template.id)
        assert created_template.name == test_template_data["name"]
        assert created_template.description == test_template_data["description"]
        assert created_template.template_type == TemplateType(test_template_data["template_type"])
        assert created_template.is_archived is False
        assert created_template.is_default is False
        assert created_template.usage_count >= 0
        
        # Track for potential cleanup
        object_tracker.add_template(created_template.id)
        
        return created_template
    
    def test_get_template(
        self, 
        sync_client: AnytypeClient,
        test_template_data: Dict[str, Any],
        object_tracker: ObjectTracker
    ):
        """Test retrieving a template by ID."""
        # Create a template first
        template_create = TemplateCreate(**test_template_data)
        created_template = sync_client.create_template(template_create)
        object_tracker.add_template(created_template.id)
        
        # Now retrieve it
        retrieved_template = sync_client.get_template(created_template.id)
        
        assert isinstance(retrieved_template, Template)
        assert retrieved_template.id == created_template.id
        assert retrieved_template.name == created_template.name
        assert retrieved_template.template_type == created_template.template_type
        assert retrieved_template.description == created_template.description
    
    def test_update_template(
        self, 
        sync_client: AnytypeClient,
        test_template_data: Dict[str, Any],
        object_tracker: ObjectTracker
    ):
        """Test updating an existing template."""
        # Create a template first
        template_create = TemplateCreate(**test_template_data)
        created_template = sync_client.create_template(template_create)
        object_tracker.add_template(created_template.id)
        
        # Update it
        update_data = TemplateUpdate(
            name="Updated Test Template",
            description="Updated description for the test template",
            is_default=True
        )
        updated_template = sync_client.update_template(created_template.id, update_data)
        
        assert isinstance(updated_template, Template)
        assert updated_template.id == created_template.id
        assert updated_template.name == "Updated Test Template"
        assert updated_template.description == "Updated description for the test template"
        assert updated_template.is_default is True
    
    def test_delete_template(
        self, 
        sync_client: AnytypeClient,
        test_template_data: Dict[str, Any]
    ):
        """Test deleting a template."""
        # Create a template first
        template_create = TemplateCreate(**test_template_data)
        created_template = sync_client.create_template(template_create)
        
        # Delete it
        result = sync_client.delete_template(created_template.id)
        assert result is True
        
        # Verify it's deleted (should raise an error)
        with pytest.raises(APIError):
            sync_client.get_template(created_template.id)
    
    def test_archive_template(
        self, 
        sync_client: AnytypeClient,
        test_template_data: Dict[str, Any],
        object_tracker: ObjectTracker
    ):
        """Test archiving a template."""
        # Create a template first
        template_create = TemplateCreate(**test_template_data)
        created_template = sync_client.create_template(template_create)
        object_tracker.add_template(created_template.id)
        
        # Archive it
        update_data = TemplateUpdate(is_archived=True)
        archived_template = sync_client.update_template(created_template.id, update_data)
        
        assert archived_template.is_archived is True
        assert archived_template.id == created_template.id


class TestTemplateTypes:
    """Test template type functionality."""
    
    def test_template_type_enum(self):
        """Test TemplateType enum values."""
        template_types = [
            TemplateType.OBJECT,
            TemplateType.PAGE,
            TemplateType.SET,
            TemplateType.COLLECTION
        ]
        
        for template_type in template_types:
            assert isinstance(template_type, TemplateType)
            assert isinstance(template_type.value, str)
        
        # Test enum can be created from string
        assert TemplateType("object") == TemplateType.OBJECT
        assert TemplateType("page") == TemplateType.PAGE
        assert TemplateType("set") == TemplateType.SET
        assert TemplateType("collection") == TemplateType.COLLECTION
    
    def test_create_templates_with_different_types(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test creating templates with different types."""
        template_types = [
            TemplateType.PAGE,
            TemplateType.OBJECT,
            TemplateType.SET,
            TemplateType.COLLECTION
        ]
        
        for template_type in template_types:
            template_data = TemplateCreate(
                name=f"Test {template_type.value.title()} Template",
                description=f"Testing {template_type.value} template type",
                template_type=template_type,
                space_id=test_space_id,
                content={"type": template_type.value, "example": True}
            )
            
            created_template = sync_client.create_template(template_data)
            object_tracker.add_template(created_template.id)
            
            assert created_template.template_type == template_type
            assert created_template.name == f"Test {template_type.value.title()} Template"
    
    def test_template_with_object_type(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test creating a template associated with a specific object type."""
        template_data = TemplateCreate(
            name="Note Template",
            description="Template for note objects",
            template_type=TemplateType.OBJECT,
            object_type=ObjectType.NOTE,
            space_id=test_space_id,
            content={
                "sections": ["Title", "Content", "Tags"],
                "default_properties": {
                    "priority": "medium",
                    "status": "draft"
                }
            }
        )
        
        created_template = sync_client.create_template(template_data)
        object_tracker.add_template(created_template.id)
        
        assert created_template.template_type == TemplateType.OBJECT
        assert created_template.object_type == ObjectType.NOTE
        assert created_template.name == "Note Template"


class TestTemplateOperations:
    """Test template-specific operations and behaviors."""
    
    def test_list_templates(
        self, 
        sync_client: AnytypeClient, 
        test_space_id: str,
        pagination_params: PaginationParams
    ):
        """Test listing all templates in a space."""
        templates = sync_client.list_templates(test_space_id, pagination_params)
        
        assert isinstance(templates, list)
        # Templates might be empty, which is fine
        for template in templates:
            assert isinstance(template, Template)
            assert_valid_id(template.id)
            assert isinstance(template.name, str)
            assert isinstance(template.template_type, TemplateType)
    
    def test_list_templates_without_pagination(
        self, 
        sync_client: AnytypeClient, 
        test_space_id: str
    ):
        """Test listing templates without pagination parameters."""
        templates = sync_client.list_templates(test_space_id)
        
        assert isinstance(templates, list)
        for template in templates:
            assert isinstance(template, Template)
    
    def test_create_multiple_templates(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test creating multiple templates in a space."""
        template_names = ["Meeting Notes", "Project Plan", "Task List", "Report"]
        template_types = [TemplateType.PAGE, TemplateType.OBJECT, TemplateType.SET, TemplateType.COLLECTION]
        created_templates = []
        
        for name, template_type in zip(template_names, template_types):
            template_data = TemplateCreate(
                name=name,
                description=f"Template for {name.lower()}",
                template_type=template_type,
                space_id=test_space_id,
                content={"template_name": name, "type": template_type.value}
            )
            
            created_template = sync_client.create_template(template_data)
            created_templates.append(created_template)
            object_tracker.add_template(created_template.id)
        
        assert len(created_templates) == len(template_names)
        
        # Verify each template
        for i, template in enumerate(created_templates):
            assert template.name == template_names[i]
            assert template.template_type == template_types[i]
            assert_valid_id(template.id)
    
    def test_template_with_complex_content(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test creating a template with complex content structure."""
        complex_content = {
            "layout": {
                "sections": [
                    {"type": "header", "content": "Project Overview"},
                    {"type": "text", "placeholder": "Project description goes here..."},
                    {"type": "checklist", "items": ["Define goals", "Set timeline", "Assign tasks"]},
                    {"type": "table", "columns": ["Task", "Assignee", "Due Date", "Status"]}
                ]
            },
            "properties": {
                "priority": {"type": "select", "options": ["low", "medium", "high"]},
                "status": {"type": "select", "options": ["planning", "in-progress", "completed"]},
                "tags": {"type": "multi-select", "options": ["work", "personal", "urgent"]}
            },
            "metadata": {
                "version": "1.0",
                "author": "template-system",
                "created_for": "project-management"
            }
        }
        
        template_data = TemplateCreate(
            name="Complex Project Template",
            description="Advanced template with rich content structure",
            template_type=TemplateType.PAGE,
            space_id=test_space_id,
            content=complex_content
        )
        
        created_template = sync_client.create_template(template_data)
        object_tracker.add_template(created_template.id)
        
        assert created_template.content == complex_content
        assert created_template.name == "Complex Project Template"
    
    def test_template_with_icons(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test creating templates with emoji and image icons."""
        # Test with emoji icon
        emoji_template = TemplateCreate(
            name="Emoji Template",
            template_type=TemplateType.PAGE,
            space_id=test_space_id,
            icon_emoji="📋"
        )
        
        created_emoji = sync_client.create_template(emoji_template)
        object_tracker.add_template(created_emoji.id)
        
        assert created_emoji.icon_emoji == "📋"
        
        # Test with image icon (URL)
        image_template = TemplateCreate(
            name="Image Template",
            template_type=TemplateType.OBJECT,
            space_id=test_space_id,
            icon_image="https://example.com/template-icon.png"
        )
        
        created_image = sync_client.create_template(image_template)
        object_tracker.add_template(created_image.id)
        
        assert created_image.icon_image == "https://example.com/template-icon.png"


class TestTemplateValidation:
    """Test template model validation and properties."""
    
    def test_template_create_validation(self, test_space_id: str):
        """Test TemplateCreate model validation."""
        # Valid template creation
        valid_template = TemplateCreate(
            name="Valid Template",
            description="Valid description",
            template_type=TemplateType.PAGE,
            space_id=test_space_id
        )
        assert valid_template.name == "Valid Template"
        assert valid_template.template_type == TemplateType.PAGE
        assert valid_template.space_id == test_space_id
        
        # Template with object type
        object_template = TemplateCreate(
            name="Object Template",
            template_type=TemplateType.OBJECT,
            object_type=ObjectType.TASK,
            space_id=test_space_id,
            content={"default_status": "todo"}
        )
        assert object_template.object_type == ObjectType.TASK
        assert object_template.content == {"default_status": "todo"}
    
    def test_template_update_validation(self):
        """Test TemplateUpdate model validation."""
        # All fields optional in update
        update = TemplateUpdate()
        assert update.name is None
        assert update.template_type is None
        assert update.is_default is None
        assert update.is_archived is None
        
        # Partial update
        partial_update = TemplateUpdate(name="New Name")
        assert partial_update.name == "New Name"
        assert partial_update.template_type is None
        
        # Full update
        full_update = TemplateUpdate(
            name="Updated Template",
            description="Updated description",
            template_type=TemplateType.SET,
            object_type=ObjectType.COLLECTION,
            is_default=True,
            is_archived=False,
            content={"updated": True}
        )
        assert full_update.name == "Updated Template"
        assert full_update.template_type == TemplateType.SET
        assert full_update.object_type == ObjectType.COLLECTION
        assert full_update.is_default is True
        assert full_update.content == {"updated": True}
    
    def test_template_properties(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test that templates have expected properties."""
        template_data = TemplateCreate(
            name="Properties Test Template",
            description="Testing template properties",
            template_type=TemplateType.PAGE,
            space_id=test_space_id,
            content={"test": "data"}
        )
        
        created_template = sync_client.create_template(template_data)
        object_tracker.add_template(created_template.id)
        
        # Required properties
        assert hasattr(created_template, 'id')
        assert hasattr(created_template, 'name')
        assert hasattr(created_template, 'template_type')
        assert hasattr(created_template, 'is_default')
        assert hasattr(created_template, 'is_archived')
        assert hasattr(created_template, 'usage_count')
        assert hasattr(created_template, 'content')
        
        # Optional properties
        assert hasattr(created_template, 'description')
        assert hasattr(created_template, 'object_type')
        assert hasattr(created_template, 'icon_emoji')
        assert hasattr(created_template, 'icon_image')
        
        # Validate types
        assert_valid_id(created_template.id)
        assert isinstance(created_template.name, str)
        assert isinstance(created_template.template_type, TemplateType)
        assert isinstance(created_template.is_default, bool)
        assert isinstance(created_template.is_archived, bool)
        assert isinstance(created_template.usage_count, int)
        assert isinstance(created_template.content, dict)


class TestTemplateErrorHandling:
    """Test error handling for template operations."""
    
    def test_get_nonexistent_template(self, sync_client: AnytypeClient):
        """Test getting a template that doesn't exist."""
        with pytest.raises(APIError):
            sync_client.get_template("nonexistent-template-id")
    
    def test_update_nonexistent_template(self, sync_client: AnytypeClient):
        """Test updating a template that doesn't exist."""
        update_data = TemplateUpdate(name="Updated Name")
        with pytest.raises(APIError):
            sync_client.update_template("nonexistent-template-id", update_data)
    
    def test_delete_nonexistent_template(self, sync_client: AnytypeClient):
        """Test deleting a template that doesn't exist."""
        with pytest.raises(APIError):
            sync_client.delete_template("nonexistent-template-id")
    
    def test_list_templates_invalid_space(self, sync_client: AnytypeClient):
        """Test listing templates from an invalid space."""
        with pytest.raises(APIError):
            sync_client.list_templates("nonexistent-space-id")
    
    def test_create_template_invalid_space(self, sync_client: AnytypeClient):
        """Test creating a template in an invalid space."""
        template_data = TemplateCreate(
            name="Invalid Space Template",
            template_type=TemplateType.PAGE,
            space_id="nonexistent-space-id"
        )
        
        with pytest.raises(APIError):
            sync_client.create_template(template_data)


class TestTemplateIntegration:
    """Test integration between templates and other operations."""
    
    def test_template_in_space_context(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        test_space,
        object_tracker: ObjectTracker
    ):
        """Test that templates are properly associated with their space."""
        # Create a template
        template_data = TemplateCreate(
            name="Space Integration Test Template",
            description="Testing space-template relationship",
            template_type=TemplateType.PAGE,
            space_id=test_space_id,
            content={"space_integration": True}
        )
        
        created_template = sync_client.create_template(template_data)
        object_tracker.add_template(created_template.id)
        
        # Verify the template was created
        assert_valid_id(created_template.id)
        
        # Template should appear when listing all templates in the space
        all_templates = sync_client.list_templates(test_space_id)
        template_ids = [template.id for template in all_templates]
        assert created_template.id in template_ids
    
    def test_template_lifecycle(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test complete lifecycle of a template."""
        # 1. Create
        template_data = TemplateCreate(
            name="Lifecycle Test Template",
            description="Testing complete template lifecycle",
            template_type=TemplateType.OBJECT,
            object_type=ObjectType.NOTE,
            space_id=test_space_id,
            content={"lifecycle": "test", "version": 1}
        )
        created_template = sync_client.create_template(template_data)
        object_tracker.add_template(created_template.id)
        assert created_template.name == "Lifecycle Test Template"
        assert created_template.template_type == TemplateType.OBJECT
        
        # 2. Read
        retrieved_template = sync_client.get_template(created_template.id)
        assert retrieved_template.id == created_template.id
        
        # 3. Update
        update_data = TemplateUpdate(
            name="Updated Lifecycle Template",
            description="Updated description",
            is_default=True,
            content={"lifecycle": "test", "version": 2, "updated": True}
        )
        updated_template = sync_client.update_template(created_template.id, update_data)
        assert updated_template.name == "Updated Lifecycle Template"
        assert updated_template.is_default is True
        
        # 4. Archive
        archive_data = TemplateUpdate(is_archived=True)
        archived_template = sync_client.update_template(created_template.id, archive_data)
        assert archived_template.is_archived is True
        
        # 5. Final verification
        final_template = sync_client.get_template(created_template.id)
        assert final_template.is_archived is True
        assert final_template.name == "Updated Lifecycle Template"
        assert final_template.is_default is True
    
    def test_default_template_management(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test managing default templates."""
        # Create a template
        template_data = TemplateCreate(
            name="Default Template Test",
            template_type=TemplateType.PAGE,
            space_id=test_space_id
        )
        created_template = sync_client.create_template(template_data)
        object_tracker.add_template(created_template.id)
        
        # Initially not default
        assert created_template.is_default is False
        
        # Make it default
        update_data = TemplateUpdate(is_default=True)
        default_template = sync_client.update_template(created_template.id, update_data)
        assert default_template.is_default is True
        
        # Remove default status
        update_data = TemplateUpdate(is_default=False)
        non_default_template = sync_client.update_template(created_template.id, update_data)
        assert non_default_template.is_default is False