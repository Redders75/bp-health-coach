# BP Health Coach - Current Features & Usage Guide

**Version:** Phase 3B Complete
**Last Updated:** January 17, 2026

---

## Overview

The BP Health Coach is an AI-powered personal health assistant that transforms your Apple Health data into actionable insights. Instead of static charts and numbers, you can have natural conversations about your health data and receive personalized, evidence-based guidance.

### What's Working

| Component | Status | Description |
|-----------|--------|-------------|
| CLI Interface | Working | Terminal-based chat and commands |
| Streamlit Web UI | Working | Browser-based interface with 3 pages |
| FastAPI Backend | Working | REST API for integrations |
| Multi-LLM Support | Working | Claude, GPT-4, and local Llama |
| Health Data Import | Working | Apple Health XML parser |
| Vector Search | Working | Semantic search across health history |
| ML Predictions | Working | BP predictions based on lifestyle factors |

### Your Data

- **4,032 days** of health data imported (11+ years)
- **299 days** with blood pressure readings
- **1,049 days** with sleep data
- **440 days** with VO2 Max measurements

---

## Interface Options

### 1. Command Line Interface (CLI)

The CLI provides quick access from your terminal.

**Start the CLI:**
```bash
cd ~/Projects/bp-health-coach
python -m src.ui.cli
```

### 2. Streamlit Web Interface

A visual web interface with chat, briefings, and scenario testing.

**Start the web app:**
```bash
cd ~/Projects/bp-health-coach
streamlit run src/ui/streamlit_app.py
```
Then open: http://localhost:8501

### 3. FastAPI REST API

For programmatic access or building integrations.

**Start the API server:**
```bash
cd ~/Projects/bp-health-coach
uvicorn src.api.main:app --reload
```
API docs available at: http://localhost:8000/docs

---

## Feature 1: Natural Language Q&A

Ask questions about your health data in plain English. The system retrieves relevant data, analyzes patterns, and provides personalized answers.

### Example Queries

**Data Lookup - Specific Date:**
```bash
python -m src.ui.cli ask "What was my blood pressure on January 5th 2026?"
```

**Response:**
```
According to the data from January 5th, 2026, your systolic blood pressure
was recorded as 138/90 mmHg. This is within a narrow range of your average
baseline (138/90 mmHg) and slightly above your goal of <130 mmHg.

On January 5th, you took 12,453 steps (below your 15,906 baseline) and
got 9.07 hours of sleep. Consider increasing your activity level to help
lower your BP.
```

---

**Root Cause Analysis:**
```bash
python -m src.ui.cli ask "Why was my BP high last week?"
```

**Response:**
```
Looking at your data from last week, I can see a clear pattern for why
your BP was elevated on January 11th (134/87 mmHg):

**Primary Factor: Poor Sleep**
Your sleep on January 11th was only 5.39 hours - significantly below
your 7-hour goal. Based on your patterns, getting less than 6 hours
of sleep typically raises your BP by about 6.2 mmHg.

**Supporting Factors:**
- Your VO2 Max was 37.35 that day, below your baseline of 39.6
- Your HRV dropped to 21.5 on January 10th, suggesting stress

**The Good News:**
When you got proper sleep on January 10th (7.94 hours), your BP dropped
to an excellent 129/84 mmHg - below your 130 goal!

**Key Takeaway:**
Your data shows sleep is crucial for your BP control. Focus on
maintaining that 7+ hour sleep target.
```

---

**Trend Analysis:**
```bash
python -m src.ui.cli ask "How has my blood pressure been trending this month?"
```

---

**Comparison Queries:**
```bash
python -m src.ui.cli ask "Compare my BP on weekdays vs weekends"
```

---

**Health Correlations:**
```bash
python -m src.ui.cli ask "What affects my blood pressure the most?"
```

**Response:**
```
Based on your 299 days of BP data, here are the factors most correlated
with your blood pressure:

1. **VO2 Max** (r = -0.494) - Strongest factor
   Higher cardio fitness = lower BP
   Each +1 VO2 point = approximately -1.96 mmHg

2. **Sleep Duration** (r = -0.375)
   More sleep = lower BP
   Each additional hour = approximately -3.1 mmHg

3. **Daily Steps** (r = -0.187)
   More activity = lower BP
   Each +1,000 steps = approximately -0.3 mmHg

Your best BP days occur when you have: VO2 Max > 40, Sleep > 7 hrs,
Steps > 12,000.
```

---

## Feature 2: Daily Health Briefing

Get a morning summary of yesterday's health metrics and a prediction for today.

### CLI Usage

```bash
python -m src.ui.cli briefing
```

**Example Output:**
```
╭─────────────────────────── Daily Briefing ───────────────────────────╮
│ MORNING BRIEFING: Friday, January 17, 2026                           │
│                                                                      │
│ YESTERDAY'S SUMMARY:                                                 │
│ • BP: 134/87 mmHg (stage 1 hypertension)                            │
│ • Sleep: 6.5 hrs (fair) - below your 7hr goal                       │
│ • Activity: 8,834 steps - moderate                                   │
│                                                                      │
│ TODAY'S PREDICTION:                                                  │
│ Expected BP: 138/90 mmHg (±10)                                      │
│ Key factor: Sleep duration was below optimal                         │
│                                                                      │
│ RECOMMENDATIONS:                                                     │
│ 1. Prioritize 7+ hours of sleep tonight                             │
│ 2. Aim for 10,000+ steps today                                      │
│ 3. Consider a 20-minute walk after lunch                            │
╰──────────────────────────────────────────────────────────────────────╯
```

### Streamlit Usage

1. Open the web interface
2. Select "Daily Briefing" from the sidebar
3. Choose any date to see the briefing for that day
4. Click "Generate Briefing"

---

## Feature 3: What-If Scenario Testing

Test how hypothetical lifestyle changes might affect your blood pressure before committing to them.

### CLI Usage

```bash
python -m src.ui.cli ask "What if I improve my VO2 Max to 42?"
```

**Response:**
```
SCENARIO ANALYSIS: VO2 Max 37 → 42

PREDICTED IMPACT:
• BP change: -9.8/-4.9 mmHg
• Your 138/90 mmHg → predicted 128/85 mmHg
• 95% confidence interval: 124 to 134 mmHg (systolic)

TIMELINE:
• Effects show in BP after 2-3 weeks
• Full impact: 4-6 weeks
• Achievement timeframe: 8-12 weeks consistent training

FEASIBILITY: MODERATE-HIGH
• Requires increasing cardio from 2x to 4-5x per week
• Duration: 30-45 min per session

RECOMMENDATIONS:
1. Start with 3x per week cardio sessions
2. Include interval training for faster VO2 gains
3. Track progress with Apple Watch VO2 readings
```

### Streamlit Usage (Interactive Sliders)

1. Open the web interface
2. Select "Scenario Testing" from the sidebar
3. Adjust the sliders:
   - **VO2 Max:** 30 - 50
   - **Sleep Hours:** 4 - 10
   - **Daily Steps:** 2,000 - 20,000
4. Click "Analyze Scenario"
5. See predicted BP change with confidence intervals

**Example Scenario:**
```
Current Settings:
• VO2 Max: 42.0 (up from baseline 37.3)
• Sleep: 8.0 hours (up from 6.5)
• Steps: 12,000 (up from 9,000)

Results:
┌─────────────────────────────────────┐
│ Current BP:    138/90 mmHg          │
│ Predicted BP:  126/82 mmHg          │
│ BP Change:     -12.3/-8.1 mmHg  ▼   │
│                (shown in green)      │
│                                      │
│ Confidence:    122 to 130 mmHg      │
│ Timeline:      8-12 weeks           │
│ Feasibility:   Moderate             │
└─────────────────────────────────────┘
```

---

## Feature 4: Interactive Chat (Streamlit)

Have multi-turn conversations with context preserved.

### Example Conversation

**You:** "What was my BP last Tuesday?"

**Coach:** "On Tuesday, January 14th, your blood pressure was 136/88 mmHg. This is slightly above your goal of 130 mmHg but within your typical range."

**You:** "Why was it elevated?"

**Coach:** "Looking at your data for January 14th, I can see a few contributing factors:

1. **Sleep was short** - You only got 5.8 hours (vs your 7-hour goal)
2. **Lower activity** - 6,200 steps (vs your 10,000 target)
3. **It was a weekday** - Your data shows weekday BP tends to be 3-4 mmHg higher

The combination of poor sleep and low activity likely contributed to the elevated reading."

**You:** "What should I do differently?"

**Coach:** "Based on your patterns, here are three actionable steps:

1. **Prioritize sleep tonight** - Aim for 7+ hours. Your data shows this alone could reduce tomorrow's BP by 4-6 mmHg.

2. **Add a morning walk** - 20 minutes before work. This sets your activity baseline and reduces stress hormones.

3. **Evening routine** - Stop screens 30 min before bed. Your best sleep nights correlate with lower BP the next day.

Would you like me to predict what your BP would be if you hit all three targets tomorrow?"

---

## Feature 5: LLM Routing

The system automatically selects the best AI model for each query:

| Query Type | Model Used | Why |
|------------|------------|-----|
| Simple lookups | Llama 3.1 8B (local) | Fast, free, private |
| Complex analysis | Claude 3.5 Sonnet | Best reasoning |
| Data validation | GPT-4 Turbo | Structured output |
| Privacy-sensitive | Llama (local) | Data stays on device |

**Example routing:**
- "What was my BP yesterday?" → Llama (simple lookup)
- "Why has my BP been trending up?" → Claude (complex reasoning)
- "What if I improve my VO2 Max?" → Claude (scenario analysis)

---

## Quick Start Examples

### Morning Routine
```bash
# Get your daily briefing
python -m src.ui.cli briefing

# Check yesterday's details
python -m src.ui.cli ask "How did I sleep last night?"
```

### Weekly Check-in
```bash
# Review the past week
python -m src.ui.cli ask "Summarize my health metrics for the past week"

# Identify patterns
python -m src.ui.cli ask "What patterns do you see in my recent BP readings?"
```

### Goal Planning
```bash
# Test a goal
python -m src.ui.cli ask "What if I consistently sleep 8 hours?"

# Compare options
python -m src.ui.cli ask "What would help my BP more - better sleep or more exercise?"
```

### Troubleshooting High BP
```bash
# Investigate a spike
python -m src.ui.cli ask "Why was my BP 145 on Monday?"

# Find what works
python -m src.ui.cli ask "When was my BP lowest and what was I doing differently?"
```

---

## Data Import

To update your health data from Apple Health:

1. **Export from iPhone:**
   - Health App → Profile → Export All Health Data
   - Save `export.zip`

2. **Extract and parse:**
   ```bash
   unzip export.zip -d data/raw/
   python scripts/parse_apple_health.py
   ```

3. **Import to database:**
   ```bash
   python scripts/import_health_data.py --csv data/raw/health_data.csv
   ```

See `docs/apple-health-import-guide.md` for detailed instructions.

---

## Configuration

### API Keys (.env file)
```
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_openai_key
```

### Local Llama (optional)
```bash
# Install Ollama
brew install ollama

# Pull the model
ollama pull llama3.1:8b

# Verify
ollama list
```

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interfaces                         │
│  ┌─────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   CLI   │    │  Streamlit  │    │   FastAPI   │         │
│  └────┬────┘    └──────┬──────┘    └──────┬──────┘         │
└───────┼────────────────┼─────────────────┼─────────────────┘
        │                │                 │
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
│   (API)     │  │   (API)     │  │  (Local)    │
└─────────────┘  └─────────────┘  └─────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  ┌─────────────────┐        ┌─────────────────┐            │
│  │     SQLite      │        │    ChromaDB     │            │
│  │  (Structured)   │        │    (Vectors)    │            │
│  │                 │        │                 │            │
│  │ • 4,032 days    │        │ • Embeddings    │            │
│  │ • BP readings   │        │ • Semantic      │            │
│  │ • Sleep data    │        │   search        │            │
│  │ • Activity      │        │ • Similar days  │            │
│  └─────────────────┘        └─────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

## What's Coming Next (Phase 3C)

| Feature | Description |
|---------|-------------|
| Weekly Reports | Automated Monday analysis emails |
| Real-Time Alerts | Notifications for streaks, anomalies |
| Goal Tracking | Progress dashboard for BP/VO2/sleep goals |
| Scheduled Briefings | Automatic 8 AM daily briefings |

---

## Troubleshooting

**Streamlit won't start:**
```bash
# Ensure you're in the project directory
cd ~/Projects/bp-health-coach

# Check Python path
which python  # Should be your venv

# Try with explicit path
python -m streamlit run src/ui/streamlit_app.py
```

**Slow responses:**
- Ensure Ollama is running for local queries: `ollama serve`
- Check API keys are valid in `.env`

**No data showing:**
- Run the import: `python scripts/import_health_data.py --csv data/raw/health_data.csv`
- Verify: `python -c "from src.data.database import get_user_baselines; print(get_user_baselines())"`

---

**Repository:** https://github.com/Redders75/bp-health-coach
**Documentation:** See `AGENT.md` for architecture details
**Test Results:** See `docs/test-results.md` for validation
