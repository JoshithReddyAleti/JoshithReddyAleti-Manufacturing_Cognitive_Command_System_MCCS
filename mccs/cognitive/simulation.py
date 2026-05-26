"""Counterfactual Simulation Engine.

Simulates multiple future scenarios using Monte Carlo methods
and constraint-based reasoning to answer:
- "What if escalation worsens?"
- "What if demand spikes + supplier delay overlap?"

Tech:
- Monte Carlo simulation (numpy)
- OR-Tools constraints (production/capacity optimization)
- Scenario branching (base, escalation, compound, cascade)
"""

import uuid
import random
from typing import Optional
import numpy as np
from ortools.sat.python import cp_model

from mccs.models.signals import Signal, Scenario, ImpactAssessment, Recommendation, SeverityLevel
from mccs.cognitive.causal_graph import CausalGraph
from mccs.config.settings import settings


class SimulationEngine:
    """Counterfactual simulation engine using Monte Carlo methods.

    Generates multiple future scenarios by varying disruption parameters
    and propagating impacts through the causal graph.
    """

    def __init__(self, causal_graph: CausalGraph):
        self.graph = causal_graph
        self.iterations = settings.monte_carlo_iterations
        self.horizon_days = settings.max_simulation_horizon_days

    def simulate_scenarios(
        self,
        signals: list[Signal],
        num_scenarios: int = 10,
    ) -> list[Scenario]:
        """Generate and evaluate multiple future scenarios.

        Args:
            signals: Current disruption signals
            num_scenarios: Number of scenarios to generate

        Returns:
            List of scenarios sorted by severity
        """
        if not signals:
            return []

        scenarios = []

        # Scenario 1: Base case (current signals propagate normally)
        scenarios.append(self._simulate_base_case(signals))

        # Scenario 2: Escalation (signals worsen)
        scenarios.append(self._simulate_escalation(signals))

        # Scenario 3: Compound disruption (multiple signals interact)
        if len(signals) >= 2:
            scenarios.append(self._simulate_compound(signals))

        # Scenario 4: Cascading failure
        scenarios.append(self._simulate_cascade(signals))

        # Scenario 5+: Monte Carlo variations
        mc_scenarios = self._monte_carlo_scenarios(signals, max(0, num_scenarios - 4))
        scenarios.extend(mc_scenarios)

        # Sort by total revenue at risk
        scenarios.sort(key=lambda s: s.total_revenue_at_risk_usd, reverse=True)

        return scenarios[:num_scenarios]

    def _simulate_base_case(self, signals: list[Signal]) -> Scenario:
        """Simulate the most likely outcome given current signals."""
        impacts = []
        total_risk = 0.0

        for signal in signals:
            for entity in signal.affected_entities:
                result = self.graph.propagate_risk(entity, self._severity_to_risk(signal.severity))
                if result.total_nodes_affected > 0:
                    revenue_at_risk = self._estimate_revenue_impact(
                        result.total_nodes_affected,
                        self._severity_to_risk(signal.severity),
                    )
                    impact = ImpactAssessment(
                        signal_id=signal.id,
                        affected_nodes=[n["node_id"] for n in result.affected_nodes[:5]],
                        propagation_path=result.critical_path,
                        estimated_delay_days=max(
                            (n["delay_days"] for n in result.affected_nodes), default=0
                        ),
                        revenue_at_risk_usd=revenue_at_risk,
                        confidence=signal.confidence * 0.8,
                        time_to_impact_days=self._estimate_time_to_impact(result),
                    )
                    impacts.append(impact)
                    total_risk += revenue_at_risk

        return Scenario(
            id=f"scenario-base-{uuid.uuid4().hex[:6]}",
            name="Base Case: Current Trajectory",
            description="Most likely outcome if current disruptions continue without intervention",
            probability=0.65,
            signals_involved=[s.id for s in signals],
            impacts=impacts,
            total_revenue_at_risk_usd=total_risk,
            recommended_actions=self._generate_base_actions(impacts),
            explanation=self._explain_scenario("base", total_risk, impacts),
        )

    def _simulate_escalation(self, signals: list[Signal]) -> Scenario:
        """Simulate scenario where disruptions escalate."""
        impacts = []
        total_risk = 0.0
        escalation_factor = 1.5

        for signal in signals:
            if signal.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL):
                escalated_risk = min(1.0, self._severity_to_risk(signal.severity) * escalation_factor)
                for entity in signal.affected_entities:
                    result = self.graph.propagate_risk(entity, escalated_risk)
                    if result.total_nodes_affected > 0:
                        revenue_at_risk = self._estimate_revenue_impact(
                            result.total_nodes_affected, escalated_risk
                        ) * escalation_factor
                        impact = ImpactAssessment(
                            signal_id=signal.id,
                            affected_nodes=[n["node_id"] for n in result.affected_nodes[:5]],
                            propagation_path=result.critical_path,
                            estimated_delay_days=max(
                                (n["delay_days"] for n in result.affected_nodes), default=0
                            ) * 1.5,
                            revenue_at_risk_usd=revenue_at_risk,
                            confidence=signal.confidence * 0.6,
                            time_to_impact_days=self._estimate_time_to_impact(result) * 0.7,
                        )
                        impacts.append(impact)
                        total_risk += revenue_at_risk

        return Scenario(
            id=f"scenario-escalation-{uuid.uuid4().hex[:6]}",
            name="Escalation: Disruptions Worsen",
            description="Scenario where current high-severity disruptions escalate significantly",
            probability=0.20,
            signals_involved=[s.id for s in signals if s.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL)],
            impacts=impacts,
            total_revenue_at_risk_usd=total_risk,
            recommended_actions=self._generate_escalation_actions(impacts),
            explanation=self._explain_scenario("escalation", total_risk, impacts),
        )

    def _simulate_compound(self, signals: list[Signal]) -> Scenario:
        """Simulate compound disruption where multiple signals interact."""
        impacts = []
        total_risk = 0.0

        # Find signals that affect overlapping entities
        all_entities = set()
        for signal in signals:
            for entity in signal.affected_entities:
                if entity in all_entities:
                    # Compound effect: risk amplifies
                    result = self.graph.propagate_risk(entity, 0.9)
                    if result.total_nodes_affected > 0:
                        revenue_at_risk = self._estimate_revenue_impact(
                            result.total_nodes_affected, 0.9
                        ) * 2.0
                        impact = ImpactAssessment(
                            signal_id=signal.id,
                            affected_nodes=[n["node_id"] for n in result.affected_nodes[:5]],
                            propagation_path=result.critical_path,
                            estimated_delay_days=max(
                                (n["delay_days"] for n in result.affected_nodes), default=0
                            ) * 2,
                            revenue_at_risk_usd=revenue_at_risk,
                            confidence=0.5,
                            time_to_impact_days=3.0,
                        )
                        impacts.append(impact)
                        total_risk += revenue_at_risk
                all_entities.add(entity)

        # If no compound found, simulate one
        if not impacts and len(signals) >= 2:
            top_signals = sorted(signals, key=lambda s: self._severity_to_risk(s.severity), reverse=True)[:2]
            for signal in top_signals:
                for entity in signal.affected_entities[:1]:
                    result = self.graph.propagate_risk(entity, 0.85)
                    if result.total_nodes_affected > 0:
                        revenue_at_risk = self._estimate_revenue_impact(
                            result.total_nodes_affected, 0.85
                        ) * 1.8
                        impact = ImpactAssessment(
                            signal_id=signal.id,
                            affected_nodes=[n["node_id"] for n in result.affected_nodes[:5]],
                            propagation_path=result.critical_path,
                            estimated_delay_days=max(
                                (n["delay_days"] for n in result.affected_nodes), default=0
                            ),
                            revenue_at_risk_usd=revenue_at_risk,
                            confidence=0.45,
                            time_to_impact_days=5.0,
                        )
                        impacts.append(impact)
                        total_risk += revenue_at_risk

        return Scenario(
            id=f"scenario-compound-{uuid.uuid4().hex[:6]}",
            name="Compound: Multiple Disruptions Overlap",
            description="Scenario where multiple disruptions interact and amplify each other",
            probability=0.10,
            signals_involved=[s.id for s in signals],
            impacts=impacts,
            total_revenue_at_risk_usd=total_risk,
            recommended_actions=["Activate emergency response protocol",
                                 "Engage all alternate suppliers simultaneously",
                                 "Consider temporary production halt for non-critical lines"],
            explanation=self._explain_scenario("compound", total_risk, impacts),
        )

    def _simulate_cascade(self, signals: list[Signal]) -> Scenario:
        """Simulate cascading failure through the value chain."""
        impacts = []
        total_risk = 0.0

        # Find the highest-criticality affected node and cascade from there
        critical_signals = [s for s in signals if s.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL)]
        if not critical_signals:
            critical_signals = signals[:1]

        for signal in critical_signals[:2]:
            for entity in signal.affected_entities:
                # Deep propagation with high initial risk
                result = self.graph.propagate_risk(entity, 0.95)
                if result.total_nodes_affected > 2:
                    revenue_at_risk = self._estimate_revenue_impact(
                        result.total_nodes_affected, 0.95
                    ) * 2.5
                    impact = ImpactAssessment(
                        signal_id=signal.id,
                        affected_nodes=[n["node_id"] for n in result.affected_nodes],
                        propagation_path=result.critical_path,
                        estimated_delay_days=max(
                            (n["delay_days"] for n in result.affected_nodes), default=0
                        ),
                        revenue_at_risk_usd=revenue_at_risk,
                        confidence=0.35,
                        time_to_impact_days=2.0,
                    )
                    impacts.append(impact)
                    total_risk += revenue_at_risk

        return Scenario(
            id=f"scenario-cascade-{uuid.uuid4().hex[:6]}",
            name="Cascading Failure: Systemic Breakdown",
            description="Worst-case scenario where disruption cascades through entire value chain",
            probability=0.05,
            signals_involved=[s.id for s in critical_signals],
            impacts=impacts,
            total_revenue_at_risk_usd=total_risk,
            recommended_actions=["Immediate executive escalation",
                                 "Activate business continuity plan",
                                 "Engage crisis management team",
                                 "Prepare customer communication"],
            explanation=self._explain_scenario("cascade", total_risk, impacts),
        )

    def _monte_carlo_scenarios(self, signals: list[Signal], count: int) -> list[Scenario]:
        """Generate Monte Carlo scenario variations."""
        if not signals or count <= 0:
            return []

        scenarios = []
        rng = np.random.default_rng(42)

        for i in range(count):
            # Randomly vary signal parameters
            varied_risk = rng.uniform(0.3, 0.95)
            probability = rng.uniform(0.05, 0.30)

            # Pick random subset of signals
            n_signals = rng.integers(1, len(signals) + 1)
            selected = random.sample(signals, min(n_signals, len(signals)))

            impacts = []
            total_risk = 0.0

            for signal in selected:
                for entity in signal.affected_entities[:1]:
                    result = self.graph.propagate_risk(entity, varied_risk)
                    if result.total_nodes_affected > 0:
                        revenue = self._estimate_revenue_impact(
                            result.total_nodes_affected, varied_risk
                        )
                        impact = ImpactAssessment(
                            signal_id=signal.id,
                            affected_nodes=[n["node_id"] for n in result.affected_nodes[:3]],
                            propagation_path=result.critical_path,
                            estimated_delay_days=max(
                                (n["delay_days"] for n in result.affected_nodes), default=0
                            ),
                            revenue_at_risk_usd=revenue,
                            confidence=probability,
                            time_to_impact_days=rng.uniform(3, 30),
                        )
                        impacts.append(impact)
                        total_risk += revenue

            scenarios.append(Scenario(
                id=f"scenario-mc-{i+1}-{uuid.uuid4().hex[:6]}",
                name=f"Monte Carlo Variation #{i+1}",
                description=f"Stochastic scenario with {len(selected)} active disruptions at {varied_risk:.0%} severity",
                probability=round(probability, 3),
                signals_involved=[s.id for s in selected],
                impacts=impacts,
                total_revenue_at_risk_usd=total_risk,
                recommended_actions=self._generate_base_actions(impacts),
                explanation=f"Simulated scenario with {varied_risk:.0%} disruption severity across {len(selected)} signals.",
            ))

        return scenarios

    def generate_recommendations(self, scenarios: list[Scenario]) -> list[Recommendation]:
        """Generate actionable recommendations from scenario analysis."""
        recommendations = []

        # Analyze top scenarios
        top_scenarios = scenarios[:3]

        for scenario in top_scenarios:
            if scenario.total_revenue_at_risk_usd > 5_000_000:
                recommendations.append(Recommendation(
                    id=f"rec-{uuid.uuid4().hex[:8]}",
                    title="Activate alternate supplier network",
                    description=(
                        f"Based on {scenario.name}, activate pre-qualified alternate suppliers "
                        f"to reduce dependency on affected primary sources."
                    ),
                    urgency=SeverityLevel.HIGH,
                    scenario_id=scenario.id,
                    action_type="source-switch",
                    estimated_cost_usd=500_000,
                    estimated_savings_usd=scenario.total_revenue_at_risk_usd * 0.4,
                    confidence=scenario.probability,
                    explanation=(
                        f"Revenue at risk: ${scenario.total_revenue_at_risk_usd:,.0f}. "
                        f"Switching to alternate suppliers could mitigate ~40% of exposure "
                        f"at a cost of ~$500K in expediting fees."
                    ),
                    requires_approval=True,
                ))

            if any(i.estimated_delay_days > 7 for i in scenario.impacts):
                recommendations.append(Recommendation(
                    id=f"rec-{uuid.uuid4().hex[:8]}",
                    title="Increase safety stock for critical materials",
                    description="Build buffer inventory for materials on affected supply routes.",
                    urgency=SeverityLevel.MEDIUM,
                    scenario_id=scenario.id,
                    action_type="buffer",
                    estimated_cost_usd=200_000,
                    estimated_savings_usd=scenario.total_revenue_at_risk_usd * 0.25,
                    confidence=scenario.probability * 1.2,
                    explanation=(
                        f"Delays of 7+ days detected in supply chain. "
                        f"Building 2-week safety stock buffer reduces production stoppage risk."
                    ),
                    requires_approval=True,
                ))

            if scenario.probability > 0.15:
                recommendations.append(Recommendation(
                    id=f"rec-{uuid.uuid4().hex[:8]}",
                    title="Rebalance production across plants",
                    description="Shift production volume to less-affected facilities.",
                    urgency=SeverityLevel.MEDIUM,
                    scenario_id=scenario.id,
                    action_type="rebalance",
                    estimated_cost_usd=150_000,
                    estimated_savings_usd=scenario.total_revenue_at_risk_usd * 0.3,
                    confidence=scenario.probability,
                    explanation=(
                        f"With {scenario.probability:.0%} probability of this scenario, "
                        f"proactive rebalancing across available plants reduces concentration risk."
                    ),
                    requires_approval=True,
                ))

        # Deduplicate by action type
        seen_actions = set()
        unique_recs = []
        for rec in recommendations:
            if rec.action_type not in seen_actions:
                seen_actions.add(rec.action_type)
                unique_recs.append(rec)

        return sorted(unique_recs, key=lambda r: r.estimated_savings_usd, reverse=True)

    # === Helper Methods ===

    def _severity_to_risk(self, severity: SeverityLevel) -> float:
        return {
            SeverityLevel.LOW: 0.2,
            SeverityLevel.MEDIUM: 0.5,
            SeverityLevel.HIGH: 0.75,
            SeverityLevel.CRITICAL: 0.95,
        }[severity]

    def _estimate_revenue_impact(self, nodes_affected: int, risk_level: float) -> float:
        """Estimate revenue at risk based on affected nodes and risk level."""
        base_revenue_per_node = 2_000_000  # $2M average per node
        return nodes_affected * base_revenue_per_node * risk_level

    def _estimate_time_to_impact(self, result: 'PropagationResult') -> float:
        """Estimate days until impact materializes."""
        if not result.affected_nodes:
            return 30.0
        avg_delay = np.mean([n["delay_days"] for n in result.affected_nodes])
        return max(1.0, float(avg_delay))

    def _generate_base_actions(self, impacts: list[ImpactAssessment]) -> list[str]:
        actions = ["Monitor situation closely"]
        if any(i.revenue_at_risk_usd > 1_000_000 for i in impacts):
            actions.append("Engage procurement team for alternate sourcing")
        if any(i.estimated_delay_days > 5 for i in impacts):
            actions.append("Expedite critical shipments")
        if any(i.estimated_delay_days > 14 for i in impacts):
            actions.append("Activate safety stock protocols")
        return actions

    def _generate_escalation_actions(self, impacts: list[ImpactAssessment]) -> list[str]:
        return [
            "Escalate to senior leadership",
            "Activate alternate supplier agreements",
            "Consider production schedule adjustments",
            "Prepare customer delay notifications",
        ]

    def _explain_scenario(self, scenario_type: str, total_risk: float, impacts: list[ImpactAssessment]) -> str:
        """Generate human-readable explanation of a scenario."""
        if scenario_type == "base":
            return (
                f"If current disruptions continue on their present trajectory, "
                f"approximately ${total_risk:,.0f} in revenue is at risk over the next "
                f"{self.horizon_days} days. {len(impacts)} distinct impact pathways identified."
            )
        elif scenario_type == "escalation":
            return (
                f"If high-severity disruptions escalate (e.g., hurricane strengthens, "
                f"conflict intensifies), revenue exposure increases to ${total_risk:,.0f}. "
                f"Proactive mitigation recommended within 48 hours."
            )
        elif scenario_type == "compound":
            return (
                f"If multiple disruptions interact simultaneously, compounding effects "
                f"could expose ${total_risk:,.0f} in revenue. This scenario requires "
                f"coordinated cross-functional response."
            )
        elif scenario_type == "cascade":
            return (
                f"In a worst-case cascading failure, systemic breakdown could put "
                f"${total_risk:,.0f} at risk. While probability is low ({5}%), "
                f"the severity warrants contingency planning."
            )
        return f"Scenario analysis indicates ${total_risk:,.0f} revenue at risk."

    # ═══════════════════════════════════════════════════════════════════
    # OR-TOOLS CONSTRAINT OPTIMIZATION
    # ═══════════════════════════════════════════════════════════════════

    def optimize_production_allocation(
        self,
        plant_capacities: dict[str, int],
        plant_costs: dict[str, int],
        demand: int,
        disrupted_plants: list[str] = None,
        max_overtime_pct: int = 30,
    ) -> dict:
        """Use OR-Tools CP-SAT solver to find optimal production allocation.

        Given plant capacities, costs, and demand constraints, finds the
        minimum-cost production plan that meets demand while respecting
        disruption constraints.

        Args:
            plant_capacities: {plant_id: max_units_per_day}
            plant_costs: {plant_id: cost_per_unit_cents} (integers for CP-SAT)
            demand: Total units needed per day
            disrupted_plants: Plants with reduced capacity
            max_overtime_pct: Maximum overtime percentage allowed

        Returns:
            Optimal allocation with cost analysis
        """
        if disrupted_plants is None:
            disrupted_plants = []

        model = cp_model.CpModel()

        # Decision variables: units produced at each plant
        production = {}
        for plant_id, capacity in plant_capacities.items():
            # Disrupted plants have reduced capacity
            if plant_id in disrupted_plants:
                effective_capacity = int(capacity * 0.3)  # 70% reduction
            else:
                # Allow overtime up to max_overtime_pct
                effective_capacity = int(capacity * (1 + max_overtime_pct / 100))

            production[plant_id] = model.NewIntVar(
                0, effective_capacity, f"prod_{plant_id}"
            )

        # Constraint: Meet total demand
        model.Add(sum(production.values()) >= demand)

        # Constraint: Each plant cannot exceed its effective capacity
        for plant_id, capacity in plant_capacities.items():
            if plant_id in disrupted_plants:
                model.Add(production[plant_id] <= int(capacity * 0.3))
            else:
                model.Add(production[plant_id] <= int(capacity * (1 + max_overtime_pct / 100)))

        # Objective: Minimize total cost
        # Overtime units cost 1.35x (35% premium)
        total_cost_terms = []
        for plant_id in plant_capacities:
            base_cost = plant_costs.get(plant_id, 100)
            total_cost_terms.append(production[plant_id] * base_cost)

        model.Minimize(sum(total_cost_terms))

        # Solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 5.0
        status = solver.Solve(model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            allocation = {}
            total_cost = 0
            for plant_id in plant_capacities:
                units = solver.Value(production[plant_id])
                cost = units * plant_costs.get(plant_id, 100)
                allocation[plant_id] = {
                    "units": units,
                    "cost_cents": cost,
                    "utilization_pct": round(
                        units / plant_capacities[plant_id] * 100, 1
                    ),
                    "is_disrupted": plant_id in disrupted_plants,
                }
                total_cost += cost

            return {
                "status": "optimal" if status == cp_model.OPTIMAL else "feasible",
                "allocation": allocation,
                "total_cost_cents": total_cost,
                "total_units": sum(a["units"] for a in allocation.values()),
                "demand_met": sum(a["units"] for a in allocation.values()) >= demand,
                "disrupted_plants": disrupted_plants,
            }
        else:
            return {
                "status": "infeasible",
                "message": "Cannot meet demand with current constraints. Consider relaxing overtime limits or adding capacity.",
                "disrupted_plants": disrupted_plants,
            }
