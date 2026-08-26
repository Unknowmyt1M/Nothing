# OpenCode — Mangayomi Multi-Site Anime Extension Engineering Task

You are an autonomous senior Mangayomi extension engineer, web reverse-engineering researcher, JavaScript developer, QA engineer, and technical documentation researcher.

Your task is to research, implement, test, debug, and finalize **THREE SEPARATE, production-quality Mangayomi anime extensions** for:

1. https://animexin.dev/
2. https://luciferdonghua.in/
3. https://animecube.live/

Each website MUST have its own independently maintainable extension. Do not blindly merge unrelated site-specific logic into one giant conditional source.

---

## 0. CRITICAL: YOU HAVE A LOCAL REFERENCE PROJECT

A few days ago you worked on a similar project. Its local project folder is:

`D:\Projects\Websites\Donghua`

**You MUST inspect, read, and analyze this project before designing the new extensions.**

Use it as a valuable reference for:

- site discovery
- scraping/parsing approaches
- API discovery
- WordPress handling
- player/iframe analysis
- video extraction
- HLS/m3u8 handling
- URL normalization
- headers/referer/origin handling
- anti-adblock/anti-bot observations
- reusable utilities
- bugs and fixes already discovered
- lessons learned
- failed approaches

However, **DO NOT TRUST THIS PROJECT BLINDLY.** Treat it as evidence/reference material, not authoritative truth.

For every important approach copied/adapted from `D:\Projects\Websites\Donghua`:

1. Understand what it does.
2. Verify that it is still correct against the current target website.
3. Check whether the Mangayomi runtime supports the approach.
4. Improve it if it is fragile/outdated.
5. Do not reproduce known bugs merely because the old project used them.

If the local project contains code for any of the target sites or related sites, compare its implementation against your new research and explicitly document what you reused, changed, or rejected and why.

---

# 1. RESEARCH FIRST — DO NOT START CODING IMMEDIATELY

Before writing production code, perform deep research.

Read the current/official Mangayomi source and extension-development documentation. Do not rely on memory or outdated tutorials.

Official Mangayomi GitHub:
https://github.com/kodjodevf/mangayomi

Also inspect the current/known extension ecosystem and community repositories, including JavaScript anime extensions where available.

Research:

- Mangayomi architecture
- anime source architecture
- JavaScript extension architecture
- source metadata
- source IDs
- extension versioning
- `getPopular`
- `getLatest`
- search
- filters
- details
- episodes
- `getVideoList`
- pagination
- HTTP client
- DOM selectors/parsing
- JSON/API handling
- headers
- cookies
- referer/origin handling
- JavaScript runtime limitations
- available helper functions
- crypto/deobfuscation helpers where officially supported
- source installation/index conventions
- current build/validation workflow
- Windows desktop testing workflow

Read the actual official documentation/source code before making architectural decisions.

---

# 2. EXISTING EXTENSIONS — RESEARCH THEM DEEPLY

Search GitHub, Google, Reddit, GitHub Issues/PRs, forums, and other technical sources for existing Mangayomi anime extensions and extensions for the exact target websites.

Useful reference repositories may include:

- official Mangayomi repository
- official/archived Mangayomi extension repository
- actively maintained community anime extension repositories
- other working JavaScript anime sources

For any existing target-site extension you find:

1. Inspect its complete implementation.
2. Check its last update/commit.
3. Inspect issues and PRs.
4. Identify known bugs.
5. Analyze its video extraction strategy.
6. Compare it with the current website.
7. Reuse good ideas where appropriate.
8. Respect its license and attribution requirements.
9. Never assume it is correct merely because it exists.

Community code is reference material, not ground truth.

---

# 3. DEEP RESEARCH FOR EACH TARGET SITE

Investigate each site independently:

### AnimeXin
https://animexin.dev/

### Lucifer Donghua
https://luciferdonghua.in/

### AnimeCube
https://animecube.live/

For EACH site determine:

- CMS/framework
- whether it is actually WordPress (do NOT assume)
- theme
- plugins if publicly detectable
- REST APIs
- AJAX endpoints
- GraphQL if present
- HTML structure
- search mechanism
- popular pages
- latest pages
- genre/category pages
- detail pages
- episode pages
- pagination
- URL patterns
- embedded data
- `data-*` attributes
- JSON blobs
- JavaScript-generated content
- iframe/player architecture
- external video providers
- HLS/DASH/direct MP4 availability
- API requests
- token/signature generation
- cookies
- required headers
- referer requirements
- origin requirements
- anti-hotlink behavior
- Cloudflare/other protection
- anti-adblock behavior
- redirects
- obfuscation
- URL encoding
- dynamic player URLs

Use actual inspection, requests, source analysis, browser/network inspection when useful, and credible public research. Do not guess.

### WordPress hypothesis
AnimeXin and Lucifer Donghua may be WordPress-based. This is only a hypothesis.

Verify indicators such as:

- `/wp-content/`
- `/wp-includes/`
- `wp-json`
- WordPress REST API
- theme/plugin identifiers
- WordPress-generated markup
- AJAX endpoints

If a stable public API exists, determine whether it is more reliable than HTML scraping. If not, implement robust HTML parsing.

---

# 4. VIDEO EXTRACTION IS A TOP PRIORITY

For every website determine the full real-world chain:

`anime -> detail -> episode -> player -> iframe/provider -> API/request -> video source`

`getVideoList()` MUST return valid Mangayomi video objects.

Where technically supported, expose:

- multiple servers
- multiple qualities
- HLS `.m3u8`
- direct MP4
- subtitles
- original URL
- playable URL
- required headers
- referer
- origin
- meaningful server names

Do not simply return an iframe URL when an actual playable source can be extracted.

If several servers exist, expose independent server options when practical so one failing server does not kill playback completely.

Analyze players such as:

- HTML5 video
- JWPlayer
- Video.js
- Plyr
- custom players
- HLS.js
- DASH
- nested iframes
- third-party video hosts
- encoded/obfuscated player configuration

Look for:

- `file`
- `source`
- `sources`
- `playlist`
- `m3u8`
- `mp4`
- `manifest`
- API endpoints
- JSON configuration
- token/signature parameters
- referer/origin requirements

Prefer structured/API data over brittle regex whenever possible.

---

# 5. FUNCTIONAL REQUIREMENTS

Each extension should implement as much of the current Mangayomi anime source API as the platform supports:

### Discovery
- Popular
- Latest
- Search
- Pagination
- Genres/categories
- Filters where supported

### Details
Return, where available:

- title
- alternative titles
- poster/thumbnail
- description
- genres
- status
- type
- year/date
- rating
- author/studio/creator metadata

### Episodes
Return:

- episode number
- episode title
- episode URL
- upload date where available
- season information where available
- correct ordering
- specials/OVAs/movies where supported

### Playback
Return:

- video URL
- original URL
- quality
- server
- subtitles if supported
- required headers
- referer/origin where required

---

# 6. EDGE CASES — HANDLE THEM EXPLICITLY

Investigate and gracefully handle:

- empty search results
- invalid search queries
- missing posters
- missing descriptions
- missing genres
- missing ratings
- malformed HTML
- malformed JSON
- missing episode numbers
- decimal episode numbers such as `12.5`
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
- timeouts
- unavailable player
- unavailable video server
- multiple servers
- duplicate qualities
- missing quality
- relative URLs
- protocol-relative URLs
- encoded URLs
- signed URLs
- expired tokens
- referer requirements
- origin requirements
- Cloudflare
- anti-adblock
- JavaScript-generated content
- nested iframes
- external video hosts
- HLS playlists
- direct MP4
- subtitles
- domain changes
- SSL/HTTPS issues
- unexpected layout changes

Do not crash the extension on malformed/missing data.

---

# 7. ROBUSTNESS RULES

Avoid fragile approaches such as:

- giant regexes for complete HTML pages
- selectors based on random CSS classes
- selectors based only on visual layout
- hardcoded episode counts
- hardcoded anime IDs
- hardcoded temporary video URLs
- hardcoded temporary tokens
- arbitrary sleeps
- unnecessary delays
- assumptions from one page

Prefer:

- semantic selectors
- stable attributes
- stable URL patterns
- API/JSON data
- structured parsing
- validation
- fallback selectors
- multiple extraction strategies when justified
- defensive null handling

---

# 8. ARCHITECTURE / FOLDER STRUCTURE

Create a beautiful, professional, maintainable project structure, but **follow the actual Mangayomi repository/build conventions first**.

Do not invent a folder layout that breaks the extension ecosystem.

Conceptually, aim for clean separation such as:

```text
extensions/
├── README.md
├── LICENSE
├── docs/
│   ├── research/
│   │   ├── animexin.md
│   │   ├── luciferdonghua.md
│   │   └── animecube.md
│   ├── architecture.md
│   ├── testing.md
│   └── troubleshooting.md
│
├── animexin/
│   ├── README.md
│   ├── source.js
│   ├── parser.js
│   ├── player.js
│   ├── constants.js
│   └── tests/
│
├── luciferdonghua/
│   ├── README.md
│   ├── source.js
│   ├── parser.js
│   ├── player.js
│   ├── constants.js
│   └── tests/
│
├── animecube/
│   ├── README.md
│   ├── source.js
│   ├── parser.js
│   ├── player.js
│   ├── constants.js
│   └── tests/
│
└── tools/
```

Treat that only as an architectural goal. Adapt it to the real Mangayomi extension source/index conventions.

Keep site-specific logic isolated and independently maintainable.

---

# 9. TESTING — REAL TESTS ONLY

Do not declare success because code merely compiles.

For every extension test:

### Search
- common anime
- uncommon anime
- no-result search

### Browse
- popular
- latest
- pagination

### Details
- ongoing anime
- completed anime
- movie
- multi-season anime

### Episodes
- first episode
- middle episode
- latest episode
- special if available

### Video
- every available server
- multiple qualities
- HLS if available
- direct video if available
- subtitle track if available

### Failure cases
- unavailable episode
- invalid URL
- unavailable player
- HTTP failure
- malformed response

Actually execute tests using the available environment/tools. Record what was tested and the results.

Never fabricate test results.

---

# 10. BUILD / LINT / VALIDATION

Use the real Mangayomi extension workflow.

Before completion:

- format
- lint
- type-check if applicable
- run source validation
- run build/generation scripts
- verify metadata/index files if required
- verify extension IDs
- verify names
- verify language
- verify icon URLs
- verify versions
- verify imports
- verify JSON
- verify source compatibility

Fix all errors you encounter.

---

# 11. RESEARCH DOCUMENTATION

For every site create a research document covering:

- URL
- CMS/framework
- discovery mechanism
- search mechanism
- pagination
- details structure
- episode structure
- player structure
- video extraction flow
- APIs/endpoints
- stable selectors
- headers
- cookies
- anti-bot behavior
- known limitations
- fallback strategies

Document evidence and links to the sources actually used.

Include relevant:

- official Mangayomi documentation
- official repositories
- GitHub implementations
- GitHub issues/PRs
- Reddit discussions
- technical references
- website observations

Do not fabricate citations.

---

# 12. OFFICIAL-DOCS-FIRST RULE

Whenever you use a framework, API, library, runtime, or Mangayomi capability:

**Read its official/current documentation first whenever it exists.**

Community sources can supplement official docs but must not replace them when official documentation is available.

This applies especially to:

- Mangayomi
- JavaScript extension APIs
- HTTP APIs
- DOM/parser APIs
- crypto helpers
- HLS/video-related APIs
- build tooling
- repository/index formats

---

# 13. DEEP WEB RESEARCH

Research broadly across:

- Google
- GitHub
- Reddit
- official documentation
- GitHub Issues
- GitHub Pull Requests
- Stack Overflow when relevant
- technical forums
- existing extension repositories
- archived projects

Use exact-domain and implementation-focused searches, for example:

`"animexin.dev" API`
`"animexin.dev" player`
`"animexin.dev" m3u8`
`"animexin.dev" iframe`
`"animexin.dev" wordpress`
`"luciferdonghua" API`
`"luciferdonghua" player`
`"luciferdonghua" m3u8`
`"luciferdonghua" iframe`
`"luciferdonghua" wordpress`
`"animecube.live" API`
`"animecube.live" player`
`"animecube.live" iframe`
`"animecube.live" m3u8`
`site:github.com Mangayomi AnimeXin`
`site:github.com Mangayomi LuciferDonghua`
`site:github.com Mangayomi AnimeCube`

Create better queries as new clues appear.

---

# 14. PERFORMANCE

These extensions may run on low-end devices.

Avoid:

- unnecessary HTTP requests
- duplicate requests
- unnecessary browser/page loads
- repeated expensive parsing
- infinite retries
- long artificial delays

Prefer:

- efficient selectors
- structured API data
- early exits
- sensible retries
- timeouts
- lightweight parsing
- minimal requests

---

# 15. SECURITY / BOUNDARIES

Never hardcode:

- personal credentials
- private API keys
- private cookies
- user secrets

Do not implement credential theft, account takeover, malicious execution, or unauthorized access.

For anti-bot/anti-adblock behavior, only use technically appropriate handling within the normal publicly accessible browsing flow and what the Mangayomi runtime legitimately supports. Do not attempt to defeat authentication or private access controls.

Treat remote HTML/JSON as untrusted input and validate extracted URLs.

---

# 16. AUTONOMOUS WORKFLOW

You should work autonomously.

Do not repeatedly ask me whether you should continue or which obvious engineering choice to make.

Instead:

1. Inspect the local reference project.
2. Read official Mangayomi documentation/source.
3. Research existing extensions.
4. Research all three target sites.
5. Build a technical plan.
6. Implement each extension.
7. Test each extension.
8. Debug failures.
9. Improve robustness.
10. Run final validation.
11. Document everything.

Only ask me when an actual external decision, missing file, permission, credential, or genuinely ambiguous requirement is necessary.

---

# 17. DO NOT STOP AT THE FIRST WORKING VERSION

After the first implementation:

1. Re-read the code.
2. Compare it with strong existing Mangayomi extensions.
3. Compare it with `D:\Projects\Websites\Donghua`.
4. Identify fragile assumptions.
5. Improve selectors.
6. Improve fallbacks.
7. Improve video extraction.
8. Improve error handling.
9. Improve performance.
10. Re-test.

Think like an open-source maintainer, not a code generator.

---

# 18. FINAL DELIVERABLE

At the end provide:

### A. Final repository tree

### B. Implemented extensions

- AnimeXin
- Lucifer Donghua
- AnimeCube

### C. Feature matrix

For each source report:

- Search
- Popular
- Latest
- Details
- Episodes
- Pagination
- Genres/filters
- Servers
- Qualities
- Subtitles
- Video extraction

### D. Technical research findings

Explain each site's architecture and important discoveries.

### E. Video extraction flow

Explain the actual chain from episode URL to playable source for each site.

### F. Local reference-project findings

State what was learned from `D:\Projects\Websites\Donghua`, what was reused, what was improved, and what was rejected.

### G. Known limitations

Be honest and specific.

### H. Test results

Show actual tests and results.

### I. Build/validation results

Show commands/results used for validation.

### J. Sources

List important official docs, GitHub repositories, issues, discussions, and other sources actually used.

---

# NON-NEGOTIABLE FINAL RULES

- **Start with research, not code.**
- Inspect `D:\Projects\Websites\Donghua` before implementation.
- Do not blindly trust the old project.
- Do not blindly trust existing extensions.
- Read official documentation before using APIs/framework features.
- Verify WordPress instead of assuming it.
- Verify APIs instead of assuming them.
- Verify video extraction instead of assuming it.
- Do not fabricate tests, sources, or successful playback.
- Keep all three extensions independently maintainable.
- Handle edge cases and failures gracefully.
- Optimize for real Mangayomi compatibility and long-term maintainability.

**BEGIN NOW WITH PHASE 1: inspect `D:\Projects\Websites\Donghua` and perform the Mangayomi + target-site research. Do not write the final extension code until the research phase is complete.**
