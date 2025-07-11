"""
Main client implementation for the Anytype API.

This module provides both synchronous and asynchronous clients for interacting with the Anytype API.
"""
import logging
import os
from typing import Any, Dict, Generic, List as ListType, Optional, Type, TypeVar, Union
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel, ValidationError as PydanticValidationError

from .exceptions import (
    APIError,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServerError,
    TimeoutError,
    TooManyRequestsError,
    UnauthorizedError,
    ValidationError,
)
from .models import (
    Object,
    ObjectCreate,
    ObjectTypeDefinition,
    Space,
    SpaceCreate,
    SpaceUpdate,
    PaginationParams,
    Property,
    SearchQuery,
    AuthChallenge,
    APIKey,
    List,
    ListCreate,
    ListUpdate,
    Member,
    MemberInvite,
    MemberUpdate,
    PropertyCreate,
    PropertyUpdate,
    Tag,
    TagCreate,
    TagUpdate,
    Template,
    TemplateCreate,
    TemplateUpdate,
)

# Type variable for generic model parsing
T = TypeVar("T", bound=BaseModel)

# Configure logging
logger = logging.getLogger(__name__)


class BaseClient(Generic[T]):
    """Base client with shared functionality for sync and async clients."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:31009/v1/",
        timeout: float = 30.0,
        **client_kwargs: Any,
    ) -> None:
        """Initialize the base client.

        Args:
            api_key: Your Anytype API key. If not provided, will be read from ANYTYPE_API_KEY environment variable.
            base_url: The base URL for the Anytype API. Defaults to localhost:31009/v1/.
            timeout: Request timeout in seconds.
            **client_kwargs: Additional arguments to pass to the underlying HTTP client.
        """
        self.api_key = api_key or os.getenv("ANYTYPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Either pass it directly or set the ANYTYPE_API_KEY environment variable."
            )

        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self._client_kwargs = client_kwargs

    def _get_headers(self) -> Dict[str, str]:
        """Get the default headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Anytype-Version": "2025-05-20",
        }

    def _process_response(
        self, response: httpx.Response, model: Optional[Type[T]] = None
    ) -> Union[Dict[str, Any], T]:
        """Process an API response.

        Args:
            response: The HTTP response from the API.
            model: Optional Pydantic model to parse the response data into.

        Returns:
            The parsed response data, either as a dictionary or as an instance of the provided model.

        Raises:
            AuthenticationError: If the request is not authenticated.
            ForbiddenError: If the request is not authorized.
            NotFoundError: If the requested resource is not found.
            RateLimitError: If the rate limit is exceeded.
            ServerError: If the server encounters an error.
            ValidationError: If the response data is invalid.
            ValueError: If the response data cannot be parsed as JSON.
        """
        try:
            response.raise_for_status()
            data = response.json()

            if model:
                try:
                    return model(**data)
                except PydanticValidationError as e:
                    raise ValidationError(f"Failed to validate response data: {e}") from e

            return data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    logger.error(f"400 Bad Request error response: {error_data}")
                    raise BadRequestError(
                        error_data.get("error", "Bad Request"),
                        status_code=400,
                        response=e.response,
                    )
                except ValueError:
                    raise BadRequestError("Bad Request", status_code=400, response=e.response)
            elif e.response.status_code == 401:
                raise UnauthorizedError("Unauthorized", status_code=401, response=e.response)
            elif e.response.status_code == 403:
                raise ForbiddenError("Forbidden", status_code=403, response=e.response)
            elif e.response.status_code == 404:
                raise NotFoundError("Not Found", status_code=404, response=e.response)
            elif e.response.status_code == 409:
                raise ConflictError("Conflict", status_code=409, response=e.response)
            elif e.response.status_code == 429:
                raise TooManyRequestsError(
                    "Too Many Requests", status_code=429, response=e.response
                )
            elif 500 <= e.response.status_code < 600:
                raise ServerError(
                    f"Server Error: {e.response.status_code}",
                    status_code=e.response.status_code,
                    response=e.response,
                )
            else:
                raise APIError(
                    f"Unexpected status code: {e.response.status_code}",
                    status_code=e.response.status_code,
                    response=e.response,
                )
        except httpx.TimeoutException as e:
            raise TimeoutError("Request timed out") from e
        except httpx.RequestError as e:
            raise APIError(f"Request failed: {str(e)}") from e
        except ValueError as e:
            raise ValueError(f"Failed to parse response as JSON: {e}") from e


class AnytypeClient(BaseClient[Any]):
    """Synchronous client for the Anytype API."""

    def __init__(self, *args, **kwargs):
        """Initialize the synchronous client."""
        super().__init__(*args, **kwargs)
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self._get_headers(),
            **self._client_kwargs,
        )

    def __enter__(self):
        """Support for context manager protocol."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources when exiting context manager."""
        self.close()

    def close(self):
        """Close the underlying HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        model: Optional[Type[T]] = None,
    ) -> Union[Dict[str, Any], T, ListType[T]]:
        """Make an HTTP request to the Anytype API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: Request body as JSON
            model: Optional model to parse the response into

        Returns:
            The parsed API response.
        """
        url = urljoin(self.base_url, endpoint.lstrip("/"))
        logger.debug("Making %s request to %s", method, url)

        try:
            response = self._client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
            )
            return self._process_response(response, model=model)
        except httpx.RequestError as e:
            raise APIError(f"Request failed: {str(e)}")

    # Authentication methods
    def create_auth_challenge(self, app_name: str) -> AuthChallenge:
        """Create an authentication challenge.

        Args:
            app_name: Name of the application requesting access.

        Returns:
            AuthChallenge containing the challenge ID and expiration.
        """
        data = {"app_name": app_name}
        response = self.request("POST", "auth/challenges", json_data=data)
        return AuthChallenge.model_validate(response)

    def create_api_key(self, challenge_id: str, code: str) -> APIKey:
        """Create an API key using a challenge code.

        Args:
            challenge_id: The challenge ID from create_auth_challenge.
            code: The verification code shown in the Anytype app.

        Returns:
            APIKey containing the API key and metadata.
        """
        data = {"challenge_id": challenge_id, "code": code}
        response = self.request("POST", "auth/api_keys", json_data=data)
        return APIKey.model_validate(response)

    # Space methods
    def list_spaces(self) -> ListType[Space]:
        """List all available spaces.

        Returns:
            List of Space objects.

        The API returns a response in the following format:
        {
            "data": [
                {
                    "object": "space",
                    "id": "...",
                    "name": "...",
                    "icon": null,
                    "description": "",
                    "gateway_url": "...",
                    "network_id": "..."
                },
                ...
            ],
            "pagination": {
                "total": 4,
                "offset": 0,
                "limit": 100,
                "has_more": false
            }
        }
        """
        response = self.request("GET", "spaces")

        # Handle the actual API response format with 'data' key
        if isinstance(response, dict) and "data" in response and isinstance(response["data"], list):
            spaces = []
            for space_data in response["data"]:
                try:
                    spaces.append(Space.model_validate(space_data))
                except Exception:
                    logger.error(f"Failed to parse space data: {space_data}")
                    raise
            return spaces

        # Fallback for other formats (shouldn't be needed with current API)
        if isinstance(response, list):
            return [Space.model_validate(space) for space in response]

        if isinstance(response, dict) and "spaces" in response:
            return [Space.model_validate(space) for space in response["spaces"]]

        logger.warning(f"Unexpected response format: {type(response)}")
        return []

    def get_space(self, space_id: str) -> Space:
        """Get details for a specific space.

        Args:
            space_id: ID of the space to retrieve.

        Returns:
            Space object with details.
        """
        response = self.request("GET", f"spaces/{space_id}")
        # Handle nested response format
        if isinstance(response, dict) and "space" in response:
            return Space.model_validate(response["space"])
        return Space.model_validate(response)

    def create_space(self, space_data: SpaceCreate) -> Space:
        """Create a new space.

        Args:
            space_data: Data for creating the space.

        Returns:
            The created space.
        """
        response = self.request(
            "POST", "spaces", json_data=space_data.model_dump(exclude_unset=True)
        )
        return Space.model_validate(response)

    def update_space(self, space_id: str, updates: SpaceUpdate) -> Space:
        """Update an existing space.

        Args:
            space_id: ID of the space to update.
            updates: Data for updating the space.

        Returns:
            The updated space.
        """
        response = self.request(
            "PATCH", f"spaces/{space_id}", json_data=updates.model_dump(exclude_unset=True)
        )
        return Space.model_validate(response)

    def delete_space(self, space_id: str) -> bool:
        """Delete a space.

        Args:
            space_id: ID of the space to delete.

        Returns:
            True if the space was deleted successfully.
        """
        self.request("DELETE", f"spaces/{space_id}")
        return True

    # Object methods
    def get_object(self, space_id: str, object_id: str) -> Object:
        """Get an object by ID.

        Args:
            space_id: ID of the space containing the object.
            object_id: ID of the object to retrieve.

        Returns:
            Object with the specified ID.
        """
        response = self.request("GET", f"spaces/{space_id}/objects/{object_id}")
        # Handle nested response format
        if isinstance(response, dict) and "object" in response:
            return Object.model_validate(response["object"])
        return Object.model_validate(response)

    def create_object(self, space_id: str, obj: ObjectCreate) -> Object:
        """Create a new object.

        Args:
            space_id: ID of the space to create the object in.
            obj: Object to create.

        Returns:
            The created object with server-assigned fields.
        """
        # Exclude space_id from the request body since it's in the URL
        data = obj.model_dump(exclude_unset=True, exclude={"space_id"})
        response = self.request("POST", f"spaces/{space_id}/objects", json_data=data)
        # Handle nested response format
        if isinstance(response, dict) and "object" in response:
            return Object.model_validate(response["object"])
        return Object.model_validate(response)

    def update_object(self, space_id: str, object_id: str, updates: Dict[str, Any]) -> Object:
        """Update an existing object.

        Args:
            space_id: ID of the space containing the object.
            object_id: ID of the object to update.
            updates: Dictionary of fields to update.

        Returns:
            The updated object.
        """
        response = self.request(
            "PATCH", f"spaces/{space_id}/objects/{object_id}", json_data=updates
        )
        if isinstance(response, dict) and "object" in response:
            return Object.model_validate(response["object"])
        return Object.model_validate(response)

    def delete_object(self, space_id: str, object_id: str) -> bool:
        """Delete an object.

        Args:
            space_id: ID of the space containing the object.
            object_id: ID of the object to delete.

        Returns:
            True if deletion was successful.
        """
        self.request("DELETE", f"spaces/{space_id}/objects/{object_id}")
        return True

    # Search methods
    def search_objects(self, query: SearchQuery) -> ListType[Object]:
        """Search for objects globally across all accessible spaces.

        Args:
            query: Search query parameters.

        Returns:
            List of matching objects.
        """
        response = self.request(
            "POST", "search", json_data=query.model_dump(exclude_unset=True, mode="json")
        )

        # Handle different response formats
        if isinstance(response, dict):
            if "results" in response:
                return [Object.model_validate(obj) for obj in response["results"]]
            elif "data" in response:
                return [Object.model_validate(obj) for obj in response["data"]]
            elif isinstance(response.get("objects"), list):
                return [Object.model_validate(obj) for obj in response["objects"]]

        return []

    # Type methods
    def list_types(self, space_id: str) -> ListType[ObjectTypeDefinition]:
        """List all available object types in a space.

        Args:
            space_id: ID of the space to list types from.

        Returns:
            List of ObjectTypeDefinition objects.
        """
        response = self.request("GET", f"spaces/{space_id}/types")

        # Handle paginated response format
        if isinstance(response, dict) and "data" in response and isinstance(response["data"], list):
            return [ObjectTypeDefinition.model_validate(t) for t in response["data"]]
        elif isinstance(response, dict) and "types" in response:
            return [ObjectTypeDefinition.model_validate(t) for t in response["types"]]
        elif isinstance(response, list):
            return [ObjectTypeDefinition.model_validate(t) for t in response]

        return []

    def get_type(self, space_id: str, type_id: str) -> ObjectTypeDefinition:
        """Get details for a specific type.

        Args:
            space_id: ID of the space containing the type.
            type_id: ID of the type to retrieve.

        Returns:
            ObjectTypeDefinition object with details.
        """
        response = self.request("GET", f"spaces/{space_id}/types/{type_id}")

        # Handle nested response format
        if isinstance(response, dict) and "type" in response:
            return ObjectTypeDefinition.model_validate(response["type"])
        return ObjectTypeDefinition.model_validate(response)

    # List methods
    def list_lists(
        self, space_id: str, params: Optional[PaginationParams] = None
    ) -> ListType[List]:
        """List all lists in a space.

        Args:
            space_id: ID of the space to list lists from.
            params: Optional pagination parameters.

        Returns:
            List of List objects.
        """
        endpoint = f"spaces/{space_id}/lists"
        query_params = params.model_dump() if params else {}
        response = self.request("GET", endpoint, params=query_params)

        # Handle paginated response format
        if isinstance(response, dict) and "data" in response and isinstance(response["data"], list):
            lists = []
            for list_data in response["data"]:
                try:
                    lists.append(List.model_validate(list_data))
                except Exception:
                    logger.error(f"Failed to parse list data: {list_data}")
                    raise
            return lists

        # Fallback for other formats
        if isinstance(response, list):
            return [List.model_validate(list_item) for list_item in response]

        logger.warning(f"Unexpected response format: {type(response)}")
        return []

    def get_list(self, list_id: str) -> List:
        """Get details for a specific list.

        Args:
            list_id: ID of the list to retrieve.

        Returns:
            List object with details.
        """
        response = self.request("GET", f"lists/{list_id}")
        return List.model_validate(response)

    def create_list(self, list_data: ListCreate) -> List:
        """Create a new list.

        Args:
            list_data: List creation data.

        Returns:
            The created list.
        """
        endpoint = f"spaces/{list_data.space_id}/lists"
        response = self.request(
            "POST", endpoint, json_data=list_data.model_dump(exclude_unset=True)
        )
        return List.model_validate(response)

    def update_list(self, list_id: str, updates: ListUpdate) -> List:
        """Update an existing list.

        Args:
            list_id: ID of the list to update.
            updates: List update data.

        Returns:
            The updated list.
        """
        response = self.request(
            "PATCH", f"lists/{list_id}", json_data=updates.model_dump(exclude_unset=True)
        )
        return List.model_validate(response)

    def delete_list(self, list_id: str) -> bool:
        """Delete a list.

        Args:
            list_id: ID of the list to delete.

        Returns:
            True if deletion was successful.
        """
        self.request("DELETE", f"lists/{list_id}")
        return True

    # Member methods
    def list_members(
        self, space_id: str, params: Optional[PaginationParams] = None
    ) -> ListType[Member]:
        """List all members in a space.

        Args:
            space_id: ID of the space to list members from.
            params: Optional pagination parameters.

        Returns:
            List of Member objects.
        """
        endpoint = f"spaces/{space_id}/members"
        query_params = params.model_dump() if params else {}
        response = self.request("GET", endpoint, params=query_params)

        # Handle paginated response format
        if isinstance(response, dict) and "data" in response and isinstance(response["data"], list):
            members = []
            for member_data in response["data"]:
                try:
                    members.append(Member.model_validate(member_data))
                except Exception:
                    logger.error(f"Failed to parse member data: {member_data}")
                    raise
            return members

        # Fallback for other formats
        if isinstance(response, list):
            return [Member.model_validate(member) for member in response]

        logger.warning(f"Unexpected response format: {type(response)}")
        return []

    def get_member(self, space_id: str, member_id: str) -> Member:
        """Get details for a specific member.

        Args:
            space_id: ID of the space.
            member_id: ID of the member to retrieve.

        Returns:
            Member object with details.
        """
        response = self.request("GET", f"spaces/{space_id}/members/{member_id}")
        return Member.model_validate(response)

    def invite_member(self, invite_data: MemberInvite) -> Member:
        """Invite a new member to a space.

        Args:
            invite_data: Member invitation data.

        Returns:
            The invited member.
        """
        endpoint = f"spaces/{invite_data.space_id}/members"
        response = self.request(
            "POST", endpoint, json_data=invite_data.model_dump(exclude_unset=True)
        )
        return Member.model_validate(response)

    def update_member(self, space_id: str, member_id: str, updates: MemberUpdate) -> Member:
        """Update an existing member.

        Args:
            space_id: ID of the space.
            member_id: ID of the member to update.
            updates: Member update data.

        Returns:
            The updated member.
        """
        response = self.request(
            "PATCH",
            f"spaces/{space_id}/members/{member_id}",
            json_data=updates.model_dump(exclude_unset=True),
        )
        return Member.model_validate(response)

    def remove_member(self, space_id: str, member_id: str) -> bool:
        """Remove a member from a space.

        Args:
            space_id: ID of the space.
            member_id: ID of the member to remove.

        Returns:
            True if removal was successful.
        """
        self.request("DELETE", f"spaces/{space_id}/members/{member_id}")
        return True

    # Property methods
    def list_properties(
        self, space_id: str, params: Optional[PaginationParams] = None
    ) -> ListType[Property]:
        """List all properties in a space.

        Args:
            space_id: ID of the space to list properties from.
            params: Optional pagination parameters.

        Returns:
            List of Property objects.
        """
        endpoint = f"spaces/{space_id}/properties"
        query_params = params.model_dump() if params else {}
        response = self.request("GET", endpoint, params=query_params)

        # Handle paginated response format
        if isinstance(response, dict) and "data" in response and isinstance(response["data"], list):
            properties = []
            for property_data in response["data"]:
                try:
                    properties.append(Property.model_validate(property_data))
                except Exception:
                    logger.error(f"Failed to parse property data: {property_data}")
                    raise
            return properties

        # Fallback for other formats
        if isinstance(response, list):
            return [Property.model_validate(prop) for prop in response]

        logger.warning(f"Unexpected response format: {type(response)}")
        return []

    def get_property(self, space_id: str, property_id: str) -> Property:
        """Get details for a specific property.

        Args:
            space_id: ID of the space containing the property.
            property_id: ID of the property to retrieve.

        Returns:
            Property object with details.
        """
        response = self.request("GET", f"spaces/{space_id}/properties/{property_id}")
        if isinstance(response, dict) and "property" in response:
            return Property.model_validate(response["property"])
        return Property.model_validate(response)

    def create_property(self, property_data: PropertyCreate) -> Property:
        """Create a new property.

        Args:
            property_data: Property creation data.

        Returns:
            The created property.
        """
        endpoint = f"spaces/{property_data.space_id}/properties"
        response = self.request(
            "POST", endpoint, json_data=property_data.model_dump(exclude_unset=True, mode="json")
        )
        if isinstance(response, dict) and "property" in response:
            return Property.model_validate(response["property"])
        return Property.model_validate(response)

    def update_property(self, space_id: str, property_id: str, updates: PropertyUpdate) -> Property:
        """Update an existing property.

        Args:
            space_id: ID of the space containing the property.
            property_id: ID of the property to update.
            updates: Property update data.

        Returns:
            The updated property.
        """
        response = self.request(
            "PATCH",
            f"spaces/{space_id}/properties/{property_id}",
            json_data=updates.model_dump(exclude_unset=True, mode="json"),
        )
        if isinstance(response, dict) and "property" in response:
            return Property.model_validate(response["property"])
        return Property.model_validate(response)

    def delete_property(self, space_id: str, property_id: str) -> bool:
        """Delete a property.

        Args:
            space_id: ID of the space containing the property.
            property_id: ID of the property to delete.

        Returns:
            True if deletion was successful.
        """
        self.request("DELETE", f"spaces/{space_id}/properties/{property_id}")
        return True

    # Tag methods
    def list_tags(self, space_id: str, params: Optional[PaginationParams] = None) -> ListType[Tag]:
        """List all tags in a space.

        Args:
            space_id: ID of the space to list tags from.
            params: Optional pagination parameters.

        Returns:
            List of Tag objects.
        """
        endpoint = f"spaces/{space_id}/tags"
        query_params = params.model_dump() if params else {}
        response = self.request("GET", endpoint, params=query_params)

        # Handle paginated response format
        if isinstance(response, dict) and "data" in response and isinstance(response["data"], list):
            tags = []
            for tag_data in response["data"]:
                try:
                    tags.append(Tag.model_validate(tag_data))
                except Exception:
                    logger.error(f"Failed to parse tag data: {tag_data}")
                    raise
            return tags

        # Fallback for other formats
        if isinstance(response, list):
            return [Tag.model_validate(tag) for tag in response]

        logger.warning(f"Unexpected response format: {type(response)}")
        return []

    def get_tag(self, tag_id: str) -> Tag:
        """Get details for a specific tag.

        Args:
            tag_id: ID of the tag to retrieve.

        Returns:
            Tag object with details.
        """
        response = self.request("GET", f"tags/{tag_id}")
        return Tag.model_validate(response)

    def create_tag(self, tag_data: TagCreate) -> Tag:
        """Create a new tag.

        Args:
            tag_data: Tag creation data.

        Returns:
            The created tag.
        """
        endpoint = f"spaces/{tag_data.space_id}/tags"
        response = self.request("POST", endpoint, json_data=tag_data.model_dump(exclude_unset=True))
        return Tag.model_validate(response)

    def update_tag(self, tag_id: str, updates: TagUpdate) -> Tag:
        """Update an existing tag.

        Args:
            tag_id: ID of the tag to update.
            updates: Tag update data.

        Returns:
            The updated tag.
        """
        response = self.request(
            "PATCH", f"tags/{tag_id}", json_data=updates.model_dump(exclude_unset=True)
        )
        return Tag.model_validate(response)

    def delete_tag(self, tag_id: str) -> bool:
        """Delete a tag.

        Args:
            tag_id: ID of the tag to delete.

        Returns:
            True if deletion was successful.
        """
        self.request("DELETE", f"tags/{tag_id}")
        return True

    # Template methods
    def list_templates(
        self, space_id: str, params: Optional[PaginationParams] = None
    ) -> ListType[Template]:
        """List all templates in a space.

        Args:
            space_id: ID of the space to list templates from.
            params: Optional pagination parameters.

        Returns:
            List of Template objects.
        """
        endpoint = f"spaces/{space_id}/templates"
        query_params = params.model_dump() if params else {}
        response = self.request("GET", endpoint, params=query_params)

        # Handle paginated response format
        if isinstance(response, dict) and "data" in response and isinstance(response["data"], list):
            templates = []
            for template_data in response["data"]:
                try:
                    templates.append(Template.model_validate(template_data))
                except Exception:
                    logger.error(f"Failed to parse template data: {template_data}")
                    raise
            return templates

        # Fallback for other formats
        if isinstance(response, list):
            return [Template.model_validate(template) for template in response]

        logger.warning(f"Unexpected response format: {type(response)}")
        return []

    def get_template(self, template_id: str) -> Template:
        """Get details for a specific template.

        Args:
            template_id: ID of the template to retrieve.

        Returns:
            Template object with details.
        """
        response = self.request("GET", f"templates/{template_id}")
        return Template.model_validate(response)

    def create_template(self, template_data: TemplateCreate) -> Template:
        """Create a new template.

        Args:
            template_data: Template creation data.

        Returns:
            The created template.
        """
        endpoint = f"spaces/{template_data.space_id}/templates"
        response = self.request(
            "POST", endpoint, json_data=template_data.model_dump(exclude_unset=True)
        )
        return Template.model_validate(response)

    def update_template(self, template_id: str, updates: TemplateUpdate) -> Template:
        """Update an existing template.

        Args:
            template_id: ID of the template to update.
            updates: Template update data.

        Returns:
            The updated template.
        """
        response = self.request(
            "PATCH", f"templates/{template_id}", json_data=updates.model_dump(exclude_unset=True)
        )
        return Template.model_validate(response)

    def delete_template(self, template_id: str) -> bool:
        """Delete a template.

        Args:
            template_id: ID of the template to delete.

        Returns:
            True if deletion was successful.
        """
        self.request("DELETE", f"templates/{template_id}")
        return True


class AsyncAnytypeClient(BaseClient[Any]):
    """Asynchronous client for the Anytype API."""

    def __init__(self, *args, **kwargs):
        """Initialize the asynchronous client."""
        super().__init__(*args, **kwargs)
        self._client = None

    async def __aenter__(self):
        """Support for async context manager protocol."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources when exiting async context manager."""
        await self.close()

    async def connect(self):
        """Initialize the async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self._get_headers(),
                **self._client_kwargs,
            )

    async def close(self):
        """Close the underlying async HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        model: Optional[Type[T]] = None,
    ) -> Union[Dict[str, Any], T, ListType[T]]:
        """Make an async HTTP request to the Anytype API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: Request body as JSON
            model: Optional model to parse the response into

        Returns:
            The parsed API response.
        """
        if self._client is None:
            await self.connect()

        url = urljoin(self.base_url, endpoint.lstrip("/"))
        logger.debug("Making async %s request to %s", method, url)

        try:
            response = await self._client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
            )
            return self._process_response(response, model=model)
        except httpx.RequestError as e:
            raise APIError(f"Request failed: {str(e)}")

    # Authentication methods
    async def create_auth_challenge(self, app_name: str) -> AuthChallenge:
        """Create an authentication challenge (async)."""
        data = {"app_name": app_name}
        response = await self.request("POST", "auth/challenges", json_data=data)
        return AuthChallenge.model_validate(response)

    async def create_api_key(self, challenge_id: str, code: str) -> APIKey:
        """Create an API key using a challenge code (async)."""
        data = {"challenge_id": challenge_id, "code": code}
        response = await self.request("POST", "auth/api_keys", json_data=data)
        return APIKey.model_validate(response)

    # Space methods (async versions)
    async def list_spaces(self) -> ListType[Space]:
        """List all available spaces (async).

        The API returns a response in the following format:
        {
            "data": [
                {
                    "object": "space",
                    "id": "...",
                    "name": "...",
                    "icon": null,
                    "description": "",
                    "gateway_url": "...",
                    "network_id": "..."
                },
                ...
            ],
            "pagination": {
                "total": 4,
                "offset": 0,
                "limit": 100,
                "has_more": false
            }
        }
        """
        response = await self.request("GET", "spaces")

        # Handle the actual API response format with 'data' key
        if isinstance(response, dict) and "data" in response and isinstance(response["data"], list):
            spaces = []
            for space_data in response["data"]:
                try:
                    spaces.append(Space.model_validate(space_data))
                except Exception:
                    logger.error(f"Failed to parse space data: {space_data}")
                    raise
            return spaces

        # Fallback for other formats (shouldn't be needed with current API)
        if isinstance(response, list):
            return [Space.model_validate(space) for space in response]

        if isinstance(response, dict) and "spaces" in response:
            return [Space.model_validate(space) for space in response["spaces"]]

        logger.warning(f"Unexpected response format: {type(response)}")
        return []

    async def get_space(self, space_id: str) -> Space:
        """Get details for a specific space (async)."""
        response = await self.request("GET", f"spaces/{space_id}")
        # Handle nested response format
        if isinstance(response, dict) and "space" in response:
            return Space.model_validate(response["space"])
        return Space.model_validate(response)

    async def create_space(self, space_data: SpaceCreate) -> Space:
        """Create a new space (async).

        Args:
            space_data: Data for creating the space.

        Returns:
            The created space.
        """
        response = await self.request(
            "POST", "spaces", json_data=space_data.model_dump(exclude_unset=True)
        )
        return Space.model_validate(response)

    async def update_space(self, space_id: str, updates: SpaceUpdate) -> Space:
        """Update an existing space (async).

        Args:
            space_id: ID of the space to update.
            updates: Data for updating the space.

        Returns:
            The updated space.
        """
        response = await self.request(
            "PATCH", f"spaces/{space_id}", json_data=updates.model_dump(exclude_unset=True)
        )
        return Space.model_validate(response)

    async def delete_space(self, space_id: str) -> bool:
        """Delete a space (async).

        Args:
            space_id: ID of the space to delete.

        Returns:
            True if the space was deleted successfully.
        """
        await self.request("DELETE", f"spaces/{space_id}")
        return True

    # Object methods (async versions)
    async def get_object(self, space_id: str, object_id: str) -> Object:
        """Get an object by ID (async)."""
        response = await self.request("GET", f"spaces/{space_id}/objects/{object_id}")
        # Handle nested response format
        if isinstance(response, dict) and "object" in response:
            return Object.model_validate(response["object"])
        return Object.model_validate(response)

    async def create_object(self, space_id: str, obj: ObjectCreate) -> Object:
        """Create a new object (async)."""
        # Exclude space_id from the request body since it's in the URL
        data = obj.model_dump(exclude_unset=True, exclude={"space_id"})
        response = await self.request("POST", f"spaces/{space_id}/objects", json_data=data)
        # Handle nested response format
        if isinstance(response, dict) and "object" in response:
            return Object.model_validate(response["object"])
        return Object.model_validate(response)

    async def update_object(self, space_id: str, object_id: str, updates: Dict[str, Any]) -> Object:
        """Update an existing object (async)."""
        response = await self.request(
            "PATCH", f"spaces/{space_id}/objects/{object_id}", json_data=updates
        )
        return Object.model_validate(response)

    async def delete_object(self, space_id: str, object_id: str) -> bool:
        """Delete an object (async)."""
        await self.request("DELETE", f"spaces/{space_id}/objects/{object_id}")
        return True

    # Search methods (async versions)
    async def search_objects(self, query: SearchQuery) -> ListType[Object]:
        """Search for objects globally across all accessible spaces (async)."""
        response = await self.request(
            "POST", "search", json_data=query.model_dump(exclude_unset=True, mode="json")
        )

        # Handle different response formats
        if isinstance(response, dict):
            if "results" in response:
                return [Object.model_validate(obj) for obj in response["results"]]
            elif "data" in response:
                return [Object.model_validate(obj) for obj in response["data"]]
            elif isinstance(response.get("objects"), list):
                return [Object.model_validate(obj) for obj in response["objects"]]

        return []

    # Type methods (async versions)
    async def list_types(self, space_id: str) -> ListType[ObjectTypeDefinition]:
        """List all available object types in a space (async)."""
        response = await self.request("GET", f"spaces/{space_id}/types")

        # Handle paginated response format
        if isinstance(response, dict) and "data" in response and isinstance(response["data"], list):
            return [ObjectTypeDefinition.model_validate(t) for t in response["data"]]
        elif isinstance(response, dict) and "types" in response:
            return [ObjectTypeDefinition.model_validate(t) for t in response["types"]]
        elif isinstance(response, list):
            return [ObjectTypeDefinition.model_validate(t) for t in response]

        return []

    async def get_type(self, space_id: str, type_id: str) -> ObjectTypeDefinition:
        """Get details for a specific type (async)."""
        response = await self.request("GET", f"spaces/{space_id}/types/{type_id}")

        # Handle nested response format
        if isinstance(response, dict) and "type" in response:
            return ObjectTypeDefinition.model_validate(response["type"])
        return ObjectTypeDefinition.model_validate(response)

    # List methods (async versions)
    async def list_lists(
        self, space_id: str, params: Optional[PaginationParams] = None
    ) -> ListType[List]:
        """List all lists in a space (async)."""
        endpoint = f"spaces/{space_id}/lists"
        query_params = params.model_dump() if params else {}
        response = await self.request("GET", endpoint, params=query_params)

        # Handle paginated response format
        if isinstance(response, dict) and "data" in response and isinstance(response["data"], list):
            lists = []
            for list_data in response["data"]:
                try:
                    lists.append(List.model_validate(list_data))
                except Exception:
                    logger.error(f"Failed to parse list data: {list_data}")
                    raise
            return lists

        # Fallback for other formats
        if isinstance(response, list):
            return [List.model_validate(list_item) for list_item in response]

        logger.warning(f"Unexpected response format: {type(response)}")
        return []

    async def get_list(self, list_id: str) -> List:
        """Get details for a specific list (async)."""
        response = await self.request("GET", f"lists/{list_id}")
        return List.model_validate(response)

    async def create_list(self, list_data: ListCreate) -> List:
        """Create a new list (async)."""
        endpoint = f"spaces/{list_data.space_id}/lists"
        response = await self.request(
            "POST", endpoint, json_data=list_data.model_dump(exclude_unset=True)
        )
        return List.model_validate(response)

    async def update_list(self, list_id: str, updates: ListUpdate) -> List:
        """Update an existing list (async)."""
        response = await self.request(
            "PATCH", f"lists/{list_id}", json_data=updates.model_dump(exclude_unset=True)
        )
        return List.model_validate(response)

    async def delete_list(self, list_id: str) -> bool:
        """Delete a list (async)."""
        await self.request("DELETE", f"lists/{list_id}")
        return True

    # Member methods (async versions)
    async def list_members(
        self, space_id: str, params: Optional[PaginationParams] = None
    ) -> ListType[Member]:
        """List all members in a space (async)."""
        endpoint = f"spaces/{space_id}/members"
        query_params = params.model_dump() if params else {}
        response = await self.request("GET", endpoint, params=query_params)

        # Handle paginated response format
        if isinstance(response, dict) and "data" in response and isinstance(response["data"], list):
            members = []
            for member_data in response["data"]:
                try:
                    members.append(Member.model_validate(member_data))
                except Exception:
                    logger.error(f"Failed to parse member data: {member_data}")
                    raise
            return members

        # Fallback for other formats
        if isinstance(response, list):
            return [Member.model_validate(member) for member in response]

        logger.warning(f"Unexpected response format: {type(response)}")
        return []

    async def get_member(self, space_id: str, member_id: str) -> Member:
        """Get details for a specific member (async)."""
        response = await self.request("GET", f"spaces/{space_id}/members/{member_id}")
        return Member.model_validate(response)

    async def invite_member(self, invite_data: MemberInvite) -> Member:
        """Invite a new member to a space (async)."""
        endpoint = f"spaces/{invite_data.space_id}/members"
        response = await self.request(
            "POST", endpoint, json_data=invite_data.model_dump(exclude_unset=True)
        )
        return Member.model_validate(response)

    async def update_member(self, space_id: str, member_id: str, updates: MemberUpdate) -> Member:
        """Update an existing member (async)."""
        response = await self.request(
            "PATCH",
            f"spaces/{space_id}/members/{member_id}",
            json_data=updates.model_dump(exclude_unset=True),
        )
        return Member.model_validate(response)

    async def remove_member(self, space_id: str, member_id: str) -> bool:
        """Remove a member from a space (async)."""
        await self.request("DELETE", f"spaces/{space_id}/members/{member_id}")
        return True

    # Property methods (async versions)
    async def list_properties(
        self, space_id: str, params: Optional[PaginationParams] = None
    ) -> ListType[Property]:
        """List all properties in a space (async)."""
        endpoint = f"spaces/{space_id}/properties"
        query_params = params.model_dump() if params else {}
        response = await self.request("GET", endpoint, params=query_params)

        # Handle paginated response format
        if isinstance(response, dict) and "data" in response and isinstance(response["data"], list):
            properties = []
            for property_data in response["data"]:
                try:
                    properties.append(Property.model_validate(property_data))
                except Exception:
                    logger.error(f"Failed to parse property data: {property_data}")
                    raise
            return properties

        # Fallback for other formats
        if isinstance(response, list):
            return [Property.model_validate(prop) for prop in response]

        logger.warning(f"Unexpected response format: {type(response)}")
        return []

    async def get_property(self, space_id: str, property_id: str) -> Property:
        """Get details for a specific property (async)."""
        response = await self.request("GET", f"spaces/{space_id}/properties/{property_id}")
        if isinstance(response, dict) and "property" in response:
            return Property.model_validate(response["property"])
        return Property.model_validate(response)

    async def create_property(self, property_data: PropertyCreate) -> Property:
        """Create a new property (async)."""
        endpoint = f"spaces/{property_data.space_id}/properties"
        response = await self.request(
            "POST", endpoint, json_data=property_data.model_dump(exclude_unset=True, mode="json")
        )
        if isinstance(response, dict) and "property" in response:
            return Property.model_validate(response["property"])
        return Property.model_validate(response)

    async def update_property(
        self, space_id: str, property_id: str, updates: PropertyUpdate
    ) -> Property:
        """Update an existing property (async)."""
        response = await self.request(
            "PATCH",
            f"spaces/{space_id}/properties/{property_id}",
            json_data=updates.model_dump(exclude_unset=True, mode="json"),
        )
        if isinstance(response, dict) and "property" in response:
            return Property.model_validate(response["property"])
        return Property.model_validate(response)

    async def delete_property(self, space_id: str, property_id: str) -> bool:
        """Delete a property (async)."""
        await self.request("DELETE", f"spaces/{space_id}/properties/{property_id}")
        return True

    # Tag methods (async versions)
    async def list_tags(
        self, space_id: str, params: Optional[PaginationParams] = None
    ) -> ListType[Tag]:
        """List all tags in a space (async)."""
        endpoint = f"spaces/{space_id}/tags"
        query_params = params.model_dump() if params else {}
        response = await self.request("GET", endpoint, params=query_params)

        # Handle paginated response format
        if isinstance(response, dict) and "data" in response and isinstance(response["data"], list):
            tags = []
            for tag_data in response["data"]:
                try:
                    tags.append(Tag.model_validate(tag_data))
                except Exception:
                    logger.error(f"Failed to parse tag data: {tag_data}")
                    raise
            return tags

        # Fallback for other formats
        if isinstance(response, list):
            return [Tag.model_validate(tag) for tag in response]

        logger.warning(f"Unexpected response format: {type(response)}")
        return []

    async def get_tag(self, tag_id: str) -> Tag:
        """Get details for a specific tag (async)."""
        response = await self.request("GET", f"tags/{tag_id}")
        return Tag.model_validate(response)

    async def create_tag(self, tag_data: TagCreate) -> Tag:
        """Create a new tag (async)."""
        endpoint = f"spaces/{tag_data.space_id}/tags"
        response = await self.request(
            "POST", endpoint, json_data=tag_data.model_dump(exclude_unset=True)
        )
        return Tag.model_validate(response)

    async def update_tag(self, tag_id: str, updates: TagUpdate) -> Tag:
        """Update an existing tag (async)."""
        response = await self.request(
            "PATCH", f"tags/{tag_id}", json_data=updates.model_dump(exclude_unset=True)
        )
        return Tag.model_validate(response)

    async def delete_tag(self, tag_id: str) -> bool:
        """Delete a tag (async)."""
        await self.request("DELETE", f"tags/{tag_id}")
        return True

    # Template methods (async versions)
    async def list_templates(
        self, space_id: str, params: Optional[PaginationParams] = None
    ) -> ListType[Template]:
        """List all templates in a space (async)."""
        endpoint = f"spaces/{space_id}/templates"
        query_params = params.model_dump() if params else {}
        response = await self.request("GET", endpoint, params=query_params)

        # Handle paginated response format
        if isinstance(response, dict) and "data" in response and isinstance(response["data"], list):
            templates = []
            for template_data in response["data"]:
                try:
                    templates.append(Template.model_validate(template_data))
                except Exception:
                    logger.error(f"Failed to parse template data: {template_data}")
                    raise
            return templates

        # Fallback for other formats
        if isinstance(response, list):
            return [Template.model_validate(template) for template in response]

        logger.warning(f"Unexpected response format: {type(response)}")
        return []

    async def get_template(self, template_id: str) -> Template:
        """Get details for a specific template (async)."""
        response = await self.request("GET", f"templates/{template_id}")
        return Template.model_validate(response)

    async def create_template(self, template_data: TemplateCreate) -> Template:
        """Create a new template (async)."""
        endpoint = f"spaces/{template_data.space_id}/templates"
        response = await self.request(
            "POST", endpoint, json_data=template_data.model_dump(exclude_unset=True)
        )
        return Template.model_validate(response)

    async def update_template(self, template_id: str, updates: TemplateUpdate) -> Template:
        """Update an existing template (async)."""
        response = await self.request(
            "PATCH", f"templates/{template_id}", json_data=updates.model_dump(exclude_unset=True)
        )
        return Template.model_validate(response)

    async def delete_template(self, template_id: str) -> bool:
        """Delete a template (async)."""
        await self.request("DELETE", f"templates/{template_id}")
        return True
