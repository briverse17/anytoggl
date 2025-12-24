# anytoggl/cli.py
import time
import typer
from environs import Env

from anytoggl.clients.anytype import AnytypeClient
from anytoggl.clients.toggl import TogglClient
from anytoggl.sync_engine import SyncEngine

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
        token=env.str("TOGGL_API_TOKEN"),
        workspace_id=env.int("TOGGL_WORKSPACE_ID"),
    )
    return SyncEngine(anytype, toggl)


@app.command()
def once():
    """Run sync once"""
    engine = build_engine()
    engine.run()


@app.command()
def run(interval: int = typer.Option(300, help="Sync interval in seconds")):
    """Run sync loop"""
    engine = build_engine()
    while True:
        engine.run()
        time.sleep(interval)


@app.command()
def doctor():
    """Check configuration"""
    required = [
        "ANYTYPE_API_URL",
        "ANYTYPE_TOKEN",
        "ANYTYPE_SPACE_ID",
        "TOGGL_API_TOKEN",
        "TOGGL_WORKSPACE_ID",
    ]
    missing = [k for k in required if not env.str(k, default=None)]
    if missing:
        typer.echo(f"Missing env vars: {missing}")
        raise typer.Exit(1)
    typer.echo("Configuration OK")


if __name__ == "__main__":
    app()
