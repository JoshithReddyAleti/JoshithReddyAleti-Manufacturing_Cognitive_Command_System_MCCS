"""MCCS Orchestrator - Coordinates all agents and cognitive layers.

This is the main entry point that ties together all 6 agents:
- 8.1 Signal Intelligence Agent (data collection & anomaly detection)
- 8.2 Supply Chain Reasoning Agent (alternatives & sourcing risk)
- 8.3 Production Rebalancing Agent (virtual plant shifts)
- 8.4 Financial Impact Agent (revenue at risk & margin erosion)
- 8.5 Policy & Safety Agent (rules enforcement & guardrails)
- 8.6 Executive Explanation Agent (trust & communication)

Plus the Cognitive Layer:
- 7.1 Causal Graph Agent (propagation reasoning)
- 7.2 Risk Propagation Reasoning
- 7.3 Counterfactual Simulation Engine
"""

import asyncio
from dataclasses import dataclass, field
from typing import Optional

from mccs.agents.signal_intelligence import SignalIntelligenceAgent
from mccs.agents.supply_chain import SupplyChainAgent
from mccs.agents.production_rebalancing import ProductionRebalancingAgent
from mccs.agents.financial_impact import FinancialImpactAgent
from mccs.agents.policy_safety import PolicySafetyAgent
from mccs.agents.explanation import ExplanationAgent
from mccs.agents.auto_trigger import AutoTriggerEngine
from mccs.agents.chatbot import ChatbotAgent
from mccs.agents.email_generator import EmailGenerator
from mccs.agents.alternatives import AlternativesAgent
from mccs.cognitive.causal_graph import CausalGraph, build_demo_graph
from mccs.cognitive.simulation import SimulationEngine
from mccs.cognitive.explainability import ExplainabilityEngine
from mccs.cognitive.risk_propagation import RiskPropagationEngine
from mccs.models.signals import Signal, Scenario, Recommendation
from mccs.config.settings import settings


@dataclass
class MCCSResult:
    """Complete result from an MCCS analysis run."""
    signals: list[Signal] = field(default_factory=list)
    scenarios: list[Scenario] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    financial_impact: dict = field(default_factory=dict)
    supply_chain_assessment: dict = field(default_factory=dict)
    production_rebalancing: dict = field(default_factory=dict)
    policy_review: dict = field(default_factory=dict)
    risk_propagation_reports: list = field(default_factory=list)
    alternatives: dict = field(default_factory=dict)
    executive_briefing: dict = field(default_factory=dict)
    graph_stats: dict = field(default_factory=dict)


class MCCSOrchestrator:
    """Main orchestrator for the Manufacturing Cognitive Command System.

    Coordinates the full analysis pipeline with all 6 agents in a loop:

    ┌─────────────────────────────────────────────────────────┐
    │  AGENT LOOP (runs sequentially, feeds forward)          │
    │                                                         │
    │  1. Signal Intelligence → collect & rank signals        │
    │  2. Causal Graph        → propagate risk                │
    │  3. Simulation Engine   → generate scenarios            │
    │  4. Supply Chain Agent  → assess alternatives           │
    │  5. Production Rebalancing → create shift plans         │
    │  6. Financial Impact    → calculate exposure            │
    │  7. Policy & Safety     → enforce rules & guardrails    │
    │  8. Executive Explanation → generate briefing           │
    │                                                         │
    │  Loop back: if policy blocks actions, re-simulate       │
    └─────────────────────────────────────────────────────────┘
    """

    def __init__(self, causal_graph: Optional[CausalGraph] = None):
        self.graph = causal_graph or build_demo_graph()

        # All 6 agents from the PRD
        self.signal_agent = SignalIntelligenceAgent()              # 8.1
        self.supply_chain_agent = SupplyChainAgent(self.graph)     # 8.2
        self.rebalancing_agent = ProductionRebalancingAgent(self.graph)  # 8.3
        self.financial_agent = FinancialImpactAgent()              # 8.4
        self.policy_agent = PolicySafetyAgent()                    # 8.5
        self.explanation_agent = ExplanationAgent()                # 8.6

        # New: Auto-trigger, Chatbot, Email, Alternatives
        self.auto_trigger = AutoTriggerEngine()
        self.chatbot = ChatbotAgent()
        self.email_generator = EmailGenerator()
        self.alternatives_agent = AlternativesAgent()

        # Cognitive layer
        self.simulation_engine = SimulationEngine(self.graph)      # 7.3
        self.explainability = ExplainabilityEngine(self.graph)     # 7.1 + 7.2
        self.risk_propagation = RiskPropagationEngine(self.graph)  # 7.2

    async def run_full_analysis(self, num_scenarios: int = 10, industry: str = "", countries: list = None) -> MCCSResult:
        """Execute the complete MCCS analysis pipeline.

        Runs all agents in sequence, with policy feedback loop.
        This is the main entry point for a full disruption analysis.
        
        Args:
            num_scenarios: Number of Monte Carlo scenarios to generate
            industry: Optional industry focus (e.g., "semiconductor", "pharmaceutical")
            countries: Optional list of country codes to focus monitoring on
        """
        if countries is None:
            countries = []
        # ═══════════════════════════════════════════════════════════
        # STEP 1: Signal Intelligence Agent (8.1)
        # Polls MCP servers with INDUSTRY-SPECIFIC queries
        # ═══════════════════════════════════════════════════════════
        signals = await self.signal_agent.collect_all_signals(industry=industry, countries=countries)

        # ═══════════════════════════════════════════════════════════
        # STEP 2: Causal Graph Reasoning (7.1 + 7.2)
        # Propagate risk through the causal graph using:
        # - Lead-time heuristics
        # - Historical lag assumptions
        # - Confidence ranges
        # ═══════════════════════════════════════════════════════════
        propagation_reports = []
        for signal in signals:
            for entity in signal.affected_entities:
                if entity in self.graph._nodes:
                    severity_risk = self._severity_to_risk(signal.severity)
                    # Basic propagation (updates node risk levels)
                    self.graph.propagate_risk(entity, severity_risk)
                    # Full 7.2 analysis with confidence ranges
                    report = self.risk_propagation.analyze_propagation(
                        entity, severity_risk, signal=signal
                    )
                    if report.total_nodes_affected > 0:
                        propagation_reports.append(report)

        # ═══════════════════════════════════════════════════════════
        # STEP 3: Counterfactual Simulation Engine (7.3)
        # Simulate futures, not predict one
        # ═══════════════════════════════════════════════════════════
        scenarios = self.simulation_engine.simulate_scenarios(signals, num_scenarios)

        # ═══════════════════════════════════════════════════════════
        # STEP 4: Supply Chain Reasoning Agent (8.2)
        # Suggest alternatives, score sourcing risk
        # ═══════════════════════════════════════════════════════════
        supply_assessment = self.supply_chain_agent.evaluate_sourcing_strategy(signals)

        # ═══════════════════════════════════════════════════════════
        # STEP 5: Production Rebalancing Agent (8.3)
        # Create virtual plant shifts, trade cost vs risk
        # ═══════════════════════════════════════════════════════════
        rebalancing_plan = self.rebalancing_agent.generate_rebalancing_plan(signals, scenarios)

        # ═══════════════════════════════════════════════════════════
        # STEP 6: Financial Impact Agent (8.4)
        # Revenue at risk, inventory exposure, margin erosion
        # ═══════════════════════════════════════════════════════════
        financial = self.financial_agent.calculate_impact(scenarios)

        # Generate initial recommendations from simulation
        recommendations = self.simulation_engine.generate_recommendations(scenarios)

        # ═══════════════════════════════════════════════════════════
        # STEP 7: Policy & Safety Agent (8.5)
        # Enforce rules: max risk tolerance, ethical sourcing,
        # regulatory limits. May block or flag recommendations.
        # ═══════════════════════════════════════════════════════════
        policy_review = self.policy_agent.review_recommendations(
            recommendations, signals, scenarios
        )
        scenario_risk_check = self.policy_agent.check_scenario_risk(scenarios)

        # FEEDBACK LOOP: If policy blocks recommendations, filter them
        if policy_review["blocked_count"] > 0:
            blocked_titles = {b["title"] for b in policy_review["blocked"]}
            recommendations = [r for r in recommendations if r.title not in blocked_titles]

        # ═══════════════════════════════════════════════════════════
        # STEP 8: Executive Explanation Agent (8.6)
        # Most important for trust — turns numbers into narrative
        # Now powered by Google Gemini for AI-generated explanations
        # ═══════════════════════════════════════════════════════════
        briefing = self.explanation_agent.generate_executive_briefing(
            signals, scenarios, recommendations, financial
        )

        # AI-powered narrative via Gemini
        if settings.gemini_api_key and signals:
            try:
                from mccs.cognitive.llm_engine import generate_executive_narrative
                ai_narrative = await generate_executive_narrative(
                    signals_count=len(signals),
                    top_signal=signals[0].title if signals else "None",
                    expected_loss=financial.get("expected_loss_usd", 0),
                    worst_case=financial.get("worst_case_usd", 0),
                    recommendations=[r.title for r in recommendations],
                )
                briefing["ai_narrative"] = ai_narrative
            except Exception as e:
                briefing["ai_narrative"] = f"[AI narrative unavailable: {e}]"

        # Add policy and rebalancing context to briefing
        briefing["policy_status"] = policy_review.get("policy_summary", "")
        briefing["rebalancing_available"] = rebalancing_plan.get("status") == "plan_generated"
        briefing["data_source"] = "LIVE APIs (OpenWeather, FRED, GDELT, BLS, Finnhub) + Gemini AI"
        briefing["industry_focus"] = industry or "All Manufacturing (General)"
        briefing["countries_monitored"] = countries if countries else ["Global"]

        # ═══════════════════════════════════════════════════════════
        # AUTO-TRIGGER: Evaluate signals against thresholds
        # Bounded autonomy - auto-escalate when thresholds breach
        # ═══════════════════════════════════════════════════════════
        auto_triggers = self.auto_trigger.evaluate_signals(signals)

        # ═══════════════════════════════════════════════════════════
        # ALTERNATIVES AGENT: Find alternative paths for disruptions
        # Activates when signals indicate blocked routes/suppliers
        # ═══════════════════════════════════════════════════════════
        alternatives = self.alternatives_agent.find_alternatives(signals, industry)

        # Update chatbot context
        result = MCCSResult(
            signals=signals,
            scenarios=scenarios,
            recommendations=recommendations,
            financial_impact=financial,
            supply_chain_assessment=supply_assessment,
            production_rebalancing=rebalancing_plan,
            policy_review=policy_review,
            risk_propagation_reports=propagation_reports,
            alternatives=alternatives,
            executive_briefing=briefing,
            graph_stats=self.graph.get_graph_stats(),
        )
        self.chatbot.build_context_from_result(result)

        return result

    async def run_continuous_loop(self, interval_seconds: int = 300, max_iterations: int = 0):
        """Run the analysis pipeline in a continuous monitoring loop.

        This implements the "always-on" monitoring pattern where agents
        continuously poll for new signals and re-evaluate the situation.

        Args:
            interval_seconds: Seconds between analysis runs (default 5 min)
            max_iterations: Max loops to run (0 = infinite)
        """
        iteration = 0
        while max_iterations == 0 or iteration < max_iterations:
            iteration += 1
            print(f"\n{'='*60}")
            print(f"  MCCS Analysis Loop - Iteration #{iteration}")
            print(f"{'='*60}")

            result = await self.run_full_analysis()

            # Print summary
            print(f"  Signals: {len(result.signals)}")
            print(f"  Scenarios: {len(result.scenarios)}")
            print(f"  Recommendations: {len(result.recommendations)}")
            print(f"  Policy blocked: {result.policy_review.get('blocked_count', 0)}")
            print(f"  Expected loss: ${result.financial_impact.get('expected_loss_usd', 0):,.0f}")

            # Check for critical signals that need immediate attention
            critical = [s for s in result.signals if s.severity.value == "critical"]
            if critical:
                print(f"\n  🔴 CRITICAL ALERTS ({len(critical)}):")
                for sig in critical:
                    print(f"     - {sig.title}")

            if max_iterations > 0 and iteration >= max_iterations:
                break

            print(f"\n  Next analysis in {interval_seconds}s...")
            await asyncio.sleep(interval_seconds)

        return result

    async def get_signal_summary(self) -> dict:
        """Quick signal check without full analysis."""
        signals = await self.signal_agent.collect_all_signals()
        return self.signal_agent.get_signal_summary()

    def get_graph_visualization_data(self) -> dict:
        """Get data for graph visualization."""
        nodes = []
        for node_id, node in self.graph._nodes.items():
            nodes.append({
                "id": node_id,
                "name": node.name,
                "type": node.node_type.value,
                "location": node.location,
                "country": node.country,
                "criticality": node.criticality,
                "risk": node.current_risk,
            })

        edges = []
        for edge in self.graph._edges:
            edges.append({
                "source": edge.source_id,
                "target": edge.target_id,
                "type": edge.edge_type.value,
                "weight": edge.weight,
                "lag_days": edge.lag_days,
            })

        return {"nodes": nodes, "edges": edges}

    def get_node_detail(self, node_id: str) -> Optional[dict]:
        """Get detailed information about a specific node."""
        node = self.graph.get_node(node_id)
        if not node:
            return None

        downstream = self.graph.get_downstream_nodes(node_id)
        upstream = self.graph.get_upstream_nodes(node_id)

        return {
            "node": node.model_dump(),
            "downstream_count": len(downstream),
            "upstream_count": len(upstream),
            "downstream_nodes": downstream[:10],
            "upstream_nodes": upstream[:10],
        }

    def get_capacity_overview(self) -> dict:
        """Get production capacity overview from rebalancing agent."""
        return self.rebalancing_agent.assess_capacity()

    def get_policy_status(self) -> dict:
        """Get current policy configuration and violation history."""
        return self.policy_agent.get_policy_status()

    def validate_sourcing(self, country: str, product: str) -> dict:
        """Validate a sourcing decision against policy."""
        return self.policy_agent.validate_sourcing_decision(country, product)

    def simulate_plant_shift(self, source: str, target: str, units: int) -> dict:
        """Simulate a specific production shift between plants."""
        return self.rebalancing_agent.simulate_shift(source, target, units)

    def what_breaks_next(self, node_id: str, risk: float = 0.8) -> list[dict]:
        """Answer: 'If this happens here, what breaks next — and when?'

        Uses the Risk Propagation Engine (7.2) with:
        - Lead-time heuristics
        - Historical lag assumptions
        - Confidence ranges
        """
        return self.risk_propagation.what_breaks_next(node_id, risk)

    def get_propagation_narrative(self, node_id: str, risk: float = 0.8) -> str:
        """Get human-readable narrative of risk propagation from a node."""
        report = self.risk_propagation.analyze_propagation(node_id, risk)
        return report.narrative

    @staticmethod
    def _severity_to_risk(severity) -> float:
        """Convert severity level to numeric risk score."""
        from mccs.models.signals import SeverityLevel
        return {
            SeverityLevel.LOW: 0.2,
            SeverityLevel.MEDIUM: 0.5,
            SeverityLevel.HIGH: 0.75,
            SeverityLevel.CRITICAL: 0.95,
        }.get(severity, 0.5)


def run_analysis_sync(num_scenarios: int = 10) -> MCCSResult:
    """Synchronous wrapper for running the full analysis."""
    orchestrator = MCCSOrchestrator()
    return asyncio.run(orchestrator.run_full_analysis(num_scenarios))


def run_continuous_sync(interval: int = 300, iterations: int = 3):
    """Synchronous wrapper for running the continuous monitoring loop."""
    orchestrator = MCCSOrchestrator()
    return asyncio.run(orchestrator.run_continuous_loop(interval, iterations))
