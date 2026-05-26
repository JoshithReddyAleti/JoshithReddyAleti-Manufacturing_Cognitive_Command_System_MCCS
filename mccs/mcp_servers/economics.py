"""MCP Economics Server - REAL FRED API integration.

Detects macro demand shocks using live Federal Reserve Economic Data.
"""

import uuid
from typing import Any
from mccs.mcp_servers.base import BaseMCPServer
from mccs.models.signals import Signal, SignalCategory, SeverityLevel


# Key FRED series IDs for manufacturing
FRED_SERIES = {
    "industrial_production": "INDPRO",       # Industrial Production Index
    "manufacturing_orders": "AMTMNO",        # Manufacturers New Orders
    "gdp_growth": "A191RL1Q225SBEA",         # Real GDP growth rate
    "pmi": "MANEMP",                         # Manufacturing Employment (proxy)
    "consumer_confidence": "UMCSENT",        # Consumer Sentiment
    "capacity_utilization": "MCUMFN",        # Manufacturing Capacity Utilization
    "inventory_sales_ratio": "MNFCTRIRSA",   # Manufacturers Inventory/Sales Ratio
}


class EconomicsMCPServer(BaseMCPServer):
    """MCP server for REAL economic indicators from FRED."""

    @property
    def category(self) -> SignalCategory:
        return SignalCategory.ECONOMIC

    async def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "get_industrial_production_index",
                "description": "Get latest Industrial Production Index from FRED (LIVE)",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "get_manufacturing_orders",
                "description": "Get latest Manufacturers New Orders from FRED (LIVE)",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "get_gdp_growth",
                "description": "Get latest GDP growth rate from FRED (LIVE)",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "get_capacity_utilization",
                "description": "Get manufacturing capacity utilization from FRED (LIVE)",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "get_fred_series",
                "description": "Get any FRED series by ID (LIVE)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "series_id": {"type": "string", "description": "FRED series ID"},
                        "limit": {"type": "integer", "description": "Number of observations"},
                    },
                    "required": ["series_id"],
                },
            },
        ]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        if tool_name == "get_industrial_production_index":
            return await self._get_series("INDPRO", "Industrial Production Index")
        elif tool_name == "get_manufacturing_orders":
            return await self._get_series("AMTMNO", "Manufacturers New Orders")
        elif tool_name == "get_gdp_growth":
            return await self._get_series("A191RL1Q225SBEA", "Real GDP Growth Rate")
        elif tool_name == "get_capacity_utilization":
            return await self._get_series("MCUMFN", "Manufacturing Capacity Utilization")
        elif tool_name == "get_fred_series":
            return await self._get_series(
                arguments["series_id"],
                arguments["series_id"],
                limit=arguments.get("limit", 12),
            )
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _get_series(self, series_id: str, name: str, limit: int = 12) -> dict:
        """Fetch a FRED series via the real API."""
        url = f"{self.base_url}/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit,
        }
        try:
            resp = await self._client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            observations = data.get("observations", [])

            if not observations:
                return {"series": series_id, "name": name, "error": "No data"}

            # Parse values
            values = []
            for obs in observations:
                try:
                    values.append({
                        "date": obs["date"],
                        "value": float(obs["value"]) if obs["value"] != "." else None,
                    })
                except (ValueError, KeyError):
                    continue

            valid_values = [v["value"] for v in values if v["value"] is not None]

            if len(valid_values) >= 2:
                current = valid_values[0]
                previous = valid_values[1]
                mom_change = ((current - previous) / previous) * 100 if previous != 0 else 0
            else:
                current = valid_values[0] if valid_values else 0
                previous = 0
                mom_change = 0

            yoy_change = 0
            if len(valid_values) >= 12:
                year_ago = valid_values[11]
                yoy_change = ((current - year_ago) / year_ago) * 100 if year_ago != 0 else 0

            return {
                "series_id": series_id,
                "name": name,
                "current_value": current,
                "previous_value": previous,
                "mom_change_pct": round(mom_change, 2),
                "yoy_change_pct": round(yoy_change, 2),
                "latest_date": values[0]["date"] if values else "unknown",
                "trend": "declining" if mom_change < -0.5 else "rising" if mom_change > 0.5 else "stable",
                "observations": values[:6],
                "source": "FRED API (LIVE)",
            }
        except Exception as e:
            return {"series_id": series_id, "name": name, "error": str(e)}

    async def detect_signals(self) -> list[Signal]:
        """Detect economic disruption signals from REAL FRED data."""
        signals = []

        # Check Industrial Production
        ip = await self._get_series("INDPRO", "Industrial Production Index")
        if "error" not in ip and ip.get("mom_change_pct", 0) < -1.0:
            signals.append(self._create_signal(
                signal_id=f"sig-econ-{uuid.uuid4().hex[:8]}",
                severity=SeverityLevel.HIGH if ip["mom_change_pct"] < -2 else SeverityLevel.MEDIUM,
                title=f"Industrial production declining ({ip['mom_change_pct']:.1f}% MoM)",
                description=(
                    f"Industrial Production Index at {ip['current_value']:.1f}, "
                    f"down {abs(ip['mom_change_pct']):.1f}% from previous month. "
                    f"Latest data: {ip['latest_date']}."
                ),
                confidence=0.92,
                raw_data=ip,
                affected_entities=["all-plants", "all-suppliers"],
            ))

        # Check Capacity Utilization
        cu = await self._get_series("MCUMFN", "Manufacturing Capacity Utilization")
        if "error" not in cu:
            val = cu.get("current_value", 80)
            if val < 72:  # Below 72% signals weak demand
                signals.append(self._create_signal(
                    signal_id=f"sig-econ-{uuid.uuid4().hex[:8]}",
                    severity=SeverityLevel.MEDIUM,
                    title=f"Low capacity utilization ({val:.1f}%)",
                    description=(
                        f"Manufacturing capacity utilization at {val:.1f}%. "
                        f"Below 72% indicates weak demand environment."
                    ),
                    confidence=0.88,
                    raw_data=cu,
                    affected_entities=["demand-all-markets"],
                ))

        # Check Manufacturing Orders
        mo = await self._get_series("AMTMNO", "Manufacturers New Orders")
        if "error" not in mo and mo.get("mom_change_pct", 0) < -3.0:
            signals.append(self._create_signal(
                signal_id=f"sig-econ-{uuid.uuid4().hex[:8]}",
                severity=SeverityLevel.HIGH,
                title=f"Manufacturing orders sharp decline ({mo['mom_change_pct']:.1f}% MoM)",
                description=(
                    f"New manufacturing orders dropped {abs(mo['mom_change_pct']):.1f}% month-over-month. "
                    f"Current level: ${mo['current_value']:,.0f}M."
                ),
                confidence=0.90,
                raw_data=mo,
                affected_entities=["all-plants", "inventory-all"],
            ))

        # If no negative signals, report stable
        if not signals:
            # Still check if there's a YoY decline
            if "error" not in ip and ip.get("yoy_change_pct", 0) < -2:
                signals.append(self._create_signal(
                    signal_id=f"sig-econ-{uuid.uuid4().hex[:8]}",
                    severity=SeverityLevel.LOW,
                    title=f"Industrial production below year-ago ({ip['yoy_change_pct']:.1f}% YoY)",
                    description=f"Production trending below year-ago levels.",
                    confidence=0.80,
                    raw_data=ip,
                    affected_entities=["all-plants"],
                ))

        return signals
