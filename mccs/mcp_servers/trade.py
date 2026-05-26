"""MCP Trade Server - REAL World Bank WITS + GDELT trade news integration.

Detects tariff changes and trade policy disruptions using live data.
"""

import uuid
from typing import Any
from mccs.mcp_servers.base import BaseMCPServer
from mccs.models.signals import Signal, SignalCategory, SeverityLevel


# Key trade relationships to monitor
TRADE_MONITORS = {
    "us_china": {"query": "United States China tariff trade war", "entities": ["supplier-electronics-cn", "supplier-rare-earth"]},
    "semiconductor": {"query": "semiconductor export controls chips", "entities": ["supplier-semiconductors-tw", "supplier-electronics-cn"]},
}


class TradeMCPServer(BaseMCPServer):
    """MCP server for REAL trade policy monitoring via GDELT news analysis."""

    @property
    def category(self) -> SignalCategory:
        return SignalCategory.TRADE

    async def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "get_tariff_rate",
                "description": "Get trade tension level for a country pair (LIVE news analysis)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "country": {"type": "string"},
                        "product_category": {"type": "string"},
                    },
                    "required": ["country", "product_category"],
                },
            },
            {
                "name": "get_trade_restrictions",
                "description": "Get trade restriction news volume for a country (LIVE)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "country": {"type": "string"},
                    },
                    "required": ["country"],
                },
            },
            {
                "name": "get_trade_risk_overview",
                "description": "Get overall trade risk across monitored relationships (LIVE)",
                "parameters": {"type": "object", "properties": {}},
            },
        ]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        if tool_name == "get_tariff_rate":
            return await self._get_trade_tension(arguments["country"], arguments["product_category"])
        elif tool_name == "get_trade_restrictions":
            return await self._get_restriction_news(arguments["country"])
        elif tool_name == "get_trade_risk_overview":
            return await self._get_overview()
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _get_trade_tension(self, country: str, product: str) -> dict:
        """Query GDELT for trade tension news volume."""
        query = f"{country} {product} tariff sanctions trade restriction"
        return await self._query_gdelt_volume(query, f"{country}_{product}")

    async def _get_restriction_news(self, country: str) -> dict:
        """Get trade restriction news for a country."""
        query = f"{country} trade restriction sanctions embargo export control"
        return await self._query_gdelt_volume(query, country)

    async def _get_overview(self) -> dict:
        """Get overview of all monitored trade relationships."""
        results = {}
        for key, monitor in TRADE_MONITORS.items():
            data = await self._query_gdelt_volume(monitor["query"], key)
            if "error" not in data:
                results[key] = {
                    "spike_ratio": data.get("spike_ratio", 0),
                    "volume": data.get("recent_volume", 0),
                    "risk_level": data.get("risk_level", "low"),
                }
        return {"trade_monitors": results, "source": "GDELT Trade Analysis (LIVE)"}

    async def _query_gdelt_volume(self, query: str, label: str) -> dict:
        """Query GDELT for article volume on a trade topic."""
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

                    risk_level = (
                        "critical" if spike_ratio > 3
                        else "high" if spike_ratio > 2
                        else "medium" if spike_ratio > 1.3
                        else "low"
                    )

                    return {
                        "label": label,
                        "query": query[:50],
                        "avg_volume": round(avg_volume, 0),
                        "recent_volume": round(recent_volume, 0),
                        "spike_ratio": round(spike_ratio, 2),
                        "risk_level": risk_level,
                        "source": "GDELT DOC 2.0 (LIVE)",
                    }

            return {"label": label, "spike_ratio": 0, "risk_level": "low", "source": "GDELT (no data)"}
        except Exception as e:
            return {"label": label, "error": str(e)}

    async def detect_signals(self) -> list[Signal]:
        """Detect trade disruption signals from REAL GDELT data."""
        signals = []

        for key, monitor in TRADE_MONITORS.items():
            data = await self._query_gdelt_volume(monitor["query"], key)
            if "error" in data:
                continue

            spike_ratio = data.get("spike_ratio", 0)
            risk_level = data.get("risk_level", "low")

            if risk_level in ("critical", "high"):
                severity = SeverityLevel.CRITICAL if risk_level == "critical" else SeverityLevel.HIGH
                signals.append(self._create_signal(
                    signal_id=f"sig-trade-{uuid.uuid4().hex[:8]}",
                    severity=severity,
                    title=f"Trade disruption risk: {key.replace('_', ' ')} ({spike_ratio:.1f}x spike)",
                    description=(
                        f"Trade/tariff news volume for '{key.replace('_', ' ')}' is "
                        f"{spike_ratio:.1f}x above normal. Recent volume: "
                        f"{data.get('recent_volume', 0):.0f} articles/day."
                    ),
                    confidence=min(0.92, spike_ratio / 4.0),
                    location=key.split("_")[0] if "_" in key else key,
                    raw_data=data,
                    affected_entities=monitor["entities"],
                ))
            elif risk_level == "medium":
                signals.append(self._create_signal(
                    signal_id=f"sig-trade-{uuid.uuid4().hex[:8]}",
                    severity=SeverityLevel.MEDIUM,
                    title=f"Elevated trade tension: {key.replace('_', ' ')}",
                    description=f"Above-normal trade policy news for {key.replace('_', ' ')}.",
                    confidence=0.60,
                    location=key.split("_")[0] if "_" in key else key,
                    raw_data=data,
                    affected_entities=monitor["entities"],
                ))

        return signals
