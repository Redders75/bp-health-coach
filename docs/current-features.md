# BP Health Coach - Current Features & Usage Guide

**Version:** Phase 3D Complete (v1.0)
**Last Updated:** January 17, 2026

---

## Overview

The BP Health Coach is an AI-powered personal health assistant that transforms your Apple Health data into actionable insights. Instead of static charts and numbers, you can have natural conversations about your health data and receive personalized, evidence-based guidance.

### What's Working

| Component | Status | Description |
|-----------|--------|-------------|
| CLI Interface | Working | Terminal-based chat and commands |
| Streamlit Web UI | Working | Browser-based interface with 8 pages |
| FastAPI Backend | Working | REST API for integrations |
| Multi-LLM Support | Working | Claude, GPT-4, and local Llama |
| Health Data Import | Working | Apple Health XML parser |
| Vector Search | Working | Semantic search across health history |
| ML Predictions | Working | BP predictions based on lifestyle factors |
| Weekly Reports | Working | Comprehensive weekly health analysis |
| Goal Tracking | Working | Progress toward BP, VO2, sleep, steps goals |
| Alert System | Working | Pattern detection and notifications |
| Scheduler | Working | Automated briefings and alert checks |
| Dashboard | Working | Health overview with metrics and charts |
| Settings | Working | User profile and preferences configuration |

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

A visual web interface with 8 pages: Dashboard, Chat, Daily Briefing, Weekly Report, Goals, Scenarios, Alerts, and Settings.

**Start the web app:**
```bash
cd ~/Projects/bp-health-coach
streamlit run src/ui/streamlit_app.py
```
Then open: http://localhost:8501

**Available Pages:**
| Page | Description |
|------|-------------|
| Dashboard | Health overview with BP trend, goals preview, and today's briefing |
| Chat | Interactive conversation with the health coach |
| Daily Briefing | Morning summary with yesterday's data and today's prediction |
| Weekly Report | Comprehensive weekly analysis with trends and action plan |
| Goals | Progress tracking for BP, VO2 Max, sleep, and steps goals |
| Scenarios | What-if analysis for lifestyle changes |
| Alerts | Health notifications and pattern warnings |
| Settings | User profile, AI preferences, and notification settings |

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

## Feature 6: Weekly Health Reports

Get comprehensive weekly analysis every Monday with trends, patterns, and action plans.

### CLI Usage

```bash
python -m src.ui.cli weekly
```

**Example Output:**
```
WEEKLY HEALTH REPORT: January 05 - January 11, 2026

1. BLOOD PRESSURE SUMMARY
Average: 137/90 mmHg
Range: 129/81 - 146/97 mmHg
Variability: ±6.1 mmHg (systolic)
Days with readings: 7/7
Status: 7 mmHg above your 130 mmHg goal

2. SLEEP ANALYSIS
Average: 7.4 hours/night
Range: 5.4 - 9.1 hours
Days under 7 hours: 2/7
vs Previous Week: +0.3 hours ↑

3. ACTIVITY SUMMARY
Daily Average: 18,316 steps
Weekly Total: 128,211 steps
Days over 10,000: 7/7

4. FITNESS (VO2 MAX)
Current: 37.4 mL/kg/min
Goal: 43.0 mL/kg/min

5. KEY INSIGHTS
BEST DAY: 2026-01-10
- BP: 129/81 mmHg
- Sleep: 7.9 hours
- Steps: 21,056

CHALLENGING DAY: 2026-01-07
- BP: 146/94 mmHg
- Sleep: 6.5 hours
- Steps: 26,335

6. ACTION PLAN FOR NEXT WEEK
1. Focus on BP Reduction - Average BP is 7 mmHg above goal
2. Add Cardio Sessions - VO2 Max is your strongest BP predictor
3. Replicate Your Best Day - Follow the same sleep/activity pattern
```

### Streamlit Usage

1. Navigate to "Weekly Report" page
2. Select the week ending date
3. Click "Generate Report"
4. View raw statistics in expandable section

---

## Feature 7: Goal Tracking Dashboard

Track progress toward your health goals with visual progress bars, trends, and projections.

### CLI Usage

```bash
python -m src.ui.cli goals
```

**Example Output:**
```
╔══════════════════════════════════════════════════════════════╗
║                    GOAL TRACKING DASHBOARD                    ║
╚══════════════════════════════════════════════════════════════╝

Overall Status: ⚠️ AT_RISK
Goals: 0/4 achieved, 2 on track

────────────────────────────────────────────────────────────

✅ Blood Pressure
   Current: 131/84 mmHg → Target: 130 mmHg (systolic)
   Progress: [█████████████████░░░] 86%
   Trend: ↓ decreasing (-8.5/month)
   Projection: At current rate, goal in ~1 weeks

○ VO2 Max
   Current: 37.4 mL/kg/min → Target: 43.0 mL/kg/min
   Progress: [░░░░░░░░░░░░░░░░░░░░] 0%
   Trend: → stable (-0.7/month)

○ Sleep Duration
   Current: 6.7 hours → Target: 7.0 hours
   Progress: [░░░░░░░░░░░░░░░░░░░░] 0%
   Trend: → stable (-0.3/month)

✅ Daily Steps
   Current: 19,588 steps → Target: 10,000 steps
   Progress: [████████████░░░░░░░░] 61%
   Trend: ↑ increasing (+1,502/month)
```

### Goals Tracked

| Goal | Target | Direction |
|------|--------|-----------|
| Blood Pressure | 130 mmHg (systolic) | Lower is better |
| VO2 Max | 43 mL/kg/min | Higher is better |
| Sleep Duration | 7 hours | Higher is better |
| Daily Steps | 10,000 steps | Higher is better |

### Streamlit Usage

1. Navigate to "Goals" page
2. View overall status and progress summary
3. Click individual goals for detailed tips and recommendations

---

## Feature 8: Smart Alerts

Get notified about health patterns, achievements, and concerns.

### CLI Usage

```bash
# Check for new alerts
python -m src.ui.cli alerts --check

# View recent alerts
python -m src.ui.cli alerts
```

### Alert Types

| Alert | Trigger | Priority |
|-------|---------|----------|
| Sleep Streak Warning | 3+ nights under 6 hours | Warning |
| BP Spike | BP > 2 std devs above average | Warning |
| BP Excellent | BP > 2 std devs below average | Celebration |
| BP Goal Streak | 7 or 14 days under goal | Celebration |
| Activity Streak | 7 days with 10k+ steps | Celebration |
| Trend Warning | BP increased 5+ mmHg week-over-week | Warning |
| Trend Positive | BP decreased 5+ mmHg week-over-week | Celebration |
| Unusual Pattern | Elevated BP despite good habits | Warning |

### Streamlit Usage

1. Navigate to "Alerts" page
2. Click "Check for New Alerts"
3. View alerts with priority indicators
4. Dismiss acknowledged alerts

---

## Feature 9: Automated Scheduler

Schedule automatic briefings, reports, and alert checks.

### CLI Usage

```bash
# View available jobs
python -m src.ui.cli scheduler

# Run a job manually
python -m src.ui.cli scheduler --run daily_briefing
python -m src.ui.cli scheduler --run weekly_report
python -m src.ui.cli scheduler --run alert_check

# Start scheduler daemon (background)
python -m src.ui.cli scheduler --start
```

### Default Schedule

| Job | Schedule | Description |
|-----|----------|-------------|
| Daily Briefing | 8:00 AM | Morning health summary |
| Weekly Report | Monday 7:00 AM | Comprehensive weekly analysis |
| Alert Check | Every 4 hours | Pattern detection |

---

## Feature 10: Dashboard (Streamlit)

A visual overview of your health status, accessible from the Streamlit web interface.

### Dashboard Components

1. **Today's Metrics** - Current BP, sleep, steps, VO2 Max with goal comparisons
2. **BP Trend Chart** - 30-day blood pressure visualization
3. **Goals Preview** - Top 2 goals with progress bars
4. **Today's Briefing** - Abbreviated daily summary
5. **Quick Actions** - Links to detailed pages

### Usage

1. Start Streamlit: `streamlit run src/ui/streamlit_app.py`
2. Dashboard is the default landing page
3. Click metrics or buttons to navigate to detailed views

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

## What's Coming Next (Future Versions)

| Feature | Target Version | Description |
|---------|----------------|-------------|
| Voice Interface | v1.1 | Ask questions using voice commands |
| Mobile App | v1.1 | iOS/Android companion app |
| Doctor Reports | v2.0 | Generate PDF reports for healthcare provider visits |
| Medication Tracking | v2.0 | Log medications and see impact on BP |
| Family Sharing | v2.0 | Share progress with family members |
| Apple Watch Complication | v2.0 | Quick BP status on watch face |

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
