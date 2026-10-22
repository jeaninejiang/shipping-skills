---
name: ios-app-store-release
description: Take a SwiftUI iOS app from source to TestFlight and the App Store — XcodeGen project.yml setup, bundling resources, build and marketing version numbers, archiving, the privacy manifest, App Privacy answers, screenshots and creative assets at Apple's exact pixel sizes, and the pre-submission checklist. Use this whenever you are configuring an Xcode project, preparing a build for upload, answering anything in App Store Connect, generating store screenshots, setting up internal or external TestFlight testers, or diagnosing a rejection. Reach for it before the first submission rather than after — most rejections here are metadata, and most of them are predictable.
---

# Shipping a SwiftUI app to the App Store

## XcodeGen

If the project is generated from `project.yml`, the `.xcodeproj` is
build output: gitignore it, never hand-edit it, and re-run `xcodegen
generate` after every change to `project.yml`.

Two traps account for most lost time.

### `resources:` does not bundle anything

Files land in the bundle because they are under a target's `sources:`,
not because a `resources:` block names them. A privacy manifest or a
markdown file listed only under `resources:` is silently absent at
runtime — and `PrivacyInfo.xcprivacy` missing is an upload rejection,
not a runtime bug.

```yaml
targets:
  MyApp:
    sources:
      - path: MyApp
      - path: MyApp/Resources      # this is what bundles them
```

### Version numbers are baked in at generate time

XcodeGen writes an `Info.plist` with literal values, and a literal beats
a build setting. If `CFBundleVersion` is the string `"1"`, setting
`CURRENT_PROJECT_VERSION` does nothing — you will archive again and
again and watch Xcode report the old number.

Make the plist reference the settings:

```yaml
info:
  properties:
    CFBundleShortVersionString: "$(MARKETING_VERSION)"
    CFBundleVersion: "$(CURRENT_PROJECT_VERSION)"
settings:
  base:
    MARKETING_VERSION: "1.0.0"
    CURRENT_PROJECT_VERSION: "4"   # bump for EVERY upload
    DEVELOPMENT_TEAM: XXXXXXXXXX
    CODE_SIGN_STYLE: Automatic
```

A build number can never be reused, even for a rejected or deleted
build. Marketing version changes only when the release does.

### When the archive still shows the old version

Work down this list; it is ordered by how often it is the answer.

1. **Is the change on this machine?** Editing `project.yml` on GitHub
   does not touch your Mac, and Xcode builds from your Mac. `git pull`.
2. `xcodegen generate` — did it actually run, in the repo root?
3. **Close the project window entirely**, then reopen. XcodeGen rewrote
   the `.xcodeproj` underneath Xcode, which is still holding the old one.
4. Product → Clean Build Folder (⇧⌘K).
5. Check `Info.plist`: `CFBundleVersion` should read
   `$(CURRENT_PROJECT_VERSION)`, not a number.

## The privacy manifest

`PrivacyInfo.xcprivacy` at the bundle root. Required if you touch a
"required reason API" — and `@AppStorage` is `UserDefaults`, so most
apps do (reason `CA92.1` for your own app's values, no app group).

Declare `NSPrivacyTracking` honestly and list every collected data type
with its purpose. Then — this is the part people miss — **make the
manifest and your App Store Connect answers agree.** Apple can compare
them, and a contradiction is machine-checkable.

## App Privacy in App Store Connect

"Tracking" has a narrow meaning: linking your data with third-party data
for targeted advertising, or sharing it with data brokers. Using an
analytics SDK, or sending data to your own backend, is **not** tracking.
If you do neither of those things, **"Data Used to Track You" must be
empty** — anything in it prints a warning banner on your public listing.

Equally, do not under-declare. If your manifest lists five data types,
Connect should list the same five. Typical set for an app with accounts:

| Type | Linked | Tracking | Purpose |
|---|---|---|---|
| Email Address | Yes | No | App Functionality |
| Name | Yes | No | App Functionality |
| User ID | Yes | No | App Functionality |
| Other User Content | Yes | No | App Functionality |

Only declare Crash/Performance Data if you actually ship an SDK that
collects it — Apple's own crash reporting is Apple's, not yours.

**App Privacy has its own Publish button**, separate from everything
else, and editing after publishing un-publishes it. "An Admin must
provide information about the app's privacy practices" almost always
means saved-but-not-published, not a permissions problem.

## Screenshots and creative assets

App Store Connect matches on **exact pixel size** and rejects anything
else. Useful sizes:

| Purpose | Size | Notes |
|---|---|---|
| iPhone, Dynamic Island medium | 1179 × 2556 | |
| iPhone 6.9" | 1320 × 2868 | |
| Product page header, 21:9 | 3840 × 1646 | optional, iOS 27+ |
| Header / search, 16:9 | 5244 × 2950 | PNG only; valid in both slots |
| Search results, 3:2 | 1920×1280 – 3840×2560 | optional, iOS 27+ |

Header and search assets are **optional** — skip them for a first
submission. No transparency or alpha channel is allowed on any of them.

Generate rather than hand-composite: express every measurement against a
reference width and scale, so adding a size costs nothing and a UI
change means re-running a script. `scripts/` here holds a working
generator — `brandkit.py` (palette, gradient, type, device frame),
`store-screenshots.py` (portrait panels), `store-creative-assets.py`
(landscape header/search). Copy them in and change the palette, the
font and the panel list.

Draw a plain rounded bezel rather than a photoreal iPhone; App Review is
touchier about depicting specific hardware.

## Before you submit

- [ ] **Build attached** — and it is the build you just uploaded
- [ ] **Demo account**, already in whatever state the app needs. For
      anything multi-user, the accounts must already be joined and
      populated: a reviewer with one account sees empty states and
      rejects under 2.1 as incomplete. This is the single most common
      rejection for two-person apps.
- [ ] **App Review notes**: what the app is, the demo credentials, how
      age gating works, where account deletion lives, which third
      parties process data, and which visible features are deliberately
      not reachable
- [ ] **Copyright**: `2026 Your Name Or Company`, no © symbol
- [ ] **Content Rights**: "No" unless you display someone else's
      licensed media — your own content and model-generated text for the
      user are not third-party content
- [ ] **Age rating** answered honestly; understating is a fast rejection
- [ ] **Privacy Policy URL** live and reachable
- [ ] **Support URL** filled in
- [ ] **Account deletion in-app** (5.1.1(v)) if you offer sign-up
- [ ] **App Privacy published**
- [ ] Every in-app external link actually loads

### Guideline 4.8

If you offer Google or Facebook sign-in, you must also offer a
privacy-preserving option. Email/password usually satisfies it and many
apps pass on exactly that basis, but it is ambiguous and 4.8 rejections
happen. It is a metadata/login rejection, not a redesign — a day of
work, not a reason to delay a first submission.

## TestFlight

Three separate gates, routinely conflated:

| | Review |
|---|---|
| Internal testers (≤100, your team) | none |
| External testers (≤10,000) | **Beta App Review**, per build |
| App Store release | App Review |

App Store approval does **not** open external TestFlight — that is its
own submission from the TestFlight tab, usually faster. Fill in Test
Information including demo account details; beta reviewers hit the same
walls as App Review. Once one build in a version train clears, later
builds usually go out much faster.

## Release order that works

1. Register the bundle ID and create the app record
2. `CURRENT_PROJECT_VERSION` → next number; `xcodegen generate`
3. Archive, upload, wait for processing
4. Internal TestFlight, on a real device, with a *fresh* account —
   first-run bugs are invisible to accounts that already have data
5. Metadata, screenshots, privacy, review notes
6. Attach build, submit
