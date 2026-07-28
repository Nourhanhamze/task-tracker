# AI-Assisted Code Review Log

**Diff reviewed:** commit `47e9cfe` — "Redesign frontend: cohesive design
system + dark mode" (`frontend/index.html` +332/-83, `frontend/app.js` +6).
Chosen because it's a real, substantial diff (not a toy example) that
touches CSS, markup, and a small amount of JS behavior together.

Reviewer prompt used: *"Review this diff for correctness, tests, security,
and documentation drift. Cite the exact file and line for every finding."*

## Findings

| # | Finding | File / evidence | Category | Justification |
|---|---|---|---|---|
| 1 | No fallback for `color-mix()` / `backdrop-filter` — both used 7 times (header background, `#status-banner` border colors) with no plain-color fallback declared first. In a browser without support, the whole declaration is dropped, so the header could render with no background at all (invisible sticky header over scrolling content). | `frontend/index.html`, `header { background: color-mix(...) }` and `.error`/`.loading` border-color rules | **Useful** | Concrete, file-specific, and a real (if minor) risk. Not fixed in this pass — AGENTS.md targets evergreen browsers for this course project, so the risk was accepted and documented here rather than adding fallback rules, but it's worth knowing about before this ever needs to run somewhere with an older WebView. |
| 2 | The `.card` entrance animation (`animation: cardIn 0.18s ease both`) and the `.card:hover { transform: translateY(-2px) }` rule both set `transform` on the same element. My earlier manual browser QA for this commit checked computed style values (border-radius, box-shadow, background, dragging class, drag-and-drop, filters) but never actually triggered `:hover` or resized below the 860px breakpoint to confirm the mobile single-column stack. | `frontend/index.html`, `.card` / `.card:hover` / `@media (max-width: 860px)` | **Useful** | Not a confirmed bug — CSS cascade rules mean the `:hover` transform should simply override the animation's final value once the animation ends — but it's a real gap in what I verified versus what I claimed was "verified in-browser" in the commit message. The commit message overstates the QA coverage slightly. |
| 3 | Decorative icons added via CSS `content` (`.assignee::before { content: "👤" }`, `.pill.overdue::before { content: "⚠" }`) are not marked `aria-hidden="true"`, so a screen reader may announce them ("bust in silhouette", "warning sign") redundantly alongside the adjacent text they decorate. | `frontend/index.html`, `.assignee::before`, `.pill.overdue::before` | **Useful** | Small, concrete accessibility polish item with an exact fix (`aria-hidden="true"` on the pseudo-element isn't directly possible via CSS alone; would need to move the icon to a real `<span aria-hidden="true">` in the markup, or accept the redundancy as low-severity). Logged as a follow-up, not blocking. |
| 4 | `-webkit-font-smoothing: antialiased` is a non-standard, WebKit/Blink-only property. | `frontend/index.html`, `body` rule | **Noise** | Technically true, but it's inert (silently ignored) on engines that don't support it and carries zero risk. Not worth a follow-up. |
| 5 | "Renaming `--card-bg` to `--surface` risks breaking any other file or script that still references the old variable name." | Initial suspicion before checking | **Wrong** | Checked with `grep -rn "card-bg" frontend/` — zero matches anywhere in the repo. The rename is clean; there was nothing left to break. This is the kind of finding that sounds like careful due diligence but is wrong once you actually check, rather than assume, usage. |
| 6 | "The `:focus-visible { outline: none; ... }` rule removes focus indicators, which is an accessibility regression." | First read of `frontend/index.html`, `:focus-visible` rule | **Wrong** | On a closer read, the same rule immediately replaces `outline` with `box-shadow: var(--focus-ring)` and is scoped to `:focus-visible` specifically (not a blanket `:focus` or global reset), which is the standard modern pattern for a custom-styled focus ring rather than a removed one. My first pass mentally flagged only the `outline: none` token and didn't register the replacement on the next line — exactly the kind of misread the course warns about (reading a snippet instead of the whole rule). |

## My own human review of the same diff

Reading the diff myself (separately from generating the table above) turned
up the same six points, plus one thing the "AI reviewer" pass undersold:
the commit message's claim "light and dark tokens both resolve correctly"
is true (I verified `--accent`/`--bg` computed values in both color
schemes via the browser's `getComputedStyle`, in the mid-course session),
but that check was narrow — it read two CSS variables, not a full visual
pass over every component in dark mode. Finding #2 above captures the
general shape of this gap; this is the specific instance of it.

## Reconciliation

- **Caught by both:** #1, #4 (the color-mix/backdrop-filter risk and the
  vendor-prefix noise were obvious from a straight read of the CSS either
  way).
- **AI-review-only:** #3 (I would not have thought to check for
  `aria-hidden` on decorative pseudo-element icons without being prompted
  to look at the diff systematically for accessibility, not just
  correctness).
- **Human-only:** the "QA claim was narrower than the commit message
  implies" framing in the section above — an AI reading only the diff has
  no way to know what was or wasn't actually clicked through in a browser
  during the original session; that context lived outside the diff.

## One personal AI-review rule

I will use an AI review pass for broad first-coverage on diffs over ~100
lines, but I will not act on any finding — Useful or otherwise — until I
have located the exact line myself and, for anything framed as a "risk"
rather than an observed failure, checked whether it's actually reachable
(e.g. `grep` for real usage before trusting a "this might break X" claim).
