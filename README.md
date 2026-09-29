# NEXUS — Organizational Memory

**Every incident becomes experience. Every experience improves the next decision.**

NEXUS is an enterprise incident-intelligence MVP built around persistent organizational memory. It connects technical incident history, customer context, support/sales context and real outcomes, then uses Hindsight recall before recommending the next action.

## What makes the product different

NEXUS is not a generic chatbot. Its core loop is:

**Incident → Hindsight Recall → Decision → Actual Outcome → Retain → Next Incident**

The product deliberately records both successful and failed approaches so future recommendations can avoid repeated mistakes.

## Stack

- Frontend: React + Vite + Lucide
- Backend: FastAPI + Python
- Memory: Hindsight
- Reasoning: Groq
- Demo data: synthetic enterprise experiences

## Run locally

### 1. Backend

```powershell
cd backend
python -m pip install -r requirements.txt
copy .env.example .env
python -m uvicorn main:app --reload
```

Set real `GROQ_API_KEY` and `HINDSIGHT_API_KEY` in `.env`.

### 2. Frontend

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

Open the Vite URL shown in the terminal.

## Production configuration

Set:

```text
VITE_API_URL=https://api.your-domain.com
ALLOWED_ORIGINS=https://app.your-domain.com
```

Do not expose either API key to the browser. They belong only in the backend environment.

## API

- `GET /api/health` — dependency status
- `GET /api/experiences` — organizational memory library
- `POST /api/analyze` — recall + decision
- `POST /api/learn` — retain an observed outcome

## Demo flow

1. Analyze Incident 1.
2. Show the Hindsight evidence.
3. Explain why the recommended action is based on prior success/failure.
4. Enter the real resolution, technical result and business outcome.
5. Click **Resolve & Teach NEXUS**.
6. Open **Experience Library** to show the retained experience.
7. Load Incident 2 and analyze again.
8. Show that the next decision is informed by accumulated experience.

## Production notes

This repository is a production-oriented MVP, not a complete enterprise SaaS platform. Before commercial launch, add authentication/SSO, tenant isolation, billing, audit logs, encrypted secret management, rate limiting, observability, automated tests, a managed database if needed for application metadata, and a deployment pipeline.
