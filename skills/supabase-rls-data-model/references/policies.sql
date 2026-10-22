-- RLS policy templates for a Supabase app with shared, multi-user data.
--
-- Substitute your own table and relationship names. The four shapes
-- below cover nearly everything: per-user rows, relationship-scoped
-- rows, write-your-own-only, and the claim that only a service role may
-- perform.

-- ============================================================
-- 0. The relationship table itself
--
-- `partnerships` here; a team, household or workspace is the same
-- shape. Note that `partner_id` is NULL until someone joins — that
-- nullability is what the whole claim flow turns on.
-- ============================================================

create table if not exists partnerships (
  id uuid primary key default gen_random_uuid(),
  initiator_id uuid not null references auth.users(id) on delete cascade,
  initiator_email text not null,
  partner_id uuid references auth.users(id) on delete set null,
  partner_email text,
  -- Short, human-typed join code. Exclude visually confusable
  -- characters (0/O, 1/I/L) — this gets read aloud and retyped.
  pairing_code text unique,
  -- Long, unguessable token for share links.
  invite_token uuid not null default gen_random_uuid(),
  status text not null default 'pending',
  created_at timestamptz not null default now()
);

alter table partnerships enable row level security;

-- Members see their own relationships. Deliberately does NOT expose a
-- row to someone holding its code — that lookup is a service-role job,
-- because exposing unclaimed rows by code to every authenticated user
-- turns the code space into something worth enumerating.
create policy "members read own partnerships"
  on partnerships for select
  using (
    initiator_id = auth.uid()
    or partner_id = auth.uid()
    or partner_email = auth.jwt() ->> 'email'
  );

create policy "users create their own partnerships"
  on partnerships for insert
  with check (initiator_id = auth.uid());

-- Members may update shared columns. Remember Postgres RLS is per-ROW:
-- this permits updating any column on the row, partner_id included. If
-- that matters, keep the sensitive column on its own table.
create policy "members update own partnerships"
  on partnerships for update
  using (initiator_id = auth.uid() or partner_id = auth.uid())
  with check (initiator_id = auth.uid() or partner_id = auth.uid());


-- ============================================================
-- 1. Per-user rows (profiles)
--
-- Yours to write; visible to you and to anyone you are related to.
-- ============================================================

alter table profiles enable row level security;

create policy "read own profile"
  on profiles for select using (id = auth.uid());

create policy "read related profiles"
  on profiles for select
  using (
    exists (
      select 1 from partnerships p
      where (p.initiator_id = auth.uid() and p.partner_id = profiles.id)
         or (p.partner_id   = auth.uid() and p.initiator_id = profiles.id)
    )
  );

create policy "write own profile"
  on profiles for update
  using (id = auth.uid())
  with check (id = auth.uid());


-- ============================================================
-- 2. Relationship-scoped rows both members may read
-- ============================================================

alter table important_dates enable row level security;

create policy "members read dates"
  on important_dates for select
  using (
    exists (
      select 1 from partnerships p
      where p.id = important_dates.partnership_id
        and (p.initiator_id = auth.uid() or p.partner_id = auth.uid())
    )
  );

create policy "members write dates"
  on important_dates for insert
  with check (
    exists (
      select 1 from partnerships p
      where p.id = important_dates.partnership_id
        and (p.initiator_id = auth.uid() or p.partner_id = auth.uid())
    )
  );


-- ============================================================
-- 3. Both read, each writes only their own
--
-- The shape for answers, reflections, nicknames — anything where the
-- pair shares visibility but authorship stays personal.
-- ============================================================

alter table answers enable row level security;

create policy "members read all answers"
  on answers for select
  using (
    exists (
      select 1 from partnerships p
      where p.id = answers.partnership_id
        and (p.initiator_id = auth.uid() or p.partner_id = auth.uid())
    )
  );

create policy "write only your own answer"
  on answers for insert
  with check (
    user_id = auth.uid()
    and exists (
      select 1 from partnerships p
      where p.id = answers.partnership_id
        and (p.initiator_id = auth.uid() or p.partner_id = auth.uid())
    )
  );

create policy "update only your own answer"
  on answers for update
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- One row per person per question, so a resubmit updates rather than
-- accumulating. Without this, "both have answered" counts get strange.
create unique index if not exists answers_one_per_person
  on answers (partnership_id, question_id, user_id);


-- ============================================================
-- 4. The claim
--
-- No policy here, on purpose. Attaching a joiner to a row they cannot
-- yet see is a service-role operation in a server function. Two things
-- make it safe to repeat:
--
--   * `is null` in the WHERE makes it atomic — concurrent claims cannot
--     both win, and the loser updates zero rows.
--   * checking what came back distinguishes "claimed it" from "someone
--     else already had it", which the caller needs in order to say
--     something true to the user.
-- ============================================================

-- As executed by the server with the service role:
--
--   update partnerships
--      set partner_id = $joiner, partner_email = $email, status = 'active'
--    where id = $row
--      and partner_id is null
--  returning *;
--
-- Zero rows back means it was already claimed. Say so; do not report a
-- successful join.
