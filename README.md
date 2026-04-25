# Requirements Gatherer

A web application that guides users through a structured conversation to capture software requirements, then generates a formatted PDF document. Built with Vue 3 + FastAPI, powered by Claude.

## Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3, Vite, Tailwind CSS (shadcn-style components) |
| Backend | FastAPI (Python 3.11+) |
| Database | SQLite (via SQLAlchemy) |
| LLM | Claude (claude-sonnet-4-6) |
| Auth | Microsoft Entra ID (Azure AD) |
| PDF | fpdf2 |
| Deployment | Docker Compose |

## Quick Start

See [SETUP.md](SETUP.md) for full instructions. The short version:

```powershell
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Set `DEV_AUTH=true` in `.env` to bypass Entra ID during local development.

---

## To-Do

### High Priority

- [ ] **Azure AI Foundry integration** — Refactor `backend/app/services/claude_service.py` to call Claude through an Azure AI Foundry endpoint using the `azure-ai-inference` SDK and `DefaultAzureCredential`, replacing the direct Anthropic API dependency. Update `requirements.txt` and `.env` accordingly (`AZURE_AI_FOUNDRY_ENDPOINT`, `AZURE_AI_FOUNDRY_MODEL`).

- [ ] **Complete Entra ID auth** — The OIDC callback in `backend/app/routers/auth.py` decodes the ID token without verifying the signature. Before production, validate the token against the Entra ID JWKS endpoint (the `get_entra_public_keys()` helper in `auth_service.py` is already stubbed for this). Also wire up `@azure/msal-browser` in the frontend `LoginView.vue` for the production sign-in flow.

- [ ] **Set `DEV_AUTH=false` before deployment** — The login form defaults to dev mode. Confirm `DEV_AUTH=false` and all three `AZURE_*` env vars are set in the production `.env`.

### Medium Priority

- [ ] **Production secret hardening** — Replace the default `SECRET_KEY` in `.env` with a securely generated random string before deploying. Consider rotating it on a schedule.

- [ ] **HTTPS / reverse proxy** — Add an nginx or Caddy config for TLS termination in front of the Docker stack. The current nginx config (`frontend/nginx.conf`) is HTTP-only.

- [ ] **Fix `ADMIN_EMAILS`** — Update `ADMIN_EMAILS` in `.env` from the placeholder to real administrator email addresses.

- [ ] **Rate limiting** — The message endpoint (`POST /sessions/{id}/messages`) calls Claude on every request with no throttling. Add per-user rate limiting (e.g., `slowapi`) before exposing publicly.

- [ ] **Session titles for non-ASCII** — The title truncation in `messages.py` slices by character index which can split multi-byte characters. Use a proper Unicode-safe truncation.

### Nice to Have

- [ ] **Streaming error recovery** — If the SSE stream drops mid-response, the partial assistant message is lost. Consider persisting the partial content and allowing retry.

- [ ] **Dev auth hardcoded fallback** — `LoginView.vue` has `|| true` after the env var check, meaning dev mode is always on regardless of the env var. Remove the `|| true` once `VITE_DEV_AUTH` is properly set in the Vite env config.

- [ ] **PDF regeneration** — Currently clicking "Generate PDF" on a completed session overwrites the existing PDF silently. Consider prompting the user or versioning the files.

- [ ] **Admin session filtering** — The admin panel fetches all sessions before filtering in the frontend. Move filtering to the backend query for large datasets.

- [ ] **Automated tests** — No test suite exists yet. Priority areas: auth token validation, PDF generation, Claude service streaming mock.

- [ ] **Docker healthcheck** — Add a `healthcheck` to the backend service in `docker-compose.yml` so the frontend container waits for the API to be ready.
