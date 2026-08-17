# OpenCode Task — Nothing / UpDownVid: Safe Supabase Migration + OAuth + YouTube Analytics + Extraction Validation + Downloader Hardening

## READ THIS FIRST

You are working on the existing **Nothing / UpDownVid** repository.

Repository:
`https://github.com/Unknowmyt1M/Nothing`

Supabase project already exists:
`https://supabase.com/dashboard/project/nrrtzcqikofzzzcanwxr`

I have already connected/configured a **Supabase MCP** for you. You can access this Supabase project through MCP.

### CRITICAL MCP RULE

Use the Supabase MCP for work that the MCP can perform, especially:

- Inspecting the existing Supabase project
- Inspecting tables/schema
- Creating/updating tables
- Creating migrations where supported
- Creating indexes/constraints
- Creating/updating RLS policies
- Inspecting database state
- Verifying inserted/migrated records
- Checking database errors
- Any other database operation supported by the MCP

Do **NOT** ask me to manually perform database work if the Supabase MCP can do it.

I will manually configure/provide the Google OAuth **Client ID and Client Secret** in Supabase's Google provider. Do not generate or hardcode those credentials.

---

# 0. VERY IMPORTANT — PREVENT THE WEBSITE/AGENT FROM FREEZING

The previous large implementation prompt caused my website/browser to freeze for around 10 minutes. Therefore this task MUST be executed incrementally.

## Never do this

- Do not rewrite the entire repository in one operation.
- Do not generate huge files unnecessarily.
- Do not dump the entire repository into context repeatedly.
- Do not make unrelated refactors.
- Do not install dozens of packages at once.
- Do not run expensive full-project tests after every tiny change.
- Do not start multiple duplicate dev servers/workers.
- Do not make repeated Supabase API calls in loops when one query will work.
- Do not repeatedly re-read unchanged files.

## Required implementation strategy

Work in small phases:

1. Inspect repository and current architecture.
2. Inspect Supabase through MCP.
3. Create a short implementation plan.
4. Implement one logical subsystem at a time.
5. Run a small targeted validation after each subsystem.
6. Only then continue to the next subsystem.
7. Run the final regression suite once the implementation is stable.

After each major phase, briefly record:

- files changed
- what was fixed
- what remains
- validation performed

Do not pause for confirmation between phases unless you encounter an actual destructive/ambiguous decision.

---

# 1. FIRST: READ THE ACTUAL CODE

Before modifying anything, inspect the repository's current implementation.

The repository currently contains, among other things:

```text
backend/
  api/
    auth_routes.py
    automation_routes.py
    debug_routes.py
    downloader_routes.py
  database/
    json_db.py
  platforms/
  services/
  app.py
  config.py
  main.py
frontend/
  src/
```

Do not assume the architecture from this prompt is perfectly current. The code is the source of truth.

Inspect:

- downloader routes/services
- platform detection
- metadata extraction
- format extraction
- download logic
- temporary file handling
- YouTube upload flow
- Google OAuth flow
- Accounts page/components
- automation service/routes
- JSON database layer
- current Supabase integration, if partially implemented
- frontend API/client/session handling
- environment configuration
- package manifests

Also inspect the current Git status/diff before changing anything so existing user work is not overwritten.

---

# 2. CURRENT EXTRACTION BUG — MUST FIX FIRST

The attached screenshot demonstrates a serious bug.

A YouTube URL such as:

```text
https://youtube.com/playables/...
```

is currently being detected as a normal YouTube video and the UI is displaying fake/placeholder-looking metadata such as:

```text
Title: playables
Duration: 0:00
Views: 0
```

This is NOT acceptable.

The extractor must never treat an unsupported/non-video YouTube resource as a valid video merely because the URL contains a YouTube hostname.

---

# 3. STRICT URL VALIDATION / RESOURCE VALIDATION

Separate these concepts:

```text
URL belongs to YouTube
```

and:

```text
URL identifies a supported downloadable video resource
```

They are NOT the same.

Before returning successful metadata, the backend must validate that the resource is actually a supported video.

For YouTube, explicitly handle/reject unsupported URL types including, where applicable:

- `/playables/`
- channel URLs
- `/@handle`
- `/channel/...`
- `/c/...`
- search URLs
- playlist-only URLs unless playlist support is intentionally implemented
- Shorts if Shorts are unsupported by the current downloader path
- live pages/live streams if unsupported
- YouTube Music pages if unsupported
- malformed YouTube URLs
- non-video YouTube pages

Do not guess.

If the project already supports some of these, preserve that support and validate them correctly.

The same principle applies to every other supported platform.

---

# 4. NEVER RETURN FAKE METADATA

This is a strict rule.

If extraction fails, do NOT return:

```text
Title = URL slug
Duration = 0
Views = 0
Thumbnail = placeholder
Platform = supported
```

and pretend extraction succeeded.

Instead return a structured error.

Example:

```json
{
  "success": false,
  "error_code": "UNSUPPORTED_URL_TYPE",
  "message": "This YouTube URL is not a supported video URL."
}
```

The frontend must render a clear human-readable error.

---

# 5. STRUCTURED EXTRACTION RESULT

Where practical, normalize extractor results to something like:

```text
success
platform
resource_type
url
canonical_url
title
description
thumbnail
duration
views
uploader
upload_date
formats
error_code
error_message
```

`success=true` must mean that the resource was genuinely validated and metadata is trustworthy.

`formats=[]` must not be presented as a successful extraction if the underlying resource itself is invalid.

---

# 6. ERROR CODES

Create consistent application-level error codes.

At minimum support categories like:

```text
INVALID_URL
UNSUPPORTED_URL_TYPE
UNSUPPORTED_PLATFORM
VIDEO_NOT_FOUND
VIDEO_PRIVATE
VIDEO_UNAVAILABLE
VIDEO_REGION_BLOCKED
LOGIN_REQUIRED
BOT_CHECK
AGE_RESTRICTED
EXTRACTION_FAILED
NO_VIDEO_FORMATS
NETWORK_ERROR
TIMEOUT
RATE_LIMITED
DOWNLOAD_FAILED
DOWNLOAD_CANCELLED
FILE_TOO_LARGE
FFMPEG_FAILED
YOUTUBE_AUTH_EXPIRED
YOUTUBE_PERMISSION_DENIED
DATABASE_ERROR
UNKNOWN_ERROR
```

Map low-level yt-dlp/platform/library errors into these codes where possible.

Never expose raw stack traces to normal users.

Keep detailed errors in server logs for debugging.

---

# 7. BEAUTIFUL ERROR UX

The existing frontend style should be preserved.

Use the project's existing toast/error components if available.

Errors should be specific and useful.

Examples:

### Unsupported YouTube Playable

> This link is a YouTube Playable, not a standard video URL. Nothing can't extract it as a normal video yet.

### Private video

> This video is private and cannot be downloaded with the current account/session.

### Region blocked

> This video isn't available in your current region.

### No formats

> The video was found, but no downloadable formats are currently available.

### Network failure

> We couldn't reach the source. Check your connection and try again.

### Login required

> This video requires authentication. Connect an authorized account or provide supported cookies.

Do not use one generic `Something went wrong` message for every failure.

---

# 8. TEST EVERY URL TYPE

Build a safe validation/test matrix for every platform already supported by Nothing.

Test at least:

- normal video URL
- short URL
- mobile URL
- watch URL with query parameters
- URL with tracking parameters
- malformed URL
- unsupported resource URL
- deleted/unavailable URL
- private URL where safely testable
- playlist URL
- channel URL
- live URL
- Shorts URL
- direct media URL if supported

Do not perform unauthorized/private access.

Use public URLs and existing project-supported authentication only.

If a URL cannot be safely tested automatically, add a deterministic parser/validation test instead of trying to bypass access controls.

---

# 9. QUALITY TESTING / DOWNLOAD HARDENING

For valid downloadable videos, test the downloader against every **available quality/format that the extractor reports**.

Do not blindly download every enormous 4K/8K file.

Instead implement a safe test policy.

For each available format:

1. Inspect estimated file size when available.
2. If the size is reasonable, test the complete download.
3. If the file is very large or unknown and the purpose is only extraction/download validation, perform a controlled partial/range test if the downloader/backend supports it.
4. Cancel safely after enough bytes have been downloaded to verify the stream.
5. Delete the temporary file immediately.
6. Never leave test files behind.

### Important

Do not interpret a partial/cancelled test as a successful full download.

Record:

```text
format_id
resolution
fps
codec
container
estimated_size
test_type
bytes_downloaded
status
error
```

---

# 10. FILE SIZE SAFETY

Implement a configurable safety limit for test downloads.

If an individual test would require an excessive amount of data:

```text
Do not fully download it just for testing.
```

Perform a bounded stream/range validation if technically possible.

If partial testing is not supported safely by the specific platform/format, skip that format and report:

```text
SKIPPED_LARGE_TEST
```

Do not corrupt production download behavior merely to make automated tests pass.

---

# 11. TEMP FILE CLEANUP

Every test/download path must have cleanup in a `finally`-equivalent path.

After a test:

- delete partial file
- delete merged file
- delete temporary metadata
- delete temporary thumbnails if created
- remove empty temporary directories where appropriate

Cleanup must also happen when:

- extraction fails
- download fails
- user cancels
- timeout occurs
- process crashes after a recoverable step

Do not delete user-owned files outside the application's own temporary/download workspace.

---

# 12. DO NOT BREAK THE EXISTING DOWNLOADER

Preserve:

- platform detection
- metadata extraction
- format selection
- quality selector
- download progress
- cancellation
- ffmpeg merging
- uploader pipeline
- local file cleanup

Only improve validation/error handling where necessary.

---

# 13. SUPABASE — USE THE EXISTING MCP

Supabase project:

```text
nrrtzcqikofzzzcanwxr
```

Use the connected Supabase MCP for all database work it supports.

First inspect what already exists in the project.

Do NOT blindly create duplicate tables.

Determine whether the previous implementation already created any of:

```text
profiles
youtube_connections
user_settings
monitored_channels
automation_logs
automation_status
upload_history
download_jobs
channel_analytics_cache
```

Reuse/alter existing correct structures instead of duplicating them.

---

# 14. SUPABASE DATA MODEL

The final application should use Supabase/PostgreSQL as the authoritative persistent database.

User identity must be based on:

```text
auth.users.id
```

not an email-derived directory name.

At minimum support user-owned data for:

- profile
- settings
- YouTube connection
- monitored channels
- automation state/logs
- upload history
- download jobs where useful
- analytics cache where useful

Use proper foreign keys, constraints and indexes.

---

# 15. RLS

Enable and verify Row Level Security for user-owned tables.

A user must only access their own records.

Use the authenticated user ID as the ownership boundary.

Do not rely on frontend filtering for authorization.

The service-role key must never be exposed to the browser.

---

# 16. GOOGLE OAUTH / SUPABASE

I will provide/configure the Google OAuth Client ID and Client Secret in Supabase.

The configured Google scopes include:

```text
openid
https://www.googleapis.com/auth/userinfo.email
https://www.googleapis.com/auth/userinfo.profile
https://www.googleapis.com/auth/yt-analytics.readonly
https://www.googleapis.com/auth/yt-analytics-monetary.readonly
https://www.googleapis.com/auth/youtube.readonly
https://www.googleapis.com/auth/youtube
https://www.googleapis.com/auth/youtube.force-ssl
https://www.googleapis.com/auth/youtube.upload
```

Use only the scopes actually required by each feature.

Verify that the resulting Google authorization/token flow genuinely supports:

- channel information
- YouTube uploads
- YouTube Analytics
- monetary analytics where eligible
- token refresh for long-running automation

Do not assume Supabase session authentication alone automatically solves long-lived YouTube API credentials.

If a secure backend-side provider-token/Google credential connection is required, implement it using the existing architecture while keeping Supabase user identity as the canonical application identity.

Never expose refresh tokens/access tokens/client secrets to the frontend.

---

# 17. ACCOUNTS PAGE — CHANNEL ANALYTICS TAB

Read the existing Accounts page and account components first.

Add a new integrated tab:

```text
Channel Analytics
```

It must visually belong to Nothing.

Do not create an unrelated dashboard style.

---

# 18. CHANNEL ANALYTICS DASHBOARD

Build a production-quality YouTube analytics dashboard using actual YouTube API data.

Include, where the authorized API/data supports it:

### Channel overview

- channel avatar
- channel name
- handle
- channel ID
- subscriber count
- total videos
- total views
- connection status

### Date range

- Last 7 days
- Last 28 days
- Last 30 days
- Last 90 days
- Last 365 days
- This year
- Previous year
- Custom

Default to Last 28 Days.

### KPI cards

- Views
- Watch time
- Subscribers gained
- Subscribers lost
- Net subscribers
- Estimated revenue when available

Show previous-period comparison where reliable.

---

# 19. CHARTS

Add interactive, responsive charts for:

- views over time
- watch time
- subscriber growth
- revenue when available
- engagement where meaningful

Include hover tooltips and smooth but lightweight transitions.

Do not create fake data.

---

# 20. TOP VIDEOS

Show top-performing videos for the selected period.

Where available include:

- thumbnail
- title
- published date
- views
- watch time
- likes
- comments
- subscribers gained
- revenue

Allow opening the video on YouTube.

If detailed per-video analytics are available, provide a detail view.

---

# 21. TRAFFIC / AUDIENCE

Where supported by YouTube Analytics API, include:

- traffic sources
- geography/countries
- device type
- operating system
- audience/content dimensions supported by the API

Do not fabricate unsupported dimensions.

---

# 22. SHORTS VS VIDEOS

If reliable classification is possible from actual data, provide:

```text
All | Videos | Shorts
```

with meaningful comparisons.

Do not misclassify content based on title/URL alone when the API cannot reliably establish the type.

---

# 23. REVENUE

The OAuth configuration includes:

```text
https://www.googleapis.com/auth/yt-analytics-monetary.readonly
```

Use monetary analytics only when the connected channel/account and API response support it.

Show:

- estimated revenue
- revenue trend
- RPM/CPM where available
- revenue by video where available

For a non-monetized/ineligible channel, show a clean unavailable state instead of fake zeroes.

Revenue data must remain owner-only.

---

# 24. INSIGHTS

Add a deterministic `Insights` section calculated from real API data.

Examples:

- views increased/decreased compared with previous period
- subscriber growth trend
- top-performing video contribution
- strongest traffic source
- watch-time trend
- engagement changes

Do not introduce an AI API just for these basic insights.

Clearly distinguish Nothing-generated insights from official YouTube metrics.

---

# 25. CHANNEL HEALTH

Optionally add a transparent Nothing-generated channel health score based only on real data.

Possible inputs:

- views trend
- subscriber growth
- watch-time trend
- engagement
- upload consistency

Clearly label it:

> Nothing Channel Health — an application-generated analytical score, not an official YouTube metric.

Show the calculation/breakdown so the score is explainable.

If insufficient data exists, do not manufacture a score.

---

# 26. UPLOAD ACTIVITY

If enough historical data exists, add a contribution-style upload calendar showing:

- upload days
- upload count
- views associated with uploads where reliable

---

# 27. EXPORT

Allow exporting the selected analytics range as:

- CSV
- JSON

Never include OAuth credentials in exports.

---

# 28. CACHING / API QUOTA

YouTube APIs have quota limitations.

Do not fetch analytics on every React render.

Use sensible server-side caching and/or Supabase analytics snapshots.

Avoid duplicate requests.

Do not write high-frequency chart points to PostgreSQL every second.

Keep realtime downloader/upload progress on the existing progress mechanism.

---

# 29. PARTIAL FAILURE

Analytics must degrade gracefully.

If revenue fails but overview works:

```text
Overview ✓
Videos ✓
Traffic ✓
Revenue ⚠ unavailable
```

Do not blank the entire dashboard because one API section failed.

Use structured error responses per section.

---

# 30. ANALYTICS ERROR STATES

Support polished states for:

- not authenticated
- no YouTube channel
- analytics permission missing
- token expired/revoked
- API quota exceeded
- network failure
- no data
- non-monetized channel
- partial data

Provide actionable reconnect/refresh controls where appropriate.

---

# 31. VISUAL DESIGN

Use the existing Nothing visual identity.

You may add:

- animated KPI counters
- chart draw animations
- staggered card entrance
- smooth tab indicator
- hover elevation
- subtle gradients
- glass/blur effects
- skeleton loaders
- tooltip transitions
- polished empty states

But keep animations lightweight.

Respect:

```text
prefers-reduced-motion
```

Do not add huge animation libraries unless already present and genuinely useful.

---

# 32. RESPONSIVE

The Channel Analytics tab must work on:

- desktop
- laptop
- tablet
- mobile

No horizontal overflow.

Charts must resize correctly.

---

# 33. AUTHENTICATED BACKEND API

Create/use a reusable authentication dependency such as:

```text
get_current_user()
```

Every protected endpoint must validate the Supabase user.

Never trust a frontend-supplied `user_id`.

A user must not be able to request another user's:

- settings
- channels
- history
- analytics
- OAuth credentials

---

# 34. EXISTING UPLOADER / AUTOMATION

Preserve the existing uploader and automation pipeline.

The desired flow remains:

```text
monitor channel
→ detect new video
→ extract metadata
→ download
→ upload to YouTube
→ cleanup
→ save history
→ save logs
```

Move persistence to Supabase without changing behavior unnecessarily.

Refresh expired Google credentials securely.

If YouTube authorization is revoked:

> Your YouTube connection has expired. Reconnect Google to continue uploading.

---

# 35. JSON DATABASE MIGRATION

The old JSON database layer may contain:

```text
tokens.json
oauth_tokens.json
settings.json
channels.json
automation_logs.json
history.json
```

If these still exist in the current implementation, migrate their useful data to Supabase.

Migration must:

1. read
2. validate
3. map old user identity to Supabase user ID
4. upsert
5. verify
6. report failures

Do not silently attach data to the wrong user.

Do not delete old JSON files until migration has been verified.

---

# 36. ENVIRONMENT VARIABLES

Inspect the current `.env.example` and actual configuration usage first.

Remove obsolete database variables only if truly unused.

Use appropriate variables such as:

```text
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

Keep Google/YouTube variables only where still required by the chosen architecture.

Never commit real secrets.

---

# 37. TESTING STRATEGY — DO NOT FREEZE THE APP

Use targeted tests first.

### Extraction tests

Test parser/resource classification without downloading large files.

### Download tests

Use bounded/controlled downloads.

### Supabase tests

Use MCP/database verification where possible.

### OAuth tests

Use real configured OAuth flow.

### Analytics tests

Use the connected test channel/account and real API responses.

Only after targeted tests pass should you run broader tests.

Avoid long-running or huge-data tests.

---

# 38. FINAL REGRESSION CHECKLIST

Before declaring completion, verify:

```text
[ ] Normal YouTube video extracts correctly
[ ] YouTube Playable is rejected instead of becoming fake metadata
[ ] Invalid URLs show useful errors
[ ] Unsupported resources show useful errors
[ ] Metadata is never fabricated
[ ] Format list is trustworthy
[ ] Quality selection still works
[ ] Large format tests are bounded/skipped safely
[ ] Partial test files are deleted
[ ] Download cancellation works
[ ] Upload still works
[ ] Automation still works
[ ] Supabase is the persistent source of truth
[ ] RLS protects user data
[ ] Google OAuth works
[ ] YouTube permissions work
[ ] Token refresh works
[ ] Accounts page works
[ ] Channel Analytics tab works
[ ] Analytics use real API data
[ ] Revenue is hidden when unavailable
[ ] Partial analytics failures do not destroy the dashboard
[ ] Date ranges work
[ ] Charts work
[ ] Top videos work
[ ] Insights are data-derived
[ ] Mobile layout works
[ ] Reduced-motion preference works
[ ] No secrets are exposed
[ ] No duplicate workers/dev servers were created
[ ] No temporary test files remain
```

---

# 39. FINAL REPORT

At the end provide a concise report containing:

## Changed files

List files created/modified.

## Supabase changes

List:

- tables
- columns
- relationships
- indexes
- RLS policies
- migrations

## OAuth

Explain:

- Supabase Google provider usage
- required scopes
- token handling
- refresh behavior

## Extraction bug

Explain exactly why `/playables/` was being treated as a video and how it was fixed.

## Downloader testing

Report which format/quality tests passed, failed, or were safely skipped due to size.

## Analytics

Report which analytics sections are actually backed by real YouTube API data.

## Remaining limitations

Be honest. Do not mark a feature as PASS if it was only mocked or visually implemented.

---

# FINAL RULES

1. **The existing codebase is the source of truth.**
2. **Use Supabase MCP whenever it can perform the required database work.**
3. **Do not ask me to manually create database tables/policies if MCP can do it.**
4. **I will manually provide Google OAuth Client ID/Secret through Supabase.**
5. **Never expose secrets.**
6. **Never fabricate video metadata or analytics.**
7. **Never treat a YouTube hostname as proof that the URL is a downloadable video.**
8. **Never fully download enormous files just to test a format.**
9. **Always clean temporary test files.**
10. **Do not break existing downloader/uploader/automation functionality.**
11. **Implement incrementally to prevent browser/agent freezing.**
12. **Do not perform huge context dumps or unnecessary full-repository rewrites.**
13. **Prefer targeted validation before expensive tests.**
14. **Use real YouTube API data for analytics.**
15. **If a metric/API is unavailable, show an honest unavailable state.**
16. **Keep the UI premium, responsive, and consistent with Nothing.**
17. **Do not declare success until the regression checklist has been validated.**
