# Architecture — Strategy C (Targeted Anchor Files)

**Context given for this pass:** only `app/main.py`, `app/models.py`, and
`app/storage.py`, re-read fresh immediately before writing this document.
Explicitly not read for this pass: `app/business_rules.py`, any file under
`frontend/`, `tests/`, or `docs/`. Where those files would be needed to
confirm something, it's marked "not visible from the files I read" below
rather than filled in from outside memory.

## System overview

A FastAPI app (`app/main.py`) exposing five task CRUD routes plus
`/health`, backed by an in-memory dict (`app/storage.py`) and validated by
Pydantic v2 models (`app/models.py`).

## Backend structure

- `app/models.py`: `TaskStatus` and `TaskPriority` string enums;
  `TaskCreate`/`TaskUpdate`/`TaskResponse` models, all with
  `extra="forbid"`; a `_validate_title` helper (strip, reject empty, max
  200 chars) and `_validate_tags` helper (strip each, reject empty, max 10
  tags, max 30 chars each — constants `MAX_TAGS`/`MAX_TAG_LENGTH` defined
  at module level); `new_task_id()` (`uuid4().hex`) and `utc_now()`
  helpers.
- `app/storage.py`: a single module-level `_tasks: dict[str,
  TaskResponse]`. Five functions: `add_task` (builds `TaskResponse` from
  `id`/`created_at`/`updated_at` plus `**payload.model_dump()` — notably
  *not* a hand-written field list, so every `TaskCreate` field flows
  through automatically), `get_all_tasks`, `get_task_by_id`, `update_task`
  (uses `model_dump(exclude_unset=True)` so omitted fields in a PATCH stay
  untouched), `delete_task`, and a test-only `_reset()`.
- `app/main.py`: `FastAPI()` app with `CORSMiddleware` allowing four
  hardcoded local origins (`localhost`/`127.0.0.1`, ports 5500 and 5173).
  Two private helpers: `_with_overdue` (imports `compute_overdue` from
  `app.business_rules` — not read in this pass — and recomputes it on
  every response rather than trusting the stored value) and
  `_get_task_or_404`. Five routes: `POST /tasks` (201), `GET /tasks` (200,
  filters by `status`/`priority`/`tag`/`overdue` query params), `GET
  /tasks/{id}` (200/404), `PATCH /tasks/{id}` (200/404/422 — imports
  `validate_status_transition` from `app.business_rules`, also not read in
  this pass), `DELETE /tasks/{id}` (204/404).

## Frontend structure

**Not visible from the files I read.** `app/main.py`'s CORS config implies
*some* browser client exists on `localhost:5500` or `:5173`, but nothing
about its structure, framework (or lack of one), or behavior can be
confirmed from these three files.

## Data flow

Request body → Pydantic validation (`TaskCreate`/`TaskUpdate`, 422 on
failure) → route handler → `app/storage.py` function → (on
create/get/list/patch) `_with_overdue` recomputes the overdue flag using
logic imported from a file not read in this pass → `TaskResponse` JSON.
The exact rule for what makes a task "overdue," and the exact rule for
which status transitions are legal, are both delegated to
`app.business_rules` — visible as import statements and call sites in
`app/main.py`, but the logic itself is not visible from the files read for
this pass.

## Testing and verification

**Not visible from the files I read.** No test file was part of this
pass's context. `app/storage.py`'s `_reset()` function's docstring
mentions "called by the autouse pytest fixture," which implies a pytest
suite with a reset fixture exists, but its location, coverage, and
contents cannot be confirmed from these three files alone.

## Known limits

No authentication or authorization code appears in any of the three files
read. No database or ORM import appears anywhere. Both are confirmable
directly from what's visible, not inferred.

---

## Self-assessment (for the comparison log)

The most honest of the three about its own boundaries — every "not
visible" statement above is true and specific, not a hedge. It's also the
most precise about the parts it *does* cover (e.g. citing
`model_dump(exclude_unset=True)` as the exact mechanism, not just "partial
updates work somehow"). The cost is real gaps: a reader gets zero
information about the frontend or tests from this document alone, even
though both obviously exist and matter.
