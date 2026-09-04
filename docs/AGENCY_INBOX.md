# Agency Inbox V1

`/agency-inbox` is an agency-wide, public read-only evidence view. Operator-only
PATCH controls change read/unread/archive state, not evidence. Archived events
are retained. POST `/api/v1/agency-inbox/reconcile` performs the initial backfill
and can retry deterministic reconciliation without any paid calls or crawls.

The additive `d8a1f6b9c302` migration creates events and internal checkpoints.
Reconciliation runs after benchmark derivation, technical audit completion,
priority refresh/status changes, monitoring completion/configuration and the
durable dispatcher. GET endpoints never reconcile. Reconciliation failures do
not invalidate completed measurements; the dispatcher retries stored evidence.

Project row locks serialize writers and unique event identities prevent duplicate
inserts. Checkpoints distinguish recurring conditions from unchanged conditions.
Resolution creates a new event; it never replaces the original evidence. An empty
or stable check creates no event. Initial backfill includes current high priorities,
verifiable rechecks and latest failed monitoring executions; it seeds measurement
comparisons rather than replaying every historical benchmark.

Internal V1 rules (not industry standards): 5-point visibility, verified coverage,
answerability or technical sample-score movement is meaningful; a decline of 10
points is high severity. Gains/resolutions are low severity. A target moving to or
from zero verified coverage is surfaced even below 5 points. Grounded competitor
response-share movement of 10 points is medium severity and is not market share.
Overdue/failure and new high priorities are high; unchanged rechecks are medium.

Comparisons require the same project, mode, model, exact frozen prompt texts,
retrieval/tool configuration and current brand/domain configuration. Missing
analysis is never treated as zero gaps. Technical comparisons require the same
website and sample size and explicitly disclose that page counts alone do not
prove identical coverage. Memory is not mixed with Web Search or Site RAG.

The Inbox does not run AI, refresh measurements, enable schedules, or send messages.
No email, assignments or custom alert rules are included. Read-only pages use the
existing server-only API credential; operator credentials never enter public JS.
