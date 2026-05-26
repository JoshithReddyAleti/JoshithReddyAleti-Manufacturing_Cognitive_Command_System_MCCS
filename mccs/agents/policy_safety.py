"""Policy & Safety Agent.

Enforces rules and constraints on all recommendations:
- Maximum risk tolerance thresholds
- Ethical sourcing requirements
- Regulatory compliance limits
- Safety constraints on production changes

This agent acts as a guardrail — it reviews recommendations from
other agents and flags or blocks those that violate policy.
"""

from dataclasses import dataclass, field
from enum import Enum
from mccs.models.signals import Signal, Scenario, Recommendation, SeverityLevel


class PolicyViolationType(str, Enum):
    """Types of policy violations."""
    RISK_TOLERANCE_EXCEEDED = "risk_tolerance_exceeded"
    ETHICAL_SOURCING = "ethical_sourcing"
    REGULATORY_LIMIT = "regulatory_limit"
    SAFETY_CONSTRAINT = "safety_constraint"
    COST_THRESHOLD = "cost_threshold"
    CONCENTRATION_RISK = "concentration_risk"


@dataclass
class PolicyViolation:
    """A detected policy violation."""
    violation_type: PolicyViolationType
    severity: str  # "warning" or "block"
    description: str
    affected_recommendation: str = ""
    remediation: str = ""


@dataclass
class PolicyConfig:
    """Configurable policy parameters."""
    # Risk tolerance
    max_acceptable_risk_score: float = 0.85
    max_single_supplier_dependency_pct: float = 60.0
    max_single_country_concentration_pct: float = 50.0

    # Financial limits
    max_single_action_cost_usd: float = 2_000_000
    max_total_mitigation_budget_usd: float = 5_000_000
    min_roi_threshold_pct: float = 50.0

    # Ethical sourcing
    banned_countries: list[str] = field(default_factory=lambda: [
        "north_korea", "syria", "iran"
    ])
    restricted_countries: list[str] = field(default_factory=lambda: [
        "russia", "belarus", "myanmar"
    ])

    # Safety
    max_overtime_hours_per_week: int = 60
    min_safety_stock_days: int = 3
    max_capacity_utilization_pct: float = 95.0

    # Regulatory
    max_tariff_avoidance_risk: float = 0.3
    require_dual_source_for_critical: bool = True


class PolicySafetyAgent:
    """Enforces organizational policies and safety constraints.

    Reviews all recommendations and scenarios against configurable
    policy rules. Can flag warnings or block actions that violate policy.

    This agent ensures the system never recommends:
    - Sourcing from banned/sanctioned countries
    - Exceeding risk tolerance thresholds
    - Violating labor safety regulations
    - Spending beyond authorized limits
    - Creating dangerous concentration risks
    """

    def __init__(self, config: PolicyConfig = None):
        self.config = config or PolicyConfig()
        self._violations: list[PolicyViolation] = []

    def review_recommendations(
        self,
        recommendations: list[Recommendation],
        signals: list[Signal],
        scenarios: list[Scenario],
    ) -> dict:
        """Review all recommendations against policy constraints.

        Returns:
            Dict with approved, flagged, and blocked recommendations
        """
        self._violations = []
        approved = []
        flagged = []
        blocked = []

        for rec in recommendations:
            violations = self._check_recommendation(rec, signals)

            if not violations:
                approved.append(rec)
            else:
                blocking = [v for v in violations if v.severity == "block"]
                warnings = [v for v in violations if v.severity == "warning"]

                if blocking:
                    blocked.append({
                        "recommendation": rec,
                        "violations": blocking,
                        "reason": blocking[0].description,
                    })
                else:
                    flagged.append({
                        "recommendation": rec,
                        "warnings": warnings,
                        "note": "Approved with conditions",
                    })
                    approved.append(rec)  # Warnings don't block

                self._violations.extend(violations)

        return {
            "approved": [r.model_dump() for r in approved],
            "approved_count": len(approved),
            "flagged": [
                {"title": f["recommendation"].title, "warnings": [w.description for w in f["warnings"]]}
                for f in flagged
            ],
            "flagged_count": len(flagged),
            "blocked": [
                {"title": b["recommendation"].title, "reason": b["reason"]}
                for b in blocked
            ],
            "blocked_count": len(blocked),
            "total_violations": len(self._violations),
            "policy_summary": self._generate_policy_summary(),
        }

    def check_scenario_risk(self, scenarios: list[Scenario]) -> dict:
        """Check if any scenario exceeds risk tolerance."""
        violations = []
        max_risk = self.config.max_acceptable_risk_score

        for scenario in scenarios:
            if scenario.probability > max_risk:
                violations.append(PolicyViolation(
                    violation_type=PolicyViolationType.RISK_TOLERANCE_EXCEEDED,
                    severity="warning",
                    description=(
                        f"Scenario '{scenario.name}' has probability {scenario.probability:.0%} "
                        f"which exceeds max tolerance of {max_risk:.0%}"
                    ),
                    remediation="Consider immediate mitigation actions",
                ))

        # Check for concentration risk
        all_affected = []
        for scenario in scenarios:
            for impact in scenario.impacts:
                all_affected.extend(impact.affected_nodes)

        if all_affected:
            from collections import Counter
            node_counts = Counter(all_affected)
            most_common = node_counts.most_common(1)[0]
            concentration = most_common[1] / len(scenarios)
            if concentration > 0.7:
                violations.append(PolicyViolation(
                    violation_type=PolicyViolationType.CONCENTRATION_RISK,
                    severity="warning",
                    description=(
                        f"Node '{most_common[0]}' appears in {most_common[1]}/{len(scenarios)} "
                        f"scenarios — high concentration risk"
                    ),
                    remediation="Diversify supply chain to reduce single-point-of-failure",
                ))

        return {
            "risk_within_tolerance": len(violations) == 0,
            "violations": [
                {"type": v.violation_type.value, "description": v.description, "remediation": v.remediation}
                for v in violations
            ],
            "max_tolerance": max_risk,
        }

    def validate_sourcing_decision(self, supplier_country: str, product: str) -> dict:
        """Validate a sourcing decision against ethical and regulatory policy."""
        country_lower = supplier_country.lower().replace(" ", "_")

        if country_lower in self.config.banned_countries:
            return {
                "approved": False,
                "severity": "block",
                "reason": f"Sourcing from {supplier_country} is prohibited (sanctioned country)",
                "policy": "ethical_sourcing",
            }

        if country_lower in self.config.restricted_countries:
            return {
                "approved": True,
                "severity": "warning",
                "reason": (
                    f"Sourcing from {supplier_country} is restricted. "
                    f"Requires additional compliance review and documentation."
                ),
                "policy": "ethical_sourcing",
                "conditions": [
                    "Compliance officer approval required",
                    "Enhanced due diligence documentation",
                    "Quarterly review of supplier status",
                ],
            }

        return {
            "approved": True,
            "severity": "none",
            "reason": f"No policy restrictions for sourcing from {supplier_country}",
            "policy": "ethical_sourcing",
        }

    def check_production_safety(self, plant_id: str, proposed_utilization: float, overtime_hours: int) -> dict:
        """Check if a production change respects safety constraints."""
        violations = []

        if proposed_utilization > self.config.max_capacity_utilization_pct:
            violations.append(PolicyViolation(
                violation_type=PolicyViolationType.SAFETY_CONSTRAINT,
                severity="block",
                description=(
                    f"Proposed utilization {proposed_utilization:.0f}% exceeds "
                    f"safety maximum of {self.config.max_capacity_utilization_pct:.0f}%"
                ),
                remediation="Reduce production target or add capacity",
            ))

        if overtime_hours > self.config.max_overtime_hours_per_week:
            violations.append(PolicyViolation(
                violation_type=PolicyViolationType.SAFETY_CONSTRAINT,
                severity="block",
                description=(
                    f"Proposed overtime of {overtime_hours}h/week exceeds "
                    f"regulatory limit of {self.config.max_overtime_hours_per_week}h/week"
                ),
                remediation="Hire temporary workers or reduce shift targets",
            ))

        return {
            "safe": len(violations) == 0,
            "violations": [
                {"type": v.violation_type.value, "description": v.description, "remediation": v.remediation}
                for v in violations
            ],
            "plant_id": plant_id,
        }

    def get_policy_status(self) -> dict:
        """Get current policy configuration and violation history."""
        return {
            "config": {
                "max_risk_tolerance": self.config.max_acceptable_risk_score,
                "max_single_action_cost": self.config.max_single_action_cost_usd,
                "max_budget": self.config.max_total_mitigation_budget_usd,
                "min_roi": self.config.min_roi_threshold_pct,
                "banned_countries": self.config.banned_countries,
                "restricted_countries": self.config.restricted_countries,
                "max_overtime_hours": self.config.max_overtime_hours_per_week,
                "max_utilization": self.config.max_capacity_utilization_pct,
            },
            "total_violations_detected": len(self._violations),
            "violation_breakdown": self._violation_breakdown(),
        }

    def _check_recommendation(self, rec: Recommendation, signals: list[Signal]) -> list[PolicyViolation]:
        """Check a single recommendation against all policies."""
        violations = []

        # Cost threshold
        if rec.estimated_cost_usd > self.config.max_single_action_cost_usd:
            violations.append(PolicyViolation(
                violation_type=PolicyViolationType.COST_THRESHOLD,
                severity="warning",
                description=(
                    f"Action cost ${rec.estimated_cost_usd:,.0f} exceeds single-action "
                    f"limit of ${self.config.max_single_action_cost_usd:,.0f}"
                ),
                affected_recommendation=rec.title,
                remediation="Requires executive approval for budget override",
            ))

        # ROI threshold
        if rec.estimated_cost_usd > 0:
            roi = ((rec.estimated_savings_usd - rec.estimated_cost_usd) / rec.estimated_cost_usd) * 100
            if roi < self.config.min_roi_threshold_pct:
                violations.append(PolicyViolation(
                    violation_type=PolicyViolationType.COST_THRESHOLD,
                    severity="warning",
                    description=(
                        f"Action ROI of {roi:.0f}% is below minimum threshold "
                        f"of {self.config.min_roi_threshold_pct:.0f}%"
                    ),
                    affected_recommendation=rec.title,
                    remediation="Consider alternative actions with better ROI",
                ))

        # Check for ethical sourcing issues in source-switch recommendations
        if rec.action_type == "source-switch":
            # Check if any signal involves restricted countries
            for signal in signals:
                if signal.location and signal.location.lower() in self.config.restricted_countries:
                    violations.append(PolicyViolation(
                        violation_type=PolicyViolationType.ETHICAL_SOURCING,
                        severity="warning",
                        description=(
                            f"Source switch involves region with restricted status: "
                            f"{signal.location}"
                        ),
                        affected_recommendation=rec.title,
                        remediation="Verify alternate supplier is not in restricted territory",
                    ))

        return violations

    def _generate_policy_summary(self) -> str:
        """Generate human-readable policy compliance summary."""
        if not self._violations:
            return "All recommendations comply with organizational policy."

        blocking = [v for v in self._violations if v.severity == "block"]
        warnings = [v for v in self._violations if v.severity == "warning"]

        parts = []
        if blocking:
            parts.append(f"{len(blocking)} action(s) blocked by policy")
        if warnings:
            parts.append(f"{len(warnings)} warning(s) issued")

        return f"Policy review complete: {'; '.join(parts)}."

    def _violation_breakdown(self) -> dict:
        """Break down violations by type."""
        breakdown = {}
        for v in self._violations:
            key = v.violation_type.value
            breakdown[key] = breakdown.get(key, 0) + 1
        return breakdown
