# Repository Knowledge Base

## Platform Snapshot
- SaaSControl-Pro is a full-stack AI data analysis platform in a single monorepo.
- Frontend: Next.js 15.3.3 + TypeScript + Tailwind CSS, running inside Firebase Studio’s managed Nix environment on port 9000.
- Backend: Two FastAPI microservice stacks (`backend-pro1`, `backend-pro2`) with API Gateway, Data Service, AI Service, and shared utilities.
- Core infrastructure: PostgreSQL, Redis, MinIO, Ray, Dockerized services, and Prometheus-based monitoring.
- AI layer: Google Genkit flows (Gemini 2.5 Flash) under `frontend/src/ai/` with contextual assistive UI components.

## Architecture & Services
- **Frontend**: App Router in `frontend/src/app`, shared UI in `frontend/src/components` (Radix UI primitives, custom variants via `cva`), hooks in `frontend/src/hooks`, and Genkit configuration in `frontend/src/ai/genkit.ts` with flows in `frontend/src/ai/flows/`.
- **Backend**: Each project folder (`backend/backend-pro1`, `backend/backend-pro2`) contains `api-gateway`, `data-service`, `ai-service`, and common packages; port windows 8000–8099 (pro1) and 8100–8199 (pro2).
- **Inter-service communication**: Frontend targets `http://localhost:8000` or `http://localhost:8100` during local integration; backend exposes REST APIs with JWT auth and optional WebSockets for real-time data.
- **UI libraries**: Radix UI is production standard. HeroUI is exploratory and blocked by Tailwind v4 requirement—use only for targeted experiments and document any forced installs.

## Environment & Ports
- **Firebase Studio (primary dev)**: Do NOT manually run `npm run dev`; the Nix runtime auto-starts the frontend preview on port 9000 as defined in `.idx/dev.nix`.
- **Manual frontend runs**: Outside Firebase Studio use `npm run dev` (port 9000), `npm run build`, and `npm start` for production mode.
- **Backend stack**: Bootstrap with `./backend/scripts/setup.sh`, then `./backend/scripts/start-dev.sh`; confirm status via `./backend/scripts/status.sh`.
- **Reserved ports**: 9000 (frontend), 8000–8099 (backend-pro1 services), 8100–8199 (backend-pro2 services). Respect allocations when adding new services.

## Database & Data Services
- Cloud PostgreSQL host `47.79.87.199:5432` (deployed 2025-09-16) backs all environments with six logical DBs: `saascontrol_{dev,stage,prod}_{pro1,pro2}`.
- Development credentials (Firebase Studio):
  - `DATABASE_URL="postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro1"`
  - `SECONDARY_DATABASE_URL="postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro2"`
- Follow the least-privilege model: staging users have restricted rights; production access requires elevated approval.
- Verification scripts: `./scripts/database/comprehensive-verification.sh` and direct `psql` commands (see `docs/DATABASE_DEPLOYMENT_REPORT.md`).
- Storage and caching: Redis and MinIO are provisioned via Docker Compose when backend stack is running.

## MCP Integration
- Claude MCP PostgreSQL servers are preconfigured for dev/staging (`postgres-docker`, `postgres-dev-pro2`, `postgres-staging-pro1`, `postgres-staging-pro2`) with gated production endpoints.
- Available MCP tools include schema discovery (`list_schemas`, `list_objects`), query execution (`execute_sql`, `explain_query`), performance diagnostics (`analyze_workload_indexes`, `get_top_queries`), and health checks (`analyze_db_health`).
- Use MCP for data introspection, workload tuning, and health monitoring; all operations are logged—treat production with extra caution.

## Development Workflow & Commands
- Run all npm scripts from repo root; scripts `dev`, `build`, `start`, `lint`, `typecheck`, `genkit:dev`, and `genkit:watch` proxy into `frontend/`.
- Backend testing and orchestration: `./scripts/ci/run-tests.sh -t backend` (ensures Postgres, Redis, MinIO, Ray availability); service-level pytest can run from each microservice root.
- Frontend tests: `npm run test`; maintain snapshots adjacent to components. Type safety enforced with `npm run typecheck` and backend `mypy`.
- Use `./scripts/ci/run-tests.sh -t frontend` for CI-aligned frontend checks.
- Respect existing lint/formatting: TypeScript with 2-space indent, PascalCase exports, kebab-case component filenames; Python formatting via `black` (line length 88) and `isort` per `pyproject.toml`.

## CI/CD & Ops
- Delivery pipeline: Firebase Studio (dev previews) → GitHub → Vercel (staging/production) → Dockerized backend services with health validation.
- Prometheus gathers metrics across microservices; security scanning integrates via Trivy during Docker builds.
- Specialized Claude agent: `.claude/agents/SaaSControl-Pro/cicd-workflow-specialist.md` owns CI/CD automation, understands port allocations, GitHub Actions tweaks, Vercel team `team_5qxA92e7EhxCquOBE7DO3lrP`, and multi-stage Docker builds.
- Common ops commands: `git push origin main` (production pipeline), `git push origin develop` (staging), `curl -f "https://[vercel-domain]/api/health"`, and `./scripts/ci/validate-saascontrol-setup.sh` for pipeline validation.

## Archive System Expectations
- `.archive/` holds historical decisions, deprecated features, experiments, releases, and incident reports. Always search archives before large changes (`find .archive/ -name "*authentication*"`, `grep -r "performance issue" .archive/...`).
- Document new architectures or deprecations in the matching subdirectories (e.g., `decisions/architecture/`, `systems/frontend/legacy-components/`).

## Additional References
- Backend deep dive: `backend/CLAUDE.md`
- Deployment details: `backend/DEPLOYMENT_GUIDE.md`
- Database rollout report: `docs/DATABASE_DEPLOYMENT_REPORT.md`
- Firebase Studio preview config: `.idx/dev.nix`
- Vercel configuration: `vercel.json`
- Monitoring stack: `monitoring/`, `docker/`, `nginx/`
- Test suites: `tests/database` for regression coverage guidance.
