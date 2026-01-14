# PRODUCT REQUIREMENTS DOCUMENT
# Phase 3: AI-Powered Blood Pressure Health Coach

**Version:** 1.0  
**Date:** January 14, 2026  
**Status:** Ready for Implementation

---

## TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [Problem & Goals](#problem-and-goals)
3. [Architecture Overview](#architecture-overview)
4. [LLM Strategy](#llm-strategy)
5. [Knowledge Base](#knowledge-base)
6. [Core Features](#core-features)
7. [Implementation Structure](#implementation-structure)
8. [Security & Privacy](#security-and-privacy)
9. [Cost Analysis](#cost-analysis)
10. [Development Roadmap](#development-roadmap)
11. [Future Evolution](#future-evolution)

---

## EXECUTIVE SUMMARY

### Product Vision
Transform 4,100 days of health data into an intelligent conversational AI health coach.

### Core Value Proposition
Instead of static charts, get:
✓ Conversational interface to YOUR data
✓ Evidence-based personalized guidance
✓ Proactive recommendations
✓ Predictive insights
✓ Continuous learning

### Success Metrics
- Daily engagement: >80%
- Implementation rate: ≥60% of recommendations
- Prediction accuracy: ±10 mmHg (80% of time)
- Health outcome: >5 mmHg BP reduction over 3 months

### Technical Summary
- **Architecture:** RAG (Retrieval-Augmented Generation)
- **Primary LLM:** Claude 3.5 Sonnet
- **Data Store:** ChromaDB (vector) + SQLite (structured)
- **Timeline:** 6-8 weeks to MVP
- **Cost:** $30-45/month ($10-15 optimized)

---

## PROBLEM AND GOALS

### Current State (Phases 1 & 2 Complete)
✅ Statistical analysis complete
✅ ML models trained  
✅ Key factors identified (VO2, Sleep, Steps)
✅ Static dashboards created

### Problems
❌ Static analysis - frozen in time
❌ Requires technical knowledge
❌ No specific guidance
❌ Reactive only (no alerts)
❌ Fragmented (multiple scripts)

### Phase 3 Goals

**MVP (Must Have):**
1. Natural Language Q&A
2. Daily Briefings (automated)
3. Pattern Explanations
4. Simple Predictions
5. Local Data Storage

**v1.1 (Should Have):**
6. What-If Scenarios
7. Weekly Reports
8. Real-Time Alerts
9. Goal Tracking
10. Conversation History

**v2.0 (Nice to Have):**
11. Voice Interface
12. Mobile App
13. Multi-User Support
14. Doctor Reports
15. Research Integration

**Explicit Non-Goals:**
❌ Medical diagnosis
❌ Prescription management
❌ Emergency detection
❌ Social features
❌ Commercial product

---

## ARCHITECTURE OVERVIEW

### High-Level Architecture

```
User Query → LangChain Orchestration → LLM Ensemble → Response

Data Sources:
├─ Personal Health Data (SQLite + ChromaDB)
├─ Medical Knowledge Base
└─ Conversation History

LLM Ensemble:
├─ Claude 3.5 Sonnet (primary reasoning)
├─ GPT-4 Turbo (validation & code)
└─ Llama 3.1 70B (local privacy)
```

### Component Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit / CLI | User interface |
| **Orchestration** | LangChain | LLM chains & agents |
| **Vector DB** | ChromaDB | Semantic search |
| **SQL DB** | SQLite | Structured data |
| **LLM Primary** | Claude 3.5 | Main reasoning |
| **LLM Secondary** | GPT-4 | Validation |
| **LLM Local** | Llama 3.1 | Privacy + cost |
| **ML Models** | scikit-learn | Predictions |

### Data Flow

```
1. User: "Why was my BP high yesterday?"
2. Intent Classification: Explanatory query, date-specific
3. Data Retrieval: 
   - Vector search: Similar past days
   - SQL query: Yesterday's exact data
   - Context: User's baselines
4. LLM Selection: Claude 3.5 (complex reasoning)
5. Prompt Construction: System + context + query
6. LLM Inference: Generate explanation
7. Post-Processing: Citations, formatting
8. Response: Natural language with evidence
9. Logging: Save conversation for context
```

---

## LLM STRATEGY

### Multi-Model Approach

**Why Multiple LLMs?**
- Different strengths for different tasks
- Cost optimization (use local when possible)
- Privacy (sensitive queries stay local)
- Redundancy (fallback if API down)

### Model Selection Decision Tree

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
    ↓
Needs code generation?
    YES → GPT-4
    NO  → Use selected model
    ↓
Medical grounding needed?
    YES → BioGPT + primary (ensemble)
    NO  → Use selected model
```

### Model Specifications

**Claude 3.5 Sonnet:**
- **Use for:** Complex reasoning, medical advice, reports
- **Cost:** $3/M input, $15/M output tokens
- **Monthly:** ~$20-30 for typical usage
- **Strengths:** Best reasoning, safety, 200K context
- **Example:** Root cause analysis, multi-factor explanations

**GPT-4 Turbo:**
- **Use for:** Validation, code generation, structured output
- **Cost:** $10/M input, $30/M output tokens  
- **Monthly:** ~$10-15 for validation tasks
- **Strengths:** Fast, JSON mode, code generation
- **Example:** Cross-check advice, generate viz code

**Llama 3.1 70B:**
- **Use for:** Simple lookups, privacy queries, cost savings
- **Cost:** FREE (local, one-time 40GB download)
- **Hardware:** Mac M1/M2 with 32GB+ RAM
- **Strengths:** Privacy, no API cost, offline capable
- **Example:** "What was my BP last Tuesday?"

### Cost Optimization Strategies

**Strategy 1: Use Local LLM for 70% of Queries**
- Simple lookups → Llama (was Claude)
- Savings: ~$20/month

**Strategy 2: Cache Common Responses**
- Daily briefing templates
- Frequent patterns
- Savings: ~$10/month

**Strategy 3: Batch Processing**
- Generate all weekly reports together
- Reduce API overhead
- Savings: ~$5/month

**Total Optimized Cost:** $10-15/month (from $30-45)

### Prompt Engineering Examples

**Template: Root Cause Analysis**
```
You are analyzing blood pressure for Andy.

USER PROFILE:
- Average BP: 142 mmHg, Goal: <130 mmHg
- Top factors: VO2 Max (r=-0.494), Sleep (r=-0.375), Steps (r=-0.187)
- Patterns: Weekend BP +4.8 mmHg, Sleep <6hrs = +6.2 mmHg

QUERY: Why was BP {value} on {date}?

DATA for {date}:
{daily_metrics}

COMPARISON (typical day):
{baseline_metrics}

SIMILAR PAST DAYS:
{similar_days}

INSTRUCTIONS:
1. Identify top 3 factors (ranked by impact)
2. Provide quantitative evidence
3. Compare to user's patterns (not population averages)
4. Give specific recommendations
5. Acknowledge uncertainty if data ambiguous
```

---

## KNOWLEDGE BASE

### Three-Tier Architecture

**Tier 1: Personal Health Data (Highest Priority)**

*SQLite Tables:*
- `daily_health_data`: 4,100 days × 46 columns
- `bp_measurements`: 299 measurements  
- `derived_features`: Stress scores, trends
- `conversations`: Chat history

*ChromaDB Collections:*
- `daily_summaries`: Natural language descriptions
- `patterns`: Identified relationships
- Example embedding: "High BP day, poor sleep, low activity"

**Tier 2: Medical Knowledge (Medium Priority)**

Content:
- AHA/ESC Hypertension Guidelines 2023
- Sleep recommendations (NSF, AASM)
- Exercise guidelines (AHA, ACSM)
- PubMed abstracts (120 curated papers)

**Tier 3: User Context (Low Priority)**

Content:
- User profile (goals, preferences)
- Conversation history
- Feedback (thumbs up/down)

### Embedding Strategy

```python
# Convert structured data to natural language
def create_daily_summary(date, data_row):
    bp = data_row['systolic_mean']
    sleep_hrs = data_row['sleep_hours']
    sleep_eff = data_row['sleep_efficiency_pct']
    steps = data_row['steps']
    
    summary = f"{date}: BP {bp} mmHg. Sleep {sleep_hrs:.1f}hrs "
              f"({sleep_eff:.0f}% efficiency). Activity {steps:,} steps."
    
    return summary

# Embed and store in ChromaDB
embedding = model.encode(summary)
collection.add(documents=[summary], embeddings=[embedding])

# Later: Semantic search
results = collection.query(
    query_texts=["high blood pressure with poor sleep"],
    n_results=5
)
```

---

## CORE FEATURES

### Feature 1: Natural Language Q&A (MVP - P0)

**Description:** Ask questions in plain English, get data-backed answers.

**Example Interaction:**

Q: "Why was my BP high yesterday?"

A: "On January 13th, your BP was 152/94 mmHg (elevated).

I analyzed your data and found three contributing factors:

1. SLEEP DISRUPTION (Primary)
   • Only 5.1 hours (vs 7hr target)
   • 8 awakenings (high for you)
   • Your data shows sleep <6hrs = +6.2 mmHg

2. LOW ACTIVITY (Secondary)  
   • 4,100 steps (vs 10k target)
   • Zero exercise
   • Your low-activity days average +5.8 mmHg

3. STRESS INDICATORS
   • Respiratory rate: 17.2 bpm (elevated)
   • HRV: 24 ms (lower than usual)

The combination explains the elevated reading."

**Implementation:**
- Intent classification via LangChain
- Multi-source data retrieval
- LLM reasoning (Claude/GPT-4/Llama based on complexity)
- Citation of specific data points
- Response in <5 seconds

### Feature 2: Daily Briefing (MVP - P0)

**Description:** Automated morning health summary at 8 AM.

**Template:**
```
🌅 MORNING BRIEFING: {date}

YESTERDAY'S SUMMARY:
• BP: {bp} mmHg ({category})
• Sleep: {hours}hrs ({efficiency}% eff) - {quality}
• Activity: {steps} steps - {activity_level}

{analysis_paragraph}

TODAY'S PREDICTION:
Expected BP: {predicted_range} mmHg
Key factor: {main_influence}

RECOMMENDATIONS:
1. {priority_1} - Impact: {impact_1}
2. {priority_2}
3. {priority_3}

{motivational_message}
```

**Implementation:**
- Scheduled job (cron) at 8 AM daily
- Gathers last 7 days data
- ML prediction for today
- Claude generates briefing
- Delivered via notification + in-app

### Feature 3: What-If Scenarios (v1.1 - P1)

**Description:** Test hypothetical changes before implementing.

**Example:**

Q: "What if I improve VO2 from 37 to 42?"

A: "SCENARIO ANALYSIS: VO2 Max 37 → 42

PREDICTED IMPACT:
• BP reduction: -9.8 mmHg (95% CI: -7.2 to -12.1)
• Your 142 mmHg → predicted 132 mmHg
• Stage 1 HTN → Elevated category

TIMELINE:
• Effects show in BP after 2-3 weeks
• Full impact: 4-6 weeks
• Achievement timeframe: 3-4 months consistent training

HOW TO ACHIEVE:
• Increase cardio from 2x to 4-5x per week
• Duration: 30-45 min per session
• Include 2 high-intensity interval sessions

EXPECTED BP TRAJECTORY:
Week 0:  142 mmHg
Week 4:  140 mmHg  
Week 8:  136 mmHg
Week 12: 132 mmHg (goal achieved)

FEASIBILITY: MODERATE-HIGH
• Time: ~3.5 hrs/week
• Difficulty: Requires 3x current effort
• Sustainability: MEDIUM (maintainable with 3-4x/week after)

Would you like a detailed 12-week training plan?"

**Implementation:**
- Loads ML models
- Counterfactual inference
- Monte Carlo simulation for confidence intervals
- LLM synthesizes findings into narrative
- Can compare multiple scenarios

### Feature 4: Weekly Report (v1.1 - P1)

**Description:** Comprehensive automated analysis every Monday.

**Sections:**
1. BP Summary & Trends
2. Root Cause Analysis
3. Positive Highlights
4. Week-Ahead Action Plan
5. Goal Progress
6. Predictions

**Delivery:**
- Email + in-app + optional PDF
- ~1500-2000 words
- Comparison to previous weeks
- Specific daily recommendations

### Feature 5: Real-Time Alerts (v1.1 - P1)

**Alert Types:**

**Streak Breaking:**
"⚠️ 3 consecutive nights <6hrs sleep. Tomorrow's BP predicted: 146-150 mmHg. Prioritize 7+ hours tonight."

**Unusual Pattern:**
"🔍 BP elevated 4 days despite good habits. Possible factors: stress? dietary changes? Monitor or consult doctor."

**Goal Achievement:**
"🎉 7 consecutive days BP <140 mmHg! Longest streak in 3 months. Keep the momentum going!"

**Implementation:**
- Rule engine checks on each data sync
- ML anomaly detection
- Prioritized (critical vs informational)
- User-configurable thresholds

### Feature 6: Goal Tracking (v1.1 - P1)

**Tracks:**
- VO2 Max progress (37.3 → 43+)
- Sleep efficiency (74% → 85%)
- Daily steps (9k → 10k)
- BP trend (142 → 130)

**Shows:**
- Current vs target
- Trend direction
- Pace estimate ("At current rate, reach goal in X weeks")
- Recommendations if off track

---

## IMPLEMENTATION STRUCTURE

### Project Directory

```
bp-health-coach/
├── config/
│   ├── settings.py
│   └── prompts/          # LLM templates
├── src/
│   ├── data/
│   │   ├── database.py
│   │   └── vector_store.py
│   ├── models/
│   │   ├── ml_models.py
│   │   └── predictions.py
│   ├── llm/
│   │   ├── claude.py
│   │   ├── gpt4.py
│   │   ├── llama.py
│   │   └── router.py
│   ├── orchestration/
│   │   ├── intent_classifier.py
│   │   ├── context_retrieval.py
│   │   └── conversation_manager.py
│   ├── features/
│   │   ├── daily_briefing.py
│   │   ├── query_answering.py
│   │   └── scenario_testing.py
│   ├── api/
│   │   └── main.py       # FastAPI
│   └── ui/
│       ├── streamlit_app.py
│       └── cli.py        # Typer CLI
├── scripts/
│   ├── setup_database.py
│   └── import_health_data.py
├── tests/
├── data/
│   ├── raw/
│   ├── processed/
│   └── chroma_db/
└── docs/
```

### Key Module: LLM Router

```python
class LLMRouter:
    def select_model(self, metadata: QueryMetadata) -> str:
        # Privacy override
        if metadata.privacy == PrivacySensitivity.SENSITIVE:
            return 'llama'
        
        # Code generation
        if metadata.requires_code:
            return 'gpt4'
        
        # Complexity-based
        if metadata.complexity == QueryComplexity.HIGH:
            return 'claude'
        elif metadata.complexity == QueryComplexity.MEDIUM:
            return 'gpt4' if not cost_mode else 'llama'
        else:
            return 'llama'  # Simple queries
```

### Key Module: Context Retrieval

```python
def retrieve_context_for_query(query, intent_type, date_scope):
    context = {
        'user_profile': get_user_profile(),
        'relevant_data': get_date_range_data(date_scope),
        'similar_cases': search_similar_days(query, n=3),
        'medical_knowledge': search_medical_refs(query),
        'conversation_history': get_recent_conversation(n=5)
    }
    return context
```

---

## SECURITY AND PRIVACY

### Data Storage
✓ All health data stored locally (no cloud)
✓ SQLite + ChromaDB on user's machine
✓ Conversations encrypted at rest
✓ API calls encrypted in transit (HTTPS)

### LLM API Usage
✓ Anthropic & OpenAI: Data not used for training
✓ No persistent storage on their servers
✓ Option to use local Llama for sensitive queries
✓ Can delete everything anytime

### Sensitive Data Handling
- Medications: Process locally with Llama
- Mental health: Process locally
- Financial info: Never included
- Personal identifiers: Anonymized in prompts

### Compliance
- No HIPAA requirements (personal use)
- GDPR-compliant (user owns all data)
- Can export data in standard formats

---

## COST ANALYSIS

### Development Costs
- Time: 6-8 weeks part-time
- External: $0 (all open-source)

### Operational Costs

**Standard Usage:**
- Claude API: $20-30/month
- GPT-4 API: $10-15/month
- Hosting: FREE (Streamlit Cloud)
- Total: $30-45/month

**Optimized Usage:**
- Use Llama for 70% of queries: -$20/month
- Cache common responses: -$10/month
- Batch processing: -$5/month
- **Optimized Total: $10-15/month**

### Cost Per Feature

| Feature | Tokens/Day | Cost/Month |
|---------|-----------|------------|
| Daily Briefing | 1,500 | $2 |
| Q&A (10 queries) | 15,000 | $8 |
| Weekly Report | 3,000 | $1 |
| Alerts (5/week) | 2,000 | $1 |
| **Total** | | **$12** |

---

## DEVELOPMENT ROADMAP

### Phase 3A: Foundation (Weeks 1-2)

**Goals:**
- Set up infrastructure
- Basic Q&A working
- Local data searchable

**Deliverables:**
- ✅ ChromaDB with health data embeddings
- ✅ Claude API integration
- ✅ Simple CLI chatbot
- ✅ Can answer basic questions

**Success Criteria:**
- Responds to "What was my BP last Tuesday?"
- <5 second response time
- Cites correct data

### Phase 3B: Intelligence (Weeks 3-4)

**Goals:**
- Add ML predictions
- Implement scenario analysis
- Pattern recognition

**Deliverables:**
- ✅ ML model integration
- ✅ What-if scenario engine
- ✅ Complex query handling
- ✅ Multi-turn conversations

**Success Criteria:**
- Can predict tomorrow's BP
- Can analyze "what if" scenarios
- Maintains conversation context

### Phase 3C: Automation (Weeks 5-6)

**Goals:**
- Daily briefings automated
- Weekly reports generated
- Alert system active

**Deliverables:**
- ✅ Scheduled briefing cron job
- ✅ Weekly report generator
- ✅ Real-time alert engine
- ✅ Goal tracking dashboard

**Success Criteria:**
- Briefing delivered at 8 AM daily
- Reports accurate and actionable
- Alerts trigger appropriately

### Phase 3D: Polish (Weeks 7-8)

**Goals:**
- UI/UX improvements
- Response quality tuning
- Testing & optimization

**Deliverables:**
- ✅ Streamlit web interface
- ✅ Improved prompts
- ✅ Edge case handling
- ✅ Performance optimization
- ✅ User testing feedback incorporated

**Success Criteria:**
- User satisfaction score ≥4/5
- All acceptance criteria met
- Ready for daily use

---

## FUTURE EVOLUTION

### v1.1 (Weeks 9-12) - Enhanced Intelligence
- Advanced scenario comparison
- Optimization suggestions ("fastest path to goal")
- Multi-user support (family)
- Export reports for doctor

### v2.0 (Months 4-6) - Mobile & Voice
- Native iOS app
- Direct Apple Health integration
- Voice interface (Siri-like)
- Real-time sync
- Push notifications

### v3.0 (Months 7-12) - Advanced AI
- LSTM for temporal patterns
- Causal inference (beyond correlation)
- Research literature integration
- Multi-modal (include photos, notes)
- Federated learning (privacy-preserving insights from others)

### v4.0 (Year 2+) - Health Ecosystem
- Integration with other health apps
- Doctor collaboration features
- Insurance report generation
- Medication tracking & reminders
- Wearable SDK for real-time analysis

### Possible Roadmap to Commercial Product

**Phase 1: Validate (Months 1-6)**
- Use personally, refine
- Beta test with 10 friends/family
- Collect feedback, iterate

**Phase 2: Polish (Months 7-12)**
- Professional UI/UX design
- HIPAA compliance review
- Security audit
- Privacy certification

**Phase 3: Launch (Year 2)**
- Freemium model ($0-20/month)
- Direct-to-consumer marketing
- Partner with cardiologists
- Clinical validation study

**Phase 4: Scale (Year 3+)**
- B2B (employers, insurers)
- Integration with EHR systems
- AI health coaching as a service
- International expansion

---

## SUCCESS CRITERIA

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Response Time | <5 sec | Instrumentation |
| Factual Accuracy | 100% | Validate vs DB |
| Relevance | 95% | Human eval |
| Actionability | 90% | Regex check |
| Uptime | 99% | Monitoring |

### User Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Daily Engagement | >80% | Usage logs |
| Implementation Rate | ≥60% | Self-reported |
| User Satisfaction | ≥4/5 | Survey |
| Retention (30 day) | >90% | Analytics |

### Health Outcome Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| BP Prediction Accuracy | ±10 mmHg (80%) | Compare actual |
| BP Reduction | >5 mmHg in 3 months | Trend analysis |
| Goal Achievement | ≥1 goal hit in 3 months | Progress tracking |

### MVP Launch Criteria (All Must Pass)

✅ Can answer 20 test questions correctly  
✅ Daily briefing delivered automatically  
✅ Response time <5 seconds (95th percentile)
✅ No data loss or corruption
✅ Privacy requirements met
✅ User can export all their data
✅ Documentation complete
✅ Beta tested by 3 users

---

## APPENDICES

### A. API Endpoints

```
POST /api/query
  Body: {query: string, session_id: string}
  Returns: {response: string, citations: array, confidence: float}

GET /api/briefing
  Returns: {date: string, content: string}

POST /api/scenario
  Body: {current_state: object, hypothetical_state: object}
  Returns: {prediction: object, feasibility: object, timeline: object}

GET /api/report/weekly
  Params: {week_start: date}
  Returns: {report: string, charts: array}
```

### B. Database Schema

```sql
CREATE TABLE daily_health_data (
    date DATE PRIMARY KEY,
    systolic_mean REAL,
    diastolic_mean REAL,
    steps INTEGER,
    sleep_hours REAL,
    sleep_efficiency_pct REAL,
    vo2_max REAL,
    stress_score REAL,
    -- ... 40+ more columns
);

CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    timestamp TIMESTAMP,
    user_query TEXT,
    assistant_response TEXT,
    llm_model TEXT,
    tokens_used INTEGER,
    cost_usd REAL
);
```

### C. Testing Strategy

**Unit Tests:**
- Database queries
- Data preprocessing
- LLM routing logic
- Prompt construction

**Integration Tests:**
- End-to-end query flow
- LLM API calls
- ChromaDB searches
- Multi-turn conversations

**User Acceptance Tests:**
- 20 predefined Q&A scenarios
- Daily briefing generation
- Scenario analysis accuracy
- Report generation

---

## CONCLUSION

Phase 3 transforms static health data analysis into a dynamic, conversational AI coach. By combining:
- Multiple specialized LLMs
- Rich personal health data
- Medical knowledge base
- Predictive ML models

We create a system that provides:
- Daily personalized guidance
- Evidence-based recommendations
- Predictive insights
- Natural language interaction

**Timeline:** 6-8 weeks to production MVP
**Cost:** $10-15/month (optimized)
**Value:** Actionable health insights based on YOUR data

**Next Step:** Begin Phase 3A (Foundation) implementation.

---

**Document Prepared By:** Andy Redfearn  
**Review Status:** Ready for Implementation  
**Last Updated:** January 14, 2026  
**Version:** 1.0
