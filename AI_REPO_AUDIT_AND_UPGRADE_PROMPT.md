# UpDownVid / Nothing — Full Repository Audit, Bug Fix & Upgrade Prompt

## Mission

You are the senior engineer responsible for auditing and improving the entire **UpDownVid / Nothing** repository. Do not treat this as a narrow bug-fix task. Perform a complete production-readiness audit across the frontend, backend, authentication, OAuth, API contracts, deployment configuration, security, data persistence, upload/download flows, YouTube integration, error handling, performance, UX, accessibility, maintainability, and developer experience.

The repository must remain functional while improvements are made. Preserve existing intended features unless they are demonstrably broken, unsafe, obsolete, redundant, or incompatible with the production architecture.

## Non-negotiable rules

1. **Read the entire repository before making architectural decisions.** Inspect source files, configuration, package manifests, deployment files, environment examples, API routes, services, components, hooks, utilities, database code, scripts, and documentation. Do not infer behavior from filenames alone.
2. Build a dependency and execution map first: frontend entry points, backend entry points, API routing/proxying, authentication flow, OAuth callbacks, session flow, database/storage flow, upload/download pipeline, and deployment topology.
3. Identify duplicate or competing implementations. The current project contains both a Supabase Google OAuth flow and a legacy/direct Google OAuth flow. Determine which is actually used by each UI path and either unify them safely or isolate/document them so they cannot conflict.
4. Never silently replace working functionality with a speculative rewrite. Prefer focused, testable improvements.
5. Never hardcode production secrets, tokens, API keys, credentials, private URLs, or user data.
6. Treat every environment-dependent URL as environment configuration. Localhost defaults are acceptable for local development but must never accidentally become production redirect targets.
7. Validate every redirect and callback URL for local, preview, and production environments.
8. Preserve backwards compatibility where practical, but remove dead code only after proving it is unused or superseded.
9. Do not claim a fix is complete without checking all call sites and related configuration.
10. Run/build/lint/test what is available. If a check cannot be run because the environment lacks a dependency or external service, document exactly why and provide the appropriate validation command.

## Known issue to explicitly investigate

A production deployment at `https://updownvide.vercel.app` has redirected the user back to a localhost URL after login. Investigate the entire redirect chain, not just the first suspicious line.

Known repository behavior that must be verified:

- Frontend Supabase OAuth uses a redirect based on `window.location.origin + '/accounts'`.
- Backend configuration currently has localhost fallbacks for `FRONTEND_URL`, `BACKEND_URL`, `CORS_ORIGINS`, and `GOOGLE_REDIRECT_URI`.
- The backend has a legacy Google OAuth callback that redirects using `FRONTEND_URL`.
- The backend also has Supabase OAuth sync/callback endpoints.
- Determine whether Supabase's Site URL / Redirect URLs, Google Cloud OAuth Authorized Redirect URIs, Vercel environment variables, backend deployment variables, or legacy routes can cause the production-to-localhost redirect.
- Verify whether Vercel is hosting only the Next.js frontend or whether API routes/backend services are also expected to be available there.
- Trace every authentication entry point from UI click through provider authorization, callback, token exchange, session creation, frontend navigation, and error handling.

## Audit scope

### 1. Repository architecture

- Map the complete directory structure.
- Identify frontend framework/version and backend framework/version.
- Identify all runtime entry points.
- Identify all build scripts and deployment scripts.
- Identify unused, duplicated, obsolete, or contradictory modules.
- Identify architecture boundaries that are currently unclear.
- Document which parts run on Vercel, which require a persistent server/process, and which depend on filesystem persistence.
- Check whether any code assumes a writable persistent filesystem, long-running processes, background workers, SSE/WebSockets, large request bodies, or local binaries in a serverless environment.

### 2. Frontend audit

Inspect every page, component, hook, utility, API client, auth helper, and state-management path.

Check for:

- React/Next.js anti-patterns.
- Client/server component mistakes if applicable.
- Incorrect use of browser-only APIs during server rendering.
- Hydration mismatches.
- Race conditions in auth/session initialization.
- Duplicate API calls.
- Missing loading/error/empty states.
- Stale state after login/logout.
- Navigation bugs.
- Broken deep links.
- Incorrect environment variable usage.
- Hardcoded localhost URLs.
- Incorrect API base URL selection.
- CORS and credentials behavior.
- Cookie/session behavior across domains.
- XSS risks from rendered external metadata.
- Unsafe HTML injection.
- Accessibility problems.
- Mobile/responsive issues.
- Performance bottlenecks and unnecessary re-renders.
- Image optimization problems.
- Missing `alt`, labels, keyboard handling, focus management, and semantic structure.
- Error messages that expose internal details.
- Dead UI controls or features whose backend is missing.

### 3. Backend/API audit

Inspect all FastAPI routes, middleware, services, database modules, schemas, utilities, background tasks, and error handling.

Check for:

- Incorrect route prefixes.
- Frontend/backend URL mismatches.
- CORS configuration.
- Credentialed cross-origin requests.
- Session cookie configuration.
- Secure/HttpOnly/SameSite settings.
- Trusting forwarded headers incorrectly.
- Production DEBUG mode.
- Weak/default secrets.
- Unhandled exceptions.
- Leaking exception strings to clients.
- Missing request validation.
- Missing response validation.
- SSRF risks where arbitrary URLs are accepted.
- Command injection risks around yt-dlp/ffmpeg/aria2c or shell commands.
- Path traversal and unsafe filenames.
- Temporary-file cleanup failures.
- Resource exhaustion.
- Missing request size limits.
- Missing timeouts.
- Blocking operations inside async routes.
- Background task lifecycle problems.
- Long-running jobs incompatible with serverless execution.
- SSE/WebSocket assumptions incompatible with deployment platform.
- Race conditions in JSON/file-based persistence.
- Concurrent writes and corruption risks.
- Missing locking/atomic writes.
- Sensitive data stored in logs.

### 4. Authentication and OAuth — deep audit

Treat authentication as a first-class subsystem.

Trace and document these flows independently:

1. Supabase Google OAuth login.
2. Supabase session recovery on page load.
3. Supabase-to-backend token synchronization.
4. Legacy/direct Google OAuth login.
5. Legacy Google OAuth callback.
6. Logout.
7. Session expiration.
8. Refresh token behavior.
9. YouTube provider token retrieval.

For each flow identify:

- Initiating URL.
- Provider authorization URL.
- `redirect_uri`.
- Callback endpoint.
- Token exchange location.
- Session creation.
- Final browser redirect.
- Environment variables involved.
- Cookies involved.
- Production/preview/local differences.

Specifically verify:

- `FRONTEND_URL`.
- `BACKEND_URL`.
- `GOOGLE_REDIRECT_URI`.
- `CORS_ORIGINS`.
- Supabase URL configuration.
- Supabase allowed redirect URLs.
- Google Cloud OAuth authorized redirect URIs.
- Vercel environment variables for Development/Preview/Production.
- Any hardcoded localhost values anywhere in the repository.
- Any redirects constructed from untrusted query parameters.
- Open redirect vulnerabilities.
- Whether JWT verification is actually cryptographic. If the code currently decodes Supabase JWTs with signature verification disabled, flag this as a security issue and replace it with proper verification appropriate to the deployed Supabase configuration.
- Whether provider access/refresh tokens are exposed unnecessarily to the browser.
- Whether refresh tokens are stored in JSON files, sessions, or database records without appropriate protection.

The desired production behavior is:

`https://updownvide.vercel.app` → Google/Supabase → production callback → `https://updownvide.vercel.app/accounts`

and local development should remain isolated, e.g. localhost → localhost.

### 5. Environment/configuration audit

Search the complete repository for:

- `localhost`
- `127.0.0.1`
- `0.0.0.0`
- `FRONTEND_URL`
- `BACKEND_URL`
- `GOOGLE_REDIRECT_URI`
- `NEXT_PUBLIC_*`
- `SUPABASE_*`
- `GOOGLE_*`
- API base URLs
- Vercel-specific configuration
- deployment-specific assumptions

Classify each occurrence as:

- safe local default,
- production-safe configuration,
- accidental production dependency,
- obsolete/dead configuration,
- or security risk.

Create a clean configuration strategy with explicit local/preview/production behavior.

### 6. Download pipeline audit

Inspect the entire video download flow, including metadata extraction, format selection, yt-dlp invocation, ffmpeg merging, cookies/authentication, progress reporting, temporary storage, cancellation, cleanup, and error propagation.

Check:

- yt-dlp command construction.
- Shell escaping.
- User-controlled URLs/options.
- Cookies handling.
- Format availability.
- Requested quality vs actual quality.
- Audio/video merging.
- FFmpeg availability.
- Progress parsing.
- Retry behavior.
- Timeout behavior.
- Temporary directory cleanup.
- Concurrent downloads.
- Disk-space handling.
- Large-file behavior.
- Serverless compatibility.
- Abuse/rate limiting.

### 7. YouTube upload pipeline audit

Inspect the entire upload path from selected file/URL through processing, metadata, OAuth authorization, upload initiation, resumable chunks, progress, retries, completion, and cleanup.

Check:

- YouTube API scopes.
- OAuth token lifecycle.
- Resumable upload support.
- Large files.
- Retry/backoff.
- Quota failures.
- Duplicate uploads.
- Metadata validation.
- Privacy/status/category defaults.
- Error recovery.
- Cancellation.
- Progress accuracy.
- Serverless execution constraints.
- Whether download → save → upload can realistically run on the deployed platform.

Do not propose a Vercel-only architecture for workloads that require long-running processes, large local files, persistent storage, or background workers. If a split architecture is required, clearly define frontend/API/worker/storage responsibilities.

### 8. Database and persistence audit

Inspect JSON DB usage, Supabase usage, filesystem storage, sessions, caches, and any migration/schema assumptions.

Check:

- Atomicity.
- Concurrent writes.
- Data loss risk.
- Corruption recovery.
- Schema consistency.
- Missing indexes.
- Duplicate records.
- Token storage security.
- Cleanup/retention.
- Environment separation.
- Whether local filesystem persistence is incorrectly assumed in production.

### 9. Security audit

Perform a practical application-security review covering at minimum:

- Authentication bypass.
- Authorization bypass.
- Broken access control.
- CSRF.
- XSS.
- SSRF.
- Open redirects.
- Command injection.
- Path traversal.
- Unsafe deserialization.
- Secret exposure.
- Token leakage.
- Weak JWT verification.
- Session fixation.
- Cookie flags.
- CORS abuse.
- Rate limiting.
- Resource exhaustion.
- Log leakage.
- Dependency vulnerabilities.
- Unsafe third-party URL handling.
- YouTube/API abuse.

Rank every finding by severity: **Critical / High / Medium / Low / Informational**.

### 10. Dependency audit

Inspect all package manifests and lockfiles.

Identify:

- outdated dependencies,
- duplicate dependencies,
- unnecessary dependencies,
- deprecated packages/APIs,
- incompatible version combinations,
- missing lockfile consistency,
- vulnerable dependencies where detectable,
- packages that significantly increase bundle size or cold-start time.

Do not blindly upgrade everything. Recommend compatible upgrades and identify breaking changes.

### 11. Error handling and observability

Check:

- frontend error boundaries,
- API error schemas,
- HTTP status codes,
- logging levels,
- structured logging,
- correlation/request IDs,
- sensitive-data redaction,
- actionable user-facing errors,
- retryable vs permanent failures,
- monitoring/health endpoints.

### 12. Performance

Identify high-impact performance issues in:

- frontend bundle size,
- rendering,
- API calls,
- metadata extraction,
- download pipeline,
- upload pipeline,
- database access,
- image handling,
- polling/SSE,
- authentication initialization.

Prioritize changes by real-world impact rather than micro-optimizations.

### 13. Testing

Determine the current testing situation.

Where tests are missing, recommend and, where practical, add tests for:

- auth redirect behavior,
- environment URL selection,
- OAuth callback behavior,
- API validation,
- download command construction,
- upload failure/retry logic,
- session behavior,
- security-sensitive utilities,
- critical frontend components.

Include exact commands to run tests/lint/build/type checks.

### 14. Deployment audit

Audit Vercel configuration and any backend deployment configuration.

Determine whether the current architecture is actually compatible with the target platform.

Explicitly inspect:

- build output,
- framework detection,
- root directory,
- rewrites/redirects,
- serverless functions,
- API routes,
- environment variables,
- runtime versions,
- function duration limits,
- request/response limits,
- filesystem assumptions,
- background processing,
- SSE support,
- large uploads/downloads,
- binary dependencies such as FFmpeg/yt-dlp/aria2c.

If the current architecture cannot reliably support a feature on Vercel, do not hide that fact. Recommend a realistic split architecture such as Vercel frontend + persistent backend/worker + object storage, if appropriate.

### 15. UX/product audit

Review the actual user journey:

`Home → URL input → metadata → quality selection → download/upload → authentication → YouTube connection → progress → completion/error`

Find friction, dead ends, confusing states, inconsistent terminology, missing confirmations, broken mobile behavior, and places where the user can lose work.

Recommend improvements that fit the existing product rather than turning it into an unrelated redesign.

### 16. Documentation / developer experience

Check README, environment examples, setup instructions, scripts, comments, and architecture documentation.

Documentation should explain:

- local setup,
- environment variables,
- Supabase setup,
- Google Cloud OAuth setup,
- production redirect URLs,
- backend deployment,
- Vercel deployment,
- worker/storage requirements,
- testing,
- troubleshooting.

Do not document secrets or private credentials.

## Required audit output

Before changing code, produce an internal findings matrix with:

| ID | Severity | Area | File(s) | Problem | Root Cause | Impact | Recommended Fix | Priority | Verification |
|---|---|---|---|---|---|---|---|---|---|

Then implement the highest-confidence, highest-impact fixes that can be safely made without external credentials or infrastructure access.

For changes that require dashboard configuration, provide exact configuration instructions in the repository documentation rather than pretending the code alone can solve them.

## Production configuration requirements

The final architecture must support separate environments:

### Local

- Frontend localhost URL.
- Backend localhost URL.
- Local OAuth callback.
- Local CORS origins.

### Preview

- Preview frontend URL.
- Preview backend URL if applicable.
- Explicit preview OAuth redirect handling only if the OAuth provider configuration supports it safely.

### Production

- `https://updownvide.vercel.app` as the frontend origin.
- No production OAuth flow may fall back to localhost.
- Production CORS must contain only the intended production origin(s).
- Production session cookies must use secure settings.
- Production secrets must come from environment variables.
- Production DEBUG must be disabled.
- Production redirect URIs must exactly match provider configuration.

## Refactoring priorities

Use this order unless repository evidence justifies another order:

1. Security vulnerabilities.
2. Production authentication/OAuth correctness.
3. Data-loss/session/token risks.
4. Deployment/runtime incompatibilities.
5. Broken core product flows.
6. API reliability and validation.
7. Download/upload reliability.
8. Testing and observability.
9. Performance.
10. UX/accessibility.
11. Cleanup and maintainability.
12. Nice-to-have feature upgrades.

## Upgrade recommendations

After fixing defects, identify high-value upgrades that fit the product. Consider:

- stronger typed API contracts,
- centralized API client,
- centralized environment configuration,
- unified auth architecture,
- robust job queue for long-running media operations,
- object storage for temporary media,
- resumable uploads,
- proper background workers,
- database-backed job state,
- rate limiting,
- structured logs,
- health/readiness endpoints,
- automated CI checks,
- end-to-end auth tests,
- better error boundaries,
- improved accessibility,
- responsive upload/download UX,
- cancellation and retry controls,
- secure token handling,
- better cleanup and retention policies.

Only recommend upgrades that solve an identified need or materially improve reliability, security, maintainability, or user experience.

## Implementation requirements

When modifying code:

- Keep changes modular.
- Avoid giant rewrites.
- Reuse existing utilities where appropriate.
- Remove duplicated logic only when behavior remains covered.
- Add comments only where the reasoning is non-obvious.
- Use clear names.
- Preserve API compatibility where feasible.
- Add/update tests alongside behavior changes.
- Update `.env.example` and documentation when configuration changes.
- Never commit real `.env` files or secrets.

## Final verification

After implementation:

1. Search the complete repository again for accidental production `localhost` dependencies.
2. Verify every OAuth redirect and callback path.
3. Verify production environment variables and their names.
4. Run lint/typecheck/tests/build where available.
5. Verify no secrets were introduced.
6. Verify no dead references were created.
7. Verify frontend/backend API paths agree.
8. Verify error handling for failed OAuth, expired sessions, failed downloads, failed uploads, and provider failures.
9. Verify the deployment architecture against the actual runtime limitations.
10. Update documentation with all required production configuration.

## Final report to produce in the coding agent's own output

Do NOT merely say “done.” Report:

- Executive summary.
- Critical/high/medium/low findings.
- Exact files changed.
- What was fixed and why.
- Authentication/OAuth flow before and after.
- Production configuration required.
- Deployment limitations discovered.
- Tests/checks executed and results.
- Remaining issues that require external dashboard/infrastructure changes.
- Recommended next upgrades, ordered by impact.

The goal is a **secure, reliable, production-ready UpDownVid application**, not just a patch for the currently observed localhost redirect bug.
