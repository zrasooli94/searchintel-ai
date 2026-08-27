# SearchIntel V1 real-world validation

Validated on 2026-08-28 with bounded local crawls and controlled benchmark
sets. The purpose was to test semantic correctness across unlike projects, not
to optimize scores.

## Validation set

| Project class | Project | Crawl | New AI runs | Modes |
| --- | --- | ---: | ---: | --- |
| Global consumer platform | Facebook | 0 pages; robots-limited | 6 | memory, web_search |
| Established technology/SaaS | Stripe | 10 pages | 9 | memory, web_search, site_rag |
| Content-rich SaaS | HubSpot Blog | 10 pages | 9 | memory, web_search, site_rag |
| Focused product | ChargeOps | Existing reviewed data | 0 | existing modes |
| Niche product | CXOps | Existing reviewed data | 0 | existing modes |

Facebook Site RAG was intentionally not run because its configured first-party
site returned no robots-eligible crawl corpus. Each new experiment used three
representative prompts and one run per prompt.

## Evidence summary

- Facebook was recognized in all memory responses. Its Web Visibility V1 was
  61.91, with target retrieval and citation coverage in two of three responses.
  The third response did not invoke live search and is now classified as
  unmeasured rather than as a content gap.
- Stripe was recognized in all memory responses and reached Web Visibility V1
  93.92. Its ten-page crawl scored 81/100 with only low-priority findings.
- HubSpot was recognized in all memory responses. Registering both the content
  subdomain and canonical apex domain was necessary for complete first-party
  Web Search attribution. After a derived-data-only reanalysis, Web Visibility
  V1 was 94.27.
- Stripe and HubSpot Site RAG each answered the first-party product question
  from retrieved evidence. Both declined to manufacture multi-brand comparison
  claims from first-party-only corpora, producing two genuine competitive
  evidence gaps and 33.33% answerability for this deliberately comparison-heavy
  three-prompt set.
- Existing ChargeOps and CXOps behavior remained materially different from the
  established brands: Web Visibility V1 remains 0.00, while Site RAG
  answerability remains 68.75% and 90.00% respectively.

These results are directionally sensible. They must not be treated as a market
benchmark because each new validation experiment contains only three prompts.

## Recommendation audit

Good:

- Robots-limited crawl messaging is evidence-based and prevents a false
  technical audit or Site RAG baseline.
- Low-priority Stripe heading/title findings ask for manual review rather than
  claiming that multiple headings are automatically harmful.
- Site RAG comparison actions explicitly require verified competitor evidence
  and preserve unsupported-answer honesty.
- Covered Web Search prompts receive a maintain-and-monitor recommendation.

Too generic:

- Technical title and metadata recommendations are page-level rules and do not
  consolidate repeated issues into an implementation batch.
- The deterministic Site RAG comparison action is correct but similar across
  industries; a client still needs an expert to translate it into a content
  brief.

Misleading issues corrected:

- A Web Search response with no live sources was previously labeled target
  absent and received a content-strengthening recommendation.
- An explicit visibility reanalysis previously skipped current-version
  responses even after brand/domain configuration changed.
- A zero-page robots-blocked crawl previously appeared as an ordinary successful
  crawl.

Missing:

- A single cross-page prioritized plan combining technical, Web Search, entity,
  and Site RAG work.
- A persisted crawl-eligibility history and explicit coverage scope for later
  visits and client reports.
- Configuration guidance for brands that own multiple domains or subdomains.

## Agency-grade gaps and next architecture

1. Add a measurement-eligibility assessment before prompt generation or
   baseline execution: robots access, crawl scope, JavaScript dependence,
   canonical domain set, and Site RAG corpus sufficiency.
2. Turn onboarding into a guided discovery workflow for canonical brand names,
   owned domains, competitors, and prompt portfolios, with expert approval
   rather than silent automation.
3. Create a unified prioritized guidance layer that references—not rewrites—the
   historical GEO plan, current technical findings, Web Search opportunities,
   and current Site RAG actions.
4. Add configuration-aware analysis invalidation and clear before/after recheck
   workflows.
5. Add action ownership, status, confidence, scheduled monitoring, and
   client-ready reporting after the prioritized guidance model is stable.

The recommended next milestone is **Measurement Eligibility and Guided
Onboarding**, followed by the unified prioritized guidance layer.
