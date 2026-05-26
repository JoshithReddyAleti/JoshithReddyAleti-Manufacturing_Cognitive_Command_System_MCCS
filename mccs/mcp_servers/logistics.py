"""MCP Logistics Server - REAL logistics monitoring via GDELT + public data.

Monitors port congestion, shipping delays, and logistics chokepoints
using live news analysis as a proxy for real-time logistics data.
"""

import uuid
from typing import Any
from mccs.mcp_servers.base import BaseMCPServer
from mccs.models.signals import Signal, SignalCategory, SeverityLevel


# Key logistics chokepoints and routes to monitor
LOGISTICS_MONITORS = {
    "suez_canal": {"query": "Suez Canal shipping disruption blocked", "entities": ["route-suez"]},
    "red_sea": {"query": "Red Sea Houthi shipping attack disruption", "entities": ["route-red-sea"]},
    "freight_rates": {"query": "container freight rates shipping cost surge", "entities": ["all-logistics"]},
}


class LogisticsMCPServer(BaseMCPServer):
    """MCP server for REAL logistics disruption monitoring."""

    @property
    def category(self) -> SignalCategory:
        return SignalCategory.LOGISTICS

    async def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "get_port_congestion",
                "description": "Get congestion/disruption news for a port (LIVE)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "port": {"type": "string", "description": "Port name"}
                    },
                    "required": ["port"],
                },
            },
            {
                "name": "get_freight_delay_stats",
                "description": "Get global freight/shipping disruption indicators (LIVE)",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "get_chokepoint_status",
                "description": "Get status of major shipping chokepoints (LIVE)",
                "parameters": {"type": "object", "properties": {}},
            },
        ]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        if tool_name == "get_port_congestion":
            port = arguments["port"].lower().replace(" ", "_")
            key = f"port_{port}"
            if key in LOGISTICS_MONITORS:
                return await self._query_gdelt(LOGISTICS_MONITORS[key]["query"], key)
            return await self._query_gdelt(f"Port {arguments['port']} congestion delay", port)
        elif tool_name == "get_freight_delay_stats":
            return await self._query_gdelt(LOGISTICS_MONITORS["freight_rates"]["query"], "freight_rates")
        elif tool_name == "get_chokepoint_status":
            results = {}
            for key in ["suez_canal", "red_sea"]:
                if key in LOGISTICS_MONITORS:
                    data = await self._query_gdelt(LOGISTICS_MONITORS[key]["query"], key)
                    results[key] = data
            return {"chokepoints": results, "source": "GDELT Logistics Analysis (LIVE)"}
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _query_gdelt(self, query: str, label: str) -> dict:
        """Query GDELT for logistics disruption news volume."""
        url = "https://api.gdeltproject.org/api/v2/doc/doc"
        params = {
            "query": query,
            "mode": "timelinevol",
            "timespan": "14d",
            "format": "json",
        }
        try:
            resp = await self._client.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            timeline = data.get("timeline", [])
            if timeline and len(timeline) > 0:
                series = timeline[0].get("data", [])
                volumes = [point.get("value", 0) for point in series]

                if volumes:
                    avg_volume = sum(volumes) / len(volumes)
                    recent_volume = sum(volumes[-3:]) / 3 if len(volumes) >= 3 else avg_volume
                    spike_ratio = recent_volume / max(avg_volume, 1)

                    congestion_level = (
                        "severe" if spike_ratio > 2.5
                        else "moderate" if spike_ratio > 1.5
                        else "low"
                    )

                    return {
                        "label": label,
                        "avg_volume": round(avg_volume, 0),
                        "recent_volume": round(recent_volume, 0),
                        "spike_ratio": round(spike_ratio, 2),
                        "congestion_level": congestion_level,
                        "source": "GDELT Logistics Analysis (LIVE)",
                    }

            return {"label": label, "spike_ratio": 0, "congestion_level": "low", "source": "GDELT (no data)"}
        except Exception as e:
            return {"label": label, "error": str(e)}

    async def detect_signals(self) -> list[Signal]:
        """Detect logistics disruption signals from REAL data."""
        signals = []

        for key, monitor in LOGISTICS_MONITORS.items():
            data = await self._query_gdelt(monitor["query"], key)
            if "error" in data:
                continue

            spike_ratio = data.get("spike_ratio", 0)
            congestion = data.get("congestion_level", "low")

            if congestion == "severe":
                signals.append(self._create_signal(
                    signal_id=f"sig-log-{uuid.uuid4().hex[:8]}",
                    severity=SeverityLevel.HIGH,
                    title=f"Logistics disruption: {key.replace('_', ' ')} ({spike_ratio:.1f}x spike)",
                    description=(
                        f"Disruption news for '{key.replace('_', ' ')}' is {spike_ratio:.1f}x "
                        f"above normal. Recent volume: {data.get('recent_volume', 0):.0f} articles/day."
                    ),
                    confidence=min(0.90, spike_ratio / 3.5),
                    location=key,
                    raw_data=data,
                    affected_entities=monitor["entities"],
                ))
            elif congestion == "moderate":
                signals.append(self._create_signal(
                    signal_id=f"sig-log-{uuid.uuid4().hex[:8]}",
                    severity=SeverityLevel.MEDIUM,
                    title=f"Elevated logistics activity: {key.replace('_', ' ')}",
                    description=f"Above-normal disruption coverage for {key.replace('_', ' ')}.",
                    confidence=0.65,
                    location=key,
                    raw_data=data,
                    affected_entities=monitor["entities"],
                ))

        return signals
