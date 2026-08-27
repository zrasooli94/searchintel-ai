# SearchIntel AI V1 deployment

## Architecture

SearchIntel V1 uses the same provider split as ChargeOps:

1. Vercel runs the Next.js application in `frontend/` and its same-origin
   server proxy routes.
2. Render runs the FastAPI application in `backend/`, including `/api/v1`,
   liveness, readiness, and OpenAPI endpoints.
3. Neon runs the separate PostgreSQL database over TLS.

The frontend calls the backend from the Next.js server. The shared API token
is server-only and must never use a `NEXT_PUBLIC_` prefix.

## Prepared staging architecture

- `render.yaml` defines only `searchintel-staging-api`, a free Render Python
  web service in Singapore. It does not provision a frontend or database.
- `frontend/vercel.json` selects Next.js and the verified webpack production
  build for the Vercel project whose root directory is `frontend/`.
- Neon must contain a separate SearchIntel PostgreSQL project/database. Never
  reuse the ChargeOps Neon database.

Configure Render `DATABASE_URL` from the Neon pooled or direct TLS connection
string. SearchIntel normalizes Neon provider URLs beginning with
`postgresql://` to the installed Psycopg 3 driver. The Render Blueprint
generates `API_TOKEN`; securely copy the same value into Vercel as the
server-only `SEARCHINTEL_API_TOKEN`.

After Vercel assigns the frontend origin, set Render `CORS_ORIGINS` to that
exact HTTPS origin. Set Vercel `SEARCHINTEL_API_BASE_URL` to the Render HTTPS
origin followed by `/api/v1`. Do not use `NEXT_PUBLIC_` variables.

The staging API runs `alembic upgrade head` before starting its single Uvicorn
worker, matching the established portfolio deployment pattern. Paid production
may move migrations into a distinct release job.

The staging data strategy is an empty migrated database first. After health
acceptance, import only reviewed demo data through a temporary, access-controlled
database transfer. Do not commit a database dump, copy local `.env` values, or
rerun paid AI benchmarks merely to populate staging. The current local
ChargeOps/CXOps dataset may be copied only after confirming it contains no
private customer data. A reviewed transfer must preserve the relational rows
for the local ChargeOps and CXOps projects only (currently project IDs 1 and
4), exclude the unrelated Facebook test project (currently project ID 5), and
verify row counts and foreign keys transactionally before acceptance. The
schema contains no application credential table, but the transfer process must
still inspect exported column names and never include provider credentials or
environment files.

## Prerequisites

- Python 3.13-compatible runtime
- Node.js runtime supported by Next.js 16
- PostgreSQL 16
- A generated, high-entropy shared API token
- An OpenAI API key only when benchmark execution or AI analysis is enabled

Create production environment variables in the hosting provider's secret
store. Do not copy or commit local `.env` files.

## Backend environment

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | Yes | SQLAlchemy PostgreSQL URL using the `postgresql+psycopg` driver. |
| `APP_ENV` | Yes | Set to `production`; enables production configuration validation. |
| `API_TOKEN` | Production | Shared bearer token required for every `/api/v1` request. |
| `CORS_ORIGINS` | Production | Comma-separated HTTPS frontend origins, without trailing slashes. |
| `OPENAI_API_KEY` | For AI execution | Server-side OpenAI credential. Read-only dashboards can start without it. |
| `APP_NAME` | No | Display/OpenAPI name; defaults to `SearchIntel AI`. |
| `PORT` | Host-dependent | Port supplied to the Uvicorn start command. |
| `WEB_CONCURRENCY` | No | Uvicorn worker count; start conservatively because benchmark tasks are in-process. |

`APP_ENV=production` rejects a missing API token, empty CORS list, or localhost
CORS origin. `/health` and `/health/live` remain unauthenticated for hosting
checks. Database and API secrets are represented as secret values in backend
settings and are not returned by health responses.

## Frontend environment

| Variable | Required | Purpose |
| --- | --- | --- |
| `SEARCHINTEL_API_BASE_URL` | Production | Backend URL including `/api/v1`, for example `https://api.example.com/api/v1`. |
| `SEARCHINTEL_API_TOKEN` | Production | Must exactly match backend `API_TOKEN`; used only by server code. |

The production frontend fails fast when either variable is absent. Local
development alone falls back to `http://127.0.0.1:8000/api/v1`. Neither
variable is public browser configuration.

## Database and migrations

The migration chain has one head. For V1 the expected revision is
`c31d8f2a4b70`.

Before a release:

1. Confirm a recent restorable database backup or provider snapshot.
2. Record the current revision with `alembic current`.
3. Inspect pending SQL when required by change policy with `alembic upgrade
   head --sql` against an appropriate baseline.
4. Run `.venv/bin/alembic upgrade head` once as a release job, not in every
   web worker.
5. Confirm `.venv/bin/alembic current` reports the expected head.

The V1 zero-gap migration adds `site_rag_gap_analyses`, preserves historical
gap rows, and backfills completed analysis markers. Unknown historical total
prompt counts remain `NULL` instead of being guessed. Do not reset or recreate
the database during deployment.

## Build and start commands

Run commands from each service directory.

Backend migration:

```bash
.venv/bin/alembic upgrade head
```

Backend production start:

```bash
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers "${WEB_CONCURRENCY:-1}"
```

Frontend build and start:

```bash
npm ci
npm exec next -- build --webpack
npm run start -- -p "${PORT:-3000}"
```

The explicit webpack build is the verified V1 path. Turbopack may require
local process/port capabilities that are unavailable in restricted builders.

## Release order

1. Verify backup, secrets, database reachability, and the currently deployed
   revision.
2. Build immutable backend and frontend artifacts from the same commit.
3. Put long-running benchmark creation into a maintenance window if needed.
4. Run the Alembic migration job.
5. Start/release the backend.
6. Verify `/health/live`, then `/health` and the schema revision.
7. Release the frontend with its backend URL and matching API token.
8. Run the smoke checklist below.

For staging, first create or link the GitHub repository and push the reviewed
release commits. Then create the Neon database, sync the Render backend from
`render.yaml`, and import the Vercel project with `frontend/` as its root.
Auto-deploy remains disabled on the Render backend until live acceptance is
complete.

## Smoke checklist

Use `Authorization: Bearer <API_TOKEN>` for `/api/v1` calls. Do not paste the
real token into tickets or logs.

- `GET /health/live` returns HTTP 200 and V1 version metadata.
- `GET /health` returns HTTP 200 with `database=available`.
- `GET /api/v1/projects/workspaces` returns the workspace list.
- `GET /api/v1/projects/{id}/technical-seo-summary` returns the technical SEO
  data path for a configured project.
- `GET /api/v1/projects/{id}/experiments-summary` returns AI visibility and
  experiment state without starting a benchmark.
- `GET /api/v1/projects/{id}/action-plan-summary` returns HTTP 200.
- For CXOps, the Action Plan response has `has_historical_plan=false` while
  current `site_rag` actions may be present.
- For ChargeOps, the historical plan remains present and current `site_rag`
  data remains independent.
- Repeating all GET checks does not change plan, gap-analysis, or action counts.
- The frontend root and a project Action Plan route render successfully.
- Benchmark job status can be read at `GET /api/v1/benchmark-jobs/{job_id}`;
  no benchmark needs to be launched for release validation.

## Rollback

- Prefer rolling application code back while leaving additive schema changes
  in place; the V1 migration is backward-compatible with the preceding code.
- Do not run an Alembic downgrade while web workers are active.
- If a schema rollback is mandatory, stop writes, take another backup, test the
  downgrade against a restored copy, and follow the provider's recovery plan.
- Restore the database snapshot only for confirmed data/schema corruption, not
  for an ordinary application rollback.

## Known V1 limitations

- Authentication is a single shared service token, not user accounts, roles,
  or project-level authorization. Put the portfolio deployment behind an
  access gateway if it is exposed broadly.
- Background benchmark work runs in the backend process rather than a durable
  external queue. Use one worker for benchmark-capable deployments unless the
  execution model is deliberately redesigned.
- `OPENAI_API_KEY` is optional at startup, but AI execution endpoints fail
  explicitly when it is absent.
- Site RAG measures first-party crawled-site answerability. `[Source N]`
  references are retrieval grounding references, not web citations.
- `memory`, `web_search`, and `site_rag` measurements are not quantitatively
  interchangeable.
- Provider accounts, custom domains, Neon backups, and external monitoring are
  managed outside this repository; the committed manifests configure only the
  Render backend and Vercel frontend build.
