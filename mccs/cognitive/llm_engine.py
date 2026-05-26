"""LLM Reasoning Engine - Google Gemini integration.

Powers the AI reasoning across all agents:
- Causal reasoning about disruption propagation
- Scenario narrative generation
- Executive explanation synthesis
- Signal interpretation and anomaly detection
"""

from google import genai
from mccs.config.settings import settings
import ssl
import httpx

# Initialize Gemini client
_client = None


def get_llm_client():
    """Get or create the Gemini client."""
    global _client
    if _client is None:
        _client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options={"api_version": "v1beta"},
        )
    return _client


async def reason_about_signals(signals_summary: str) -> str:
    """Use Gemini to reason about what disruption signals mean together."""
    client = get_llm_client()
    prompt = f"""You are a manufacturing supply chain intelligence analyst. 
Analyze these real-time disruption signals and provide a brief, actionable assessment.

SIGNALS DETECTED:
{signals_summary}

Provide:
1. What is the most critical threat right now? (1-2 sentences)
2. How might these signals interact/compound? (1-2 sentences)  
3. What should leadership know immediately? (1-2 sentences)

Be concise and specific. Use plain business language."""

    try:
        response = client.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        # Try fallback model
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
            )
            return response.text
        except Exception:
            return f"[AI reasoning unavailable: {e}]"


async def generate_executive_narrative(
    signals_count: int,
    top_signal: str,
    expected_loss: float,
    worst_case: float,
    recommendations: list[str],
) -> str:
    """Use Gemini to generate an executive-level narrative."""
    client = get_llm_client()
    prompt = f"""You are writing a 3-sentence executive briefing for a manufacturing COO.

FACTS:
- {signals_count} active disruption signals detected across the supply chain
- Most critical: {top_signal}
- Expected financial exposure: ${expected_loss:,.0f}
- Worst-case scenario: ${worst_case:,.0f}
- Top recommendations: {', '.join(recommendations[:3])}

Write exactly 3 sentences: (1) What's happening, (2) What's at risk, (3) What to do.
Be direct. No jargon. No hedging."""

    try:
        response = client.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"[LLM narrative unavailable: {e}]"


async def interpret_causal_chain(chain_description: str) -> str:
    """Use Gemini to explain a causal propagation chain in plain language."""
    client = get_llm_client()
    prompt = f"""Convert this technical supply chain propagation analysis into a 2-3 sentence 
plain-language explanation that a business executive would understand.

TECHNICAL ANALYSIS:
{chain_description}

Write in plain business English. Focus on: what breaks, when, and how bad."""

    try:
        response = client.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"[LLM interpretation unavailable: {e}]"


async def assess_compound_risk(signal_descriptions: list[str]) -> str:
    """Use Gemini to assess how multiple signals might compound."""
    client = get_llm_client()
    signals_text = "\n".join(f"- {s}" for s in signal_descriptions[:8])
    prompt = f"""You are a supply chain risk analyst. These disruption signals are active simultaneously:

{signals_text}

In 2-3 sentences, explain:
1. Which signals could amplify each other?
2. What's the compound risk that individual analysis would miss?

Be specific about the interaction effects."""

    try:
        response = client.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"[LLM compound analysis unavailable: {e}]"
