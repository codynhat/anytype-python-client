"""Data models for the Anytype API."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List as ListType, Optional, Union, Literal
from pydantic import BaseModel, Field


# Enums for various types
class SpaceStatus(str, Enum):
    """Status of a space in Anytype."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ObjectType(str, Enum):
    """Types of objects in Anytype."""

    NOTE = "note"
    TASK = "task"
    BOOKMARK = "bookmark"
    COLLECTION = "collection"
    SET = "set"
    PROFILE = "profile"
    SPACE = "space"
    TYPE = "type"


class RelationFormat(str, Enum):
    """Formats for relation values.

    Based on API documentation: https://developers.anytype.io/docs/reference/2025-05-20/create-property
    """

    TEXT = "text"
    NUMBER = "number"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    DATE = "date"
    FILES = "files"
    CHECKBOX = "checkbox"
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"
    OBJECTS = "objects"

    # Legacy aliases for backward compatibility
    SHORT_TEXT = "text"
    LONG_TEXT = "text"
    EMOJI = "emoji"
    OBJECT = "object"
    TAGS = "tags"
    FILE = "file"
    STATUS = "status"


class LayoutType(str, Enum):
    """Layout types for objects.

    Based on API documentation: https://developers.anytype.io/docs/reference/2025-05-20/create-type
    """

    BASIC = "basic"
    PROFILE = "profile"
    ACTION = "action"
    NOTE = "note"

    # Legacy aliases for backward compatibility
    TODO = "action"
    SET = "basic"
    COLLECTION = "basic"
    SPACE = "basic"
    BOOKMARK = "basic"


# Base Models
class BaseAnytypeModel(BaseModel):
    """Base model for all Anytype models with common fields."""

    id: str = Field(..., description="Unique identifier")
    created_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp"
    )
    last_modified_date: Optional[datetime] = Field(None, description="Last modification timestamp")
    space_id: Optional[str] = Field(None, description="ID of the containing space")


# Space Models
class Space(BaseAnytypeModel):
    """Represents an Anytype space.

    The API returns spaces in the following format:
    {
        "object": "space",
        "id": "...",
        "name": "...",
        "icon": null,
        "description": "",
        "gateway_url": "...",
        "network_id": "..."
    }
    """

    object: str = Field("space", description="Type of object, always 'space'")
    name: str = Field(..., description="Name of the space")
    description: str = Field("", description="Space description")
    icon: Optional[str] = Field(None, description="Emoji or URL icon for the space")
    gateway_url: str = Field(..., description="Gateway URL for the space")
    network_id: str = Field(..., description="Network ID of the space")

    # For backward compatibility
    @property
    def icon_emoji(self) -> Optional[str]:
        """Get the emoji icon if it's an emoji."""
        if self.icon and len(self.icon) <= 2:  # Simple check for emoji
            return self.icon
        return None

    @property
    def icon_image(self) -> Optional[str]:
        """Get the icon URL if it's a URL."""
        if self.icon and self.icon.startswith(("http://", "https://")):
            return self.icon
        return None


class SpaceCreate(BaseModel):
    """Data for creating a new space."""

    name: str = Field(..., description="Name of the space")
    description: Optional[str] = Field(None, description="Space description")
    icon_emoji: Optional[str] = Field(None, description="Emoji icon for the space")


class SpaceUpdate(BaseModel):
    """Data for updating an existing space."""

    name: Optional[str] = Field(None, description="Updated name of the space")
    description: Optional[str] = Field(None, description="Updated space description")
    icon_emoji: Optional[str] = Field(None, description="Updated emoji icon for the space")


# Object Models
class ObjectLink(BaseModel):
    """Represents a link to another object."""

    id: str
    type: Optional[ObjectType] = None
    title: Optional[str] = None


class PropertyValue(BaseModel):
    """Represents a property value with its type information.

    Based on API documentation: https://developers.anytype.io/docs/reference/2025-05-20/create-object
    """

    key: str = Field(..., description="Property key")
    value: Any = Field(..., description="Property value")

    # For backward compatibility
    @property
    def type(self) -> RelationFormat:
        """Get the property format type."""
        # This is a simplified mapping - actual format should be determined from property definition
        return RelationFormat.TEXT


class Property(BaseModel):
    """Represents a property definition."""

    id: str
    name: str
    description: Optional[str] = None
    format: RelationFormat
    is_required: bool = False
    is_readonly: bool = False
    is_hidden: bool = False
    is_archived: bool = False
    default_value: Optional[Any] = None
    source: ListType[str] = Field(default_factory=list)


class ObjectCreate(BaseModel):
    """Model for creating a new Anytype object.

    Based on API documentation: https://developers.anytype.io/docs/reference/2025-05-20/create-object
    """

    name: str = Field(..., description="Name of the object")
    type_key: str = Field(..., description="The type key for the object (e.g., 'page', 'note')")
    layout: Optional[LayoutType] = Field(None, description="Layout type for the object")
    space_id: str = Field(..., description="ID of the space")
    properties: Optional[ListType[Dict[str, Any]]] = Field(
        None, description="Properties as array of key-value objects"
    )
    icon: Optional[Dict[str, Any]] = Field(None, description="Icon configuration")
    body: Optional[str] = Field(None, description="Body content (supports Markdown)")
    description: Optional[str] = Field(None, description="Object description")
    source_url: Optional[str] = Field(None, description="Source URL (required for bookmarks)")
    template_id: Optional[str] = Field(None, description="Template identifier")

    # For backward compatibility
    @property
    def icon_emoji(self) -> Optional[str]:
        """Get emoji from icon configuration."""
        if self.icon and self.icon.get("format") == "emoji":
            return self.icon.get("emoji")
        return None

    @property
    def icon_image(self) -> Optional[str]:
        """Get image URL from icon configuration."""
        if self.icon and self.icon.get("format") == "image":
            return self.icon.get("url")
        return None


class ObjectUpdate(BaseModel):
    """Model for updating an existing Anytype object.

    Based on API documentation: https://developers.anytype.io/docs/reference/2025-05-20/update-object
    """

    name: Optional[str] = Field(None, description="Updated name of the object")
    properties: Optional[ListType[Dict[str, Any]]] = Field(
        None, description="Properties as array of key-value objects"
    )
    icon: Optional[Dict[str, Any]] = Field(None, description="Updated icon configuration")
    body: Optional[str] = Field(None, description="Updated body content")
    description: Optional[str] = Field(None, description="Updated object description")
    source_url: Optional[str] = Field(None, description="Updated source URL")
    is_archived: Optional[bool] = Field(None, description="Whether to archive the object")
    is_favorite: Optional[bool] = Field(None, description="Whether to favorite the object")

    # For backward compatibility
    @property
    def icon_emoji(self) -> Optional[str]:
        """Get emoji from icon configuration."""
        if self.icon and self.icon.get("format") == "emoji":
            return self.icon.get("emoji")
        return None

    @property
    def icon_image(self) -> Optional[str]:
        """Get image URL from icon configuration."""
        if self.icon and self.icon.get("format") == "image":
            return self.icon.get("url")
        return None


class Object(BaseAnytypeModel):
    """Represents an Anytype object.

    Based on API documentation: https://developers.anytype.io/docs/reference/2025-05-20/get-object
    """

    name: str = Field(..., description="Name of the object")
    type: Dict[str, Any] = Field(..., description="Type object with id, key, name, etc.")
    layout: Union[LayoutType, str] = Field(..., description="Layout type")
    properties: ListType[Dict[str, Any]] = Field(
        default_factory=list, description="Properties as array of objects"
    )
    snippet: Optional[str] = Field(None, description="Text snippet/preview")
    archived: bool = Field(False, description="Whether the object is archived")
    icon: Optional[Dict[str, Any]] = Field(None, description="Icon configuration")
    is_favorite: Optional[bool] = Field(None, description="Whether the object is favorited")
    is_archived: Optional[bool] = Field(None, description="Whether the object is archived")
    body: Optional[str] = Field(None, description="Body content in Markdown format")
    description: Optional[str] = Field(None, description="Object description")
    source_url: Optional[str] = Field(None, description="Source URL for bookmarks")
    last_opened_date: Optional[datetime] = Field(None, description="Last opened timestamp")

    # Computed properties for backward compatibility
    @property
    def type_key(self) -> Optional[str]:
        """Get the type key from the type object."""
        return self.type.get("key") if isinstance(self.type, dict) else None

    @property
    def type_name(self) -> Optional[str]:
        """Get the type name from the type object."""
        return self.type.get("name") if isinstance(self.type, dict) else None

    @property
    def icon_emoji(self) -> Optional[str]:
        """Get emoji from icon configuration."""
        if self.icon and self.icon.get("format") == "emoji":
            return self.icon.get("emoji")
        return None

    @property
    def icon_image(self) -> Optional[str]:
        """Get image URL from icon configuration."""
        if self.icon and self.icon.get("format") == "image":
            return self.icon.get("url")
        return None


# Type Models
class TypeLayout(BaseModel):
    """Layout configuration for a custom type."""

    type: LayoutType
    is_collection: bool = False
    default_template_id: Optional[str] = None


class ObjectTypeDefinition(BaseAnytypeModel):
    """Represents a custom object type in Anytype."""

    name: str
    description: Optional[str] = None
    icon_emoji: Optional[str] = None
    layout: Union[TypeLayout, LayoutType, str]  # API returns string, flexible handling
    default_template_id: Optional[str] = None
    is_archived: bool = False
    recommended_layout: Optional[LayoutType] = None
    recommended_relations: ListType[str] = Field(default_factory=list)


# Request/Response Models
class APIResponse(BaseModel):
    """Standard API response format."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class PaginationParams(BaseModel):
    """Pagination parameters for list operations."""

    limit: int = 20
    offset: int = 0
    sort_by: Optional[str] = None
    sort_direction: Literal["asc", "desc"] = "asc"


class SearchQuery(BaseModel):
    """Search query parameters."""

    text: Optional[str] = None
    type: Optional[ObjectType] = None
    space_id: Optional[str] = None
    filters: ListType[Dict[str, Any]] = Field(default_factory=list)
    sort: ListType[Dict[str, Any]] = Field(default_factory=list)
    limit: int = 20
    offset: int = 0


# Authentication Models
class AuthChallenge(BaseModel):
    """Authentication challenge response."""

    challenge_id: str
    expires_at: datetime


class APIKey(BaseModel):
    """API key information."""

    key: str
    name: str
    created_at: datetime
    last_used_at: Optional[datetime] = None


# Event Models
class EventType(str, Enum):
    """Types of events that can be received from the Anytype API."""

    OBJECT_CREATED = "object_created"
    OBJECT_UPDATED = "object_updated"
    OBJECT_DELETED = "object_deleted"
    SPACE_CREATED = "space_created"
    SPACE_UPDATED = "space_updated"
    SPACE_DELETED = "space_deleted"


class Event(BaseModel):
    """Represents an event from the Anytype API."""

    type: EventType
    object_id: str
    space_id: str
    timestamp: datetime
    data: Dict[str, Any]


# List Models
class ListItem(BaseModel):
    """Represents an item in a list."""

    id: str
    object_id: str
    position: int
    added_at: datetime


class List(BaseAnytypeModel):
    """Represents a list in Anytype."""

    name: str
    description: Optional[str] = None
    items: ListType[ListItem] = Field(default_factory=list)
    is_archived: bool = False
    total_items: int = 0


class ListCreate(BaseModel):
    """Model for creating a new list."""

    name: str
    description: Optional[str] = None
    space_id: str


class ListUpdate(BaseModel):
    """Model for updating an existing list."""

    name: Optional[str] = None
    description: Optional[str] = None
    is_archived: Optional[bool] = None


# Member Models
class MemberRole(str, Enum):
    """Member roles in a space."""

    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class Member(BaseModel):
    """Represents a member in a space."""

    id: str
    name: str
    identity: Optional[str] = None  # Network identity instead of email
    global_name: Optional[str] = None  # Global username like "beaucronin.any"
    role: MemberRole
    icon: Optional[str] = None  # API uses 'icon' not 'avatar'
    status: str = "active"  # API uses 'status' not 'is_active'
    space_id: Optional[str] = None  # For backward compatibility

    # For backward compatibility
    @property
    def email(self) -> Optional[str]:
        """Get email from global_name if it looks like an email."""
        if self.global_name and "@" in self.global_name:
            return self.global_name
        return None

    @property
    def avatar(self) -> Optional[str]:
        """Alias for icon for backward compatibility."""
        return self.icon

    @property
    def is_active(self) -> bool:
        """Check if member is active based on status."""
        return self.status == "active"

    @property
    def joined_at(self) -> datetime:
        """Provide a fake joined_at for backward compatibility."""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc)

    @property
    def last_active(self) -> Optional[datetime]:
        """Provide None for last_active for backward compatibility."""
        return None


class MemberInvite(BaseModel):
    """Model for inviting a member to a space."""

    email: str
    role: MemberRole
    space_id: str


class MemberUpdate(BaseModel):
    """Model for updating a member's details."""

    role: Optional[MemberRole] = None
    is_active: Optional[bool] = None


# Property Models (extending existing Property model)
class PropertyCreate(BaseModel):
    """Model for creating a new property."""

    name: str
    description: Optional[str] = None
    format: RelationFormat
    is_required: bool = False
    is_readonly: bool = False
    is_hidden: bool = False
    default_value: Optional[Any] = None
    source: ListType[str] = Field(default_factory=list)
    space_id: str


class PropertyUpdate(BaseModel):
    """Model for updating an existing property."""

    name: Optional[str] = None
    description: Optional[str] = None
    format: Optional[RelationFormat] = None
    is_required: Optional[bool] = None
    is_readonly: Optional[bool] = None
    is_hidden: Optional[bool] = None
    is_archived: Optional[bool] = None
    default_value: Optional[Any] = None
    source: Optional[ListType[str]] = None


# Tag Models
class TagColor(str, Enum):
    """Predefined colors for tags."""

    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    PURPLE = "purple"
    PINK = "pink"
    GREY = "grey"


class Tag(BaseAnytypeModel):
    """Represents a tag in Anytype."""

    name: str
    color: TagColor = TagColor.GREY
    description: Optional[str] = None
    usage_count: int = 0
    is_archived: bool = False


class TagCreate(BaseModel):
    """Model for creating a new tag."""

    name: str
    color: TagColor = TagColor.GREY
    description: Optional[str] = None
    space_id: str


class TagUpdate(BaseModel):
    """Model for updating an existing tag."""

    name: Optional[str] = None
    color: Optional[TagColor] = None
    description: Optional[str] = None
    is_archived: Optional[bool] = None


# Template Models
class TemplateType(str, Enum):
    """Types of templates."""

    OBJECT = "object"
    PAGE = "page"
    SET = "set"
    COLLECTION = "collection"


class Template(BaseAnytypeModel):
    """Represents a template in Anytype."""

    name: str
    description: Optional[str] = None
    template_type: TemplateType
    object_type: Optional[ObjectType] = None
    icon_emoji: Optional[str] = None
    icon_image: Optional[str] = None
    is_default: bool = False
    is_archived: bool = False
    usage_count: int = 0
    content: Dict[str, Any] = Field(default_factory=dict)


class TemplateCreate(BaseModel):
    """Model for creating a new template."""

    name: str
    description: Optional[str] = None
    template_type: TemplateType
    object_type: Optional[ObjectType] = None
    icon_emoji: Optional[str] = None
    icon_image: Optional[str] = None
    space_id: str
    content: Dict[str, Any] = Field(default_factory=dict)


class TemplateUpdate(BaseModel):
    """Model for updating an existing template."""

    name: Optional[str] = None
    description: Optional[str] = None
    template_type: Optional[TemplateType] = None
    object_type: Optional[ObjectType] = None
    icon_emoji: Optional[str] = None
    icon_image: Optional[str] = None
    is_default: Optional[bool] = None
    is_archived: Optional[bool] = None
    content: Optional[Dict[str, Any]] = None


# Extended response models for list operations
class ListResponse(BaseModel):
    """Response model for list operations with pagination."""

    data: ListType[Dict[str, Any]]
    pagination: Dict[str, Any]


class MemberListResponse(BaseModel):
    """Response model for member list operations."""

    data: ListType[Dict[str, Any]]
    pagination: Dict[str, Any]


# Type aliases for better type hints
ObjectID = str
SpaceID = str
RelationID = str
TypeID = str
ListID = str
MemberID = str
PropertyID = str
TagID = str
TemplateID = str
