# SearchIntel AI V1

SearchIntel AI is a full-stack SEO, GEO, AEO, and controlled AI-search
intelligence platform. It keeps three measurement modes semantically
separate:

- `memory`: latent model-knowledge measurement
- `web_search`: controlled API web-search measurement
- `site_rag`: controlled first-party crawled-site answerability

## Repository layout

- `backend/`: FastAPI, SQLAlchemy, PostgreSQL, and Alembic
- `frontend/`: Next.js dashboard
- `docs/`: product, data-model, and deployment documentation
- `docker-compose.yml`: local PostgreSQL development service

## Local development

Use `backend/.env.example` and `frontend/.env.example` as placeholder-only
configuration references. Start PostgreSQL with `docker compose up -d
postgres`, migrate from `backend/` with `.venv/bin/alembic upgrade head`, and
run the services with:

```bash
cd backend
.venv/bin/uvicorn app.main:app --reload
```

```bash
cd frontend
npm run dev
```

Production setup, release order, health checks, smoke tests, and rollback
guidance are documented in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).
