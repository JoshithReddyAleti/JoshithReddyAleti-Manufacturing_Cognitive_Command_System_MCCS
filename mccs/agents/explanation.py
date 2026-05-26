"""Executive Explanation Agent.

The most important agent for trust. Transforms technical analysis
into clear, actionable executive communication.

Turns: "Probability × severity = 0.42"
Into: "If left unaddressed, production loss risk increases materially within 14 days."
"""

from mccs.models.signals import Signal, Scenario, Recommendation, SeverityLevel


class ExplanationAgent:
    """Generates human-readable explanations of system reasoning.

    Designed for manufacturing strategy analysts and operations leaders
    who need to understand WHY the system recommends what it does.
    """

    def generate_executive_briefing(
        self,
        signals: list[Signal],
        scenarios: list[Scenario],
        recommendations: list[Recommendation],
        financial_impact: dict,
    ) -> dict:
        """Generate a complete executive briefing.

        Returns structured content suitable for dashboard display
        or report generation.
        """
        return {
            "headline": self._generate_headline(signals, scenarios),
            "situation_summary": self._situation_summary(signals),
            "risk_narrative": self._risk_narrative(scenarios, financial_impact),
            "action_brief": self._action_brief(recommendations),
            "confidence_statement": self._confidence_statement(signals, scenarios),
            "timeline": self._timeline(scenarios),
            "what_if_summary": self._what_if_summary(scenarios),
        }

    def explain_signal(self, signal: Signal) -> str:
        """Generate plain-language explanation of a single signal."""
        severity_text = {
            SeverityLevel.LOW: "minor",
            SeverityLevel.MEDIUM: "moderate",
            SeverityLevel.HIGH: "significant",
            SeverityLevel.CRITICAL: "critical",
        }

        base = (
            f"A {severity_text[signal.severity]} disruption signal has been detected: "
            f"{signal.title}. "
        )

        if signal.location:
            base += f"This affects operations in {signal.location}. "

        if signal.affected_entities:
            entities = ", ".join(signal.affected_entities[:3])
            base += f"Directly impacted: {entities}. "

        base += f"Detection confidence: {signal.confidence:.0%}."

        return base

    def explain_scenario(self, scenario: Scenario) -> str:
        """Generate plain-language explanation of a scenario."""
        lines = [f"**{scenario.name}** (Probability: {scenario.probability:.0%})"]
        lines.append("")
        lines.append(scenario.explanation)
        lines.append("")

        if scenario.impacts:
            max_delay = max(i.estimated_delay_days for i in scenario.impacts)
            lines.append(
                f"If this scenario materializes, expect up to {max_delay:.0f} days "
                f"of supply chain delay with ${scenario.total_revenue_at_risk_usd:,.0f} "
                f"in revenue at risk."
            )

        if scenario.recommended_actions:
            lines.append("")
            lines.append("Recommended actions:")
            for action in scenario.recommended_actions:
                lines.append(f"  • {action}")

        return "\n".join(lines)

    def explain_recommendation(self, rec: Recommendation) -> str:
        """Generate plain-language explanation of a recommendation."""
        urgency_text = {
            SeverityLevel.LOW: "when convenient",
            SeverityLevel.MEDIUM: "within the next week",
            SeverityLevel.HIGH: "within 48 hours",
            SeverityLevel.CRITICAL: "immediately",
        }

        lines = [
            f"**Recommendation: {rec.title}**",
            "",
            rec.description,
            "",
            f"Urgency: Act {urgency_text[rec.urgency]}.",
            f"Estimated cost: ${rec.estimated_cost_usd:,.0f}",
            f"Estimated savings: ${rec.estimated_savings_usd:,.0f}",
            f"Net benefit: ${rec.estimated_savings_usd - rec.estimated_cost_usd:,.0f}",
            "",
            f"Reasoning: {rec.explanation}",
        ]

        if rec.requires_approval:
            lines.append("")
            lines.append("⚠️ This action requires human approval before execution.")

        return "\n".join(lines)

    def _generate_headline(self, signals: list[Signal], scenarios: list[Scenario]) -> str:
        """Generate attention-grabbing headline for the briefing."""
        critical = [s for s in signals if s.severity == SeverityLevel.CRITICAL]
        high = [s for s in signals if s.severity == SeverityLevel.HIGH]

        if critical:
            return f"🔴 CRITICAL: {len(critical)} critical disruption(s) detected — immediate attention required"
        elif high:
            max_risk = max(s.total_revenue_at_risk_usd for s in scenarios) if scenarios else 0
            return f"🟠 HIGH ALERT: {len(high)} significant disruption(s) — ${max_risk:,.0f} at risk"
        else:
            return "🟡 MONITORING: Active disruption signals detected — situation developing"

    def _situation_summary(self, signals: list[Signal]) -> str:
        """Generate situation summary paragraph."""
        if not signals:
            return "No active disruption signals detected. All systems nominal."

        categories = set(s.category.value for s in signals)
        locations = set(s.location for s in signals if s.location)

        return (
            f"The system is tracking {len(signals)} active disruption signals "
            f"across {len(categories)} categories ({', '.join(categories)}). "
            f"Affected regions include: {', '.join(locations) if locations else 'multiple locations'}. "
            f"The highest severity signal is: {signals[0].title}."
        )

    def _risk_narrative(self, scenarios: list[Scenario], financial: dict) -> str:
        """Generate risk narrative for executives."""
        if not scenarios:
            return "Insufficient data for risk assessment."

        expected = financial.get("expected_loss_usd", 0)
        worst = financial.get("worst_case_usd", 0)

        return (
            f"Based on {len(scenarios)} simulated scenarios, the expected financial "
            f"exposure is ${expected:,.0f}. In the worst case, exposure could reach "
            f"${worst:,.0f}. "
            f"The most likely scenario ({scenarios[0].name}) has a "
            f"{scenarios[0].probability:.0%} probability of materializing. "
            f"If left unaddressed, production loss risk increases materially "
            f"within {self._estimate_urgency_days(scenarios)} days."
        )

    def _action_brief(self, recommendations: list[Recommendation]) -> str:
        """Generate action brief."""
        if not recommendations:
            return "No immediate actions required. Continue monitoring."

        lines = [f"The system recommends {len(recommendations)} actions:"]
        for i, rec in enumerate(recommendations[:3], 1):
            lines.append(
                f"{i}. {rec.title} — "
                f"Cost: ${rec.estimated_cost_usd:,.0f}, "
                f"Potential savings: ${rec.estimated_savings_usd:,.0f}"
            )

        total_cost = sum(r.estimated_cost_usd for r in recommendations[:3])
        total_savings = sum(r.estimated_savings_usd for r in recommendations[:3])
        lines.append(
            f"\nTotal investment: ${total_cost:,.0f} | "
            f"Total potential savings: ${total_savings:,.0f} | "
            f"ROI: {((total_savings - total_cost) / total_cost * 100):.0f}%"
        )

        return "\n".join(lines)

    def _confidence_statement(self, signals: list[Signal], scenarios: list[Scenario]) -> str:
        """Generate transparency statement about confidence levels."""
        avg_confidence = sum(s.confidence for s in signals) / len(signals) if signals else 0

        return (
            f"Signal detection confidence: {avg_confidence:.0%} average. "
            f"Scenario simulations based on {len(scenarios)} Monte Carlo iterations. "
            f"Causal graph contains known relationships; unknown dependencies may exist. "
            f"All recommendations require human approval before execution."
        )

    def _timeline(self, scenarios: list[Scenario]) -> list[dict]:
        """Generate timeline of expected impacts."""
        events = []
        for scenario in scenarios[:3]:
            for impact in scenario.impacts:
                events.append({
                    "days_from_now": impact.time_to_impact_days,
                    "event": f"{scenario.name}: impact on {', '.join(impact.affected_nodes[:2])}",
                    "severity": "high" if impact.revenue_at_risk_usd > 2_000_000 else "medium",
                    "revenue_at_risk": impact.revenue_at_risk_usd,
                })

        return sorted(events, key=lambda x: x["days_from_now"])[:10]

    def _what_if_summary(self, scenarios: list[Scenario]) -> list[dict]:
        """Generate what-if scenario summaries."""
        return [
            {
                "scenario": s.name,
                "probability": f"{s.probability:.0%}",
                "revenue_at_risk": f"${s.total_revenue_at_risk_usd:,.0f}",
                "key_insight": s.explanation[:150] + "..." if len(s.explanation) > 150 else s.explanation,
            }
            for s in scenarios[:5]
        ]

    def _estimate_urgency_days(self, scenarios: list[Scenario]) -> int:
        """Estimate how many days before action becomes critical."""
        if not scenarios:
            return 30
        min_time = 30
        for s in scenarios:
            for impact in s.impacts:
                if impact.time_to_impact_days < min_time:
                    min_time = impact.time_to_impact_days
        return max(1, int(min_time))
