# Reflection

I used Claude (in an editor-integrated, agentic coding session) for the whole
sprint: scaffolding the FastAPI backend and vanilla-JS frontend, implementing
both features, writing the pytest suite, running the Break Tests, and
drafting these docs. I didn't use a second tool for comparison this round —
the course's Module 1 tool-comparison habit (ChatGPT vs. Claude) was applied
earlier in the course; this sprint reused the same assistant throughout to
keep file-context continuity (Module 2's point about editor-based tools
being able to read real project files rather than re-explaining the stack
every prompt).

**Where it helped most:** generating the repetitive-but-easy-to-get-wrong
scaffolding — the five CRUD routes, the Pydantic validators, the 33 pytest
tests — in a form I could actually read and check line by line, rather than
writing it from scratch. The two Break Tests were the clearest payoff: I
didn't have to guess whether `test_create_task_rejects_empty_tag` was
actually testing anything — disabling the validation it protects and
watching that exact test (and only that test) fail was direct proof.

**Where it slowed things down:** the very first version of `storage.add_task()`
hand-listed every field to copy from the input model into the response
model. That was fine for the Module 2 baseline, but the moment I added
`due_date` and `tags` to the models, that hardcoded list became a silent
bug — new tasks came back with `due_date: null` no matter what was sent.
Nothing in the 21 baseline tests caught it, because none of them ever sent a
`due_date`. It only showed up when I ran a manual verification script by
hand. That cost more time than the feature itself did, and the lesson was
specific: adding a field to a Pydantic model doesn't mean it's actually
wired through every hand-written function that touches that model — grep
for every place a model gets rebuilt field-by-field, not just the model
definition itself.

**Where my review changed the result:** the "compute overdue once, at
write time" version. It passed every test I'd written *for that draft*,
because those tests all created a task and immediately checked it in the
same request — they never simulated time passing. Reading the code before
running anything is what caught it: a boolean that's only ever set on
write can't correctly represent something that depends on today's date.
Recomputing `overdue` on every read instead of trusting a stored flag was
the one architectural decision in this sprint that came from stepping back
and asking "what happens if nobody touches this task for a week," not from
a test failing.
