"""Business rules that don't belong to a single model or route.

Kept separate from app/models.py (data shape) and app/main.py (HTTP
wiring) so the actual rules - which transitions are legal, what counts as
overdue - are in one place a reviewer can read without touching routing
code.
"""

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
    """Check whether a status change is allowed.

    Same-status "transitions" (e.g. InProgress -> InProgress) are
    intentionally not in `VALID_TRANSITIONS` and are therefore rejected as
    no-ops, matching the six-case transition matrix this project is tested
    against (200, 200, 422, 200, 422, 200).

    Args:
        current: The task's current status.
        new: The requested new status.

    Returns:
        bool: True if `(current, new)` is in `VALID_TRANSITIONS`.
    """
    return (current, new) in VALID_TRANSITIONS


def compute_overdue(due_date: Optional[date], status: TaskStatus, today: Optional[date] = None) -> bool:
    """Determine whether a task is overdue right now.

    A task is overdue if it has a due date strictly before the reference
    date and its status is not Done. This is a pure function of its
    inputs - it does not read or write storage - so callers must call it
    fresh on every read rather than trusting a previously stored value.

    Args:
        due_date: The task's due date, or None if it has none.
        status: The task's current status.
        today: Reference date to compare against; defaults to
            `date.today()`. Exposed as a parameter for testability.

    Returns:
        bool: True if `due_date` is in the past relative to `today` and
            `status` is not Done. False if `due_date` is None, in the
            future, equal to `today`, or `status` is Done.
    """
    if due_date is None or status == TaskStatus.DONE:
        return False
    reference = today or date.today()
    return due_date < reference
