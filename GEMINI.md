# Project Overview

This project, `anytoggl`, is a Python command-line interface (CLI) tool designed to synchronize tasks between an [Anytype](https://anytype.io/) instance and [Toggl Track](https://toggl.com/track/) time entries.

The tool fetches tasks from Anytype that are tagged with "Toggl" and creates corresponding time entries in Toggl. The synchronization logic is based on the last modified timestamp of the tasks in each system.

## Key Technologies & Libraries

*   **Python:** The core programming language.
*   **Typer:** Used to create the command-line interface.
*   **HTTPX:** For making HTTP requests to the Anytype and Toggl APIs.
*   **Pydantic:** For data validation and settings management.
*   **Tenacity:** To provide robust retrying mechanism for HTTP requests.
*   **environs:** For managing environment variables.

## Architecture

The application is structured into several components:

*   `cli.py`: Defines the CLI commands (`once`, `run`, `doctor`) using Typer.
*   `sync_engine.py`: Contains the core business logic for the synchronization process.
*   `clients/`: Contains modules for interacting with the Anytype (`anytype.py`) and Toggl (`toggl.py`) APIs.
*   `models.py`: Defines the Pydantic data models for Anytype tasks and Toggl time entries.
*   `http.py`: Configures a retry mechanism for HTTP requests using `tenacity`.

# Building and Running

## Setup

1.  **Install Dependencies:** This project uses `uv` for dependency management:
    ```bash
    uv sync
    ```

2.  **Configuration:** The application requires the following environment variables. Create a `.env` file in the project root:

    ```
    ANYTYPE_API_URL=http://localhost:31009
    ANYTYPE_TOKEN=<Your Anytype API Token>
    ANYTYPE_SPACE_ID=<Your Anytype Space ID>
    TOGGL_API_TOKEN=<Your Toggl API Token>
    TOGGL_WORKSPACE_ID=<Your Toggl Workspace ID>
    ```

    **Note:** Get your Anytype Space ID from: Settings → Space → Technical Info

## Running the tool

1.  **Check Configuration:**
    ```bash
    uv run python -m anytoggl.cli doctor
    ```

2.  **Run Sync Once:**
    ```bash
    uv run python -m anytoggl.cli once
    ```

3.  **Run Continuously:** (default 300 second interval)
    ```bash
    uv run python -m anytoggl.cli run
    ```
    Specify a different interval:
    ```bash
    uv run python -m anytoggl.cli run --interval 60
    ```

# Sync Behavior

- Anytype tasks tagged with "Toggl" → Toggl time entries
- Task name → Time entry description
- Status "In Progress" → Running timer (duration=-1)
- Status "Done" → Stopped timer
- Projects are auto-created in Toggl if missing

# API Rate Limits

Toggl Free plan: **30 requests/hour** for organization endpoints (create/update).
See `TODO.md` for optimization strategies.

# Development Conventions

*   **Code Style:** The code follows standard Python conventions (PEP 8).
*   **Type Hinting:** The codebase uses type hints for clarity and static analysis.
*   **Modularity:** The application is divided into modules with distinct responsibilities.
*   **Error Handling:** HTTP requests are wrapped in a retry mechanism.
*   **Configuration:** All configuration is managed via environment variables.
