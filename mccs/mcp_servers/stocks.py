"""MCP Stocks Server - REAL Finnhub API integration.

Monitors stock market swings for manufacturing-relevant sectors
and individual companies to detect demand/supply shocks.
"""

import uuid
from typing import Any
from mccs.mcp_servers.base import BaseMCPServer
from mccs.models.signals import Signal, SignalCategory, SeverityLevel
from mccs.config.settings import settings


class StocksMCPServer(BaseMCPServer):
    """MCP server for REAL stock market data from Finnhub."""

    @property
    def category(self) -> SignalCategory:
        return SignalCategory.ECONOMIC

    async def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "get_stock_quote",
                "description": "Get real-time stock quote from Finnhub (LIVE)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock ticker symbol"}
                    },
                    "required": ["symbol"],
                },
            },
            {
                "name": "get_market_news",
                "description": "Get latest market news from Finnhub (LIVE)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "general, forex, crypto, merger"}
                    },
                    "required": ["category"],
                },
            },
            {
                "name": "get_sector_performance",
                "description": "Get sector ETF performance (LIVE)",
                "parameters": {"type": "object", "properties": {}},
            },
        ]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        if tool_name == "get_stock_quote":
            return await self._get_quote(arguments["symbol"])
        elif tool_name == "get_market_news":
            return await self._get_news(arguments.get("category", "general"))
        elif tool_name == "get_sector_performance":
            return await self._get_sector_performance()
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _get_quote(self, symbol: str) -> dict:
        """Get real-time quote from Finnhub."""
        url = "https://finnhub.io/api/v1/quote"
        params = {"symbol": symbol, "token": self.api_key}
        try:
            resp = await self._client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            current = data.get("c", 0)
            prev_close = data.get("pc", 0)
            change_pct = ((current - prev_close) / prev_close * 100) if prev_close else 0

            return {
                "symbol": symbol,
                "current_price": current,
                "previous_close": prev_close,
                "change_pct": round(change_pct, 2),
                "high": data.get("h", 0),
                "low": data.get("l", 0),
                "open": data.get("o", 0),
                "timestamp": data.get("t", 0),
                "source": "Finnhub API (LIVE)",
                "link": f"https://finnhub.io/api/v1/quote?symbol={symbol}",
            }
        except Exception as e:
            return {"symbol": symbol, "error": str(e)}

    async def _get_news(self, category: str) -> dict:
        """Get market news from Finnhub."""
        url = "https://finnhub.io/api/v1/news"
        params = {"category": category, "token": self.api_key}
        try:
            resp = await self._client.get(url, params=params)
            resp.raise_for_status()
            articles = resp.json()[:5]
            return {
                "category": category,
                "articles": [
                    {
                        "headline": a.get("headline", ""),
                        "source": a.get("source", ""),
                        "url": a.get("url", ""),
                        "summary": a.get("summary", "")[:150],
                        "datetime": a.get("datetime", 0),
                    }
                    for a in articles
                ],
                "source": "Finnhub News API (LIVE)",
            }
        except Exception as e:
            return {"category": category, "error": str(e)}

    async def _get_sector_performance(self) -> dict:
        """Get performance of monitored sector ETFs."""
        results = []
        for stock in settings.monitored_stocks:
            quote = await self._get_quote(stock["symbol"])
            if "error" not in quote:
                results.append({
                    "symbol": stock["symbol"],
                    "name": stock["name"],
                    "type": stock["type"],
                    "change_pct": quote["change_pct"],
                    "current_price": quote["current_price"],
                    "link": quote.get("link", ""),
                })
        return {
            "sectors": sorted(results, key=lambda x: x["change_pct"]),
            "source": "Finnhub API (LIVE)",
            "worst_performer": results[0]["name"] if results else "N/A",
        }

    async def detect_signals(self) -> list[Signal]:
        """Detect stock market disruption signals from REAL Finnhub data."""
        signals = []
        threshold = settings.alert_stock_drop_pct

        for stock in settings.monitored_stocks:
            quote = await self._get_quote(stock["symbol"])
            if "error" in quote:
                continue

            change = quote.get("change_pct", 0)

            if change < -threshold:
                severity = (
                    SeverityLevel.CRITICAL if change < -7
                    else SeverityLevel.HIGH if change < -5
                    else SeverityLevel.MEDIUM
                )
                signals.append(self._create_signal(
                    signal_id=f"sig-stock-{uuid.uuid4().hex[:8]}",
                    severity=severity,
                    title=f"Market drop: {stock['name']} ({stock['symbol']}) {change:+.1f}%",
                    description=(
                        f"{stock['name']} ({stock['symbol']}) dropped {abs(change):.1f}% today. "
                        f"Current: ${quote['current_price']:.2f}, Prev close: ${quote['previous_close']:.2f}. "
                        f"This may signal demand weakness or sector disruption."
                    ),
                    confidence=0.85,
                    location="market",
                    raw_data={**quote, "proof_link": quote.get("link", "")},
                    affected_entities=self._infer_affected(stock),
                ))
            elif change > threshold * 2:
                # Unusual spike can also signal disruption (panic buying, supply squeeze)
                signals.append(self._create_signal(
                    signal_id=f"sig-stock-{uuid.uuid4().hex[:8]}",
                    severity=SeverityLevel.LOW,
                    title=f"Market spike: {stock['name']} ({stock['symbol']}) {change:+.1f}%",
                    description=f"Unusual upward movement may indicate supply squeeze or speculation.",
                    confidence=0.60,
                    location="market",
                    raw_data=quote,
                    affected_entities=self._infer_affected(stock),
                ))

        return signals

    def _infer_affected(self, stock: dict) -> list[str]:
        mapping = {
            "XLI": ["all-plants", "all-suppliers"],
            "XLE": ["supplier-gulf-chemicals", "supplier-energy-ru"],
            "XLB": ["supplier-rare-earth", "supplier-gulf-chemicals"],
            "SOXX": ["supplier-semiconductors-tw", "supplier-electronics-cn"],
            "IYT": ["all-logistics", "port-houston", "port-los-angeles"],
            "TSM": ["supplier-semiconductors-tw"],
            "CAT": ["plant-detroit-assembly", "demand-all-markets"],
            "UPS": ["all-logistics"],
        }
        return mapping.get(stock["symbol"], ["market-general"])
