# Mini-ADR — Due Dates + Overdue Filter, and Tags/Labels

## Decision

Both features are implemented entirely within the existing Modules 1-3
architecture: Pydantic v2 fields on the existing `TaskCreate` / `TaskUpdate` /
`TaskResponse` models, in-memory storage unchanged in shape, two new optional
query parameters on `GET /tasks` (`overdue`, `tag`), and additive-only
frontend changes (new modal fields, new card elements, new toolbar controls).
No new storage layer, no new routes, no new files beyond one new business
rule function and one new test file.

`due_date` is stored as a plain field but `overdue` is **never trusted from
storage** — it is recomputed on every response from `due_date`, `status`, and
the server's current date via `business_rules.compute_overdue()`. This keeps
the "single source of truth" rule from Module 2 (the backend owns business
rules, not the client) and avoids a stale-flag bug where a task quietly
becomes overdue without any write happening to refresh it.

`tags` is a `list[str]` on the model, not a comma-separated string column,
even though the internal store is just a Python dict. A list keeps the
validation (per-tag trim, per-tag max length, max tag count) and the
case-insensitive filter simple, and matches what the JSON API already looks
like to the frontend — no server-side parsing/joining logic needed at the
boundary.

## Alternatives AI suggested and what was rejected

- **Store `overdue` as a persisted boolean, updated at write time.** Rejected
  — see the "AI assumption corrected" note in `user-stories.md`. A flag that
  only updates when someone happens to write to the task is wrong for a
  time-based property; correctness requires recomputing it against "now" on
  read.
- **A dedicated `Tag` resource with its own CRUD endpoints** (`POST /tags`,
  `GET /tags`, tag-task association table). This is roughly what the
  assignment brief's "Bulk operations" / "Saved views" callout warns
  against — it's the kind of feature that can balloon far past a 3-4 hour
  scope. Rejected as out of scope; a `tags: list[str]` field on the task
  itself covers every acceptance criterion the brief actually asks for.
- **Client-side-only overdue calculation** (compute `overdue` in
  `app.js` from `due_date` and today's date in the browser, no backend
  field). Rejected on the same "backend owns business rules" principle
  Module 2 establishes for status transitions — a user hitting the API
  directly (curl, another client) should see the same overdue flag the UI
  does, so the rule has to live server-side.
- **A single combined "search" endpoint that also handles tag and overdue
  filtering** (folding this sprint's filters into the "Search + combined
  filters" option from the brief). Rejected as scope creep for this sprint:
  the brief explicitly lists Search + combined filters as a *separate*
  feature option, and combining it here would have doubled the surface area
  to review and test in the time available.

## One risk to revisit if the project grew

Tag filtering and overdue filtering are both linear scans over
`storage.get_all_tasks()`, filtered in Python inside `app/main.py`. That is
fine for an in-memory, single-process demo, but it would need to move to
proper query filtering (e.g. a real database with indexed columns) before
this could handle a realistic number of tasks or concurrent users.
