# Shipping Skills

Agent skills and templates to accelerate agent-assisted shipping — app
flow design, Supabase backends, and getting to the App Store. Extracted
from doing it, not from documentation.

Every rule in here is written around a bug that actually shipped. Each
one leads with the **symptom**, because the symptom is how you find the
rule again at 1am when something is broken and you don't yet know what
to call it.

Works with Claude Code, Codex, Cursor, and anything that reads
`AGENTS.md`. The content is plain Markdown; only the packaging differs.

---

## What's in here

| Skill | Covers | The bug that earned it |
|---|---|---|
| **[app-flow-design](skills/app-flow-design/)** | Gates, per-screen state matrices, dead ends, input validation, waiting states | A gate testing "a row exists" when it meant "two people are on it" — which permanently trapped accounts one step past the screen they needed |
| **[supabase-rls-data-model](skills/supabase-rls-data-model/)** | Tables, RLS policies, migrations for data shared between users | Invite links that silently did nothing, because RLS hides a row from the very person trying to join it |
| **[supabase-edge-functions](skills/supabase-edge-functions/)** | Anon vs service-role, explicit exits, background work, Vault, user-facing errors | A function returning `200` for a join that never happened |
| **[supabase-auth-swift](skills/supabase-auth-swift/)** | Sign-in, OAuth redirects, session restore, first-run decisions | Three parallel calls on launch invalidating the session, because refresh tokens are single-use |
| **[ios-app-store-release](skills/ios-app-store-release/)** | XcodeGen, versioning, privacy manifest, App Privacy, store imagery, submission | Archiving build 4 six times and getting build 3 every time |

## How much of this applies to you

Only two of the five are iOS-specific. Most of it is backend and design
work that happens to have been learned while building an iOS app.

| Skill | Platform | Backend |
|---|---|---|
| `app-flow-design` | any | any |
| `supabase-rls-data-model` | any | Supabase |
| `supabase-edge-functions` | any | Supabase |
| `supabase-auth-swift` | iOS / Swift | Supabase |
| `ios-app-store-release` | iOS | — |

So:

- **Building anything at all?** `app-flow-design` stands alone. It is
  about gates, screen states and dead ends, and nothing in it assumes a
  platform or a framework.
- **On Supabase, any client?** The RLS and Edge Functions skills apply
  unchanged. The invite-link bug they describe was found in an iOS app
  and then found *again*, identically, in the same project's Next.js
  website — it is a property of RLS, not of the client.
- **On Supabase from Flutter, React Native or Kotlin?**
  `supabase-auth-swift` has Swift samples, but its substance — single-use
  refresh tokens, what sign-up should and shouldn't create, deriving
  onboarding state from the server — translates directly.
- **Shipping to the App Store?** Then the fifth one too.

## Install

Clone it, then copy the skills you need. Copy only what applies — a
skill for a stack you aren't using is noise in every conversation.

```bash
git clone <this-repo> shipping-skills
cd shipping-skills
./install.sh /path/to/your-project            # interactive, asks which tool
./install.sh /path/to/your-project --claude   # or name it directly
```

Or do it by hand:

| Tool | Where it looks | What to do |
|---|---|---|
| **Claude Code** | `.claude/skills/<name>/SKILL.md` | `cp -r skills/* your-project/.claude/skills/` |
| **Codex** and other [AGENTS.md](https://agents.md) readers | `AGENTS.md` | Copy `skills/` into your project and append this repo's `AGENTS.md` to yours |
| **Cursor** | `.cursor/rules/*.mdc` | `cp -r skills/ .cursor/rules/` then copy `.cursor/rules/*.mdc` |
| **Copilot** | `.github/copilot-instructions.md` | Copy `skills/`, then point at them from that file |

The adapters deliberately **point at** `skills/*/SKILL.md` rather than
copying the text. One source of truth; otherwise the formats drift and
you end up fixing the same sentence four times.

## How to actually use them

The sequence that would have saved the most time on the project these
came from:

**1. Flow spec before any code.** Open `app-flow-design`, fill
`flow-spec-template.md` with your agent. Twenty minutes of being asked
awkward questions. Output: a committed `docs/flows/onboarding.md`.

**2. Schema from the flow.** The gates you just wrote *are* the list of
questions your backend has to answer. "Have they actually joined
someone" tells you there's a nullable `partner_id` and that something
privileged has to set it. Go the other way — tables first — and you get
predicates shaped by whatever the schema made easy to ask, which is how
the trap in the table above happened.

**3. Then build**, with the Supabase skills open.

**4. Open `ios-app-store-release` before your first submission**, not
after a rejection. Most App Store rejections are metadata, and most are
predictable.

## Fonts

No fonts are bundled — display faces are usually licensed and not
redistributable. `skills/ios-app-store-release/scripts/` runs without
any (Pillow's default, which is ugly but proves the pipeline), and you
point it at your own:

```bash
BRANDKIT_BODY_FONT=/path/to/Body.ttf \
BRANDKIT_DISPLAY_FONT=/path/to/Display.otf \
python3 store-screenshots.py
```

For a reasonable free default, drop [DM
Sans](https://fonts.google.com/specimen/DM+Sans) into `scripts/`.

## Provenance and limits

These come from one app: a two-person iOS app on SwiftUI and Supabase,
roughly seventeen active days of work, shipped to the App Store in
October 2026. That's the honest scope.

What that means for you:

- **The Supabase and iOS specifics are battle-tested but narrow.** They
  cover what one app hit. They are not a survey of the platform.
- **Third-party tooling moves.** App Store Connect requirements and
  Supabase APIs change. Where something is time-sensitive it says so,
  but check the vendor's docs before trusting a specific size or field
  name.
- **`app-flow-design` generalises furthest**, because the failure modes
  it describes — conflating loading with empty, testing a proxy for the
  real condition, branches with no way back — aren't platform-specific
  at all.

If a rule here turns out to be wrong, please open an issue rather than
working around it. A skill people have learned to distrust is worse
than no skill.

## Licence

MIT — see [LICENSE](LICENSE).
