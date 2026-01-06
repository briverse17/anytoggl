# Toggl Plan API Reference

> **Source:** [Toggl Plan API Documentation](https://developers.plan.toggl.com/api-v5.html)  
> **API Version:** v5  
> **Base URL:** `https://api.plan.toggl.com/api/v5`

This document summarizes all available endpoints in the Toggl Plan API. The API enables interaction with Toggl Plan's resources including tasks, projects, milestones, members, groups, and user profiles.

---

## Overview

### API Format
- **Content-Type:** `application/json`
- **Date Format:** ISO 8601 (YYYY-MM-DD)
- **DateTime Format:** ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
- **Timestamp Format:** ISO 8601 (YYYY-MM-DDTHH:MM:SS.000Z)
- **Protocol:** HTTPS only

### General Principles
- All API access is over HTTPS from `api.plan.toggl.com/api/v5`
- All data is sent and received as JSON
- All dates are in ISO 8601 format
- For GET requests, parameters can be passed as query strings
- For POST, PUT, DELETE requests, parameters should be in request body

---

## Authentication

Toggl Plan uses **OAuth 2.0** for authentication and authorization.

### OAuth 2.0 Methods

#### 1. Authorization Code Grant (Web Application Flow)

**Step 1: Redirect users to request access**

```bash
GET https://plan.toggl.com/oauth/login
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `response_type` | string | Required. Must be "code" |
| `client_id` | string | Required. Your App Key from Toggl Plan |
| `redirect_uri` | string | URL where users will be sent after authorization |
| `state` | string | Unguessable random string for CSRF protection |

**Step 2: Exchange code for access token**

```bash
POST https://api.plan.toggl.com/api/v5/authenticate/token
Authorization: Basic Base64(CLIENT-ID:CLIENT-SECRET)
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `grant_type` | string | Required. Must be "authorization_code" |
| `code` | string | Required. Code from Step 1 |
| `client_id` | string | Required. Your App Key |

**Response:**
```json
{
  "access_token": "e72e16c7e42f292c6912e7710c838347ae178b4a",
  "refresh_token": "2c6912e7710c838347ae178b4ae72e16c7e42f292",
  "expires_in": 3600,
  "token_type": "bearer"
}
```

#### 2. Resource Owner Password Credentials Grant

For trusted applications that can securely store credentials.

### Using Access Tokens

**In Header (Recommended):**
```bash
curl "https://api.plan.toggl.com/api/v5/me" \
  -H "Authorization: Bearer OAUTH-TOKEN"
```

**As Query Parameter:**
```bash
curl "https://api.plan.toggl.com/api/v5/me?access_token=OAUTH-TOKEN"
```

### Refreshing Access Tokens

When access token expires, use the refresh token to obtain a new one.

---

## API Quota & Rate Limits

Toggl Plan implements API quotas to ensure service stability and fair usage across all users.

### Quota System

The API uses a **sliding window** quota system that tracks requests over a 60-minute period. The quota is applied per user per workspace.

### Quota Limits by Plan

**Workspace-specific requests** (endpoints with `{workspace_id}`):

| Plan | Requests per Hour (per user, per workspace) |
|------|---------------------------------------------|
| Free | 30 |
| Starter | 240 |
| Premium | 600 |
| Enterprise | Custom (contact Toggl) |

**User-specific requests** (e.g., `/api/v5/me`):
- 30 requests/hour per user (all plans)

### Monitoring Quota Usage

While Toggl Plan's official documentation doesn't specify quota headers, based on Toggl's ecosystem patterns, you should monitor response headers:

| Header | Description |
|--------|-------------|
| `X-Toggl-Quota-Remaining` | Requests remaining in current window (if available) |
| `X-Toggl-Quota-Resets-In` | Seconds until window resets (if available) |

### Rate Limit Responses

When quota is exceeded, the API will respond with:

| Code | Description | Action |
|------|-------------|--------|
| `402` | Payment Required / Quota Exceeded | Wait for quota reset or upgrade plan |
| `429` | Too Many Requests | Implement exponential backoff |

### Best Practices

1. **Implement Retry Logic**: Use exponential backoff when receiving 429 responses
2. **Cache Responses**: Store frequently accessed data locally to reduce API calls
3. **Batch Operations**: Group related operations when possible
4. **Monitor Usage**: Track your API consumption to stay within limits
5. **Safe Rate**: Aim for **1 request per second** as a safe baseline

### Example: Handling Rate Limits in Python

```python
import httpx
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class RateLimitError(Exception):
    pass

@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5)
)
def make_api_request(url, headers):
    response = httpx.get(url, headers=headers)
    
    if response.status_code == 429:
        raise RateLimitError("Rate limit exceeded")
    elif response.status_code == 402:
        raise Exception("API quota exceeded - upgrade plan or wait for reset")
    
    response.raise_for_status()
    return response.json()

# Usage
access_token = "<your_access_token>"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {access_token}"
}

try:
    data = make_api_request(
        "https://api.plan.toggl.com/api/v5/me",
        headers
    )
    print(data)
except Exception as e:
    print(f"Error: {e}")
```

---

## Error Handling

### HTTP Status Codes

| Code | Description | Action |
|------|-------------|--------|
| `200` | OK - Success | - |
| `204` | No Content - Success (no response body) | - |
| `401` | Unauthorized | Check Authorization header |
| `403` | Forbidden | User lacks permission for resource |
| `404` | Not Found | Resource doesn't exist or unauthorized |
| `422` | Unprocessable Entity | Invalid field values |

### Error Response Format

```json
{
  "errors": {
    "email": ["format is invalid"],
    "avatar_color": ["is not included in the list"]
  }
}
```

---

## User Profile Endpoints

Manage user profile information.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v5/me` | **Get Profile** - Returns current user profile information. |
| `PUT` | `/api/v5/me` | **Update Profile** - Update current user profile. |

---

## Members Endpoints

Manage workspace members and invitations.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v5/{workspace_id}/dummy_users` | **Add Member** - Add new member using name (not linked to existing user). |
| `PUT` | `/api/v5/{workspace_id}/dummy_users/{member_id}` | **Update Unlinked Member** - Update member not yet linked with existing user. |
| `GET` | `/api/v5/{workspace_id}/members` | **List Members** - Fetch list of workspace members. |
| `GET` | `/api/v5/{workspace_id}/members/{member_id}` | **Get Member** - Get single member details. |
| `PUT` | `/api/v5/{workspace_id}/members/{member_id}` | **Update Member** - Update member information. |
| `DELETE` | `/api/v5/{workspace_id}/members/{member_id}` | **Remove Member** - Remove member from workspace. |

---

## Tasks Endpoints

Core task management functionality.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v5/{workspace_id}/tasks/{filter}` | **List Tasks** - Fetch list of tasks with optional filters. |
| `POST` | `/api/v5/{workspace_id}/tasks` | **Create Task** - Add a new task. |
| `GET` | `/api/v5/{workspace_id}/tasks/{task_id}` | **Get Task** - Get single task details. |
| `PUT` | `/api/v5/{workspace_id}/tasks/{task_id}` | **Update Task** - Update task information. |
| `DELETE` | `/api/v5/{workspace_id}/tasks/{task_id}` | **Delete Task** - Remove a task. |

### Task Filters

The `{filter}` parameter in list endpoint can be:
- `timeline` - Tasks on the timeline
- `backlog` - Tasks in backlog
- (empty) - All tasks

### Task Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `since` | ISO 8601 | Only tasks after this date |
| `until` | ISO 8601 | Only tasks before this date |
| `users` | string | Filter by user IDs (timeline only) |
| `project` | string | Filter by project ID |
| `tasks` | string | Filter by task IDs |
| `group` | string | Filter by group ID |
| `tags` | string | Filter by tag IDs |

### Task Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Task ID |
| `name` | string | Task name |
| `notes` | string | Task notes/description |
| `start_date` | string | Start date (YYYY-MM-DD) |
| `end_date` | string | End date (YYYY-MM-DD) |
| `start_time` | string | Start time (HH:MM) |
| `end_time` | string | End time (HH:MM) |
| `color` | string | Color hex code |
| `color_id` | integer | Color ID |
| `estimated_hours` | string | Estimated hours |
| `estimated_minutes` | string | Estimated minutes |
| `status` | string | Task status (e.g., "done") |
| `workspace_members` | array | Assigned member IDs |
| `folder_id` | integer | Parent folder ID |
| `tag_ids` | array | Associated tag IDs |
| `position` | integer | Position in list |
| `weight` | integer | Task weight |
| `created_at` | ISO 8601 | Creation timestamp |
| `updated_at` | ISO 8601 | Last update timestamp |

---

## Projects Endpoints

Project management functionality.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v5/{workspace_id}/projects` | **List Projects** - Fetch list of projects. |
| `POST` | `/api/v5/{workspace_id}/projects` | **Create Project** - Add a new project. |
| `GET` | `/api/v5/{workspace_id}/projects/{project_id}` | **Get Project** - Get single project details. |
| `PUT` | `/api/v5/{workspace_id}/projects/{project_id}` | **Update Project** - Update project information. |
| `DELETE` | `/api/v5/{workspace_id}/projects/{project_id}` | **Delete Project** - Remove a project. |

---

## Milestones Endpoints

Milestone management for projects.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v5/{workspace_id}/milestones` | **List Milestones** - Fetch list of milestones. |
| `POST` | `/api/v5/{workspace_id}/milestones` | **Create Milestone** - Add a new milestone. |
| `GET` | `/api/v5/{workspace_id}/milestones/{milestone_id}` | **Get Milestone** - Get single milestone details. |
| `PUT` | `/api/v5/{workspace_id}/milestones/{milestone_id}` | **Update Milestone** - Update milestone information. |
| `DELETE` | `/api/v5/{workspace_id}/milestones/{milestone_id}` | **Delete Milestone** - Remove a milestone. |

### Milestone Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `since` | ISO 8601 | Only milestones after this date |
| `until` | ISO 8601 | Only milestones before this date |
| `projects` | string | Filter by project IDs |
| `groups` | string | Filter by group IDs |

---

## Groups Endpoints

Group management for organizing members.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v5/{workspace_id}/groups` | **List Groups** - Fetch list of groups. |
| `POST` | `/api/v5/{workspace_id}/groups` | **Create Group** - Add a new group. |
| `GET` | `/api/v5/{workspace_id}/groups/{group_id}` | **Get Group** - Get single group details. |
| `PUT` | `/api/v5/{workspace_id}/groups/{group_id}` | **Update Group** - Update group information. |
| `DELETE` | `/api/v5/{workspace_id}/groups/{group_id}` | **Delete Group** - Remove a group. |

### Group Memberships

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v5/{workspace_id}/groups/{group_id}/memberships` | **List Memberships** - Fetch list of group memberships. |
| `POST` | `/api/v5/{workspace_id}/groups/{group_id}/memberships` | **Add User to Group** - Add a user to the group. |
| `DELETE` | `/api/v5/{workspace_id}/groups/{group_id}/memberships/{membership_id}` | **Remove Membership** - Remove user from group. |

---

## HTTP Verbs

Toggl Plan API uses standard HTTP verbs:

| Verb | Usage |
|------|-------|
| `GET` | Retrieve resource(s) |
| `POST` | Create new resource |
| `PUT` | Update existing resource |
| `DELETE` | Remove resource |

---

## HTTP Redirects

The API may use HTTP redirects. Clients should follow redirects automatically. The `Location` header will contain the URI to redirect to.

---

## Example: Python Usage

```python
import httpx
from base64 import b64encode

# OAuth 2.0 Bearer Token Authentication
access_token = "<your_access_token>"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {access_token}"
}

# Get current user profile
response = httpx.get(
    "https://api.plan.toggl.com/api/v5/me",
    headers=headers
)
print(response.json())

# Get tasks for workspace
workspace_id = 12345
response = httpx.get(
    f"https://api.plan.toggl.com/api/v5/{workspace_id}/tasks/timeline",
    headers=headers,
    params={
        "since": "2024-01-01",
        "until": "2024-12-31"
    }
)
print(response.json())

# Create a new task
response = httpx.post(
    f"https://api.plan.toggl.com/api/v5/{workspace_id}/tasks",
    headers=headers,
    json={
        "name": "New Task",
        "notes": "Task description",
        "start_date": "2024-01-01",
        "end_date": "2024-01-05",
        "estimated_hours": "8"
    }
)
print(response.json())
```

---

## Key Differences from Toggl Track

| Feature | Toggl Track | Toggl Plan |
|---------|-------------|------------|
| **Purpose** | Time tracking | Project planning & task management |
| **Main Resources** | Time entries, projects, clients | Tasks, projects, milestones, groups |
| **Authentication** | API Token or OAuth 2.0 | OAuth 2.0 only |
| **Base URL** | `api.track.toggl.com/api/v9` | `api.plan.toggl.com/api/v5` |
| **Core Concept** | Time entries with duration | Tasks with dates and assignments |

---

## Related Links

- [Toggl Plan API Docs](https://developers.plan.toggl.com/api-v5.html)
- [Toggl Plan Developer Portal](https://developers.plan.toggl.com/)
- [Toggl Plan Support](https://support.plan.toggl.com)
- [Toggl Plan Website](https://toggl.com/plan/)
