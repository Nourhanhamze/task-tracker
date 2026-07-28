from datetime import date
from typing import Optional

from app.models import TaskStatus

VALID_TRANSITIONS: frozenset[tuple[TaskStatus, TaskStatus]] = frozenset(
    {
        (TaskStatus.TODO, TaskStatus.IN_PROGRESS),
        (TaskStatus.IN_PROGRESS, TaskStatus.DONE),
        (TaskStatus.DONE, TaskStatus.IN_PROGRESS),
    }
)


def validate_status_transition(current: TaskStatus, new: TaskStatus) -> bool:
    return (current, new) in VALID_TRANSITIONS


def compute_overdue(due_date: Optional[date], status: TaskStatus, today: Optional[date] = None) -> bool:
    """A task is overdue if it has a due date in the past and is not Done."""
    if due_date is None or status == TaskStatus.DONE:
        return False
    reference = today or date.today()
    return due_date < reference
