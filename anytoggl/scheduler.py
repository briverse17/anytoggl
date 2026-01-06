# anytoggl/scheduler.py
from datetime import datetime, timedelta
from loguru import logger
from anytoggl.models import AnytypeTask, TogglPlanTask


class TaskScheduler:
    """Automatic task scheduler for Toggl Plan integration."""

    def __init__(
        self,
        start_hour: int = 8,
        end_hour: int = 20,
        default_duration_hours: int = 1,
    ):
        """Initialize task scheduler.

        Args:
            start_hour: Daily work start hour (0-23)
            end_hour: Daily work end hour (0-23)
            default_duration_hours: Default task duration in hours
        """
        self.start_hour = start_hour
        self.end_hour = end_hour
        self.default_duration_hours = default_duration_hours

    def schedule_tasks(
        self, anytype_tasks: list[AnytypeTask], plan_tasks: list[TogglPlanTask]
    ) -> list[AnytypeTask]:
        """Schedule tasks with automatic time assignment.

        For tasks without start_date/end_date, assigns them sequentially starting from today,
        with incremental time windows (e.g., 8-9, 9-10, 10-11, etc.).

        Args:
            anytype_tasks: List of Anytype tasks
            plan_tasks: List of existing Toggl Plan tasks (for reference)

        Returns:
            List of tasks with scheduling information added
        """
        scheduled_tasks = []
        current_date = datetime.now().date()
        current_hour = self.start_hour

        for task in anytype_tasks:
            # If task already has dates, keep them and add time window
            if task.start_date and task.end_date:
                # Add time window if not already set
                if not hasattr(task, "start_time") or not task.start_time:
                    # Assign incremental time window
                    task.start_time = f"{current_hour:02d}:00"
                    end_hour = current_hour + self.default_duration_hours

                    # Wrap to next day if exceeding end_hour
                    if end_hour > self.end_hour:
                        current_hour = self.start_hour
                        end_hour = current_hour + self.default_duration_hours

                    task.end_time = f"{end_hour:02d}:00"
                    current_hour = end_hour

                    logger.debug(
                        f"Assigned time window {task.start_time}-{task.end_time} to '{task.name}'"
                    )

                scheduled_tasks.append(task)
                continue

            # Auto-schedule tasks without dates
            task.start_date = current_date
            task.end_date = current_date
            task.start_time = f"{current_hour:02d}:00"

            end_hour = current_hour + self.default_duration_hours

            # If exceeding work hours, move to next day
            if end_hour > self.end_hour:
                current_date = current_date + timedelta(days=1)
                current_hour = self.start_hour
                end_hour = current_hour + self.default_duration_hours

                task.start_date = current_date
                task.end_date = current_date
                task.start_time = f"{current_hour:02d}:00"

            task.end_time = f"{end_hour:02d}:00"
            current_hour = end_hour

            logger.info(
                f"Auto-scheduled '{task.name}': {task.start_date} {task.start_time}-{task.end_time}"
            )

            scheduled_tasks.append(task)

        return scheduled_tasks
