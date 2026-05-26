"""MCP Labor Server - REAL US Bureau of Labor Statistics API integration.

Anticipates labor shortages, strikes, and workforce disruptions
using live BLS data.
"""

import uuid
import json
from typing import Any
from mccs.mcp_servers.base import BaseMCPServer
from mccs.models.signals import Signal, SignalCategory, SeverityLevel


# BLS Series IDs for manufacturing-relevant data
BLS_SERIES = {
    "manufacturing_employment": "CES3000000001",      # Manufacturing employees (thousands)
    "manufacturing_hours": "CES3000000006",           # Avg weekly hours manufacturing
    "manufacturing_earnings": "CES3000000008",        # Avg hourly earnings manufacturing
    "unemployment_rate": "LNS14000000",               # Total unemployment rate
    "manufacturing_unemployment": "LNU04032232",      # Manufacturing unemployment
    "job_openings_manufacturing": "JTS3000000000000000JOL",  # JOLTS manufacturing openings
    "quits_manufacturing": "JTS3000000000000000QUR",  # JOLTS manufacturing quits rate
}


class LaborMCPServer(BaseMCPServer):
    """MCP server for REAL labor market data from BLS."""

    @property
    def category(self) -> SignalCategory:
        return SignalCategory.LABOR

    async def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "get_unemployment_rate",
                "description": "Get unemployment rate from BLS (LIVE)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "industry": {"type": "string", "description": "Industry (manufacturing, total)"}
                    },
                    "required": ["industry"],
                },
            },
            {
                "name": "get_labor_disruptions",
                "description": "Get manufacturing labor indicators from BLS (LIVE)",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "get_manufacturing_employment",
                "description": "Get manufacturing employment trends from BLS (LIVE)",
                "parameters": {"type": "object", "properties": {}},
            },
        ]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        if tool_name == "get_unemployment_rate":
            industry = arguments.get("industry", "total")
            series_id = (
                BLS_SERIES["manufacturing_unemployment"]
                if "manuf" in industry.lower()
                else BLS_SERIES["unemployment_rate"]
            )
            return await self._get_bls_series([series_id])
        elif tool_name == "get_labor_disruptions":
            return await self._get_bls_series([
                BLS_SERIES["manufacturing_employment"],
                BLS_SERIES["manufacturing_hours"],
            ])
        elif tool_name == "get_manufacturing_employment":
            return await self._get_bls_series([
                BLS_SERIES["manufacturing_employment"],
                BLS_SERIES["manufacturing_earnings"],
            ])
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _get_bls_series(self, series_ids: list[str]) -> dict:
        """Call the real BLS Public API v2."""
        url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
        payload = json.dumps({
            "seriesid": series_ids,
            "startyear": "2024",
            "endyear": "2026",
        })
        headers = {"Content-type": "application/json"}

        try:
            resp = await self._client.post(url, content=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") != "REQUEST_SUCCEEDED":
                return {"error": data.get("message", "BLS API error"), "source": "BLS API"}

            results = {}
            for series in data.get("Results", {}).get("series", []):
                series_id = series["seriesID"]
                observations = []
                for item in series.get("data", [])[:12]:
                    try:
                        observations.append({
                            "year": item["year"],
                            "period": item["period"],
                            "value": float(item["value"]),
                        })
                    except (ValueError, KeyError):
                        continue

                if observations:
                    current = observations[0]["value"]
                    previous = observations[1]["value"] if len(observations) > 1 else current
                    change = current - previous
                    change_pct = (change / previous * 100) if previous != 0 else 0

                    results[series_id] = {
                        "current_value": current,
                        "previous_value": previous,
                        "change": round(change, 2),
                        "change_pct": round(change_pct, 2),
                        "latest_period": f"{observations[0]['year']}-{observations[0]['period']}",
                        "trend": "declining" if change_pct < -0.5 else "rising" if change_pct > 0.5 else "stable",
                        "observations": observations[:6],
                    }

            return {
                "series": results,
                "source": "BLS API v2 (LIVE)",
            }
        except Exception as e:
            return {"error": str(e), "source": "BLS API"}

    async def detect_signals(self) -> list[Signal]:
        """Detect labor disruption signals from REAL BLS data."""
        signals = []

        # Get manufacturing employment data
        emp_data = await self._get_bls_series([
            BLS_SERIES["manufacturing_employment"],
            BLS_SERIES["manufacturing_hours"],
        ])

        if "error" in emp_data:
            return signals

        for series_id, data in emp_data.get("series", {}).items():
            change_pct = data.get("change_pct", 0)

            if series_id == BLS_SERIES["manufacturing_employment"]:
                if change_pct < -0.5:
                    signals.append(self._create_signal(
                        signal_id=f"sig-labor-{uuid.uuid4().hex[:8]}",
                        severity=SeverityLevel.HIGH if change_pct < -1.0 else SeverityLevel.MEDIUM,
                        title=f"Manufacturing employment declining ({change_pct:.1f}%)",
                        description=(
                            f"Manufacturing employment at {data['current_value']:.0f}K workers, "
                            f"down {abs(change_pct):.1f}% from previous period. "
                            f"Latest: {data['latest_period']}."
                        ),
                        confidence=0.90,
                        raw_data=data,
                        affected_entities=["labor-pool-all", "all-plants"],
                    ))

            elif series_id == BLS_SERIES["manufacturing_hours"]:
                if change_pct < -1.0:
                    signals.append(self._create_signal(
                        signal_id=f"sig-labor-{uuid.uuid4().hex[:8]}",
                        severity=SeverityLevel.MEDIUM,
                        title=f"Manufacturing hours declining ({change_pct:.1f}%)",
                        description=(
                            f"Average weekly hours in manufacturing: {data['current_value']:.1f}h, "
                            f"declining {abs(change_pct):.1f}%. May indicate demand weakness."
                        ),
                        confidence=0.82,
                        raw_data=data,
                        affected_entities=["all-plants"],
                    ))

        return signals
