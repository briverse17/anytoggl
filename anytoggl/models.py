# anytoggl/models.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AnytypeTask(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str
    project: Optional[str] = None
    toggl_track_id: Optional[str] = None  # For Track sync (renamed from toggl_id)
    toggl_plan_id: Optional[str] = None  # For Plan sync
    last_modified: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    start_time: Optional[str] = None  # Scheduled start time (HH:MM)
    end_time: Optional[str] = None  # Scheduled end time (HH:MM)


class TogglTimeEntry(BaseModel):
    id: int
    description: Optional[str] = None
    project_id: Optional[int] = None
    start: datetime
    stop: Optional[datetime] = None
    duration: int  # negative = running timer
    at: datetime  # last updated timestamp


class TogglPlanTask(BaseModel):
    id: int
    name: Optional[str] = None  # Can be None in API responses
    start_date: datetime  # ISO 8601 format
    end_date: datetime  # ISO 8601 format
    user_id: Optional[int] = None
    project_id: Optional[int] = None
    notes: Optional[str] = None  # Contains description and #anytype_id marker
    status: Optional[str] = None
    tags: Optional[list[str]] = None
    updated_at: datetime
