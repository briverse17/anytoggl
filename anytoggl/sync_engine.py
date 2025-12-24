# anytoggl/sync_engine.py
from datetime import datetime, timezone
from anytoggl.clients.anytype import AnytypeClient
from anytoggl.clients.toggl import TogglClient


class SyncEngine:
    def __init__(self, anytype: AnytypeClient, toggl: TogglClient):
        self.anytype = anytype
        self.toggl = toggl

    def run(self):
        any_tasks = self.anytype.search_tasks()
        toggl_entries = self.toggl.list_time_entries()
        projects = self.toggl.list_projects()

        # Index Toggl entries by ID for quick lookup
        toggl_by_id = {str(e.id): e for e in toggl_entries}

        for task in any_tasks:
            # Resolve project
            project_id = None
            if task.project:
                project_id = projects.get(task.project)
                if project_id is None:
                    project_id = self.toggl.create_project(task.project)
                    projects[task.project] = project_id

            # Create in Toggl if no toggl_id exists
            if not task.toggl_id:
                # Create a time entry for this task
                # Use current time as start, duration=-1 for running timer if "In Progress"
                now = datetime.now(timezone.utc).isoformat()
                is_running = task.status == "In Progress"

                payload = {
                    "description": task.name,
                    "start": now,
                    "duration": -1
                    if is_running
                    else 0,  # -1 = running, 0 = stopped immediately
                }
                if project_id:
                    payload["project_id"] = project_id

                toggl_entry = self.toggl.create_time_entry(payload)
                self.anytype.update_task(task.id, {"toggl_id": str(toggl_entry.id)})
                continue

            # Update flow - check if entry exists in Toggl
            toggl_entry = toggl_by_id.get(task.toggl_id)
            if not toggl_entry:
                continue

            # Compare timestamps for sync direction
            at_ts = task.last_modified
            tg_ts = toggl_entry.at

            # Skip if no valid timestamp comparison available
            if not at_ts or not tg_ts:
                continue

            # Anytype newer → push to Toggl
            if at_ts > tg_ts:
                payload = {"description": task.name}
                if project_id:
                    payload["project_id"] = project_id
                self.toggl.update_time_entry(toggl_entry.id, payload)

            # Toggl newer → pull to Anytype
            elif tg_ts > at_ts:
                updates = {}
                if toggl_entry.description:
                    updates["name"] = toggl_entry.description
                # If entry is running (negative duration), set to In Progress
                if toggl_entry.duration < 0:
                    updates["status"] = "In Progress"
                elif toggl_entry.stop:
                    updates["status"] = "Done"
                if updates:
                    self.anytype.update_task(task.id, updates)
