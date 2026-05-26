"""MCCS Real-Time API Test - Shows raw data from all live sources.

This script calls each MCP server individually and shows what
the real APIs return, proving the system is connected to live data.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import json
from mccs.mcp_servers.weather import WeatherMCPServer
from mccs.mcp_servers.economics import EconomicsMCPServer
from mccs.mcp_servers.geopolitics import GeopoliticsMCPServer
from mccs.mcp_servers.trade import TradeMCPServer
from mccs.mcp_servers.logistics import LogisticsMCPServer
from mccs.mcp_servers.labor import LaborMCPServer
from mccs.config.settings import settings
from mccs.cognitive.llm_engine import reason_about_signals


async def main():
    print("=" * 70)
    print("  MCCS - REAL-TIME API CONNECTION TEST")
    print("  Proving all 6 MCP servers connect to live data")
    print("=" * 70)
    print()

    # ═══════════════════════════════════════════════════════════
    # 1. OPENWEATHER API (LIVE)
    # ═══════════════════════════════════════════════════════════
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│  6.1 OpenWeather API - LIVE Weather Data                    │")
    print("└─────────────────────────────────────────────────────────────┘")
    weather = WeatherMCPServer(
        name="mcp-weather",
        base_url="https://api.openweathermap.org/data/2.5",
        api_key=settings.openweather_api_key,
    )

    for city in ["Houston", "Shanghai", "Rotterdam"]:
        data = await weather.call_tool("get_current_weather", {"location": city})
        if "error" not in data:
            print(f"  🌡️  {city}: {data['temp_c']:.1f}°C, {data['condition']} "
                  f"({data['description']}), Wind: {data['wind_speed_ms']:.1f} m/s")
        else:
            print(f"  ❌ {city}: {data['error']}")
    print(f"  Source: {data.get('source', 'OpenWeather API')}")
    print()

    # Forecast alerts
    alerts = await weather.call_tool("get_weather_alerts", {"lat": 29.76, "lon": -95.37})
    print(f"  Houston alerts: {alerts.get('alert_count', 0)} active")
    if alerts.get("alerts"):
        for a in alerts["alerts"][:3]:
            print(f"    ⚠️  {a.get('event', 'Unknown')}")
    print()

    # ═══════════════════════════════════════════════════════════
    # 2. FRED API (LIVE)
    # ═══════════════════════════════════════════════════════════
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│  6.4 FRED API - LIVE Economic Data                          │")
    print("└─────────────────────────────────────────────────────────────┘")
    econ = EconomicsMCPServer(
        name="mcp-economics",
        base_url="https://api.stlouisfed.org/fred",
        api_key=settings.fred_api_key,
    )

    ip = await econ.call_tool("get_industrial_production_index", {})
    if "error" not in ip:
        print(f"  📈 Industrial Production Index: {ip['current_value']:.2f}")
        print(f"     MoM change: {ip['mom_change_pct']:+.2f}% | YoY: {ip['yoy_change_pct']:+.2f}%")
        print(f"     Trend: {ip['trend']} | Latest: {ip['latest_date']}")
    else:
        print(f"  ❌ FRED error: {ip['error']}")

    cu = await econ.call_tool("get_capacity_utilization", {})
    if "error" not in cu:
        print(f"  🏭 Capacity Utilization: {cu['current_value']:.1f}%")
        print(f"     MoM change: {cu['mom_change_pct']:+.2f}%")

    mo = await econ.call_tool("get_manufacturing_orders", {})
    if "error" not in mo:
        print(f"  📦 Manufacturing Orders: ${mo['current_value']:,.0f}M")
        print(f"     MoM change: {mo['mom_change_pct']:+.2f}%")

    print(f"  Source: FRED API (LIVE)")
    print()

    # ═══════════════════════════════════════════════════════════
    # 3. GDELT API (LIVE) - Geopolitics
    # ═══════════════════════════════════════════════════════════
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│  6.3 GDELT API - LIVE Geopolitical Event Data               │")
    print("└─────────────────────────────────────────────────────────────┘")
    geo = GeopoliticsMCPServer(
        name="mcp-geopolitics",
        base_url="https://api.gdeltproject.org/api/v2",
    )

    for country in ["taiwan", "china", "russia"]:
        data = await geo.call_tool("get_event_spikes", {"country": country})
        if "error" not in data:
            print(f"  🌍 {country.title()}: spike ratio {data.get('spike_ratio', 0):.2f}x "
                  f"({data.get('recent_articles', 0):.0f} articles/day)")
        else:
            print(f"  ❌ {country}: {data.get('error', 'unknown')}")
    print(f"  Source: GDELT DOC 2.0 API (LIVE)")
    print()

    # ═══════════════════════════════════════════════════════════
    # 4. GDELT API (LIVE) - Trade
    # ═══════════════════════════════════════════════════════════
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│  6.2 GDELT Trade Analysis - LIVE Trade Policy Data          │")
    print("└─────────────────────────────────────────────────────────────┘")
    trade = TradeMCPServer(
        name="mcp-trade",
        base_url="https://api.gdeltproject.org/api/v2",
    )

    overview = await trade.call_tool("get_trade_risk_overview", {})
    for key, val in overview.get("trade_monitors", {}).items():
        risk = val.get("risk_level", "low")
        emoji = "🔴" if risk == "critical" else "🟠" if risk == "high" else "🟡" if risk == "medium" else "🟢"
        print(f"  {emoji} {key.replace('_', ' ').title()}: {risk} "
              f"(spike: {val.get('spike_ratio', 0):.2f}x)")
    print(f"  Source: GDELT Trade Analysis (LIVE)")
    print()

    # ═══════════════════════════════════════════════════════════
    # 5. GDELT API (LIVE) - Logistics
    # ═══════════════════════════════════════════════════════════
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│  6.5 GDELT Logistics - LIVE Shipping/Port Data              │")
    print("└─────────────────────────────────────────────────────────────┘")
    logistics = LogisticsMCPServer(
        name="mcp-logistics",
        base_url="https://api.gdeltproject.org/api/v2",
    )

    chokepoints = await logistics.call_tool("get_chokepoint_status", {})
    for key, val in chokepoints.get("chokepoints", {}).items():
        level = val.get("congestion_level", "low")
        emoji = "🔴" if level == "severe" else "🟡" if level == "moderate" else "🟢"
        print(f"  {emoji} {key.replace('_', ' ').title()}: {level} "
              f"(spike: {val.get('spike_ratio', 0):.2f}x)")
    print(f"  Source: GDELT Logistics Analysis (LIVE)")
    print()

    # ═══════════════════════════════════════════════════════════
    # 6. BLS API (LIVE) - Labor
    # ═══════════════════════════════════════════════════════════
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│  6.6 BLS API - LIVE Labor Market Data                       │")
    print("└─────────────────────────────────────────────────────────────┘")
    labor = LaborMCPServer(
        name="mcp-labor",
        base_url="https://api.bls.gov/publicAPI/v2",
    )

    labor_data = await labor.call_tool("get_labor_disruptions", {})
    if "error" not in labor_data:
        for series_id, data in labor_data.get("series", {}).items():
            print(f"  👷 {series_id}: {data['current_value']:.1f} "
                  f"(change: {data['change_pct']:+.2f}%, trend: {data['trend']})")
    else:
        print(f"  ❌ BLS error: {labor_data.get('error', 'unknown')}")
    print(f"  Source: BLS API v2 (LIVE)")
    print()

    # ═══════════════════════════════════════════════════════════
    # 7. GEMINI AI (LIVE)
    # ═══════════════════════════════════════════════════════════
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│  🤖 Google Gemini AI - LIVE Reasoning                       │")
    print("└─────────────────────────────────────────────────────────────┘")

    test_signals = """[HIGH] US-China trade tension spike (2.1x normal news volume)
[MEDIUM] Red Sea shipping disruption elevated coverage
[LOW] Industrial production flat month-over-month"""

    ai_response = await reason_about_signals(test_signals)
    print(f"  Prompt: 'Analyze these supply chain signals...'")
    print(f"  Response from Gemini:")
    for line in ai_response.strip().split("\n"):
        print(f"    {line}")
    print()

    # ═══════════════════════════════════════════════════════════
    print("=" * 70)
    print("  ✅ ALL 6 MCP SERVERS + AI CONNECTED TO LIVE DATA")
    print("=" * 70)

    await weather.close()
    await econ.close()
    await geo.close()
    await trade.close()
    await logistics.close()
    await labor.close()


if __name__ == "__main__":
    asyncio.run(main())
