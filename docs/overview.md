# anytoggl — Project Overview

## 1. Idea

**anytoggl** synchronizes tasks between **Anytype** and **Toggl Track** time entries.

Goals:

* Use Anytype as the **task source of truth**
* Create/update Toggl time entries from Anytype tasks
* Keep the system deterministic, minimal, and safe

Non-goals:

* No automatic task creation in Anytype from Toggl
* No real-time sync (polling only)

---

## 2. High-level Architecture

```
[Anytype Desktop]
      │  (Local API)
      ▼
[ anytoggl (Python CLI / Daemon) ]
      ▲
      │  (REST API)
[Toggl Track]
```

Key constraints:

* Anytype API is **local-only**
* Polling-based synchronization
* Toggl Free plan: 30 org requests/hour

---

## 3. Design Decisions

### 3.1 Task Origin

* Tasks are **created only in Anytype**
* Toggl time entries are created from Anytype tasks

### 3.2 Sync Direction

* **Two-way updates** (description, status)
* **One-way creation** (Anytype → Toggl)

### 3.3 Scope Control

* Only Anytype tasks tagged **`Toggl`** are synced
* All other tasks are untouched

### 3.4 Conflict Resolution

* **Last-updated-wins** using timestamps

### 3.5 Identity Mapping

* Toggl time entry ID stored in Anytype (`toggl_id`, Text property)
* No fuzzy matching

### 3.6 Project Mapping

* Anytype Project name ⇄ Toggl Project name
* Toggl projects auto-created if missing

---

## 4. Data Model

### Anytype Task (Type)

Required properties:

* `Name`
* `Description`
* `Status`: `To Do | In Progress | Done`
* `Project` (relation)
* `Tag` (must contain `Toggl`)
* `toggl_id` (Text)

### Toggl Time Entry

* `id`
* `description`
* `project_id`
* `start`, `stop`
* `duration` (negative = running timer)
* `at` (last updated)

---

## 5. Status Mapping

| Anytype Status | Toggl Time Entry |
| -------------- | ---------------- |
| In Progress    | Running timer (duration=-1) |
| Done           | Stopped timer |
| To Do          | Stopped timer |

---

## 6. API Usage

### Anytype (Local API)

* `POST /v1/spaces/{space_id}/search` — query tagged tasks
* `PATCH /v1/spaces/{space_id}/objects/{id}` — update task details

Auth:

```
Authorization: Bearer <ANYTYPE_TOKEN>
```

### Toggl Track API v9

* `GET /workspaces/{wid}/projects` — list projects
* `POST /workspaces/{wid}/projects` — create project
* `GET /me/time_entries` — list time entries
* `POST /workspaces/{wid}/time_entries` — create time entry
* `PUT /workspaces/{wid}/time_entries/{id}` — update time entry

Auth:

```
Basic <api_token>:api_token
```

---

## 7. Implementation Structure

```
anytoggl/
 ├─ cli.py              # CLI entrypoint
 ├─ sync_engine.py      # Core sync logic
 ├─ clients/
 │   ├─ anytype.py      # Anytype HTTP client
 │   └─ toggl.py        # Toggl HTTP client
 ├─ models.py           # Pydantic DTOs
 └─ http.py             # Retry + backoff logic
```

---

## 8. Sync Algorithm

### Anytype → Toggl

1. Query Anytype tasks tagged `Toggl`
2. Resolve / create Toggl project
3. If `toggl_id` missing → create Toggl time entry
4. Store `toggl_id` back to Anytype

### Update Flow (Two-way)

1. Compare `last_modified` vs `at`
2. Newer side overwrites older
3. Apply description + status

Safety rules:

* Never touch untagged Anytype tasks
* Never create Anytype tasks from Toggl

---

## 9. Execution Modes

### CLI

```
uv run python -m anytoggl.cli once
uv run python -m anytoggl.cli run --interval 300
uv run python -m anytoggl.cli doctor
```

### Polling

* Default: every **5 minutes** (recommended due to API limits)
* Cron / Task Scheduler supported

---

## 10. Configuration

Environment variables (via `environs`):

```
ANYTYPE_API_URL=http://localhost:31009
ANYTYPE_TOKEN=...
ANYTYPE_SPACE_ID=...
TOGGL_API_TOKEN=...
TOGGL_WORKSPACE_ID=...
```

---

## 11. Error Handling & Reliability

* Retries on:
  * Network errors
  * HTTP 429 (rate limit)
  * HTTP 5xx
* Exponential backoff (tenacity)
* Idempotent-safe operations
* Partial failure healed on next cycle

---

## 12. Checkpoints

### Phase 1 — Setup

* [x] Define scope & rules
* [x] Anytype schema prepared
* [x] API endpoints identified

### Phase 2 — Core Sync

* [x] Clients implemented
* [x] Sync engine implemented
* [x] Conflict resolution

### Phase 3 — Safety & Ops

* [x] Retry & backoff
* [x] CLI
* [ ] Logging
* [ ] Dry-run mode

### Phase 4 — Test & Harden

* [x] First live test run
* [ ] Edge-case validation
* [ ] Packaging / versioning

---

**Status:** Working — First sync completed successfully
