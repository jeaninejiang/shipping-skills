# Agent instructions

Reference material for building and shipping a mobile app on Supabase.
Each file below is self-contained guidance; read the one that matches
the task rather than all of them.

These are written around bugs that actually shipped, so each leads with
a symptom. If you are debugging something that matches a symptom in the
table, read that file before continuing.

## When to read what

| Read | When the task involves |
|---|---|
| `skills/app-flow-design/SKILL.md` | Planning onboarding or any multi-step flow; adding a screen that loads data; writing a conditional that picks between screens; a screen showing the wrong thing briefly, showing first-run prompts to returning users, or trapping someone with no way back |
| `skills/supabase-rls-data-model/SKILL.md` | Creating or changing a Supabase table; writing or debugging an RLS policy; adding an invite, pairing or join flow; a query returning nothing for one user and working for another |
| `skills/supabase-edge-functions/SKILL.md` | Anything under `supabase/functions/`; choosing between the anon and service-role client; secrets or Vault; wiring a Postgres trigger to a function; a function returning 200 without doing its job; a deployed function behaving like older code |
| `skills/supabase-auth-swift/SKILL.md` | Sign-up, sign-in or session handling in SwiftUI; OAuth redirect schemes; what the app does on launch before it knows who the user is; intermittent 401 or cancellation errors just after launch |
| `skills/ios-app-store-release/SKILL.md` | Xcode or XcodeGen project config; preparing a build for upload; anything in App Store Connect; store screenshots; TestFlight; diagnosing a rejection |

Each directory may also hold `references/` (read when the SKILL.md
points at them) and `scripts/` (run rather than read).

## Two rules worth applying everywhere

**Design the flow before the schema.** The gates in a flow spec are the
questions the backend must be able to answer. Building tables first
produces predicates shaped by whatever the schema made convenient,
which is the origin of the worst bug these notes describe.

**Prefer a precise sentence to a convenient condition.** `partnership
!= nil` and "they have actually joined someone" are not the same claim.
When a gate is named after the sentence it asserts, the wrong predicate
becomes visible on sight.
