from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, field_validator

MAX_TAGS = 10
MAX_TAG_LENGTH = 30


class TaskStatus(str, Enum):
    TODO = "ToDo"
    IN_PROGRESS = "InProgress"
    DONE = "Done"


class TaskPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


def _validate_title(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("title must not be empty or whitespace-only")
    if len(stripped) > 200:
        raise ValueError("title must be at most 200 characters")
    return stripped


def _validate_tags(value: list[str]) -> list[str]:
    if len(value) > MAX_TAGS:
        raise ValueError(f"at most {MAX_TAGS} tags are allowed")
    cleaned: list[str] = []
    for tag in value:
        stripped = tag.strip()
        if not stripped:
            raise ValueError("tags must not be empty or whitespace-only")
        if len(stripped) > MAX_TAG_LENGTH:
            raise ValueError(f"each tag must be at most {MAX_TAG_LENGTH} characters")
        cleaned.append(stripped)
    return cleaned


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: Optional[str] = None
    due_date: Optional[date] = None
    tags: list[str] = []

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _validate_title(value)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        return _validate_tags(value)


class TaskUpdate(BaseModel):
    """Client payload for `PATCH /tasks/{id}`.

    Every field defaults to `None` so a request can touch just one field;
    an omitted field is left unchanged (see `storage.update_task`'s use of
    `model_dump(exclude_unset=True)`). `None` is only a valid *value* for
    `assignee` and `due_date`, which are genuinely nullable on
    `TaskResponse` - sending them as `null` clears them. `title`,
    `description`, `status`, and `priority` are NOT nullable on
    `TaskResponse`, so an explicit `null` for any of those is rejected as
    invalid input (422) rather than silently accepted and stored, which
    would leave the task in a state its own response model claims is
    impossible (e.g. a `TaskResponse.title: str` that's actually `None`).
    """

    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[str] = None
    due_date: Optional[date] = None
    tags: Optional[list[str]] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: Optional[str]) -> str:
        if value is None:
            raise ValueError("title must not be null")
        return _validate_title(value)

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: Optional[str]) -> str:
        if value is None:
            raise ValueError("description must not be null")
        return value

    @field_validator("status")
    @classmethod
    def validate_status_not_null(cls, value: Optional[TaskStatus]) -> TaskStatus:
        if value is None:
            raise ValueError("status must not be null")
        return value

    @field_validator("priority")
    @classmethod
    def validate_priority_not_null(cls, value: Optional[TaskPriority]) -> TaskPriority:
        if value is None:
            raise ValueError("priority must not be null")
        return value

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: Optional[list[str]]) -> list[str]:
        if value is None:
            raise ValueError("tags must not be null")
        return _validate_tags(value)


class TaskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee: Optional[str]
    due_date: Optional[date] = None
    tags: list[str] = []
    overdue: bool = False
    created_at: datetime
    updated_at: datetime


def new_task_id() -> str:
    return uuid4().hex


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
