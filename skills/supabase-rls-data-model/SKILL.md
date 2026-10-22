---
name: supabase-rls-data-model
description: Design Postgres tables, Row Level Security policies and migrations for a Supabase app where data is shared between users — couples, teams, households, invites, join codes, anything two or more accounts touch. Use this whenever you are creating or changing a Supabase table, writing or debugging an RLS policy, adding an invite/pairing/join flow, or investigating why a query returns nothing for one user but works for another. Reach for it early: RLS decisions are cheap to make correctly up front and expensive to unpick once rows exist, and the most common failure mode is a silent empty result rather than an error.
---

# Shared data and RLS on Supabase

RLS is a filter, not a gate. A query the policy excludes does not fail —
it returns zero rows, with a 200. Almost every hard bug in this area is
that silence being mistaken for "no data", so the design job is mostly
about noticing where a user legitimately needs to touch a row they do
not yet own.

## The rule that matters most

**Anyone joining something cannot see it yet.**

An invite code, a pairing code, a share link, a team join token — the
whole point is that a stranger acts on a row that is not theirs. Every
RLS policy you would naturally write keys on "is this user on this row",
and the joiner is not, *yet*. So:

> A claim operation — the write that first attaches a user to a row —
> must run with the service role, on the server. It can never work from
> a user-scoped client.

This is not an optimisation. It is the difference between working and
silently doing nothing. Write the claim as a server function (Supabase
Edge Function, or a Next.js route handler) with a service-role client,
and keep the rest of the app on user-scoped clients where RLS protects
you.

See the `supabase-edge-functions` skill for how to write that function
safely — the claim has its own trap list (atomicity, explicit exits).

## Designing a table

For each new table, answer these before writing the DDL:

1. **Who owns a row?** One user, or a relationship/group?
2. **Who may read it?** Often "both members", which means the policy has
   to reach through the relationship table.
3. **Who may write it?** Usually narrower than read — "only your own
   answer", even when both can see both answers.
4. **Is there a moment someone joins?** If yes, that path needs the
   service role, and you should write down where that code lives.
5. **What should happen on delete?** `on delete cascade` from the
   relationship is right for data that only makes sense inside it.

Then enable RLS. A table without `enable row level security` is readable
by every authenticated user via the anon key, which is public by design
and shipped in your client.

## Policy shapes

Keyed on the relationship, not duplicated per row — this is the shape
that keeps "both members can see it, only you can write yours" honest:

```sql
alter table answers enable row level security;

create policy "members can read answers"
  on answers for select
  using (
    exists (
      select 1 from partnerships p
      where p.id = answers.partnership_id
        and (p.initiator_id = auth.uid() or p.partner_id = auth.uid())
    )
  );

create policy "you write only your own"
  on answers for insert
  with check (
    user_id = auth.uid()
    and exists (
      select 1 from partnerships p
      where p.id = answers.partnership_id
        and (p.initiator_id = auth.uid() or p.partner_id = auth.uid())
    )
  );
```

Two things worth internalising:

- **Postgres RLS cannot restrict individual columns.** A policy is
  per-row. If one column on a shared table should be writable by only
  one party, it needs its own table — otherwise "can update this row"
  means "can update every column on it".
- **`using` governs which rows are visible to the operation; `with
  check` governs what the new values may be.** Updates generally want
  both, and leaving `with check` off an update policy lets someone move
  a row out of their own visibility.

`references/policies.sql` has copy-ready templates for the common
shapes: per-user rows, relationship-scoped rows, write-your-own-only,
and the "claim" row that only a service role may set.

## Two bugs that look like a broken feature

### Reading a row you do not own yet

Symptom: an invite link or join code does nothing. No error. The
database shows the row still unclaimed.

Cause: the lookup ran on a user-scoped client. RLS hid it.

The tell is that the code *falls through* to some other branch and
returns a success response built from different data, so the client
cannot distinguish "joined" from "did nothing". Fix the client used for
the lookup, and make the join path return an explicit error when it
cannot join — see the Edge Functions skill.

### "Most recent wins" picks the wrong row

Symptom: a user joins successfully, then on the next launch is back in
an empty state.

Cause: signing up (or using the product alone) created a row of their
own, and it is *newer* than the one they joined. `order by created_at
desc limit 1` picks the empty one, forever.

Resolve a user's primary row by **completeness first, recency second**:

```sql
-- prefer a relationship with both members, then the newest
select * from partnerships
where initiator_id = $1 or partner_id = $1 or partner_email = $2
order by (partner_id is not null) desc, created_at desc
limit 1;
```

Apply the same rule everywhere the client asks "which one is mine" — one
helper, used by every call site, rather than `.first` repeated in five
views. Those drift.

## Migrations

Keep one `.sql` file per change under `supabase/migrations/`, named
`YYYYMMDD_what_it_does.sql`, and make each idempotent (`create table if
not exists`, `drop policy if exists` before `create policy`). You will
re-run them against a database that is partly migrated more often than
you expect.

Write a comment at the top of each file explaining *why*, not what. The
schema says what. Six months on, "why is this column nullable" is the
question you actually have.

## Checking your work

The only reliable test is two real accounts. Specifically:

- Account B joins A's invite/code. Does the row show B attached?
- B closes and reopens. Do they still see the shared data?
- B tries a code that was already used. Do they get a clear error?
- B tries their own code. Does it refuse rather than silently succeed?

Each of those maps to a bug that is invisible with one account.
