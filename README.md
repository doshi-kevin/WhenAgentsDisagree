# When Agents Disagree: Multi-Agent Conflict Resolution Platform

A research platform for studying how different conflict resolution strategies affect accuracy, efficiency, and behavior in multi-LLM agent systems when agents receive contradictory instructions or evidence.

Built as a CS584 course project.

## Research Question

> How do different conflict resolution strategies affect the accuracy, efficiency, and behavior of multi-LLM agent systems when agents are given contradictory instructions or evidence?

## Features

- **Four conflict resolution strategies** implemented as LangGraph workflows:
  - **Majority Voting** &mdash; Independent agent votes with confidence-based tie-breaking
  - **Structured Debate** &mdash; Multi-round argumentation with judge-mediated deadlock resolution
  - **Hierarchical Authority** &mdash; Subordinate briefs reviewed by a lead agent who issues binding decisions
  - **Evidence-Weighted Consensus** &mdash; Peer-ranked source reliability scores weight each agent's vote

- **Rich per-turn metrics**: aggressiveness, sentiment, persuasion, citation quality, argument novelty, hedging, and word count

- **Deadlock detection** using sentence-transformer embeddings (cosine similarity > 0.90 threshold)

- **Real-time debate streaming** via Server-Sent Events (SSE)

- **Batch experiment runner** for multi-scenario, multi-strategy experiments with aggregated statistics

- **Admin dashboard** with strategy comparison charts, model comparison, per-debate deep-dive analysis, and data export

## Tech Stack

### Backend

| Component | Technology |
|---|---|
| Web Framework | FastAPI |
| LLM Orchestration | LangGraph + LangChain |
| LLM Providers | Groq, Cerebras, OpenRouter |
| Models | Llama 3.3 70B, Llama 3.1 8B, Nemotron 120B |
| Database | SQLite (async via SQLAlchemy + aiosqlite) |
| Semantic Metrics | sentence-transformers (all-MiniLM-L6-v2) |
| Streaming | SSE (sse-starlette) |

### Frontend

| Component | Technology |
|---|---|
| Framework | Next.js (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS |
| Charts | Recharts |
| Data Fetching | SWR |
| Real-time | EventSource (SSE) |

## Project Structure

```
├── backend/
│   └── app/
│       ├── main.py                # FastAPI app entry point
│       ├── config.py              # Settings and environment variables
│       ├── api/                   # REST + SSE endpoints
│       ├── agents/                # BaseAgent, ConflictAgent, JudgeAgent, prompts
│       ├── graphs/                # LangGraph workflows (one per strategy)
│       ├── llm/                   # LLM provider factory, model registry, rate limiter
│       ├── metrics/               # Per-turn metric analyzers and aggregation
│       ├── services/              # Debate runner and experiment orchestration
│       ├── scenarios/             # JSON scenario loader
│       └── db/                    # SQLAlchemy models, CRUD, schemas
│   └── data/scenarios/            # Scenario JSON files
│
└── frontend/src/
    ├── app/                       # Next.js pages (home, debate viewer, admin)
    ├── components/                # UI components
    ├── hooks/                     # useDebateStream SSE hook
    └── lib/                       # API client, types, constants, utils
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- API key for at least one provider: [Groq](https://console.groq.com/), [Cerebras](https://cloud.cerebras.ai/), or [OpenRouter](https://openrouter.ai/)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

Create a `.env` file in `backend/`:

```env
GROQ_API_KEY=your_groq_key
CEREBRAS_API_KEY=your_cerebras_key
OPENROUTER_API_KEY=your_openrouter_key
DATABASE_URL=sqlite+aiosqlite:///./data/experiments.db
```

Start the server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

On first startup, the database is created automatically and scenarios are loaded from the JSON files.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:3000` and connects to the backend at `http://localhost:8000`.

## Usage

### Running a Debate

1. Open `http://localhost:3000`
2. Select a conflict scenario
3. Choose a resolution strategy
4. Select models (one per agent, minimum 3)
5. Click **Run Debate** to watch agents argue in real-time

### Running Batch Experiments

Navigate to the Admin panel at `/admin/experiments` to configure multi-scenario, multi-strategy batch runs and compare results across the strategy and model comparison dashboards.

## Scenario Categories

| Category | Description |
|---|---|
| Instruction Conflicts | Agents given conflicting directives on ethical/business dilemmas |
| Factual Contradictions | Agents given conflicting factual claims |
| Evidence Quality | Agents given sources of varying reliability |
