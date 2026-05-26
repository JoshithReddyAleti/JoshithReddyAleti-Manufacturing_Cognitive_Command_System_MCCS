"""Base MCP server class with common functionality."""

from abc import ABC, abstractmethod
from typing import Any
import httpx
from mccs.models.signals import Signal, SignalCategory, SeverityLevel


class BaseMCPServer(ABC):
    """Abstract base class for all MCP servers.

    Each MCP server wraps a single external data source and exposes
    clean tool interfaces for agents to consume.
    """

    def __init__(self, name: str, base_url: str, api_key: str = "", timeout: int = 30):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout, verify=False)

    @property
    @abstractmethod
    def category(self) -> SignalCategory:
        """The signal category this server produces."""
        ...

    @abstractmethod
    async def get_tools(self) -> list[dict[str, Any]]:
        """Return the list of tools this MCP server exposes."""
        ...

    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Execute a tool by name with given arguments."""
        ...

    @abstractmethod
    async def detect_signals(self) -> list[Signal]:
        """Poll the data source and return any disruption signals."""
        ...

    def _create_signal(
        self,
        signal_id: str,
        severity: SeverityLevel,
        title: str,
        description: str,
        confidence: float,
        location: str = "",
        raw_data: dict = None,
        affected_entities: list[str] = None,
    ) -> Signal:
        """Helper to create a properly formatted Signal."""
        return Signal(
            id=signal_id,
            category=self.category,
            severity=severity,
            title=title,
            description=description,
            source=self.name,
            location=location or None,
            confidence=confidence,
            raw_data=raw_data or {},
            affected_entities=affected_entities or [],
        )

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
