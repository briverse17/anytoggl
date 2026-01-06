# anytoggl/anytype_client.py
import httpx
from anytoggl.http import RETRY
from anytoggl.models import AnytypeTask


class AnytypeClient:
    def __init__(self, base_url: str, token: str, space_id: str):
        self.space_id = space_id
        self.client = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
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
    def _patch(self, url: str, json: dict):
        r = self.client.patch(url, json=json)
        r.raise_for_status()
        return r

    def get_object(self, object_id: str) -> dict:
        """Get an object by ID."""
        r = self._get(f"/v1/spaces/{self.space_id}/objects/{object_id}")
        return r.json().get("object", {})

    def search_tasks(self) -> list[AnytypeTask]:
        """Search for tasks tagged with 'Toggl' in the configured space."""
        r = self._post(
            f"/v1/spaces/{self.space_id}/search",
            {"query": "", "types": ["task"]},
        )
        # Filter results to only include tasks with "Toggl" tag
        tasks = []
        for o in r.json().get("data", []):
            # Extract properties
            props = o.get("properties", [])

            # Check if task has Toggl tag (in properties with key='tag')
            tag_prop = next((p for p in props if p.get("key") == "tag"), None)
            if tag_prop:
                multi_select = tag_prop.get("multi_select", [])
                tag_names = [t.get("name", "") for t in multi_select]
            else:
                tag_names = []

            if "Toggl" not in tag_names:
                continue

            # Extract project name from linked_projects property
            project_prop = next(
                (p for p in props if p.get("key") == "linked_projects"), None
            )
            project_name = None
            if project_prop and project_prop.get("objects"):
                project_ids = project_prop.get("objects", [])
                if project_ids:
                    # IDs are strings, need to fetch the object to get name
                    first_project_id = project_ids[0]
                    if isinstance(first_project_id, str):
                        try:
                            project_obj = self.get_object(first_project_id)
                            project_name = project_obj.get("name")
                        except Exception:
                            pass  # Skip if can't fetch project
                    elif isinstance(first_project_id, dict):
                        project_name = first_project_id.get("name")

            # Extract done/status
            done_prop = next((p for p in props if p.get("key") == "done"), None)
            is_done = done_prop.get("checkbox", False) if done_prop else False

            status_prop = next((p for p in props if p.get("key") == "status"), None)
            if is_done:
                status = "Done"
            elif status_prop and status_prop.get("select"):
                status = status_prop["select"].get("name", "To Do")
            else:
                status = "To Do"

            # Extract toggl_track_id if exists (renamed from toggl_id)
            toggl_track_prop = next(
                (p for p in props if p.get("key") == "toggl_track_id"), None
            )
            toggl_track_id = toggl_track_prop.get("text") if toggl_track_prop else None

            # Extract toggl_plan_id if exists
            toggl_plan_prop = next(
                (p for p in props if p.get("key") == "toggl_plan_id"), None
            )
            toggl_plan_id = toggl_plan_prop.get("text") if toggl_plan_prop else None

            # Extract start_date if exists
            start_date_prop = next(
                (p for p in props if p.get("key") == "start_date"), None
            )
            start_date = start_date_prop.get("date") if start_date_prop else None

            # Extract end_date if exists
            end_date_prop = next((p for p in props if p.get("key") == "end_date"), None)
            end_date = end_date_prop.get("date") if end_date_prop else None

            # Extract last_modified_date
            modified_prop = next(
                (p for p in props if p.get("key") == "last_modified_date"), None
            )
            last_modified = modified_prop.get("date") if modified_prop else None

            tasks.append(
                AnytypeTask(
                    id=o["id"],
                    name=o.get("name", ""),
                    description=o.get("snippet"),
                    status=status,
                    project=project_name,
                    toggl_track_id=toggl_track_id,
                    toggl_plan_id=toggl_plan_id,
                    last_modified=last_modified,
                    start_date=start_date,
                    end_date=end_date,
                )
            )
        return tasks

    def update_task(self, object_id: str, details: dict):
        """Update a task in the configured space."""
        self._patch(f"/v1/spaces/{self.space_id}/objects/{object_id}", details)
