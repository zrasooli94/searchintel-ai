# Measurement Eligibility and Guided Onboarding

SearchIntel evaluates project configuration before a new crawl, audit, or AI
benchmark is started. The read-only endpoint is:

```text
GET /api/v1/projects/{project_id}/readiness
```

Loading readiness never crawls a website, searches the web, calls OpenAI, or
changes project configuration. It evaluates four modes independently:

- `technical_seo`: bounded SearchIntel crawl and audit capability.
- `memory`: latent model knowledge without live retrieval.
- `web_search`: controlled API web-search retrieval and citation evidence.
- `site_rag`: answerability using stored first-party crawl evidence only.

States are `ready`, `needs_review`, `limited`, `blocked`, and
`not_applicable`. Execution availability is reported separately so a project
can be correctly configured while the backend lacks an AI execution key.
Historical results remain visible even when a future run is blocked.

## Approval boundary

First-party domain and competitor suggestions are derived only from stored
project evidence. Suggestions are never persisted automatically:

```text
detect -> explain -> suggest -> agency user approves -> persist
```

Domain suggestions require repeated sources already resolved to the target
brand or canonical evidence from an existing first-party crawl. The agency
user remains responsible for confirming ownership. Competitor suggestions
require repeated resolved non-target appearances. Prompt-category guidance
opens the existing prompt editor; it does not manufacture prompt text.

## Crawl evidence

Each explicit crawl now stores its bounded outcome on the website, including
robots-blocked counts and limitation messages. This lets later GET preflight
requests explain a Facebook-like limitation without rerunning the crawler.
"SearchIntelBot was blocked" is deliberately not presented as a claim about
Google or another crawler.

Site RAG requires at least three usable HTTP-success pages and 500 meaningful
stored words. These are corpus-sufficiency safeguards, not quality scores.
