import re
import datetime
from loguru import logger
from anytoggl.clients.anytype import AnytypeClient
from anytoggl.clients.toggl_plan import TogglPlanClient
from anytoggl.scheduler import TaskScheduler


class PlanSyncEngine:
    """Sync engine for Anytype → Toggl Plan synchronization."""

    def __init__(
        self,
        anytype: AnytypeClient,
        toggl_plan: TogglPlanClient,
        scheduler: TaskScheduler,
        default_project_name: str = "Anytype Sync",
        default_estimated_minutes: int = 60,
    ):
        """Initialize Plan sync engine.

        Args:
            anytype: Anytype API client
            toggl_plan: Toggl Plan API client
            scheduler: Task scheduler for auto-scheduling
            default_project_name: Default project name for tasks
            default_estimated_minutes: Default time estimate in minutes
        """
        self.anytype = anytype
        self.toggl_plan = toggl_plan
        self.scheduler = scheduler
        self.default_project_name = default_project_name
        self.default_estimated_minutes = default_estimated_minutes
        self.default_project_id = None
        self.project_status_maps = {}  # project_id -> {type/name: status_id}

    def _cache_project_statuses(self, project: dict):
        """Cache status IDs for a project.

        Args:
            project: Project object from API including 'statuses' list
        """
        if "statuses" not in project:
            return

        pid = project["id"]
        status_map = {}
        for status in project["statuses"]:
            sid = status["id"]
            stype = status.get("type")
            sname = status.get("name")

            # Map both type and name for flexibility
            if stype:
                status_map[stype] = sid
            if sname:
                status_map[sname.lower()] = sid

        self.project_status_maps[pid] = status_map
        logger.debug(f"Cached statuses for project {pid}: {status_map}")

    def _ensure_default_project(self):
        """Ensure default project exists and cache its ID."""
        if self.default_project_id is not None:
            return self.default_project_id

        # Find or create default project
        projects = self.toggl_plan.list_projects()
        for project in projects:
            self._cache_project_statuses(project)
            if project.get("name") == self.default_project_name:
                self.default_project_id = project["id"]
                logger.info(
                    f"Found default project '{self.default_project_name}' (ID: {self.default_project_id})"
                )
                return self.default_project_id

        # Create project if not found
        logger.info(f"Creating default project '{self.default_project_name}'...")
        project = self.toggl_plan.create_project(
            self.default_project_name, board_enabled=True
        )
        # Note: Create project might return partial obj, so we should fetch details or list again if statuses missing
        # But for now assume it might lack statuses, so we rely on future fetches or defaults
        self.default_project_id = project["id"]
        # Try to cache if statuses present
        self._cache_project_statuses(project)

        logger.info(f"Created default project (ID: {self.default_project_id})")
        return self.default_project_id

    def _get_project_id(self, task, projects_cache: dict[str, int]) -> int:
        """Get project ID for a task, using Anytype project if available.

        Args:
            task: Anytype task
            projects_cache: Cache of project name -> ID mappings

        Returns:
            Project ID to use for this task
        """
        # If task has a project, try to find/create it in Toggl Plan
        if hasattr(task, "project") and task.project:
            project_name = task.project

            # Check cache first
            if project_name in projects_cache:
                return projects_cache[project_name]

            # Find or create project
            projects = self.toggl_plan.list_projects()
            for project in projects:
                self._cache_project_statuses(project)
                if project.get("name") == project_name:
                    project_id = project["id"]
                    projects_cache[project_name] = project_id
                    logger.debug(
                        f"Using existing project '{project_name}' (ID: {project_id})"
                    )
                    return project_id

            # Create new project
            logger.info(f"Creating new project '{project_name}'...")
            # Enable board to get statuses immediately
            project = self.toggl_plan.create_project(project_name, board_enabled=True)
            project_id = project["id"]
            self._cache_project_statuses(project)
            projects_cache[project_name] = project_id
            logger.info(f"Created project '{project_name}' (ID: {project_id})")
            return project_id

        # Fall back to default project
        return self._ensure_default_project()

    def _get_status_id(self, project_id: int, anytype_status: str) -> int | None:
        """Map Anytype status to Toggl Plan status ID for a specific project.

        Args:
            project_id: Toggl Plan project ID
            anytype_status: Anytype task status string

        Returns:
            Plan Status ID or None if not found
        """
        if not anytype_status:
            # Map empty/None to "No status" or "To-do"
            anytype_status = "No status"

        status_map = self.project_status_maps.get(project_id, {})

        # Map Anytype status -> Toggl Plan type/name key
        # We try to match Anytype status to Toggl Plan 'type' or 'name' (lowercase)

        target_key = "todo"  # Default fallback

        if anytype_status == "Done":
            target_key = "done"
        elif anytype_status == "In Progress":
            target_key = "in_progress"
        elif anytype_status == "To Do":
            target_key = "todo"
        elif anytype_status == "Blocked":
            target_key = "blocked"
        elif anytype_status == "No status":
            # Try to find "no status" name or type
            if "no status" in status_map:
                return status_map["no status"]
            return None  # Let API decide default

        # Try to find target_key in map (checking type first)
        if target_key in status_map:
            return status_map[target_key]

        # Try direct name match (lowercase)
        lower_status = anytype_status.lower()
        if lower_status in status_map:
            return status_map[lower_status]

        # Fallback to 'todo' if exists
        return status_map.get("todo")

    def _map_status_string(self, anytype_status: str) -> str:
        """Map Anytype task status to Toggl Plan status string.
        Used as fallback for projects without custom statuses.
        """
        if not anytype_status:
            return "to-do"  # Default

        status_map = {
            "Done": "done",
            "In Progress": "in_progress",
            "To Do": "to-do",
            "Backlog": "to-do",
            "Blocked": "blocked",
            "Canceled": "to-do",
        }
        return status_map.get(anytype_status, "to-do")

    def _build_notes(self, description: str | None, anytype_id: str) -> str:
        """Build notes field with anytype_id marker appended.

        Args:
            description: Optional task description
            anytype_id: Anytype task ID

        Returns:
            Notes string with #anytype_id marker
        """
        parts = []
        if description:
            parts.append(description)
        parts.append(f"#anytype_id:{anytype_id}")
        return "\n\n".join(parts)

    def _extract_anytype_id(self, notes: str | None) -> str | None:
        """Extract anytype_id from notes field.

        Args:
            notes: Notes field from Toggl Plan task

        Returns:
            Extracted anytype_id or None if not found
        """
        if not notes:
            return None

        # Look for #anytype_id:xxx pattern
        match = re.search(r"#anytype_id:(\S+)", notes)
        if match:
            return match.group(1)
        return None

    def run(self):
        """Run one-way sync from Anytype to Toggl Plan."""
        logger.info("Starting Toggl Plan sync...")

        # Ensure default project exists
        self._ensure_default_project()

        # Cache for project name -> ID mappings
        projects_cache = {}

        # Fetch all Anytype tasks tagged with "Toggl"
        anytype_tasks = self.anytype.search_tasks()
        logger.info(f"Found {len(anytype_tasks)} Anytype tasks tagged with 'Toggl'")

        # Fetch all existing Toggl Plan tasks
        plan_tasks = self.toggl_plan.list_tasks()
        logger.info(f"Found {len(plan_tasks)} existing Toggl Plan tasks")

        # Run scheduling algorithm to assign times to unscheduled tasks
        scheduled_tasks = self.scheduler.schedule_tasks(anytype_tasks, plan_tasks)

        # Index Plan tasks by ID for quick lookup
        plan_by_id = {str(task.id): task for task in plan_tasks}

        # Also index by anytype_id extracted from notes
        plan_by_anytype_id = {}
        for task in plan_tasks:
            # Try to extract anytype_id from notes
            anytype_id = self._extract_anytype_id(getattr(task, "notes", None))
            if anytype_id:
                plan_by_anytype_id[anytype_id] = task

        # Track sync statistics
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for task in scheduled_tasks:
            # Skip tasks without scheduling (couldn't be scheduled)
            if not task.start_date or not task.end_date:
                logger.warning(
                    f"Skipping task '{task.name}' - no start/end date available"
                )
                skipped_count += 1
                continue

            # Get scheduled time window (from scheduler)
            start_time = getattr(task, "start_time", None)
            end_time = getattr(task, "end_time", None)

            if not start_time or not end_time:
                logger.warning(f"Skipping task '{task.name}' - no time window assigned")
                skipped_count += 1
                continue

            # Check if task exists in Toggl Plan (by toggl_plan_id or anytype_id)
            plan_task = None
            if task.toggl_plan_id:
                plan_task = plan_by_id.get(task.toggl_plan_id)
            if not plan_task:
                # Try to find by anytype_id in notes
                plan_task = plan_by_anytype_id.get(task.id)
                if plan_task:
                    logger.info(
                        f"Matched task '{task.name}' via notes (ID: {plan_task.id}). Healing link..."
                    )
                    try:
                        self.anytype.update_task(
                            task.id, {"toggl_plan_id": str(plan_task.id)}
                        )
                    except Exception as e:
                        logger.error(f"Failed to heal link for '{task.name}': {e}")

            # Create in Toggl Plan if doesn't exist
            if not plan_task:
                try:
                    # Get project ID for this task (Anytype project or default)
                    project_id = self._get_project_id(task, projects_cache)
                    status_id = self._get_status_id(project_id, task.status)

                    # Build notes with anytype_id marker
                    notes = self._build_notes(task.description, task.id)

                    payload = {
                        "name": task.name,
                        "start_date": task.start_date.strftime("%Y-%m-%d"),
                        "end_date": task.end_date.strftime("%Y-%m-%d"),
                        "start_time": start_time,  # Use scheduled time
                        "end_time": end_time,  # Use scheduled time
                        "user_id": self.toggl_plan.user_id,  # Required field
                        "project_id": project_id,  # Anytype project or default
                        "notes": notes,  # Description + anytype_id marker
                        "estimated_minutes": self.default_estimated_minutes,
                    }

                    if status_id:
                        payload["plan_status_id"] = status_id
                    else:
                        # Fallback for projects without custom statuses
                        payload["status"] = self._map_status_string(task.status)

                    # Create task in Toggl Plan
                    created_plan_task = self.toggl_plan.create_task(payload)

                    # Save Plan task ID back to Anytype
                    self.anytype.update_task(
                        task.id, {"toggl_plan_id": str(created_plan_task.id)}
                    )

                    logger.info(
                        f"Created Toggl Plan task '{task.name}' (ID: {created_plan_task.id}, Time: {start_time}-{end_time})"
                    )
                    created_count += 1

                except Exception as e:
                    logger.error(f"Failed to create Toggl Plan task '{task.name}': {e}")
                    skipped_count += 1

                continue

            # Update flow - compare timestamps
            anytype_ts = task.last_modified
            plan_ts = plan_task.updated_at

            # Skip if no valid timestamp comparison available
            if not anytype_ts or not plan_ts:
                logger.debug(
                    f"Skipping '{task.name}' - no timestamp comparison available"
                )
                skipped_count += 1
                continue

            # Ensure both are timezone aware
            if anytype_ts.tzinfo is None:
                anytype_ts = anytype_ts.replace(tzinfo=datetime.timezone.utc)
            if plan_ts.tzinfo is None:
                plan_ts = plan_ts.replace(tzinfo=datetime.timezone.utc)

            # Anytype newer → push to Toggl Plan
            if anytype_ts > plan_ts:
                try:
                    # Retrieve project_id to lookup status mapping
                    # Task might have different project in Plan than expected, but we prioritize current Anytype project
                    project_id = self._get_project_id(task, projects_cache)
                    status_id = self._get_status_id(project_id, task.status)

                    # Build notes with anytype_id marker (preserve or add)
                    notes = self._build_notes(task.description, task.id)

                    payload = {
                        "name": task.name,
                        "start_date": task.start_date.strftime("%Y-%m-%d"),
                        "end_date": task.end_date.strftime("%Y-%m-%d"),
                        "start_time": start_time,  # Use scheduled time
                        "end_time": end_time,  # Use scheduled time
                        "notes": notes,
                        "estimated_minutes": self.default_estimated_minutes,
                    }

                    if status_id:
                        payload["plan_status_id"] = status_id
                    else:
                        # Fallback for projects without custom statuses
                        payload["status"] = self._map_status_string(task.status)

                    self.toggl_plan.update_task(plan_task.id, payload)

                    logger.info(
                        f"Updated Toggl Plan task '{task.name}' (Time: {start_time}-{end_time})"
                    )
                    updated_count += 1

                except Exception as e:
                    logger.error(f"Failed to update Toggl Plan task '{task.name}': {e}")
                    skipped_count += 1

            else:
                # Plan is newer or same - skip (one-way sync)
                logger.debug(f"Skipping '{task.name}' - Toggl Plan is newer or same")
                skipped_count += 1

        logger.info(
            f"Sync complete: {created_count} created, {updated_count} updated, {skipped_count} skipped"
        )
