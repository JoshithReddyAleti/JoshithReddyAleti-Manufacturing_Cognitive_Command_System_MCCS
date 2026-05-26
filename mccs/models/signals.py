"""Signal data models - the core data flowing through MCCS."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SignalCategory(str, Enum):
    """Categories of disruption signals."""
    WEATHER = "weather"
    TRADE = "trade"
    GEOPOLITICAL = "geopolitical"
    ECONOMIC = "economic"
    LOGISTICS = "logistics"
    LABOR = "labor"


class SeverityLevel(str, Enum):
    """Signal severity classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Signal(BaseModel):
    """A disruption signal detected from an MCP source."""
    id: str = Field(description="Unique signal identifier")
    category: SignalCategory
    severity: SeverityLevel
    title: str
    description: str
    source: str = Field(description="MCP server that produced this signal")
    location: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    raw_data: dict = Field(default_factory=dict)
    affected_entities: list[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "sig-weather-001",
                "category": "weather",
                "severity": "high",
                "title": "Hurricane approaching Gulf Coast",
                "description": "Category 3 hurricane expected to make landfall within 72 hours",
                "source": "mcp-weather",
                "location": "Gulf of Mexico",
                "confidence": 0.92,
                "affected_entities": ["port-houston", "supplier-gulf-chemicals"],
            }
        }


class ImpactAssessment(BaseModel):
    """Assessment of a signal's impact on the value chain."""
    signal_id: str
    affected_nodes: list[str] = Field(description="Causal graph nodes affected")
    propagation_path: list[str] = Field(description="Path of impact propagation")
    estimated_delay_days: float = 0.0
    revenue_at_risk_usd: float = 0.0
    confidence: float = Field(ge=0.0, le=1.0)
    time_to_impact_days: float = Field(description="Days until impact materializes")


class Scenario(BaseModel):
    """A simulated future scenario."""
    id: str
    name: str
    description: str
    probability: float = Field(ge=0.0, le=1.0)
    signals_involved: list[str] = Field(description="Signal IDs contributing")
    impacts: list[ImpactAssessment] = Field(default_factory=list)
    total_revenue_at_risk_usd: float = 0.0
    recommended_actions: list[str] = Field(default_factory=list)
    explanation: str = ""


class Recommendation(BaseModel):
    """An actionable recommendation from the system."""
    id: str
    title: str
    description: str
    urgency: SeverityLevel
    scenario_id: str
    action_type: str = Field(description="e.g., rebalance, source-switch, buffer")
    estimated_cost_usd: float = 0.0
    estimated_savings_usd: float = 0.0
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str = Field(description="Human-readable reasoning")
    requires_approval: bool = True
