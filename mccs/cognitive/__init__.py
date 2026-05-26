"""Cognitive layer - Causal reasoning, risk propagation, and simulation.

7.1 Causal Graph Agent - Directed acyclic graph of manufacturing value chain
7.2 Risk Propagation Reasoning - Lead-time heuristics, historical lags, confidence ranges
7.3 Counterfactual Simulation Engine - Monte Carlo scenario generation
"""

from mccs.cognitive.causal_graph import CausalGraph, build_demo_graph
from mccs.cognitive.risk_propagation import RiskPropagationEngine
from mccs.cognitive.simulation import SimulationEngine
from mccs.cognitive.explainability import ExplainabilityEngine

__all__ = [
    "CausalGraph",
    "build_demo_graph",
    "RiskPropagationEngine",
    "SimulationEngine",
    "ExplainabilityEngine",
]
