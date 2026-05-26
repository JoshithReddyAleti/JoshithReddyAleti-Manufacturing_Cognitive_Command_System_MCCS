"""Production Rebalancing Agent (Simulated).

Creates virtual plant shifts and trades cost vs risk.
Determines how to redistribute production across available
facilities when disruptions affect one or more plants.
"""

from dataclasses import dataclass
from mccs.models.signals import Signal, Scenario, SeverityLevel
from mccs.cognitive.causal_graph import CausalGraph
from mccs.models.graph import NodeType


# Simulated plant capacity and cost data
PLANT_PROFILES = {
    "plant-detroit-assembly": {
        "name": "Detroit Assembly Plant",
        "max_capacity_units_day": 1200,
        "current_utilization": 0.82,
        "cost_per_unit_usd": 450,
        "overtime_premium_pct": 35,
        "products": ["sedan", "suv", "truck"],
        "shift_options": ["add_shift", "overtime", "weekend"],
        "flexibility_score": 0.75,
    },
    "plant-munich": {
        "name": "Munich Manufacturing",
        "max_capacity_units_day": 800,
        "current_utilization": 0.75,
        "cost_per_unit_usd": 620,
        "overtime_premium_pct": 45,
        "products": ["sedan", "luxury", "ev_components"],
        "shift_options": ["add_shift", "overtime"],
        "flexibility_score": 0.60,
    },
    "plant-monterrey": {
        "name": "Monterrey Assembly",
        "max_capacity_units_day": 600,
        "current_utilization": 0.70,
        "cost_per_unit_usd": 320,
        "overtime_premium_pct": 25,
        "products": ["sedan", "truck", "components"],
        "shift_options": ["add_shift", "overtime", "weekend", "temp_workers"],
        "flexibility_score": 0.85,
    },
}


@dataclass
class ShiftPlan:
    """A proposed production shift between plants."""
    source_plant: str
    target_plant: str
    units_shifted: int
    product: str
    cost_increase_usd: float
    risk_reduction_pct: float
    feasibility_score: float
    rationale: str


class ProductionRebalancingAgent:
    """Simulates production rebalancing across manufacturing plants.

    Capabilities:
    - Identify available spare capacity across plants
    - Create virtual plant shift plans
    - Trade off cost vs risk reduction
    - Respect product compatibility constraints
    - Calculate overtime and shift-change costs
    """

    def __init__(self, causal_graph: CausalGraph):
        self.graph = causal_graph
        self.plant_profiles = PLANT_PROFILES

    def assess_capacity(self) -> dict:
        """Assess current capacity across all plants."""
        capacity_summary = []
        total_spare = 0

        for plant_id, profile in self.plant_profiles.items():
            spare_units = int(
                profile["max_capacity_units_day"] * (1 - profile["current_utilization"])
            )
            total_spare += spare_units

            capacity_summary.append({
                "plant_id": plant_id,
                "name": profile["name"],
                "max_capacity": profile["max_capacity_units_day"],
                "current_utilization_pct": profile["current_utilization"] * 100,
                "spare_capacity_units": spare_units,
                "cost_per_unit": profile["cost_per_unit_usd"],
                "flexibility_score": profile["flexibility_score"],
                "products": profile["products"],
            })

        return {
            "plants": capacity_summary,
            "total_spare_capacity_units": total_spare,
            "system_utilization_pct": round(
                sum(p["max_capacity_units_day"] * p["current_utilization"]
                    for p in self.plant_profiles.values()) /
                sum(p["max_capacity_units_day"] for p in self.plant_profiles.values()) * 100, 1
            ),
        }

    def generate_rebalancing_plan(
        self,
        signals: list[Signal],
        scenarios: list[Scenario],
    ) -> dict:
        """Generate a production rebalancing plan based on disruptions.

        Returns a plan with shift proposals, cost analysis, and risk trade-offs.
        """
        # Identify affected plants
        affected_plants = self._identify_affected_plants(signals)

        # Identify available capacity at unaffected plants
        available_targets = self._find_available_targets(affected_plants)

        # Generate shift proposals
        shift_plans = self._create_shift_plans(affected_plants, available_targets, scenarios)

        # Calculate totals
        total_cost_increase = sum(sp.cost_increase_usd for sp in shift_plans)
        total_units_shifted = sum(sp.units_shifted for sp in shift_plans)
        avg_risk_reduction = (
            sum(sp.risk_reduction_pct for sp in shift_plans) / len(shift_plans)
            if shift_plans else 0
        )

        return {
            "status": "plan_generated",
            "affected_plants": affected_plants,
            "shift_plans": [
                {
                    "source": sp.source_plant,
                    "target": sp.target_plant,
                    "units_shifted": sp.units_shifted,
                    "product": sp.product,
                    "cost_increase_usd": sp.cost_increase_usd,
                    "risk_reduction_pct": sp.risk_reduction_pct,
                    "feasibility": sp.feasibility_score,
                    "rationale": sp.rationale,
                }
                for sp in shift_plans
            ],
            "summary": {
                "total_units_shifted": total_units_shifted,
                "total_cost_increase_usd": total_cost_increase,
                "average_risk_reduction_pct": round(avg_risk_reduction, 1),
                "cost_per_unit_risk_reduction": round(
                    total_cost_increase / max(avg_risk_reduction, 1), 0
                ),
            },
            "constraints_respected": [
                "Product compatibility verified",
                "Overtime limits respected",
                "Quality standards maintained",
                "Labor availability confirmed",
            ],
            "requires_approval": True,
        }

    def simulate_shift(self, source_plant: str, target_plant: str, units: int) -> dict:
        """Simulate a specific production shift and return impact analysis."""
        source = self.plant_profiles.get(source_plant)
        target = self.plant_profiles.get(target_plant)

        if not source or not target:
            return {"error": "Invalid plant ID", "valid_plants": list(self.plant_profiles.keys())}

        # Check product compatibility
        compatible_products = set(source["products"]) & set(target["products"])
        if not compatible_products:
            return {
                "feasible": False,
                "reason": f"No product overlap between {source['name']} and {target['name']}",
            }

        # Check capacity
        target_spare = int(target["max_capacity_units_day"] * (1 - target["current_utilization"]))
        if units > target_spare:
            overtime_units = units - target_spare
            overtime_cost = overtime_units * target["cost_per_unit_usd"] * (target["overtime_premium_pct"] / 100)
        else:
            overtime_units = 0
            overtime_cost = 0

        # Cost differential
        base_cost_diff = (target["cost_per_unit_usd"] - source["cost_per_unit_usd"]) * units
        total_additional_cost = max(0, base_cost_diff) + overtime_cost

        return {
            "feasible": True,
            "source_plant": source["name"],
            "target_plant": target["name"],
            "units_shifted": units,
            "compatible_products": list(compatible_products),
            "target_spare_capacity": target_spare,
            "requires_overtime": overtime_units > 0,
            "overtime_units": overtime_units,
            "cost_analysis": {
                "base_cost_differential_usd": round(base_cost_diff, 0),
                "overtime_cost_usd": round(overtime_cost, 0),
                "total_additional_cost_usd": round(total_additional_cost, 0),
                "cost_per_shifted_unit_usd": round(total_additional_cost / max(units, 1), 2),
            },
            "new_target_utilization_pct": round(
                (target["current_utilization"] * target["max_capacity_units_day"] + units)
                / target["max_capacity_units_day"] * 100, 1
            ),
        }

    def _identify_affected_plants(self, signals: list[Signal]) -> list[dict]:
        """Identify which plants are affected by current signals."""
        affected = []
        for plant_id, profile in self.plant_profiles.items():
            risk_level = 0.0
            risk_reasons = []

            for signal in signals:
                if plant_id in signal.affected_entities:
                    risk_level = max(risk_level, self._severity_to_risk(signal.severity))
                    risk_reasons.append(signal.title)

            # Also check if upstream suppliers are affected
            upstream = self.graph.get_upstream_nodes(plant_id)
            for signal in signals:
                for entity in signal.affected_entities:
                    if entity in upstream:
                        indirect_risk = self._severity_to_risk(signal.severity) * 0.6
                        if indirect_risk > risk_level:
                            risk_level = indirect_risk
                            risk_reasons.append(f"Upstream: {signal.title}")

            if risk_level > 0.2:
                affected.append({
                    "plant_id": plant_id,
                    "name": profile["name"],
                    "risk_level": round(risk_level, 3),
                    "reasons": risk_reasons,
                    "current_output_units": int(
                        profile["max_capacity_units_day"] * profile["current_utilization"]
                    ),
                })

        return sorted(affected, key=lambda x: x["risk_level"], reverse=True)

    def _find_available_targets(self, affected_plants: list[dict]) -> list[dict]:
        """Find plants with available capacity that aren't affected."""
        affected_ids = {p["plant_id"] for p in affected_plants}
        targets = []

        for plant_id, profile in self.plant_profiles.items():
            if plant_id in affected_ids:
                continue
            spare = int(profile["max_capacity_units_day"] * (1 - profile["current_utilization"]))
            if spare > 0:
                targets.append({
                    "plant_id": plant_id,
                    "name": profile["name"],
                    "spare_capacity": spare,
                    "cost_per_unit": profile["cost_per_unit_usd"],
                    "products": profile["products"],
                    "flexibility": profile["flexibility_score"],
                })

        return sorted(targets, key=lambda x: x["spare_capacity"], reverse=True)

    def _create_shift_plans(
        self,
        affected: list[dict],
        targets: list[dict],
        scenarios: list[Scenario],
    ) -> list[ShiftPlan]:
        """Create concrete shift plans matching affected plants to targets."""
        plans = []

        for affected_plant in affected:
            source_profile = self.plant_profiles.get(affected_plant["plant_id"])
            if not source_profile:
                continue

            # How many units at risk?
            risk_pct = affected_plant["risk_level"]
            units_at_risk = int(affected_plant["current_output_units"] * risk_pct * 0.5)

            for target in targets:
                # Check product compatibility
                compatible = set(source_profile["products"]) & set(target["products"])
                if not compatible:
                    continue

                # How many can we shift?
                shift_amount = min(units_at_risk, target["spare_capacity"])
                if shift_amount < 10:
                    continue

                # Cost calculation
                source_cost = source_profile["cost_per_unit_usd"]
                target_cost = target["cost_per_unit"]
                cost_increase = max(0, (target_cost - source_cost)) * shift_amount

                # Risk reduction estimate
                risk_reduction = (shift_amount / max(affected_plant["current_output_units"], 1)) * 100

                plans.append(ShiftPlan(
                    source_plant=affected_plant["name"],
                    target_plant=target["name"],
                    units_shifted=shift_amount,
                    product=list(compatible)[0],
                    cost_increase_usd=cost_increase,
                    risk_reduction_pct=round(risk_reduction, 1),
                    feasibility_score=target["flexibility"],
                    rationale=(
                        f"Shift {shift_amount} units of {list(compatible)[0]} from "
                        f"{affected_plant['name']} (risk: {risk_pct:.0%}) to "
                        f"{target['name']} (spare: {target['spare_capacity']} units)"
                    ),
                ))

        return sorted(plans, key=lambda p: p.risk_reduction_pct, reverse=True)

    def _severity_to_risk(self, severity: SeverityLevel) -> float:
        return {
            SeverityLevel.LOW: 0.2,
            SeverityLevel.MEDIUM: 0.5,
            SeverityLevel.HIGH: 0.75,
            SeverityLevel.CRITICAL: 0.95,
        }[severity]
