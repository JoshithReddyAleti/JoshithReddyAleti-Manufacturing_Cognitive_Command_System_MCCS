# MCCS — Extended Setup & Technical Guide

## Complete Setup Instructions (From Zero to Running)

#If you want to have a look at Product Review Document
link : https://github.com/JoshithReddyAleti/JoshithReddyAleti-Manufacturing_Cognitive_Command_System_MCCS/blob/main/PRD.md

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Backend, MCP servers, agents, cognitive layer |
| Node.js | 20+ | Next.js frontend |
| npm | 10+ | Package management for frontend |
| Git | Any | Version control |

---

## Step 1: Clone & Navigate

```bash
git clone <your-repo-url>
cd [Project_1_KIRO](https://github.com/JoshithReddyAleti/JoshithReddyAleti-Manufacturing_Cognitive_Command_System_MCCS.git)
```

---

## Step 2: Python Environment Setup

### Option A: Standard Python (Recommended)

```bash
# Install Python 3.11+ from https://www.python.org/downloads/
# Make sure to check "Add Python to PATH" during installation

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate
```

### Option B: Embeddable Python (No Admin Required — Windows)

```powershell
# Download embeddable Python
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip" -OutFile "$env:TEMP\python-embed.zip"

# Extract
Expand-Archive -Path "$env:TEMP\python-embed.zip" -DestinationPath "$env:USERPROFILE\.python311" -Force

# Enable pip
# Edit python311._pth file: uncomment "import site"
(Get-Content "$env:USERPROFILE\.python311\python311._pth") -replace '#import site','import site' | Set-Content "$env:USERPROFILE\.python311\python311._pth"

# Install pip
Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile "$env:TEMP\get-pip.py"
& "$env:USERPROFILE\.python311\python.exe" "$env:TEMP\get-pip.py"
```

---

## Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Core Libraries Explained

| Library | Version | Purpose |
|---------|---------|---------|
| `fastapi` | 0.115.6 | REST API backend serving data to Next.js |
| `uvicorn` | 0.32.1 | ASGI server to run FastAPI |
| `httpx` | 0.27.2 | Async HTTP client for calling external APIs |
| `networkx` | 3.4.2 | Causal graph (DAG) construction and traversal |
| `numpy` | 1.26.4 | Monte Carlo simulation, statistical calculations |
| `ortools` | 9.11.4210 | Google OR-Tools for constraint optimization (production allocation) |
| `pydantic` | 2.10.3 | Data validation and serialization for all models |
| `python-dotenv` | 1.0.1 | Load API keys from .env file |
| `google-genai` | latest | Google Gemini AI SDK for LLM reasoning |

### Install individually if needed:

```bash
pip install fastapi uvicorn httpx networkx numpy ortools pydantic python-dotenv google-genai
```

---

## Step 4: Node.js & Frontend Setup

```bash
# Install Node.js 20+ from https://nodejs.org/

# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Back to root
cd ..
```

### Frontend Libraries (auto-installed via npm):

| Library | Purpose |
|---------|---------|
| `next` | React framework with server-side rendering |
| `react` | UI component library |
| `tailwindcss` | Utility-first CSS framework |
| `typescript` | Type safety |

---

## Step 5: API Keys & Tokens

You need 4 API keys. All have free tiers.

### 5.1 OpenWeather API Key

- **URL:** https://openweathermap.org/api
- **Sign up:** Create free account → API Keys section
- **Free tier:** 60 calls/minute, 1,000,000 calls/month
- **Used for:** Real-time weather at manufacturing locations
- **Put in .env as:** `OPENWEATHER_API_KEY=your_key_here`

### 5.2 FRED API Key

- **URL:** https://fred.stlouisfed.org/docs/api/api_key.html
- **Sign up:** Create free account → Request API key
- **Free tier:** 120 requests/minute (very generous)
- **Used for:** Industrial Production Index, Capacity Utilization, Manufacturing Orders
- **Put in .env as:** `FRED_API_KEY=your_key_here`

### 5.3 Finnhub API Key

- **URL:** https://finnhub.io/register
- **Sign up:** Create free account → Dashboard → API Key
- **Free tier:** 60 calls/minute
- **Used for:** Real-time stock quotes for industry-specific tickers
- **Put in .env as:** `FINNHUB_API_KEY=your_key_here`

### 5.4 Google Gemini API Key

- **URL:** https://aistudio.google.com/apikey
- **Sign up:** Sign in with Google → Create API Key
- **Free tier:** 15 requests/minute, 1,500 requests/day (gemini-2.0-flash)
- **Used for:** AI reasoning, executive narratives, chatbot
- **Put in .env as:** `GEMINI_API_KEY=your_key_here`

### 5.5 No Key Required (Public APIs)

| API | URL | Notes |
|-----|-----|-------|
| GDELT Project | https://api.gdeltproject.org | Fully public, no auth |
| US BLS | https://api.bls.gov/publicAPI/v2 | Public, optional key for higher limits |
| World Bank WITS | https://wits.worldbank.org | Public data |

---

## Step 6: Configure .env File

```bash
# Copy the example
copy .env.example .env    # Windows
cp .env.example .env      # Mac/Linux

# Edit .env with your actual keys:
```

```env
# .env file contents
GEMINI_API_KEY=AIzaSy...your_key
OPENWEATHER_API_KEY=1c170c...your_key
FRED_API_KEY=ed807a...your_key
FINNHUB_API_KEY=d7ucvp...your_key
LLM_MODEL=gemini-2.0-flash
```

---

## Step 7: Run the Application

### Terminal 1 — Backend (FastAPI)

```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Terminal 2 — Frontend (Next.js)

```bash
cd frontend
npm run dev
```

You should see:
```
▲ Next.js 16.x
- Local: http://localhost:3000
✓ Ready
```

### Open in Browser

Navigate to **http://localhost:3000**

---

## Step 8: Using the Application

1. **Select an industry** from the dropdown (Semiconductor, Automotive, Pharmaceutical, etc.)
2. **Select countries** to monitor (click to toggle)
3. **Click "Run Analysis"** — watch the interactive pipeline execute
4. **Review results** — signals, scenarios, recommendations, alternatives
5. **Use the chatbot** — ask questions about the analysis
6. **View email summary** — auto-generated executive briefing

---

## Project Structure

```
Project_1_KIRO/
├── api.py                          # FastAPI backend (main entry point)
├── run_demo.py                     # CLI demo script
├── run_realtime_test.py            # API connection test
├── .env                            # API keys (not committed)
├── .env.example                    # Template for .env
├── requirements.txt                # Python dependencies
├── pyproject.toml                  # Python project config
│
├── mccs/                           # Core Python package
│   ├── __init__.py
│   ├── config/
│   │   ├── settings.py             # Global settings + thresholds
│   │   └── industries.py           # Industry-specific configurations
│   │
│   ├── mcp_servers/                # MCP Data Layer (7 servers)
│   │   ├── base.py                 # Abstract base class
│   │   ├── weather.py              # OpenWeather API
│   │   ├── economics.py            # FRED API
│   │   ├── geopolitics.py          # GDELT API
│   │   ├── trade.py                # GDELT trade analysis
│   │   ├── logistics.py            # GDELT logistics
│   │   ├── labor.py                # BLS API
│   │   └── stocks.py              # Finnhub API
│   │
│   ├── cognitive/                  # Cognitive Layer (Thinking)
│   │   ├── causal_graph.py         # 7.1 NetworkX DAG
│   │   ├── risk_propagation.py     # 7.2 Lead-time + lags + confidence
│   │   ├── simulation.py           # 7.3 Monte Carlo + OR-Tools
│   │   ├── explainability.py       # Causal chain explanations
│   │   └── llm_engine.py           # Google Gemini integration
│   │
│   ├── agents/                     # Agentic Layer (Doing)
│   │   ├── orchestrator.py         # Main pipeline coordinator
│   │   ├── signal_intelligence.py  # 8.1 Signal collection
│   │   ├── supply_chain.py         # 8.2 Supplier alternatives
│   │   ├── production_rebalancing.py # 8.3 Plant shifts
│   │   ├── financial_impact.py     # 8.4 Revenue at risk
│   │   ├── policy_safety.py        # 8.5 Rules enforcement
│   │   ├── explanation.py          # 8.6 Narrative generation
│   │   ├── alternatives.py         # 8.7 Alternative paths
│   │   ├── auto_trigger.py         # Auto-alert system
│   │   ├── chatbot.py              # Gemini chatbot
│   │   └── email_generator.py      # Email summary
│   │
│   ├── models/                     # Data Models
│   │   ├── signals.py              # Signal, Scenario, Recommendation
│   │   └── graph.py                # GraphNode, GraphEdge
│   │
│   └── ui/                         # (Legacy Streamlit components)
│       └── components.py
│
├── frontend/                       # Next.js Application
│   ├── src/app/
│   │   ├── page.tsx                # Main dashboard page
│   │   ├── layout.tsx              # Root layout
│   │   └── globals.css             # Global styles
│   ├── package.json
│   └── tailwind.config.ts
│
└── tests/                          # Test suite
    └── test_full_pipeline.py
```

---

## Troubleshooting

### "Module not found" errors
```bash
# Make sure you're in the project root
# Add project to Python path
set PYTHONPATH=.   # Windows
export PYTHONPATH=.  # Mac/Linux
```

### Gemini rate limit (429 error)
- Free tier: 15 requests/minute, 1,500/day
- System handles this gracefully — works without AI
- Fix: Wait 60 seconds, or enable billing on Google Cloud

### Finnhub returns 0 for stock price
- Market may be closed (weekends, holidays, after hours)
- Finnhub free tier has 60 calls/minute limit

### GDELT returns empty data
- Some queries may not have recent articles
- GDELT API can be slow (10-15 second responses)
- System handles timeouts gracefully

### Frontend can't connect to backend
- Make sure backend is running on port 8000
- Check CORS is enabled (it is by default in api.py)
- Try: http://localhost:8000/api/health

---

## Extending the System

### Add a new industry:
1. Add entry to `mccs/config/industries.py` with stocks, keywords, locations
2. Add alternatives to `mccs/agents/alternatives.py`
3. Add to frontend dropdown in `frontend/src/app/page.tsx`

### Add a new MCP server:
1. Create file in `mccs/mcp_servers/` extending `BaseMCPServer`
2. Implement `get_tools()`, `call_tool()`, `detect_signals()`
3. Add to `SignalIntelligenceAgent` in `mccs/agents/signal_intelligence.py`

### Add a new agent:
1. Create file in `mccs/agents/`
2. Add to orchestrator pipeline in `mccs/agents/orchestrator.py`
3. Add output to API response in `api.py`
4. Add UI section in `frontend/src/app/page.tsx`
