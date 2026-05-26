"""MCCS - Manufacturing Cognitive Command System
Interactive Web Application with:
- Real-time data from 7 MCP servers (OpenWeather, FRED, GDELT, BLS, Finnhub)
- AI-powered reasoning (Google Gemini)
- Auto-trigger alerts
- Chatbot interface
- Email summary generation
- Hyperlinks to data sources as proof
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import streamlit as st
from datetime import datetime

from mccs.agents.orchestrator import MCCSOrchestrator, MCCSResult
from mccs.agents.chatbot import ChatbotAgent
from mccs.agents.email_generator import EmailGenerator
from mccs.agents.auto_trigger import AutoTriggerEngine
from mccs.config.settings import settings


# Page config
st.set_page_config(
    page_title="MCCS - Manufacturing Cognitive Command System",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS
st.markdown("""
<style>
    .main-header { font-size: 2em; font-weight: 700; color: #1e293b; }
    .sub-header { font-size: 1em; color: #64748b; margin-top: -10px; }
    .live-badge { background: #10b981; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.7em; }
    .signal-card { border-left: 4px solid; padding: 12px; margin: 8px 0; background: rgba(0,0,0,0.02); border-radius: 4px; }
    .proof-link { font-size: 0.8em; color: #3b82f6; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_orchestrator():
    return MCCSOrchestrator()


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def main():
    # Header
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown('<p class="main-header">🏭 MCCS - Manufacturing Cognitive Command System</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Real-time disruption intelligence powered by live APIs + Google Gemini AI</p>', unsafe_allow_html=True)
    with col_h2:
        st.markdown(f'<span class="live-badge">🔴 LIVE DATA</span>', unsafe_allow_html=True)
        st.caption(f"Last update: {datetime.utcnow().strftime('%H:%M:%S UTC')}")

    st.divider()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Control Panel")
        st.caption("All data is REAL-TIME from public APIs")

        st.subheader("Data Sources (LIVE)")
        st.markdown("""
        - 🌡️ [OpenWeather API](https://openweathermap.org) — Weather
        - 📈 [FRED](https://fred.stlouisfed.org) — Economics
        - 🌍 [GDELT](https://gdeltproject.org) — Geopolitics
        - 📊 [Finnhub](https://finnhub.io) — Stock Market
        - 👷 [BLS](https://www.bls.gov) — Labor
        - 🚢 [GDELT](https://gdeltproject.org) — Logistics
        """)

        st.divider()
        st.subheader("🤖 AI Engine")
        st.markdown(f"**Model:** Google Gemini ({settings.llm_model})")

        st.divider()
        num_scenarios = st.slider("Scenarios to simulate", 3, 15, 8)

        st.divider()
        st.subheader("Auto-Trigger Thresholds")
        settings.alert_stock_drop_pct = st.slider("Stock drop alert (%)", 1.0, 10.0, 3.0)
        settings.alert_weather_wind_ms = st.slider("Wind alert (m/s)", 10.0, 30.0, 15.0)

    # Main content
    orchestrator = get_orchestrator()

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        run_btn = st.button("🚀 Run Full Analysis", type="primary", use_container_width=True)
    with col2:
        email_btn = st.button("📧 Generate Email Summary", use_container_width=True)
    with col3:
        clear_btn = st.button("🗑️ Clear Results", use_container_width=True)

    if clear_btn:
        if "result" in st.session_state:
            del st.session_state["result"]
        st.rerun()

    if run_btn:
        with st.spinner("🔍 Collecting LIVE data from 7 MCP servers..."):
            result = run_async(orchestrator.run_full_analysis(num_scenarios))
            st.session_state.result = result
        st.rerun()

    # Tabs
    if "result" not in st.session_state:
        st.info("👆 Click **Run Full Analysis** to collect real-time data from all sources.")
        # Show chatbot even without analysis
        _render_chatbot(orchestrator)
        return

    result: MCCSResult = st.session_state.result

    # Email generation
    if email_btn:
        email = orchestrator.email_generator.generate_summary_email(result)
        st.session_state.email = email

    # Main tabs
    tabs = st.tabs([
        "📋 Executive Briefing",
        "⚠️ Live Signals",
        "📊 Stock Market",
        "🔮 Scenarios",
        "💡 Recommendations",
        "🔔 Auto-Triggers",
        "📧 Email Summary",
        "💬 AI Chatbot",
        "🔗 Causal Graph",
    ])

    # TAB 1: Executive Briefing
    with tabs[0]:
        briefing = result.executive_briefing
        st.markdown(f"### {briefing.get('headline', '')}")

        # AI Narrative
        ai_narrative = briefing.get("ai_narrative", "")
        if ai_narrative and "[" not in ai_narrative:
            st.info(f"🤖 **AI Analysis (Gemini):** {ai_narrative}")

        st.markdown(briefing.get("situation_summary", ""))
        st.divider()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Active Signals", len(result.signals))
        with col2:
            st.metric("Scenarios", len(result.scenarios))
        with col3:
            st.metric("Expected Exposure", f"${result.financial_impact.get('expected_loss_usd', 0):,.0f}")
        with col4:
            st.metric("Recommendations", len(result.recommendations))

        st.subheader("Risk Narrative")
        st.markdown(briefing.get("risk_narrative", ""))
        st.subheader("Recommended Actions")
        st.markdown(briefing.get("action_brief", ""))
        st.caption(f"📡 Data source: {briefing.get('data_source', 'LIVE APIs')}")

    # TAB 2: Live Signals
    with tabs[1]:
        st.subheader(f"⚠️ Live Disruption Signals ({len(result.signals)})")
        if not result.signals:
            st.success("✅ No disruption signals detected. All monitored systems nominal.")
            st.caption("The system monitors weather, economics, geopolitics, stocks, logistics, and labor in real-time.")
        else:
            for signal in result.signals:
                color = {"critical": "#dc2626", "high": "#ea580c", "medium": "#ca8a04", "low": "#16a34a"}
                c = color.get(signal.severity.value, "#666")
                proof = signal.raw_data.get("proof_link", signal.raw_data.get("link", ""))
                st.markdown(f"""
                <div style="border-left: 4px solid {c}; padding: 12px; margin: 8px 0; background: rgba(0,0,0,0.02); border-radius: 4px;">
                    <strong>{signal.title}</strong>
                    <span style="background:{c}; color:white; padding:2px 8px; border-radius:12px; font-size:0.75em; margin-left:8px;">{signal.severity.value.upper()}</span>
                    <p style="margin:8px 0 4px 0; color:#555;">{signal.description}</p>
                    <div style="font-size:0.8em; color:#888;">
                        Source: {signal.source} | Location: {signal.location or 'Global'} | Confidence: {signal.confidence:.0%}
                        {f' | <a href="{proof}" target="_blank">🔗 Proof</a>' if proof else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # TAB 3: Stock Market
    with tabs[2]:
        st.subheader("📊 Stock Market Monitor (Finnhub LIVE)")
        st.caption("Manufacturing-relevant sectors and companies")
        # Show stock data from signals
        stock_signals = [s for s in result.signals if "Market" in s.title or "stock" in s.source]
        if stock_signals:
            for s in stock_signals:
                st.markdown(f"**{s.title}** — {s.description[:150]}")
        else:
            st.info("No significant stock market disruptions detected. Sectors within normal range.")
        st.markdown("[📈 View on Finnhub](https://finnhub.io/)")

    # TAB 4: Scenarios
    with tabs[3]:
        st.subheader(f"🔮 Simulated Scenarios ({len(result.scenarios)})")
        for i, scenario in enumerate(result.scenarios[:8]):
            with st.expander(f"{'🔴' if scenario.probability > 0.3 else '🟠' if scenario.probability > 0.1 else '🟡'} {scenario.name} — ${scenario.total_revenue_at_risk_usd:,.0f} at risk ({scenario.probability:.0%})", expanded=(i == 0)):
                st.markdown(scenario.explanation)
                if scenario.recommended_actions:
                    st.markdown("**Actions:**")
                    for a in scenario.recommended_actions:
                        st.markdown(f"- {a}")

    # TAB 5: Recommendations
    with tabs[4]:
        st.subheader(f"💡 Recommendations ({len(result.recommendations)})")
        for rec in result.recommendations:
            roi = ((rec.estimated_savings_usd - rec.estimated_cost_usd) / rec.estimated_cost_usd * 100) if rec.estimated_cost_usd > 0 else 0
            st.markdown(f"### {rec.title}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Cost", f"${rec.estimated_cost_usd:,.0f}")
            with col2:
                st.metric("Savings", f"${rec.estimated_savings_usd:,.0f}")
            with col3:
                st.metric("ROI", f"{roi:.0f}%")
            st.caption(f"💡 {rec.explanation}")
            st.markdown("⚠️ *Requires human approval*")
            st.divider()

    # TAB 6: Auto-Triggers
    with tabs[5]:
        st.subheader("🔔 Auto-Trigger System (Bounded Autonomy)")
        triggers = orchestrator.auto_trigger.get_trigger_summary()
        st.metric("Triggers Fired", triggers["total_triggers"])
        st.metric("Escalations Needed", triggers["escalations_needed"])
        if triggers["recent_triggers"]:
            for t in triggers["recent_triggers"]:
                st.warning(f"**{t['title']}** — Action: {t['action']}")
                if t.get("proof"):
                    st.markdown(f"[🔗 Source proof]({t['proof']})")
        else:
            st.success("No auto-triggers fired. All thresholds within normal range.")

    # TAB 7: Email Summary
    with tabs[6]:
        st.subheader("📧 Email Summary Generator")
        if "email" in st.session_state:
            email = st.session_state.email
            st.markdown(f"**To:** {email['to']}")
            st.markdown(f"**Subject:** {email['subject']}")
            st.divider()
            st.markdown("### Preview (HTML)")
            st.components.v1.html(email["body_html"], height=600, scrolling=True)
            st.divider()
            st.markdown("### Plain Text Version")
            st.code(email["body_text"], language=None)
        else:
            st.info("Click '📧 Generate Email Summary' above to create an email.")

    # TAB 8: Chatbot
    with tabs[7]:
        _render_chatbot(orchestrator)

    # TAB 9: Causal Graph
    with tabs[8]:
        st.subheader("🔗 Manufacturing Value Chain")
        stats = result.graph_stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nodes", stats.get("total_nodes", 0))
        with col2:
            st.metric("Edges", stats.get("total_edges", 0))
        with col3:
            st.metric("DAG Valid", "✅" if stats.get("is_dag") else "❌")

        ranking = orchestrator.graph.get_node_criticality_ranking()
        if ranking:
            st.subheader("Node Criticality Ranking")
            for i, node in enumerate(ranking[:10], 1):
                risk_emoji = "🔴" if node["current_risk"] > 0.5 else "🟡" if node["current_risk"] > 0.2 else "🟢"
                st.markdown(f"{i}. {risk_emoji} **{node['name']}** (centrality: {node['centrality']:.3f})")


def _render_chatbot(orchestrator):
    """Render the AI chatbot interface."""
    st.subheader("💬 AI Chatbot (Gemini-powered)")
    st.caption("Ask questions about signals, scenarios, supply chain risks, or recommendations.")

    # Chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask MCCS anything..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = run_async(orchestrator.chatbot.chat(prompt))
            st.markdown(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
