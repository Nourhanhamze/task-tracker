# AI Usage Rules

Concrete rules, not vibes — each one is testable ("could a teammate read
this and know whether a behavior violates it?") and grounded in something
that actually happened on this project.

## Never paste

- Never paste `.env` files, API keys, tokens, passwords, or any
  credential — regardless of environment (dev, staging, prod) — into an AI
  tool, chat, or commit message.
- Never paste real customer/user data, personal data, or production logs.
  This project has none (it's a course sample app with an in-memory
  store), but the rule holds regardless of project.
- Never paste another person's private data (emails, names, IDs) that
  isn't already public, even incidentally — e.g. don't paste a colleague's
  Slack message into a prompt to "explain this error" without checking
  what's in it first.

## Always verify

- Before accepting any AI-written validation, business-rule, or
  status-code claim, run the actual request against the actual code.
  "Looks right" is not evidence — this exact category of mistake is what
  caused the `storage.add_task` field-dropping bug (Mid-Course Sprint) and
  the `verify_a.py` always-exits-0 bug (End-of-Course CI work): both
  looked correct on read and were wrong on run.
- Before trusting an AI security/review finding, check whether it's
  actually reachable in this specific codebase, not just plausible in
  general. `docs/security-review.md` graded "SQL injection risk" as a
  False Positive for exactly this reason — the finding was generic, the
  codebase has no SQL.
- Before accepting a CI or Docker artifact as "done," produce the
  green→red→green (or build→run→exec) evidence, not just the file. A
  workflow that runs is not the same as a workflow that catches a real
  failure — see `docs/verification.md` for the specific commit that proved
  this project's CI actually turns red.
- When Docker (or any tool) isn't available to verify a claim, say so
  explicitly in the docs rather than writing evidence that implies a check
  ran. `docs/verification.md`'s Docker section exists specifically to
  record this boundary instead of hiding it.

## Record AI contributions

- For any AI-generated code kept in the repo, the commit message states
  what was generated, what was changed after review, and what was run to
  verify it — every commit on this repo's `mid-course-project` and
  `final-project` branches follows this, not just the ones that happened
  to go smoothly.
- When an AI-suggested design is rejected (e.g. the `StorageBackend`
  protocol suggestion in `docs/decisions/in-memory-task-storage.md`, or
  the "compute overdue once at write time" approach in
  `docs/midcourse/mini-adr.md`), the rejection and its reasoning are
  written down in the relevant decision note — not just silently
  discarded.
- Every AI review/audit pass (code review, security review) produces a
  graded log (Useful/Noise/Wrong or Valid/False Positive/Noise) rather
  than a raw list of "things the AI said." An ungraded AI output is not a
  deliverable in this project.
