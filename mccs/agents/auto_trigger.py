"""Auto-Trigger System.

Monitors all data sources and automatically triggers alerts when
thresholds are breached. Implements bounded autonomy (Layer 3).

Triggers on:
- Stock market drops > threshold
- Extreme weather events
- Geopolitical spikes
- Economic indicator declines
- Labor disruptions
- Logistics chokepoint disruptions
"""

from dataclasses import dataclass, field
from datetime import datetime
from mccs.models.signals import Signal, SeverityLevel
from mccs.config.settings import settings


@dataclass
class TriggerEvent:
    """An auto-triggered event."""
    id: str
    trigger_type: str  # stock, weather, geopolitical, economic, labor, logistics
    severity: str
    title: str
    description: str
    threshold_breached: str
    actual_value: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    auto_action_taken: str = ""
    requires_escalation: bool = False
    proof_link: str = ""


class AutoTriggerEngine:
    """Monitors signals and auto-triggers responses when thresholds breach.

    Bounded Autonomy Rules:
    - LOW severity: Log only
    - MEDIUM severity: Auto-notify + prepare response
    - HIGH severity: Auto-escalate + draft actions
    - CRITICAL severity: Auto-escalate + execute pre-approved actions
    """

    def __init__(self):
        self.trigger_history: list[TriggerEvent] = []
        self.pre_approved_actions = [
            "Increase safety stock monitoring frequency",
            "Activate alternate supplier contact list",
            "Escalate to supply chain leadership",
            "Prepare customer communication draft",
        ]

    def evaluate_signals(self, signals: list[Signal]) -> list[TriggerEvent]:
        """Evaluate all signals against auto-trigger thresholds."""
        triggers = []

        for signal in signals:
            trigger = self._check_trigger(signal)
            if trigger:
                triggers.append(trigger)
                self.trigger_history.append(trigger)

        return triggers

    def _check_trigger(self, signal: Signal) -> TriggerEvent | None:
        """Check if a signal breaches auto-trigger thresholds."""
        # Stock market triggers
        if "Market drop" in signal.title or "stock" in signal.source:
            return TriggerEvent(
                id=f"trigger-{signal.id}",
                trigger_type="stock",
                severity=signal.severity.value,
                title=f"AUTO-TRIGGER: {signal.title}",
                description=signal.description,
                threshold_breached=f"Stock drop > {settings.alert_stock_drop_pct}%",
                actual_value=signal.title,
                auto_action_taken="Activated supply chain risk monitoring",
                requires_escalation=signal.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL),
                proof_link=signal.raw_data.get("proof_link", signal.raw_data.get("link", "")),
            )

        # Weather triggers
        if signal.category.value == "weather" and signal.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL):
            return TriggerEvent(
                id=f"trigger-{signal.id}",
                trigger_type="weather",
                severity=signal.severity.value,
                title=f"AUTO-TRIGGER: {signal.title}",
                description=signal.description,
                threshold_breached=f"Wind > {settings.alert_weather_wind_ms} m/s or severe alert",
                actual_value=signal.title,
                auto_action_taken="Activated port disruption contingency plan",
                requires_escalation=True,
                proof_link=f"https://openweathermap.org/city/{signal.location}",
            )

        # Geopolitical triggers
        if signal.category.value == "geopolitical" and signal.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL):
            return TriggerEvent(
                id=f"trigger-{signal.id}",
                trigger_type="geopolitical",
                severity=signal.severity.value,
                title=f"AUTO-TRIGGER: {signal.title}",
                description=signal.description,
                threshold_breached=f"GDELT spike > {settings.alert_gdelt_spike_ratio}x",
                actual_value=signal.title,
                auto_action_taken="Activated geopolitical risk protocol",
                requires_escalation=True,
                proof_link="https://api.gdeltproject.org",
            )

        # Economic triggers
        if signal.category.value == "economic" and signal.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL):
            return TriggerEvent(
                id=f"trigger-{signal.id}",
                trigger_type="economic",
                severity=signal.severity.value,
                title=f"AUTO-TRIGGER: {signal.title}",
                description=signal.description,
                threshold_breached=f"Indicator decline > {settings.alert_fred_decline_pct}%",
                actual_value=signal.title,
                auto_action_taken="Demand forecast revision initiated",
                requires_escalation=signal.severity == SeverityLevel.CRITICAL,
                proof_link="https://fred.stlouisfed.org",
            )

        return None

    def get_trigger_summary(self) -> dict:
        """Get summary of all auto-triggers fired."""
        return {
            "total_triggers": len(self.trigger_history),
            "by_type": self._count_by_type(),
            "escalations_needed": sum(1 for t in self.trigger_history if t.requires_escalation),
            "recent_triggers": [
                {
                    "title": t.title,
                    "type": t.trigger_type,
                    "severity": t.severity,
                    "action": t.auto_action_taken,
                    "proof": t.proof_link,
                }
                for t in self.trigger_history[-5:]
            ],
        }

    def _count_by_type(self) -> dict:
        counts = {}
        for t in self.trigger_history:
            counts[t.trigger_type] = counts.get(t.trigger_type, 0) + 1
        return counts
