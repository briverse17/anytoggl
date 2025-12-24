# anytoggl

Sync Anytype tasks to Toggl Track time entries.

## Quick Start

```bash
# Install dependencies
uv sync

# Configure (create .env file)
ANYTYPE_API_URL=http://localhost:31009
ANYTYPE_TOKEN=<your_token>
ANYTYPE_SPACE_ID=<your_space_id>
TOGGL_API_TOKEN=<your_token>
TOGGL_WORKSPACE_ID=<your_workspace_id>

# Check configuration
uv run python -m anytoggl.cli doctor

# Run sync once
uv run python -m anytoggl.cli once

# Run continuously (every 300s)
uv run python -m anytoggl.cli run
```

## How It Works

1. Fetches Anytype tasks tagged with **"Toggl"**
2. Creates/updates Toggl time entries
3. Stores Toggl ID back in Anytype for future syncs

| Anytype Status | Toggl Timer |
|----------------|-------------|
| In Progress    | Running     |
| Done / To Do   | Stopped     |

## API Limits

Toggl Free: **30 requests/hour** for create/update operations.

See [docs/overview.md](docs/overview.md) for full documentation.
