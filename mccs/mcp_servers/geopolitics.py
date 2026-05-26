"""MCP Geopolitics Server - REAL GDELT Project API integration.

Detects political instability that threatens suppliers or logistics
using live GDELT global event data.
"""

import uuid
from typing import Any
from mccs.mcp_servers.base import BaseMCPServer
from mccs.models.signals import Signal, SignalCategory, SeverityLevel


# Countries we monitor for supply chain impact
MONITORED_COUNTRIES = {
    "taiwan": {"entities": ["supplier-semiconductors-tw", "port-kaohsiung"]},
    "china": {"entities": ["supplier-electronics-cn", "port-shanghai", "supplier-rare-earth"]},
    "russia": {"entities": ["supplier-titanium-ru", "supplier-energy-ru"]},
}


class GeopoliticsMCPServer(BaseMCPServer):
    """MCP server for REAL geopolitical risk monitoring via GDELT."""

    @property
    def category(self) -> SignalCategory:
        return SignalCategory.GEOPOLITICAL

    async def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "get_event_spikes",
                "description": "Get GDELT event activity for a country (LIVE)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "country": {"type": "string"}
                    },
                    "required": ["country"],
                },
            },
            {
                "name": "get_conflict_intensity",
                "description": "Get conflict/instability tone for a region (LIVE)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "region": {"type": "string"}
                    },
                    "required": ["region"],
                },
            },
            {
                "name": "get_global_risk_summary",
                "description": "Get global geopolitical risk summary (LIVE)",
                "parameters": {"type": "object", "properties": {}},
            },
        ]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        if tool_name == "get_event_spikes":
            return await self._get_event_data(arguments["country"])
        elif tool_name == "get_conflict_intensity":
            return await self._get_conflict_tone(arguments["region"])
        elif tool_name == "get_global_risk_summary":
            return await self._get_global_summary()
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _get_event_data(self, query: str) -> dict:
        """Query GDELT DOC 2.0 API for event data."""
        url = "https://api.gdeltproject.org/api/v2/doc/doc"
        params = {
            "query": f"{query} (conflict OR sanctions OR military OR protest OR strike)",
            "mode": "timelinevol",
            "timespan": "7d",
            "format": "json",
        }
        try:
            resp = await self._client.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            # Parse timeline volume data
            timeline = data.get("timeline", [])
            if timeline and len(timeline) > 0:
                series = timeline[0].get("data", [])
                volumes = [point.get("value", 0) for point in series]
                avg_volume = sum(volumes) / len(volumes) if volumes else 0
                max_volume = max(volumes) if volumes else 0
                recent_volume = volumes[-1] if volumes else 0

                # Spike detection: recent vs average
                spike_ratio = recent_volume / max(avg_volume, 1)

                return {
                    "query": query,
                    "avg_daily_articles": round(avg_volume, 0),
                    "recent_articles": round(recent_volume, 0),
                    "max_articles": round(max_volume, 0),
                    "spike_ratio": round(spike_ratio, 2),
                    "data_points": len(volumes),
                    "source": "GDELT DOC 2.0 API (LIVE)",
                }
            return {"query": query, "spike_ratio": 0, "source": "GDELT (no data)"}
        except Exception as e:
            return {"query": query, "error": str(e), "source": "GDELT API"}

    async def _get_conflict_tone(self, region: str) -> dict:
        """Get average tone (sentiment) for conflict-related news in a region."""
        url = "https://api.gdeltproject.org/api/v2/doc/doc"
        params = {
            "query": f"{region} (conflict OR war OR sanctions OR military)",
            "mode": "tonechart",
            "timespan": "7d",
            "format": "json",
        }
        try:
            resp = await self._client.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            # Tone chart returns average tone (negative = conflict)
            tone_data = data.get("tonechart", [])
            if tone_data:
                avg_tone = sum(t.get("tone", 0) for t in tone_data) / len(tone_data)
                return {
                    "region": region,
                    "avg_tone": round(avg_tone, 2),
                    "interpretation": "high_conflict" if avg_tone < -5 else "moderate_tension" if avg_tone < -2 else "stable",
                    "articles_analyzed": len(tone_data),
                    "source": "GDELT Tone Analysis (LIVE)",
                }
            return {"region": region, "avg_tone": 0, "interpretation": "no_data"}
        except Exception as e:
            return {"region": region, "error": str(e)}

    async def _get_global_summary(self) -> dict:
        """Get summary across all monitored countries."""
        results = {}
        for country in list(MONITORED_COUNTRIES.keys())[:5]:
            data = await self._get_event_data(country)
            if "error" not in data:
                results[country] = {
                    "spike_ratio": data.get("spike_ratio", 0),
                    "recent_articles": data.get("recent_articles", 0),
                }
        return {"countries": results, "source": "GDELT (LIVE)"}

    async def detect_signals(self) -> list[Signal]:
        """Detect geopolitical disruption signals from REAL GDELT data."""
        signals = []

        for country, meta in MONITORED_COUNTRIES.items():
            data = await self._get_event_data(country)
            if "error" in data:
                continue

            spike_ratio = data.get("spike_ratio", 0)

            if spike_ratio > 2.0:
                severity = SeverityLevel.CRITICAL if spike_ratio > 4 else SeverityLevel.HIGH
                signals.append(self._create_signal(
                    signal_id=f"sig-geo-{uuid.uuid4().hex[:8]}",
                    severity=severity,
                    title=f"Geopolitical event spike: {country} ({spike_ratio:.1f}x normal)",
                    description=(
                        f"GDELT detects {data.get('recent_articles', 0):.0f} conflict-related articles "
                        f"for {country} — {spike_ratio:.1f}x above average. "
                        f"Potential supply chain disruption risk."
                    ),
                    confidence=min(0.95, spike_ratio / 5.0),
                    location=country,
                    raw_data=data,
                    affected_entities=meta["entities"],
                ))
            elif spike_ratio > 1.5:
                signals.append(self._create_signal(
                    signal_id=f"sig-geo-{uuid.uuid4().hex[:8]}",
                    severity=SeverityLevel.MEDIUM,
                    title=f"Elevated geopolitical activity: {country} ({spike_ratio:.1f}x)",
                    description=(
                        f"Above-normal conflict/instability coverage for {country}. "
                        f"Monitoring for escalation."
                    ),
                    confidence=0.65,
                    location=country,
                    raw_data=data,
                    affected_entities=meta["entities"],
                ))

        return signals
