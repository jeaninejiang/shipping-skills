---
name: supabase-edge-functions
description: Write, debug and deploy Supabase Edge Functions (Deno) — privileged server logic, invite/claim endpoints, calls to model and third-party APIs, transactional email, database-trigger webhooks. Use this whenever you are creating or editing anything under supabase/functions/, choosing between the anon and service-role client, handling secrets or Vault values, wiring a Postgres trigger to a function, or debugging a function that returns 200 but does not do what it should. Also use it when a deployed function behaves like an older version than the code in front of you.
---

# Supabase Edge Functions

Edge Functions exist to do the things the client is not allowed to do.
That privilege is the whole point, and also where the bugs live.

## Two clients, one decision

Every function that touches the database should create both, and the
choice per query is deliberate:

```ts
// User-scoped: respects the caller's JWT and RLS. The default.
const supabase = createClient(supabaseUrl, anonKey, {
  global: { headers: { Authorization: req.headers.get("Authorization")! } },
});

// Admin: bypasses RLS. For rows the caller legitimately needs but does
// not yet own.
const admin = createClient(supabaseUrl, serviceRoleKey, {
  auth: { autoRefreshToken: false, persistSession: false },
});
```

**Use `admin` only where RLS would hide a row the caller has a right to
act on.** In practice that is a short list:

- looking up a row by invite token or join code (the joiner does not own
  it — that is what joining means)
- the write that attaches them to it
- resolving "which of this user's rows is the primary one" across rows
  they may reach by email match rather than id

Everything else stays on `supabase`, so RLS keeps being a safety net
rather than decoration.

The failure is silent and worth recognising on sight: a user-scoped
lookup of a row the caller does not own returns **no error and no row**.
The branch then falls through to whatever comes next, which usually
succeeds with different data, and the caller gets a 200 describing
something that did not happen.

## Make every branch exit explicitly

Fall-through is what turns the above into a mystery. If a request
supplied a join code, that request should end inside the join branch —
paired, 404, or 409 — never by quietly becoming a different kind of
request.

```ts
if (pairingCode) {
  const { data: row } = await admin
    .from("partnerships").select("*").eq("pairing_code", code).maybeSingle();

  if (!row) return json({ error: "That code doesn't match anyone waiting to pair." }, 404);

  if (row.initiator_id === user.id || row.partner_id === user.id) {
    return json({ session: await getOrCreateSession(...), partnership: row });
  }
  if (row.partner_id) return json({ error: "That code has already been used." }, 409);

  // `is null` makes the claim atomic; checking the result distinguishes
  // winning the race from losing it.
  const { data: claimed } = await admin
    .from("partnerships")
    .update({ partner_id: user.id, status: "active" })
    .eq("id", row.id).is("partner_id", null)
    .select().maybeSingle();

  if (!claimed) return json({ error: "That code has already been used." }, 409);
  return json({ session: await getOrCreateSession(...), partnership: claimed });
}
```

Prefer `.maybeSingle()` over `.single()` for lookups that may legitimately
find nothing — `.single()` treats zero rows as an error, which pushes you
back toward swallowing it.

## Work that outlives the response

A function that responds and then keeps working gets killed mid-flight.
Database triggers calling in via `pg_net` are the classic case: `pg_net`
fires and disconnects, the runtime sees no client, and the worker is
dropped ("EarlyDrop") part-way through your `fetch`.

```ts
const task = (async () => { await sendEmail(...); })();
EdgeRuntime.waitUntil(task);
return json({ ok: true });          // respond immediately
```

Respond first, keep the work alive explicitly.

## Secrets

Function secrets are set with `supabase secrets set NAME=value` and read
with `Deno.env.get("NAME")`. `SUPABASE_URL` and `SUPABASE_ANON_KEY` are
provided by the platform; `SUPABASE_SERVICE_ROLE_KEY` you set yourself.

When a *database trigger* needs a value (a function URL, a shared
secret), it cannot read function secrets — put it in Vault and read it
from SQL. If you store the same name twice, lookups that take "the"
value get whichever row they happen to hit, so read deterministically:

```sql
select decrypted_secret from vault.decrypted_secrets
 where name = 'welcome_hook_secret'
 order by created_at desc limit 1;
```

A mismatch between a Vault value and a function secret produces an
unauthorised call that looks exactly like a bug in the function. Check
both before reading code.

## Errors the user will see

Provider errors must not reach a screen. They leak which vendor you use
and internal request ids, they make a temporary outage look like a
broken app, and they tell the reader nothing actionable:

> Failed to generate: 401 {"type":"error","error":{"type":
> "authentication_error","message":"invalid x-api-key"},"request_id":...}

Map status to one honest sentence, and keep the detail in the logs.
`references/errors.ts` is a ready-made version — copy it in. Note that
it deliberately never says a key is invalid or missing: the reader
cannot act on that, and "we're having trouble" is the true shape of it
from where they sit.

## Logging, because failures here are invisible

The client can only say "that didn't work", and the database shows the
end state rather than which branch produced it. One structured line per
interesting decision closes that gap:

```ts
console.log(JSON.stringify({
  fn: "session-bootstrap", flow: "pairing_code", code,
  user: user.id, found: Boolean(row), outcome: "paired",
}));
```

Read them in the dashboard under **Edge Functions → your function →
Logs**. `supabase functions logs <name>` exists only in newer CLI
versions, so the dashboard is the portable answer.

## Deploying

```bash
supabase functions deploy <name>
# --no-verify-jwt for functions called by database triggers or webhooks,
# which arrive without a user JWT
```

**`deploy` uploads the file on your disk, not the file in your repo.**
If you edited on GitHub, in another checkout, or in a web editor, pull
first. A deploy of stale code reports success exactly like a real one,
and the symptom — "I fixed it and redeployed and nothing changed" — is
indistinguishable from the fix not working.

When a deployed function seems older than your code, confirm before
re-debugging: **Edge Functions → your function → Code** shows what is
actually live. Searching it for a distinctive comment from your change
takes seconds and saves an hour.

## Checklist for a new function

- [ ] `OPTIONS` handled and CORS headers on every response
- [ ] Rejects a missing/invalid `Authorization` with 401 before any work
- [ ] Each query deliberately on `supabase` or `admin`
- [ ] Every branch returns; no silent fall-through
- [ ] Claim-style writes are `is null`-guarded and check the result
- [ ] Work after the response wrapped in `EdgeRuntime.waitUntil`
- [ ] Errors mapped through `readerFacing`
- [ ] One structured log line per meaningful outcome
- [ ] Secrets set, and Vault entries deduplicated
