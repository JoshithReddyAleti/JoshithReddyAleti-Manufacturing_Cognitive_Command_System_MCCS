"""Email Summary Generator.

Generates formatted email content summarizing the MCCS analysis
for executive distribution. Does not send — just generates content.
"""

from datetime import datetime
from mccs.models.signals import SeverityLevel


class EmailGenerator:
    """Generates executive email summaries from MCCS analysis results."""

    def generate_summary_email(self, result, recipient: str = "leadership@company.com") -> dict:
        """Generate a complete email summary.

        Returns dict with subject, body_html, body_text, metadata.
        """
        signals = result.signals
        scenarios = result.scenarios
        recommendations = result.recommendations
        financial = result.financial_impact

        # Determine urgency
        critical_count = sum(1 for s in signals if s.severity == SeverityLevel.CRITICAL)
        high_count = sum(1 for s in signals if s.severity == SeverityLevel.HIGH)

        if critical_count > 0:
            urgency = "🔴 CRITICAL"
            subject_prefix = "[CRITICAL]"
        elif high_count > 0:
            urgency = "🟠 HIGH"
            subject_prefix = "[HIGH ALERT]"
        else:
            urgency = "🟡 MONITORING"
            subject_prefix = "[Update]"

        subject = (
            f"{subject_prefix} MCCS Disruption Intelligence - "
            f"{len(signals)} signals, ${financial.get('expected_loss_usd', 0):,.0f} exposure"
        )

        # Build HTML body
        body_html = self._build_html(
            urgency, signals, scenarios, recommendations, financial, result
        )

        # Build plain text body
        body_text = self._build_text(
            urgency, signals, scenarios, recommendations, financial, result
        )

        return {
            "to": recipient,
            "subject": subject,
            "body_html": body_html,
            "body_text": body_text,
            "generated_at": datetime.utcnow().isoformat(),
            "urgency": urgency,
            "signal_count": len(signals),
            "scenario_count": len(scenarios),
        }

    def _build_html(self, urgency, signals, scenarios, recommendations, financial, result) -> str:
        """Build HTML email body."""
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        # Signal rows
        signal_rows = ""
        for s in signals[:8]:
            color = {"critical": "#dc2626", "high": "#ea580c", "medium": "#ca8a04", "low": "#16a34a"}
            c = color.get(s.severity.value, "#666")
            signal_rows += f"""
            <tr>
                <td style="color:{c};font-weight:bold;">{s.severity.value.upper()}</td>
                <td>{s.title}</td>
                <td>{s.source}</td>
                <td>{s.location or 'Global'}</td>
            </tr>"""

        # Recommendation rows
        rec_rows = ""
        for r in recommendations[:5]:
            roi = ((r.estimated_savings_usd - r.estimated_cost_usd) / r.estimated_cost_usd * 100)
            rec_rows += f"""
            <tr>
                <td><strong>{r.title}</strong></td>
                <td>${r.estimated_cost_usd:,.0f}</td>
                <td>${r.estimated_savings_usd:,.0f}</td>
                <td>{roi:.0f}%</td>
            </tr>"""

        html = f"""
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #1e293b, #334155); color: white; padding: 24px; border-radius: 12px;">
        <h1 style="margin:0;">🏭 MCCS Disruption Intelligence</h1>
        <p style="margin:8px 0 0 0; opacity:0.8;">Manufacturing Cognitive Command System | {now}</p>
    </div>

    <div style="background: #fef2f2; border-left: 4px solid #dc2626; padding: 16px; margin: 16px 0; border-radius: 4px;">
        <strong>{urgency}</strong> — {len(signals)} active disruption signals detected
    </div>

    <h2>📊 Financial Exposure</h2>
    <table style="width:100%; border-collapse:collapse;">
        <tr>
            <td style="padding:8px; background:#f8fafc;"><strong>Expected Loss</strong></td>
            <td style="padding:8px; background:#f8fafc;">${financial.get('expected_loss_usd', 0):,.0f}</td>
            <td style="padding:8px; background:#f8fafc;"><strong>Worst Case</strong></td>
            <td style="padding:8px; background:#f8fafc;">${financial.get('worst_case_usd', 0):,.0f}</td>
        </tr>
        <tr>
            <td style="padding:8px;"><strong>Net Exposure</strong></td>
            <td style="padding:8px;">${financial.get('net_exposure_usd', 0):,.0f}</td>
            <td style="padding:8px;"><strong>Mitigation ROI</strong></td>
            <td style="padding:8px;">{financial.get('mitigation_roi', {}).get('roi_pct', 0):.0f}%</td>
        </tr>
    </table>

    <h2>⚠️ Active Signals ({len(signals)})</h2>
    <table style="width:100%; border-collapse:collapse; font-size:0.9em;">
        <tr style="background:#f1f5f9;">
            <th style="padding:8px; text-align:left;">Severity</th>
            <th style="padding:8px; text-align:left;">Signal</th>
            <th style="padding:8px; text-align:left;">Source</th>
            <th style="padding:8px; text-align:left;">Location</th>
        </tr>
        {signal_rows}
    </table>

    <h2>💡 Recommendations</h2>
    <table style="width:100%; border-collapse:collapse; font-size:0.9em;">
        <tr style="background:#f1f5f9;">
            <th style="padding:8px; text-align:left;">Action</th>
            <th style="padding:8px; text-align:left;">Cost</th>
            <th style="padding:8px; text-align:left;">Savings</th>
            <th style="padding:8px; text-align:left;">ROI</th>
        </tr>
        {rec_rows}
    </table>

    <h2>🔮 Top Scenarios</h2>
    <ul>
    {"".join(f'<li><strong>{s.name}</strong> — {s.probability:.0%} probability, ${s.total_revenue_at_risk_usd:,.0f} at risk</li>' for s in scenarios[:4])}
    </ul>

    <div style="background:#f8fafc; padding:16px; margin-top:24px; border-radius:8px; font-size:0.85em; color:#64748b;">
        <p><strong>Data Sources:</strong> OpenWeather API, FRED, GDELT, Finnhub, BLS (all LIVE)</p>
        <p><strong>AI:</strong> Google Gemini (reasoning & explanation)</p>
        <p><strong>Note:</strong> All recommendations require human approval. This is a decision-intelligence system.</p>
        <p>Generated by MCCS v0.1.0 | {now}</p>
    </div>
</body>
</html>"""
        return html

    def _build_text(self, urgency, signals, scenarios, recommendations, financial, result) -> str:
        """Build plain text email body."""
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            "=" * 60,
            "MCCS DISRUPTION INTELLIGENCE SUMMARY",
            f"Generated: {now}",
            "=" * 60,
            "",
            f"STATUS: {urgency}",
            f"Active Signals: {len(signals)}",
            f"Expected Exposure: ${financial.get('expected_loss_usd', 0):,.0f}",
            f"Worst Case: ${financial.get('worst_case_usd', 0):,.0f}",
            "",
            "TOP SIGNALS:",
        ]

        for s in signals[:6]:
            lines.append(f"  [{s.severity.value.upper()}] {s.title} ({s.source})")

        lines.append("")
        lines.append("RECOMMENDATIONS:")
        for r in recommendations[:4]:
            roi = ((r.estimated_savings_usd - r.estimated_cost_usd) / r.estimated_cost_usd * 100)
            lines.append(f"  • {r.title} (Cost: ${r.estimated_cost_usd:,.0f}, ROI: {roi:.0f}%)")

        lines.append("")
        lines.append("SCENARIOS:")
        for s in scenarios[:4]:
            lines.append(f"  • {s.name}: {s.probability:.0%} prob, ${s.total_revenue_at_risk_usd:,.0f} at risk")

        lines.extend([
            "",
            "-" * 60,
            "Data: OpenWeather, FRED, GDELT, Finnhub, BLS (LIVE)",
            "AI: Google Gemini | All actions require human approval",
            "=" * 60,
        ])

        return "\n".join(lines)
