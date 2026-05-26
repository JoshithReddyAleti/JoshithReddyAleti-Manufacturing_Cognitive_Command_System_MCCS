"""Reusable Streamlit UI components for MCCS."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
from mccs.models.signals import Signal, Scenario, Recommendation, SeverityLevel


SEVERITY_COLORS = {
    "critical": "#dc2626",
    "high": "#ea580c",
    "medium": "#ca8a04",
    "low": "#16a34a",
}

CATEGORY_ICONS = {
    "weather": "🌪️",
    "trade": "📊",
    "geopolitical": "🌍",
    "economic": "📈",
    "logistics": "🚢",
    "labor": "👷",
}


def render_signal_card(signal: Signal):
    """Render a single signal as a styled card."""
    icon = CATEGORY_ICONS.get(signal.category.value, "⚠️")
    color = SEVERITY_COLORS.get(signal.severity.value, "#666")

    st.markdown(
        f"""
        <div style="border-left: 4px solid {color}; padding: 12px; margin: 8px 0;
                    background: rgba(0,0,0,0.02); border-radius: 4px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong>{icon} {signal.title}</strong>
                <span style="background: {color}; color: white; padding: 2px 8px;
                             border-radius: 12px; font-size: 0.75em;">
                    {signal.severity.value.upper()}
                </span>
            </div>
            <p style="margin: 8px 0 4px 0; color: #555;">{signal.description}</p>
            <div style="font-size: 0.8em; color: #888;">
                Source: {signal.source} | Location: {signal.location or 'Global'} |
                Confidence: {signal.confidence:.0%}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_scenario_card(scenario: Scenario, expanded: bool = False):
    """Render a scenario as an expandable card."""
    prob_color = (
        SEVERITY_COLORS["critical"] if scenario.probability > 0.5
        else SEVERITY_COLORS["high"] if scenario.probability > 0.2
        else SEVERITY_COLORS["medium"]
    )

    with st.expander(
        f"{'🔴' if scenario.probability > 0.5 else '🟠' if scenario.probability > 0.2 else '🟡'} "
        f"{scenario.name} — ${scenario.total_revenue_at_risk_usd:,.0f} at risk "
        f"({scenario.probability:.0%} probability)",
        expanded=expanded,
    ):
        st.markdown(scenario.explanation)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Revenue at Risk", f"${scenario.total_revenue_at_risk_usd:,.0f}")
        with col2:
            st.metric("Probability", f"{scenario.probability:.0%}")
        with col3:
            st.metric("Impacts", f"{len(scenario.impacts)} pathways")

        if scenario.recommended_actions:
            st.markdown("**Recommended Actions:**")
            for action in scenario.recommended_actions:
                st.markdown(f"- {action}")


def render_recommendation_card(rec: Recommendation):
    """Render a recommendation with approve/reject buttons."""
    urgency_color = SEVERITY_COLORS.get(rec.urgency.value, "#666")

    st.markdown(
        f"""
        <div style="border: 1px solid {urgency_color}; padding: 16px; margin: 8px 0;
                    border-radius: 8px;">
            <h4 style="margin: 0 0 8px 0;">{rec.title}</h4>
            <p>{rec.description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Cost", f"${rec.estimated_cost_usd:,.0f}")
    with col2:
        st.metric("Savings", f"${rec.estimated_savings_usd:,.0f}")
    with col3:
        net = rec.estimated_savings_usd - rec.estimated_cost_usd
        st.metric("Net Benefit", f"${net:,.0f}")
    with col4:
        roi = ((rec.estimated_savings_usd - rec.estimated_cost_usd) / rec.estimated_cost_usd * 100)
        st.metric("ROI", f"{roi:.0f}%")

    st.caption(f"💡 {rec.explanation}")

    if rec.requires_approval:
        col_a, col_b = st.columns(2)
        with col_a:
            st.button(f"✅ Approve", key=f"approve-{rec.id}")
        with col_b:
            st.button(f"❌ Reject", key=f"reject-{rec.id}")


def render_financial_dashboard(financial: dict):
    """Render financial impact dashboard."""
    st.subheader("💰 Financial Impact Summary")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Expected Loss",
            f"${financial.get('expected_loss_usd', 0):,.0f}",
        )
    with col2:
        st.metric(
            "Worst Case",
            f"${financial.get('worst_case_usd', 0):,.0f}",
        )
    with col3:
        st.metric(
            "Net Exposure",
            f"${financial.get('net_exposure_usd', 0):,.0f}",
        )
    with col4:
        roi = financial.get("mitigation_roi", {})
        st.metric(
            "Mitigation ROI",
            f"{roi.get('roi_pct', 0):.0f}%",
        )

    # Margin erosion gauge
    margin = financial.get("margin_erosion_pct", 0)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=margin,
        title={"text": "Margin Erosion (%)"},
        gauge={
            "axis": {"range": [0, 5]},
            "bar": {"color": "darkred"},
            "steps": [
                {"range": [0, 1], "color": "lightgreen"},
                {"range": [1, 3], "color": "yellow"},
                {"range": [3, 5], "color": "salmon"},
            ],
        },
    ))
    fig.update_layout(height=250, margin=dict(t=50, b=0, l=30, r=30))
    st.plotly_chart(fig, use_container_width=True)


def render_causal_graph(graph_data: dict):
    """Render the causal graph as an interactive network visualization."""
    st.subheader("🔗 Causal Graph - Manufacturing Value Chain")

    # Build NetworkX graph for layout
    G = nx.DiGraph()
    for node in graph_data["nodes"]:
        G.add_node(node["id"])
    for edge in graph_data["edges"]:
        G.add_edge(edge["source"], edge["target"])

    # Use spring layout
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

    # Create Plotly figure
    edge_x, edge_y = [], []
    for edge in graph_data["edges"]:
        if edge["source"] in pos and edge["target"] in pos:
            x0, y0 = pos[edge["source"]]
            x1, y1 = pos[edge["target"]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color="#888"),
        hoverinfo="none",
        mode="lines",
    )

    node_x, node_y, node_text, node_color, node_size = [], [], [], [], []
    type_colors = {
        "supplier": "#3b82f6",
        "port": "#06b6d4",
        "plant": "#8b5cf6",
        "warehouse": "#f59e0b",
        "market": "#10b981",
        "transport_route": "#6b7280",
        "material": "#ec4899",
        "product": "#14b8a6",
        "labor_pool": "#f97316",
    }

    for node in graph_data["nodes"]:
        if node["id"] in pos:
            x, y = pos[node["id"]]
            node_x.append(x)
            node_y.append(y)
            node_text.append(f"{node['name']}<br>Type: {node['type']}<br>Risk: {node['risk']:.2f}")
            node_color.append(type_colors.get(node["type"], "#666"))
            node_size.append(15 + node["criticality"] * 20 + node["risk"] * 15)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        hoverinfo="text",
        text=[n["name"][:15] for n in graph_data["nodes"] if n["id"] in pos],
        textposition="top center",
        textfont=dict(size=8),
        hovertext=node_text,
        marker=dict(
            size=node_size,
            color=node_color,
            line=dict(width=2, color="white"),
        ),
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        showlegend=False,
        hovermode="closest",
        margin=dict(b=0, l=0, r=0, t=0),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Legend
    st.markdown("**Node Types:** 🔵 Supplier | 🔷 Port | 🟣 Plant | 🟡 Warehouse | 🟢 Market")


def render_signal_timeline(signals: list[Signal]):
    """Render signals on a timeline by category."""
    if not signals:
        return

    categories = [s.category.value for s in signals]
    severities = [s.severity.value for s in signals]
    titles = [s.title[:40] for s in signals]
    confidences = [s.confidence for s in signals]

    fig = px.scatter(
        x=categories,
        y=confidences,
        color=severities,
        size=[40] * len(signals),
        hover_name=titles,
        color_discrete_map=SEVERITY_COLORS,
        labels={"x": "Category", "y": "Confidence", "color": "Severity"},
    )
    fig.update_layout(height=300, margin=dict(t=20, b=40))
    st.plotly_chart(fig, use_container_width=True)
