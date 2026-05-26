"""Explainability Engine - Makes causal reasoning transparent.

Generates human-readable causal chains that explain WHY the system
believes a disruption will propagate in a certain way.
"""

from mccs.cognitive.causal_graph import CausalGraph
from mccs.models.graph import PropagationResult
from mccs.models.signals import Signal, SeverityLevel


class ExplainabilityEngine:
    """Generates transparent explanations of causal reasoning.

    Answers the key user question: "Why does the system think this?"
    """

    def __init__(self, graph: CausalGraph):
        self.graph = graph

    def explain_propagation(self, result: PropagationResult, signal: Signal) -> str:
        """Generate a natural-language explanation of risk propagation.

        Example output:
        "Hurricane Warning in Houston → Port of Houston congested (1 day lag)
         → Detroit Assembly Plant delayed (3 day lag) → US Central Warehouse
         understocked (1 day lag) → North America Market revenue at risk"
        """
        if not result.critical_path:
            return "No significant propagation detected."

        lines = [
            f"**Causal Chain** (triggered by: {signal.title})",
            "",
        ]

        path = result.critical_path
        for i in range(len(path) - 1):
            source_id = path[i]
            target_id = path[i + 1]

            source_node = self.graph.get_node(source_id)
            target_node = self.graph.get_node(target_id)

            source_name = source_node.name if source_node else source_id
            target_name = target_node.name if target_node else target_id

            # Get edge data
            edge_data = self.graph.graph.edges.get((source_id, target_id), {})
            lag = edge_data.get("lag_days", 0)
            weight = edge_data.get("weight", 1.0)

            arrow = "→" if i < len(path) - 2 else "⇒"
            lag_text = f" ({lag:.0f} day lag)" if lag > 0 else ""
            confidence_text = f" [{weight:.0%} confidence]" if weight < 0.9 else ""

            lines.append(f"  {i+1}. **{source_name}** {arrow} **{target_name}**{lag_text}{confidence_text}")

        # Summary
        total_delay = sum(
            self.graph.graph.edges.get((path[i], path[i+1]), {}).get("lag_days", 0)
            for i in range(len(path) - 1)
        )
        lines.append("")
        lines.append(f"**Total propagation time:** ~{total_delay:.0f} days")
        lines.append(f"**Nodes in critical path:** {len(path)}")

        return "\n".join(lines)

    def explain_risk_score(self, node_id: str, risk_level: float) -> str:
        """Explain why a node has a particular risk score."""
        node = self.graph.get_node(node_id)
        if not node:
            return f"Node {node_id} not found in graph."

        upstream = self.graph.get_upstream_nodes(node_id)
        downstream = self.graph.get_downstream_nodes(node_id)

        explanation = (
            f"**{node.name}** has a risk level of {risk_level:.0%}.\n\n"
            f"This is because:\n"
            f"- It has {len(upstream)} upstream dependencies (supply sources)\n"
            f"- It feeds {len(downstream)} downstream nodes\n"
            f"- Its structural criticality is {node.criticality:.0%}\n"
            f"- Current capacity utilization: {node.capacity_utilization:.0%}\n"
        )

        if risk_level > 0.7:
            explanation += (
                f"\n⚠️ This node is at HIGH risk. Disruption here would affect "
                f"{len(downstream)} downstream operations."
            )

        return explanation

    def generate_assumption_list(self, signal: Signal) -> list[str]:
        """List the assumptions the system is making about a signal.

        This supports human-in-the-loop by making assumptions explicit
        so humans can validate or override them.
        """
        assumptions = [
            f"Signal '{signal.title}' is accurate (confidence: {signal.confidence:.0%})",
            f"Affected entities: {', '.join(signal.affected_entities) or 'inferred from location'}",
        ]

        if signal.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL):
            assumptions.append("Disruption will persist for at least 7 days")
            assumptions.append("No pre-existing mitigation is in place")
        else:
            assumptions.append("Disruption may resolve within 3-5 days")

        assumptions.extend([
            "Causal graph relationships reflect current supply chain structure",
            "Lead times are based on historical averages",
            "No simultaneous mitigating actions are being taken",
        ])

        return assumptions

    def compare_scenarios(self, scenario_a_name: str, scenario_b_name: str,
                          risk_a: float, risk_b: float) -> str:
        """Generate comparative explanation between two scenarios."""
        diff = abs(risk_a - risk_b)
        worse = scenario_a_name if risk_a > risk_b else scenario_b_name

        return (
            f"Comparing **{scenario_a_name}** (${risk_a:,.0f} at risk) vs "
            f"**{scenario_b_name}** (${risk_b:,.0f} at risk):\n\n"
            f"- Difference: ${diff:,.0f}\n"
            f"- **{worse}** represents the higher-risk outcome\n"
            f"- The gap suggests that {'escalation' if risk_a > risk_b else 'the base case'} "
            f"would have significantly more financial impact"
        )
