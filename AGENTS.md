# Repository Guidelines

## Project Structure & Module Organization

CivicMirror is a full-stack project. Django code lives in `backend/`, with apps such as `accounts`, `elections`, `integrations`, `results`, and `voting`. Shared backend tests are in `backend/tests/`; app-local tests are `tests.py`. React/Vite code lives in `frontend/src/`, organized by `api`, `components`, `hooks`, `pages`, `schemas`, `store`, `types`, and `utils`. Infrastructure is in `terraform/`, research notes are in `docs/`, and local orchestration is in `docker-compose.yml`.

## Build, Test, and Development Commands

- `docker compose up`: starts Postgres, Redis, Django, Celery, and Celery Beat.
- `cd backend && python manage.py runserver`: runs the Django API when dependencies and services are already available.
- `cd backend && pytest`: runs backend tests using `config.settings.dev`.
- `cd frontend && npm install`: installs frontend dependencies.
- `cd frontend && npm run dev`: starts the Vite dev server.
- `cd frontend && npm run build`: type-checks with `tsc -b` and builds the production frontend.
- `cd frontend && npm run typecheck`: runs TypeScript checks without emitting a build.

## Coding Style & Naming Conventions

Use TypeScript for frontend code and Python for backend code. Frontend files use `PascalCase` for React pages/components (`RaceDetailPage.tsx`) and `camelCase` for hooks, stores, utilities, and API clients (`useAuth.ts`, `civicApiClient.ts`). Keep domain logic in `utils`, API calls in `api`, and shared types in `types`. Backend modules follow Django conventions: `models.py`, `serializers.py`, `views.py`, `urls.py`, and `tasks.py`. Keep formatting consistent with surrounding code; frontend ESLint covers TypeScript, React Hooks, and Vite React Refresh.

## Testing Guidelines

Backend tests use `pytest` and `pytest-django`; files must match `tests.py`, `test_*.py`, or `*_tests.py`. Add tests near the feature owner for model, serializer, service, and API behavior; use `backend/tests/` for cross-app coverage. There is no frontend test runner configured yet, so validate frontend changes with `npm run typecheck` and `npm run build`.

## Commit & Pull Request Guidelines

Recent history uses conventional-style commits such as `feat(coverage): add NC to full coverage tier` and `fix(format): add timeZone: UTC...`. Prefer `type(scope): summary`; keep it imperative and specific. Pull requests should include a clear description, linked issue when applicable, test/build commands run, screenshots for UI changes, and notes for migrations, environment variables, or external API behavior.

## Security & Configuration Tips

Do not commit secrets. Backend local configuration should come from `backend/.env`; Terraform examples belong in `terraform/*.example` files. For election-data integrations and scheduled tasks, document source assumptions, rate limits, and required API keys.
