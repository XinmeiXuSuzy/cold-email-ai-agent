# Cold Email Agent

An AI-powered full-stack cold email assistant. Research prospects, generate personalized drafts with DSPy, review and edit before sending, and track memory across your entire outreach — all from a clean dashboard.

---

## Stack

| Layer | Tech |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy (async) |
| AI | LiteLLM, DSPy |
| Database | PostgreSQL + pgvector |
| Observability | Langfuse |
| Frontend | Next.js 14, React, Tailwind CSS |
| Infra | Docker Compose (local), Render + Supabase + Vercel (prod) |

---

## Architecture

```
frontend (Next.js)
  └─ calls → backend (FastAPI)
               ├─ /prospects     → prospect CRUD + CSV upload + research
               ├─ /emails        → generate (DSPy) + edit + send + feedback
               └─ /analytics     → aggregate stats

backend services
  ├─ research_service    → LiteLLM + memory RAG → ResearchSummary
  ├─ email_generator     → DSPy pipeline → EmailDraft + Langfuse trace
  ├─ memory_service      → pgvector semantic search
  ├─ email_sender        → SMTP or mock
  └─ evaluation_service  → LLM-as-judge scoring

database (PostgreSQL + pgvector)
  ├─ prospects
  ├─ research_summaries  (with embeddings)
  ├─ email_drafts
  ├─ sent_emails
  ├─ memory_items        (with embeddings)
  └─ feedback_events
```

---

## Quickstart (Docker Compose)

### 1. Clone and configure

```bash
cp .env.example .env
# Fill in your OPENAI_API_KEY (required)
# Optionally add LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY
```

### 2. Start all services

```bash
docker compose up --build
```

This starts:
- PostgreSQL with pgvector on port 5432
- FastAPI backend on port 8000
- Next.js frontend on port 3000

### 3. Open the app

```
http://localhost:3000
```

API docs at `http://localhost:8000/docs`.

### 4. Seed sample data (optional)

```bash
docker compose exec backend python -m seed.seed_data
```

---

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start a local Postgres with pgvector (or use Supabase)
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/cold_email"
export OPENAI_API_KEY="sk-..."

uvicorn app.main:app --reload
```

Run migrations:

```bash
alembic upgrade head
```

Run tests:

```bash
pytest tests/ -v
```

### Frontend

```bash
cd frontend
npm install
cp ../.env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
```

---

## CSV Import Format

Upload prospects in bulk from the Prospects page. Required columns: `name`, `email`.

Optional: `role`, `company`, `industry`, `website`, `linkedin_url`, `notes`

Sample file at `backend/seed/sample_prospects.csv`.

---

## Email Generation Pipeline (DSPy)

Each email is generated as a structured multi-step pipeline:

1. **Subject line** — short, personalized, under 60 chars
2. **Opening line** — specific to the prospect, no clichés
3. **Body** — 2-3 paragraphs, value-driven, tone-matched
4. **CTA** — clear, low-friction ask
5. **Follow-up** — shorter version for non-responders

Tone options: `concise` · `warm` · `direct` · `consultative` · `casual`

---

## Memory & RAG

Every research summary, sent email, and edited draft is saved as a `MemoryItem` with a 1536-dim embedding via `text-embedding-3-small`. Before generating each email, the system:

1. Retrieves semantically similar past outreach using pgvector cosine similarity
2. Retrieves prospect-specific history
3. Injects both into the DSPy pipeline as context

This helps avoid repetition and improves personalization over time.

---

## Observability (Langfuse)

Every generation run creates a Langfuse trace with:
- Prompt inputs and completions
- Token usage per step
- Auto-eval scores (personalization, clarity, spamminess, factual consistency)

Set `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` in `.env` to enable.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/prospects` | Create prospect |
| POST | `/prospects/upload` | Import CSV |
| GET | `/prospects` | List (paginated, filterable) |
| GET | `/prospects/{id}` | Get prospect |
| PATCH | `/prospects/{id}` | Update prospect |
| DELETE | `/prospects/{id}` | Delete prospect |
| POST | `/prospects/{id}/research` | Run research enrichment |
| GET | `/prospects/{id}/research` | Get latest research |
| POST | `/emails/generate` | Generate email draft |
| GET | `/emails` | List drafts |
| GET | `/emails/{id}` | Get draft |
| PATCH | `/emails/{id}` | Edit draft |
| POST | `/emails/send` | Send draft |
| GET | `/emails/sent` | List sent emails |
| PATCH | `/emails/sent/{id}/reply-status` | Update reply status |
| POST | `/emails/{id}/feedback` | Submit feedback |
| GET | `/analytics` | Aggregate stats |

---

## Deployment

### Backend → Render

1. Connect GitHub repo to Render
2. Set build command: `pip install -r requirements.txt && alembic upgrade head`
3. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables from `.env`

### Database → Supabase

1. Create a Supabase project
2. Enable pgvector: `CREATE EXTENSION vector;`
3. Set `DATABASE_URL` to your Supabase connection string

### Frontend → Vercel

1. Connect GitHub repo to Vercel
2. Set `NEXT_PUBLIC_API_URL` to your Render backend URL
3. Deploy

---

## Data Models

| Model | Purpose |
|---|---|
| `Prospect` | Contact record with outreach status |
| `ResearchSummary` | LLM-generated context with embedding |
| `EmailDraft` | Generated + editable email with tone/status |
| `SentEmail` | Delivery record with reply tracking |
| `MemoryItem` | Semantic memory store (embeddings) |
| `FeedbackEvent` | User ratings + auto-eval scores |

---

## Project Structure

```
cold-email-agent/
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app
│   │   ├── config.py           # Settings (pydantic)
│   │   ├── database.py         # Async engine + session
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── routers/            # FastAPI route handlers
│   │   ├── services/           # Business logic
│   │   └── dspy_modules/       # DSPy pipeline
│   ├── migrations/             # Alembic migrations
│   ├── seed/                   # Sample data + CSV
│   └── tests/                  # Pytest smoke tests
└── frontend/
    ├── app/                    # Next.js App Router pages
    ├── components/             # React components
    └── lib/                    # API client + utils
```
