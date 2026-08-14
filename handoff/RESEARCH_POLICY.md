# Research and Asset Policy

Pūpūkahi publishes educational material about fast-changing and sometimes high-stakes subjects. Research is evidence collection, not an LLM confidence exercise.

This policy applies whether the planner is local or hosted. A larger model does not relax it.

## Non-negotiable sequence

```text
topic or supplied material
    -> discover candidate sources
    -> fetch and freeze allowed sources
    -> extract proposed facts with evidence
    -> human approves facts and assets
    -> write narration and storyboard from approved IDs only
    -> render with no network access
```

Never write a script first and browse until something appears to support it.

## Research modes

| Mode | Behavior |
|---|---|
| `auto` | Begin with supplied material, then search for missing or current evidence |
| `provided_only` | Fetch only supplied URLs and use supplied text; perform no broader search |
| `none` | Perform no network access; require sufficient supplied text |

Topic-only requests require `auto`. `provided_only` requires at least one source URL or supplied text. `none` requires supplied text.

## What the local model can do

Ollama does not receive unrestricted internet, shell, or filesystem access. Python owns narrow tools such as:

```text
search_web(query)
fetch_page(approved_url)
search_open_images(query)
download_approved_asset(asset_id)
```

The application validates and executes tool calls. Model output is data, never authority to execute a command or fetch an arbitrary internal address.

## Source priority

Prefer, in order:

1. government publications, statutes, regulations, standards, official statistics, and public advisories
2. peer-reviewed research, universities, and recognized research institutions
3. first-party product or protocol documentation for claims about that product or protocol
4. established nonprofits and professional organizations with named expertise
5. reputable journalism for recent events and attributed reporting
6. encyclopedias, blogs, forums, and social media for discovery only

Popularity, search rank, repetition, and an LLM's familiarity are not evidence quality.

Two pages repeating the same upstream statement count as one source. Prefer the original.

## Source suitability

For every source, record:

- stable source ID
- canonical URL
- page title and publisher
- author when available
- publication or update date when available
- retrieval timestamp
- source class: `primary`, `secondary`, or `discovery_only`
- local frozen path
- SHA-256

Reject or escalate:

- anonymous claims with no evidence
- undated advice where currentness matters
- unofficial mirrors when the original is available
- search snippets used as proof
- pages that cannot be fetched without bypassing access controls
- material whose licensing does not permit the intended use

## Fact ledger

Each proposed fact records:

- stable fact ID
- publication-ready claim
- short evidence excerpt
- source IDs
- relevant date, unit, jurisdiction, version, and conditions
- whether sources agree, conflict, or leave uncertainty
- approval state and reviewer note

Rules:

- Numbers, dates, rankings, names, and quotations must appear in frozen evidence.
- A paraphrase must preserve scope and uncertainty.
- Never convert “may,” “associated with,” or “in this study” into a universal statement.
- Never infer causation from correlation.
- If credible sources conflict, state the disagreement or omit the claim.
- If evidence is insufficient, return fewer facts. Do not pad a ledger.
- Approved facts are immutable for that review revision. A changed claim receives a new revision and approval.

The script, storyboard, captions, and posting copy may reference approved fact IDs only.

## Currentness

Treat these as time-sensitive by default:

- laws, regulations, government programs, elections, and public officials
- prices, market values, interest rates, and economic indicators
- platform features, policies, APIs, model capabilities, and software versions
- security vulnerabilities, scam methods, and official incident guidance
- event schedules, availability, and organization contact information

Record an “as of” date in the fact and show it in the video when omission could mislead.

## AI content rules

- Describe tested capabilities and limitations, not human-like intent.
- Distinguish a product's marketing claim from independent evidence.
- Name the model/product version and date when behavior can change.
- Do not claim generated content is private, secure, unbiased, accurate, or copyright-safe without qualified evidence.
- Clearly distinguish a demonstration from a recommended production practice.

## Crypto and financial-content rules

Crypto content is educational, not financial advice.

- Do not recommend buying, selling, holding, staking, lending, bridging, or connecting a wallet.
- Do not make price predictions or portray returns as expected.
- Do not use urgency, scarcity, fear of missing out, or wealth imagery.
- Explain risks alongside mechanisms: custody, irreversible transactions, smart-contract risk, fees, impersonation, and recovery limitations where relevant.
- Never ask for a seed phrase, private key, wallet connection, payment, or transfer.
- Verify legal, tax, regulatory, and product-availability claims with current official sources and human review.
- Demonstrations use mock addresses, mock balances, and clearly labeled non-live data.
- Security incidents and scam-response steps prioritize current official law-enforcement, regulator, platform, or wallet-provider guidance.

Every crypto video requires human fact approval even when it contains no price or recommendation.

## Other high-stakes subjects

Medical, legal, financial, election, public-safety, and active-security guidance requires:

- at least one current primary or official source
- explicit human approval
- visible jurisdiction/date when applicable
- careful separation of general education from individual advice

When a short video cannot carry the necessary nuance, narrow the claim or do not publish it.

## Network safety

Every URL crosses a trust boundary. The fetch layer must:

- allow only `http` and `https`
- reject embedded credentials
- resolve DNS and reject loopback, private, link-local, multicast, and cloud-metadata addresses
- revalidate every redirect target
- enforce connect/read timeouts, redirect limits, and maximum response bytes
- allow only expected HTML, text, PDF, and image MIME types
- use a truthful application user agent
- never bypass authentication, paywalls, CAPTCHAs, robots controls, or access restrictions
- cache successful documents by content hash
- perform no network requests during HyperFrames rendering

PDF support is added only when a real approved source needs it.

## Image and media rights

Use assets in this order:

1. user-supplied assets with confirmed permission
2. organization-owned brand assets
3. public-domain or CC0 material
4. CC BY material with complete attribution
5. other Creative Commons material only when every condition is supported
6. generated artwork in a later approved milestone

Do not treat a generic image-search result as a license or reusable asset.

Openverse may discover candidates, but its license metadata must be verified against the original source page. Wikimedia Commons metadata may support verification but does not replace human review when terms are unclear.

Each asset ledger entry contains:

- stable asset ID
- local frozen filename and SHA-256
- original file URL and source/detail page
- title and creator
- license name and URL
- exact required attribution
- retrieval timestamp
- modifications such as crop or color treatment
- approval status and reviewer note

Only approved local asset paths may enter a storyboard. Remote URLs never enter the rendered composition.

## Required artifacts

Each job produces:

```text
.work/JOB_ID/research/sources.json
.work/JOB_ID/research/facts.json
.work/JOB_ID/research/assets.json
.work/JOB_ID/research/FACTS.md
.work/JOB_ID/research/CREDITS.md
```

The final output includes the approved `FACTS.md`, `CREDITS.md`, and an artifact manifest beside the MP4.

## Approval gate

A human reviewer must be able to see:

- the proposed claim
- its supporting excerpt
- the source page and date
- relevant conditions and uncertainty
- every selected asset and its license/attribution

Rejecting a fact or asset invalidates only downstream script, storyboard, preview, and render artifacts that depend on it. It does not restart unrelated research.
