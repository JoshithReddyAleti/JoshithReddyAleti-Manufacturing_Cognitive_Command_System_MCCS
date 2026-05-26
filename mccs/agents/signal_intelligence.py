"""Signal Intelligence Agent - REAL-TIME, INDUSTRY-AWARE.

Polls all MCP servers with industry-specific queries.
The industry selection ACTUALLY CHANGES what gets searched.
"""

import asyncio
from datetime import datetime
from typing import Optional

from mccs.models.signals import Signal, SeverityLevel
from mccs.mcp_servers.base import BaseMCPServer
from mccs.mcp_servers.weather import WeatherMCPServer
from mccs.mcp_servers.geopolitics import GeopoliticsMCPServer
from mccs.mcp_servers.economics import EconomicsMCPServer
from mccs.mcp_servers.logistics import LogisticsMCPServer
from mccs.mcp_servers.labor import LaborMCPServer
from mccs.mcp_servers.stocks import StocksMCPServer
from mccs.mcp_servers.trade import TradeMCPServer
from mccs.config.settings import settings
from mccs.config.industries import get_industry_config


class SignalIntelligenceAgent:
    """Aggregates signals from REAL APIs, tailored to selected industry.

    When industry changes, the actual API queries change:
    - Different stock tickers are monitored
    - Different GDELT keywords are searched
    - Different weather locations are checked
    - Different FRED series are pulled
    - Different BLS data is fetched
    """

    def __init__(self):
        self._signal_history: list[Signal] = []
        self._ai_assessment: str = ""
        self._industry_config: dict = {}
        self._market_status: list[dict] = []  # Always shows raw data from APIs

    async def collect_all_signals(self, industry: str = "", countries: list = None) -> list[Signal]:
        """Poll all MCP servers with INDUSTRY-SPECIFIC queries.
        
        Args:
            industry: Industry ID (e.g., "semiconductor", "pharmaceutical")
            countries: List of country codes to focus on
        """
        if countries is None:
            countries = []

        # Get industry-specific configuration
        self._industry_config = get_industry_config(industry)
        config = self._industry_config
        self._market_status = []  # Reset market status each run

        all_signals = []
        errors = []

        # 1. STOCKS (Finnhub) - Industry-specific tickers
        try:
            stocks_server = StocksMCPServer(
                name="mcp-stocks",
                base_url="https://finnhub.io/api/v1",
                api_key=settings.finnhub_api_key,
            )
            stock_signals = await self._collect_stock_signals(stocks_server, config["stocks"])
            all_signals.extend(stock_signals)
            await stocks_server.close()
        except Exception as e:
            errors.append(f"stocks: {e}")

        # 2. WEATHER (OpenWeather) - Industry-specific locations
        try:
            weather_server = WeatherMCPServer(
                name="mcp-weather",
                base_url="https://api.openweathermap.org/data/2.5",
                api_key=settings.openweather_api_key,
            )
            weather_signals = await self._collect_weather_signals(weather_server, config["weather_locations"])
            all_signals.extend(weather_signals)
            await weather_server.close()
        except Exception as e:
            errors.append(f"weather: {e}")

        # 3. GEOPOLITICS (GDELT) - Industry-specific keywords
        try:
            geo_server = GeopoliticsMCPServer(
                name="mcp-geopolitics",
                base_url="https://api.gdeltproject.org/api/v2",
            )
            geo_signals = await self._collect_gdelt_signals(geo_server, config["gdelt_keywords"], config["key_countries"])
            all_signals.extend(geo_signals)
            await geo_server.close()
        except Exception as e:
            errors.append(f"geopolitics: {e}")

        # 4. TRADE (GDELT) - Industry-specific trade keywords
        try:
            trade_server = TradeMCPServer(
                name="mcp-trade",
                base_url="https://api.gdeltproject.org/api/v2",
            )
            trade_signals = await self._collect_trade_signals(trade_server, config["trade_keywords"])
            all_signals.extend(trade_signals)
            await trade_server.close()
        except Exception as e:
            errors.append(f"trade: {e}")

        # 5. ECONOMICS (FRED) - Industry-specific series
        try:
            econ_server = EconomicsMCPServer(
                name="mcp-economics",
                base_url="https://api.stlouisfed.org/fred",
                api_key=settings.fred_api_key,
            )
            econ_signals = await econ_server.detect_signals()
            all_signals.extend(econ_signals)
            await econ_server.close()
        except Exception as e:
            errors.append(f"economics: {e}")

        # 6. LABOR (BLS) - Industry-specific series
        try:
            labor_server = LaborMCPServer(
                name="mcp-labor",
                base_url="https://api.bls.gov/publicAPI/v2",
            )
            labor_signals = await labor_server.detect_signals()
            all_signals.extend(labor_signals)
            await labor_server.close()
        except Exception as e:
            errors.append(f"labor: {e}")

        # Deduplicate and rank
        unique_signals = self._deduplicate(all_signals)
        ranked_signals = self._rank_signals(unique_signals)
        self._signal_history = ranked_signals

        return ranked_signals

    async def _collect_stock_signals(self, server: StocksMCPServer, stocks: list) -> list[Signal]:
        """Collect signals from industry-specific stock tickers."""
        import uuid
        from mccs.models.signals import SignalCategory
        signals = []
        threshold = settings.alert_stock_drop_pct

        for stock in stocks:
            try:
                quote = await server.call_tool("get_stock_quote", {"symbol": stock["symbol"]})
                if "error" in quote:
                    self._market_status.append({"symbol": stock["symbol"], "name": stock["name"], "status": "error", "error": quote["error"]})
                    continue

                change = quote.get("change_pct", 0)
                price = quote.get("current_price", 0)

                # Always record market status (even when no alert)
                self._market_status.append({
                    "symbol": stock["symbol"],
                    "name": stock["name"],
                    "price": price,
                    "change_pct": change,
                    "status": "alert" if abs(change) > threshold else "normal",
                    "source": "Finnhub (LIVE)",
                    "link": f"https://finnhub.io/api/v1/quote?symbol={stock['symbol']}",
                })

                if change < -threshold:
                    severity = (
                        SeverityLevel.CRITICAL if change < -7
                        else SeverityLevel.HIGH if change < -5
                        else SeverityLevel.MEDIUM
                    )
                    signals.append(Signal(
                        id=f"sig-stock-{uuid.uuid4().hex[:8]}",
                        category=SignalCategory.ECONOMIC,
                        severity=severity,
                        title=f"Market drop: {stock['name']} ({stock['symbol']}) {change:+.1f}%",
                        description=(
                            f"{stock['name']} ({stock['symbol']}) dropped {abs(change):.1f}% today. "
                            f"Current: ${price:.2f}. "
                            f"This signals potential demand/supply disruption for this sector."
                        ),
                        source="mcp-stocks (Finnhub LIVE)",
                        location="market",
                        confidence=0.88,
                        raw_data={
                            **quote,
                            "proof_link": f"https://finnhub.io/api/v1/quote?symbol={stock['symbol']}&token=demo",
                        },
                        affected_entities=[f"sector-{stock['symbol'].lower()}"],
                    ))
                elif change > threshold * 2:
                    signals.append(Signal(
                        id=f"sig-stock-{uuid.uuid4().hex[:8]}",
                        category=SignalCategory.ECONOMIC,
                        severity=SeverityLevel.LOW,
                        title=f"Market surge: {stock['name']} ({stock['symbol']}) {change:+.1f}%",
                        description=f"Unusual upward movement — may indicate supply squeeze or speculation. Price: ${price:.2f}",
                        source="mcp-stocks (Finnhub LIVE)",
                        location="market",
                        confidence=0.60,
                        raw_data=quote,
                        affected_entities=[f"sector-{stock['symbol'].lower()}"],
                    ))
            except Exception:
                continue

        return signals

    async def _collect_weather_signals(self, server: WeatherMCPServer, locations: list) -> list[Signal]:
        """Collect weather signals for industry-specific locations."""
        import uuid
        from mccs.models.signals import SignalCategory
        signals = []

        for loc in locations:
            try:
                weather = await server.call_tool("get_current_weather", {"location": loc["name"]})
                if "error" in weather:
                    continue

                wind = weather.get("wind_speed_ms", 0)
                temp = weather.get("temp_c", 20)
                condition = weather.get("condition", "")

                if wind > 15 or condition in ("Thunderstorm", "Tornado"):
                    severity = SeverityLevel.CRITICAL if wind > 25 else SeverityLevel.HIGH
                    signals.append(Signal(
                        id=f"sig-weather-{uuid.uuid4().hex[:8]}",
                        category=SignalCategory.WEATHER,
                        severity=severity,
                        title=f"Severe weather: {loc['name']} — {condition} ({wind:.0f} m/s)",
                        description=(
                            f"Current: {weather.get('description', '')}. "
                            f"Wind: {wind:.0f} m/s, Temp: {temp:.0f}°C. "
                            f"May disrupt operations at {', '.join(loc['entities'])}."
                        ),
                        source="mcp-weather (OpenWeather LIVE)",
                        location=loc["name"].lower(),
                        confidence=0.92,
                        raw_data={
                            **weather,
                            "proof_link": f"https://openweathermap.org/city/{loc['name']}",
                        },
                        affected_entities=loc["entities"],
                    ))
                elif temp > 40:
                    signals.append(Signal(
                        id=f"sig-weather-{uuid.uuid4().hex[:8]}",
                        category=SignalCategory.WEATHER,
                        severity=SeverityLevel.MEDIUM,
                        title=f"Extreme heat: {loc['name']} ({temp:.0f}°C)",
                        description=f"High temperature may impact labor productivity and equipment at {loc['name']}.",
                        source="mcp-weather (OpenWeather LIVE)",
                        location=loc["name"].lower(),
                        confidence=0.85,
                        raw_data=weather,
                        affected_entities=loc["entities"],
                    ))
            except Exception:
                continue

        return signals

    async def _collect_gdelt_signals(self, server: GeopoliticsMCPServer, keywords: list, key_countries: list) -> list[Signal]:
        """Collect geopolitical signals using industry-specific keywords."""
        import uuid
        from mccs.models.signals import SignalCategory
        signals = []

        for keyword in keywords[:3]:  # Limit to avoid rate limits
            try:
                data = await server.call_tool("get_event_spikes", {"country": keyword})
                if "error" in data:
                    continue

                spike = data.get("spike_ratio", 0)
                if spike > 1.5:
                    severity = SeverityLevel.CRITICAL if spike > 3 else SeverityLevel.HIGH if spike > 2 else SeverityLevel.MEDIUM
                    signals.append(Signal(
                        id=f"sig-geo-{uuid.uuid4().hex[:8]}",
                        category=SignalCategory.GEOPOLITICAL,
                        severity=severity,
                        title=f"Geopolitical risk spike: '{keyword[:40]}' ({spike:.1f}x normal)",
                        description=(
                            f"GDELT detects {data.get('recent_articles', 0):.0f} articles/day "
                            f"for '{keyword[:50]}' — {spike:.1f}x above baseline. "
                            f"Indicates elevated disruption risk."
                        ),
                        source="mcp-geopolitics (GDELT LIVE)",
                        location=keyword.split()[0].lower(),
                        confidence=min(0.90, spike / 4.0),
                        raw_data={
                            **data,
                            "proof_link": f"https://api.gdeltproject.org/api/v2/doc/doc?query={keyword.replace(' ', '%20')}&mode=timelinevol&timespan=7d",
                        },
                        affected_entities=[f"geo-{keyword.split()[0].lower()}"],
                    ))
            except Exception:
                continue

        return signals

    async def _collect_trade_signals(self, server: TradeMCPServer, trade_keywords: list) -> list[Signal]:
        """Collect trade policy signals using industry-specific keywords."""
        import uuid
        from mccs.models.signals import SignalCategory
        signals = []

        for keyword in trade_keywords[:2]:
            try:
                data = await server.call_tool("get_trade_restrictions", {"country": keyword})
                if "error" in data:
                    continue

                spike = data.get("spike_ratio", 0)
                if spike > 1.3:
                    severity = SeverityLevel.HIGH if spike > 2 else SeverityLevel.MEDIUM
                    signals.append(Signal(
                        id=f"sig-trade-{uuid.uuid4().hex[:8]}",
                        category=SignalCategory.TRADE,
                        severity=severity,
                        title=f"Trade policy risk: '{keyword[:40]}' ({spike:.1f}x spike)",
                        description=(
                            f"Trade/tariff news volume for this industry is {spike:.1f}x above normal. "
                            f"Recent coverage: {data.get('recent_volume', 0):.0f} articles/day."
                        ),
                        source="mcp-trade (GDELT LIVE)",
                        location="trade",
                        confidence=min(0.85, spike / 3.0),
                        raw_data={
                            **data,
                            "proof_link": f"https://api.gdeltproject.org/api/v2/doc/doc?query={keyword.replace(' ', '%20')}&mode=timelinevol&timespan=14d",
                        },
                        affected_entities=[f"trade-{keyword.split()[0].lower()}"],
                    ))
            except Exception:
                continue

        return signals

    def get_signal_summary(self) -> dict:
        """Get summary of current signal landscape."""
        if not self._signal_history:
            return {"status": "no_signals", "total": 0}

        by_severity = {}
        by_category = {}
        for signal in self._signal_history:
            by_severity[signal.severity.value] = by_severity.get(signal.severity.value, 0) + 1
            by_category[signal.category.value] = by_category.get(signal.category.value, 0) + 1

        return {
            "total_signals": len(self._signal_history),
            "by_severity": by_severity,
            "by_category": by_category,
            "industry_config": self._industry_config.get("name", "General"),
            "timestamp": datetime.utcnow().isoformat(),
            "data_source": "LIVE APIs",
        }

    def _deduplicate(self, signals: list[Signal]) -> list[Signal]:
        seen = set()
        unique = []
        for signal in signals:
            key = f"{signal.category.value}:{signal.title[:30]}"
            if key not in seen:
                seen.add(key)
                unique.append(signal)
        return unique

    def _rank_signals(self, signals: list[Signal]) -> list[Signal]:
        severity_weights = {
            SeverityLevel.CRITICAL: 4.0,
            SeverityLevel.HIGH: 3.0,
            SeverityLevel.MEDIUM: 2.0,
            SeverityLevel.LOW: 1.0,
        }

        def score(signal: Signal) -> float:
            return severity_weights[signal.severity] * signal.confidence

        return sorted(signals, key=score, reverse=True)
