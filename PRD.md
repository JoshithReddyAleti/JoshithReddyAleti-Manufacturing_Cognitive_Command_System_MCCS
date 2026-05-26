# Product Requirements Document (PRD)

## Manufacturing Cognitive Command System (MCCS)

**Version:** 1.0  
**Type:** Personal Project / Portfolio Piece  
**Author:** Joshith Reddy Aleti  
**Date:** May 2026  

---

## 1. Problem Statement (From First Principles)

Modern manufacturing enterprises are highly fragile — not because of lack of data, but because of **lack of integrated reasoning**.

### Critical Observations

1. **Disruptions are inevitable** — weather, geopolitics, tariffs, labor, logistics failures happen constantly
2. **Signals appear early, but are fragmented** — scattered across weather apps, news feeds, market data, government reports
3. **Humans detect patterns too late** — by the time someone connects "Taiwan tensions + chip shortage + auto plant delay," weeks have passed
4. **Existing systems are reactive:**
   - Excel spreadsheets
   - ERP rule engines
   - Reactive dashboards
   - Manual war rooms

### Result

When disruption occurs:
- Replanning takes **days or weeks**
- Decisions are **local, not global** (plant manager optimizes their plant, not the value chain)
- Impacts **cascade** across plants and suppliers
- **Millions are lost** before action is taken

### The Gap

There is no system today that can **cognitively understand** what a disruption means across the entire manufacturing value chain and **reason about what to do next**.

---

## 2. Goals & Non-Goals

### ✅ Goals

| # | Goal | How MCCS Achieves It |
|---|------|---------------------|
| 1 | Detect early disruption signals | 7 MCP servers polling live APIs every analysis run |
| 2 | Reason about cross-domain impacts | Causal graph with risk propagation + confidence ranges |
| 3 | Simulate future scenarios | Monte Carlo + OR-Tools counterfactual engine |
| 4 | Recommend optimal responses | Financial impact analysis + cost-benefit + alternatives |
| 5 | Explain decisions transparently | Executive Explanation Agent + Gemini AI narratives |
| 6 | Use public data only | All APIs are free-tier public data sources |
| 7 | Industry-specific analysis | Configurable per industry (12 industries supported) |

### ❌ Non-Goals

- Real ERP writeback (no automatic execution)
- Full automation (human remains in the loop)
- Industry-specific plant physics (generic manufacturing model)
- Guaranteed correct decisions (this is decision-intelligence, not control)
- Real-time streaming (poll-based, not WebSocket)

---

## 3. Target User Persona

### Primary Users

| Role | Need |
|------|------|
| Manufacturing Strategy Analyst | "What is about to break?" |
| Supply Chain Architect | "How bad will it get?" |
| Operations Innovation Engineer | "What are my best options?" |
| VP of Operations | "Why does the system think this?" |

### User Questions MCCS Answers

1. "What disruptions are developing right now in my industry?"
2. "If this gets worse, what's the financial exposure?"
3. "What are my alternatives if this supplier/route is blocked?"
4. "Should I act now or wait? What's the cost of waiting?"
5. "Explain this to me in plain language so I can brief my CEO."

---

## 4. System Architecture

### High-Level Flow

```
┌────────────────────────────────────────────────────────┐
│ Public Data Sources (7 MCP Servers — LIVE APIs)         │
├────────────────────────────────────────────────────────┤
│ Weather │ Trade │ Geopolitics │ Economics │ Logistics │ │
│ Labor │ Stocks                                         │
└────────────────────────────┬───────────────────────────┘
                             │
                ┌────────────▼────────────┐
                │ Signal Intelligence      │  ← Agentic (8.1)
                │ (Industry-specific)      │
                └────────────┬────────────┘
                             │
                ┌────────────▼────────────┐
                │ Causal Graph Reasoning   │  ← Cognitive (7.1)
                │ Risk Propagation         │  ← Cognitive (7.2)
                └────────────┬────────────┘
                             │
                ┌────────────▼────────────┐
                │ Counterfactual Simulation│  ← Cognitive (7.3)
                │ Monte Carlo + OR-Tools   │
                └────────────┬────────────┘
                             │
                ┌────────────▼────────────┐
                │ Decision Agents          │  ← Agentic (8.2-8.7)
                │ Supply Chain │ Financial │
                │ Rebalancing │ Policy    │
                │ Alternatives │ Explain  │
                └────────────┬────────────┘
                             │
                ┌────────────▼────────────┐
                │ Human-in-the-Loop        │
                │ Approve / Reject / Ask   │
                └─────────────────────────┘
```

---

## 5. MCP Strategy (Core Design Choice)

### Why MCP (Model Context Protocol)?

| Reason | Explanation |
|--------|-------------|
| Clean separation | AI reasoning is separate from data fetching |
| Easy to extend | Add/remove data sources without touching agents |
| Testable | Each server is stateless and independently testable |
| Future-proof | Mimics how real AI platforms will work |
| Portfolio signal | Demonstrates understanding of modern AI architecture |

### MCP Philosophy

- Each external data source = one MCP server
- Agents consume MCP tools, never raw APIs
- All MCP servers are stateless & testable
- Industry selection changes what each server queries

---

## 6. MCP Data Sources (7 Servers)

### 6.1 Weather & Natural Disruption MCP

| Field | Value |
|-------|-------|
| Purpose | Detect extreme weather at manufacturing hubs |
| Source | OpenWeather API |
| Why chosen | Global coverage, free tier, extreme weather alerts, simple REST |
| Server name | `mcp-weather` |
| Key tools | `get_current_weather(location)`, `get_weather_alerts(lat, lon)`, `get_7day_forecast(location)` |
| Signals produced | Flood risk, heat waves, hurricanes, storm proximity |
| Proof URL | https://openweathermap.org |

### 6.2 Tariffs & Trade Policy MCP

| Field | Value |
|-------|-------|
| Purpose | Detect tariff changes and trade restrictions |
| Source | GDELT Project (news volume analysis) |
| Why chosen | Near-real-time, global, free, measures policy attention |
| Server name | `mcp-trade` |
| Key tools | `get_tariff_rate(country, product)`, `get_trade_restrictions(country)`, `get_trade_risk_overview()` |
| Signals produced | Tariff increases, trade barriers, export controls |
| Proof URL | https://api.gdeltproject.org |

### 6.3 Geopolitical & Conflict MCP

| Field | Value |
|-------|-------|
| Purpose | Detect political instability threatening supply chains |
| Source | GDELT Project |
| Why chosen | Global event database, near-real-time, used by governments |
| Server name | `mcp-geopolitics` |
| Key tools | `get_event_spikes(country)`, `get_conflict_intensity(region)`, `get_global_risk_summary()` |
| Signals produced | Political unrest, protests, sanctions risk, military tensions |
| Proof URL | https://api.gdeltproject.org |

### 6.4 Manufacturing Demand & Economy MCP

| Field | Value |
|-------|-------|
| Purpose | Detect macro demand shocks |
| Source | FRED (Federal Reserve Economic Data) |
| Why chosen | Extremely reliable, industry indicators, manufacturing indexes |
| Server name | `mcp-economics` |
| Key tools | `get_industrial_production_index()`, `get_manufacturing_orders()`, `get_gdp_growth()`, `get_capacity_utilization()` |
| Signals produced | PMI contraction, order declines, recession probability |
| Proof URL | https://fred.stlouisfed.org |

### 6.5 Logistics & Port Congestion MCP

| Field | Value |
|-------|-------|
| Purpose | Monitor shipping delays and chokepoints |
| Source | GDELT (logistics news analysis) |
| Why chosen | Public, covers Suez/Red Sea/Panama, real-time news proxy |
| Server name | `mcp-logistics` |
| Key tools | `get_port_congestion(port)`, `get_freight_delay_stats()`, `get_chokepoint_status()` |
| Signals produced | Port congestion, chokepoint restrictions, freight delays |
| Proof URL | https://api.gdeltproject.org |

### 6.6 Labor & Workforce MCP

| Field | Value |
|-------|-------|
| Purpose | Anticipate labor shortages or strikes |
| Source | US Bureau of Labor Statistics (BLS) API v2 |
| Why chosen | Ground-truth labor data, strike & unemployment trends |
| Server name | `mcp-labor` |
| Key tools | `get_unemployment_rate(industry)`, `get_labor_disruptions()`, `get_manufacturing_employment()` |
| Signals produced | Employment declines, hours reduction, wage pressure |
| Proof URL | https://www.bls.gov/developers/ |

### 6.7 Stock Market MCP

| Field | Value |
|-------|-------|
| Purpose | Detect market signals of demand/supply disruption |
| Source | Finnhub API |
| Why chosen | Real-time quotes, free tier, sector ETFs + individual stocks |
| Server name | `mcp-stocks` |
| Key tools | `get_stock_quote(symbol)`, `get_market_news(category)`, `get_sector_performance()` |
| Signals produced | Sector drops, individual stock crashes, unusual spikes |
| Proof URL | https://finnhub.io |

---

## 7. Cognitive Layer (Thinking)

### 7.1 Causal Graph Agent

| Field | Value |
|-------|-------|
| Role | Understand WHY disruption propagates, not just THAT it happens |
| Tech | NetworkX (Directed Acyclic Graph) |
| Nodes | Entities: suppliers, ports, plants, warehouses, markets (17 total) |
| Edges | Causal influence with weight (0-1) and time lag (days) |
| Example | Hurricane → Port Congestion → Shipping Delay → Material Shortage → Production Loss |
| Key methods | `propagate_risk()`, `find_critical_paths()`, `get_node_criticality_ranking()` |

### 7.2 Risk Propagation Reasoning

| Field | Value |
|-------|-------|
| Purpose | Answer: "If this happens here, what breaks next — and when?" |
| Logic | Lead-time heuristics + Historical lag assumptions + Confidence ranges |
| Lead-time heuristics | Each node type has buffer days (warehouse: 5d, plant: 2d, port: 1d) |
| Historical lags | Table of typical propagation times per node-type pair |
| Confidence ranges | Every estimate has min/expected/max bounds (not point estimates) |
| Decay | 15% confidence decay per hop through the graph |
| Output | Per node: when impact arrives (range), risk level (range), buffer, recovery |

### 7.3 Counterfactual Simulation Engine

| Field | Value |
|-------|-------|
| Purpose | Simulate futures, not predict one |
| Tech | Monte Carlo (NumPy) + OR-Tools (constraint optimization) |
| Scenarios | Base case, Escalation, Compound, Cascade, Monte Carlo variations |
| OR-Tools | Optimal production allocation under disrupted capacity constraints |
| Output | Each scenario: probability, revenue at risk, explanation, actions |
| Questions answered | "What if escalation worsens?" "What if demand spikes + supplier delay overlap?" |

---

## 8. Agentic Layer (Doing)

### 8.1 Signal Intelligence Agent

| Field | Value |
|-------|-------|
| Role | Polls MCP servers, normalizes signals, flags anomalies |
| Key behavior | Industry selection changes what gets queried (different tickers, keywords, locations) |
| Output | Ranked list of disruption signals with severity, confidence, proof links |

### 8.2 Supply Chain Reasoning Agent

| Field | Value |
|-------|-------|
| Role | Suggests alternatives, scores sourcing risk |
| Key behavior | Maintains alternate supplier database with cost/quality/lead-time scoring |
| Output | Supplier risk rankings, diversification score, immediate actions |

### 8.3 Production Rebalancing Agent (Simulated)

| Field | Value |
|-------|-------|
| Role | Creates virtual plant shifts, trades cost vs risk |
| Key behavior | Knows capacity, utilization, cost, overtime, product compatibility per plant |
| Output | Shift plans (source → target, units, cost increase, risk reduction) |

### 8.4 Financial Impact Agent

| Field | Value |
|-------|-------|
| Role | Revenue at risk, inventory exposure, margin erosion |
| Key behavior | Probability-weighted expected loss, worst case, penalty exposure, mitigation ROI |
| Output | Expected loss, worst case, net exposure, margin erosion %, payback period |

### 8.5 Policy & Safety Agent

| Field | Value |
|-------|-------|
| Role | Enforces rules: max risk tolerance, ethical sourcing, regulatory limits |
| Key behavior | Reviews recommendations against configurable policy. Can BLOCK or FLAG. |
| Rules | Banned countries, cost thresholds, overtime limits, capacity caps, ROI minimums |
| Output | Approved/flagged/blocked counts, violation details |

### 8.6 Executive Explanation Agent

| Field | Value |
|-------|-------|
| Role | Most important for trust. Turns probability into human narrative. |
| Key behavior | Generates headline, situation, risk narrative, actions, confidence, timeline |
| AI | Uses Google Gemini for natural language when available |
| Example | "Probability × severity = 0.42" → "If left unaddressed, production loss risk increases materially within 14 days." |

### 8.7 Alternatives Agent

| Field | Value |
|-------|-------|
| Role | Finds alternative paths when disruptions block routes, suppliers, or resources |
| Key behavior | Knowledge base of real alternatives per industry with feasibility, cost, time, risk reduction |
| Examples | China tariff → Samsung/Intel fabs. Hormuz closed → Cape of Good Hope. Supplier down → qualified alternates. |
| Output | Ranked alternatives with trade-offs and source-of-truth proof links |

---

## 9. Human-in-the-Loop Design

| Human does | AI does |
|-----------|---------|
| Approves assumptions | Does thinking |
| Chooses scenarios | Does simulation |
| Accepts or rejects recommendations | Does explanation |
| Selects industry & countries | Does data collection |
| Asks questions (chatbot) | Provides answers with sources |

**All recommendations require explicit human approval.** This is a decision-intelligence system, not a control system.

---

## 10. Auto-Trigger System (Bounded Autonomy)

When thresholds are breached, the system auto-triggers:

| Severity | Action |
|----------|--------|
| LOW | Log only |
| MEDIUM | Auto-notify + prepare response |
| HIGH | Auto-escalate + draft actions |
| CRITICAL | Auto-escalate + execute pre-approved actions |

Pre-approved actions (no human needed):
- Increase monitoring frequency
- Activate alternate supplier contact list
- Escalate to leadership
- Prepare customer communication draft

---

## 11. Industry Configuration

The system supports 12 manufacturing industries. Each has unique:

| Industry | Example Stocks | Example Locations | Example Keywords |
|----------|---------------|-------------------|-----------------|
| Semiconductor | SOXX, TSM, NVDA, AMD | Hsinchu, Seoul, Phoenix | "chip shortage", "export controls" |
| Automotive | TSLA, F, GM, TM | Detroit, Monterrey, Stuttgart | "EV battery", "UAW strike" |
| Pharmaceutical | PFE, JNJ, MRK, LLY | Mumbai, Basel, New Jersey | "drug shortage", "API ingredient" |
| Aerospace | BA, LMT, RTX, NOC | Seattle, Toulouse, Fort Worth | "titanium supply", "Boeing delay" |
| Energy | XOM, CVX, ENPH | Houston, Riyadh, Xinjiang | "OPEC cut", "solar panel supply" |
| Electronics | AAPL, SONY, DELL | Shenzhen, Seoul, Cupertino | "display shortage", "factory shutdown" |
| Chemicals | DD, DOW, LYB | Houston, Ludwigshafen, Jubail | "plant explosion", "polymer shortage" |
| Steel & Metals | NUE, X, CLF, FCX | Pittsburgh, Tangshan, Pilbara | "steel tariff", "mining strike" |
| Textiles | NKE, LULU, VFC | Dhaka, Ho Chi Minh, Guangzhou | "garment shutdown", "cotton shortage" |
| Food & Beverage | KO, PEP, ADM | Chicago, Sao Paulo, Odessa | "crop failure", "food safety recall" |
| Medical Devices | MDT, ABT, SYK | Minneapolis, Galway, Tuttlingen | "device recall", "implant shortage" |
| Construction | VMC, MLM, SHW | Dallas, Dubai | "cement shortage", "lumber supply" |

---

## 12. Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Language | Python 3.11 | Ecosystem, async support, data science libraries |
| Backend API | FastAPI | Fast, async, auto-docs, type-safe |
| Frontend | Next.js 16 + TypeScript + Tailwind | Modern React, SSR, great DX |
| Graph | NetworkX | Mature, well-documented, DAG support |
| Simulation | NumPy + OR-Tools | Monte Carlo + constraint optimization |
| LLM | Google Gemini | Free tier, fast, good reasoning |
| Data Protocol | MCP (custom) | Clean separation of data vs reasoning |
| Real-time Data | OpenWeather, FRED, GDELT, Finnhub, BLS | All free, all public, all reliable |

---

## 13. MVP Success Criteria

| Criterion | Status |
|-----------|--------|
| One disruption scenario end-to-end | ✅ Semiconductor ETF drop → full pipeline |
| At least 5 MCP servers wired | ✅ 7 servers (weather, trade, geo, econ, logistics, labor, stocks) |
| Causal graph built | ✅ 17 nodes, 17 edges, validated DAG |
| 10+ simulated futures | ✅ 8+ scenarios per run (Monte Carlo) |
| Clear executive explanation | ✅ Headline, narrative, actions, confidence |
| Industry-specific analysis | ✅ 12 industries with unique configs |
| Real-time data (not demo) | ✅ All APIs return live data |
| Source-of-truth hyperlinks | ✅ Every signal has proof link |
| Human-in-the-loop | ✅ All recommendations require approval |
| Alternatives when disrupted | ✅ Industry-specific alternatives with trade-offs |

---

## 14. What It Does NOT Solve (Honest Limitations)

| Limitation | Why it's OK |
|-----------|-------------|
| No ERP writeback | This is decision-intelligence, not control |
| No full automation | Human judgment is irreplaceable for strategic decisions |
| No plant physics | Generic manufacturing model, not process-specific |
| No guaranteed correctness | Probabilistic reasoning with stated confidence |
| Gemini rate limits | Free tier; system works without AI |
| GDELT is news proxy | Not direct port/shipping sensors |
| Static causal graph | Seeded with assumptions, not learned from your data |

---

## 15. Future Evolution (Complexity Layers)

### Layer 1: Supply Network Ground Truth
- Bill-of-Materials inference
- Supplier tier modeling (Tier 1 → Tier 3)
- Uncertainty scoring per assumption

### Layer 2: Adaptive Learning
- Outcome tracking ("what actually happened?")
- Assumption error analysis
- Dynamic adjustment of causal weights

### Layer 3: Partial Autonomous Execution
- Pre-approved actions with threshold-based execution
- Rollback guarantees
- Auto-trigger buffer inventory, escalation drafts

### Layer 4: Multi-Objective Trade-Off Reasoning
- Explicit trade-off curves (cost vs risk vs speed)
- Pareto-front reasoning
- Decision justification in business language

### Layer 5: External Shock Amplification
- Shock compounding models
- Non-linear impact amplification
- Scenario branching explosion control

### Layer 6: Organizational Intelligence
- Detect human bias patterns
- Flag political overrides
- Highlight ignored risks historically

---

## 16. Security & Privacy

- All data sources are public APIs (no proprietary data)
- API keys stored in `.env` (not committed to git)
- No PII collected or stored
- No data sent to third parties beyond the API calls
- CORS enabled for local development only

---

## 17. Deployment Options

| Option | Complexity | Cost |
|--------|-----------|------|
| Local (current) | Low | Free (API free tiers) |
| Docker Compose | Medium | Free (self-hosted) |
| Vercel (frontend) + Railway (backend) | Medium | ~$5/month |
| AWS (ECS + CloudFront) | High | ~$20/month |

---

*This document represents the complete product specification for MCCS v1.0.*
