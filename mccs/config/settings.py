"""Application settings loaded from environment variables."""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Global application settings."""

    # LLM - Google Gemini
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gemini-2.0-flash"))

    # MCP Server API Keys
    openweather_api_key: str = field(
        default_factory=lambda: os.getenv("OPENWEATHER_API_KEY", "")
    )
    fred_api_key: str = field(default_factory=lambda: os.getenv("FRED_API_KEY", ""))
    finnhub_api_key: str = field(default_factory=lambda: os.getenv("FINNHUB_API_KEY", ""))

    # Simulation
    monte_carlo_iterations: int = 1000
    max_simulation_horizon_days: int = 90
    risk_threshold_high: float = 0.7
    risk_threshold_medium: float = 0.4

    # Causal Graph
    max_propagation_depth: int = 5
    confidence_decay_per_hop: float = 0.15

    # Auto-trigger thresholds
    alert_stock_drop_pct: float = 2.0  # Alert if sector drops > 2%
    alert_weather_wind_ms: float = 15.0  # Alert if wind > 15 m/s
    alert_gdelt_spike_ratio: float = 1.5  # Alert if news spike > 1.5x
    alert_fred_decline_pct: float = 1.0  # Alert if indicator drops > 1%

    # Monitored locations for weather (expanded to geopolitical cities)
    monitored_locations: list = field(default_factory=lambda: [
        {"name": "Houston", "lat": 29.76, "lon": -95.37, "entities": ["port-houston", "supplier-gulf-chemicals"]},
        {"name": "Shanghai", "lat": 31.23, "lon": 121.47, "entities": ["port-shanghai", "supplier-electronics-cn"]},
        {"name": "Rotterdam", "lat": 51.92, "lon": 4.48, "entities": ["port-rotterdam", "warehouse-eu-central"]},
        {"name": "Singapore", "lat": 1.35, "lon": 103.82, "entities": ["port-singapore", "route-malacca"]},
        {"name": "Taipei", "lat": 25.03, "lon": 121.57, "entities": ["supplier-semiconductors-tw"]},
        {"name": "Shenzhen", "lat": 22.54, "lon": 114.06, "entities": ["supplier-electronics-cn"]},
        {"name": "Detroit", "lat": 42.33, "lon": -83.05, "entities": ["plant-detroit-assembly"]},
        {"name": "Mumbai", "lat": 19.08, "lon": 72.88, "entities": ["supplier-textiles-india"]},
        {"name": "Busan", "lat": 35.18, "lon": 129.08, "entities": ["port-busan", "supplier-shipbuilding-kr"]},
        {"name": "Los Angeles", "lat": 33.94, "lon": -118.41, "entities": ["port-los-angeles"]},
        {"name": "Suez", "lat": 29.97, "lon": 32.55, "entities": ["route-suez"]},
        {"name": "Panama City", "lat": 8.98, "lon": -79.52, "entities": ["route-panama"]},
    ])

    # Stock sectors to monitor
    monitored_stocks: list = field(default_factory=lambda: [
        {"symbol": "XLI", "name": "Industrials ETF", "type": "sector"},
        {"symbol": "XLE", "name": "Energy ETF", "type": "sector"},
        {"symbol": "XLB", "name": "Materials ETF", "type": "sector"},
        {"symbol": "SOXX", "name": "Semiconductor ETF", "type": "sector"},
        {"symbol": "IYT", "name": "Transportation ETF", "type": "sector"},
        {"symbol": "TSM", "name": "TSMC", "type": "stock"},
        {"symbol": "CAT", "name": "Caterpillar", "type": "stock"},
        {"symbol": "UPS", "name": "UPS", "type": "stock"},
    ])


# Singleton
settings = Settings()
