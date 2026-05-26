"""Risk Propagation Reasoning Engine (PRD Section 7.2).

Purpose: Answer "If this happens here, what breaks next — and when?"

Logic:
- Lead-time heuristics: Uses node-level lead times + edge lag to estimate
  when impact materializes at each downstream node.
- Historical lag assumptions: Maintains a table of historical disruption
  propagation patterns to calibrate delay estimates.
- Confidence ranges: Produces min/expected/max bounds for risk and timing,
  not just point estimates.

This is the reasoning layer that sits between raw causal graph structure
and the simulation engine. It answers the temporal question: WHEN does
each node feel the impact, and HOW CERTAIN are we?
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np

from mccs.cognitive.causal_graph import CausalGraph
from mccs.models.graph import NodeType, PropagationResult
from mccs.models.signals import Signal, SeverityLevel
from mccs.config.settings import settings


# ═══════════════════════════════════════════════════════════════════════
# HISTORICAL LAG ASSUMPTIONS
# Based on typical manufacturing disruption propagation patterns.
# These would be learned/updated from real data in production.
# ═══════════════════════════════════════════════════════════════════════

HISTORICAL_LAG_TABLE = {
    # (source_type, target_type): {min_days, expected_days, max_days, confidence}
    (NodeType.SUPPLIER, NodeType.PORT): {
        "min_days": 1, "expected_days": 3, "max_days": 7,
        "confidence": 0.85, "historical_variance": 1.5,
    },
    (NodeType.PORT, NodeType.PORT): {
        "min_days": 7, "expected_days": 14, "max_days": 35,
        "confidence": 0.70, "historical_variance": 5.0,
    },
    (NodeType.PORT, NodeType.PLANT): {
        "min_days": 2, "expected_days": 5, "max_days": 14,
        "confidence": 0.80, "historical_variance": 2.5,
    },
    (NodeType.SUPPLIER, NodeType.PLANT): {
        "min_days": 1, "expected_days": 4, "max_days": 10,
        "confidence": 0.82, "historical_variance": 2.0,
    },
    (NodeType.PLANT, NodeType.WAREHOUSE): {
        "min_days": 1, "expected_days": 2, "max_days": 5,
        "confidence": 0.90, "historical_variance": 1.0,
    },
    (NodeType.WAREHOUSE, NodeType.MARKET): {
        "min_days": 1, "expected_days": 3, "max_days": 7,
        "confidence": 0.88, "historical_variance": 1.2,
    },
    (NodeType.PLANT, NodeType.MARKET): {
        "min_days": 3, "expected_days": 7, "max_days": 21,
        "confidence": 0.75, "historical_variance": 3.5,
    },
}

# Lead-time heuristics by node type (buffer days before impact is felt)
LEAD_TIME_HEURISTICS = {
    NodeType.SUPPLIER: {"buffer_days": 0, "ramp_up_days": 14, "recovery_factor": 0.7},
    NodeType.PORT: {"buffer_days": 1, "ramp_up_days": 3, "recovery_factor": 0.85},
    NodeType.PLANT: {"buffer_days": 2, "ramp_up_days": 7, "recovery_factor": 0.6},
    NodeType.WAREHOUSE: {"buffer_days": 5, "ramp_up_days": 2, "recovery_factor": 0.9},
    NodeType.MARKET: {"buffer_days": 7, "ramp_up_days": 14, "recovery_factor": 0.5},
    NodeType.TRANSPORT_ROUTE: {"buffer_days": 0, "ramp_up_days": 1, "recovery_factor": 0.95},
    NodeType.MATERIAL: {"buffer_days": 3, "ramp_up_days": 10, "recovery_factor": 0.65},
    NodeType.PRODUCT: {"buffer_days": 5, "ramp_up_days": 14, "recovery_factor": 0.55},
    NodeType.LABOR_POOL: {"buffer_days": 1, "ramp_up_days": 21, "recovery_factor": 0.4},
}


@dataclass
class ConfidenceRange:
    """A range estimate with confidence bounds."""
    min_value: float
    expected_value: float
    max_value: float
    confidence: float  # How confident we are in the expected value (0-1)

    @property
    def spread(self) -> float:
        """Width of the confidence interval."""
        return self.max_value - self.min_value

    @property
    def uncertainty(self) -> float:
        """Normalized uncertainty (0 = certain, 1 = very uncertain)."""
        if self.expected_value == 0:
            return 1.0
        return min(1.0, self.spread / (self.expected_value * 2))


@dataclass
class PropagationStep:
    """A single step in the risk propagation chain."""
    source_node_id: str
    target_node_id: str
    source_node_name: str
    target_node_name: str
    source_type: str
    target_type: str

    # Timing
    delay_range: ConfidenceRange  # Days until impact arrives
    cumulative_delay_range: ConfidenceRange  # Total days from origin

    # Risk
    risk_range: ConfidenceRange  # Risk level at this node
    risk_decay_factor: float  # How much risk decayed at this hop

    # Lead-time context
    buffer_days: float  # Safety stock / buffer before impact felt
    effective_impact_day: float  # When impact is actually felt (delay + buffer consumed)
    recovery_estimate_days: float  # Estimated days to recover

    # Metadata
    hop_number: int
    edge_weight: float
    historical_basis: str  # What historical pattern this is based on


@dataclass
class RiskPropagationReport:
    """Complete risk propagation analysis report.

    Answers: "If this happens here, what breaks next — and when?"
    """
    origin_node_id: str
    origin_node_name: str
    trigger_signal: Optional[str] = None
    initial_risk: float = 0.0

    # Propagation chain
    propagation_steps: list[PropagationStep] = field(default_factory=list)

    # Summary timing
    first_impact_day: ConfidenceRange = field(
        default_factory=lambda: ConfidenceRange(0, 0, 0, 0)
    )
    last_impact_day: ConfidenceRange = field(
        default_factory=lambda: ConfidenceRange(0, 0, 0, 0)
    )

    # Summary risk
    total_nodes_affected: int = 0
    highest_downstream_risk: ConfidenceRange = field(
        default_factory=lambda: ConfidenceRange(0, 0, 0, 0)
    )
    average_confidence: float = 0.0

    # Critical path
    critical_path: list[str] = field(default_factory=list)
    critical_path_total_delay_days: float = 0.0

    # Narrative
    narrative: str = ""


class RiskPropagationEngine:
    """Risk Propagation Reasoning Engine.

    Implements PRD Section 7.2:
    - Lead-time heuristics
    - Historical lag assumptions
    - Confidence ranges

    Unlike the basic `propagate_risk` in CausalGraph (which gives point
    estimates), this engine produces full confidence-bounded temporal
    analysis of how disruption cascades through the value chain.
    """

    def __init__(self, causal_graph: CausalGraph):
        self.graph = causal_graph
        self._historical_lags = HISTORICAL_LAG_TABLE
        self._lead_time_heuristics = LEAD_TIME_HEURISTICS

    def analyze_propagation(
        self,
        origin_node_id: str,
        initial_risk: float,
        signal: Optional[Signal] = None,
        max_depth: Optional[int] = None,
    ) -> RiskPropagationReport:
        """Perform full risk propagation analysis with confidence ranges.

        This is the main entry point. It answers:
        "If this happens at [origin], what breaks next — and when?"

        Args:
            origin_node_id: Where the disruption starts
            initial_risk: Severity of the initial disruption (0-1)
            signal: Optional signal that triggered this analysis
            max_depth: Max hops to propagate (default from settings)

        Returns:
            Complete RiskPropagationReport with timing, risk ranges,
            and human-readable narrative.
        """
        if max_depth is None:
            max_depth = settings.max_propagation_depth

        origin_node = self.graph.get_node(origin_node_id)
        if not origin_node:
            return RiskPropagationReport(
                origin_node_id=origin_node_id,
                origin_node_name="Unknown",
                narrative=f"Node {origin_node_id} not found in causal graph.",
            )

        report = RiskPropagationReport(
            origin_node_id=origin_node_id,
            origin_node_name=origin_node.name,
            trigger_signal=signal.title if signal else None,
            initial_risk=initial_risk,
        )

        # BFS propagation with confidence ranges
        steps = self._propagate_with_ranges(origin_node_id, initial_risk, max_depth)
        report.propagation_steps = steps
        report.total_nodes_affected = len(steps)

        if steps:
            # Timing summary
            all_delays = [s.cumulative_delay_range for s in steps]
            report.first_impact_day = ConfidenceRange(
                min_value=min(d.min_value for d in all_delays),
                expected_value=min(d.expected_value for d in all_delays),
                max_value=min(d.max_value for d in all_delays),
                confidence=max(d.confidence for d in all_delays),
            )
            report.last_impact_day = ConfidenceRange(
                min_value=max(d.min_value for d in all_delays),
                expected_value=max(d.expected_value for d in all_delays),
                max_value=max(d.max_value for d in all_delays),
                confidence=min(d.confidence for d in all_delays),
            )

            # Risk summary
            all_risks = [s.risk_range for s in steps]
            max_risk_step = max(steps, key=lambda s: s.risk_range.expected_value)
            report.highest_downstream_risk = max_risk_step.risk_range
            report.average_confidence = np.mean([s.risk_range.confidence for s in steps])

            # Critical path (highest cumulative risk)
            report.critical_path = self._extract_critical_path(steps, origin_node_id)
            report.critical_path_total_delay_days = sum(
                s.delay_range.expected_value for s in steps
                if s.target_node_id in report.critical_path
            )

        # Generate narrative
        report.narrative = self._generate_narrative(report)

        return report

    def estimate_time_to_impact(
        self,
        origin_node_id: str,
        target_node_id: str,
    ) -> Optional[ConfidenceRange]:
        """Estimate when a disruption at origin will reach target.

        Uses both graph structure (edge lags) and historical patterns
        to produce a confidence-bounded time estimate.
        """
        origin = self.graph.get_node(origin_node_id)
        target = self.graph.get_node(target_node_id)
        if not origin or not target:
            return None

        # Find shortest path
        try:
            import networkx as nx
            path = nx.shortest_path(self.graph.graph, origin_node_id, target_node_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

        # Accumulate delays along path
        total_min = 0.0
        total_expected = 0.0
        total_max = 0.0
        total_confidence = 1.0

        for i in range(len(path) - 1):
            src_id = path[i]
            tgt_id = path[i + 1]
            src_node = self.graph.get_node(src_id)
            tgt_node = self.graph.get_node(tgt_id)

            edge_data = self.graph.graph.edges[src_id, tgt_id]
            edge_lag = edge_data.get("lag_days", 0)

            # Get historical lag for this node-type pair
            hist = self._get_historical_lag(src_node, tgt_node)

            # Combine edge lag with historical pattern
            step_min = max(edge_lag * 0.5, hist["min_days"])
            step_expected = max(edge_lag, hist["expected_days"])
            step_max = max(edge_lag * 2.0, hist["max_days"])

            total_min += step_min
            total_expected += step_expected
            total_max += step_max
            total_confidence *= hist["confidence"]

        # Add target node's buffer (safety stock absorbs some delay)
        target_heuristic = self._lead_time_heuristics.get(target.node_type, {})
        buffer = target_heuristic.get("buffer_days", 0)
        total_min += buffer * 0.5
        total_expected += buffer
        total_max += buffer * 1.5

        return ConfidenceRange(
            min_value=round(total_min, 1),
            expected_value=round(total_expected, 1),
            max_value=round(total_max, 1),
            confidence=round(total_confidence, 3),
        )

    def what_breaks_next(self, origin_node_id: str, initial_risk: float) -> list[dict]:
        """Quick answer to "what breaks next?" — sorted by time-to-impact.

        Returns a simple list of nodes that will be affected, ordered by
        when they'll feel the impact (soonest first).
        """
        report = self.analyze_propagation(origin_node_id, initial_risk)

        results = []
        for step in report.propagation_steps:
            results.append({
                "node_id": step.target_node_id,
                "node_name": step.target_node_name,
                "node_type": step.target_type,
                "impact_arrives_day": step.cumulative_delay_range.expected_value,
                "impact_arrives_range": f"{step.cumulative_delay_range.min_value:.0f}-{step.cumulative_delay_range.max_value:.0f} days",
                "effective_impact_day": step.effective_impact_day,
                "risk_level": step.risk_range.expected_value,
                "risk_range": f"{step.risk_range.min_value:.0%}-{step.risk_range.max_value:.0%}",
                "confidence": step.risk_range.confidence,
                "buffer_remaining_days": step.buffer_days,
                "recovery_estimate_days": step.recovery_estimate_days,
            })

        # Sort by effective impact day (when it's actually felt)
        results.sort(key=lambda x: x["effective_impact_day"])
        return results

    # ═══════════════════════════════════════════════════════════════════
    # INTERNAL METHODS
    # ═══════════════════════════════════════════════════════════════════

    def _propagate_with_ranges(
        self,
        origin_id: str,
        initial_risk: float,
        max_depth: int,
    ) -> list[PropagationStep]:
        """BFS propagation producing confidence ranges at each step."""
        steps = []
        visited = {origin_id}
        # Queue: (node_id, risk_min, risk_exp, risk_max, depth, cum_min, cum_exp, cum_max, confidence)
        queue = [(origin_id, initial_risk, initial_risk, initial_risk, 0, 0.0, 0.0, 0.0, 1.0)]

        while queue:
            (current_id, risk_min, risk_exp, risk_max,
             depth, cum_min, cum_exp, cum_max, cum_confidence) = queue.pop(0)

            if depth >= max_depth:
                continue

            current_node = self.graph.get_node(current_id)
            if not current_node:
                continue

            for successor_id in self.graph.graph.successors(current_id):
                if successor_id in visited:
                    continue
                visited.add(successor_id)

                successor_node = self.graph.get_node(successor_id)
                if not successor_node:
                    continue

                edge_data = self.graph.graph.edges[current_id, successor_id]
                edge_weight = edge_data.get("weight", 1.0)
                edge_lag = edge_data.get("lag_days", 0.0)

                # Get historical lag pattern
                hist = self._get_historical_lag(current_node, successor_node)

                # === LEAD-TIME HEURISTICS ===
                target_heuristic = self._lead_time_heuristics.get(
                    successor_node.node_type,
                    {"buffer_days": 0, "ramp_up_days": 7, "recovery_factor": 0.7}
                )
                buffer_days = target_heuristic["buffer_days"]
                recovery_factor = target_heuristic["recovery_factor"]
                ramp_up_days = target_heuristic["ramp_up_days"]

                # === DELAY CALCULATION (with confidence range) ===
                step_delay_min = max(edge_lag * 0.5, hist["min_days"])
                step_delay_exp = max(edge_lag, hist["expected_days"])
                step_delay_max = max(edge_lag * 2.0, hist["max_days"])

                new_cum_min = cum_min + step_delay_min
                new_cum_exp = cum_exp + step_delay_exp
                new_cum_max = cum_max + step_delay_max

                # === RISK DECAY (with confidence range) ===
                decay = settings.confidence_decay_per_hop
                # Risk range: optimistic decay vs pessimistic decay
                new_risk_min = risk_min * edge_weight * (1 - decay * 1.3)  # More decay
                new_risk_exp = risk_exp * edge_weight * (1 - decay)        # Expected decay
                new_risk_max = risk_max * edge_weight * (1 - decay * 0.7)  # Less decay

                new_risk_min = max(0.0, new_risk_min)
                new_risk_max = min(1.0, new_risk_max)

                # === CONFIDENCE CALCULATION ===
                step_confidence = hist["confidence"] * edge_weight
                new_confidence = cum_confidence * step_confidence

                # Skip if risk too low even in worst case
                if new_risk_max < 0.03:
                    continue

                # Effective impact day = when buffer is consumed
                effective_day = new_cum_exp + buffer_days

                # Recovery estimate
                recovery_days = ramp_up_days / max(recovery_factor, 0.1)

                step = PropagationStep(
                    source_node_id=current_id,
                    target_node_id=successor_id,
                    source_node_name=current_node.name,
                    target_node_name=successor_node.name,
                    source_type=current_node.node_type.value,
                    target_type=successor_node.node_type.value,
                    delay_range=ConfidenceRange(
                        min_value=round(step_delay_min, 1),
                        expected_value=round(step_delay_exp, 1),
                        max_value=round(step_delay_max, 1),
                        confidence=round(step_confidence, 3),
                    ),
                    cumulative_delay_range=ConfidenceRange(
                        min_value=round(new_cum_min, 1),
                        expected_value=round(new_cum_exp, 1),
                        max_value=round(new_cum_max, 1),
                        confidence=round(new_confidence, 3),
                    ),
                    risk_range=ConfidenceRange(
                        min_value=round(new_risk_min, 4),
                        expected_value=round(new_risk_exp, 4),
                        max_value=round(new_risk_max, 4),
                        confidence=round(new_confidence, 3),
                    ),
                    risk_decay_factor=round(1 - decay, 3),
                    buffer_days=buffer_days,
                    effective_impact_day=round(effective_day, 1),
                    recovery_estimate_days=round(recovery_days, 1),
                    hop_number=depth + 1,
                    edge_weight=edge_weight,
                    historical_basis=self._describe_historical_basis(current_node, successor_node),
                )
                steps.append(step)

                # Continue propagation
                queue.append((
                    successor_id, new_risk_min, new_risk_exp, new_risk_max,
                    depth + 1, new_cum_min, new_cum_exp, new_cum_max, new_confidence
                ))

        return steps

    def _get_historical_lag(self, source_node, target_node) -> dict:
        """Look up historical lag assumptions for a node-type pair."""
        key = (source_node.node_type, target_node.node_type)
        if key in self._historical_lags:
            return self._historical_lags[key]

        # Fallback: use edge lag with default variance
        return {
            "min_days": 1,
            "expected_days": 5,
            "max_days": 14,
            "confidence": 0.60,
            "historical_variance": 3.0,
        }

    def _describe_historical_basis(self, source_node, target_node) -> str:
        """Describe what historical pattern a lag estimate is based on."""
        key = (source_node.node_type, target_node.node_type)
        if key in self._historical_lags:
            hist = self._historical_lags[key]
            return (
                f"Based on historical {source_node.node_type.value}→{target_node.node_type.value} "
                f"patterns (variance: ±{hist['historical_variance']:.1f} days)"
            )
        return "Default estimate (no specific historical pattern available)"

    def _extract_critical_path(self, steps: list[PropagationStep], origin_id: str) -> list[str]:
        """Extract the highest-risk propagation path."""
        if not steps:
            return [origin_id]

        # Find the step with highest risk
        max_step = max(steps, key=lambda s: s.risk_range.expected_value)

        # Trace back to origin
        path = [origin_id]
        current = origin_id
        for step in sorted(steps, key=lambda s: s.hop_number):
            if step.source_node_id == current:
                path.append(step.target_node_id)
                current = step.target_node_id
                if current == max_step.target_node_id:
                    break

        return path

    def _generate_narrative(self, report: RiskPropagationReport) -> str:
        """Generate human-readable narrative of the propagation analysis.

        This is what executives read. It answers:
        - What breaks next?
        - When?
        - How confident are we?
        """
        if not report.propagation_steps:
            return (
                f"Disruption at {report.origin_node_name} has no significant "
                f"downstream propagation in the current graph structure."
            )

        lines = []

        # Opening
        lines.append(
            f"**Disruption at {report.origin_node_name}** "
            f"(initial severity: {report.initial_risk:.0%})"
        )
        lines.append("")

        # What breaks next (first 3 by time)
        by_time = sorted(report.propagation_steps, key=lambda s: s.effective_impact_day)
        lines.append("**What breaks next:**")
        for step in by_time[:5]:
            lines.append(
                f"  • **{step.target_node_name}** — "
                f"impact in {step.cumulative_delay_range.expected_value:.0f} days "
                f"(range: {step.cumulative_delay_range.min_value:.0f}–"
                f"{step.cumulative_delay_range.max_value:.0f} days), "
                f"risk: {step.risk_range.expected_value:.0%} "
                f"[confidence: {step.risk_range.confidence:.0%}]"
            )
        lines.append("")

        # Timing summary
        lines.append("**Timing:**")
        lines.append(
            f"  • First impact expected: Day {report.first_impact_day.expected_value:.0f} "
            f"(best case: Day {report.first_impact_day.min_value:.0f})"
        )
        lines.append(
            f"  • Full cascade completes: Day {report.last_impact_day.expected_value:.0f} "
            f"(worst case: Day {report.last_impact_day.max_value:.0f})"
        )
        lines.append("")

        # Confidence statement
        lines.append("**Confidence:**")
        lines.append(
            f"  • Average confidence across chain: {report.average_confidence:.0%}"
        )
        lines.append(
            f"  • Based on historical lag patterns for "
            f"{report.total_nodes_affected} downstream nodes"
        )

        # Buffer warning
        no_buffer = [s for s in report.propagation_steps if s.buffer_days < 2]
        if no_buffer:
            lines.append("")
            lines.append(
                f"  ⚠️ {len(no_buffer)} node(s) have minimal buffer — "
                f"impact will be felt almost immediately upon arrival."
            )

        return "\n".join(lines)
