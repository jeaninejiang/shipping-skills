---
name: supabase-auth-swift
description: Build sign-up, sign-in and session handling for a SwiftUI app on Supabase Auth — email/password, Sign in with Google or Apple, OAuth redirect schemes, session restore on launch, sign-out and account deletion. Use this whenever you are adding or debugging login in a SwiftUI app, wiring an OAuth callback URL, deciding what the app does on launch before it knows who the user is, or chasing an intermittent 401 / "cancelled" error that only happens right after the app starts. Also use it when planning the first-run flow — what gets created at sign-up decides how messy the data model gets later.
---

# Supabase Auth in a SwiftUI app

## The bug that will cost you a day

**Supabase refresh tokens rotate, and they are single-use.**

If two calls fire concurrently at the moment a session needs refreshing,
both try to refresh. The first succeeds; the second presents a token
that has already been spent, is rejected, and the SDK invalidates the
session. You get a 401 and a `CancellationError`, the user is bounced to
sign-in, and it reproduces only on a cold launch with an expired
session — so roughly never while you are developing, and constantly for
real users returning the next day.

The shape that triggers it is the natural one:

```swift
// Looks fine. Is a session-killer on the first call after launch.
async let a = loadProfile()
async let b = loadPartnership()
async let c = loadReport()
_ = await (a, b, c)
```

**Serialise the first authenticated call after launch.** Once one call
has completed, the session is fresh and parallelism is safe — but the
simplest durable fix is to keep the launch sequence sequential and leave
a comment saying why, because this reads like an obvious optimisation
and someone will "fix" it back:

```swift
// Deliberately sequential. Supabase refresh tokens are single-use, so
// two concurrent calls at refresh time both try to refresh; the loser
// is rejected as already-used and the whole session is invalidated.
// Do not parallelise these without serialising the token refresh first.
let profile = try await loadProfile()
let partnership = try await loadPartnership()
```

Related: treat `CancellationError` as "not an error worth showing". It
surfaces during normal teardown and turns into phantom error banners.

## Shape of the auth layer

Keep one observable object owning the session, and let the root view
switch on it. The thing to avoid is a local "is logged in" flag that has
to be kept in sync with the server:

```swift
@MainActor final class AuthModel: ObservableObject {
    @Published private(set) var userId: String?
    @Published private(set) var isRestoring = true

    func restore() async {
        defer { isRestoring = false }
        userId = try? await client.auth.session.user.id.uuidString
    }
}
```

`isRestoring` matters more than it looks: without it the root view
renders the signed-out state for a frame on every launch, and returning
users see a flash of the login screen.

## Email and password

```swift
try await client.auth.signUp(email: email, password: password)
try await client.auth.signIn(email: email, password: password)
```

On the form itself, set `textContentType` — it is what makes iOS offer
AutoFill and the strong-password suggestion, and its absence is a
quiet conversion leak:

```swift
TextField("Email", text: $email)
    .textContentType(.username)
    .keyboardType(.emailAddress)
    .textInputAutocapitalization(.never)
    .autocorrectionDisabled()

SecureField("Password", text: $password)
    .textContentType(isSignUp ? .newPassword : .password)
```

## OAuth (Google, Apple)

Three things have to agree or the browser sheet opens and never comes
back:

1. A custom URL scheme in the project config —
   `CFBundleURLSchemes: [com.yourcompany.yourapp]`
2. The same scheme registered as a Redirect URL in **Supabase Auth →
   URL Configuration**
3. The provider's own console (Google Cloud, Apple) listing Supabase's
   callback

```swift
try await client.auth.signInWithOAuth(
    provider: .google,
    redirectTo: URL(string: "com.yourcompany.yourapp://auth-callback")
)
```

**The consent screen shows your Supabase project URL by default**, which
reads as untrustworthy on a personal app ("something-random.supabase.co
wants access"). Fixing it means verifying a branded domain with Google
— a real process with a homepage and privacy policy requirement, not a
settings toggle. Plan for it before launch rather than discovering it
during one.

If you offer any third-party sign-in, read the App Store guideline 4.8
section of the `ios-app-store-release` skill before you submit.

## What sign-up creates

The most consequential decision in this file, and it is easy to make by
accident: **do not auto-create a relationship, workspace or group row
just because someone signed up.**

If you do, a user who later joins someone else's ends up owning two, and
their own empty one is the *newer* of the pair. Every "most recent wins"
lookup then prefers the empty one, forever. See the
`supabase-rls-data-model` skill — the fix is to prefer the complete row
over the recent one, in one shared helper, but not creating the stray in
the first place is better.

Create the account. Let the user tell you what they are joining.

## Onboarding state lives on the server

Derive "is onboarding done" by asking the server what exists, not from a
local flag. Someone who starts on one device and finishes on another
should not be asked twice.

And be precise about what counts as done. Checking that a relationship
row *exists* is not the same as checking it has two people in it:

```swift
// Wrong: any row counts, including the empty one they made by accident.
step = partnership == nil ? .pairing : .profile

// Right: only an actually-joined relationship skips the join step.
step = partnership?.partnerId == nil ? .pairing : .profile
```

The wrong version builds a trap — once a stray row exists, the join
screen never renders again and the account can never be paired.

## Sign-out and deletion

`client.auth.signOut()` clears the local session. Deleting an account
needs the service role, so it belongs in an Edge Function; the App Store
requires it to be reachable in-app (guideline 5.1.1(v)) if you offer
account creation at all. Be explicit in your privacy policy about what
deletion removes and what it does not — data that genuinely belongs to
another user is normally retained, and saying so plainly is better than
implying a clean sweep.

## Recovering from a 401

A session can end at any time. Catch 401 at the service layer, clear the
session and route to sign-in with a short explanation, rather than
letting a failed decode surface as a generic error. Users read "couldn't
load" as the app being broken; "please sign in again" they just act on.
