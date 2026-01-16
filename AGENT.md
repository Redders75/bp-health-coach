# BP Health Coach - Architecture & Design Decisions

## Overview

BP Health Coach is an AI-powered health coaching system that transforms personal health data into conversational, personalized guidance. It uses a RAG (Retrieval-Augmented Generation) architecture with multiple LLMs to provide evidence-based recommendations based on YOUR data.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interfaces                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  CLI (Typer)│  │  Streamlit  │  │  FastAPI REST API       │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
└─────────┼────────────────┼─────────────────────┼────────────────┘
          │                │                     │
          └────────────────┼─────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                           │
│  ┌──────────────────┐  ┌───────────────┐  ┌──────────────────┐  │
│  │Intent Classifier │→ │Context Retrieval│→│Conversation Mgr │  │
│  └──────────────────┘  └───────────────┘  └──────────────────┘  │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Claude 3.5    │    │    GPT-4        │    │  Llama 3.1      │
│   (Primary)     │    │  (Validation)   │    │   (Local)       │
│  Complex reason │    │  Code/JSON      │    │  Privacy/Cost   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                                 │
│  ┌─────────────────────┐         ┌─────────────────────────┐    │
│  │  SQLite Database    │         │  ChromaDB Vector Store  │    │
│  │  - daily_health_data│         │  - Semantic search      │    │
│  │  - conversations    │         │  - Similar day lookup   │    │
│  │  - 4,032 days       │         │  - Pattern matching     │    │
│  └─────────────────────┘         └─────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Multi-LLM Strategy

**Decision:** Use multiple LLMs with intelligent routing rather than a single model.

**Rationale:**
- Different models excel at different tasks
- Cost optimization (use cheaper/local models when possible)
- Privacy (sensitive queries can stay local)
- Redundancy (fallback if API unavailable)

**Implementation:**
```
Query arrives
    ↓
Privacy-sensitive? (meds, mental health)
    YES → Llama 3.1 (local)
    NO  ↓
Complexity level?
    LOW    → Llama 3.1 (cost savings)
    MEDIUM → GPT-4 (balance)
    HIGH   → Claude 3.5 (best reasoning)
```

**Current Status:**
- Claude 3.5 Sonnet: Configured and primary
- GPT-4 Turbo: Configured for validation
- Llama 3.1: Optional (requires Ollama)

### 2. Dual Database Architecture

**Decision:** Use both SQLite (structured) and ChromaDB (vector) databases.

**Rationale:**
- SQLite: Fast exact queries ("What was my BP on Jan 5?")
- ChromaDB: Semantic search ("Days similar to yesterday")
- Combined: Rich context for LLM responses

**SQLite Schema:**
```sql
daily_health_data (
    date DATE PRIMARY KEY,
    systolic_mean, diastolic_mean,  -- Blood pressure
    heart_rate_mean,                 -- Heart rate
    steps,                           -- Activity
    sleep_hours, sleep_efficiency_pct,  -- Sleep
    vo2_max,                         -- Cardio fitness
    hrv_mean,                        -- Heart rate variability
    respiratory_rate,
    active_calories, exercise_minutes,
    ...
)
```

**Vector Store:**
- Embeds daily health summaries as natural language
- Enables "find similar days" queries
- Uses sentence-transformers for embeddings

### 3. Intent Classification

**Decision:** Use regex-based intent classification for MVP.

**Rationale:**
- Fast and deterministic
- No additional API costs
- Sufficient for common query patterns
- Can upgrade to ML-based later

**Intent Types:**
| Intent | Example Query |
|--------|---------------|
| DATA_LOOKUP | "What was my BP yesterday?" |
| EXPLANATION | "Why was my BP high?" |
| PREDICTION | "What will my BP be tomorrow?" |
| SCENARIO | "What if I improve my sleep?" |
| RECOMMENDATION | "How can I lower my BP?" |
| TREND | "How has my BP changed this month?" |
| COMPARISON | "Compare this week to last week" |
| GENERAL | General health questions |

### 4. Context Retrieval Strategy

**Decision:** Multi-source context gathering for every query.

**Sources:**
1. **User Profile:** Baselines, goals, known patterns
2. **Date-Scoped Data:** Exact data for queried dates
3. **Similar Cases:** Vector search for comparable days
4. **Medical Knowledge:** Guidelines and research (future)
5. **Conversation History:** Last 10 messages for continuity

### 5. Local-First Data Storage

**Decision:** All health data stored locally, never in cloud.

**Rationale:**
- Maximum privacy for sensitive health data
- No dependency on external storage services
- User maintains full control
- GDPR-compliant by design

**Data Locations:**
- SQLite: `data/processed/health_coach.db`
- ChromaDB: `data/chroma_db/`
- Raw exports: `data/raw/` (gitignored)

### 6. Apple Health Integration

**Decision:** Parse Apple Health XML exports directly.

**Rationale:**
- Apple Health is the canonical source on iOS
- XML export contains complete history
- No need for real-time sync for MVP
- Supports all major health metrics

**Extracted Metrics:**
- Blood Pressure (Systolic/Diastolic)
- Heart Rate
- Steps
- Sleep (actual sleep time, not just "in bed")
- VO2 Max
- HRV (Heart Rate Variability)
- Respiratory Rate
- Active Calories
- Exercise Minutes

### 7. Feature Architecture

**Core Features (MVP):**

1. **Natural Language Q&A** (`src/features/query_answering.py`)
   - Ask questions in plain English
   - Get data-backed answers with citations
   - Maintains conversation context

2. **Daily Briefing** (`src/features/daily_briefing.py`)
   - Automated morning health summary
   - Yesterday's metrics + today's prediction
   - Personalized recommendations

3. **Scenario Testing** (`src/features/scenario_testing.py`)
   - "What if" analysis
   - Impact coefficients: VO2 (-1.96), Sleep (-3.1), Steps (-0.0003)
   - Feasibility and timeline estimates

### 8. Prediction Approach

**Decision:** Use empirically-derived coefficients for MVP predictions.

**Impact Coefficients (per unit change on BP):**
| Factor | Impact | Source |
|--------|--------|--------|
| VO2 Max | -1.96 mmHg per 1 mL/kg/min | Phase 2 analysis |
| Sleep | -3.1 mmHg per hour | Phase 2 analysis |
| Steps | -0.0003 mmHg per step | Phase 2 analysis |

**Future:** Train personalized ML models on user's historical data.

## Project Structure

```
bp-health-coach/
├── config/
│   ├── settings.py          # Environment & configuration
│   └── prompts/              # LLM prompt templates
├── src/
│   ├── data/
│   │   ├── database.py       # SQLite operations
│   │   └── vector_store.py   # ChromaDB operations
│   ├── llm/
│   │   ├── claude.py         # Anthropic integration
│   │   ├── gpt4.py           # OpenAI integration
│   │   ├── llama.py          # Ollama/local integration
│   │   └── router.py         # Model selection logic
│   ├── orchestration/
│   │   ├── intent_classifier.py
│   │   ├── context_retrieval.py
│   │   └── conversation_manager.py
│   ├── features/
│   │   ├── daily_briefing.py
│   │   ├── query_answering.py
│   │   └── scenario_testing.py
│   ├── models/
│   │   ├── ml_models.py      # BP prediction models
│   │   └── predictions.py    # Scenario analysis
│   ├── api/
│   │   └── main.py           # FastAPI endpoints
│   └── ui/
│       ├── cli.py            # Typer CLI
│       └── streamlit_app.py  # Web interface
├── scripts/
│   ├── setup_database.py
│   ├── import_health_data.py
│   └── parse_apple_health.py
├── data/
│   ├── raw/                  # Apple Health exports
│   ├── processed/            # SQLite database
│   └── chroma_db/            # Vector embeddings
└── tests/
```

## API Endpoints

```
POST /api/query
  Request:  { "query": "Why was my BP high?", "session_id": "..." }
  Response: { "response": "...", "intent": "EXPLANATION", "confidence": 0.95 }

GET /api/briefing
  Response: { "date": "2026-01-16", "briefing": "..." }

POST /api/scenario
  Request:  { "vo2_change": 5, "sleep_change": 1, "steps_change": 2000 }
  Response: { "predicted_bp_change": -8.2, "timeline": "4-6 weeks" }
```

## CLI Commands

```bash
# Interactive chat
python -m src.ui.cli chat

# Get today's briefing
python -m src.ui.cli briefing

# Ask a single question
python -m src.ui.cli ask "What was my BP yesterday?"

# Test a scenario
python -m src.ui.cli scenario --vo2 42 --sleep 8
```

## Environment Variables

```env
ANTHROPIC_API_KEY=sk-ant-...    # Required: Claude API
OPENAI_API_KEY=sk-...           # Optional: GPT-4 validation
DEBUG=false
LOG_LEVEL=INFO
```

## Data Pipeline

```
Apple Health Export (export.xml)
         │
         ▼
parse_apple_health.py
         │
         ▼
health_data.csv (4,032 days)
         │
         ▼
import_health_data.py
         │
    ┌────┴────┐
    ▼         ▼
SQLite    ChromaDB
```

## Cost Estimates

| Usage | Monthly Cost |
|-------|--------------|
| Daily Briefing | ~$2 |
| 10 Q&A queries/day | ~$8 |
| Weekly Report | ~$1 |
| Alerts | ~$1 |
| **Total** | **~$12/month** |

*With local Llama for simple queries: ~$5/month*

## Future Roadmap

### Phase 3B (Next)
- [ ] Multi-turn conversation improvements
- [ ] ML model training on user data
- [ ] Weekly automated reports

### Phase 3C
- [ ] Real-time alerts
- [ ] Goal tracking
- [ ] What-if scenario comparison

### Phase 3D
- [ ] Streamlit UI polish
- [ ] Mobile-friendly web interface
- [ ] Voice interface (optional)

## Security & Privacy

- All data stored locally (SQLite + ChromaDB)
- No cloud storage of health data
- API calls use HTTPS
- Sensitive queries can route to local Llama
- User can export/delete all data anytime

---

*Document Version: 1.0*
*Last Updated: January 2026*
