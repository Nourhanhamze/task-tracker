# Verification — Mid-Course Feature Sprint

## Baseline check (before any feature work)

Before branching, the Modules 1-3 baseline was verified on `main`:

```
GET /health -> 200 {"status": "ok", "timestamp": "..."}
python -m tests.verify_a   -> 8/8 PASS
pytest tests/ -v            -> 21 passed
```

This matched the Module 2 deliverable checklist: strict Pydantic v2 models,
five CRUD endpoints, the six-case status-transition matrix
(`200, 200, 422, 200, 422, 200`), and a green pytest suite. Branch
`mid-course-project` was created from this commit.

## Backend test results (after both features)

```
$ python -m tests.verify_a
PASS: whitespace title rejected
PASS: empty title rejected
PASS: title > 200 chars rejected
PASS: defaults applied (status=ToDo, priority=Medium, description='')
PASS: extra field rejected on TaskCreate
PASS: id rejected on TaskCreate
PASS: created_at rejected on TaskUpdate
PASS: invalid status rejected
--- Part A verifications complete ---

$ pytest tests/ -v
33 passed, 1 warning in 0.35s
```

21 original tests (`tests/test_tasks.py`) + 12 new feature tests
(`tests/test_features.py`) = 33, all green. The 12 new tests cover exactly
the scenarios listed in the assignment brief for both features: valid due
date, invalid date format, overdue detection, update due date, filter
returns only overdue tasks; create with tags, reject empty tag, update tags,
filter by tag, preserve tags after unrelated update — plus two extra edge
cases (`Done` tasks are never overdue; more than 10 tags is rejected).

## Manual browser checks

Backend run at `http://localhost:8000`, frontend served statically at
`http://localhost:5500`, exercised in a real browser (Chromium via the
Claude Code browser tool), not just read as source:

| Check | Result |
|---|---|
| Board loads with empty-state columns, no console errors | Pass |
| Create task via modal (title, priority) | Pass — card appears in ToDo, correct priority pill |
| Whitespace-only title blocked client-side | Pass — no network request fires, inline error shown, modal stays open |
| Drag ToDo → InProgress (valid, native HTML5 DnD) | Pass — `PATCH` fires, card moves, persists after reload |
| Drag ToDo → Done (invalid, skips InProgress) | Pass — card reverts to ToDo, server's 422 message shown in the banner |
| Create task with past `due_date` | Pass — card shows red "Overdue" pill + red due-date text |
| Move that task to Done | Pass — overdue pill disappears |
| "Overdue only" toolbar checkbox | Pass — board narrows to just the overdue task |
| Create task with tags `docs, urgent` | Pass — two tag chips render on the card |
| Tag filter box, typed "docs" | Pass — only the matching task remains after the debounced re-fetch |

Two real bugs were caught during this manual pass and fixed in source (not
worked around):

1. **`due_date`/`tags` silently dropped on create.** `storage.add_task()`
   originally hand-listed the fields copied from `TaskCreate` into
   `TaskResponse`, written before those two fields existed. First manual
   check after adding the fields showed `due_date: null` on a task created
   *with* a due date. Fixed by building the response from
   `payload.model_dump()` instead of a hardcoded field list — see
   `docs/midcourse/prompt-log.md`, Prompt 2.
2. **Rejected-move error banner disappeared instantly.** The drag-and-drop
   handler called `showBanner(errorMessage)` and then `await fetchTasks()`,
   but `fetchTasks()` shows its own "Loading…" banner and hides it on
   success — clobbering the error message before a user could read it.
   Fixed by reordering: refresh first, then show the error.

## Behavior contract (before / after refactor)

A small refactor was made on the feature branch: `get_task` and `patch_task`
in `app/main.py` both fetched a task by ID and raised `404` if missing —
this duplicated logic was extracted into `_get_task_or_404()`. Contract
re-run before and after:

| # | Behavior | Before refactor | After refactor |
|---|---|---|---|
| 1 | `GET /health` returns 200 | Pass | Pass |
| 2 | `POST /tasks` valid → 201, invalid title → 422 | Pass | Pass |
| 3 | `GET /tasks` empty/no-match → 200 `[]` | Pass | Pass |
| 4 | `GET /tasks/{id}` found → 200, missing → 404 | Pass | Pass |
| 5 | `PATCH /tasks/{id}` missing id → 404 (checked before transition/validation errors) | Pass | Pass |
| 6 | Status-transition matrix `200,200,422,200,422,200` | Pass | Pass |
| 7 | `DELETE /tasks/{id}` existing → 204 empty body, missing → 404 | Pass | Pass |
| 8 | Full pytest suite | 33 passed | 33 passed |

No behavior changed; the diff between the two full pytest runs was only the
wall-clock timing line.

## Break Test evidence (two tests, both features)

### Break Test 1 — overdue detection (`app/business_rules.py`)

`compute_overdue()`'s final `return due_date < reference` was temporarily
replaced with `return False`.

```
$ pytest tests/test_features.py -k overdue -v
tests/test_features.py::test_task_with_past_due_date_is_overdue FAILED
tests/test_features.py::test_done_task_with_past_due_date_is_not_overdue PASSED
tests/test_features.py::test_filter_returns_only_overdue_tasks FAILED
...
2 failed, 1 passed, 9 deselected
```

Both overdue-detection tests failed for the expected reason
(`assert True is False` / an overdue task missing from the filtered list);
the one test that doesn't depend on detection actually firing
(`test_done_task_with_past_due_date_is_not_overdue`, which expects
`overdue: False` regardless) correctly kept passing. Source restored;
re-run confirmed `33 passed` again.

### Break Test 2 — empty-tag validation (`app/models.py`)

`_validate_tags()`'s `if not stripped: raise ValueError(...)` guard was
temporarily disabled (`if False: ...`).

```
$ pytest tests/test_features.py -k tag -v
tests/test_features.py::test_create_task_rejects_empty_tag FAILED
    assert 201 == 422
...
1 failed, 5 passed, 6 deselected
```

The test failed for the expected reason — the API accepted a `"   "` tag and
returned `201` instead of `422`. Source restored; re-run confirmed
`33 passed` again.

## Facilitator feedback fix (resubmission)

**Finding:** "Sending an explicit null value for title in a task update is
accepted with a 200 response and stores the invalid value. This allows a
task to end up with no title. This case is not covered by any tests."

**Confirmed and reproduced first**, before touching anything:

```python
r = client.post("/tasks", json={"title": "Original title"})
r2 = client.patch(f"/tasks/{r.json()['id']}", json={"title": None})
# r2.status_code == 200, r2.json()["title"] is None
```

**Root cause:** `TaskUpdate.title` is `Optional[str] = None` so the field
can be *omitted* from a PATCH (meaning "don't touch it"), but the old
`validate_title` validator treated any `None` it saw the same way —
including an explicitly-sent `null` — and passed it straight through
instead of rejecting it. `storage.update_task` then wrote that `None`
onto `TaskResponse.title`, which is typed `str`, via `model_copy(update=...)`,
which does not re-validate. The result: a `TaskResponse` object whose own
type annotation says `title: str` was actually holding `None`, silently.

**Scope check — this was not just `title`.** Before fixing anything, the
same explicit-null probe was run against every other `TaskUpdate` field
that maps to a non-nullable `TaskResponse` field:

```
title=null       -> 200, title becomes None      (the reported bug)
description=null -> 200, description becomes None (same bug)
status=null      -> 200, status becomes None       (same bug)
priority=null    -> 200, priority becomes None      (same bug)
tags=null        -> 200, tags becomes None            (same bug)
assignee=null    -> 200, assignee becomes None   <- correct: assignee IS nullable
due_date=null    -> 200, due_date becomes None   <- correct: due_date IS nullable
```

Five fields shared the exact same root cause; two were fine because
`assignee`/`due_date` are genuinely `Optional` on `TaskResponse` and
`null` legitimately means "clear this field" for those.

**Fix:** `app/models.py`'s `TaskUpdate` validators for `title`,
`description`, `status`, `priority`, and `tags` now raise
`ValueError` (→ 422) when the value is explicitly `None`, instead of
passing it through. Verified this doesn't break the "omit a field = leave
it unchanged" behavior every other PATCH test depends on, by checking
Pydantic v2's actual behavior first: a field validator only runs when the
client provides a value (including an explicit `null`) — it does **not**
run when the field is simply absent from the request body and the default
is used. So omitting `title` still skips the validator entirely and
leaves the stored title untouched; only an explicit `"title": null` now
gets caught.

**New tests:** `tests/test_null_updates.py`, 9 tests — explicit-null
rejected (422) for each of the 5 affected fields, a dedicated check that a
rejected null-title PATCH doesn't corrupt the stored title, confirmation
that `assignee`/`due_date` still correctly accept `null` as "clear this
field," and confirmation that omitting a field from a PATCH still leaves
it unchanged (the fix could easily have overcorrected and broken that).

**Break Test:** `git stash`-ed the fix, reran `tests/test_null_updates.py`
— 6 of 9 tests failed for the expected reason (`assert 200 == 422`), the 3
unrelated ones (assignee, due_date, omitted-field) correctly kept passing.
Restored the fix; all 9 pass again.

```
$ pytest tests/ -v
42 passed, 1 warning in 0.32s
```

(33 previous + 9 new.)

## Final state

```
$ python -m tests.verify_a   -> 8/8 PASS
$ pytest tests/ -v            -> 42 passed, 1 warning
```
