# Toggl Plan API v5 Reference

This document provides a comprehensive reference for the Toggl Plan API v5, including authentication, endpoints, and practical implementation notes based on real-world testing.

## Base URL

```
https://api.plan.toggl.com/api/v5
```

## Authentication

Toggl Plan API v5 uses OAuth 2.0 for authentication. Two grant types are supported:

### 1. Authorization Code Grant

**Use case:** Web applications where users authorize access through a browser.

**Flow:**
1. Redirect user to authorization URL
2. User authorizes the application
3. Receive authorization code via callback
4. Exchange code for access token

**Authorization URL:**
```
https://api.plan.toggl.com/api/v5/authorize
```

**Parameters:**
- `client_id`: Your application's client ID
- `redirect_uri`: Callback URL
- `response_type`: Set to `code`
- `state`: Optional CSRF token

**Token Exchange:**
```http
POST /api/v5/authenticate/token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {base64(client_id:client_secret)}

grant_type=authorization_code&code={authorization_code}&redirect_uri={redirect_uri}
```

### 2. Resource Owner Password Credentials Grant

**Use case:** Server-to-server applications, CLI tools, trusted applications.

**Token Request:**
```http
POST /api/v5/authenticate/token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {base64(client_id:client_secret)}

grant_type=password&username={user_email}&password={user_password}
```

**Response:**
```json
{
  "access_token": "your_access_token",
  "refresh_token": "your_refresh_token",
  "token_type": "Bearer",
  "expires_in": 7776000
}
```

**Notes:**
- Access tokens expire in 90 days (7,776,000 seconds)
- Store both access_token and refresh_token
- Use refresh_token to obtain new access_token when expired

### 3. Token Refresh

```http
POST /api/v5/authenticate/token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {base64(client_id:client_secret)}

grant_type=refresh_token&refresh_token={refresh_token}
```

### Using Access Tokens

Include the access token in the Authorization header for all API requests:

```http
Authorization: Bearer {access_token}
```

## User Profile

### Get Current User

```http
GET /api/v5/me
```

**Response:**
```json
{
  "id": 7509708,
  "name": "User Name",
  "email": "user@example.com",
  "workspace_id": 960111,
  ...
}
```

**Use case:** Retrieve user_id required for task creation.

## Projects

### List Projects

```http
GET /api/v5/{workspace_id}/projects
```

**Response:**
```json
[
  {
    "id": 4393294,
    "name": "Project Name",
    "color_id": 1,
    "workspace_id": 960111,
    ...
  }
]
```

### Create Project

```http
POST /api/v5/{workspace_id}/projects
Content-Type: application/json

{
  "name": "Project Name",
  "color_id": 1
}
```

## Tasks

### List Tasks

```http
GET /api/v5/{workspace_id}/tasks
```

**Optional Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `since` | ISO 8601 date | Filter tasks after this date |
| `before` | ISO 8601 date | Filter tasks before this date |

**Response:**
```json
[
  {
    "id": 52659484,
    "name": "Task Name",
    "notes": "Task description",
    "start_date": "2026-01-07",
    "end_date": "2026-01-08",
    "start_time": "08:00",
    "end_time": "09:00",
    "user_id": 7509708,
    "project_id": 4393294,
    "estimated_minutes": 60,
    "status": "to-do",
    "created_at": "2026-01-06T19:18:00Z",
    "updated_at": "2026-01-06T19:18:00Z",
    ...
  }
]
```

### Create Task

```http
POST /api/v5/{workspace_id}/tasks
Content-Type: application/json

{
  "name": "Task Name",
  "notes": "Task description\n\n#anytype_id:bafyreiabc123",
  "start_date": "2026-01-07",
  "end_date": "2026-01-08",
  "start_time": "08:00",
  "end_time": "09:00",
  "user_id": 7509708,
  "project_id": 4393294,
  "estimated_minutes": 60
}
```

**Required Fields:**
- `name`: Task name
- `start_date`: Start date (YYYY-MM-DD format)
- `end_date`: End date (YYYY-MM-DD format)
- `user_id`: User ID (required - task must be assigned to a user OR have a folder_id)

**Optional Fields:**
- `notes`: Task description/notes
- `start_time`: Daily start time (HH:MM format, e.g., "08:00")
- `end_time`: Daily end time (HH:MM format, e.g., "09:00")
- `project_id`: Project ID for grouping
- `estimated_minutes`: Time estimate in minutes (e.g., 60 for 1 hour)
- `folder_id`: Folder ID (alternative to user_id)

**Response:**
```json
{
  "id": 52659484,
  "name": "Task Name",
  "notes": "Task description\n\n#anytype_id:bafyreiabc123",
  "start_date": "2026-01-07",
  "end_date": "2026-01-08",
  "start_time": "08:00",
  "end_time": "09:00",
  "user_id": 7509708,
  "project_id": 4393294,
  "estimated_minutes": 60,
  "status": "to-do",
  "created_at": "2026-01-06T19:18:00Z",
  "updated_at": "2026-01-06T19:18:00Z",
  ...
}
```

### Update Task

```http
PUT /api/v5/{workspace_id}/tasks/{task_id}
Content-Type: application/json

{
  "name": "Updated Task Name",
  "notes": "Updated description\n\n#anytype_id:bafyreiabc123",
  "start_date": "2026-01-08",
  "end_date": "2026-01-09"
}
```

### Delete Task

```http
DELETE /api/v5/{workspace_id}/tasks/{task_id}
```

### Task Fields

| Field | Type | Description | Notes |
|-------|------|-------------|-------|
| `id` | integer | Task ID | Read-only |
| `name` | string | Task name | Required |
| `notes` | string | Task notes/description | Use for descriptions and metadata |
| `start_date` | string | Start date (YYYY-MM-DD) | Required |
| `end_date` | string | End date (YYYY-MM-DD) | Required |
| `start_time` | string | Start time (HH:MM) | Daily time window start |
| `end_time` | string | End time (HH:MM) | Daily time window end |
| `user_id` | integer | Assigned user ID | Required (or folder_id) |
| `project_id` | integer | Project ID | Optional grouping |
| `estimated_minutes` | integer | Estimated minutes | Works (e.g., 60 = 1 hour) |
| `estimated_hours` | string | Estimated hours | ⚠️ Does not work via API |
| `daily_estimated_minutes` | string | Daily estimate | ⚠️ Does not work via API |
| `status` | string | Task status | "to-do", "done", etc. |
| `folder_id` | integer | Parent folder ID | Alternative to user_id |
| `tag_ids` | array | Associated tag IDs | ⚠️ Tags not supported via API |
| `created_at` | ISO 8601 | Creation timestamp | Read-only |
| `updated_at` | ISO 8601 | Last update timestamp | Read-only |
| `workspace_members` | array | Assigned member IDs | Read-only |
| `estimate_type` | string | Estimate type | Defaults to "daily" |
| `estimate_skips_weekend` | boolean | Skip weekends | Defaults to true |

## Practical Implementation Notes

### Token Management

**Best Practice:** Cache tokens in a database (e.g., DuckDB) to avoid unnecessary authentication requests.

```python
# Store tokens with expiration
{
  "access_token": "...",
  "refresh_token": "...",
  "expires_at": "2026-04-07T02:49:57"
}

# Check expiration before use (with 5-minute buffer)
if datetime.now() < expires_at - timedelta(minutes=5):
    use_cached_token()
else:
    refresh_token()
```

### Task Linking Strategy

Since custom fields are not supported, use the `notes` field with a marker pattern:

```python
def build_notes(description: str | None, external_id: str) -> str:
    parts = []
    if description:
        parts.append(description)
    parts.append(f"#anytype_id:{external_id}")
    return "\n\n".join(parts)

# Extract ID from notes
import re
match = re.search(r'#anytype_id:(\S+)', notes)
if match:
    external_id = match.group(1)
```

### Time Estimates

**Working:**
- `estimated_minutes`: Set as integer (e.g., 60 for 1 hour)

**Not Working via API:**
- `estimated_hours`: Always returns None
- `daily_estimated_minutes`: Always returns None

**Recommendation:** Use `estimated_minutes` for all time estimates.

### Daily Scheduling

Use `start_time` and `end_time` to define daily work windows:

```json
{
  "start_date": "2026-01-07",
  "end_date": "2026-01-10",
  "start_time": "08:00",
  "end_time": "09:00"
}
```

This creates a task spanning 4 days, scheduled 08:00-09:00 each day.

### Tags

**Status:** ⚠️ Tags are not supported via the API
- No tags endpoint exists (`/tags` returns 404)
- `tag_ids` field in task payload is ignored
- `tag_ids` in response is always empty

**Workaround:** Use projects for grouping instead of tags.

### Required Fields for Task Creation

**Minimum required:**
```json
{
  "name": "Task Name",
  "start_date": "2026-01-07",
  "end_date": "2026-01-08",
  "user_id": 7509708
}
```

**Error if missing user_id:**
```json
{
  "errors": {
    "folder_id": ["can't be blank if no user or plan is assigned"]
  }
}
```

### Date Format

**Correct:** `"2026-01-07"` (YYYY-MM-DD, date-only string)

**Incorrect:** 
- `"2026-01-07T00:00:00Z"` (ISO datetime)
- `"2026-01-07T00:00:00.000000"` (datetime with microseconds)

The API expects date-only strings, not datetime strings.

### Time Format

**Correct:** `"08:00"` (HH:MM, 24-hour format)

**Examples:**
- `"08:00"` = 8 AM
- `"13:30"` = 1:30 PM
- `"20:00"` = 8 PM

## Rate Limits

**Free Plan:** 30 requests/hour for organization endpoints (create/update)

**Recommendation:** Implement retry logic with exponential backoff for 429 errors.

## Error Handling

### Common Errors

| Status | Error | Solution |
|--------|-------|----------|
| 401 | Unauthorized | Check access token validity |
| 404 | Not Found | Verify workspace_id and resource IDs |
| 422 | Unprocessable Entity | Check required fields and date formats |
| 429 | Too Many Requests | Implement rate limiting and retry logic |

### Example Error Response

```json
{
  "errors": {
    "folder_id": ["can't be blank if no user or plan is assigned"]
  }
}
```

## Complete Example

```python
import httpx
import base64
from datetime import datetime, timedelta

# Authenticate
credentials = f"{client_id}:{client_secret}"
encoded = base64.b64encode(credentials.encode()).decode()

response = httpx.post(
    "https://api.plan.toggl.com/api/v5/authenticate/token",
    headers={
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/x-www-form-urlencoded",
    },
    data={
        "grant_type": "password",
        "username": "user@example.com",
        "password": "password",
    },
)
token_data = response.json()
access_token = token_data["access_token"]

# Get user ID
headers = {"Authorization": f"Bearer {access_token}"}
profile = httpx.get("https://api.plan.toggl.com/api/v5/me", headers=headers).json()
user_id = profile["id"]

# Create task
task_payload = {
    "name": "Complete integration",
    "notes": "Finish API integration\n\n#anytype_id:bafyreiabc123",
    "start_date": "2026-01-07",
    "end_date": "2026-01-08",
    "start_time": "08:00",
    "end_time": "09:00",
    "user_id": user_id,
    "project_id": 4393294,
    "estimated_minutes": 60,
}

task = httpx.post(
    f"https://api.plan.toggl.com/api/v5/{workspace_id}/tasks",
    headers=headers,
    json=task_payload,
).json()

print(f"Created task: {task['id']}")
```

## Resources

- [Official Toggl Plan API Documentation](https://developers.plan.toggl.com/api-v5.html)
- [OAuth 2.0 Specification](https://oauth.net/2/)
