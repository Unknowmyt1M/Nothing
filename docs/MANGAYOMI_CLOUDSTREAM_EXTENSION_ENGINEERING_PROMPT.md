# MANGAYOMI + CLOUDSTREAM MULTI-SITE EXTENSION ENGINEERING TASK

You are an autonomous senior extension engineer, web reverse-engineering researcher, Kotlin/JavaScript developer, scraper/parser engineer, video-extraction engineer, QA engineer, and technical documentation researcher.

Your task is to research, design, implement, test, debug, and finalize TWO COMPLETE EXTENSION IMPLEMENTATIONS for EACH of these three anime/donghua websites:

1. AnimeXin — https://animexin.dev/
2. Lucifer Donghua — https://luciferdonghua.in/
3. Anime Cube — https://animecube.live/

TARGET PLATFORMS:
- Mangayomi (current Windows-compatible extension architecture)
- CloudStream (current plugin/extension architecture)

That means the final result should contain six site adapters total:
- AnimeXin for Mangayomi
- Lucifer Donghua for Mangayomi
- AnimeCube for Mangayomi
- AnimeXin for CloudStream
- Lucifer Donghua for CloudStream
- AnimeCube for CloudStream

IMPORTANT: Do not assume that code can simply be shared between the two platforms. They have different extension/plugin APIs, runtimes, data models, build systems, and video extraction conventions. Share only genuinely platform-agnostic research/parsing ideas where appropriate.

---

# 0. EXISTING LOCAL PROJECTS — MANDATORY REFERENCE MATERIAL

Before implementing anything, inspect BOTH of these existing local projects:

## Project A — previous similar Donghua project
D:\Projects\Websites\Donghua

OpenCode worked on this project a few days ago. It may contain useful discoveries, parsers, selectors, player extraction logic, URL patterns, site-specific workarounds, debugging history, or reusable architectural ideas.

Treat it as an important research/reference source, but NEVER trust it blindly.

You MUST:
- inspect the complete project structure
- read relevant source files
- inspect scraping/parsing logic
- inspect video/player extraction logic
- inspect network/API assumptions
- inspect known bugs and workarounds
- inspect configuration and dependencies
- identify which target sites or similar sites it already handles
- identify what was experimentally successful vs merely assumed
- reuse good ideas where appropriate
- improve weak implementations
- reject obsolete or fragile approaches
- independently verify important findings against the current target websites

## Project B — existing CloudStream extension project
D:\Projects\Extensions\Uncensored

This is an existing CloudStream extension project and MUST be studied before creating the CloudStream implementations.

Inspect:
- project structure
- Gradle setup
- Kotlin conventions
- plugin metadata
- provider implementations
- extractor implementations
- HTTP helpers
- Jsoup/parsing patterns
- video extraction
- HLS handling
- referer/header handling
- error handling
- naming conventions
- build/test workflow
- reusable utilities
- known limitations

Again: DO NOT trust it blindly. Verify everything important against the current CloudStream source/API/documentation and current target websites.

Create a short comparison documenting:
- what was learned from D:\Projects\Websites\Donghua
- what was learned from D:\Projects\Extensions\Uncensored
- what was reused
- what was changed
- what was rejected and why

Do NOT modify either reference project unless explicitly required by me.

---

# 1. RESEARCH FIRST — DO NOT CODE IMMEDIATELY

Before writing production code, perform deep research.

You MUST research the CURRENT versions of both ecosystems.

## Mangayomi
Use the official Mangayomi repository and current official documentation/source.

Study:
- extension development
- JavaScript extensions
- Dart extensions if relevant
- source metadata
- source lifecycle
- search
- popular/latest
- pagination
- details
- episodes
- getVideoList
- video objects
- headers
- cookies
- referer/origin handling
- runtime limitations
- extension metadata/indexing
- testing/build workflow
- current repository conventions

Do not rely on archived extension repositories as the primary source. The old public mangayomi-extensions repository is archived; use it only as historical/reference material and prioritize the current Mangayomi repository and current source implementation.

## CloudStream
Use the official/current CloudStream repository and current extension repository/documentation.

Study:
- provider/plugin architecture
- current Kotlin APIs
- `MainAPI`
- search
- load
- loadLinks
- HomePageResponse
- LoadResponse
- Episode
- ExtractorLink / current replacement APIs
- extractor architecture
- `newExtractorLink`
- HLS/DASH handling
- referer
- headers
- cookies
- Jsoup
- NiceHttp/HTTP utilities
- Gradle plugin
- metadata
- plugin packaging
- current build/test workflow
- current API compatibility

Do NOT blindly follow old CloudStream tutorials because the API evolves.

---

# 2. OFFICIAL DOCUMENTATION RULE

Whenever you use a framework, API, library, runtime, build tool, or extension feature:

FIRST read its official/current documentation or source whenever available.

Examples:
- Mangayomi official repository/docs
- CloudStream official repository/docs
- CloudStream extension repository
- Kotlin documentation
- Gradle/plugin documentation
- Jsoup documentation
- HTTP library documentation
- any video/extractor library documentation

Community sources are supplementary, not authoritative.

If documentation conflicts with current source code, investigate the discrepancy and follow the current working implementation.

---

# 3. DEEP WEB RESEARCH

Research extensively across:
- Google
- GitHub
- GitHub code
- GitHub Issues
- GitHub Pull Requests
- Reddit
- official documentation
- developer forums
- Stack Overflow where relevant
- existing extension repositories
- archived extensions
- source code
- technical discussions

Search exact domains and implementation clues.

Useful queries include:
- "animexin.dev API"
- "animexin.dev wordpress"
- "animexin.dev player"
- "animexin.dev iframe"
- "animexin.dev m3u8"
- "luciferdonghua API"
- "luciferdonghua wordpress"
- "luciferdonghua player"
- "luciferdonghua iframe"
- "luciferdonghua m3u8"
- "animecube.live API"
- "animecube.live player"
- "animecube.live iframe"
- "animecube.live m3u8"
- "site:github.com Mangayomi AnimeXin"
- "site:github.com Mangayomi LuciferDonghua"
- "site:github.com Mangayomi AnimeCube"
- "site:github.com CloudStream AnimeXin"
- "site:github.com CloudStream LuciferDonghua"
- "site:github.com CloudStream AnimeCube"

Generate better queries dynamically as new technical clues are discovered.

---

# 4. RESEARCH EACH TARGET SITE INDEPENDENTLY

For EACH site determine:

- CMS/framework
- WordPress or not
- theme
- plugins if discoverable
- frontend framework
- REST API
- AJAX endpoints
- GraphQL if any
- HTML structure
- search mechanism
- popular/latest/category pages
- genre pages
- detail pages
- episode pages
- pagination
- query parameters
- embedded JSON
- data attributes
- player architecture
- iframe providers
- external video hosts
- HLS/DASH
- direct MP4
- cookies
- headers
- referer requirements
- origin requirements
- anti-hotlinking
- Cloudflare
- anti-bot
- anti-adblock
- redirects
- token generation
- signed URLs
- obfuscation
- JavaScript-generated URLs

Do not guess. Verify.

---

# 5. WORDPRESS HYPOTHESIS

AnimeXin and Lucifer Donghua MAY be WordPress-based.

This is ONLY a hypothesis.

Verify using evidence such as:
- /wp-content/
- /wp-includes/
- wp-json
- WordPress REST API
- theme identifiers
- plugin identifiers
- generated HTML
- AJAX endpoints
- WordPress metadata

If WordPress APIs provide reliable structured data, determine whether they are preferable to HTML scraping.

If not, implement robust HTML parsing.

---

# 6. VIDEO EXTRACTION — HIGHEST PRIORITY

For every website, determine the complete extraction chain:

anime
→ detail
→ episode
→ player
→ iframe/provider
→ API/request
→ video source
→ quality/server/subtitles

Implement the most reliable extraction strategy available for EACH platform.

Do not merely return an iframe URL if a playable source can be extracted.

Investigate:
- m3u8
- MP4
- DASH
- JSON player configs
- `sources`
- `file`
- `playlist`
- manifests
- API endpoints
- encoded URLs
- token parameters
- signed URLs
- referer
- origin
- user-agent requirements
- subtitle tracks
- multiple servers
- multiple qualities

For CloudStream, follow the CURRENT extractor/provider API and use the modern link APIs rather than deprecated APIs.

For Mangayomi, follow the CURRENT source/video model and runtime.

---

# 7. EXISTING EXTENSION DISCOVERY

Before implementing each site, search whether a working or historical extension already exists for that exact site.

Inspect:
- code
- commits
- issues
- PRs
- forks
- bugs
- video extraction
- architecture
- update history

Existing implementations may be used as references where licensing permits.

Do not assume they are correct or current.

If broken, determine why and document the improvement.

---

# 8. FUNCTIONAL REQUIREMENTS

For each site/platform combination implement as much as the platform currently supports:

Discovery:
- search
- popular
- latest
- pagination
- genres/categories
- filters where supported

Details:
- title
- alternative titles
- poster
- description
- genres
- status
- type
- year/date
- rating where available
- studio/author where available

Episodes:
- episode number
- title
- URL
- date
- season
- correct ordering
- specials
- OVAs
- movies where supported

Playback:
- video URL
- quality
- server
- subtitles
- headers
- referer
- origin
- HLS
- MP4
- DASH where supported

---

# 9. EDGE CASES

Actively handle and test:

- empty results
- invalid search
- missing poster
- missing description
- missing genres
- malformed HTML
- missing episode numbers
- decimal episodes such as 12.5
- specials
- OVAs
- movies
- multi-season anime
- duplicate episodes
- pagination ending
- pagination gaps
- changed URL structures
- redirects
- 403
- 404
- 429
- 5xx
- timeout
- malformed JSON
- unavailable player
- dead server
- multiple servers
- missing quality
- duplicate qualities
- relative URLs
- protocol-relative URLs
- URL encoding
- signed URLs
- expired tokens
- referer requirements
- origin requirements
- Cloudflare
- anti-adblock
- JavaScript-generated content
- nested iframes
- external hosts
- HLS
- MP4
- subtitles
- domain changes

Fail gracefully instead of crashing.

---

# 10. ROBUSTNESS

Avoid:
- giant page-wide regexes
- fragile CSS classes
- visual-layout-dependent selectors
- hardcoded IDs
- hardcoded temporary URLs
- hardcoded tokens
- unnecessary sleeps
- arbitrary delays
- hardcoded episode counts

Prefer:
- stable attributes
- semantic selectors
- APIs
- structured JSON
- URL patterns
- defensive parsing
- validation
- fallbacks
- multiple extraction strategies
- sensible retries/timeouts

---

# 11. PLATFORM-SPECIFIC ARCHITECTURE

Keep Mangayomi and CloudStream implementations separate.

Do NOT create one abstraction that obscures platform-specific behavior.

Use shared research or pure parsing utilities only when they genuinely reduce duplication without harming maintainability.

Recommended conceptual structure:

extensions/
├── mangayomi/
│   ├── animexin/
│   ├── luciferdonghua/
│   └── animecube/
│
├── cloudstream/
│   ├── animexin/
│   ├── luciferdonghua/
│   └── animecube/
│
├── docs/
│   ├── research/
│   ├── architecture/
│   ├── testing/
│   └── compatibility/
│
└── tools/

BUT: adapt the final structure to the actual repository/build conventions of each ecosystem. Do not invent a layout that breaks the official build systems.

---

# 12. CLOUDSTREAM-SPECIFIC REQUIREMENTS

For CloudStream:

- follow the current official extension repository structure
- use Kotlin
- use the current Gradle plugin
- use current CloudStream APIs
- use current provider classes
- use modern extractor link APIs
- avoid deprecated APIs
- correctly set quality
- correctly identify HLS/DASH
- preserve referer and headers where required
- use extractors when an external provider requires reusable extraction logic
- keep provider-specific extraction isolated
- validate plugin metadata
- build the plugin using the current CloudStream build workflow

Study the existing project:
D:\Projects\Extensions\Uncensored

Use it as a practical local reference, but validate every important implementation against current upstream CloudStream source.

---

# 13. MANGAYOMI-SPECIFIC REQUIREMENTS

For Mangayomi:

- follow the current official repository/source
- determine whether JS or Dart is appropriate for each source
- follow current extension metadata conventions
- implement search/popular/latest/details/episodes/video extraction as supported
- respect runtime limitations
- correctly construct video objects
- handle headers/referer/cookies correctly
- validate source metadata
- use current testing/build workflow

Do not blindly rely on the archived old mangayomi-extensions repository.

---

# 14. TESTING

Do NOT consider the task complete because code compiles.

For every site/platform combination test:

Search:
- common title
- uncommon title
- no results

Browse:
- popular
- latest
- pagination

Details:
- ongoing
- completed
- movie
- multi-season

Episodes:
- first
- middle
- latest
- special if available

Video:
- every available server
- multiple qualities
- HLS
- direct video
- subtitles if available

Failure:
- invalid URL
- missing episode
- unavailable player
- HTTP errors
- malformed response

Record real results.

---

# 15. BUILD / LINT / VALIDATION

For BOTH ecosystems run their actual current validation workflow.

Mangayomi:
- formatting
- linting/type checks if applicable
- extension validation
- metadata/index validation
- build/test scripts

CloudStream:
- Gradle build
- Kotlin compilation
- lint/static checks where applicable
- plugin validation
- metadata validation
- packaging

Fix errors rather than merely reporting them.

---

# 16. PERFORMANCE

These extensions may run on low-end devices.

Avoid:
- unnecessary requests
- duplicate requests
- repeated parsing
- infinite retries
- expensive browser automation when HTTP/API parsing works
- arbitrary delays

Prefer lightweight HTTP and HTML/JSON parsing whenever possible.

---

# 17. SECURITY / PRIVACY / BOUNDARIES

Never hardcode:
- personal credentials
- private API keys
- private cookies
- session secrets

Do not attempt account takeover, credential theft, destructive actions, or unauthorized access.

Treat external HTML/JSON as untrusted input.

Validate URLs before returning them.

For anti-bot/anti-adblock behavior, only use technically appropriate handling compatible with the normal publicly accessible browsing flow and the platform runtime; do not bypass authentication or private access controls.

---

# 18. DOCUMENTATION

Create research documentation for each target site and each platform where behavior differs.

Document:
- site architecture
- CMS
- search
- pagination
- detail parsing
- episode parsing
- player architecture
- extraction chain
- APIs
- selectors
- headers
- cookies
- anti-bot behavior
- fallback strategies
- known limitations

Also document the local reference-project analysis:

### D:\Projects\Websites\Donghua
- useful discoveries
- reusable logic
- obsolete logic
- bugs/workarounds
- what was independently verified

### D:\Projects\Extensions\Uncensored
- useful CloudStream patterns
- reusable utilities
- obsolete/deprecated patterns
- build setup
- bugs/workarounds
- what was independently verified

---

# 19. RESEARCH EVIDENCE

Do not fabricate sources.

For important technical conclusions provide evidence/links to:
- official Mangayomi source/docs
- official CloudStream source/docs
- current extension repositories
- relevant GitHub issues/PRs
- relevant Reddit discussions
- relevant technical pages
- target-site observations

Distinguish clearly between:
- verified fact
- strong inference
- unverified hypothesis

---

# 20. AUTONOMOUS EXECUTION

Work autonomously.

Do not repeatedly ask:
- "Should I continue?"
- "Which approach should I use?"
- "Do you want me to test it?"

Instead:
1. research
2. inspect local projects
3. inspect upstream source/docs
4. decide
5. implement
6. test
7. debug
8. improve
9. validate
10. document

Ask me only when a genuinely unavoidable external decision, credential, or missing input is required.

---

# 21. DO NOT STOP AT FIRST WORKING VERSION

After the first successful implementation:

1. review it
2. compare with high-quality current extensions
3. compare with local reference projects
4. identify fragile logic
5. improve selectors
6. improve extraction
7. improve fallbacks
8. improve error handling
9. improve performance
10. rerun tests
11. validate again

Think like a long-term open-source maintainer, not a code generator.

---

# 22. FINAL DELIVERABLE

At the end provide:

## A. Final repository tree

## B. Six implementations
- AnimeXin / Mangayomi
- Lucifer Donghua / Mangayomi
- AnimeCube / Mangayomi
- AnimeXin / CloudStream
- Lucifer Donghua / CloudStream
- AnimeCube / CloudStream

## C. Feature matrix
For each implementation show:
- search
- popular
- latest
- details
- episodes
- pagination
- genres/filters
- video extraction
- servers
- qualities
- subtitles
- HLS
- MP4
- DASH

## D. Technical research findings

## E. Exact video extraction flow for every site

## F. Local reference-project analysis
Clearly explain what was learned/reused/rejected from both local projects.

## G. Known limitations

## H. Real test results

## I. Build/validation results

## J. Sources actually used

---

# 23. ABSOLUTE RULES

DO NOT fabricate successful tests.

DO NOT claim an API exists unless verified.

DO NOT claim a site is WordPress unless verified.

DO NOT claim video extraction works unless an actual playable source/link was successfully obtained and validated.

DO NOT blindly trust either local reference project.

DO NOT blindly trust old extension repositories.

DO NOT blindly trust old tutorials.

CURRENT UPSTREAM SOURCE + OFFICIAL DOCUMENTATION + REAL TESTING > OLD CODE, BLOG POSTS, MEMORY, OR ASSUMPTIONS.

When uncertain, investigate further.

START WITH RESEARCH AND LOCAL PROJECT ANALYSIS.

DO NOT START BY WRITING PRODUCTION CODE.
