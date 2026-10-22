---
name: app-flow-design
description: Design screen flow, onboarding and per-screen states before building them — gates and their predicates, the loading/empty/ready/error matrix, dead-end checks, input validation and escape hatches, and waiting states for slow operations. Use this whenever you are planning onboarding or a multi-step flow, adding a screen that loads data, deciding what a user sees before their data arrives, wiring a conditional that picks between screens, or debugging a screen that shows the wrong thing for a moment, shows a new-user prompt to a returning user, or traps someone with no way back. Reach for it while designing rather than after: most of these bugs are invisible to the account you develop with and obvious to every real user.
---

# Designing app flow

Most flow bugs are not wrong arrows between screens. They are one screen
rendering the wrong state — because "we don't know yet" and "there is
nothing" were the same condition, or because a gate tested a proxy for
the thing it meant.

So the order here is deliberate: get the gates and the states right
first, and the diagram afterwards. A flow chart drawn first looks
correct while every box still has the bug.

## 1. Write the gates as sentences

A gate is any point where the app chooses what to show. For each one,
write the predicate as a sentence about the user, then check the code
says the same thing.

| Gate | The sentence | The predicate |
|---|---|---|
| Skip the join step? | "They have actually joined someone." | `partnership?.partnerId != nil` |
| Show results? | "Both of them have finished." | `mySession.isComplete && theirSession.isComplete` |
| Show the paywall? | "They have no active entitlement." | `entitlement?.isActive != true` |

**If you cannot name the gate as a sentence about the user, the
predicate is a proxy and it will be wrong.** The costly version of this
in the app these came from was:

```swift
// "They have a partnership row" — a proxy.
step = partnership == nil ? .pairing : .profile

// "They have actually joined someone" — the real thing.
step = partnership?.partnerId == nil ? .pairing : .profile
```

A row existed after tapping Generate, after Skip, after starting alone,
and after every failed join. So the first version sent people past the
one screen they needed, permanently, and no amount of backend fixing
reached it.

Name gate variables after the sentence — `hasJoinedPartner`, not
`hasPartnership`. The name is what stops the next person widening it.

## 2. Fill the state matrix for every screen

Every screen that loads anything has at least four states, and a
multi-user app has a fifth. Write what the user sees in each, before
writing the view:

| State | Means | Trap |
|---|---|---|
| **Loading** | We don't know yet | Rendering the empty state while waiting |
| **Empty** | We know; there is nothing | Only true once loading has finished |
| **Ready** | We know; there is something | — |
| **Waiting on someone else** | Our part is done, theirs isn't | Reads as "empty" and tells them to start what they already did |
| **Error** | We tried and failed | Showing empty, so it looks like their fault |

The single most common bug in this list:

```swift
// Wrong. Before data arrives, `items` is ALSO empty.
if items.isEmpty { EmptyStatePrompt() } else { List(items) }

// Right. Empty is a conclusion, not a starting condition.
if !hasLoaded      { LoadingSkeleton() }
else if items.isEmpty { EmptyStatePrompt() }
else               { List(items) }
```

Keep a `hasLoaded` flag **per data source**, set in a `defer` so every
exit path — success, failure, early return — sets it. One global
`isLoading` is not enough when a screen loads three things that finish
at different times; the fast one renders its empty state while the slow
one is still in flight.

This is what made returning users see "get started" prompts for two
seconds on every launch. It is invisible to a developer with warm data
and glaring to everyone else.

## 3. Check every branch for a way out

For each branch, ask: **if the user is here by mistake, how do they get
out?**

The rule that catches most traps: *a branch chosen for the user, rather
than by the user, must be reversible.* Nobody chose to skip the join
step — a predicate did — so there had to be a route back to it. There
wasn't, and the account could never be paired again.

Two checks that find these quickly:

- **Entry points.** If something can only be set during onboarding, a
  user who skipped it has no way to provide it later. Every piece of
  data collected in a flow needs a second home in settings.
- **Mutually exclusive choices.** When a screen offers A or B, taking A
  usually hides B. If someone can legitimately want B afterwards — they
  tapped the wrong one, or their partner got there first — B has to stay
  reachable.

## 4. Every input: validate, explain, escape

A Continue button that does nothing when tapped is the worst possible
outcome, because the user has no idea whether the app is broken, slow,
or disagreeing with them. For each required input:

- **Validate against the real rule**, not the format. A date picker that
  accepts any date still needs the 18+ check.
- **Attach the error to the field**, not a banner at the top. "Enter the
  city where you were born" under the city field beats "Please complete
  all fields".
- **Either disable the CTA with a visible reason, or let it be tapped
  and explain.** Enabled-but-inert is what to avoid.
- **Offer an escape** for anything not strictly required. "Skip this,
  just browsing" costs one line and rescues the people who would
  otherwise delete the app at step two.

Also: match the input to the data. A scroll wheel for a birth year means
eighty flicks. Three numeric fields with focus auto-advance is less
elegant and far faster — and validate the round trip (`31 February`
parses into March unless you check the components come back out).

## 5. Time-box every wait

| Duration | What to show |
|---|---|
| under ~1s | nothing — a flash of spinner is worse than none |
| 1–3s | a skeleton shaped like the final layout |
| 3–10s | skeleton plus a line saying what is happening |
| over 10s | narrate: what, roughly how long, and keep moving |

For anything that takes the better part of a minute — a model call, a
long import — an unlabelled spinner reads as a hang. People tap away, or
tap again, and the second tap costs another API call. Say what it is
doing, say roughly how long, and change the message every few seconds:
the movement is what signals progress, more than the spinner is. Write
the messages as stages of real work rather than filler, and honour
Reduce Motion.

## 6. Walk it as three people

Before building, trace the flow three times:

1. **Brand new.** Nothing exists. Every screen hits its empty state.
2. **Returning.** Everything exists. No screen should ask for something
   they already gave, and nothing should flash a first-run prompt.
3. **Half-done.** Started on another device, abandoned mid-flow, or the
   other person hasn't acted yet.

**Most bugs live in the third one**, and it is the one nobody tests,
because the development account is permanently in the second. Deliberately
make a half-finished account and keep it.

For anything multi-user, add a fourth axis to every screen: what does
this look like when the other person hasn't done their part? "Waiting on
Sam" and "nothing here yet" are different screens with different copy
and different buttons.

## Artefacts

Fill `references/flow-spec-template.md` per flow — it is a page, not a
document, and the point is that writing it surfaces the gaps before the
code does. `references/worked-example.md` is a real onboarding flow run
through this method, with the bugs the matrix would have caught.

Draw the tree last, from the gates you wrote in step 1. By then it is a
record of decisions already made rather than a guess at them, which is
also what makes it worth keeping up to date.
