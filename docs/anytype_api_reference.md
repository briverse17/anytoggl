# Anytype API Reference

> **Source:** [Anytype API Documentation](https://developers.anytype.io/docs/reference)  
> **API Version:** 2025-11-08  

This document summarizes all available endpoints in the Anytype API. The API enables interaction with Anytype's resources including spaces, objects, properties, types, templates, lists, members, and tags.

---

## Authentication

The Anytype API uses **Bearer Token (JWT)** authentication. All requests require an `Authorization` header with a valid API key.

```
Authorization: Bearer <your_api_key>
```

### Auth Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/auth/challenges` | Create Challenge - Generates a one-time authentication challenge. Requires `app_name` in request body. Returns a `challenge_id` and displays a 4-digit code in Anytype Desktop. |
| `POST` | `/v1/auth/api_keys` | Create API Key - After receiving `challenge_id`, submit the 4-digit code to verify and receive an `api_key` for subsequent requests. |

#### Auth Flow:
1. Call `POST /v1/auth/challenges` with `app_name` → receive `challenge_id`
2. User enters the 4-digit code displayed in Anytype Desktop
3. Call `POST /v1/auth/api_keys` with `challenge_id` and code → receive `api_key`

---

## Search Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/search` | **Search Global** - Executes a global search over all spaces accessible to the authenticated user. Supports `query`, optional `types` filter, and sort directives. Pagination via `offset` and `limit`. |
| `POST` | `/v1/spaces/:space_id/search` | **Search Space** - Performs a search within a single space. Accepts `query`, `types`, and sorting preferences. |

### Search Parameters:
- `query` - Search text (matches object name and snippet)
- `types` - Optional filter on types (e.g., 'page', 'task')
- `offset` / `limit` - Pagination parameters
- Default sort: descending by last modified date

---

## Spaces Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/spaces` | **List Spaces** - Retrieves paginated list of all spaces accessible by the authenticated user. Returns space ID, name, icon, and metadata. Supports dynamic filtering via query parameters (e.g., `?name[contains]=project`). |
| `POST` | `/v1/spaces` | **Create Space** - Creates a new space with `name` and `description`. Subject to rate limiting. Returns full space metadata. |
| `GET` | `/v1/spaces/:space_id` | **Get Space** - Fetches full details about a single space including name, icon, and various workspace IDs (home, archive, profile, etc.). |
| `PATCH` | `/v1/spaces/:space_id` | **Update Space** - Updates the name or description of an existing space. Returns updated space metadata. |

### Response Codes:
- `200` OK - Success
- `201` Created - Space created
- `400` Bad request
- `401` Unauthorized
- `404` Space not found
- `429` Rate limit exceeded
- `500` Internal server error

---

## Objects Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/spaces/:space_id/objects` | **List Objects** - Retrieves paginated list of objects in a space. Returns object ID, name, icon, type, snippet, layout, blocks, and details. Supports dynamic filtering (e.g., `?done=false`, `?created_date[gte]=2024-01-01`, `?tags[in]=urgent,important`). |
| `POST` | `/v1/spaces/:space_id/objects` | **Create Object** - Creates a new object. Payload includes: `name`, `icon`, `description`, `body` (Markdown), `source` (URL for bookmarks), `template`, and `type_key`. Subject to rate limiting. |
| `GET` | `/v1/spaces/:space_id/objects/:object_id` | **Get Object** - Fetches full details of a single object including metadata, blocks (text, files, properties, dataviews), timestamps, and linked member information. |
| `PATCH` | `/v1/spaces/:space_id/objects/:object_id` | **Update Object** - Updates an existing object with JSON payload. Returns full updated object data. Subject to rate limiting. |
| `DELETE` | `/v1/spaces/:space_id/objects/:object_id` | **Delete Object** - "Deletes" an object by marking it as archived. Returns object details after archival. Subject to rate limiting. |

### Object Response Codes:
- `200` OK - Success (get, update, delete)
- `201` Created - Object created
- `400` Bad request
- `401` Unauthorized
- `404` Resource not found
- `410` Resource deleted
- `429` Rate limit exceeded
- `500` Internal server error

---

## Lists Endpoints

Lists can be either **queries** or **collections**.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/spaces/:space_id/lists/:list_id/objects` | **Add Objects to List** - Adds one or more objects to a collection by submitting an array of object IDs. Collections only. |
| `DELETE` | `/v1/spaces/:space_id/lists/:list_id/objects/:object_id` | **Remove Object from List** - Removes an object from a collection. Does not delete the underlying object. |
| `GET` | `/v1/spaces/:space_id/lists/:list_id/views` | **Get List Views** - Returns paginated list of views defined for a list. Each view includes layout, filters, and sorting options. |
| `GET` | `/v1/spaces/:space_id/lists/:list_id/views/:view_id/objects` | **Get Objects in List** - Returns paginated list of objects in a list/view. Supports dynamic filtering (e.g., `?done=false`, `?tags[in]=urgent`). |

---

## Members Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/spaces/:space_id/members` | **List Members** - Returns paginated list of members in a space. Includes profile ID, name, icon, network identity, global name, status (joining, active), and role (Viewer, Editor, Owner). Supports dynamic filtering (e.g., `?name[ne]=john`). |
| `GET` | `/v1/spaces/:space_id/members/:member_id` | **Get Member** - Fetches detailed information about a single member. The `member_id` can be the member's ID (starting with `_participant`) or the member's identity. |

---

## Properties Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/spaces/:space_id/properties` | **List Properties** - Retrieves paginated list of properties in a space. Each property includes ID, name, and format. Supports dynamic filtering (e.g., `?name[contains]=date`). |
| `POST` | `/v1/spaces/:space_id/properties` | **Create Property** - Creates a new property with `name` and `format`. Subject to rate limiting. |
| `GET` | `/v1/spaces/:space_id/properties/:property_id` | **Get Property** - Fetches detailed information about a specific property. |
| `PATCH` | `/v1/spaces/:space_id/properties/:property_id` | **Update Property** - Updates an existing property (name). Subject to rate limiting. |
| `DELETE` | `/v1/spaces/:space_id/properties/:property_id` | **Delete Property** - Archives a property. Subject to rate limiting. |

---

## Tags Endpoints

Tags are associated with properties (for select/multi-select).

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/spaces/:space_id/properties/:property_id/tags` | **List Tags** - Retrieves paginated list of tags for a property. Each tag includes ID, name, and color. Supports dynamic filtering (e.g., `?name[contains]=urgent`). |
| `POST` | `/v1/spaces/:space_id/properties/:property_id/tags` | **Create Tag** - Creates a new tag with `name` and `color`. Subject to rate limiting. |
| `GET` | `/v1/spaces/:space_id/properties/:property_id/tags/:tag_id` | **Get Tag** - Retrieves a specific tag including ID, name, and color. |
| `PATCH` | `/v1/spaces/:space_id/properties/:property_id/tags/:tag_id` | **Update Tag** - Updates a tag's name and/or color. Subject to rate limiting. |
| `DELETE` | `/v1/spaces/:space_id/properties/:property_id/tags/:tag_id` | **Delete Tag** - Archives a tag. Subject to rate limiting. |

---

## Types Endpoints

Types define object templates (e.g., 'Page', 'Note', 'Task').

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/spaces/:space_id/types` | **List Types** - Retrieves paginated list of types in a space. Each type includes ID, key, name, icon, and layout. The `key` can be the same across spaces for known types (e.g., 'page' for 'Page'). Supports dynamic filtering (e.g., `?name[contains]=task`). |
| `POST` | `/v1/spaces/:space_id/types` | **Create Type** - Creates a new type with `name`, `icon`, and `layout`. Subject to rate limiting. |
| `GET` | `/v1/spaces/:space_id/types/:type_id` | **Get Type** - Fetches detailed information about a specific type including key, name, icon, and layout. |
| `PATCH` | `/v1/spaces/:space_id/types/:type_id` | **Update Type** - Updates a type's name and properties. Subject to rate limiting. |
| `DELETE` | `/v1/spaces/:space_id/types/:type_id` | **Delete Type** - Archives a type. Subject to rate limiting. |

---

## Templates Endpoints

Templates provide pre-configured structures for creating new objects.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/spaces/:space_id/types/:type_id/templates` | **List Templates** - Returns paginated list of templates for a specific type. Each template includes ID, name, and icon. Supports dynamic filtering (e.g., `?name[contains]=invoice`). |
| `GET` | `/v1/spaces/:space_id/types/:type_id/templates/:template_id` | **Get Template** - Fetches full details for a template including ID, name, icon, and metadata. |

---

## Filter Conditions (FilterCondition Enum)

Many list endpoints support dynamic filtering via query parameters. Available conditions:

| Condition | Description | Example |
|-----------|-------------|---------|
| `eq` | Equals | `?status=active` or `?status[eq]=active` |
| `ne` | Not equals | `?name[ne]=john` |
| `contains` | Contains substring | `?name[contains]=project` |
| `gte` | Greater than or equal | `?created_date[gte]=2024-01-01` |
| `lte` | Less than or equal | `?due_date[lte]=2024-12-31` |
| `in` | In list (comma-separated) | `?tags[in]=urgent,important` |

---

## Pagination

All list endpoints support pagination via query parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `offset` | Number of items to skip | 0 |
| `limit` | Maximum number of items to return | varies |

---

## Rate Limiting

Endpoints that create or modify resources are subject to rate limiting. When rate limit is exceeded:
- Response code: `429 Rate limit exceeded`

---

## Common Response Codes

| Code | Description |
|------|-------------|
| `200` | OK - Request successful |
| `201` | Created - Resource created |
| `400` | Bad request - Invalid request body or parameters |
| `401` | Unauthorized - Missing or invalid authentication |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not found - Resource does not exist |
| `410` | Gone - Resource has been deleted |
| `429` | Rate limit exceeded |
| `500` | Internal server error |

---

## Related Links

- [Anytype API GitHub](https://github.com/anyproto/anytype-api)
- [Anytype Guides](https://developers.anytype.io/docs/guides/get-started/authentication)
- [Anytype Examples](https://developers.anytype.io/docs/examples/overview)
- [Anytype Community](https://community.anytype.io)
