"""Supply Chain Reasoning Agent.

Suggests alternatives, scores sourcing risk, and identifies
mitigation strategies for supply chain disruptions.
"""

from mccs.models.signals import Signal, SeverityLevel
from mccs.models.graph import GraphNode, NodeType
from mccs.cognitive.causal_graph import CausalGraph


# Alternate supplier database (simulated)
ALTERNATE_SUPPLIERS = {
    "supplier-electronics-cn": [
        {"id": "alt-electronics-vn", "name": "Vietnam Electronics Co", "country": "vietnam",
         "lead_time_days": 28, "cost_premium_pct": 12, "quality_score": 0.82},
        {"id": "alt-electronics-in", "name": "India Electronics Ltd", "country": "india",
         "lead_time_days": 25, "cost_premium_pct": 8, "quality_score": 0.78},
    ],
    "supplier-rare-earth": [
        {"id": "alt-rare-earth-au", "name": "Australian Minerals", "country": "australia",
         "lead_time_days": 35, "cost_premium_pct": 25, "quality_score": 0.90},
    ],
    "supplier-semiconductors-tw": [
        {"id": "alt-semi-kr", "name": "Samsung Foundry", "country": "south_korea",
         "lead_time_days": 50, "cost_premium_pct": 15, "quality_score": 0.92},
        {"id": "alt-semi-us", "name": "Intel Foundry Services", "country": "usa",
         "lead_time_days": 40, "cost_premium_pct": 20, "quality_score": 0.88},
    ],
    "supplier-auto-parts-mx": [
        {"id": "alt-auto-us", "name": "US Auto Components", "country": "usa",
         "lead_time_days": 7, "cost_premium_pct": 18, "quality_score": 0.85},
    ],
    "supplier-gulf-chemicals": [
        {"id": "alt-chem-eu", "name": "BASF Europe", "country": "germany",
         "lead_time_days": 14, "cost_premium_pct": 10, "quality_score": 0.95},
    ],
}


class SupplyChainAgent:
    """Reasons about supply chain alternatives and risk mitigation.

    Capabilities:
    - Score sourcing risk for each supplier
    - Suggest alternate suppliers when primary is disrupted
    - Evaluate trade-offs (cost vs. risk vs. lead time)
    - Recommend diversification strategies
    """

    def __init__(self, causal_graph: CausalGraph):
        self.graph = causal_graph

    def assess_supplier_risk(self, signals: list[Signal]) -> list[dict]:
        """Assess risk for all suppliers based on current signals."""
        supplier_risks = []

        for node_id, node in self.graph._nodes.items():
            if node.node_type != NodeType.SUPPLIER:
                continue

            # Calculate risk from signals
            risk_score = 0.0
            risk_factors = []

            for signal in signals:
                if node_id in signal.affected_entities:
                    risk_score = max(risk_score, self._severity_to_score(signal.severity))
                    risk_factors.append(signal.title)
                elif node.country and node.country.lower() in (signal.location or "").lower():
                    risk_score = max(risk_score, self._severity_to_score(signal.severity) * 0.6)
                    risk_factors.append(f"Regional: {signal.title}")

            # Get alternates
            alternates = ALTERNATE_SUPPLIERS.get(node_id, [])

            supplier_risks.append({
                "supplier_id": node_id,
                "name": node.name,
                "country": node.country,
                "risk_score": round(risk_score, 3),
                "risk_level": self._score_to_level(risk_score),
                "risk_factors": risk_factors,
                "alternates_available": len(alternates),
                "criticality": node.criticality,
                "lead_time_days": node.lead_time_days,
            })

        return sorted(supplier_risks, key=lambda x: x["risk_score"], reverse=True)

    def suggest_alternatives(self, supplier_id: str) -> list[dict]:
        """Suggest alternate suppliers for a given primary supplier."""
        alternates = ALTERNATE_SUPPLIERS.get(supplier_id, [])
        if not alternates:
            return [{"message": f"No pre-qualified alternates for {supplier_id}"}]

        # Score alternates
        scored = []
        for alt in alternates:
            # Composite score: lower is better
            score = (
                alt["lead_time_days"] * 0.3 +
                alt["cost_premium_pct"] * 0.4 +
                (1 - alt["quality_score"]) * 100 * 0.3
            )
            scored.append({**alt, "composite_score": round(score, 2)})

        return sorted(scored, key=lambda x: x["composite_score"])

    def evaluate_sourcing_strategy(self, signals: list[Signal]) -> dict:
        """Evaluate overall sourcing strategy given current disruptions."""
        risks = self.assess_supplier_risk(signals)
        high_risk = [r for r in risks if r["risk_level"] in ("high", "critical")]
        critical_without_alt = [
            r for r in high_risk
            if r["alternates_available"] == 0 and r["criticality"] > 0.7
        ]

        return {
            "total_suppliers_monitored": len(risks),
            "high_risk_suppliers": len(high_risk),
            "critical_single_source": len(critical_without_alt),
            "diversification_score": self._calc_diversification_score(risks),
            "top_risks": high_risk[:5],
            "immediate_actions": self._generate_actions(high_risk),
            "strategic_recommendations": self._strategic_recommendations(risks),
        }

    def _severity_to_score(self, severity: SeverityLevel) -> float:
        return {
            SeverityLevel.LOW: 0.2,
            SeverityLevel.MEDIUM: 0.5,
            SeverityLevel.HIGH: 0.75,
            SeverityLevel.CRITICAL: 0.95,
        }[severity]

    def _score_to_level(self, score: float) -> str:
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.3:
            return "medium"
        return "low"

    def _calc_diversification_score(self, risks: list[dict]) -> float:
        """Score 0-100 for supply base diversification."""
        if not risks:
            return 0.0
        with_alts = sum(1 for r in risks if r["alternates_available"] > 0)
        return round((with_alts / len(risks)) * 100, 1)

    def _generate_actions(self, high_risk: list[dict]) -> list[str]:
        actions = []
        for risk in high_risk[:3]:
            if risk["alternates_available"] > 0:
                actions.append(f"Activate alternate for {risk['name']} (risk: {risk['risk_level']})")
            else:
                actions.append(f"URGENT: Find alternate for {risk['name']} - single source, high risk")
        return actions

    def _strategic_recommendations(self, risks: list[dict]) -> list[str]:
        recs = []
        countries = {}
        for r in risks:
            c = r.get("country", "unknown")
            countries[c] = countries.get(c, 0) + 1

        for country, count in countries.items():
            if count > 2:
                recs.append(f"Reduce geographic concentration in {country} ({count} suppliers)")

        single_source = [r for r in risks if r["alternates_available"] == 0 and r["criticality"] > 0.6]
        if single_source:
            recs.append(f"Qualify alternates for {len(single_source)} critical single-source suppliers")

        return recs
