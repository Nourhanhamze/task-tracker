# Governance Worksheet

A concrete look at what actually crossed the AI boundary across this
project — Mid-Course Sprint through End-of-Course hardening — not a
hypothetical policy.

## What I shared with AI

| Shared | Risk | Reason |
|---|---|---|
| Full Task Tracker source (`app/`, `frontend/`, `tests/`) | Low | Course sample code, no real users, no real data, already public on GitHub by design. |
| pytest output / failure tracebacks (e.g. `assert 200 == 422` on the deliberately broken transition test) | Low | Local test output about toy data (`"title": "x"`), nothing identifying. |
| `docs/*.md` drafts, README content, project structure | Low | Documentation about the project itself, public by design. |
| Dockerfile, `.github/workflows/ci.yml`, `.dockerignore` contents | Low | Contains no credentials or endpoints — just build/test configuration for a public repo. |
| GitHub Actions run URLs and `curl`/API output while checking CI status | Low | Public repo, public Actions logs; nothing private in the URLs or run metadata. |
| Course assignment text (Moodle brief, lecture PDF content) | Low | Institutional coursework material shared by the user directly, not personal data. |
| My own git config (`user.name`/`user.email`) surfaced in `git log` output while checking commit authorship | **Medium** | Real name and a real institutional email address (`nsh23@mail.aub.edu`) appeared in tool output during this session. Not a secret, but it is personally identifying and wasn't something I'd necessarily want in a fully public transcript by default — flagged here rather than waved through as "just code." |

Nothing at the **High** risk level (credentials, tokens, `.env` values,
real customer/personal data, private production logs) was ever part of
this project — confirmed by the secret scan in `docs/security-review.md`,
which found none in the repository, and by not having any such data to
begin with (this is a course project with no real backend, database, or
users).

## What I received from AI

| Received | Still understand it? | Needs review? |
|---|---|---|
| Backend models, validators, routes, storage functions (`app/*.py`) | Yes — traced line-by-line below, and separately explained in the docstrings added during the End-of-Course pass | No open questions |
| Frontend fetch/render/drag-and-drop logic and the CSS design system (`frontend/*`) | Mostly — the CSS custom-property color-mix/backdrop-filter fallback gap noted in `docs/review-log.md` finding #1 is a place I accepted the output without fully working through browser-compatibility implications at the time | Yes — logged as a follow-up, not blocking |
| `.github/workflows/ci.yml` | Yes — verified by actually breaking a test and watching it fail, not just reading the YAML | No open questions |
| `Dockerfile` / `.dockerignore` | Yes, structurally — but **not** verified against a running container (Docker isn't installed here) | Yes — flagged explicitly in `docs/verification.md` as an unverified claim |
| Security audit findings (`docs/security-review.md`) | Yes — every finding was independently checked (grep for secrets, an actual 2MB POST request, `uuid4().hex` read directly) before being graded | No open questions |
| Refactoring suggestion: `_get_task_or_404` helper extracted from duplicated 404-check logic in `get_task`/`patch_task` | Yes | No open questions |

## Trace one generated block line by line

Picked `app/business_rules.py::compute_overdue` (added during the
Mid-Course Sprint, still load-bearing at the end of the course):

```python
def compute_overdue(due_date: Optional[date], status: TaskStatus, today: Optional[date] = None) -> bool:
    if due_date is None or status == TaskStatus.DONE:
        return False
    reference = today or date.today()
    return due_date < reference
```

- `due_date: Optional[date], status: TaskStatus, today: Optional[date] = None` —
  takes the two real inputs (`due_date`, `status`) plus an optional
  `today` override. The `today` parameter exists purely for testability:
  without it, a test would need to mock `date.today()` globally to test
  "is a task overdue," which is exactly what `tests/test_features.py`'s
  `FUTURE_DATE`/`PAST_DATE` constants avoid needing to do, since they
  compute relative to the real `date.today()` at import time instead.
- `if due_date is None or status == TaskStatus.DONE: return False` — two
  short-circuit exits. No due date means "not applicable," not "overdue by
  default" (removing this line would make every task with no due date
  register as overdue, since `None < reference` would raise a `TypeError`
  in Python anyway — dates aren't comparable to `None`). A Done task is
  never overdue regardless of its date, which is a deliberate product
  decision (see `docs/midcourse/user-stories.md`, Story 3), not something
  Python gives you for free.
- `reference = today or date.today()` — this is the line I'd flag if
  reviewing it fresh: `today or date.today()` treats a falsy `today` the
  same as a missing one. `date` objects are never falsy in Python (there's
  no "zero date"), so this is safe in practice, but it reads like it could
  be hiding a bug if you don't know that. `if today is not None else
  date.today()` would say the same thing more explicitly. I understand why
  it works; I would still write it the more explicit way if I revisited
  this file.
- `return due_date < reference` — the actual comparison; `date` supports
  `<` directly via its own `__lt__`, no conversion needed. Removing this
  line (or flipping the operator) is exactly what the Break Test in
  `docs/midcourse/verification.md` exercises: replacing this with `return
  False` was shown to make two specific tests fail for the right reason.

## What pattern changes

**Keep doing:** running the actual code before trusting a claim about it —
the `_with_overdue`/`storage.add_task` bugs (mid-course), the CI
`verify_a.py` silent-pass bug, and the missing `404` in `/openapi.json`
(end-of-course) were all caught this way, not by reading code and deciding
it looked right.

**Stop doing:** accepting a commit message's own claim about what was
verified as if it were independent evidence. `docs/review-log.md` finding
#2 is the concrete instance: a past commit message said "verified in
browser," and that was true but narrower than it sounded.

See `docs/ai-usage.md` for these as concrete rules rather than these two
paragraphs of narrative.
