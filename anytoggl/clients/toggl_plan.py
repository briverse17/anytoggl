# anytoggl/clients/toggl_plan.py
import base64
import httpx
import duckdb
from datetime import datetime, timedelta
from pathlib import Path
from anytoggl.http import RETRY
from anytoggl.models import TogglPlanTask
from loguru import logger


class TogglPlanClient:
    """Client for interacting with Toggl Plan API v5 with automatic OAuth authentication and token caching."""

    def __init__(
        self,
        workspace_id: int,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
        token_db_path: str | None = None,
    ):
        """Initialize Toggl Plan client with OAuth credentials.

        Args:
            workspace_id: Toggl Plan workspace ID
            client_id: OAuth app key
            client_secret: OAuth app secret
            username: Toggl Plan user email
            password: Toggl Plan user password
            token_db_path: Optional path to token cache database (defaults to ~/.anytoggl/tokens.db)
        """
        self.workspace_id = workspace_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.access_token = None
        self.user_id = None  # Will be set during authentication

        # Setup token cache database
        if token_db_path is None:
            cache_dir = Path.home() / ".anytoggl"
            cache_dir.mkdir(exist_ok=True)
            token_db_path = str(cache_dir / "tokens.db")

        self.token_db_path = token_db_path
        self._init_token_db()

        self.client = httpx.Client(
            base_url="https://api.plan.toggl.com/api/v5",
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        # Obtain access token on initialization
        self._authenticate()

    def _init_token_db(self):
        """Initialize token cache database."""
        conn = duckdb.connect(self.token_db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY,
                access_token TEXT NOT NULL,
                refresh_token TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.close()

    def _get_cached_token(self):
        """Get cached token if not expired."""
        conn = duckdb.connect(self.token_db_path)
        result = conn.execute("""
            SELECT access_token, refresh_token, expires_at 
            FROM tokens 
            WHERE id = 1
        """).fetchone()
        conn.close()

        if not result:
            return None

        access_token, refresh_token, expires_at = result

        # Check if token is expired (with 5 minute buffer)
        if datetime.now() < expires_at - timedelta(minutes=5):
            logger.info(f"Using cached access token (expires at {expires_at})")
            return access_token, refresh_token
        else:
            logger.info(f"Cached token expired at {expires_at}")
            return None

    def _save_token(self, access_token: str, refresh_token: str, expires_in: int):
        """Save token to database."""
        expires_at = datetime.now() + timedelta(seconds=expires_in)

        conn = duckdb.connect(self.token_db_path)
        conn.execute(
            """
            INSERT OR REPLACE INTO tokens (id, access_token, refresh_token, expires_at)
            VALUES (1, ?, ?, ?)
        """,
            [access_token, refresh_token, expires_at],
        )
        conn.close()

        logger.info(f"Saved token to database (expires at {expires_at})")

    def _authenticate(self):
        """Obtain access token using Resource Owner Password Credentials Grant with caching."""
        # Try cached token first
        cached = self._get_cached_token()
        if cached:
            self.access_token, _ = cached
            self.client.headers["Authorization"] = f"Bearer {self.access_token}"

            # Get user profile
            profile_response = httpx.get(
                "https://api.plan.toggl.com/api/v5/me",
                headers=self.client.headers,
                timeout=10,
            )
            profile_response.raise_for_status()
            profile = profile_response.json()
            self.user_id = profile["id"]

            logger.info(f"Authenticated with cached token (User ID: {self.user_id})")
            return

        # Get new token
        logger.info("Authenticating with Toggl Plan API...")

        # Create Basic Auth header
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        response = httpx.post(
            "https://api.plan.toggl.com/api/v5/authenticate/token",
            headers={
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "password",
                "username": self.username,
                "password": self.password,
            },
            timeout=10,
        )
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]

        # Save token to cache
        self._save_token(
            token_data["access_token"],
            token_data["refresh_token"],
            token_data["expires_in"],
        )

        # Update client headers with Bearer token
        self.client.headers["Authorization"] = f"Bearer {self.access_token}"

        # Get user profile to retrieve user_id (required for task creation)
        profile_response = httpx.get(
            "https://api.plan.toggl.com/api/v5/me",
            headers=self.client.headers,
            timeout=10,
        )
        profile_response.raise_for_status()
        profile = profile_response.json()
        self.user_id = profile["id"]

        logger.info(
            f"Successfully authenticated with Toggl Plan API (User ID: {self.user_id})"
        )

    @RETRY
    def _get(self, url: str):
        r = self.client.get(url)
        r.raise_for_status()
        return r

    @RETRY
    def _post(self, url: str, json: dict):
        r = self.client.post(url, json=json)
        r.raise_for_status()
        return r

    @RETRY
    def _put(self, url: str, json: dict):
        r = self.client.put(url, json=json)
        r.raise_for_status()
        return r

    @RETRY
    def _delete(self, url: str):
        r = self.client.delete(url)
        r.raise_for_status()
        return r

    def list_tasks(
        self, since: str | None = None, before: str | None = None
    ) -> list[TogglPlanTask]:
        """List all tasks in the workspace.

        Args:
            since: Optional ISO 8601 date to filter tasks after this date
            before: Optional ISO 8601 date to filter tasks before this date

        Returns:
            List of TogglPlanTask objects
        """
        params = {}
        if since:
            params["since"] = since
        if before:
            params["before"] = before

        url = f"/{self.workspace_id}/tasks"
        if params:
            query_string = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query_string}"

        r = self._get(url)
        data = r.json() or []
        return [TogglPlanTask(**task) for task in data]

    def create_task(self, payload: dict) -> TogglPlanTask:
        """Create a new task in the workspace.

        Args:
            payload: Task data including name, start_date, end_date, etc.

        Returns:
            Created TogglPlanTask object
        """
        r = self._post(f"/{self.workspace_id}/tasks", payload)
        return TogglPlanTask(**r.json())

    def update_task(self, task_id: int, payload: dict) -> TogglPlanTask:
        """Update an existing task.

        Args:
            task_id: ID of the task to update
            payload: Updated task data

        Returns:
            Updated TogglPlanTask object
        """
        r = self._put(f"/{self.workspace_id}/tasks/{task_id}", payload)
        return TogglPlanTask(**r.json())

    def delete_task(self, task_id: int):
        """Delete a task.

        Args:
            task_id: ID of the task to delete
        """
        self._delete(f"/{self.workspace_id}/tasks/{task_id}")

    def list_projects(self) -> list[dict]:
        """List all projects in the workspace.

        Returns:
            List of project dictionaries
        """
        r = self._get(f"/{self.workspace_id}/projects")
        return r.json() or []

    def create_project(
        self, name: str, color_id: int = 1, board_enabled: bool = False
    ) -> dict:
        """Create a new project.

        Args:
            name: Project name
            color_id: Color ID (default: 1)
            board_enabled: Whether to enable board view/statuses (default: False)

        Returns:
            Created project dictionary
        """
        payload = {"name": name, "color_id": color_id}
        if board_enabled:
            payload["board_enabled"] = True

        r = self._post(f"/{self.workspace_id}/projects", payload)
        return r.json()
