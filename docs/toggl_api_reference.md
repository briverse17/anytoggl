# Toggl Track API Reference

> **Source:** [Toggl Track API Documentation](https://engineering.toggl.com/docs/)  
> **API Version:** v9  
> **Base URL:** `https://api.track.toggl.com/api/v9`

This document summarizes all available endpoints in the Toggl Track API. The API enables interaction with Toggl Track's resources including time entries, workspaces, projects, tasks, tags, and clients.

---

## Overview

### API Format
- **Content-Type:** `application/json` (required header)
- **Date/Time Format:** ISO 8601 / RFC 3339
- **Timezone:** Times are stored in UTC (GMT); returned data is adjusted to user profile timezone

### General Principles
- Only send JSON requests with `Content-Type: application/json` header
- For update requests, send only fields that have changed
- Don't include fields unavailable for current workspace subscription level
- Fetch only the data you need

---

## Authentication

Toggl supports multiple authentication methods:

### HTTP Basic Auth with Email and Password

```bash
curl -u <email>:<password> https://api.track.toggl.com/api/v9/me
```

### HTTP Basic Auth with API Token (Recommended)

Use the API token as username and `api_token` as password:

```bash
curl -u <api_token>:api_token https://api.track.toggl.com/api/v9/me
```

### Session Cookie Authentication

```bash
# Create session
curl -i 'https://accounts.toggl.com/api/sessions' -X POST \
  -d '{"email":"<email>","password":"<password>"}' \
  -H 'Content-Type: application/json'

# Use cookie from response header: __Secure-accounts-session

# Destroy session
curl --cookie __Secure-accounts-session=<cookie_value> \
  -X DELETE https://accounts.toggl.com/api/sessions
```

---

## API Quota

Toggl uses a **Sliding Window** request quota system that is applied per user per organization.

### Quota Headers
| Header | Description |
|--------|-------------|
| `X-Toggl-Quota-Remaining` | Requests remaining in current window |
| `X-Toggl-Quota-Resets-In` | Seconds until window resets |

### Quota Limits by Plan

**Organization-specific requests** (workspace/organization endpoints):

| Plan | Requests per Hour (per user, per org) |
|------|---------------------------------------|
| Free | 30 |
| Starter | 240 |
| Premium | 600 |
| Enterprise | Custom |

**User-specific requests** (e.g., `/api/v9/me`):
- 30 requests/hour per user (all plans)

---

## Rate Limits

A **Leaky Bucket** algorithm is used as a safeguard:
- Safe rate: **1 request per second**
- Limiting applied per API token per IP
- HTTP `429` response when limit exceeded

---

## Me Endpoints

User profile and personal data endpoints.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v9/me` | **Get Me** - Returns details for the current user including workspaces, clients, projects, tags, tasks, and time entries. |
| `PUT` | `/api/v9/me` | **Update Me** - Update current user profile. |
| `GET` | `/api/v9/me/clients` | **Get Clients** - Returns clients visible to the user. |
| `GET` | `/api/v9/me/features` | **Get Features** - Returns features available to the user. |
| `GET` | `/api/v9/me/location` | **Get Location** - Returns user's last known location. |
| `GET` | `/api/v9/me/logged` | **Get Logged** - Returns whether user is logged in. |
| `GET` | `/api/v9/me/organizations` | **Get Organizations** - Returns organizations the user is part of. |
| `GET` | `/api/v9/me/projects` | **Get Projects** - Returns projects visible to the user. |
| `GET` | `/api/v9/me/projects/paginated` | **Get Projects Paginated** - Returns paginated projects. |
| `GET` | `/api/v9/me/quota` | **Get API Quota** - Returns API quota status for the user. |
| `GET` | `/api/v9/me/tags` | **Get Tags** - Returns tags for the user. |
| `GET` | `/api/v9/me/tasks` | **Get Tasks** - Returns tasks for the user. |
| `GET` | `/api/v9/me/track_reminders` | **Get Track Reminders** - Returns tracking reminders. |
| `GET` | `/api/v9/me/web_timer` | **Get Web Timer** - Returns web timer info. |
| `GET` | `/api/v9/me/workspaces` | **Get Workspaces** - Returns workspaces for the user. |

---

## Time Entries Endpoints

Core endpoints for time tracking functionality.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v9/me/time_entries` | **List Time Entries** - Lists latest time entries for the user. Supports `start_date`, `end_date`, `meta` query params. |
| `GET` | `/api/v9/me/time_entries/current` | **Get Current** - Load currently running time entry. |
| `GET` | `/api/v9/me/time_entries/{time_entry_id}` | **Get by ID** - Load time entry by ID. |
| `POST` | `/api/v9/workspaces/{workspace_id}/time_entries` | **Create** - Creates a new time entry in workspace. |
| `PUT` | `/api/v9/workspaces/{workspace_id}/time_entries/{time_entry_id}` | **Update** - Updates an existing time entry. |
| `DELETE` | `/api/v9/workspaces/{workspace_id}/time_entries/{time_entry_id}` | **Delete** - Deletes a time entry. |
| `PATCH` | `/api/v9/workspaces/{workspace_id}/time_entries/{time_entry_ids}` | **Bulk Edit** - Bulk edit multiple time entries (RFC 6902 JSON Patch format). |
| `PATCH` | `/api/v9/workspaces/{workspace_id}/time_entries/{time_entry_id}/stop` | **Stop Timer** - Stops a running time entry. |

### Time Entry Fields

| Field | Type | Description |
|-------|------|-------------|
| `billable` | boolean | Whether entry is billable |
| `created_with` | string | Client app that created entry |
| `description` | string | Time entry description |
| `duration` | integer | Duration in seconds (negative = running) |
| `duronly` | boolean | Duration-only mode |
| `pid` / `project_id` | integer | Project ID |
| `start` | string | Start time (ISO 8601) |
| `start_date` | string | Start date (YYYY-MM-DD) |
| `stop` | string | Stop time (ISO 8601) |
| `tag_ids` | array | Array of tag IDs |
| `tags` | array | Array of tag names |
| `task_id` / `tid` | integer | Task ID |
| `wid` / `workspace_id` | integer | Workspace ID |

---

## Workspaces Endpoints

Workspace management endpoints.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v9/organizations/{organization_id}/workspaces` | **Create Workspace** - Create a workspace within an organization. |
| `GET` | `/api/v9/workspaces/{workspace_id}` | **Get Workspace** - Get single workspace information. |
| `PUT` | `/api/v9/workspaces/{workspace_id}` | **Update Workspace** - Update workspace settings. |
| `GET` | `/api/v9/workspaces/{workspace_id}/statistics` | **Get Statistics** - Get workspace statistics. |
| `GET` | `/api/v9/workspaces/{workspace_id}/time_entry_constraints` | **Get Constraints** - Get workspace time entry constraints. |

### Workspace Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v9/workspaces/{workspace_id}/users` | **List Users** - List users in workspace. |
| `GET` | `/api/v9/workspaces/{workspace_id}/workspace_users` | **Get Workspace Users** - Get workspace users. |
| `PATCH` | `/api/v9/workspaces/{workspace_id}/users` | **Update Users** - Bulk update users in workspace. |
| `PUT` | `/api/v9/workspaces/{workspace_id}/users/{user_id}` | **Update User** - Update single user in workspace. |
| `DELETE` | `/api/v9/workspaces/{workspace_id}/users/{user_id}` | **Remove User** - Remove user from workspace. |

### Workspace Alerts & Reminders

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v9/workspaces/{workspace_id}/alerts` | **Create Alert** - Create workspace alert. |
| `DELETE` | `/api/v9/workspaces/{workspace_id}/alerts/{alert_id}` | **Delete Alert** - Delete workspace alert. |
| `GET` | `/api/v9/workspaces/{workspace_id}/track_reminders` | **List Reminders** - List tracking reminders. |
| `POST` | `/api/v9/workspaces/{workspace_id}/track_reminders` | **Create Reminder** - Create tracking reminder. |
| `PUT` | `/api/v9/workspaces/{workspace_id}/track_reminders/{reminder_id}` | **Update Reminder** - Update tracking reminder. |
| `DELETE` | `/api/v9/workspaces/{workspace_id}/track_reminders/{reminder_id}` | **Delete Reminder** - Delete tracking reminder. |

---

## Projects Endpoints

Project management endpoints.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v9/workspaces/{workspace_id}/projects` | **List Projects** - Get all projects for workspace. |
| `POST` | `/api/v9/workspaces/{workspace_id}/projects` | **Create Project** - Create a new project. |
| `PATCH` | `/api/v9/workspaces/{workspace_id}/projects/{project_ids}` | **Bulk Edit** - Bulk edit multiple projects. |
| `GET` | `/api/v9/workspaces/{workspace_id}/projects/{project_id}` | **Get Project** - Get single project. |
| `PUT` | `/api/v9/workspaces/{workspace_id}/projects/{project_id}` | **Update Project** - Update project. |
| `DELETE` | `/api/v9/workspaces/{workspace_id}/projects/{project_id}` | **Delete Project** - Delete project. |

### Project Fields

| Field | Type | Description |
|-------|------|-------------|
| `active` | boolean | Whether project is active |
| `auto_estimates` | boolean | Auto-estimate enabled |
| `billable` | boolean | Whether project is billable |
| `client_id` / `cid` | integer | Client ID |
| `client_name` | string | Client name (for creation) |
| `color` | string | Project color |
| `currency` | string | Project currency |
| `end_date` | string | Project end date |
| `estimated_hours` | integer | Estimated hours |
| `is_private` | boolean | Whether project is private |
| `is_shared` | boolean | Whether project is shared |
| `name` | string | Project name |
| `rate` | number | Hourly rate |
| `recurring` | boolean | Whether recurring |
| `start_date` | string | Project start date |
| `template` | boolean | Whether this is a template |

### Project Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v9/workspaces/{workspace_id}/project_users` | **List Project Users** - Get workspace project users. |
| `POST` | `/api/v9/workspaces/{workspace_id}/project_users` | **Add Project User** - Add user to project. |
| `PUT` | `/api/v9/workspaces/{workspace_id}/project_users/{project_user_id}` | **Update Project User** - Update project user. |
| `DELETE` | `/api/v9/workspaces/{workspace_id}/project_users/{project_user_id}` | **Remove Project User** - Remove user from project. |
| `PATCH` | `/api/v9/workspaces/{workspace_id}/project_users` | **Bulk Edit Project Users** - Bulk edit project users. |

---

## Tasks Endpoints

Task management within projects.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v9/workspaces/{workspace_id}/projects/{project_id}/tasks` | **List Tasks** - Get tasks for project. |
| `POST` | `/api/v9/workspaces/{workspace_id}/projects/{project_id}/tasks` | **Create Task** - Create task in project. |
| `PATCH` | `/api/v9/workspaces/{workspace_id}/projects/{project_id}/tasks/{task_ids}` | **Bulk Edit Tasks** - Bulk edit tasks. |
| `GET` | `/api/v9/workspaces/{workspace_id}/projects/{project_id}/tasks/{task_id}` | **Get Task** - Get single task. |
| `PUT` | `/api/v9/workspaces/{workspace_id}/projects/{project_id}/tasks/{task_id}` | **Update Task** - Update task. |
| `DELETE` | `/api/v9/workspaces/{workspace_id}/projects/{project_id}/tasks/{task_id}` | **Delete Task** - Delete task. |
| `GET` | `/api/v9/workspaces/{workspace_id}/tasks` | **List Workspace Tasks** - Get all tasks in workspace. |

### Task Fields

| Field | Type | Description |
|-------|------|-------------|
| `active` | boolean | Whether task is active |
| `estimated_seconds` | integer | Estimated time in seconds |
| `external_reference` | string | External reference ID |
| `name` | string | Task name |
| `user_id` | integer | Assigned user ID |

---

## Tags Endpoints

Tag management for time entries.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v9/workspaces/{workspace_id}/tags` | **List Tags** - List all workspace tags. |
| `POST` | `/api/v9/workspaces/{workspace_id}/tags` | **Create Tag** - Create workspace tag. Payload: `{"name": "string"}` |
| `PUT` | `/api/v9/workspaces/{workspace_id}/tags/{tag_id}` | **Update Tag** - Update tag name. |
| `DELETE` | `/api/v9/workspaces/{workspace_id}/tags/{tag_id}` | **Delete Tag** - Delete tag. |

---

## Clients Endpoints

Client management for projects.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v9/workspaces/{workspace_id}/clients` | **List Clients** - List all workspace clients. |
| `POST` | `/api/v9/workspaces/{workspace_id}/clients` | **Create Client** - Create workspace client. |
| `GET` | `/api/v9/workspaces/{workspace_id}/clients/{client_id}` | **Get Client** - Load client by ID. |
| `PUT` | `/api/v9/workspaces/{workspace_id}/clients/{client_id}` | **Update Client** - Update client. |
| `DELETE` | `/api/v9/workspaces/{workspace_id}/clients/{client_id}` | **Delete Client** - Delete client. |
| `POST` | `/api/v9/workspaces/{workspace_id}/clients/{client_id}/archive` | **Archive Client** - Archive client. |
| `POST` | `/api/v9/workspaces/{workspace_id}/clients/{client_id}/restore` | **Restore Client** - Restore archived client and projects. |

### Client Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Client name |
| `notes` | string | Client notes |
| `external_reference` | string | External reference ID |

---

## Common Response Codes

| Code | Description | Recommendation |
|------|-------------|----------------|
| `200` | OK - Success | - |
| `400` | Bad Request | Don't retry with same payload; inspect response body |
| `401` | Unauthorized | Check authentication credentials |
| `402` | Payment Required | Workspace needs upgrade; quota exceeded |
| `403` | Forbidden | User lacks access to resource |
| `404` | Not Found | Resource doesn't exist |
| `410` | Gone | Resource permanently removed; don't retry |
| `429` | Too Many Requests | Back off; wait before retrying (1 req/sec safe) |
| `500` | Internal Server Error | Add random delay before retry |

---

## Eventual Consistency

The API uses an event-based architecture with eventual consistency:

- Creating entities (organizations, workspaces, projects, groups) requires waiting for session update
- Recommended: **2-5 seconds delay** with up to **3 retries**
- Use `/me` endpoint to check `updated_at` timestamp for session changes

---

## Example: Python Usage

```python
import requests
from base64 import b64encode

# Using API token authentication
api_token = "<your_api_token>"
auth = b64encode(f"{api_token}:api_token".encode()).decode()

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {auth}"
}

# Get current user
response = requests.get(
    "https://api.track.toggl.com/api/v9/me",
    headers=headers
)
print(response.json())

# Get time entries
response = requests.get(
    "https://api.track.toggl.com/api/v9/me/time_entries",
    headers=headers
)
print(response.json())

# Create time entry
workspace_id = 12345
response = requests.post(
    f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/time_entries",
    headers=headers,
    json={
        "description": "Working on project",
        "duration": -1,  # Running timer
        "start": "2024-01-01T09:00:00Z",
        "workspace_id": workspace_id,
        "created_with": "anytoggl"
    }
)
print(response.json())
```

---

## Related Links

- [Toggl Track API Docs](https://engineering.toggl.com/docs/)
- [Toggl Track GitHub](https://github.com/toggl)
- [Support & Knowledge Base](https://support.toggl.com/)
