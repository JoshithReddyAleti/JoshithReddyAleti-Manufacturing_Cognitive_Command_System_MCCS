"""MCCS Chatbot Agent - Gemini-powered conversational interface.

Allows users to ask questions about:
- Current signals and their meaning
- Scenario details and probabilities
- Recommendations and trade-offs
- Supply chain relationships
- Historical patterns

Uses the LLM gateway + all agent context to answer.
"""

from google import genai
from mccs.config.settings import settings


SYSTEM_PROMPT = """You are the MCCS (Manufacturing Cognitive Command System) AI assistant.
You help manufacturing executives and supply chain analysts understand disruption risks.

You have access to real-time data from:
- OpenWeather API (weather at key ports/plants)
- FRED (Federal Reserve economic indicators)
- GDELT (geopolitical event monitoring)
- Finnhub (stock market data)
- BLS (labor statistics)

When answering:
1. Be concise and actionable
2. Reference specific data points when available
3. Explain confidence levels
4. Suggest next steps
5. If you don't know something, say so clearly

You are NOT a general chatbot. Stay focused on supply chain disruption intelligence."""


class ChatbotAgent:
    """Gemini-powered chatbot for MCCS user interaction."""

    def __init__(self):
        self._client = None
        self._context = ""
        self._history = []

    def _get_client(self):
        if self._client is None:
            self._client = genai.Client(
                api_key=settings.gemini_api_key,
                http_options={"api_version": "v1beta"},
            )
        return self._client

    def set_context(self, context: str):
        """Update the chatbot's context with latest analysis results."""
        self._context = context

    def build_context_from_result(self, result) -> str:
        """Build context string from MCCSResult."""
        lines = ["CURRENT MCCS ANALYSIS STATE:"]
        lines.append(f"- Active signals: {len(result.signals)}")
        for s in result.signals[:5]:
            lines.append(f"  [{s.severity.value}] {s.title} (source: {s.source})")

        lines.append(f"\n- Scenarios simulated: {len(result.scenarios)}")
        for s in result.scenarios[:3]:
            lines.append(f"  {s.name}: {s.probability:.0%} probability, ${s.total_revenue_at_risk_usd:,.0f} at risk")

        lines.append(f"\n- Recommendations: {len(result.recommendations)}")
        for r in result.recommendations[:3]:
            lines.append(f"  {r.title}: cost ${r.estimated_cost_usd:,.0f}, saves ${r.estimated_savings_usd:,.0f}")

        fi = result.financial_impact
        lines.append(f"\n- Financial exposure: ${fi.get('expected_loss_usd', 0):,.0f} expected")
        lines.append(f"- Worst case: ${fi.get('worst_case_usd', 0):,.0f}")

        sc = result.supply_chain_assessment
        lines.append(f"\n- Supply chain: {sc.get('high_risk_suppliers', 0)} high-risk suppliers")
        lines.append(f"- Diversification score: {sc.get('diversification_score', 0):.0f}%")

        context = "\n".join(lines)
        self._context = context
        return context

    async def chat(self, user_message: str) -> str:
        """Process a user message and return AI response."""
        client = self._get_client()

        # Build full prompt with context
        full_prompt = f"""{SYSTEM_PROMPT}

{self._context}

CONVERSATION HISTORY:
{self._format_history()}

USER QUESTION: {user_message}

Respond concisely and helpfully. If the question relates to current data, reference the analysis state above."""

        try:
            response = client.models.generate_content(
                model=settings.llm_model,
                contents=full_prompt,
            )
            answer = response.text
        except Exception as e:
            # Try fallback model
            try:
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=full_prompt,
                )
                answer = response.text
            except Exception as e2:
                return (
                    f"The AI service is temporarily rate-limited (Gemini free tier: 15 req/min, 1500/day). "
                    f"Please wait 60 seconds and try again. "
                    f"Meanwhile, all data analysis (signals, scenarios, recommendations) works without AI."
                )

        # Store in history
        self._history.append({"role": "user", "content": user_message})
        self._history.append({"role": "assistant", "content": answer})

        if len(self._history) > 20:
            self._history = self._history[-20:]

        return answer

    def _format_history(self) -> str:
        if not self._history:
            return "(No previous messages)"
        lines = []
        for msg in self._history[-6:]:
            role = "User" if msg["role"] == "user" else "MCCS"
            lines.append(f"{role}: {msg['content'][:200]}")
        return "\n".join(lines)

    def clear_history(self):
        """Clear conversation history."""
        self._history = []
