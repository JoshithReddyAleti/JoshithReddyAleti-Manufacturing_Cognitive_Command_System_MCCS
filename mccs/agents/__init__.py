"""Agentic layer - All 6 agents from the MCCS PRD.

8.1 Signal Intelligence Agent - Polls MCP servers, normalizes signals, flags anomalies
8.2 Supply Chain Reasoning Agent - Suggests alternatives, scores sourcing risk
8.3 Production Rebalancing Agent - Creates virtual plant shifts, trades cost vs risk
8.4 Financial Impact Agent - Revenue at risk, inventory exposure, margin erosion
8.5 Policy & Safety Agent - Enforces rules: max risk tolerance, ethical sourcing, regulatory limits
8.6 Executive Explanation Agent - Turns probability into human narrative
"""

from mccs.agents.signal_intelligence import SignalIntelligenceAgent
from mccs.agents.supply_chain import SupplyChainAgent
from mccs.agents.production_rebalancing import ProductionRebalancingAgent
from mccs.agents.financial_impact import FinancialImpactAgent
from mccs.agents.policy_safety import PolicySafetyAgent
from mccs.agents.explanation import ExplanationAgent
from mccs.agents.orchestrator import MCCSOrchestrator, MCCSResult

__all__ = [
    "SignalIntelligenceAgent",
    "SupplyChainAgent",
    "ProductionRebalancingAgent",
    "FinancialImpactAgent",
    "PolicySafetyAgent",
    "ExplanationAgent",
    "MCCSOrchestrator",
    "MCCSResult",
]
