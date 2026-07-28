from typing import Optional

from app.models import TaskCreate, TaskResponse, TaskUpdate, new_task_id, utc_now

_tasks: dict[str, TaskResponse] = {}


def add_task(payload: TaskCreate) -> TaskResponse:
    now = utc_now()
    task = TaskResponse(
        id=new_task_id(),
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        assignee=payload.assignee,
        created_at=now,
        updated_at=now,
    )
    _tasks[task.id] = task
    return task


def get_all_tasks() -> list[TaskResponse]:
    return list(_tasks.values())


def get_task_by_id(task_id: str) -> Optional[TaskResponse]:
    return _tasks.get(task_id)


def update_task(task_id: str, payload: TaskUpdate) -> Optional[TaskResponse]:
    existing = _tasks.get(task_id)
    if existing is None:
        return None
    updates = payload.model_dump(exclude_unset=True)
    updated = existing.model_copy(update={**updates, "updated_at": utc_now()})
    _tasks[task_id] = updated
    return updated


def delete_task(task_id: str) -> bool:
    if task_id not in _tasks:
        return False
    del _tasks[task_id]
    return True


def _reset() -> None:
    _tasks.clear()
