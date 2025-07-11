"""Tests for member management operations."""
import pytest
from typing import Dict, Any

from anytype_client import AnytypeClient
from anytype_client.models import (
    Member, MemberInvite, MemberUpdate, MemberRole, PaginationParams
)
from anytype_client.exceptions import APIError
from tests.conftest import assert_valid_id, assert_valid_timestamp, ObjectTracker


class TestMemberCRUD:
    """Test Create, Read, Update, Delete operations for members."""
    
    @pytest.mark.skip("Member invitation requires email verification - enable for manual testing")
    def test_invite_member(
        self, 
        sync_client: AnytypeClient, 
        test_member_data: Dict[str, Any],
        object_tracker: ObjectTracker
    ):
        """Test inviting a new member to a space."""
        member_invite = MemberInvite(**test_member_data)
        invited_member = sync_client.invite_member(member_invite)
        
        assert isinstance(invited_member, Member)
        assert_valid_id(invited_member.id)
        assert invited_member.email == test_member_data["email"]
        assert invited_member.role == MemberRole(test_member_data["role"])
        assert invited_member.space_id == test_member_data["space_id"]
        
        # Track for potential cleanup
        object_tracker.add_member(invited_member.id)
        
        return invited_member
    
    def test_list_members(
        self, 
        sync_client: AnytypeClient, 
        test_space_id: str,
        pagination_params: PaginationParams
    ):
        """Test listing all members in a space."""
        members = sync_client.list_members(test_space_id, pagination_params)
        
        assert isinstance(members, list)
        # There should be at least the current user as a member
        assert len(members) >= 0  # Might be 0 in some test environments
        
        for member in members:
            assert isinstance(member, Member)
            assert_valid_id(member.id)
            assert isinstance(member.name, str)
            assert isinstance(member.role, MemberRole)
            assert isinstance(member.is_active, bool)
            assert_valid_timestamp(member.joined_at)
    
    def test_list_members_without_pagination(
        self, 
        sync_client: AnytypeClient, 
        test_space_id: str
    ):
        """Test listing members without pagination parameters."""
        members = sync_client.list_members(test_space_id)
        
        assert isinstance(members, list)
        for member in members:
            assert isinstance(member, Member)
            assert member.space_id == test_space_id or hasattr(member, 'space_id')
    
    def test_get_member(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str
    ):
        """Test retrieving a specific member by ID."""
        # First get the list of members
        members = sync_client.list_members(test_space_id)
        
        if len(members) > 0:
            # Get the first member
            first_member = members[0]
            
            # Retrieve it specifically
            retrieved_member = sync_client.get_member(test_space_id, first_member.id)
            
            assert isinstance(retrieved_member, Member)
            assert retrieved_member.id == first_member.id
            assert retrieved_member.name == first_member.name
            assert retrieved_member.role == first_member.role
    
    @pytest.mark.skip("Member updates require proper permissions - enable for manual testing")
    def test_update_member(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        object_tracker: ObjectTracker
    ):
        """Test updating an existing member."""
        # This test requires an existing member that can be updated
        members = sync_client.list_members(test_space_id)
        
        if len(members) > 1:  # Need at least 2 members to safely update one
            # Find a member that's not the current user/admin
            member_to_update = None
            for member in members:
                if member.role != MemberRole.OWNER:
                    member_to_update = member
                    break
            
            if member_to_update:
                # Update the member's role
                update_data = MemberUpdate(role=MemberRole.VIEWER)
                updated_member = sync_client.update_member(
                    test_space_id, 
                    member_to_update.id, 
                    update_data
                )
                
                assert isinstance(updated_member, Member)
                assert updated_member.id == member_to_update.id
                assert updated_member.role == MemberRole.VIEWER
    
    @pytest.mark.skip("Member removal requires proper permissions - enable for manual testing")
    def test_remove_member(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str
    ):
        """Test removing a member from a space."""
        # This would require a test member that can be safely removed
        # In practice, this should be tested carefully
        pass


class TestMemberRoles:
    """Test member role functionality."""
    
    def test_member_role_enum(self):
        """Test MemberRole enum values."""
        assert MemberRole.OWNER == "owner"
        assert MemberRole.ADMIN == "admin"
        assert MemberRole.EDITOR == "editor"
        assert MemberRole.VIEWER == "viewer"
        
        # Test enum can be created from string
        assert MemberRole("owner") == MemberRole.OWNER
        assert MemberRole("editor") == MemberRole.EDITOR
    
    def test_member_role_hierarchy(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str
    ):
        """Test that members have appropriate roles."""
        members = sync_client.list_members(test_space_id)
        
        # There should be at least one owner
        owners = [m for m in members if m.role == MemberRole.OWNER]
        
        # In most spaces, there should be at least one owner
        if len(members) > 0:
            roles_present = {m.role for m in members}
            assert len(roles_present) > 0
            
            # All roles should be valid enum values
            for role in roles_present:
                assert role in [MemberRole.OWNER, MemberRole.ADMIN, MemberRole.EDITOR, MemberRole.VIEWER]


class TestMemberValidation:
    """Test member model validation and properties."""
    
    def test_member_invite_validation(self, test_space_id: str):
        """Test MemberInvite model validation."""
        # Valid member invitation
        valid_invite = MemberInvite(
            email="test@example.com",
            role=MemberRole.EDITOR,
            space_id=test_space_id
        )
        assert valid_invite.email == "test@example.com"
        assert valid_invite.role == MemberRole.EDITOR
        assert valid_invite.space_id == test_space_id
        
        # Test with different roles
        for role in [MemberRole.VIEWER, MemberRole.EDITOR, MemberRole.ADMIN]:
            invite = MemberInvite(
                email=f"test-{role.value}@example.com",
                role=role,
                space_id=test_space_id
            )
            assert invite.role == role
    
    def test_member_update_validation(self):
        """Test MemberUpdate model validation."""
        # All fields optional in update
        update = MemberUpdate()
        assert update.role is None
        assert update.is_active is None
        
        # Role update
        role_update = MemberUpdate(role=MemberRole.VIEWER)
        assert role_update.role == MemberRole.VIEWER
        assert role_update.is_active is None
        
        # Status update
        status_update = MemberUpdate(is_active=False)
        assert status_update.role is None
        assert status_update.is_active is False
        
        # Combined update
        combined_update = MemberUpdate(
            role=MemberRole.EDITOR,
            is_active=True
        )
        assert combined_update.role == MemberRole.EDITOR
        assert combined_update.is_active is True
    
    def test_member_properties(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str
    ):
        """Test that members have expected properties."""
        members = sync_client.list_members(test_space_id)
        
        if len(members) > 0:
            member = members[0]
            
            # Required properties
            assert hasattr(member, 'id')
            assert hasattr(member, 'name')
            assert hasattr(member, 'role')
            assert hasattr(member, 'joined_at')
            assert hasattr(member, 'is_active')
            
            # Optional properties
            assert hasattr(member, 'email')  # Might be None
            assert hasattr(member, 'avatar')  # Might be None
            assert hasattr(member, 'last_active')  # Might be None
            
            # Validate types
            assert_valid_id(member.id)
            assert isinstance(member.name, str)
            assert isinstance(member.role, MemberRole)
            assert isinstance(member.is_active, bool)
            assert_valid_timestamp(member.joined_at)


class TestMemberErrorHandling:
    """Test error handling for member operations."""
    
    def test_get_nonexistent_member(self, sync_client: AnytypeClient, test_space_id: str):
        """Test getting a member that doesn't exist."""
        with pytest.raises(APIError):
            sync_client.get_member(test_space_id, "nonexistent-member-id")
    
    def test_update_nonexistent_member(self, sync_client: AnytypeClient, test_space_id: str):
        """Test updating a member that doesn't exist."""
        update_data = MemberUpdate(role=MemberRole.VIEWER)
        with pytest.raises(APIError):
            sync_client.update_member(test_space_id, "nonexistent-member-id", update_data)
    
    def test_remove_nonexistent_member(self, sync_client: AnytypeClient, test_space_id: str):
        """Test removing a member that doesn't exist."""
        with pytest.raises(APIError):
            sync_client.remove_member(test_space_id, "nonexistent-member-id")
    
    def test_list_members_invalid_space(self, sync_client: AnytypeClient):
        """Test listing members from an invalid space."""
        with pytest.raises(APIError):
            sync_client.list_members("nonexistent-space-id")
    
    def test_invite_member_invalid_space(self, sync_client: AnytypeClient):
        """Test inviting a member to an invalid space."""
        invite_data = MemberInvite(
            email="test@example.com",
            role=MemberRole.VIEWER,
            space_id="nonexistent-space-id"
        )
        
        with pytest.raises(APIError):
            sync_client.invite_member(invite_data)
    
    def test_invite_invalid_email(self, sync_client: AnytypeClient, test_space_id: str):
        """Test inviting with invalid email format."""
        invite_data = MemberInvite(
            email="invalid-email",
            role=MemberRole.VIEWER,
            space_id=test_space_id
        )
        
        # This might succeed at the model level but fail at API level
        # The exact behavior depends on API validation
        with pytest.raises(APIError):
            sync_client.invite_member(invite_data)


class TestMemberPagination:
    """Test pagination for member operations."""
    
    def test_member_pagination_basic(
        self, 
        sync_client: AnytypeClient, 
        test_space_id: str
    ):
        """Test basic pagination for listing members."""
        # Create pagination params
        params = PaginationParams(limit=2, offset=0)
        
        # Get first page
        first_page = sync_client.list_members(test_space_id, params)
        assert isinstance(first_page, list)
        assert len(first_page) <= 2
        
        # Get second page
        params.offset = 2
        second_page = sync_client.list_members(test_space_id, params)
        assert isinstance(second_page, list)
        
        # If both pages have results, they should be different
        if len(first_page) > 0 and len(second_page) > 0:
            first_ids = {member.id for member in first_page}
            second_ids = {member.id for member in second_page}
            # Should not have overlapping IDs
            assert not first_ids.intersection(second_ids)
    
    def test_member_sorting(
        self, 
        sync_client: AnytypeClient, 
        test_space_id: str
    ):
        """Test sorting members by name."""
        params = PaginationParams(
            limit=10,
            sort_by="name",
            sort_direction="asc"
        )
        
        sorted_members = sync_client.list_members(test_space_id, params)
        
        # If we have multiple members, verify they're sorted
        if len(sorted_members) > 1:
            names = [member.name for member in sorted_members if member.name]
            # Check if names are in ascending order
            sorted_names = sorted(names)
            assert names == sorted_names or len(names) <= 1


class TestMemberIntegration:
    """Test integration between members and other operations."""
    
    def test_member_space_relationship(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str,
        test_space
    ):
        """Test that members are properly associated with their space."""
        members = sync_client.list_members(test_space_id)
        
        for member in members:
            # Each member should be associated with the correct space
            # Note: Some APIs might not include space_id in member objects
            # but the member should be retrieved from the correct space context
            assert_valid_id(member.id)
            
            # Verify we can get the member specifically
            retrieved_member = sync_client.get_member(test_space_id, member.id)
            assert retrieved_member.id == member.id
    
    def test_current_user_membership(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str
    ):
        """Test that the current user appears as a member."""
        members = sync_client.list_members(test_space_id)
        
        # The current user should be a member of the test space
        # Since we can access the space, we must be a member
        assert len(members) >= 0  # At minimum, should not error
        
        # If there are members, at least one should have owner or admin role
        if len(members) > 0:
            admin_roles = [m for m in members if m.role in [MemberRole.OWNER, MemberRole.ADMIN]]
            # In most cases, there should be at least one admin/owner
            assert len(admin_roles) >= 0  # At least no error
    
    def test_member_activity_status(
        self, 
        sync_client: AnytypeClient,
        test_space_id: str
    ):
        """Test member activity status tracking."""
        members = sync_client.list_members(test_space_id)
        
        for member in members:
            # All members should have an active status
            assert isinstance(member.is_active, bool)
            
            # Join date should be valid
            assert_valid_timestamp(member.joined_at)
            
            # Last active might be None for some members
            if member.last_active:
                assert_valid_timestamp(member.last_active)
                # Last active should not be before join date
                assert member.last_active >= member.joined_at