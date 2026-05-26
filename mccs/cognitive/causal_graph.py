"""Causal Graph Engine - The core reasoning layer of MCCS.

Builds and maintains a directed acyclic graph representing causal
relationships in the manufacturing value chain. Propagates risk
through the graph to understand cascading impacts.
"""

from typing import Optional
import networkx as nx

from mccs.models.graph import (
    GraphNode, GraphEdge, NodeType, EdgeType, PropagationResult
)
from mccs.config.settings import settings


class CausalGraph:
    """Manufacturing value chain causal graph.

    Nodes represent entities (suppliers, ports, plants, etc.)
    Edges represent causal influence with weights and time lags.
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self._nodes: dict[str, GraphNode] = {}
        self._edges: list[GraphEdge] = []

    def add_node(self, node: GraphNode) -> None:
        """Add a node to the causal graph."""
        self._nodes[node.id] = node
        self.graph.add_node(
            node.id,
            name=node.name,
            node_type=node.node_type.value,
            location=node.location,
            country=node.country,
            criticality=node.criticality,
            current_risk=node.current_risk,
            capacity_utilization=node.capacity_utilization,
            lead_time_days=node.lead_time_days,
        )

    def add_edge(self, edge: GraphEdge) -> None:
        """Add a causal edge to the graph."""
        self._edges.append(edge)
        self.graph.add_edge(
            edge.source_id,
            edge.target_id,
            edge_type=edge.edge_type.value,
            weight=edge.weight,
            lag_days=edge.lag_days,
            description=edge.description,
        )

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID."""
        return self._nodes.get(node_id)

    def get_downstream_nodes(self, node_id: str) -> list[str]:
        """Get all nodes downstream of a given node."""
        if node_id not in self.graph:
            return []
        return list(nx.descendants(self.graph, node_id))

    def get_upstream_nodes(self, node_id: str) -> list[str]:
        """Get all nodes upstream of a given node."""
        if node_id not in self.graph:
            return []
        return list(nx.ancestors(self.graph, node_id))

    def propagate_risk(
        self,
        origin_node_id: str,
        initial_risk: float,
        max_depth: Optional[int] = None,
    ) -> PropagationResult:
        """Propagate risk from an origin node through the causal graph.

        Uses BFS with decay to simulate how disruption cascades through
        the value chain over time.

        Args:
            origin_node_id: The node where disruption originates
            initial_risk: Risk level at origin (0.0 to 1.0)
            max_depth: Maximum propagation hops (default from settings)

        Returns:
            PropagationResult with all affected nodes and their risk levels
        """
        if max_depth is None:
            max_depth = settings.max_propagation_depth

        if origin_node_id not in self.graph:
            return PropagationResult(
                origin_node=origin_node_id,
                affected_nodes=[],
                total_nodes_affected=0,
                max_propagation_depth=0,
                critical_path=[],
            )

        affected = []
        visited = {origin_node_id}
        queue = [(origin_node_id, initial_risk, 0, 0.0, [origin_node_id])]
        max_depth_reached = 0
        critical_path = [origin_node_id]
        max_risk_seen = 0.0

        while queue:
            current_id, current_risk, depth, cumulative_delay, path = queue.pop(0)

            if depth >= max_depth:
                continue

            for successor in self.graph.successors(current_id):
                if successor in visited:
                    continue

                visited.add(successor)
                edge_data = self.graph.edges[current_id, successor]
                edge_weight = edge_data.get("weight", 1.0)
                edge_lag = edge_data.get("lag_days", 0.0)

                # Risk decays with each hop and is modulated by edge weight
                decay = settings.confidence_decay_per_hop
                propagated_risk = current_risk * edge_weight * (1 - decay)
                new_delay = cumulative_delay + edge_lag
                new_path = path + [successor]

                if propagated_risk > 0.05:  # Threshold to stop propagation
                    affected.append({
                        "node_id": successor,
                        "risk_level": round(propagated_risk, 4),
                        "hops": depth + 1,
                        "delay_days": round(new_delay, 1),
                        "path": new_path,
                    })

                    # Update node risk
                    if successor in self._nodes:
                        node = self._nodes[successor]
                        node.current_risk = max(node.current_risk, propagated_risk)

                    if depth + 1 > max_depth_reached:
                        max_depth_reached = depth + 1

                    if propagated_risk > max_risk_seen:
                        max_risk_seen = propagated_risk
                        critical_path = new_path

                    queue.append((successor, propagated_risk, depth + 1, new_delay, new_path))

        # Sort by risk level descending
        affected.sort(key=lambda x: x["risk_level"], reverse=True)

        return PropagationResult(
            origin_node=origin_node_id,
            affected_nodes=affected,
            total_nodes_affected=len(affected),
            max_propagation_depth=max_depth_reached,
            critical_path=critical_path,
        )

    def find_critical_paths(self, source_id: str, target_id: str) -> list[list[str]]:
        """Find all paths between two nodes, sorted by total weight."""
        if source_id not in self.graph or target_id not in self.graph:
            return []
        try:
            paths = list(nx.all_simple_paths(self.graph, source_id, target_id, cutoff=6))
            # Sort by total edge weight (higher = more critical)
            def path_weight(path):
                total = 0
                for i in range(len(path) - 1):
                    edge = self.graph.edges[path[i], path[i + 1]]
                    total += edge.get("weight", 1.0)
                return total
            paths.sort(key=path_weight, reverse=True)
            return paths
        except nx.NetworkXNoPath:
            return []

    def get_node_criticality_ranking(self) -> list[dict]:
        """Rank nodes by their structural importance in the graph."""
        if not self.graph.nodes:
            return []

        betweenness = nx.betweenness_centrality(self.graph)
        ranking = []
        for node_id, centrality in sorted(betweenness.items(), key=lambda x: x[1], reverse=True):
            node = self._nodes.get(node_id)
            if node:
                ranking.append({
                    "node_id": node_id,
                    "name": node.name,
                    "type": node.node_type.value,
                    "centrality": round(centrality, 4),
                    "criticality": node.criticality,
                    "current_risk": node.current_risk,
                })
        return ranking

    def get_graph_stats(self) -> dict:
        """Get summary statistics about the causal graph."""
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_types": self._count_by_type(),
            "is_dag": nx.is_directed_acyclic_graph(self.graph),
            "connected_components": nx.number_weakly_connected_components(self.graph),
        }

    def _count_by_type(self) -> dict[str, int]:
        counts = {}
        for node in self._nodes.values():
            t = node.node_type.value
            counts[t] = counts.get(t, 0) + 1
        return counts


def build_demo_graph() -> CausalGraph:
    """Build a demonstration causal graph for the MVP scenario.

    Represents a simplified manufacturing value chain with:
    - Suppliers in multiple countries
    - Ports and shipping routes
    - Manufacturing plants
    - Warehouses and markets
    """
    graph = CausalGraph()

    # === SUPPLIERS ===
    suppliers = [
        GraphNode(id="supplier-electronics-cn", name="Electronics Supplier (China)",
                  node_type=NodeType.SUPPLIER, location="shenzhen", country="china",
                  criticality=0.9, lead_time_days=21),
        GraphNode(id="supplier-rare-earth", name="Rare Earth Minerals (China)",
                  node_type=NodeType.SUPPLIER, location="baotou", country="china",
                  criticality=0.95, lead_time_days=30),
        GraphNode(id="supplier-auto-parts-mx", name="Auto Parts Supplier (Mexico)",
                  node_type=NodeType.SUPPLIER, location="monterrey", country="mexico",
                  criticality=0.7, lead_time_days=5),
        GraphNode(id="supplier-gulf-chemicals", name="Chemical Supplier (Gulf)",
                  node_type=NodeType.SUPPLIER, location="houston", country="usa",
                  criticality=0.8, lead_time_days=7),
        GraphNode(id="supplier-machinery-de", name="Machinery Supplier (Germany)",
                  node_type=NodeType.SUPPLIER, location="munich", country="germany",
                  criticality=0.6, lead_time_days=14),
        GraphNode(id="supplier-semiconductors-tw", name="Semiconductor Fab (Taiwan)",
                  node_type=NodeType.SUPPLIER, location="hsinchu", country="taiwan",
                  criticality=0.95, lead_time_days=45),
    ]

    # === PORTS ===
    ports = [
        GraphNode(id="port-shanghai", name="Port of Shanghai",
                  node_type=NodeType.PORT, location="shanghai", country="china",
                  criticality=0.85, lead_time_days=2),
        GraphNode(id="port-houston", name="Port of Houston",
                  node_type=NodeType.PORT, location="houston", country="usa",
                  criticality=0.75, lead_time_days=1),
        GraphNode(id="port-rotterdam", name="Port of Rotterdam",
                  node_type=NodeType.PORT, location="rotterdam", country="netherlands",
                  criticality=0.8, lead_time_days=1),
        GraphNode(id="port-los-angeles", name="Port of Los Angeles",
                  node_type=NodeType.PORT, location="los_angeles", country="usa",
                  criticality=0.8, lead_time_days=2),
    ]

    # === PLANTS ===
    plants = [
        GraphNode(id="plant-detroit-assembly", name="Detroit Assembly Plant",
                  node_type=NodeType.PLANT, location="detroit", country="usa",
                  criticality=0.9, capacity_utilization=0.82, lead_time_days=3),
        GraphNode(id="plant-munich", name="Munich Manufacturing",
                  node_type=NodeType.PLANT, location="munich", country="germany",
                  criticality=0.7, capacity_utilization=0.75, lead_time_days=2),
        GraphNode(id="plant-monterrey", name="Monterrey Assembly",
                  node_type=NodeType.PLANT, location="monterrey", country="mexico",
                  criticality=0.65, capacity_utilization=0.70, lead_time_days=2),
    ]

    # === WAREHOUSES ===
    warehouses = [
        GraphNode(id="warehouse-us-central", name="US Central Warehouse",
                  node_type=NodeType.WAREHOUSE, location="chicago", country="usa",
                  criticality=0.6, lead_time_days=1),
        GraphNode(id="warehouse-eu-central", name="EU Central Warehouse",
                  node_type=NodeType.WAREHOUSE, location="frankfurt", country="germany",
                  criticality=0.55, lead_time_days=1),
    ]

    # === MARKETS ===
    markets = [
        GraphNode(id="market-north-america", name="North America Market",
                  node_type=NodeType.MARKET, location="usa", country="usa", criticality=0.9),
        GraphNode(id="market-europe", name="European Market",
                  node_type=NodeType.MARKET, location="europe", country="germany", criticality=0.7),
    ]

    # Add all nodes
    for node_list in [suppliers, ports, plants, warehouses, markets]:
        for node in node_list:
            graph.add_node(node)

    # === EDGES (Causal Relationships) ===
    edges = [
        # Suppliers → Ports
        GraphEdge(source_id="supplier-electronics-cn", target_id="port-shanghai",
                  edge_type=EdgeType.SHIPS_THROUGH, weight=0.9, lag_days=3),
        GraphEdge(source_id="supplier-rare-earth", target_id="port-shanghai",
                  edge_type=EdgeType.SHIPS_THROUGH, weight=0.85, lag_days=5),
        GraphEdge(source_id="supplier-semiconductors-tw", target_id="port-shanghai",
                  edge_type=EdgeType.SHIPS_THROUGH, weight=0.8, lag_days=4),
        GraphEdge(source_id="supplier-gulf-chemicals", target_id="port-houston",
                  edge_type=EdgeType.SHIPS_THROUGH, weight=0.95, lag_days=1),
        GraphEdge(source_id="supplier-machinery-de", target_id="port-rotterdam",
                  edge_type=EdgeType.SHIPS_THROUGH, weight=0.85, lag_days=2),

        # Ports → Plants (via shipping)
        GraphEdge(source_id="port-shanghai", target_id="port-los-angeles",
                  edge_type=EdgeType.FEEDS_INTO, weight=0.85, lag_days=14,
                  description="Transpacific shipping route"),
        GraphEdge(source_id="port-shanghai", target_id="port-rotterdam",
                  edge_type=EdgeType.FEEDS_INTO, weight=0.7, lag_days=25,
                  description="Asia-Europe shipping route"),
        GraphEdge(source_id="port-los-angeles", target_id="plant-detroit-assembly",
                  edge_type=EdgeType.FEEDS_INTO, weight=0.9, lag_days=4,
                  description="Rail/truck to Detroit"),
        GraphEdge(source_id="port-houston", target_id="plant-detroit-assembly",
                  edge_type=EdgeType.FEEDS_INTO, weight=0.8, lag_days=3,
                  description="Chemical supply to assembly"),
        GraphEdge(source_id="port-rotterdam", target_id="plant-munich",
                  edge_type=EdgeType.FEEDS_INTO, weight=0.85, lag_days=2,
                  description="EU distribution"),

        # Direct supplier → plant
        GraphEdge(source_id="supplier-auto-parts-mx", target_id="plant-monterrey",
                  edge_type=EdgeType.SUPPLIES, weight=0.9, lag_days=1),
        GraphEdge(source_id="supplier-auto-parts-mx", target_id="plant-detroit-assembly",
                  edge_type=EdgeType.SUPPLIES, weight=0.75, lag_days=3),

        # Plants → Warehouses
        GraphEdge(source_id="plant-detroit-assembly", target_id="warehouse-us-central",
                  edge_type=EdgeType.STORES_AT, weight=0.9, lag_days=1),
        GraphEdge(source_id="plant-munich", target_id="warehouse-eu-central",
                  edge_type=EdgeType.STORES_AT, weight=0.85, lag_days=1),
        GraphEdge(source_id="plant-monterrey", target_id="warehouse-us-central",
                  edge_type=EdgeType.STORES_AT, weight=0.7, lag_days=2),

        # Warehouses → Markets
        GraphEdge(source_id="warehouse-us-central", target_id="market-north-america",
                  edge_type=EdgeType.FEEDS_INTO, weight=0.95, lag_days=2),
        GraphEdge(source_id="warehouse-eu-central", target_id="market-europe",
                  edge_type=EdgeType.FEEDS_INTO, weight=0.9, lag_days=2),
    ]

    for edge in edges:
        graph.add_edge(edge)

    return graph
