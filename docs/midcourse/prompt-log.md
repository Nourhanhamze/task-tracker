# Prompt Log — Mid-Course Feature Sprint

Format per entry: prompt, what the AI (Claude, in-editor) returned, and what
was accepted / edited / rejected after inspection and running the code.

## Feature 1: Due dates + overdue filter

### Prompt 1 (weak → rewritten)

**Weak version:** "Add due dates to the task tracker."

**Why it's weak:** no target files, no validation rule, no statement of
whether "overdue" is computed on the backend or the frontend, no constraint
on what *not* to touch (existing transition rules, existing tests).

**Rewritten, structured prompt actually used:**
> You are extending `app/models.py`, `app/business_rules.py`, `app/main.py`,
> and `app/storage.py` in an existing FastAPI Task Tracker. Add an optional
> `due_date: date` field to `TaskCreate`, `TaskUpdate`, and `TaskResponse`.
> Add a derived `overdue: bool` field to `TaskResponse` — a task is overdue
> if `due_date` is in the past and `status != Done`. Do not persist `overdue`
> as a fixed value; it must be recomputed from `due_date`/`status` on every
> read, since it depends on the current date, not just the last write. Add
> `overdue: Optional[bool]` as a query filter on `GET /tasks`. Do not change
> the existing status-transition rules or the five existing routes' status
> codes. Keep the change additive — do not remove or rename existing fields.

**What AI returned:** a `compute_overdue()` function in `business_rules.py`,
new fields on all three models, and a `due_date` query filter — but the
draft only called `compute_overdue()` inside `storage.add_task()` /
`storage.update_task()`, storing the boolean once at write time.

**Accepted / edited / rejected:** rejected the "compute once, store" part
(see `mini-adr.md` — this is the corrected assumption from the user
stories). Edited it to a `_with_overdue()` helper in `app/main.py` that
recomputes the flag immediately before every response is returned
(`create_task`, `list_tasks`, `get_task`, `patch_task`), so the date check
always uses "now," not "whenever this task last changed."

### Prompt 2

> Attach `app/storage.py`. I just added `due_date` and `tags` fields to
> `TaskCreate`/`TaskResponse` in `app/models.py`. Update `add_task()` to make
> sure every field on `TaskCreate` reaches `TaskResponse` — do not hand-list
> individual fields, since that silently drops new fields the next time a
> field is added.

**What AI returned:** `TaskResponse(id=new_task_id(), created_at=now,
updated_at=now, **payload.model_dump())` instead of a hand-written field list.

**Accepted / edited / rejected:** accepted as-is. This directly fixed a real
bug caught during manual verification: the *original* `storage.add_task()`
(written before this prompt, during baseline scaffolding) hard-listed
`title`, `description`, `status`, `priority`, `assignee` — so when
`due_date`/`tags` were added to the model, a task created with a due date
came back with `due_date: null` every time. Caught by running a manual
`TestClient` script (see `docs/midcourse/verification.md`), not by pytest,
because the original 21 baseline tests never sent a `due_date` at all — a
gap the new feature tests now close.

### Prompt 3

> Write pytest tests in a new file `tests/test_features.py` using the
> existing `client` and `created_task` fixtures from `tests/conftest.py`.
> Cover: valid due date accepted, invalid date format returns 422, a task
> with a past due date is overdue, a Done task with a past due date is not
> overdue, updating due date works, and `GET /tasks?overdue=true` returns
> only overdue tasks. Use `date.today() ± timedelta` for dates, not
> hardcoded date strings, so the tests don't go stale.

**What AI returned:** the six due-date tests now in `test_features.py`,
using `FUTURE_DATE`/`PAST_DATE` module-level constants built from
`date.today()`.

**Accepted / edited / rejected:** accepted without edits — this was
double-checked against the actual `compute_overdue()` behavior by running
the suite (`33 passed`), and against a deliberate Break Test (see
`verification.md`) that confirms two of these tests fail when the
overdue-detection line is disabled.

## Feature 2: Tags / labels

### Prompt 4

> Add a `tags: list[str]` field to `TaskCreate`, `TaskUpdate`, and
> `TaskResponse` in `app/models.py`. Validate: each tag is trimmed of
> whitespace; a tag that's empty after trimming is rejected (422 for the
> whole request); at most 10 tags per task; each tag at most 30 characters.
> Add a case-insensitive `tag` query filter to `GET /tasks` in
> `app/main.py`. Do not add a separate tags table or endpoint — tags live on
> the task only.

**What AI returned:** a `_validate_tags()` helper and `field_validator`s on
both `TaskCreate` and `TaskUpdate`, plus a `tag` query param in
`list_tasks()` doing `needle in [x.lower() for x in t.tags]`.

**Accepted / edited / rejected:** accepted the validation logic as written.
Edited the filter slightly to strip the incoming `tag` query value too
(`tag.strip().lower()`), since a filter box that only trims tag values on
save but not on search would treat `" frontend"` (typed with a leading
space) as a non-match even though no stored tag would ever have that space.

### Prompt 5

> Update `frontend/app.js` and `frontend/index.html`: add a "Tags
> (comma-separated)" text input to the create/edit modal, render each tag as
> a small chip on the card, add a "Filter by tag" text box to the toolbar
> that re-fetches the board (debounced, ~250ms) as the user types. Reuse the
> existing `fetchTasks()`/`cardHtml()` functions — do not introduce a second
> fetch path.

**What AI returned:** `parseTags()` (split on comma, trim, drop empties),
a `tag-chip` element in `cardHtml()`, a `debounce()` helper, and a
`URLSearchParams`-based query string built inside `fetchTasks()`.

**Accepted / edited / rejected:** accepted the structure. Caught one issue
in manual browser testing (see `verification.md`): the drop handler's error
banner (used for rejected drag-and-drop moves) was being immediately
overwritten by the follow-up `fetchTasks()` call's own loading/hide-banner
cycle, so a real 422 rejection flashed and vanished before a user could read
it. This was a pre-existing baseline bug, unrelated to tags, surfaced while
testing the new toolbar changes in the same browser session — fixed by
reordering `await fetchTasks()` before `showBanner(...)` in the drop handler
so the error banner is shown *after* the board finishes refreshing, not
before.

### Prompt 6

> Add tests to `tests/test_features.py`: create with tags, reject an empty
> tag in the list, reject more than 10 tags, update tags, filter by tag, and
> confirm tags survive an unrelated update (e.g. changing only
> `description`).

**What AI returned:** six tag tests, including
`test_tags_preserved_after_unrelated_update`.

**Accepted / edited / rejected:** accepted as-is. The "preserved after
unrelated update" case passed on the first run with no code changes needed,
because `storage.update_task()` already used
`payload.model_dump(exclude_unset=True)` from the Module 2 baseline — a case
where the existing design already did the right thing and the test just
confirms it, rather than driving a new fix.
