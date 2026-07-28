# In-Memory Dict as the Task Storage Layer

## Context

The Task Tracker needed somewhere to persist tasks across requests within a
single running process. This decision was made in Module 1 while scaffolding
the FastAPI skeleton, and it's still the storage layer at the end of the
course — every feature added since (status transitions, due dates, tags)
was built on top of it without changing its shape, so it's worth writing
down now why it's still the right call and where it stops being one.

## Decision

`app/storage.py` holds tasks in a single module-level `dict[str,
TaskResponse]`, keyed by task id, with plain functions (`add_task`,
`get_all_tasks`, `get_task_by_id`, `update_task`, `delete_task`, `_reset`)
as the only way anything else in the app touches it. No ORM, no SQL, no
file persistence.

## Alternatives considered

- **SQLite via SQLModel/SQLAlchemy.** This is the alternative I actually
  went back and forth on. It's more realistic — real query filtering
  instead of Python list comprehensions, and data survives a restart. I
  rejected it for this project specifically because the course scope
  (Module 1) explicitly calls out "production database" as something to
  defer, and because every added feature so far (tags, due-date filtering)
  has stayed simple enough that a dict-and-list-comprehension approach is
  still genuinely easier to read than an ORM query would be for the same
  filter.
- **A JSON file on disk.** This would have given us data that survives a
  restart without pulling in a database dependency. I rejected it because
  it adds a real failure mode (concurrent writes, partial writes on crash)
  for a benefit — persistence across restarts — that doesn't actually
  matter for a course project that gets `_reset()` between every test
  anyway.
- **A generic "swap the backend later" abstraction (repository interface,
  storage protocol).** An AI-assisted first draft of this note suggested
  introducing a `StorageBackend` protocol now so a future database swap
  would be "clean." I rejected this specifically: there is exactly one
  storage backend in this codebase and has been for the whole course. An
  interface with one implementation isn't abstraction, it's a layer of
  indirection with no second caller to justify it — YAGNI, not
  engineering discipline.

## Trade-offs

What the dict makes easier: every storage function is a few lines, testable
without mocking anything, and the `_reset()` autouse pytest fixture (see
`tests/conftest.py`) gives every test a clean slate with zero setup
ceremony. Filtering (`GET /tasks?status=&priority=&tag=&overdue=`) is plain
Python list comprehensions instead of query-building.

What it makes worse: nothing persists across a restart — stop the
`uvicorn` process and every task is gone. There's no query optimization at
all; `get_all_tasks()` plus a Python-side filter is O(n) on every list
call, which is irrelevant at course-project scale (dozens of tasks) and
would not be irrelevant at real scale. It's also single-process only — two
`uvicorn` workers would each have their own independent, inconsistent
`_tasks` dict, which is a real problem the moment this needs concurrency
handled by more than the CI test suite's single test process.

## Consequences

Every route in `app/main.py` calls straight into `app/storage.py` with no
data-access layer to route around, which is exactly why the storage
functions had to be careful (`add_task` rebuilding `TaskResponse` from
`payload.model_dump()` rather than hand-listing fields — see
`docs/verification.md` — is a direct consequence of there being no schema
layer to catch a missed field for you). Docker/CI both inherit this: the
container has no volume or database service to configure, and CI doesn't
need a test-database fixture, both of which kept this project's DevOps
setup smaller than it would otherwise be.

## Open questions

- At what task count would the O(n) filtering actually start to matter in
  practice? I don't have a real answer — I'd want to actually load-test it
  with a few thousand synthetic tasks before claiming a number.
- If this ever needs to survive a restart, is SQLite really the next step,
  or would something even simpler (a single JSON file, loaded on startup
  and written on every mutation) cover the actual requirement without the
  ORM overhead? I lean toward SQLite mainly because the query filtering
  gets meaningfully easier, not because file-based persistence itself is
  wrong.
- I would do this differently if I were starting the course over: I'd
  still choose the dict, but I'd write this decision note in Module 1
  instead of Module 5's End-of-Course pass — writing it now, after the
  fact, meant reconstructing the Module 1 reasoning from memory instead of
  capturing it while it was fresh.
