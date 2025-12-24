# anytoggl/toggl_client.py
import httpx
from anytoggl.http import RETRY
from anytoggl.models import TogglTimeEntry


class TogglClient:
    def __init__(self, token: str, workspace_id: int):
        self.wid = workspace_id
        self.client = httpx.Client(
            base_url="https://api.track.toggl.com/api/v9",
            auth=(token, "api_token"),
            headers={"Content-Type": "application/json"},
            timeout=10,
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

    def list_projects(self) -> dict[str, int]:
        """List all projects in the workspace."""
        r = self._get(f"/workspaces/{self.wid}/projects")
        return {p["name"]: p["id"] for p in r.json()}

    def create_project(self, name: str) -> int:
        """Create a new project in the workspace."""
        r = self._post(
            f"/workspaces/{self.wid}/projects",
            {"name": name, "active": True},
        )
        return r.json()["id"]

    def list_time_entries(self) -> list[TogglTimeEntry]:
        """List recent time entries for the user."""
        r = self._get("/me/time_entries")
        data = r.json() or []
        return [TogglTimeEntry(**t) for t in data]

    def create_time_entry(self, payload: dict) -> TogglTimeEntry:
        """Create a new time entry in the workspace."""
        # Ensure workspace_id is set
        payload["workspace_id"] = self.wid
        payload["created_with"] = "anytoggl"
        r = self._post(
            f"/workspaces/{self.wid}/time_entries",
            payload,
        )
        return TogglTimeEntry(**r.json())

    def update_time_entry(self, time_entry_id: int, payload: dict):
        """Update an existing time entry."""
        self._put(
            f"/workspaces/{self.wid}/time_entries/{time_entry_id}",
            payload,
        )
