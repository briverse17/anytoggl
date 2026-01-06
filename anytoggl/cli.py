# anytoggl/cli.py
import typer
import time
from environs import Env
from anytoggl.sync_engine import SyncEngine
from anytoggl.plan_sync_engine import PlanSyncEngine
from anytoggl.clients.anytype import AnytypeClient
from anytoggl.clients.toggl import TogglClient
from anytoggl.clients.toggl_plan import TogglPlanClient
from anytoggl.scheduler import TaskScheduler

app = typer.Typer()
env = Env()
env.read_env()


def build_engine() -> SyncEngine:
    anytype = AnytypeClient(
        base_url=env.str("ANYTYPE_API_URL"),
        token=env.str("ANYTYPE_TOKEN"),
        space_id=env.str("ANYTYPE_SPACE_ID"),
    )
    toggl = TogglClient(
        api_token=env.str("TOGGL_API_TOKEN"),
        workspace_id=env.int("TOGGL_WORKSPACE_ID"),
    )
    return SyncEngine(anytype, toggl)


def build_plan_engine() -> PlanSyncEngine:
    anytype = AnytypeClient(
        base_url=env.str("ANYTYPE_API_URL"),
        token=env.str("ANYTYPE_TOKEN"),
        space_id=env.str("ANYTYPE_SPACE_ID"),
    )
    toggl_plan = TogglPlanClient(
        workspace_id=env.int("TOGGL_PLAN_WORKSPACE_ID"),
        client_id=env.str("TOGGL_PLAN_CLIENT_ID"),
        client_secret=env.str("TOGGL_PLAN_CLIENT_SECRET"),
        username=env.str("TOGGL_PLAN_USERNAME"),
        password=env.str("TOGGL_PLAN_PASSWORD"),
    )
    scheduler = TaskScheduler(
        start_hour=env.int("SCHEDULE_START_HOUR", 8),
        end_hour=env.int("SCHEDULE_END_HOUR", 20),
        default_duration_hours=env.int("DEFAULT_TASK_DURATION_HOURS", 1),
    )
    return PlanSyncEngine(
        anytype,
        toggl_plan,
        scheduler,
        default_project_name=env.str("TOGGL_PLAN_DEFAULT_PROJECT", "anytoggl"),
        default_estimated_minutes=env.int("TOGGL_PLAN_DEFAULT_MINUTES", 60),
    )


@app.command()
def once():
    """Run Toggl Track sync once"""
    engine = build_engine()
    engine.run()


@app.command()
def run(interval: int = 300):
    """Run Toggl Track sync continuously"""
    engine = build_engine()
    while True:
        engine.run()
        time.sleep(interval)


@app.command()
def doctor():
    """Check Toggl Track configuration"""
    try:
        engine = build_engine()
        print("✓ Toggl Track configuration OK")
    except Exception as e:
        print(f"✗ Toggl Track configuration error: {e}")
        raise typer.Exit(code=1)


@app.command()
def plan_once():
    """Run Toggl Plan sync once"""
    engine = build_plan_engine()
    engine.run()


@app.command()
def plan_run(interval: int = 300):
    """Run Toggl Plan sync continuously"""
    engine = build_plan_engine()
    while True:
        engine.run()
        time.sleep(interval)


@app.command()
def plan_doctor():
    """Check Toggl Plan configuration"""
    try:
        engine = build_plan_engine()
        print("✓ Toggl Plan configuration OK")

        # Test Anytype connection
        tasks = engine.anytype.search_tasks()
        print(f"✓ Found {len(tasks)} Anytype tasks tagged with 'Toggl'")

        # Test Toggl Plan connection
        plan_tasks = engine.toggl_plan.list_tasks()
        print(f"✓ Found {len(plan_tasks)} existing Toggl Plan tasks")

        # Show scheduler config
        print("\nScheduling configuration:")
        print(f"  Start hour: {engine.scheduler.start_hour}:00")
        print(f"  End hour: {engine.scheduler.end_hour}:00")
        print(f"  Default duration: {engine.scheduler.default_duration_hours} hour(s)")
        print("  → Tasks will be scheduled incrementally: 8-9, 9-10, 10-11, etc.")

        # Show sync config
        print("\nSync configuration:")
        print(f"  Default project: {engine.default_project_name}")
        print(f"  Default estimate: {engine.default_estimated_minutes} minutes")
        print("  → Tasks with Anytype project will use that project")
        print("  → Tasks without project will use default project")

    except Exception as e:
        print(f"✗ Toggl Plan configuration error: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
