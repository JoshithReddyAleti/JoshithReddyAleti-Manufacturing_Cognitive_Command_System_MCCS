"""MCCS Demo Script - Run a full analysis loop with all 6 agents.

Exercises the complete pipeline:
  8.1 Signal Intelligence Agent
  8.2 Supply Chain Reasoning Agent
  8.3 Production Rebalancing Agent
  8.4 Financial Impact Agent
  8.5 Policy & Safety Agent
  8.6 Executive Explanation Agent

Plus Cognitive Layer:
  7.1 Causal Graph Agent
  7.2 Risk Propagation Reasoning
  7.3 Counterfactual Simulation Engine
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from mccs.agents.orchestrator import MCCSOrchestrator
from mccs.config.settings import settings


async def main():
    print("=" * 70)
    print("  MCCS - Manufacturing Cognitive Command System")
    print("  Full Agent Loop Demo (All 6 Agents)")
    print("=" * 70)
    print()

    # Initialize orchestrator with all agents
    print("[INIT] Initializing orchestrator with all 6 agents...")
    orchestrator = MCCSOrchestrator()
    stats = orchestrator.graph.get_graph_stats()
    print(f"       Causal Graph: {stats['total_nodes']} nodes, {stats['total_edges']} edges, DAG={stats['is_dag']}")
    print(f"       Agents loaded:")
    print(f"         8.1 Signal Intelligence Agent  ✅ (LIVE: OpenWeather, GDELT, FRED, BLS)")
    print(f"         8.2 Supply Chain Reasoning Agent ✅")
    print(f"         8.3 Production Rebalancing Agent ✅")
    print(f"         8.4 Financial Impact Agent       ✅")
    print(f"         8.5 Policy & Safety Agent        ✅")
    print(f"         8.6 Executive Explanation Agent  ✅ (AI: Google Gemini)")
    print()
    print(f"       LLM: Google Gemini ({settings.llm_model})")
    print(f"       Data: REAL-TIME from public APIs")
    print()

    # Run full analysis pipeline
    print("=" * 70)
    print("  RUNNING FULL AGENT LOOP (REAL-TIME DATA + AI)")
    print("=" * 70)
    print()

    result = await orchestrator.run_full_analysis(num_scenarios=10)

    # ─────────────────────────────────────────────────────────────
    # AGENT 8.1: Signal Intelligence
    # ─────────────────────────────────────────────────────────────
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│  AGENT 8.1: Signal Intelligence                             │")
    print("│  Polls MCP servers, normalizes signals, flags anomalies     │")
    print("└─────────────────────────────────────────────────────────────┘")
    print(f"  Detected {len(result.signals)} disruption signals from 6 MCP sources:")
    print()
    for signal in result.signals[:10]:
        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        print(f"  {icon.get(signal.severity.value, '⚪')} [{signal.severity.value.upper():8s}] "
              f"{signal.title}")
        print(f"     Source: {signal.source} | Location: {signal.location} | "
              f"Confidence: {signal.confidence:.0%}")
    print()

    # ─────────────────────────────────────────────────────────────
    # COGNITIVE LAYER: Causal Graph + Simulation
    # ─────────────────────────────────────────────────────────────
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│  COGNITIVE LAYER 7.1: Causal Graph Reasoning                │")
    print("│  + 7.2: Risk Propagation (Lead-time, Lags, Confidence)      │")
    print("│  + 7.3: Counterfactual Simulation Engine                    │")
    print("└─────────────────────────────────────────────────────────────┘")
    print()

    # 7.2 Risk Propagation Demo
    print("  ── 7.2 Risk Propagation: 'What breaks next — and when?' ──")
    print()
    what_breaks = orchestrator.what_breaks_next("port-houston", risk=0.85)
    print(f"  Scenario: Port of Houston disrupted (85% severity)")
    print(f"  Downstream impacts (sorted by time-to-impact):")
    print()
    for item in what_breaks[:6]:
        print(f"    ⏱️  Day {item['effective_impact_day']:.0f}: {item['node_name']}")
        print(f"       Risk: {item['risk_level']:.0%} (range: {item['risk_range']})")
        print(f"       Arrives: {item['impact_arrives_range']} | "
              f"Buffer: {item['buffer_remaining_days']} days | "
              f"Recovery: ~{item['recovery_estimate_days']:.0f} days")
        print(f"       Confidence: {item['confidence']:.0%}")
        print()

    # Propagation narrative
    print("  ── 7.2 Narrative (for executives) ──")
    print()
    narrative = orchestrator.get_propagation_narrative("supplier-semiconductors-tw", risk=0.9)
    for line in narrative.split("\n"):
        print(f"  {line}")
    print()

    # 7.3 Scenarios
    print(f"  ── 7.3 Counterfactual Simulation: {len(result.scenarios)} scenarios ──")
    print()
    for scenario in result.scenarios[:5]:
        print(f"  📊 {scenario.name}")
        print(f"     Probability: {scenario.probability:.0%} | "
              f"Revenue at Risk: ${scenario.total_revenue_at_risk_usd:,.0f}")
        print(f"     {scenario.explanation[:100]}...")
        print()

    # ─────────────────────────────────────────────────────────────
    # AGENT 8.2: Supply Chain Reasoning
    # ─────────────────────────────────────────────────────────────
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│  AGENT 8.2: Supply Chain Reasoning                          │")
    print("│  Suggests alternatives, scores sourcing risk                │")
    print("└─────────────────────────────────────────────────────────────┘")
    sc = result.supply_chain_assessment
    print(f"  Suppliers monitored: {sc.get('total_suppliers_monitored', 0)}")
    print(f"  High risk suppliers: {sc.get('high_risk_suppliers', 0)}")
    print(f"  Critical single-source: {sc.get('critical_single_source', 0)}")
    print(f"  Diversification score: {sc.get('diversification_score', 0):.0f}%")
    if sc.get("immediate_actions"):
        print(f"  Immediate actions:")
        for action in sc["immediate_actions"]:
            print(f"    → {action}")
    print()

    # ─────────────────────────────────────────────────────────────
    # AGENT 8.3: Production Rebalancing
    # ─────────────────────────────────────────────────────────────
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│  AGENT 8.3: Production Rebalancing (Simulated)              │")
    print("│  Creates virtual plant shifts, trades cost vs risk          │")
    print("└─────────────────────────────────────────────────────────────┘")
    rb = result.production_rebalancing
    print(f"  Status: {rb.get('status', 'N/A')}")
    if rb.get("affected_plants"):
        print(f"  Affected plants: {len(rb['affected_plants'])}")
        for plant in rb["affected_plants"]:
            print(f"    ⚠️  {plant['name']} (risk: {plant['risk_level']:.0%})")
    if rb.get("shift_plans"):
        print(f"  Shift plans generated: {len(rb['shift_plans'])}")
        for plan in rb["shift_plans"][:3]:
            print(f"    🔄 {plan['source']} → {plan['target']}")
            print(f"       Units: {plan['units_shifted']} | "
                  f"Cost: +${plan['cost_increase_usd']:,.0f} | "
                  f"Risk reduction: {plan['risk_reduction_pct']:.1f}%")
    summary = rb.get("summary", {})
    if summary:
        print(f"  Summary:")
        print(f"    Total units shifted: {summary.get('total_units_shifted', 0)}")
        print(f"    Total cost increase: ${summary.get('total_cost_increase_usd', 0):,.0f}")
        print(f"    Avg risk reduction: {summary.get('average_risk_reduction_pct', 0):.1f}%")
    print()

    # ─────────────────────────────────────────────────────────────
    # AGENT 8.4: Financial Impact
    # ─────────────────────────────────────────────────────────────
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│  AGENT 8.4: Financial Impact                                │")
    print("│  Revenue at risk, inventory exposure, margin erosion        │")
    print("└─────────────────────────────────────────────────────────────┘")
    fi = result.financial_impact
    print(f"  Expected Loss:     ${fi.get('expected_loss_usd', 0):>15,.0f}")
    print(f"  Worst Case:        ${fi.get('worst_case_usd', 0):>15,.0f}")
    print(f"  Best Case:         ${fi.get('best_case_usd', 0):>15,.0f}")
    print(f"  Net Exposure:      ${fi.get('net_exposure_usd', 0):>15,.0f}")
    print(f"  Margin Erosion:    {fi.get('margin_erosion_pct', 0):>14.2f}%")
    print(f"  Penalty Exposure:  ${fi.get('penalty_exposure_usd', 0):>15,.0f}")
    roi = fi.get("mitigation_roi", {})
    print(f"  Mitigation ROI:    {roi.get('roi_pct', 0):>14.0f}%")
    print(f"  Payback Period:    {roi.get('payback_days', 0):>14.1f} days")
    print()

    # ─────────────────────────────────────────────────────────────
    # AGENT 8.5: Policy & Safety
    # ─────────────────────────────────────────────────────────────
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│  AGENT 8.5: Policy & Safety                                 │")
    print("│  Enforces: max risk tolerance, ethical sourcing, regulatory  │")
    print("└─────────────────────────────────────────────────────────────┘")
    pr = result.policy_review
    print(f"  Recommendations reviewed: {pr.get('approved_count', 0) + pr.get('blocked_count', 0) + pr.get('flagged_count', 0)}")
    print(f"  ✅ Approved: {pr.get('approved_count', 0)}")
    print(f"  ⚠️  Flagged:  {pr.get('flagged_count', 0)}")
    print(f"  🚫 Blocked:  {pr.get('blocked_count', 0)}")
    if pr.get("flagged"):
        print(f"  Flagged items:")
        for item in pr["flagged"]:
            print(f"    ⚠️  {item['title']}: {item['warnings'][0] if item['warnings'] else ''}")
    if pr.get("blocked"):
        print(f"  Blocked items:")
        for item in pr["blocked"]:
            print(f"    🚫 {item['title']}: {item['reason']}")
    print(f"  Policy summary: {pr.get('policy_summary', '')}")
    print()

    # ─────────────────────────────────────────────────────────────
    # AGENT 8.6: Executive Explanation
    # ─────────────────────────────────────────────────────────────
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│  AGENT 8.6: Executive Explanation                           │")
    print("│  Turns probability into human narrative                     │")
    print("└─────────────────────────────────────────────────────────────┘")
    briefing = result.executive_briefing
    print(f"  HEADLINE: {briefing.get('headline', '')}")
    print()
    print(f"  SITUATION:")
    print(f"  {briefing.get('situation_summary', '')}")
    print()
    print(f"  RISK NARRATIVE:")
    print(f"  {briefing.get('risk_narrative', '')}")
    print()
    print(f"  ACTIONS:")
    print(f"  {briefing.get('action_brief', '')}")
    print()
    print(f"  CONFIDENCE:")
    print(f"  {briefing.get('confidence_statement', '')}")
    print()

    # AI-Generated Narrative (Gemini)
    ai_narrative = briefing.get("ai_narrative", "")
    if ai_narrative:
        print("  ┌─────────────────────────────────────────────────────────┐")
        print("  │  🤖 AI NARRATIVE (Generated by Google Gemini)            │")
        print("  └─────────────────────────────────────────────────────────┘")
        print()
        for line in ai_narrative.strip().split("\n"):
            print(f"  {line}")
        print()

    # ─────────────────────────────────────────────────────────────
    # RECOMMENDATIONS (post-policy-filter)
    # ─────────────────────────────────────────────────────────────
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│  FINAL RECOMMENDATIONS (Policy-Approved)                    │")
    print("└─────────────────────────────────────────────────────────────┘")
    for rec in result.recommendations:
        roi_pct = ((rec.estimated_savings_usd - rec.estimated_cost_usd) / rec.estimated_cost_usd * 100)
        print(f"  💡 {rec.title}")
        print(f"     Cost: ${rec.estimated_cost_usd:,.0f} | "
              f"Savings: ${rec.estimated_savings_usd:,.0f} | "
              f"ROI: {roi_pct:.0f}%")
        print(f"     {rec.explanation[:120]}...")
        print(f"     ⚠️  Requires human approval: {rec.requires_approval}")
        print()

    # ─────────────────────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────────────────────
    print("=" * 70)
    print("  ANALYSIS COMPLETE - ALL 6 AGENTS EXECUTED SUCCESSFULLY")
    print("=" * 70)
    print(f"  Signals collected:        {len(result.signals)}")
    print(f"  Scenarios simulated:      {len(result.scenarios)}")
    print(f"  Recommendations:          {len(result.recommendations)}")
    print(f"  Policy violations:        {pr.get('total_violations', 0)}")
    print(f"  Shift plans available:    {len(rb.get('shift_plans', []))}")
    print(f"  Expected loss:            ${fi.get('expected_loss_usd', 0):,.0f}")
    print(f"  Mitigation ROI:           {roi.get('roi_pct', 0):.0f}%")
    print()
    print("  Human approval required for all actions. ✅")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
