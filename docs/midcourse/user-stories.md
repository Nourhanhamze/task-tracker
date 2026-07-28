# User Stories — Mid-Course Feature Sprint

Two features were selected from the core options list: **Due dates + overdue
filter** and **Tags / labels**. Both are visible and usable in the Kanban
frontend (modal fields, card display, toolbar filters), not just the API.

## Feature 1: Due dates + overdue filter

**Story 1 — Set a due date when creating a task**
As a team member, I want to set an optional due date when I create a task, so
that I know when it needs to be finished.
Acceptance criteria:
- `due_date` is optional; a task can be created with no due date.
- A valid ISO date (`YYYY-MM-DD`) is accepted and stored.
- An invalid date string returns `422` and the task is not created.

**Story 2 — See overdue tasks called out on the board**
As a team member, I want overdue tasks to be visually flagged, so that I don't
miss deadlines that have already passed.
Acceptance criteria:
- A task with a due date in the past and status not `Done` shows a red
  "Overdue" pill and a red due-date label on its card.
- A task due in the future shows a plain due-date label, no pill.
- A task with no due date shows no due-date row at all.

**Story 3 — A finished task is never "overdue"**
As a team member, I want a completed task to stop being flagged overdue, so
that the board doesn't nag me about work that's already done.
Acceptance criteria:
- Moving a task to `Done` clears the overdue pill even if its due date is in
  the past.
- **AI assumption corrected:** the first draft computed `overdue` once, at
  create/update time, and stored it as a fixed field. That's wrong — a task
  created today with a due date next week silently becomes overdue a week
  later without anyone touching it, and the stored flag would never update.
  Corrected the design so `overdue` is recomputed from `due_date` + `status`
  on every read (`GET`, not just on write), using the server's current date.

**Story 4 — Update a task's due date**
As a team member, I want to change a task's due date after creating it, so
that I can reschedule work without recreating the task.
Acceptance criteria:
- `PATCH /tasks/{id}` with a new `due_date` updates it and leaves all other
  fields untouched.
- The response's `overdue` flag reflects the new due date immediately.

**Story 5 — Filter the board to overdue work only**
As a team member, I want to filter the task list to only overdue tasks, so
that I can triage what's late first.
Acceptance criteria:
- `GET /tasks?overdue=true` returns only tasks currently overdue.
- The frontend has an "Overdue only" checkbox that applies the same filter
  without a page reload.
- With no overdue tasks, the filtered result is `200` with an empty list, not
  an error.

## Feature 2: Tags / labels

**Story 6 — Tag a task when creating it**
As a team member, I want to attach one or more tags to a task, so that I can
categorize work beyond status and priority.
Acceptance criteria:
- `tags` is an optional list of strings, defaulting to empty.
- Each tag is trimmed of surrounding whitespace before being stored.
- A tag that is empty or whitespace-only after trimming is rejected with
  `422` for the whole request (nothing is partially saved).
- **AI assumption corrected:** the first draft accepted any list length and
  any string length for tags. Added an explicit cap (10 tags per task, 30
  characters per tag) so a single request can't silently store unbounded
  data — the assignment brief calls this out as an expected validation rule,
  and an "assume nothing" list wasn't a safe default.

**Story 7 — See tags on the board**
As a team member, I want tags to show as chips on each card, so that I can
scan the board for a category at a glance.
Acceptance criteria:
- Each tag renders as a small chip on the card.
- A task with no tags renders no chip row.

**Story 8 — Edit a task's tags**
As a team member, I want to add or remove tags from an existing task, so that
categorization can change as work evolves.
Acceptance criteria:
- `PATCH /tasks/{id}` with a new `tags` list replaces the tag list.
- Editing any other field (title, description, status, assignee, due date)
  and *not* including `tags` in the request leaves existing tags untouched.

**Story 9 — Filter the board by tag**
As a team member, I want to filter tasks by tag, so that I can see everything
related to one category (e.g. "frontend") across all three columns.
Acceptance criteria:
- `GET /tasks?tag=frontend` returns only tasks that have that tag.
- The match is case-insensitive (`Frontend` and `frontend` are treated the
  same), since users won't type tags consistently.
- The frontend has a text filter box that applies this filter as the user
  types (debounced), without needing a submit button.
