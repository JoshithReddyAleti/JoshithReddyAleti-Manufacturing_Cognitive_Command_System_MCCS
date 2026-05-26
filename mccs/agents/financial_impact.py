"""Financial Impact Agent.

Calculates revenue at risk, inventory exposure, and margin erosion
from disruption scenarios.
"""

from mccs.models.signals import Signal, Scenario, SeverityLevel


# Simulated financial parameters
FINANCIAL_PARAMS = {
    "daily_revenue_usd": 15_000_000,
    "gross_margin_pct": 0.32,
    "inventory_value_usd": 450_000_000,
    "working_capital_usd": 280_000_000,
    "insurance_coverage_pct": 0.60,
    "penalty_per_day_late_usd": 250_000,
}

# Revenue contribution by node
NODE_REVENUE_CONTRIBUTION = {
    "plant-detroit-assembly": 8_000_000,
    "plant-munich": 4_500_000,
    "plant-monterrey": 2_500_000,
    "market-north-america": 10_000_000,
    "market-europe": 5_000_000,
}


class FinancialImpactAgent:
    """Calculates financial exposure from disruption scenarios.

    Provides:
    - Revenue at risk calculations
    - Inventory exposure analysis
    - Margin erosion estimates
    - Cost of mitigation vs. cost of inaction
    """

    def __init__(self):
        self.params = FINANCIAL_PARAMS

    def calculate_impact(self, scenarios: list[Scenario]) -> dict:
        """Calculate comprehensive financial impact across scenarios."""
        if not scenarios:
            return {"status": "no_scenarios", "total_exposure": 0}

        # Weighted expected loss
        expected_loss = sum(
            s.total_revenue_at_risk_usd * s.probability
            for s in scenarios
        )

        # Worst case
        worst_case = max(s.total_revenue_at_risk_usd for s in scenarios)

        # Best case (lowest risk scenario)
        best_case = min(s.total_revenue_at_risk_usd for s in scenarios)

        return {
            "expected_loss_usd": round(expected_loss, 0),
            "worst_case_usd": round(worst_case, 0),
            "best_case_usd": round(best_case, 0),
            "daily_revenue_at_risk": self._daily_risk(scenarios),
            "margin_erosion_pct": self._margin_erosion(expected_loss),
            "inventory_exposure": self._inventory_exposure(scenarios),
            "penalty_exposure_usd": self._penalty_exposure(scenarios),
            "insurance_offset_usd": round(expected_loss * self.params["insurance_coverage_pct"], 0),
            "net_exposure_usd": round(expected_loss * (1 - self.params["insurance_coverage_pct"]), 0),
            "mitigation_roi": self._mitigation_roi(scenarios),
        }

    def revenue_at_risk_by_node(self, scenarios: list[Scenario]) -> list[dict]:
        """Break down revenue at risk by affected node."""
        node_exposure = {}

        for scenario in scenarios:
            for impact in scenario.impacts:
                for node_id in impact.affected_nodes:
                    if node_id not in node_exposure:
                        node_exposure[node_id] = {
                            "node_id": node_id,
                            "total_exposure": 0,
                            "scenarios_affected": 0,
                            "max_delay_days": 0,
                        }
                    daily_rev = NODE_REVENUE_CONTRIBUTION.get(node_id, 1_000_000)
                    exposure = daily_rev * impact.estimated_delay_days * scenario.probability
                    node_exposure[node_id]["total_exposure"] += exposure
                    node_exposure[node_id]["scenarios_affected"] += 1
                    node_exposure[node_id]["max_delay_days"] = max(
                        node_exposure[node_id]["max_delay_days"],
                        impact.estimated_delay_days,
                    )

        result = sorted(node_exposure.values(), key=lambda x: x["total_exposure"], reverse=True)
        return result

    def cost_benefit_analysis(self, scenarios: list[Scenario]) -> dict:
        """Compare cost of mitigation vs. cost of inaction."""
        expected_loss = sum(s.total_revenue_at_risk_usd * s.probability for s in scenarios)

        mitigation_options = [
            {
                "action": "Activate alternate suppliers",
                "cost_usd": 500_000,
                "risk_reduction_pct": 40,
                "net_benefit_usd": expected_loss * 0.4 - 500_000,
                "roi_pct": round(((expected_loss * 0.4 - 500_000) / 500_000) * 100, 1),
            },
            {
                "action": "Build safety stock (2 weeks)",
                "cost_usd": 200_000,
                "risk_reduction_pct": 25,
                "net_benefit_usd": expected_loss * 0.25 - 200_000,
                "roi_pct": round(((expected_loss * 0.25 - 200_000) / 200_000) * 100, 1),
            },
            {
                "action": "Expedite critical shipments",
                "cost_usd": 150_000,
                "risk_reduction_pct": 15,
                "net_benefit_usd": expected_loss * 0.15 - 150_000,
                "roi_pct": round(((expected_loss * 0.15 - 150_000) / 150_000) * 100, 1),
            },
            {
                "action": "Production rebalancing",
                "cost_usd": 300_000,
                "risk_reduction_pct": 30,
                "net_benefit_usd": expected_loss * 0.30 - 300_000,
                "roi_pct": round(((expected_loss * 0.30 - 300_000) / 300_000) * 100, 1),
            },
        ]

        return {
            "expected_loss_without_action": round(expected_loss, 0),
            "mitigation_options": sorted(mitigation_options, key=lambda x: x["roi_pct"], reverse=True),
            "recommended_bundle": {
                "actions": ["Activate alternate suppliers", "Build safety stock (2 weeks)"],
                "total_cost_usd": 700_000,
                "total_risk_reduction_pct": 55,
                "net_benefit_usd": round(expected_loss * 0.55 - 700_000, 0),
            },
        }

    def _daily_risk(self, scenarios: list[Scenario]) -> float:
        """Calculate daily revenue at risk."""
        weighted = sum(s.total_revenue_at_risk_usd * s.probability for s in scenarios)
        avg_duration = 14  # Assume 14-day average disruption
        return round(weighted / avg_duration, 0)

    def _margin_erosion(self, expected_loss: float) -> float:
        """Calculate margin erosion percentage."""
        annual_revenue = self.params["daily_revenue_usd"] * 365
        return round((expected_loss / annual_revenue) * 100, 2)

    def _inventory_exposure(self, scenarios: list[Scenario]) -> dict:
        """Calculate inventory at risk."""
        total_inv = self.params["inventory_value_usd"]
        # Assume 20% of inventory is on affected routes
        at_risk_pct = 0.20
        return {
            "total_inventory_usd": total_inv,
            "at_risk_usd": round(total_inv * at_risk_pct, 0),
            "at_risk_pct": at_risk_pct * 100,
        }

    def _penalty_exposure(self, scenarios: list[Scenario]) -> float:
        """Calculate late delivery penalty exposure."""
        max_delay = 0
        for s in scenarios:
            for impact in s.impacts:
                max_delay = max(max_delay, impact.estimated_delay_days)
        return max_delay * self.params["penalty_per_day_late_usd"]

    def _mitigation_roi(self, scenarios: list[Scenario]) -> dict:
        """Calculate ROI of taking mitigation action."""
        expected_loss = sum(s.total_revenue_at_risk_usd * s.probability for s in scenarios)
        mitigation_cost = 700_000  # Typical bundle cost
        risk_reduction = 0.55
        savings = expected_loss * risk_reduction
        return {
            "investment_usd": mitigation_cost,
            "expected_savings_usd": round(savings, 0),
            "roi_pct": round(((savings - mitigation_cost) / mitigation_cost) * 100, 1),
            "payback_days": round(mitigation_cost / (savings / 30), 1) if savings > 0 else 999,
        }
