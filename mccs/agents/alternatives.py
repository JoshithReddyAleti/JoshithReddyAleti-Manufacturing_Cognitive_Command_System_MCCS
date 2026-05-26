"""Alternatives Agent - Finds alternative paths when disruptions are detected.

When a disruption blocks a route, supplier, or resource, this agent
finds alternative ways to achieve the same outcome.

Examples:
- China tariff on chips → suggests Taiwan, South Korea, US fabs
- Strait of Hormuz closed → suggests Cape of Good Hope, pipelines
- Supplier shutdown → suggests qualified alternates with lead times
- Port congested → suggests alternate ports + inland routes
"""

import uuid
from dataclasses import dataclass
from mccs.models.signals import Signal, SeverityLevel, SignalCategory


@dataclass
class Alternative:
    """A single alternative option."""
    id: str
    title: str
    description: str
    category: str  # route, supplier, port, method, policy
    feasibility_score: float  # 0-1
    cost_impact_pct: float  # % cost increase
    time_impact_days: float  # additional days
    risk_reduction_pct: float  # how much risk it reduces
    proof_link: str  # source of truth
    trade_offs: list  # what you give up


# Knowledge base of alternatives for common disruptions
ALTERNATIVE_KNOWLEDGE = {
    "semiconductor": {
        "supply_alternatives": [
            Alternative(
                id="alt-semi-1", title="TSMC Arizona Fab (US)",
                description="TSMC's $40B Arizona fab can produce 4nm chips. Reduces Taiwan dependency.",
                category="supplier", feasibility_score=0.7, cost_impact_pct=15,
                time_impact_days=30, risk_reduction_pct=60,
                proof_link="https://www.tsmc.com/english/dedicatedFoundry/manufacturing/fab_list",
                trade_offs=["Higher cost per wafer", "Limited capacity initially", "Ramp-up takes 6-12 months"],
            ),
            Alternative(
                id="alt-semi-2", title="Samsung Foundry (South Korea)",
                description="Samsung's 3nm GAA process as alternative to TSMC for advanced nodes.",
                category="supplier", feasibility_score=0.8, cost_impact_pct=10,
                time_impact_days=14, risk_reduction_pct=50,
                proof_link="https://semiconductor.samsung.com/foundry/",
                trade_offs=["Different process design rules", "Yield differences", "Qualification time"],
            ),
            Alternative(
                id="alt-semi-3", title="Intel Foundry Services (US/EU)",
                description="Intel IFS offers 18A process. US/EU based, avoids Asia geopolitical risk.",
                category="supplier", feasibility_score=0.6, cost_impact_pct=20,
                time_impact_days=45, risk_reduction_pct=70,
                proof_link="https://www.intel.com/content/www/us/en/foundry/overview.html",
                trade_offs=["New process qualification", "Higher initial cost", "Capacity constraints"],
            ),
            Alternative(
                id="alt-semi-4", title="Mature Node Diversification (GlobalFoundries, UMC)",
                description="For non-cutting-edge chips, use GlobalFoundries (US/EU) or UMC (Taiwan/Singapore).",
                category="supplier", feasibility_score=0.9, cost_impact_pct=5,
                time_impact_days=7, risk_reduction_pct=40,
                proof_link="https://gf.com/manufacturing/",
                trade_offs=["Only for 12nm+ nodes", "Limited advanced packaging"],
            ),
        ],
        "route_alternatives": [
            Alternative(
                id="alt-route-1", title="Air freight for critical chips",
                description="Airfreight semiconductor wafers/dies instead of ocean shipping. 2 days vs 14 days.",
                category="route", feasibility_score=0.95, cost_impact_pct=300,
                time_impact_days=-12, risk_reduction_pct=80,
                proof_link="https://www.iata.org/en/programs/cargo/",
                trade_offs=["10-30x shipping cost increase", "Weight/volume limits", "Only viable for high-value chips"],
            ),
            Alternative(
                id="alt-route-2", title="Trans-Pacific via Japan/Korea hub",
                description="Route through Busan or Yokohama instead of Shanghai if China ports disrupted.",
                category="route", feasibility_score=0.8, cost_impact_pct=25,
                time_impact_days=3, risk_reduction_pct=50,
                proof_link="https://www.portofbusan.com/",
                trade_offs=["Longer transit", "Transshipment delays", "Capacity constraints"],
            ),
        ],
        "policy_alternatives": [
            Alternative(
                id="alt-policy-1", title="CHIPS Act funding acceleration",
                description="Leverage US CHIPS Act $52B to accelerate domestic fab construction.",
                category="policy", feasibility_score=0.6, cost_impact_pct=0,
                time_impact_days=365, risk_reduction_pct=40,
                proof_link="https://www.nist.gov/chips",
                trade_offs=["Long timeline (2-4 years)", "Requires government coordination", "Limited near-term impact"],
            ),
        ],
    },
    "automotive": {
        "supply_alternatives": [
            Alternative(
                id="alt-auto-1", title="Mexico nearshoring (auto parts)",
                description="Shift auto parts sourcing from China to Mexico. USMCA tariff benefits.",
                category="supplier", feasibility_score=0.85, cost_impact_pct=8,
                time_impact_days=-5, risk_reduction_pct=45,
                proof_link="https://ustr.gov/trade-agreements/free-trade-agreements/united-states-mexico-canada-agreement",
                trade_offs=["Qualification time", "Different quality standards", "Infrastructure gaps"],
            ),
            Alternative(
                id="alt-auto-2", title="India EV battery manufacturing",
                description="India's PLI scheme for battery manufacturing as alternative to China.",
                category="supplier", feasibility_score=0.6, cost_impact_pct=12,
                time_impact_days=21, risk_reduction_pct=35,
                proof_link="https://www.makeinindia.com/",
                trade_offs=["Nascent ecosystem", "Scale limitations", "Logistics complexity"],
            ),
        ],
        "route_alternatives": [
            Alternative(
                id="alt-auto-route-1", title="Rail from Mexico (vs ocean from Asia)",
                description="Use rail corridors from Monterrey/Saltillo to US plants. 2 days vs 14 days ocean.",
                category="route", feasibility_score=0.9, cost_impact_pct=-10,
                time_impact_days=-12, risk_reduction_pct=60,
                proof_link="https://www.bnsf.com/",
                trade_offs=["Requires Mexico-based suppliers", "Rail capacity limits", "Border crossing delays"],
            ),
        ],
    },
    "pharmaceutical": {
        "supply_alternatives": [
            Alternative(
                id="alt-pharma-1", title="Diversify API sourcing from India",
                description="India produces 60% of global APIs. Diversify to EU/US for critical drugs.",
                category="supplier", feasibility_score=0.7, cost_impact_pct=40,
                time_impact_days=60, risk_reduction_pct=55,
                proof_link="https://www.ema.europa.eu/en/human-regulatory-overview/research-and-development/compliance-research-and-development/good-manufacturing-practice",
                trade_offs=["Significantly higher cost", "FDA/EMA requalification", "18-24 month timeline"],
            ),
            Alternative(
                id="alt-pharma-2", title="Continuous manufacturing (vs batch)",
                description="Switch to continuous manufacturing to reduce dependency on large batch facilities.",
                category="method", feasibility_score=0.5, cost_impact_pct=25,
                time_impact_days=180, risk_reduction_pct=30,
                proof_link="https://www.fda.gov/drugs/pharmaceutical-quality-resources/continuous-manufacturing",
                trade_offs=["Major capital investment", "Regulatory approval needed", "Technical complexity"],
            ),
        ],
    },
    "aerospace": {
        "supply_alternatives": [
            Alternative(
                id="alt-aero-1", title="Dual-source titanium (VSMPO-AVISMA alternatives)",
                description="Reduce dependency on Russian titanium. Source from US (Timet), Japan (Toho), or Kazakhstan.",
                category="supplier", feasibility_score=0.75, cost_impact_pct=20,
                time_impact_days=90, risk_reduction_pct=60,
                proof_link="https://www.boeing.com/company/about-bca/supply-chain",
                trade_offs=["Higher cost", "Qualification takes 12-18 months", "Limited capacity outside Russia"],
            ),
            Alternative(
                id="alt-aero-2", title="Additive manufacturing for complex parts",
                description="3D print titanium/nickel alloy parts instead of traditional forging. Reduces supply chain dependency.",
                category="method", feasibility_score=0.6, cost_impact_pct=30,
                time_impact_days=-30, risk_reduction_pct=40,
                proof_link="https://www.ge.com/additive/additive-manufacturing",
                trade_offs=["FAA certification required", "Limited to certain part geometries", "Higher per-unit cost"],
            ),
            Alternative(
                id="alt-aero-3", title="Spirit AeroSystems alternatives (fuselage)",
                description="Qualify alternative fuselage suppliers or bring production in-house (Boeing/Airbus).",
                category="supplier", feasibility_score=0.5, cost_impact_pct=35,
                time_impact_days=180, risk_reduction_pct=50,
                proof_link="https://www.airbus.com/en/our-worldwide-presence",
                trade_offs=["Massive capital investment", "2-3 year timeline", "Regulatory re-certification"],
            ),
        ],
        "route_alternatives": [
            Alternative(
                id="alt-aero-route-1", title="Air freight for critical aerospace components",
                description="Use dedicated air cargo for time-critical engine/avionics parts.",
                category="route", feasibility_score=0.9, cost_impact_pct=200,
                time_impact_days=-10, risk_reduction_pct=70,
                proof_link="https://www.iata.org/en/programs/cargo/",
                trade_offs=["Very high cost", "Weight limits", "Only for high-value components"],
            ),
        ],
    },
    "energy": {
        "route_alternatives": [
            Alternative(
                id="alt-energy-1", title="Cape of Good Hope (bypass Hormuz/Suez)",
                description="Route oil tankers around Africa if Strait of Hormuz or Suez Canal blocked.",
                category="route", feasibility_score=0.95, cost_impact_pct=30,
                time_impact_days=14, risk_reduction_pct=90,
                proof_link="https://www.eia.gov/todayinenergy/detail.php?id=39932",
                trade_offs=["14 extra days transit", "30% higher shipping cost", "Insurance premium increase"],
            ),
            Alternative(
                id="alt-energy-2", title="Strategic Petroleum Reserve release",
                description="US SPR holds 400M+ barrels. Can release 1M bbl/day for 400 days.",
                category="policy", feasibility_score=0.9, cost_impact_pct=0,
                time_impact_days=3, risk_reduction_pct=40,
                proof_link="https://www.energy.gov/ceser/strategic-petroleum-reserve",
                trade_offs=["Temporary measure only", "Political decision required", "Depletes reserves"],
            ),
            Alternative(
                id="alt-energy-3", title="Pipeline alternatives (Druzhba, TAPI)",
                description="Use overland pipelines instead of maritime routes for oil/gas.",
                category="route", feasibility_score=0.6, cost_impact_pct=15,
                time_impact_days=-7, risk_reduction_pct=50,
                proof_link="https://www.eia.gov/international/analysis/special-topics/World_Oil_Transit_Chokepoints",
                trade_offs=["Geopolitical dependencies", "Capacity limits", "Not all destinations served"],
            ),
        ],
    },
    "logistics": {
        "route_alternatives": [
            Alternative(
                id="alt-log-1", title="Suez blocked → Cape of Good Hope",
                description="Reroute Asia-Europe shipping around Africa. Adds 10-14 days but avoids Suez.",
                category="route", feasibility_score=0.95, cost_impact_pct=25,
                time_impact_days=12, risk_reduction_pct=95,
                proof_link="https://www.marinetraffic.com/",
                trade_offs=["12-14 extra days", "Higher fuel cost", "Insurance increase"],
            ),
            Alternative(
                id="alt-log-2", title="China-Europe rail (Belt & Road)",
                description="Use China-Europe rail freight via Kazakhstan/Russia. 18 days vs 35 days ocean.",
                category="route", feasibility_score=0.7, cost_impact_pct=50,
                time_impact_days=-17, risk_reduction_pct=60,
                proof_link="https://www.railfreight.com/corridors/china-europe/",
                trade_offs=["Higher cost than ocean", "Russia transit risk", "Weight/volume limits"],
            ),
        ],
    },
}


class AlternativesAgent:
    """Finds alternative paths when disruptions are detected.
    
    This agent activates when signals indicate a disruption and
    provides concrete alternatives with:
    - Feasibility scores
    - Cost/time trade-offs
    - Source-of-truth links
    - Risk reduction estimates
    """

    def __init__(self):
        self.knowledge = ALTERNATIVE_KNOWLEDGE

    def find_alternatives(self, signals: list[Signal], industry: str = "") -> dict:
        """Find alternatives based on detected disruptions and industry.
        
        Returns categorized alternatives with trade-offs and proof links.
        """
        if not signals:
            return {"status": "no_disruptions", "alternatives": [], "message": "No disruptions detected — no alternatives needed."}

        alternatives = []
        
        # Get industry-specific alternatives
        industry_alts = self.knowledge.get(industry, self.knowledge.get("logistics", {}))
        
        # Match signals to relevant alternatives
        for signal in signals:
            matched = self._match_alternatives(signal, industry_alts, industry)
            alternatives.extend(matched)

        # Deduplicate
        seen_ids = set()
        unique_alts = []
        for alt in alternatives:
            if alt["id"] not in seen_ids:
                seen_ids.add(alt["id"])
                unique_alts.append(alt)

        # Sort by feasibility
        unique_alts.sort(key=lambda x: x["feasibility_score"], reverse=True)

        return {
            "status": "alternatives_found" if unique_alts else "no_matching_alternatives",
            "total_alternatives": len(unique_alts),
            "disruptions_addressed": len(signals),
            "alternatives": unique_alts,
            "industry": industry or "general",
            "summary": self._generate_summary(unique_alts, signals),
        }

    def _match_alternatives(self, signal: Signal, industry_alts: dict, industry: str) -> list[dict]:
        """Match a signal to relevant alternatives."""
        matched = []
        
        # Check all categories of alternatives
        for category_key in ["supply_alternatives", "route_alternatives", "policy_alternatives"]:
            alts = industry_alts.get(category_key, [])
            for alt in alts:
                # Simple relevance matching based on signal content
                relevance = self._calculate_relevance(signal, alt)
                if relevance > 0.3:
                    matched.append({
                        "id": alt.id,
                        "title": alt.title,
                        "description": alt.description,
                        "category": alt.category,
                        "feasibility_score": alt.feasibility_score,
                        "cost_impact_pct": alt.cost_impact_pct,
                        "time_impact_days": alt.time_impact_days,
                        "risk_reduction_pct": alt.risk_reduction_pct,
                        "proof_link": alt.proof_link,
                        "trade_offs": alt.trade_offs,
                        "triggered_by": signal.title,
                        "relevance": round(relevance, 2),
                    })

        # If no industry-specific match, provide generic logistics alternatives
        if not matched and signal.category in (SignalCategory.LOGISTICS, SignalCategory.GEOPOLITICAL):
            for alt in self.knowledge.get("logistics", {}).get("route_alternatives", []):
                matched.append({
                    "id": alt.id,
                    "title": alt.title,
                    "description": alt.description,
                    "category": alt.category,
                    "feasibility_score": alt.feasibility_score,
                    "cost_impact_pct": alt.cost_impact_pct,
                    "time_impact_days": alt.time_impact_days,
                    "risk_reduction_pct": alt.risk_reduction_pct,
                    "proof_link": alt.proof_link,
                    "trade_offs": alt.trade_offs,
                    "triggered_by": signal.title,
                    "relevance": 0.5,
                })

        return matched

    def _calculate_relevance(self, signal: Signal, alt: Alternative) -> float:
        """Calculate how relevant an alternative is to a signal."""
        score = 0.0
        signal_text = f"{signal.title} {signal.description}".lower()
        alt_text = f"{alt.title} {alt.description}".lower()

        # Keyword overlap
        signal_words = set(signal_text.split())
        alt_words = set(alt_text.split())
        overlap = len(signal_words & alt_words)
        score += min(overlap * 0.1, 0.5)

        # Category matching
        if signal.category == SignalCategory.TRADE and alt.category in ("supplier", "policy"):
            score += 0.3
        if signal.category == SignalCategory.LOGISTICS and alt.category == "route":
            score += 0.4
        if signal.category == SignalCategory.GEOPOLITICAL and alt.category in ("supplier", "route"):
            score += 0.3
        if signal.category == SignalCategory.ECONOMIC and alt.category in ("supplier", "method"):
            score += 0.2

        # Severity boost
        if signal.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL):
            score += 0.2

        return min(score, 1.0)

    def _generate_summary(self, alternatives: list[dict], signals: list[Signal]) -> str:
        """Generate a human-readable summary of alternatives."""
        if not alternatives:
            return "No specific alternatives identified for current disruptions."
        
        best = alternatives[0]
        return (
            f"Found {len(alternatives)} alternative(s) for {len(signals)} disruption(s). "
            f"Best option: '{best['title']}' — {best['risk_reduction_pct']}% risk reduction, "
            f"{best['feasibility_score']:.0%} feasibility, "
            f"{'+' if best['cost_impact_pct'] > 0 else ''}{best['cost_impact_pct']}% cost impact."
        )
