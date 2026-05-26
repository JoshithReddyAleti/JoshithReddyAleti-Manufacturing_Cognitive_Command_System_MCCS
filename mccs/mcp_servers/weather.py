"""MCP Weather Server - REAL OpenWeather API integration.

Detects extreme weather events that may impact plants, ports,
suppliers, and energy availability using LIVE data.
"""

import uuid
from typing import Any
import httpx

from mccs.mcp_servers.base import BaseMCPServer
from mccs.models.signals import Signal, SignalCategory, SeverityLevel
from mccs.config.settings import settings


SEVERITY_MAP = {
    "extreme": SeverityLevel.CRITICAL,
    "severe": SeverityLevel.HIGH,
    "moderate": SeverityLevel.MEDIUM,
    "minor": SeverityLevel.LOW,
}


class WeatherMCPServer(BaseMCPServer):
    """MCP server for weather and natural disruption detection.
    
    Uses REAL OpenWeather API for live weather data.
    """

    @property
    def category(self) -> SignalCategory:
        return SignalCategory.WEATHER

    async def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "get_current_weather",
                "description": "Get current weather conditions for a location (LIVE)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City name"}
                    },
                    "required": ["location"],
                },
            },
            {
                "name": "get_weather_alerts",
                "description": "Get active weather alerts for a location (LIVE)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lat": {"type": "number"},
                        "lon": {"type": "number"},
                    },
                    "required": ["lat", "lon"],
                },
            },
            {
                "name": "get_7day_forecast",
                "description": "Get 5-day forecast for a location (LIVE)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    },
                    "required": ["location"],
                },
            },
        ]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        if tool_name == "get_current_weather":
            return await self._get_current_weather(arguments["location"])
        elif tool_name == "get_weather_alerts":
            return await self._get_weather_alerts(arguments["lat"], arguments["lon"])
        elif tool_name == "get_7day_forecast":
            return await self._get_forecast(arguments["location"])
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _get_current_weather(self, location: str) -> dict:
        """Call OpenWeather Current Weather API."""
        url = f"{self.base_url}/weather"
        params = {
            "q": location,
            "appid": self.api_key,
            "units": "metric",
        }
        try:
            resp = await self._client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return {
                "location": location,
                "temp_c": data["main"]["temp"],
                "feels_like_c": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "wind_speed_ms": data["wind"]["speed"],
                "condition": data["weather"][0]["main"],
                "description": data["weather"][0]["description"],
                "pressure_hpa": data["main"]["pressure"],
                "visibility_m": data.get("visibility", 10000),
                "source": "OpenWeather API (LIVE)",
            }
        except Exception as e:
            return {"error": str(e), "location": location}

    async def _get_weather_alerts(self, lat: float, lon: float) -> dict:
        """Call OpenWeather One Call API for alerts."""
        # One Call API 3.0 endpoint
        url = "https://api.openweathermap.org/data/3.0/onecall"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "exclude": "minutely,hourly",
        }
        try:
            resp = await self._client.get(url, params=params)
            if resp.status_code == 401:
                # Fallback: use 2.5 forecast to detect extreme conditions
                return await self._detect_extreme_from_forecast(lat, lon)
            resp.raise_for_status()
            data = resp.json()
            alerts = data.get("alerts", [])
            return {
                "lat": lat,
                "lon": lon,
                "alerts": [
                    {
                        "event": a.get("event", "Unknown"),
                        "sender": a.get("sender_name", ""),
                        "description": a.get("description", "")[:200],
                        "start": a.get("start"),
                        "end": a.get("end"),
                    }
                    for a in alerts
                ],
                "alert_count": len(alerts),
                "source": "OpenWeather OneCall API (LIVE)",
            }
        except Exception:
            return await self._detect_extreme_from_forecast(lat, lon)

    async def _detect_extreme_from_forecast(self, lat: float, lon: float) -> dict:
        """Fallback: detect extreme weather from 5-day forecast data."""
        url = f"{self.base_url}/forecast"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric",
        }
        try:
            resp = await self._client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            alerts = []
            for item in data.get("list", [])[:16]:  # Next 48 hours
                wind = item["wind"]["speed"]
                temp = item["main"]["temp"]
                weather_main = item["weather"][0]["main"]

                # Detect extreme conditions
                if wind > 20:  # >20 m/s = storm force
                    alerts.append({
                        "event": f"High Wind Warning ({wind:.0f} m/s)",
                        "severity": "severe" if wind > 30 else "moderate",
                        "description": f"Wind speeds of {wind:.0f} m/s forecast",
                        "dt": item["dt_txt"],
                    })
                if temp > 42:
                    alerts.append({
                        "event": f"Extreme Heat ({temp:.0f}°C)",
                        "severity": "severe",
                        "description": f"Temperature reaching {temp:.0f}°C",
                        "dt": item["dt_txt"],
                    })
                if temp < -20:
                    alerts.append({
                        "event": f"Extreme Cold ({temp:.0f}°C)",
                        "severity": "severe",
                        "description": f"Temperature dropping to {temp:.0f}°C",
                        "dt": item["dt_txt"],
                    })
                if weather_main in ("Thunderstorm", "Tornado"):
                    alerts.append({
                        "event": f"Severe Weather: {weather_main}",
                        "severity": "extreme",
                        "description": item["weather"][0]["description"],
                        "dt": item["dt_txt"],
                    })

            return {
                "lat": lat,
                "lon": lon,
                "alerts": alerts,
                "alert_count": len(alerts),
                "source": "OpenWeather Forecast Analysis (LIVE)",
            }
        except Exception as e:
            return {"error": str(e), "lat": lat, "lon": lon, "alerts": []}

    async def _get_forecast(self, location: str) -> dict:
        """Get 5-day/3-hour forecast."""
        url = f"{self.base_url}/forecast"
        params = {
            "q": location,
            "appid": self.api_key,
            "units": "metric",
        }
        try:
            resp = await self._client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            forecasts = []
            for item in data.get("list", [])[:8]:  # Next 24 hours
                forecasts.append({
                    "dt": item["dt_txt"],
                    "temp_c": item["main"]["temp"],
                    "wind_ms": item["wind"]["speed"],
                    "condition": item["weather"][0]["main"],
                    "description": item["weather"][0]["description"],
                })
            return {
                "location": location,
                "forecasts": forecasts,
                "source": "OpenWeather Forecast API (LIVE)",
            }
        except Exception as e:
            return {"error": str(e), "location": location}

    async def detect_signals(self) -> list[Signal]:
        """Scan all monitored locations for REAL weather disruption signals."""
        signals = []

        for loc in settings.monitored_locations:
            # Get current weather
            weather = await self._get_current_weather(loc["name"])
            if "error" in weather:
                continue

            # Check for extreme conditions in current weather
            wind = weather.get("wind_speed_ms", 0)
            temp = weather.get("temp_c", 20)
            condition = weather.get("condition", "")

            if wind > 15 or condition in ("Thunderstorm", "Tornado", "Hurricane"):
                severity = SeverityLevel.CRITICAL if wind > 25 else SeverityLevel.HIGH
                signals.append(self._create_signal(
                    signal_id=f"sig-weather-{uuid.uuid4().hex[:8]}",
                    severity=severity,
                    title=f"Severe weather: {loc['name']} - {condition} ({wind:.0f} m/s wind)",
                    description=f"Current conditions at {loc['name']}: {weather.get('description', '')}. "
                                f"Wind: {wind:.0f} m/s, Temp: {temp:.0f}°C",
                    confidence=0.95,
                    location=loc["name"].lower(),
                    raw_data=weather,
                    affected_entities=loc["entities"],
                ))
            elif temp > 40:
                signals.append(self._create_signal(
                    signal_id=f"sig-weather-{uuid.uuid4().hex[:8]}",
                    severity=SeverityLevel.MEDIUM,
                    title=f"Extreme heat: {loc['name']} ({temp:.0f}°C)",
                    description=f"Temperature at {loc['name']} reaching {temp:.0f}°C. "
                                f"May impact labor productivity and equipment.",
                    confidence=0.90,
                    location=loc["name"].lower(),
                    raw_data=weather,
                    affected_entities=loc["entities"],
                ))

            # Check forecast for upcoming alerts
            alert_data = await self._get_weather_alerts(loc["lat"], loc["lon"])
            for alert in alert_data.get("alerts", []):
                sev_str = alert.get("severity", "moderate")
                severity = SEVERITY_MAP.get(sev_str, SeverityLevel.MEDIUM)
                signals.append(self._create_signal(
                    signal_id=f"sig-weather-{uuid.uuid4().hex[:8]}",
                    severity=severity,
                    title=f"{alert['event']} - {loc['name']}",
                    description=alert.get("description", "Weather alert detected")[:200],
                    confidence=0.85,
                    location=loc["name"].lower(),
                    raw_data=alert,
                    affected_entities=loc["entities"],
                ))

        return signals
