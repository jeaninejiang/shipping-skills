# Flow spec — <name of flow>

One page per flow. If it runs past two, the flow is probably two flows.

Fill it before building. The value is not the document; it is that the
blanks are uncomfortable to leave empty, and each one you cannot fill is
a decision you were about to make accidentally in code.

---

## Purpose

What the user is trying to get done, in their words, in one sentence.
Not "complete onboarding" — "get set up so I can see our results".

## Entry points

Everywhere this flow can start. Include the ones you did not design:
a push notification, a deep link, a cold launch mid-flow, a return from
the browser after OAuth.

| Entry | State on arrival |
|---|---|
| | |

## Exit conditions

| Outcome | Where they land | Is it reversible? |
|---|---|---|
| Completed | | |
| Skipped | | |
| Abandoned mid-way | | |

"Abandoned" is not optional. Someone will background the app on step
two and come back in a week.

---

## Gates

One row per decision point. Write the sentence first, then the
predicate, then check they say the same thing.

| Gate | Sentence about the user | Predicate | Where it's evaluated |
|---|---|---|---|
| | | | |

Checks:

- [ ] Every predicate tests the real condition, not a proxy for it
- [ ] Every gate variable is named after its sentence
- [ ] Gates read server state, not a local "done" flag
- [ ] The same gate is not re-derived in more than one place

---

## Screens

Copy this block per screen.

### <screen name>

| State | What they see | CTA |
|---|---|---|
| Loading | | |
| Empty | | |
| Ready | | |
| Waiting on other person | | |
| Error | | |

**Data this screen needs:** <list each source, each with its own
`hasLoaded`>

**Way out:** if someone lands here by mistake, how do they leave?

**Inputs:**

| Field | Validation rule | Error copy | Required? |
|---|---|---|---|
| | | | |

- [ ] CTA is either enabled, or disabled with a visible reason — never
      enabled and inert
- [ ] Errors attach to the field, not a banner
- [ ] Anything not strictly required has a skip
- [ ] Each input's control suits its data (no scroll wheel for a year)

**Waits:** longest operation on this screen, and what shows during it.

---

## The three walks

Trace the whole flow as each, and note what breaks.

### 1. Brand new — nothing exists

### 2. Returning — everything exists

- [ ] Nothing asks for something they already gave
- [ ] No first-run prompt flashes before data arrives

### 3. Half-done — started elsewhere, abandoned, or waiting on someone

- [ ] Resumes at the right step rather than restarting
- [ ] Partial data is not overwritten with blanks
- [ ] "Waiting on them" is distinct from "nothing here"

---

## Flow diagram

Draw it last, from the gates above.

```
        ┌──────────┐
        │  entry   │
        └────┬─────┘
             │  <gate sentence>
      ┌──────┴──────┐
      ▼             ▼
  ┌───────┐     ┌───────┐
  │   A   │◄───►│   B   │   ← both directions, if the branch
  └───┬───┘     └───┬───┘     was chosen FOR the user
      └──────┬──────┘
             ▼
        ┌──────────┐
        │   exit   │
        └──────────┘
```

Every one-way arrow into a branch the user did not pick is a trap until
you can explain why it isn't.
