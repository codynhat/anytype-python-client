"""
Anytype Python Client - A Python client for the Anytype API.

This package provides a Pythonic interface to interact with the Anytype API,
offering both synchronous and asynchronous clients for seamless integration.
"""

from .client import AnytypeClient, AsyncAnytypeClient
from .exceptions import (
    AnytypeError,
    AuthenticationError,
    APIError,
    NotFoundError,
    ValidationError,
)
from .models import (
    Space,
    SpaceCreate,
    SpaceUpdate,
    Object,
    ObjectCreate,
    ObjectUpdate,
    Property,
    ObjectTypeDefinition,
    List,
    ListCreate,
    ListUpdate,
    ListItem,
    Member,
    MemberInvite,
    MemberUpdate,
    MemberRole,
    PropertyCreate,
    PropertyUpdate,
    Tag,
    TagCreate,
    TagUpdate,
    TagColor,
    Template,
    TemplateCreate,
    TemplateUpdate,
    TemplateType,
    PaginationParams,
    SearchQuery,
)

# For backward compatibility
Type = ObjectTypeDefinition

__version__ = "0.1.0"
__all__ = [
    "AnytypeError",
    "AnytypeClient",
    "AsyncAnytypeClient",
    "APIError",
    "AuthenticationError",
    "ValidationError",
    "Space",
    "SpaceCreate",
    "SpaceUpdate",
    "Object",
    "ObjectCreate",
    "ObjectUpdate",
    "ObjectTypeDefinition",
    "Property",
    "List",
    "ListCreate",
    "ListUpdate",
    "ListItem",
    "Member",
    "MemberInvite",
    "MemberUpdate",
    "MemberRole",
    "PropertyCreate",
    "PropertyUpdate",
    "Tag",
    "TagCreate",
    "TagUpdate",
    "TagColor",
    "Template",
    "TemplateCreate",
    "TemplateUpdate",
    "TemplateType",
    "PaginationParams",
    "SearchQuery",
    "Type",  # For backward compatibility
]
