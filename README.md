# BP Health Coach

AI-powered blood pressure health coaching system that transforms your Apple Health data into personalized, conversational guidance.

## Overview

BP Health Coach uses a RAG (Retrieval-Augmented Generation) architecture with multiple LLMs to provide:

- **Natural language Q&A** - Ask questions in plain English, get data-backed answers
- **Daily health briefings** - Personalized morning summaries with predictions
- **Weekly reports** - Comprehensive weekly analysis and action plans
- **What-if scenarios** - Test how lifestyle changes might affect your BP
- **Goal tracking** - Monitor progress toward health goals
- **Smart alerts** - Get notified about patterns and achievements
- **Predictive insights** - Forecast BP based on your habits

## Features

### Core Features (Complete)

| Feature | Description | Access |
|---------|-------------|--------|
| **Natural Language Q&A** | Ask about your health data in plain English | CLI, Web, API |
| **Daily Briefings** | Morning health summary with predictions | CLI, Web |
| **Weekly Reports** | Comprehensive weekly analysis | CLI, Web |
| **Scenario Testing** | What-if analysis for lifestyle changes | CLI, Web |
| **Goal Tracking** | Progress toward BP, VO2, sleep, steps goals | CLI, Web |
| **Smart Alerts** | Pattern detection and achievements | CLI, Web |
| **Multi-LLM Support** | Claude, GPT-4, and local Llama | Automatic routing |

### Interfaces

| Interface | Command | Best For |
|-----------|---------|----------|
| **Dashboard** | `streamlit run src/ui/streamlit_app.py` | Daily monitoring |
| **CLI** | `python -m src.ui.cli` | Quick queries |
| **API** | `uvicorn src.api.main:app` | Integrations |

## Quick Start

### Prerequisites

- Python 3.10+
- Anthropic API key (Claude)
- Optional: OpenAI API key (GPT-4), Ollama (local Llama)

### Installation

```bash
# Clone the repository
git clone https://github.com/Redders75/bp-health-coach.git
cd bp-health-coach

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your API keys
```

### Import Your Health Data

1. **Export from Apple Health:**
   - Open Health app on iPhone
   - Tap your profile → Export All Health Data
   - Transfer `export.zip` to your computer

2. **Parse and import:**
   ```bash
   # Extract the export
   unzip export.zip -d data/raw/

   # Parse Apple Health XML
   python scripts/parse_apple_health.py

   # Import to database
   python scripts/import_health_data.py --csv data/raw/health_data.csv
   ```

See `docs/apple-health-import-guide.md` for detailed instructions.

### Start the App

```bash
# Web interface (recommended)
streamlit run src/ui/streamlit_app.py
# Opens at http://localhost:8501

# Or use CLI
python -m src.ui.cli chat
```

## Usage Examples

### CLI Commands

```bash
# Interactive chat
python -m src.ui.cli chat

# Daily briefing
python -m src.ui.cli briefing

# Weekly report
python -m src.ui.cli weekly

# Ask a question
python -m src.ui.cli ask "What was my BP last Tuesday?"
python -m src.ui.cli ask "Why was my BP high last week?"

# Test a scenario
python -m src.ui.cli scenario --vo2 42 --sleep 8 --steps 12000

# View goals
python -m src.ui.cli goals

# Check alerts
python -m src.ui.cli alerts --check

# Run scheduler
python -m src.ui.cli scheduler --start
```

### Example Queries

| Query Type | Example |
|------------|---------|
| Data lookup | "What was my BP on January 5th?" |
| Root cause | "Why was my BP high yesterday?" |
| Trends | "How has my BP been trending this month?" |
| Comparisons | "Compare my BP on weekdays vs weekends" |
| Correlations | "What affects my blood pressure the most?" |
| Predictions | "What will my BP be tomorrow?" |
| Scenarios | "What if I improve my VO2 Max to 42?" |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interfaces                         │
│  ┌─────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   CLI   │    │  Streamlit  │    │   FastAPI   │         │
│  └────┬────┘    └──────┬──────┘    └──────┬──────┘         │
└───────┼────────────────┼─────────────────┼─────────────────┘
        └────────────────┼─────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Orchestration Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐    │
│  │   Intent    │  │   Context   │  │   Conversation   │    │
│  │ Classifier  │  │  Retrieval  │  │     Manager      │    │
│  └─────────────┘  └─────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Claude    │  │   GPT-4     │  │   Llama     │
│   Sonnet    │  │   Turbo     │  │  3.1 8B     │
│  (Complex)  │  │ (Validation)│  │  (Simple)   │
└─────────────┘  └─────────────┘  └─────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  ┌─────────────────┐        ┌─────────────────┐            │
│  │     SQLite      │        │    ChromaDB     │            │
│  │  (Structured)   │        │    (Vectors)    │            │
│  └─────────────────┘        └─────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Orchestration | LangChain |
| Vector DB | ChromaDB |
| SQL DB | SQLite |
| Primary LLM | Claude 3.5 Sonnet |
| Secondary LLM | GPT-4 Turbo |
| Local LLM | Llama 3.1 8B (via Ollama) |
| ML Models | scikit-learn |
| API | FastAPI |
| Web UI | Streamlit |
| CLI | Typer + Rich |
| Scheduling | schedule |

## Project Structure

```
bp-health-coach/
├── config/
│   ├── settings.py          # Configuration
│   └── prompts/              # LLM prompt templates
├── src/
│   ├── data/                 # Database & vector store
│   ├── models/               # ML prediction models
│   ├── llm/                  # LLM integrations (Claude, GPT-4, Llama)
│   ├── orchestration/        # Intent classification & context
│   ├── features/             # Core features
│   │   ├── query_answering.py
│   │   ├── daily_briefing.py
│   │   ├── weekly_report.py
│   │   ├── scenario_testing.py
│   │   ├── goal_tracking.py
│   │   └── alerts.py
│   ├── scheduler/            # Automated job scheduling
│   ├── api/                  # FastAPI endpoints
│   └── ui/                   # Streamlit & CLI interfaces
├── scripts/
│   ├── parse_apple_health.py # Apple Health XML parser
│   └── import_health_data.py # Database import
├── tests/                    # Test suite
├── data/                     # Data storage (not in git)
└── docs/                     # Documentation
```

## Configuration

### Environment Variables (.env)

```env
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional
OPENAI_API_KEY=your_openai_api_key

# Settings
DEBUG=false
LOG_LEVEL=INFO
```

### User Profile (config/settings.py)

Customize your health goals:

```python
class UserProfile:
    bp_goal = 130          # Target systolic BP
    vo2_max_goal = 43      # Target VO2 Max
    sleep_goal = 7         # Target sleep hours
    steps_goal = 10000     # Target daily steps
```

## Scheduler

The scheduler automates daily briefings, weekly reports, and alert checks:

```bash
# Run scheduler as daemon (background)
python -m src.ui.cli scheduler --start

# Run a specific job immediately
python -m src.ui.cli scheduler --run daily_briefing
python -m src.ui.cli scheduler --run weekly_report
python -m src.ui.cli scheduler --run alert_check
```

**Default Schedule:**
- Daily briefing: 8:00 AM
- Weekly report: Monday 7:00 AM
- Alert checks: Every 4 hours

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
black src/ tests/
ruff check src/ tests/
mypy src/
```

## Privacy & Security

- **Local storage**: All health data stored locally (SQLite + ChromaDB)
- **Privacy routing**: Sensitive queries routed to local Llama model
- **Encryption**: API calls use HTTPS
- **No training**: LLM providers don't use your data for training
- **Data control**: Export or delete your data anytime

## Documentation

- `docs/current-features.md` - Feature guide with examples
- `docs/apple-health-import-guide.md` - Data import instructions
- `docs/test-results.md` - Test cases and results
- `AGENT.md` - Architecture and design decisions

## Roadmap

- [x] Phase 3A: Foundation (Q&A, CLI, basic chat)
- [x] Phase 3B: Intelligence (ML predictions, scenarios)
- [x] Phase 3C: Automation (alerts, weekly reports, goals)
- [x] Phase 3D: Polish (dashboard, settings, UI improvements)
- [ ] v1.1: Voice interface, mobile app
- [ ] v2.0: Doctor reports, medication tracking

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please read the contributing guidelines first.

## Acknowledgments

Built with Claude, GPT-4, LangChain, ChromaDB, and Streamlit.

---

**Repository:** https://github.com/Redders75/bp-health-coach
