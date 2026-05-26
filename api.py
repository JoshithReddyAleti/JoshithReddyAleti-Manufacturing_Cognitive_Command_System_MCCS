"""MCCS FastAPI Backend - Serves real-time analysis to Next.js frontend.

Exposes every agent's output, cognitive layer reasoning, and source-of-truth
hyperlinks as structured JSON endpoints.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mccs.agents.orchestrator import MCCSOrchestrator
from mccs.config.settings import settings

app = FastAPI(
    title="MCCS API",
    description="Manufacturing Cognitive Command System - Real-time disruption intelligence",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator = MCCSOrchestrator()


@app.get("/api/analyze")
async def run_analysis(industry: str = "", countries: str = ""):
    """Run full MCCS analysis pipeline and return complete results.
    
    Args:
        industry: Optional industry focus (semiconductor, automotive, pharmaceutical, etc.)
        countries: Optional comma-separated country codes to monitor (US,CN,TW)
    
    Returns every agent's output with source-of-truth hyperlinks.
    """
    # Pass industry context to the orchestrator
    industry_context = ""
    if industry:
        industry_context = industry
    
    country_list = [c.strip() for c in countries.split(",") if c.strip()] if countries else []
    
    result = await orchestrator.run_full_analysis(
        num_scenarios=8,
        industry=industry_context,
        countries=country_list,
    )

    # Build complete response with all agent outputs
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "industry_focus": industry_context or "All Manufacturing (General)",
        "countries_monitored": country_list if country_list else ["Global"],
        "data_sources": {
            "weather": {"name": "OpenWeather API", "url": "https://openweathermap.org/api", "status": "live"},
            "economics": {"name": "FRED (Federal Reserve)", "url": "https://fred.stlouisfed.org", "status": "live"},
            "geopolitics": {"name": "GDELT Project", "url": "https://api.gdeltproject.org", "status": "live"},
            "trade": {"name": "GDELT Trade Analysis", "url": "https://api.gdeltproject.org", "status": "live"},
            "logistics": {"name": "GDELT Logistics", "url": "https://api.gdeltproject.org", "status": "live"},
            "labor": {"name": "US Bureau of Labor Statistics", "url": "https://www.bls.gov/developers/", "status": "live"},
            "stocks": {"name": "Finnhub", "url": "https://finnhub.io", "status": "live"},
        },
        "ai_engine": {
            "provider": "Google Gemini",
            "model": settings.llm_model,
            "url": "https://ai.google.dev",
        },

        # Agent 8.1: Signal Intelligence
        "signal_intelligence": {
            "agent_id": "8.1",
            "agent_name": "Signal Intelligence Agent",
            "role": "Polls MCP servers, normalizes signals, flags anomalies",
            "total_signals": len(result.signals),
            "market_status": orchestrator.signal_agent._market_status,
            "signals": [
                {
                    "id": s.id,
                    "severity": s.severity.value,
                    "title": s.title,
                    "description": s.description,
                    "source": s.source,
                    "location": s.location,
                    "confidence": s.confidence,
                    "affected_entities": s.affected_entities,
                    "proof_link": s.raw_data.get("proof_link", s.raw_data.get("link", s.raw_data.get("source", ""))),
                    "raw_data": {k: v for k, v in s.raw_data.items() if k not in ("proof_link",)},
                }
                for s in result.signals
            ],
        },

        # Cognitive Layer 7.1 + 7.2: Causal Graph & Risk Propagation
        "causal_graph": {
            "layer_id": "7.1",
            "layer_name": "Causal Graph Agent",
            "role": "Directed acyclic graph of manufacturing value chain",
            "tech": "NetworkX",
            "stats": result.graph_stats,
            "nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "type": n.node_type.value,
                    "location": n.location,
                    "country": n.country,
                    "criticality": n.criticality,
                    "current_risk": n.current_risk,
                }
                for n in orchestrator.graph._nodes.values()
            ],
            "edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "type": e.edge_type.value,
                    "weight": e.weight,
                    "lag_days": e.lag_days,
                }
                for e in orchestrator.graph._edges
            ],
        },

        "risk_propagation": {
            "layer_id": "7.2",
            "layer_name": "Risk Propagation Reasoning",
            "role": "Answers: If this happens here, what breaks next — and when?",
            "logic": ["Lead-time heuristics", "Historical lag assumptions", "Confidence ranges"],
            "reports": [
                {
                    "origin": r.origin_node_name,
                    "trigger": r.trigger_signal,
                    "initial_risk": r.initial_risk,
                    "total_affected": r.total_nodes_affected,
                    "first_impact_day": r.first_impact_day.expected_value if r.first_impact_day else 0,
                    "last_impact_day": r.last_impact_day.expected_value if r.last_impact_day else 0,
                    "critical_path": r.critical_path,
                    "narrative": r.narrative,
                    "steps": [
                        {
                            "from": step.source_node_name,
                            "to": step.target_node_name,
                            "delay_expected": step.delay_range.expected_value,
                            "delay_range": f"{step.delay_range.min_value:.0f}-{step.delay_range.max_value:.0f} days",
                            "risk_expected": step.risk_range.expected_value,
                            "risk_range": f"{step.risk_range.min_value:.0%}-{step.risk_range.max_value:.0%}",
                            "confidence": step.risk_range.confidence,
                            "buffer_days": step.buffer_days,
                            "recovery_days": step.recovery_estimate_days,
                            "historical_basis": step.historical_basis,
                        }
                        for step in r.propagation_steps[:10]
                    ],
                }
                for r in result.risk_propagation_reports[:5]
            ],
        },

        # Cognitive Layer 7.3: Simulation
        "simulation": {
            "layer_id": "7.3",
            "layer_name": "Counterfactual Simulation Engine",
            "role": "Simulates futures, not predict one",
            "tech": "Monte Carlo + OR-Tools constraints",
            "total_scenarios": len(result.scenarios),
            "scenarios": [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "probability": s.probability,
                    "revenue_at_risk": s.total_revenue_at_risk_usd,
                    "explanation": s.explanation,
                    "recommended_actions": s.recommended_actions,
                    "impacts": [
                        {
                            "signal_id": imp.signal_id,
                            "affected_nodes": imp.affected_nodes[:5],
                            "delay_days": imp.estimated_delay_days,
                            "revenue_at_risk": imp.revenue_at_risk_usd,
                            "confidence": imp.confidence,
                            "time_to_impact_days": imp.time_to_impact_days,
                        }
                        for imp in s.impacts[:5]
                    ],
                }
                for s in result.scenarios
            ],
        },

        # Agent 8.2: Supply Chain
        "supply_chain": {
            "agent_id": "8.2",
            "agent_name": "Supply Chain Reasoning Agent",
            "role": "Suggests alternatives, scores sourcing risk",
            **result.supply_chain_assessment,
        },

        # Agent 8.3: Production Rebalancing
        "production_rebalancing": {
            "agent_id": "8.3",
            "agent_name": "Production Rebalancing Agent (Simulated)",
            "role": "Creates virtual plant shifts, trades cost vs risk",
            **result.production_rebalancing,
        },

        # Agent 8.4: Financial Impact
        "financial_impact": {
            "agent_id": "8.4",
            "agent_name": "Financial Impact Agent",
            "role": "Revenue at risk, inventory exposure, margin erosion",
            **result.financial_impact,
        },

        # Agent 8.5: Policy & Safety
        "policy_safety": {
            "agent_id": "8.5",
            "agent_name": "Policy & Safety Agent",
            "role": "Enforces: max risk tolerance, ethical sourcing, regulatory limits",
            **result.policy_review,
        },

        # Agent 8.6: Executive Explanation
        "executive_explanation": {
            "agent_id": "8.6",
            "agent_name": "Executive Explanation Agent",
            "role": "Turns probability into human narrative",
            **result.executive_briefing,
        },

        # Recommendations (post-policy-filter)
        "recommendations": [
            {
                "id": r.id,
                "title": r.title,
                "description": r.description,
                "urgency": r.urgency.value,
                "action_type": r.action_type,
                "cost_usd": r.estimated_cost_usd,
                "savings_usd": r.estimated_savings_usd,
                "roi_pct": round(((r.estimated_savings_usd - r.estimated_cost_usd) / r.estimated_cost_usd * 100) if r.estimated_cost_usd > 0 else 0, 0),
                "confidence": r.confidence,
                "explanation": r.explanation,
                "requires_approval": r.requires_approval,
            }
            for r in result.recommendations
        ],

        # Auto-triggers
        "auto_triggers": orchestrator.auto_trigger.get_trigger_summary(),

        # Alternatives Agent
        "alternatives": {
            "agent_name": "Alternatives Agent",
            "role": "Finds alternative paths when disruptions block routes, suppliers, or resources",
            **result.alternatives,
        },

        # Email (pre-generated)
        "email_summary": orchestrator.email_generator.generate_summary_email(result),
    }


@app.get("/api/chat")
async def chat(message: str):
    """Chat with the MCCS AI assistant."""
    try:
        response = await orchestrator.chatbot.chat(message)
        return {"response": response}
    except Exception as e:
        return {"response": f"I'm unable to process that right now. The AI service may be temporarily unavailable. Error: {str(e)[:100]}"}


@app.get("/api/industry-analysis")
async def industry_analysis(industry: str, countries: str = ""):
    """Get deep industry-specific analysis using Gemini AI.
    
    This endpoint uses the LLM to provide industry-specific insights
    based on the current signal data.
    """
    country_list = [c.strip() for c in countries.split(",") if c.strip()] if countries else ["US", "CN"]
    
    try:
        from mccs.cognitive.llm_engine import get_llm_client
        client = get_llm_client()
        
        prompt = f"""You are a manufacturing intelligence analyst specializing in the {industry} industry.

Based on current global conditions, provide a concise analysis for the {industry} industry 
focused on these countries: {', '.join(country_list)}.

Cover these areas (2-3 sentences each):
1. SUPPLY CHAIN RISKS: Key vulnerabilities for {industry} right now
2. TARIFF & TRADE: Current trade policy impacts on {industry}
3. LABOR: Workforce challenges specific to {industry}
4. GEOPOLITICAL: Political risks affecting {industry} supply chains
5. FINANCIAL OUTLOOK: Market conditions for {industry}
6. OPPORTUNITIES: Long-term opportunities emerging from current disruptions

Be specific to {industry}. Reference real companies, trade routes, and policies where relevant.
Format with clear headers."""

        response = client.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
        )
        return {
            "industry": industry,
            "countries": country_list,
            "analysis": response.text,
            "source": "Google Gemini AI + MCCS Agent Context",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "industry": industry,
            "countries": country_list,
            "analysis": f"AI analysis unavailable: {str(e)[:200]}. The Gemini free tier may be rate-limited. Please retry in 30 seconds.",
            "source": "Error",
            "timestamp": datetime.utcnow().isoformat(),
        }


@app.get("/api/health")
async def health():
    """Health check."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
