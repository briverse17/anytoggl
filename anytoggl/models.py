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
    toggl_id: Optional[str] = None
    last_modified: Optional[datetime] = None


class TogglTimeEntry(BaseModel):
    id: int
    description: Optional[str] = None
    project_id: Optional[int] = None
    start: datetime
    stop: Optional[datetime] = None
    duration: int  # negative = running timer
    at: datetime  # last updated timestamp
