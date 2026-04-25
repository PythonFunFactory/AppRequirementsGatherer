# Requirements Gatherer — Setup Guide

## Prerequisites

- Python 3.12+
- Node.js 22+
- Docker + Docker Compose (for containerized deployment)

## Quick Start (Local Dev — No Docker)

### 1. Install Node.js
Download from https://nodejs.org/ (LTS version). Restart your terminal after installing.

### 2. Configure environment
```bash
cp .env.example .env
```
Edit `.env` and set your `ANTHROPIC_API_KEY`. Leave `DEV_AUTH=true` for local development.

### 3. Start the backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Backend runs at http://localhost:8000

### 4. Start the frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at http://localhost:5173

### 5. Open the app
Navigate to http://localhost:5173 — you'll see a dev login form (email + name + role).

## Docker Deployment

```bash
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY and other settings
docker compose up --build
```
App available at http://localhost:5173

## Entra ID (Production Auth)

1. Register an app in Azure Portal → App Registrations
2. Add redirect URI: `http://your-domain/auth/callback`
3. Set in `.env`:
   - `AZURE_TENANT_ID`
   - `AZURE_CLIENT_ID`  
   - `AZURE_CLIENT_SECRET`
   - `DEV_AUTH=false`

## Admin Access

Set `ADMIN_EMAILS=your@email.com` in `.env`. On first login with that email, the account is automatically granted admin role and can access `/admin`.

## PDF Generation Note

PDFs are generated via WeasyPrint, which requires system libraries (libpango, libcairo). These are pre-installed in the Docker image. For local dev on Windows, you may need to install GTK+ for Windows or use WSL.
