"""In-memory task storage.

A single process-lifetime dict, not a database - see
docs/decisions/in-memory-task-storage.md for why. All functions here are
plain, synchronous, and side-effect-only on `_tasks`; no HTTP or
validation concerns belong in this module.
"""

from typing import Optional

from app.models import TaskCreate, TaskResponse, TaskUpdate, new_task_id, utc_now

_tasks: dict[str, TaskResponse] = {}


def add_task(payload: TaskCreate) -> TaskResponse:
    """Create and store a new task.

    Builds the response from `payload.model_dump()` rather than listing
    fields by hand, so every field on `TaskCreate` (including ones added
    later) reaches `TaskResponse` automatically.

    Args:
        payload: Already-validated task creation data.

    Returns:
        TaskResponse: The stored task, with a new id and matching
            created_at/updated_at timestamps.
    """
    now = utc_now()
    task = TaskResponse(
        id=new_task_id(),
        created_at=now,
        updated_at=now,
        **payload.model_dump(),
    )
    _tasks[task.id] = task
    return task


def get_all_tasks() -> list[TaskResponse]:
    """Return every stored task.

    Returns:
        list[TaskResponse]: All tasks, insertion order, `[]` if none exist.
    """
    return list(_tasks.values())


def get_task_by_id(task_id: str) -> Optional[TaskResponse]:
    """Look up one task.

    Args:
        task_id: The task's id.

    Returns:
        TaskResponse | None: The task, or None if `task_id` is not stored.
    """
    return _tasks.get(task_id)


def update_task(task_id: str, payload: TaskUpdate) -> Optional[TaskResponse]:
    """Apply a partial update to a stored task.

    Uses `model_dump(exclude_unset=True)` so fields the client did not
    include in the request body are left untouched - this is what makes
    "update the title, keep the existing tags" work without the caller
    having to resend the tags.

    Args:
        task_id: The task's id.
        payload: Fields to change (already validated and, for `status`,
            already checked against the transition rules by the caller -
            this function does not re-check transitions).

    Returns:
        TaskResponse | None: The updated task, or None if `task_id` is not
            stored (caller is responsible for turning that into a 404).
    """
    existing = _tasks.get(task_id)
    if existing is None:
        return None
    updates = payload.model_dump(exclude_unset=True)
    updated = existing.model_copy(update={**updates, "updated_at": utc_now()})
    _tasks[task_id] = updated
    return updated


def delete_task(task_id: str) -> bool:
    """Delete a stored task.

    Args:
        task_id: The task's id.

    Returns:
        bool: True if a task was deleted, False if `task_id` was not
            stored (caller is responsible for turning that into a 404).
    """
    if task_id not in _tasks:
        return False
    del _tasks[task_id]
    return True


def _reset() -> None:
    """Clear all stored tasks. Test-only; called by the autouse pytest fixture."""
    _tasks.clear()
