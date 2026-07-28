# My AI Playbook

## When I reach for AI first

Scaffolding repetitive structure (five CRUD routes, a pytest suite,
docstrings across four files) and drafting anything I'll review before it
matters (a first-pass security audit, an architecture doc, a feature
plan). AI made me faster here specifically because the output is cheap to
verify — run it, read the diff, check the status code.

## When I do not reach for AI first

Deciding what a rule *should* be, not just what it *is*. The status-
transition matrix, the overdue-must-be-recomputed-not-stored design, and
the decision to reject a `StorageBackend` abstraction with no second
implementation were all things I had to reason through myself — AI drafted
options, but "which trade-off actually fits this project" isn't something
I outsource.

## My non-negotiables

- Never paste credentials, tokens, `.env` values, or real personal data
  into an AI tool — see `docs/ai-usage.md`.
- Never accept a CI/Docker/test artifact as "done" without evidence it
  actually catches the failure it claims to catch (green→red→green, not
  just green).
- Never let an AI-generated docstring or README claim stand without
  checking it against the actual running code — see `docs/verification.md`
  for the two documentation bugs this caught.

## My review rules

Before accepting a diff: read every changed file, run the relevant test or
manual check, and — for anything framed as a risk rather than an observed
failure — verify it's actually reachable (e.g. `grep` for real usage)
before trusting it. This is the rule `docs/review-log.md` names explicitly
after catching a "renaming this variable might break something" false
positive that a two-second `grep` disproved.

## What I am still figuring out

Whether my Docker verification is actually good enough. I inspected the
Dockerfile line-by-line against the Module 4 checklist and documented that
honestly instead of faking `docker exec` output, but static review is a
real gap next to an actual `docker build && docker run`. I don't yet have
a good personal rule for "how much static inspection is enough before I
should stop and get the real tool installed instead."

---

## Decision Card

| Decision | My answer |
|---|---|
| **New feature** | Plan-first, repo-grounded: read the actual models/storage/routes/tests before proposing a shape, the way `docs/decisions/comments-feature-plan.md` did — a generic plan for this project's comments feature would have suggested a database and auth this repo doesn't have. |
| **Code review** | AI review for first-pass breadth on diffs over ~100 lines, but every finding gets graded (Useful/Noise/Wrong) and nothing gets acted on until I've found the exact line myself. |
| **Debugging** | Paste the exact failing test name, the exact assertion, and the exact status code — not "it doesn't work." Vague prompts produce generic advice; specific evidence produces specific fixes. |
| **Infrastructure** | Trust AI to draft CI/Docker configs, but require the break-test proof (a deliberately broken test, pushed, confirmed red, then reverted) before trusting the config itself — a workflow that merely runs isn't a workflow that works. |
| **Never paste** | Credentials, tokens, `.env` contents, real customer/personal data, private production logs. Not "sensitive stuff" — those exact categories. |
| **One rule** | If I can't point to the line, the test run, or the command output that proves a claim, I don't get to write it down as done. |
