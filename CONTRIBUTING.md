# Contributing

The bar for adding something here is simple: **it cost someone more than
an hour, and the next person shouldn't pay it again.**

General advice doesn't qualify. "Handle errors properly" is already in
every style guide and helps nobody. "Supabase refresh tokens are
single-use, so two concurrent calls at launch invalidate the session"
is worth the file it's written in.

## Lead with the symptom

Rules get found by people who don't yet know what their problem is
called. So write what it *looked like* before you write what it was:

> Symptom: an invite link does nothing. No error. The row is still
> unclaimed in the database.
>
> Cause: the lookup ran on a user-scoped client, and RLS hid the row
> from the person trying to join it.

Someone searching "supabase invite link does nothing" finds that. They
would not have found "use the service-role client for claims".

## Explain why, don't just forbid

If you catch yourself writing ALWAYS or NEVER in capitals, the rule
probably isn't explained well enough yet. Models and people both follow
a rule more reliably when they understand what it's protecting, and
both need the reasoning to handle the case you didn't anticipate.

Compare:

- ✗ "NEVER use the anon client for invite lookups."
- ✓ "The joiner doesn't own the row yet — that's what joining means — so
  an RLS-filtered read returns nothing, with a 200. The branch then
  falls through and the caller gets a success describing something that
  didn't happen."

The second survives contact with a situation the first didn't cover.

## Keep one source of truth

`skills/*/SKILL.md` is canonical. `AGENTS.md` and `.cursor/rules/*.mdc`
**point at** those files; they never restate the content. If you add a
skill, add a row to the `AGENTS.md` table and generate its `.mdc` — but
resist copying guidance into either. Four copies of a sentence means
three of them are stale within a month.

## Scope

- SKILL.md under ~500 lines. Past that, move detail into `references/`
  and point at it from the body.
- Frontmatter `name` must match the directory name.
- The `description` is what decides whether an agent loads the skill at
  all, so say both what it does *and* when to reach for it — including
  the symptoms.
- Nothing licensed that can't be redistributed. No fonts, no vendored
  SDKs, no screenshots containing real user data.

## Corrections are the most valuable contribution

Platform specifics rot. App Store Connect changes its fields, Supabase
changes its APIs, CLI subcommands appear and vanish. If something here
is wrong or out of date, **fix it in place** and say so in the PR — a
reference people have learned to second-guess is worse than none at
all.

Opening an issue that just says "this is stale now" is genuinely useful
too, if you don't have time for more.
