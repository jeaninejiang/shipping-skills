# Worked example — onboarding for a two-person app

The flow this method was extracted from, with the bugs it would have
caught. Every one of these shipped, and every one was found by a user
rather than by us.

---

## Purpose

Get paired with my partner and give the app enough about me that it can
say something useful.

## Entry points

| Entry | State on arrival |
|---|---|
| First launch after sign-up | nothing exists |
| Cold launch, onboarding incomplete | some of it exists |
| Returning after "Skip for now" | a solo partnership exists, no partner |

That third row is the one we never wrote down, and it is where the worst
bug lived.

## Exit conditions

| Outcome | Where they land | Reversible? |
|---|---|---|
| Completed | Home | n/a |
| Skipped | Home, browsing | yes — pairing stays reachable |
| Abandoned mid-way | resumes at the first unfilled step | yes |

---

## Gates

| Gate | Sentence | Predicate | Shipped as |
|---|---|---|---|
| Skip the pairing step? | "They have actually joined someone." | `partnership?.partnerId != nil` | ❌ `partnership != nil` |
| Show my code vs the join field? | "They chose to generate rather than join." | `choice == .generate` | ❌ `myPairingCode != nil` |
| Onboarding complete? | "Joined, named, and birth info saved." | all three, read from the server | ✅ |

### Bug 1 — the trap

`partnership != nil` meant "a row exists". A row existed after tapping
Generate, after Skip for now, after starting a map alone, and after
every failed join attempt. So:

1. User enters their partner's code
2. The join fails (a separate backend bug) but still creates a row
3. From then on, `partnership != nil` is true, so onboarding **skips the
   pairing step entirely**
4. No code field. No way back. The account can never be paired.

Writing the sentence first — *"they have actually joined someone"* —
makes `partnership != nil` obviously the wrong test. The fix was one
character of meaning and zero of difficulty; finding it took a day.

### Bug 2 — the hidden branch

The pairing screen showed the generated-code card whenever a code
existed. Having your own code is not a reason to hide the join field,
but the predicate conflated "I have a code" with "I am the one sharing
a code". Anyone who tapped Generate by accident, or whose partner got
there first, had no route to the other half of pairing.

This is exactly the §3 check: *a screen offers A or B; taking A hides B;
can someone legitimately want B afterwards?* Yes, obviously, and the
fix was a text button on the code card.

---

## Screens

### Pairing step

| State | What they see | CTA |
|---|---|---|
| Loading | spinner while resuming progress | — |
| Empty | "generate a code" / "I have a code" / skip | both, plus skip |
| Ready (code generated) | the code, how to share it | Continue, **and** "I have a code instead" |
| Waiting on other person | *we never designed this* | — |
| Error | the function's own message, inline | retry |

**Way out:** back to the choice from either branch. Missing on ship.

**Inputs:**

| Field | Validation | Error copy | Required |
|---|---|---|---|
| Pairing code | exists, unclaimed, not your own | "That code doesn't match anyone waiting to pair." / "That code has already been used." | yes, on this branch |

The three error cases are different and want different words — retype
it, get a new one, share yours instead. We shipped one generic message
for all three, which told people to double-check a code that was
perfectly correct.

### Profile step

| State | What they see | CTA |
|---|---|---|
| Loading | spinner | — |
| Empty | empty fields | Continue (disabled until valid) |
| Ready (resuming) | fields prefilled from the server | Continue |
| Error | inline per field | — |

**Inputs:**

| Field | Validation | Error copy | Required |
|---|---|---|---|
| Name | non-empty | "Let your partner know what to call you." | yes |
| Birth date | parses, round-trips, 18+ | "You need to be 18 or over to use this app." | yes |
| Birth city | non-empty | "Enter the city where you were born." | yes |

### Bug 3 — the inert button

Shipped with no validation messages: an invalid date or an untouched
city left Continue **enabled and silent**. Tapping it did nothing, with
no explanation. Users concluded the app was broken, which is the correct
conclusion from the available evidence.

### Bug 4 — the scroll wheel

A date picker for a birth year is dozens of flicks. Three numeric
fields with focus auto-advance replaced it. The round-trip check matters
too: `31 February` silently becomes March 3rd unless you read the
components back out and compare.

---

## The three walks

### 1. Brand new

Worked. This is the path we developed against, which is why everything
else broke.

### 2. Returning

**Bug 5:** Home ran `items.isEmpty` to pick between the empty state and
the content, so for the two seconds before data arrived, every returning
user was shown first-run prompts — "start your Desire Map" to someone
who finished it weeks ago.

Fixed with a `hasLoaded` flag per source, set in a `defer` so every exit
path sets it, and `empty` rendering only once loading has finished.

**Bug 6:** the Desire Map card said "Continue your map" regardless of
whether one had been started, because in-progress and not-started were
the same branch.

### 3. Half-done

Never traced, and it held bugs 1, 2 and 6. Specifically unconsidered:

- partner hasn't joined yet — most screens had no copy for it
- started on another device — resume worked by accident, not design
- skipped pairing and now wants it — the trap
- entered their partner's birth info before the partner existed — needed
  a parking table and a claim on join, discovered late

---

## What the method would have caught

| Bug | Caught by |
|---|---|
| Onboarding trap | §1 — write the gate as a sentence |
| Hidden join branch | §3 — can they legitimately want B later? |
| Inert Continue button | §4 — enabled, or disabled with a reason |
| Birth date scrolling | §4 — match the control to the data |
| First-run flash | §2 — empty is a conclusion, not a start |
| Wrong CTA copy | §2 — in-progress is its own state |
| Partner-hasn't-acted gaps | §6 — the multi-user axis |

Seven bugs, one page, written before any of it was built.
