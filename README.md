# BP Health Coach

AI-powered blood pressure health coaching system that transforms health data into personalized, conversational guidance.

## Overview

BP Health Coach uses a RAG (Retrieval-Augmented Generation) architecture with multiple LLMs to provide:

- Natural language Q&A about your health data
- Daily personalized health briefings
- Predictive insights and what-if scenario analysis
- Evidence-based recommendations based on YOUR data

## Features

### MVP (Phase 3A-3B)
- **Natural Language Q&A**: Ask questions in plain English, get data-backed answers
- **Daily Briefings**: Automated morning health summaries
- **Pattern Explanations**: Understand why your BP fluctuates
- **Simple Predictions**: Forecast tomorrow's BP based on today's habits

### Coming Soon (Phase 3C-3D)
- What-if scenario testing
- Weekly reports
- Real-time alerts
- Goal tracking

## Tech Stack

| Component | Technology |
|-----------|------------|
| Orchestration | LangChain |
| Vector DB | ChromaDB |
| SQL DB | SQLite |
| Primary LLM | Claude 3.5 Sonnet |
| Secondary LLM | GPT-4 Turbo |
| Local LLM | Llama 3.1 70B (optional) |
| API | FastAPI |
| Web UI | Streamlit |
| CLI | Typer + Rich |

## Project Structure

```
bp-health-coach/
├── config/
│   ├── settings.py          # Configuration
│   └── prompts/              # LLM prompt templates
├── src/
│   ├── data/                 # Database & vector store
│   ├── models/               # ML prediction models
│   ├── llm/                  # LLM integrations
│   ├── orchestration/        # Intent & context management
│   ├── features/             # Core features
│   ├── api/                  # FastAPI endpoints
│   └── ui/                   # Streamlit & CLI
├── scripts/                  # Setup & import scripts
├── tests/                    # Test suite
├── data/                     # Data storage
└── docs/                     # Documentation
```

## Installation

### Prerequisites
- Python 3.10+
- API keys for Anthropic (Claude) and OpenAI (GPT-4)
- Optional: Ollama for local Llama model

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/bp-health-coach.git
cd bp-health-coach
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. Initialize the database:
```bash
python scripts/setup_database.py
```

6. Import your health data:
```bash
python scripts/import_health_data.py --csv path/to/your/data.csv
```

## Usage

### CLI Interface

Start interactive chat:
```bash
python -m src.ui.cli chat
```

Get today's briefing:
```bash
python -m src.ui.cli briefing
```

Ask a single question:
```bash
python -m src.ui.cli ask "What was my BP yesterday?"
```

Test a scenario:
```bash
python -m src.ui.cli scenario --vo2 42 --sleep 8
```

### Web Interface

```bash
streamlit run src/ui/streamlit_app.py
```

### API Server

```bash
uvicorn src.api.main:app --reload
```

API endpoints:
- `POST /api/query` - Ask a question
- `GET /api/briefing` - Get daily briefing
- `POST /api/scenario` - Test what-if scenario

## Configuration

Set these environment variables in `.env`:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
DEBUG=false
LOG_LEVEL=INFO
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/ tests/
ruff check src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Privacy & Security

- All health data is stored locally (SQLite + ChromaDB)
- Sensitive queries can be routed to local Llama model
- API calls use HTTPS encryption
- No data is used for LLM training

## License

MIT License - see LICENSE file for details.

## Acknowledgments

Built with Claude, GPT-4, LangChain, and ChromaDB.
