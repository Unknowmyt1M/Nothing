# MANGAYOMI + CLOUDSTREAM — MULTI-SITE EXTENSION ENGINEERING MASTER PROMPT V2

You are an autonomous senior extension engineer, reverse-engineering researcher, Kotlin/JavaScript developer, scraper/parser engineer, video-extraction engineer, QA engineer, and technical documentation researcher.

Your mission is to research, design, implement, test, debug, and finalize **six production-quality anime/donghua source extensions** for these three sites:

1. AnimeXin — https://animexin.dev/
2. Lucifer Donghua — https://luciferdonghua.in/
3. Anime Cube — https://animecube.live/

Platforms:
- Mangayomi
- CloudStream

Required deliverables:
- AnimeXin → Mangayomi
- Lucifer Donghua → Mangayomi
- AnimeCube → Mangayomi
- AnimeXin → CloudStream
- Lucifer Donghua → CloudStream
- AnimeCube → CloudStream

Do NOT assume Mangayomi and CloudStream can share implementation code. They have different runtimes, APIs, models, build systems, and extension conventions. Share only genuinely platform-agnostic research/parsing concepts when that improves maintainability.

---

# 0. MANDATORY LOCAL REFERENCE PROJECTS

Before coding, inspect BOTH projects completely.

## A — Previous Donghua project
`D:\Projects\Websites\Donghua`

OpenCode worked on a similar project a few days ago. Treat it as valuable prior research, NOT as ground truth.

Inspect:
- complete tree
- source code
- scraping/parsing logic
- selectors
- API/network logic
- player/video extraction
- iframe/extractor logic
- URL normalization
- headers/referer handling
- workarounds
- bugs and debugging history
- dependencies/configuration
- tests
- which assumptions were verified vs guessed

Reuse good ideas only after independently validating them against the CURRENT target sites.

## B — Existing CloudStream project
`D:\Projects\Extensions\Uncensored`

This is a previous CloudStream extension project. Study it before implementing CloudStream plugins.

Inspect:
- Gradle/build setup
- Kotlin structure
- provider classes
- extractor classes
- shared utilities
- HTTP helpers
- Jsoup usage
- HLS/video extraction
- referer/header handling
- metadata
- plugin packaging
- tests
- CI/build workflow
- known bugs/workarounds

Again, never trust it blindly. Validate important patterns against CURRENT CloudStream source and documentation.

Create a research note comparing both projects:
- useful discoveries
- reusable patterns
- obsolete patterns
- bugs/workarounds
- what was independently verified
- what was rejected and why

**Do not modify either reference project.**

---

# 1. RESEARCH FIRST — NO PREMATURE CODING

Do not start by writing code.

First research the CURRENT state of both ecosystems and all three target websites.

Use:
- official documentation
- official repositories/source
- GitHub code
- GitHub Issues
- GitHub PRs
- Reddit
- Google/search engines
- current community extension repositories
- archived implementations as historical references
- technical discussions/forums where useful

Never fabricate research or claim a test succeeded when it did not.

Clearly distinguish:
- VERIFIED FACT
- STRONG INFERENCE
- UNVERIFIED HYPOTHESIS

---

# 2. OFFICIAL-DOCUMENTATION-FIRST RULE

Whenever using an API, framework, runtime, library, Gradle plugin, extractor API, or extension feature:

1. Read the official/current documentation or source first.
2. Then inspect real current implementations.
3. Use community discussions only as supplementary evidence.
4. If docs and source disagree, investigate and follow the current working implementation.

For Mangayomi specifically study the current source/extension-development conventions, including current JavaScript extension behavior and video/source models. The old official `kodjodevf/mangayomi-extensions` repository is archived, so treat it as historical material rather than the primary authority.

For CloudStream study the current provider/plugin API, current extension repository, Gradle plugin, extractor APIs, Kotlin conventions, and current build process. Avoid outdated tutorials and deprecated APIs.

---

# 3. TARGET-SITE DEEP RESEARCH

Research EACH site independently.

Determine:
- CMS/framework
- whether WordPress is actually used
- theme/plugins if discoverable
- REST/AJAX/GraphQL APIs
- HTML structure
- search URLs/API
- popular/latest/category/genre pages
- pagination
- detail pages
- episode pages
- embedded JSON/data attributes
- player architecture
- iframe nesting
- external hosts
- HLS/DASH/MP4
- cookies
- headers
- referer/origin requirements
- anti-hotlinking
- Cloudflare/anti-bot behavior
- anti-adblock behavior
- redirects
- token/signature generation
- obfuscation
- JavaScript-generated data
- domain/URL patterns

### WordPress hypothesis
AnimeXin and Lucifer Donghua MAY be WordPress-based. This is only a hypothesis.

Verify using evidence such as `/wp-content/`, `/wp-includes/`, `wp-json`, theme/plugin identifiers, WordPress metadata, AJAX endpoints, and generated HTML.

Do not call a site WordPress unless you verify it.

---

# 4. VIDEO EXTRACTION IS THE HIGHEST PRIORITY

For every site, map the complete chain:

`anime → detail → episode → player → iframe/provider → request/API → playable source → quality/server/subtitles`

Do not simply return an iframe URL when a real playable URL can be extracted.

Investigate:
- m3u8
- MP4
- DASH
- JSON player config
- `sources`
- `file`
- `playlist`
- manifest URLs
- API endpoints
- encoded URLs
- signed URLs
- token parameters
- referer
- origin
- user-agent requirements
- subtitle tracks
- multiple servers
- multiple qualities

If a server fails, use another available server when the site provides one.

---

# 5. EXISTING EXTENSION RESEARCH

Before implementing each source, search for existing/historical extensions for the exact domains.

Inspect:
- source code
- commits
- issues
- PRs
- forks
- extraction logic
- bugs
- update history
- licensing

Existing code may be used as a reference where licensing permits, but it MUST be independently validated against current site behavior.

Search both ecosystems separately.

---

# 6. REQUIRED FUNCTIONALITY

For every site/platform combination implement everything currently supported by the platform:

### Discovery
- search
- popular
- latest
- pagination
- categories/genres
- filters where available

### Details
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

### Episodes
- episode number
- episode title
- episode URL
- upload date where available
- season
- correct ordering
- specials
- OVAs
- movies where supported

### Playback
- playable URL
- original URL
- quality
- server
- subtitles
- headers
- referer/origin
- HLS
- MP4
- DASH where supported

---

# 7. EDGE CASES — MUST HANDLE

Actively test and handle:

- empty search results
- invalid search
- missing poster/description/genres
- malformed HTML/JSON
- missing episode number
- decimal episode numbers such as 12.5
- specials
- OVAs
- movies
- multi-season anime
- duplicate episodes
- pagination ending/gaps
- changed URLs
- redirects
- 403/404/429/5xx
- timeout
- unavailable/dead player
- unavailable server
- duplicate qualities
- missing quality
- relative/protocol-relative URLs
- encoded URLs
- signed/expiring URLs
- referer/origin requirements
- Cloudflare/anti-bot
- anti-adblock
- JS-generated content
- nested iframes
- external video hosts
- HLS/MP4/DASH
- subtitle tracks
- domain changes

Fail gracefully. Never crash because optional data is missing.

---

# 8. ROBUSTNESS RULES

Avoid:
- giant page-wide regexes
- random CSS classes
- layout-dependent selectors
- hardcoded anime IDs
- hardcoded temporary video URLs
- hardcoded tokens
- arbitrary sleeps
- unnecessary browser automation
- hardcoded episode counts

Prefer:
- stable attributes
- semantic selectors
- APIs/JSON
- URL patterns
- defensive parsing
- validation
- fallback selectors
- multiple extraction strategies
- sensible retries/timeouts

Use the lightest reliable approach, especially because these extensions may run on low-end devices.

---

# 9. STRICTLY SEPARATE THE TWO PLATFORM EXTENSIONS

The final project MUST have **two clearly separated extension trees**:

## A. Mangayomi extension tree

```text
extensions/
└── mangayomi/
    ├── README.md
    ├── animexin/
    │   ├── README.md
    │   ├── source.js              # or the correct current Mangayomi format
    │   ├── parser.js              # only if justified
    │   ├── player.js              # site/player extraction
    │   ├── constants.js
    │   ├── tests/
    │   └── fixtures/
    │
    ├── luciferdonghua/
    │   ├── README.md
    │   ├── source.js
    │   ├── parser.js
    │   ├── player.js
    │   ├── constants.js
    │   ├── tests/
    │   └── fixtures/
    │
    ├── animecube/
    │   ├── README.md
    │   ├── source.js
    │   ├── parser.js
    │   ├── player.js
    │   ├── constants.js
    │   ├── tests/
    │   └── fixtures/
    │
    └── docs/
        ├── architecture.md
        ├── compatibility.md
        └── testing.md
```

**IMPORTANT:** This is the conceptual structure. If the real Mangayomi repository/build system requires a different structure, follow the REAL current Mangayomi convention instead. Never break the build merely to preserve this example.

Each Mangayomi site MUST remain independently maintainable.

## B. CloudStream extension tree

```text
extensions/
└── cloudstream/
    ├── README.md
    ├── settings.gradle.kts
    ├── build.gradle.kts
    ├── gradle.properties
    ├── gradlew
    ├── gradlew.bat
    ├── gradle/
    │   └── wrapper/
    │
    ├── AnimeXin/
    │   ├── build.gradle.kts
    │   └── src/main/kotlin/
    │       └── .../AnimeXin.kt
    │
    ├── LuciferDonghua/
    │   ├── build.gradle.kts
    │   └── src/main/kotlin/
    │       └── .../LuciferDonghua.kt
    │
    ├── AnimeCube/
    │   ├── build.gradle.kts
    │   └── src/main/kotlin/
    │       └── .../AnimeCube.kt
    │
    ├── extractors/
    │   ├── README.md
    │   └── ...
    │
    └── docs/
        ├── architecture.md
        ├── compatibility.md
        └── testing.md
```

Again, adapt this to the actual current CloudStream extension repository conventions. Do not invent incompatible Gradle/module layouts.

### Critical separation rule

Do NOT put Mangayomi source files inside CloudStream modules or CloudStream Kotlin files inside Mangayomi source directories.

Do NOT create one giant `if platform == ...` implementation.

Each site should have a clean implementation per platform.

---

# 10. SHARED CODE RULE

Only share code if it is truly platform-independent and actually improves maintainability.

Good candidates:
- documented URL normalization concepts
- research notes
- test fixtures
- generic algorithm documentation

Do NOT force shared runtime code between JavaScript/Mangayomi and Kotlin/CloudStream.

Platform-specific parsing/extraction should remain platform-specific unless the actual build system supports a safe shared module.

---

# 11. MANGAYOMI-SPECIFIC REQUIREMENTS

Use the CURRENT Mangayomi extension API and repository conventions.

Determine whether JavaScript or another supported source format is best for each site.

Implement current equivalents for:
- source metadata
- search
- popular
- latest
- details
- episodes
- pagination
- video extraction

Correctly handle:
- video objects
- headers
- cookies
- referer/origin
- source IDs
- language
- icon
- version
- anime/source flags

Use current official testing/build workflow.

Do not blindly copy old extension APIs.

---

# 12. CLOUDSTREAM-SPECIFIC REQUIREMENTS

Use the CURRENT CloudStream plugin architecture.

Study the official/current extension repository and current Gradle plugin.

Use Kotlin and current provider APIs.

Correctly implement:
- provider metadata
- search
- load
- episodes
- loadLinks
- home pages where appropriate
- current extractor/link APIs
- quality
- HLS/DASH flags
- referer
- headers
- cookies

Use extractors when a third-party player requires reusable extraction logic.

Avoid deprecated APIs and verify API signatures against current upstream source before finalizing.

---

# 13. TESTING — REAL TESTS ONLY

Do not call the task complete because it compiles.

For EACH of the 6 implementations test:

### Search
- common title
- uncommon title
- no-result query

### Browse
- popular
- latest
- pagination

### Details
- ongoing title
- completed title
- multi-season title
- movie/special if available

### Episodes
- first
- middle
- latest
- special/OVA if available

### Playback
- each available server
- multiple qualities
- HLS
- MP4 if available
- subtitles if available

### Failure cases
- missing player
- dead server
- HTTP failure
- malformed response
- invalid URL

Record actual results.

If a test cannot be performed, explicitly say why. Never fabricate success.

---

# 14. BUILD + VALIDATION

Run the real current workflow for BOTH platforms.

### Mangayomi
- formatting
- lint/type checks where applicable
- extension validation
- metadata/index validation
- build/test scripts

### CloudStream
- Gradle build
- Kotlin compilation
- static/lint checks where available
- plugin metadata validation
- packaging

Fix errors instead of merely reporting them.

---

# 15. DOCUMENTATION OUTPUT

Create documentation for:

```text
docs/
├── research/
│   ├── animexin.md
│   ├── luciferdonghua.md
│   └── animecube.md
├── platform/
│   ├── mangayomi.md
│   └── cloudstream.md
├── reference-projects/
│   ├── donghua-project.md
│   └── uncensored-project.md
├── architecture/
│   └── overview.md
└── testing/
    └── test-results.md
```

Document for every site:
- CMS/framework
- verified APIs
- search strategy
- pagination
- detail parsing
- episode parsing
- player architecture
- exact extraction chain
- video servers
- quality extraction
- subtitles
- headers/referer/origin
- anti-bot behavior
- fallback strategy
- known limitations

For the local projects document:
- what was useful
- what was reused
- what was improved
- what was rejected
- what was independently verified

---

# 16. PERFORMANCE

Optimize for low-end machines/devices.

Avoid:
- duplicate requests
- unnecessary downloads
- repeated HTML parsing
- infinite retries
- arbitrary delays
- browser automation when normal HTTP/API parsing is sufficient

Prefer lightweight, deterministic requests and parsing.

---

# 17. SECURITY / LEGAL BOUNDARY

Never hardcode credentials, private API keys, private cookies, or session secrets.

Do not implement account takeover, credential theft, destructive behavior, or unauthorized access.

Treat external HTML/JSON as untrusted input.

For anti-bot/anti-adblock behavior, stay within normal publicly accessible browsing behavior and platform capabilities. Do not bypass authentication or private access controls.

---

# 18. AUTONOMOUS WORKFLOW

Do not repeatedly ask for permission to continue.

Follow this workflow:

1. Inspect both local reference projects.
2. Inspect current official Mangayomi source/docs.
3. Inspect current official CloudStream source/docs.
4. Search GitHub/Google/Reddit/current extensions.
5. Research each target website independently.
6. Build a site-by-site technical map.
7. Decide the most robust implementation strategy.
8. Implement Mangayomi sources independently.
9. Implement CloudStream providers independently.
10. Implement reusable extractors only where justified.
11. Build and validate.
12. Run real tests.
13. Debug failures.
14. Improve fallbacks and edge-case handling.
15. Re-test.
16. Write documentation.
17. Produce the final summary.

Ask me only if a genuinely unavoidable external decision, credential, or missing input is required.

---

# 19. FINAL ACCEPTANCE CRITERIA

The project is complete ONLY when:

- all 6 implementations exist
- Mangayomi and CloudStream are physically separated
- each site has independent source/provider logic
- both local reference projects were inspected
- official/current platform APIs were researched
- deep web research was performed
- existing extensions were investigated
- video extraction was actually tested
- edge cases were addressed
- builds/validation pass as far as the current toolchain permits
- documentation exists
- known limitations are explicitly documented
- no fabricated test results exist

At the end provide:

1. Final repository tree
2. Six implemented extensions
3. Supported features per extension
4. Site architecture findings
5. Video extraction flow for each site
6. Local reference-project findings
7. Tests performed + real results
8. Build/validation results
9. Known limitations
10. Sources used
11. What remains impossible and WHY

**START WITH RESEARCH. DO NOT START BY CODING.**