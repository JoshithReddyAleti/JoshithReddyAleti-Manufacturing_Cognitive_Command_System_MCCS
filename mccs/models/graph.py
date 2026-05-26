"""Causal graph data models for the manufacturing value chain."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Types of nodes in the causal graph."""
    SUPPLIER = "supplier"
    PORT = "port"
    PLANT = "plant"
    WAREHOUSE = "warehouse"
    TRANSPORT_ROUTE = "transport_route"
    MATERIAL = "material"
    PRODUCT = "product"
    MARKET = "market"
    LABOR_POOL = "labor_pool"


class EdgeType(str, Enum):
    """Types of causal relationships."""
    SUPPLIES = "supplies"
    SHIPS_THROUGH = "ships_through"
    PRODUCES_AT = "produces_at"
    STORES_AT = "stores_at"
    DEPENDS_ON = "depends_on"
    FEEDS_INTO = "feeds_into"
    EMPLOYS_FROM = "employs_from"


class GraphNode(BaseModel):
    """A node in the manufacturing causal graph."""
    id: str
    name: str
    node_type: NodeType
    location: Optional[str] = None
    country: Optional[str] = None
    criticality: float = Field(
        ge=0.0, le=1.0, default=0.5,
        description="How critical this node is to operations"
    )
    current_risk: float = Field(ge=0.0, le=1.0, default=0.0)
    capacity_utilization: float = Field(ge=0.0, le=1.0, default=0.7)
    lead_time_days: float = 0.0
    metadata: dict = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """A causal edge in the manufacturing graph."""
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = Field(
        ge=0.0, le=1.0, default=1.0,
        description="Strength of causal influence"
    )
    lag_days: float = Field(
        ge=0.0, default=0.0,
        description="Time delay for impact propagation"
    )
    description: str = ""


class PropagationResult(BaseModel):
    """Result of risk propagation through the causal graph."""
    origin_node: str
    affected_nodes: list[dict] = Field(
        default_factory=list,
        description="List of {node_id, risk_level, hops, delay_days}"
    )
    total_nodes_affected: int = 0
    max_propagation_depth: int = 0
    critical_path: list[str] = Field(default_factory=list)
