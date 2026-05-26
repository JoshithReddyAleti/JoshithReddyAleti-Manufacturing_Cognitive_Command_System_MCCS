# Manufacturing Cognitive Command System (MCCS)

Enterprise-wide disruption intelligence & autonomous replanning.

## Overview

MCCS detects early disruption signals across the manufacturing value chain, reasons about cross-domain impacts using causal graphs, simulates future scenarios, and recommends optimal responses with transparent explanations.

## Architecture

```
┌────────────────────────────────────────────┐
│ Public Data Sources (via MCP servers)       │
├────────────────────────────────────────────┤
│ Weather │ Tariffs │ News │ Logistics │ Eco │
└──────────────────────┬─────────────────────┘
                       │
           ┌───────────▼───────────┐
           │ Signal Intelligence    │  ← Agentic
           └───────────┬───────────┘
                       │
           ┌───────────▼───────────┐
           │ Causal Graph Reasoning │  ← Cognitive
           └───────────┬───────────┘
                       │
           ┌───────────▼───────────┐
           │ Counterfactual Sim     │  ← Cognitive
           └───────────┬───────────┘
                       │
           ┌───────────▼───────────┐
           │ Decision & Action      │  ← Agentic
           └───────────┬───────────┘
                       │
           ┌───────────▼───────────┐
           │ Executive Explanation  │  ← Cognitive
           └────────────────────────┘
```

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API keys
copy .env.example .env
# Edit .env with your API keys

# 4. Run the application
streamlit run app.py
```

## MCP Servers

| Server | Source | Purpose |
|--------|--------|---------|
| mcp-weather | OpenWeather API | Extreme weather detection |
| mcp-trade | World Bank WITS | Tariff & trade policy |
| mcp-geopolitics | GDELT Project | Political instability |
| mcp-economics | FRED | Macro demand shocks |
| mcp-logistics | US BTS | Port congestion & shipping |
| mcp-labor | US BLS | Labor shortages & strikes |

## Project Structure

```
mccs/
├── mcp_servers/          # MCP server implementations
├── agents/               # Agentic layer (LangGraph)
├── cognitive/            # Causal graph & simulation
├── models/               # Data models
├── ui/                   # Streamlit UI components
├── config/               # Configuration
└── tests/                # Test suite
```

## Tech Stack

- **Language**: Python 3.11+
- **Agents**: LangGraph
- **MCP**: Model Context Protocol
- **Graph**: NetworkX
- **Simulation**: OR-Tools, Monte Carlo
- **UI**: Streamlit
- **Dev**: VS Code + Kiro
