"use client";

import { useState } from "react";

const API_URL = "http://localhost:8000";

// Simple markdown to HTML converter (handles **bold** and bullet points)
function renderMarkdown(text: string): string {
  if (!text) return "";
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-white">$1</strong>')
    .replace(/^  • /gm, '<span class="text-blue-400 mr-1">→</span>')
    .replace(/\n/g, "<br/>");
}

// Available industries for selection
const INDUSTRIES = [
  { id: "semiconductor", name: "Semiconductor & Chips", keywords: "semiconductor chip fab wafer TSMC Intel AMD NVIDIA" },
  { id: "automotive", name: "Automotive & EV", keywords: "automotive car EV electric vehicle battery Tesla Ford GM" },
  { id: "pharmaceutical", name: "Pharmaceutical & Biotech", keywords: "pharmaceutical drug API biotech vaccine medicine" },
  { id: "medical_devices", name: "Medical Devices", keywords: "medical device implant surgical diagnostic MRI" },
  { id: "aerospace", name: "Aerospace & Defense", keywords: "aerospace defense aircraft Boeing Airbus titanium" },
  { id: "electronics", name: "Consumer Electronics", keywords: "electronics smartphone laptop display Apple Samsung" },
  { id: "chemicals", name: "Chemicals & Materials", keywords: "chemical polymer resin BASF DuPont petrochemical" },
  { id: "steel_metals", name: "Steel & Metals", keywords: "steel aluminum copper metal mining ore smelting" },
  { id: "textiles", name: "Textiles & Apparel", keywords: "textile apparel clothing fabric cotton shoe footwear" },
  { id: "food_beverage", name: "Food & Beverage", keywords: "food beverage agriculture grain processing packaging" },
  { id: "energy", name: "Energy & Renewables", keywords: "energy solar wind turbine oil gas refinery battery" },
  { id: "construction", name: "Construction & Building", keywords: "construction building cement concrete door window HVAC" },
];

const COUNTRIES = [
  { id: "US", name: "United States" }, { id: "CN", name: "China" }, { id: "TW", name: "Taiwan" },
  { id: "DE", name: "Germany" }, { id: "JP", name: "Japan" }, { id: "KR", name: "South Korea" },
  { id: "IN", name: "India" }, { id: "MX", name: "Mexico" }, { id: "VN", name: "Vietnam" },
  { id: "TH", name: "Thailand" }, { id: "MY", name: "Malaysia" }, { id: "GB", name: "United Kingdom" },
  { id: "FR", name: "France" }, { id: "IT", name: "Italy" }, { id: "BR", name: "Brazil" },
  { id: "SA", name: "Saudi Arabia" }, { id: "AE", name: "UAE" }, { id: "SG", name: "Singapore" },
];

interface Signal {
  id: string;
  severity: string;
  title: string;
  description: string;
  source: string;
  location: string;
  confidence: number;
  affected_entities: string[];
  proof_link: string;
}

interface Scenario {
  id: string;
  name: string;
  probability: number;
  revenue_at_risk: number;
  explanation: string;
  recommended_actions: string[];
}

interface Recommendation {
  id: string;
  title: string;
  description: string;
  urgency: string;
  cost_usd: number;
  savings_usd: number;
  roi_pct: number;
  explanation: string;
  requires_approval: boolean;
}

interface AnalysisData {
  timestamp: string;
  data_sources: Record<string, { name: string; url: string; status: string }>;
  ai_engine: { provider: string; model: string; url: string };
  signal_intelligence: { agent_id: string; agent_name: string; role: string; total_signals: number; signals: Signal[] };
  causal_graph: { layer_id: string; layer_name: string; role: string; stats: any; nodes: any[]; edges: any[] };
  risk_propagation: { layer_id: string; layer_name: string; role: string; logic: string[]; reports: any[] };
  simulation: { layer_id: string; layer_name: string; role: string; total_scenarios: number; scenarios: Scenario[] };
  supply_chain: { agent_id: string; agent_name: string; role: string; [key: string]: any };
  production_rebalancing: { agent_id: string; agent_name: string; role: string; [key: string]: any };
  financial_impact: { agent_id: string; agent_name: string; role: string; [key: string]: any };
  policy_safety: { agent_id: string; agent_name: string; role: string; [key: string]: any };
  executive_explanation: { agent_id: string; agent_name: string; role: string; [key: string]: any };
  recommendations: Recommendation[];
  auto_triggers: any;
  alternatives: { agent_name: string; role: string; summary: string; alternatives: any[]; [key: string]: any };
  email_summary: { to: string; subject: string; body_text: string; body_html: string; [key: string]: any };
}

const severityColor: Record<string, string> = {
  critical: "bg-red-600",
  high: "bg-orange-500",
  medium: "bg-yellow-500",
  low: "bg-green-500",
};

const severityBorder: Record<string, string> = {
  critical: "border-red-600",
  high: "border-orange-500",
  medium: "border-yellow-500",
  low: "border-green-500",
};

export default function Home() {
  const [data, setData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [chatMsg, setChatMsg] = useState("");
  const [chatHistory, setChatHistory] = useState<{ role: string; content: string }[]>([]);
  const [selectedIndustry, setSelectedIndustry] = useState("");
  const [selectedCountries, setSelectedCountries] = useState<string[]>(["US", "CN", "TW"]);

  const runAnalysis = async () => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (selectedIndustry) params.set("industry", selectedIndustry);
      if (selectedCountries.length > 0) params.set("countries", selectedCountries.join(","));
      const res = await fetch(`${API_URL}/api/analyze?${params.toString()}`);
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const json = await res.json();
      setData(json);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const sendChat = async () => {
    if (!chatMsg.trim()) return;
    const userMsg = chatMsg;
    setChatMsg("");
    setChatHistory((h) => [...h, { role: "user", content: userMsg }]);
    try {
      const res = await fetch(`${API_URL}/api/chat?message=${encodeURIComponent(userMsg)}`);
      const json = await res.json();
      setChatHistory((h) => [...h, { role: "assistant", content: json.response }]);
    } catch {
      setChatHistory((h) => [...h, { role: "assistant", content: "Error connecting to AI." }]);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="bg-gradient-to-r from-slate-900 to-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">🏭 MCCS</h1>
            <p className="text-slate-400 text-sm">Manufacturing Cognitive Command System — Real-time Disruption Intelligence</p>
          </div>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1 text-xs bg-green-900 text-green-300 px-2 py-1 rounded-full">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span> LIVE DATA
            </span>
            <button
              onClick={runAnalysis}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 px-4 py-2 rounded-lg font-medium text-sm transition"
            >
              {loading ? "⏳ Analyzing..." : "🚀 Run Full Analysis"}
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-6">
        {error && <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 mb-4 text-red-200">{error}</div>}

        {/* Industry & Country Selection */}
        <section className="bg-slate-900 border border-slate-700 rounded-xl p-6 mb-6">
          <h3 className="font-bold mb-3">🎯 Select Industry & Countries to Monitor</h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="text-sm text-slate-400 block mb-2">Manufacturing Industry</label>
              <select
                value={selectedIndustry}
                onChange={(e) => setSelectedIndustry(e.target.value)}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="">All Industries (General)</option>
                {INDUSTRIES.map((ind) => (
                  <option key={ind.id} value={ind.id}>{ind.name}</option>
                ))}
              </select>
              {selectedIndustry && (
                <p className="text-xs text-slate-500 mt-1">
                  Agents will focus on: {INDUSTRIES.find(i => i.id === selectedIndustry)?.keywords.split(" ").slice(0, 5).join(", ")}...
                </p>
              )}
            </div>
            <div>
              <label className="text-sm text-slate-400 block mb-2">Countries to Monitor</label>
              <div className="flex flex-wrap gap-2">
                {COUNTRIES.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => setSelectedCountries((prev) =>
                      prev.includes(c.id) ? prev.filter((x) => x !== c.id) : [...prev, c.id]
                    )}
                    className={`text-xs px-2 py-1 rounded-full border transition ${
                      selectedCountries.includes(c.id)
                        ? "bg-blue-600 border-blue-500 text-white"
                        : "bg-slate-800 border-slate-600 text-slate-400 hover:border-slate-500"
                    }`}
                  >
                    {c.name}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <div className="mt-4 flex items-center gap-4">
            <button
              onClick={runAnalysis}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 px-6 py-2 rounded-lg font-medium text-sm transition"
            >
              {loading ? "⏳ Analyzing..." : `🚀 Run Analysis${selectedIndustry ? ` for ${INDUSTRIES.find(i => i.id === selectedIndustry)?.name}` : ""}`}
            </button>
            {selectedIndustry && (
              <span className="text-xs text-slate-400">
                Monitoring {selectedCountries.length} countries for {INDUSTRIES.find(i => i.id === selectedIndustry)?.name}
              </span>
            )}
          </div>
        </section>

        {!data && !loading && (
          <div className="text-center py-20">
            <p className="text-4xl mb-4">🏭</p>
            <h2 className="text-xl font-semibold mb-2">Manufacturing Cognitive Command System</h2>
            <p className="text-slate-400 mb-6 max-w-lg mx-auto">
              Click &quot;Run Full Analysis&quot; to collect real-time data from 7 MCP servers,
              propagate through the causal graph, simulate scenarios, and generate recommendations.
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 max-w-2xl mx-auto text-xs">
              {[
                { icon: "🌡️", name: "OpenWeather", url: "https://openweathermap.org" },
                { icon: "📈", name: "FRED", url: "https://fred.stlouisfed.org" },
                { icon: "🌍", name: "GDELT", url: "https://gdeltproject.org" },
                { icon: "📊", name: "Finnhub", url: "https://finnhub.io" },
                { icon: "👷", name: "BLS", url: "https://www.bls.gov" },
                { icon: "🚢", name: "Logistics", url: "https://gdeltproject.org" },
                { icon: "🤖", name: "Gemini AI", url: "https://ai.google.dev" },
                { icon: "🔗", name: "NetworkX", url: "https://networkx.org" },
              ].map((s) => (
                <a key={s.name} href={s.url} target="_blank" className="bg-slate-800 border border-slate-700 rounded-lg p-3 hover:border-blue-500 transition">
                  <span className="text-lg">{s.icon}</span>
                  <p className="text-slate-300 mt-1">{s.name}</p>
                </a>
              ))}
            </div>
          </div>
        )}

        {loading && (
          <div className="py-10">
            <div className="max-w-3xl mx-auto">
              <div className="text-center mb-8">
                <h3 className="text-xl font-bold">🔄 Intelligence Pipeline Active</h3>
                <p className="text-slate-400 text-sm mt-1">
                  Analyzing {selectedIndustry ? INDUSTRIES.find(i => i.id === selectedIndustry)?.name : "all manufacturing"} in real-time
                </p>
              </div>

              {/* Architecture diagram */}
              <div className="bg-slate-800 rounded-xl p-6 mb-6 border border-slate-700">
                <p className="text-xs text-slate-500 text-center mb-4">MCCS ARCHITECTURE — LIVE EXECUTION</p>
                <div className="flex flex-col items-center gap-2 text-sm">
                  <div className="bg-blue-900/50 border border-blue-700 rounded-lg px-4 py-2 w-full max-w-md text-center animate-pulse">
                    📡 <strong>MCP Data Layer</strong> — Collecting from 7 live APIs
                  </div>
                  <div className="text-slate-500">↓</div>
                  <div className="bg-purple-900/50 border border-purple-700 rounded-lg px-4 py-2 w-full max-w-md text-center animate-pulse" style={{animationDelay: "0.5s"}}>
                    🧠 <strong>Cognitive Layer</strong> — Causal graph + Risk propagation + Simulation
                  </div>
                  <div className="text-slate-500">↓</div>
                  <div className="bg-green-900/50 border border-green-700 rounded-lg px-4 py-2 w-full max-w-md text-center animate-pulse" style={{animationDelay: "1s"}}>
                    🤖 <strong>Agentic Layer</strong> — 7 specialized agents reasoning in parallel
                  </div>
                  <div className="text-slate-500">↓</div>
                  <div className="bg-yellow-900/50 border border-yellow-700 rounded-lg px-4 py-2 w-full max-w-md text-center animate-pulse" style={{animationDelay: "1.5s"}}>
                    💡 <strong>Decision Layer</strong> — Recommendations + Alternatives + Explanation
                  </div>
                </div>
              </div>

              {/* Step details */}
              <div className="grid md:grid-cols-2 gap-3">
                {[
                  { icon: "📊", step: "Finnhub", desc: `Fetching ${selectedIndustry ? INDUSTRIES.find(i => i.id === selectedIndustry)?.name : "sector"} stock prices`, status: "Querying tickers..." },
                  { icon: "🌡️", step: "OpenWeather", desc: "Checking weather at manufacturing hubs", status: "Scanning locations..." },
                  { icon: "🌍", step: "GDELT", desc: "Scanning geopolitical event database", status: "Analyzing news volume..." },
                  { icon: "📈", step: "FRED", desc: "Pulling Federal Reserve economic data", status: "Reading indicators..." },
                  { icon: "👷", step: "BLS", desc: "Checking labor market conditions", status: "Fetching employment data..." },
                  { icon: "🚢", step: "Logistics", desc: "Monitoring shipping chokepoints", status: "Checking routes..." },
                  { icon: "🧠", step: "Causal Graph", desc: "Propagating risk through 17-node DAG", status: "BFS with decay..." },
                  { icon: "🎲", step: "Monte Carlo", desc: "Simulating 8 counterfactual futures", status: "Running scenarios..." },
                  { icon: "🔄", step: "Alternatives", desc: "Finding backup routes & suppliers", status: "Matching disruptions..." },
                  { icon: "🤖", step: "Gemini AI", desc: "Generating executive narrative", status: "Reasoning..." },
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-3 bg-slate-800/50 border border-slate-700/50 rounded-lg p-3" style={{ animation: `fadeSlideIn 0.3s ease-out ${i * 0.15}s both` }}>
                    <span className="text-xl">{item.icon}</span>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-xs text-slate-200">{item.step}</p>
                      <p className="text-xs text-slate-500 truncate">{item.desc}</p>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Fun facts while waiting */}
              <div className="mt-6 bg-gradient-to-r from-slate-800 to-slate-900 rounded-lg p-4 border border-slate-700">
                <p className="text-xs text-blue-400 font-medium mb-1">💡 Did you know?</p>
                <p className="text-xs text-slate-400">
                  {[
                    "MCCS uses a Directed Acyclic Graph (DAG) with 17 nodes representing your supply chain. Risk propagates through edges with time-lag and confidence decay.",
                    "The Monte Carlo engine simulates 8+ counterfactual futures — base case, escalation, compound disruption, cascading failure, and stochastic variations.",
                    "Each MCP server is stateless and testable. They wrap real APIs (OpenWeather, FRED, GDELT, Finnhub, BLS) into clean tool interfaces for agents to consume.",
                    "The Alternatives Agent has a knowledge base of real supplier alternatives, shipping routes, and policy options — each with feasibility scores and proof links.",
                    "Risk propagation uses historical lag assumptions: Supplier→Port takes 1-7 days, Port→Plant takes 2-14 days, with confidence decay of 15% per hop.",
                    "The Policy & Safety Agent enforces guardrails: max risk tolerance, ethical sourcing (banned countries), regulatory limits, and cost thresholds.",
                  ][Math.floor(Date.now() / 5000) % 6]}
                </p>
              </div>
            </div>
            <style>{`
              @keyframes fadeSlideIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
              }
            `}</style>
          </div>
        )}

        {data && (
          <div className="space-y-6">
            {/* Executive Summary */}
            <section className="bg-slate-900 border border-slate-700 rounded-xl p-6">
              <h2 className="text-lg font-bold mb-2">{data.executive_explanation.headline}</h2>
              <p className="text-slate-300">{data.executive_explanation.situation_summary}</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                <Metric label="Signals" value={data.signal_intelligence.total_signals.toString()} />
                <Metric label="Scenarios" value={data.simulation.total_scenarios.toString()} />
                <Metric label="Expected Loss" value={`$${(data.financial_impact.expected_loss_usd || 0).toLocaleString()}`} />
                <Metric label="Recommendations" value={data.recommendations.length.toString()} />
              </div>
              <p className="text-xs text-slate-500 mt-4">
                Data: {Object.values(data.data_sources).map((s) => s.name).join(", ")} | AI: {data.ai_engine.provider} ({data.ai_engine.model})
              </p>
            </section>

            {/* Agent 8.1: Signal Intelligence */}
            <AgentSection id="8.1" name="Signal Intelligence Agent" role="Polls 7 MCP servers, normalizes signals, flags anomalies">
              {data.signal_intelligence.signals.length === 0 ? (
                <p className="text-green-400">✅ No disruption signals detected. All systems nominal.</p>
              ) : (
                <div className="space-y-3">
                  {data.signal_intelligence.signals.map((s) => (
                    <div key={s.id} className={`border-l-4 ${severityBorder[s.severity]} bg-slate-800 rounded-r-lg p-4`}>
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`${severityColor[s.severity]} text-white text-xs px-2 py-0.5 rounded-full uppercase font-bold`}>{s.severity}</span>
                        <span className="font-semibold">{s.title}</span>
                      </div>
                      <p className="text-slate-300 text-sm">{s.description}</p>
                      <div className="flex gap-4 mt-2 text-xs text-slate-400">
                        <span>Source: {s.source}</span>
                        <span>Location: {s.location || "Global"}</span>
                        <span>Confidence: {(s.confidence * 100).toFixed(0)}%</span>
                        {s.proof_link && <a href={s.proof_link} target="_blank" className="text-blue-400 hover:underline">🔗 Source proof</a>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <div className="mt-3 text-xs text-slate-500">
                Sources: {Object.entries(data.data_sources).map(([k, v]) => (
                  <a key={k} href={v.url} target="_blank" className="text-blue-400 hover:underline mr-2">{v.name}</a>
                ))}
              </div>
            </AgentSection>

            {/* Cognitive Layer 7.1 + 7.2: Causal Graph & Risk Propagation */}
            <AgentSection id="7.1+7.2" name="Causal Graph + Risk Propagation" role="Answers: If this happens here, what breaks next — and when?">
              <div className="grid md:grid-cols-3 gap-3 mb-4">
                <Metric label="Nodes" value={data.causal_graph.stats.total_nodes} />
                <Metric label="Edges" value={data.causal_graph.stats.total_edges} />
                <Metric label="DAG Valid" value={data.causal_graph.stats.is_dag ? "✅" : "❌"} />
              </div>
              <p className="text-sm text-slate-400 mb-3">Logic: {data.risk_propagation.logic.join(" → ")}</p>
              {data.risk_propagation.reports.map((r, i) => (
                <div key={i} className="bg-slate-800 rounded-lg p-4 mb-3">
                  <h4 className="font-semibold text-sm mb-2">
                    Disruption at: {r.origin} (severity: {(r.initial_risk * 100).toFixed(0)}%)
                    {r.trigger && <span className="text-slate-400 ml-2">← {r.trigger}</span>}
                  </h4>
                  <div className="whitespace-pre-wrap text-sm text-slate-300 mb-3" dangerouslySetInnerHTML={{ __html: renderMarkdown(r.narrative) }}></div>
                  {r.steps.length > 0 && (
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead className="text-slate-400">
                          <tr><th className="text-left p-1">From → To</th><th>Delay</th><th>Risk</th><th>Confidence</th><th>Buffer</th><th>Recovery</th></tr>
                        </thead>
                        <tbody>
                          {r.steps.map((step: any, j: number) => (
                            <tr key={j} className="border-t border-slate-700">
                              <td className="p-1">{step.from} → {step.to}</td>
                              <td className="text-center">{step.delay_range}</td>
                              <td className="text-center">{step.risk_range}</td>
                              <td className="text-center">{(step.confidence * 100).toFixed(0)}%</td>
                              <td className="text-center">{step.buffer_days}d</td>
                              <td className="text-center">~{step.recovery_days.toFixed(0)}d</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ))}
            </AgentSection>

            {/* Cognitive Layer 7.3: Simulation */}
            <AgentSection id="7.3" name="Counterfactual Simulation Engine" role="Simulates futures, not predict one. Monte Carlo + OR-Tools constraints.">
              <div className="space-y-3">
                {data.simulation.scenarios.map((s) => (
                  <div key={s.id} className="bg-slate-800 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <h4 className="font-semibold text-sm">{s.name}</h4>
                      <div className="text-right text-xs">
                        <span className="text-yellow-400">{(s.probability * 100).toFixed(0)}% probability</span>
                        <br />
                        <span className="text-red-400">${s.revenue_at_risk.toLocaleString()} at risk</span>
                      </div>
                    </div>
                    <p className="text-slate-300 text-sm mt-2">{s.explanation}</p>
                    {s.recommended_actions.length > 0 && (
                      <div className="mt-2 text-xs text-slate-400">
                        Actions: {s.recommended_actions.join(" • ")}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </AgentSection>

            {/* Agent 8.2: Supply Chain */}
            <AgentSection id="8.2" name="Supply Chain Reasoning Agent" role="Suggests alternatives, scores sourcing risk">
              <div className="grid md:grid-cols-4 gap-3">
                <Metric label="Suppliers Monitored" value={data.supply_chain.total_suppliers_monitored} />
                <Metric label="High Risk" value={data.supply_chain.high_risk_suppliers} />
                <Metric label="Single Source Critical" value={data.supply_chain.critical_single_source} />
                <Metric label="Diversification" value={`${data.supply_chain.diversification_score?.toFixed(0)}%`} />
              </div>
              {data.supply_chain.immediate_actions?.length > 0 && (
                <div className="mt-3">
                  <p className="text-sm font-medium mb-1">Immediate Actions:</p>
                  {data.supply_chain.immediate_actions.map((a: string, i: number) => (
                    <p key={i} className="text-sm text-slate-300">→ {a}</p>
                  ))}
                </div>
              )}
            </AgentSection>

            {/* Agent 8.3: Production Rebalancing */}
            <AgentSection id="8.3" name="Production Rebalancing Agent" role="Creates virtual plant shifts, trades cost vs risk">
              <p className="text-sm mb-2">Status: <span className="text-green-400">{data.production_rebalancing.status}</span></p>
              {data.production_rebalancing.shift_plans?.map((p: any, i: number) => (
                <div key={i} className="bg-slate-800 rounded-lg p-3 mb-2 text-sm">
                  <p className="font-medium">🔄 {p.source} → {p.target}</p>
                  <p className="text-slate-400">Units: {p.units_shifted} | Cost: +${p.cost_increase_usd.toLocaleString()} | Risk reduction: {p.risk_reduction_pct}%</p>
                  <p className="text-slate-500 text-xs">{p.rationale}</p>
                </div>
              ))}
              {data.production_rebalancing.summary && (
                <div className="grid md:grid-cols-3 gap-3 mt-3">
                  <Metric label="Units Shifted" value={data.production_rebalancing.summary.total_units_shifted} />
                  <Metric label="Cost Increase" value={`$${data.production_rebalancing.summary.total_cost_increase_usd.toLocaleString()}`} />
                  <Metric label="Avg Risk Reduction" value={`${data.production_rebalancing.summary.average_risk_reduction_pct}%`} />
                </div>
              )}
            </AgentSection>

            {/* Agent 8.4: Financial Impact */}
            <AgentSection id="8.4" name="Financial Impact Agent" role="Revenue at risk, inventory exposure, margin erosion">
              <div className="grid md:grid-cols-4 gap-3">
                <Metric label="Expected Loss" value={`$${(data.financial_impact.expected_loss_usd || 0).toLocaleString()}`} />
                <Metric label="Worst Case" value={`$${(data.financial_impact.worst_case_usd || 0).toLocaleString()}`} />
                <Metric label="Net Exposure" value={`$${(data.financial_impact.net_exposure_usd || 0).toLocaleString()}`} />
                <Metric label="Margin Erosion" value={`${data.financial_impact.margin_erosion_pct || 0}%`} />
              </div>
              <div className="grid md:grid-cols-3 gap-3 mt-3">
                <Metric label="Penalty Exposure" value={`$${(data.financial_impact.penalty_exposure_usd || 0).toLocaleString()}`} />
                <Metric label="Mitigation ROI" value={`${data.financial_impact.mitigation_roi?.roi_pct || 0}%`} />
                <Metric label="Payback" value={`${data.financial_impact.mitigation_roi?.payback_days || 0} days`} />
              </div>
              <p className="text-xs text-slate-500 mt-3">
                Source: <a href="https://fred.stlouisfed.org" target="_blank" className="text-blue-400 hover:underline">FRED</a> + <a href="https://finnhub.io" target="_blank" className="text-blue-400 hover:underline">Finnhub</a> (LIVE)
              </p>
            </AgentSection>

            {/* Agent 8.5: Policy & Safety */}
            <AgentSection id="8.5" name="Policy & Safety Agent" role="Enforces: max risk tolerance, ethical sourcing, regulatory limits">
              <div className="grid md:grid-cols-4 gap-3">
                <Metric label="✅ Approved" value={data.policy_safety.approved_count} />
                <Metric label="⚠️ Flagged" value={data.policy_safety.flagged_count} />
                <Metric label="🚫 Blocked" value={data.policy_safety.blocked_count} />
                <Metric label="Violations" value={data.policy_safety.total_violations} />
              </div>
              <p className="text-sm text-slate-300 mt-3">{data.policy_safety.policy_summary}</p>
              {data.policy_safety.flagged?.map((f: any, i: number) => (
                <p key={i} className="text-yellow-400 text-sm mt-1">⚠️ {f.title}: {f.warnings?.join(", ")}</p>
              ))}
              {data.policy_safety.blocked?.map((b: any, i: number) => (
                <p key={i} className="text-red-400 text-sm mt-1">🚫 {b.title}: {b.reason}</p>
              ))}
            </AgentSection>

            {/* Agent 8.6: Executive Explanation */}
            <AgentSection id="8.6" name="Executive Explanation Agent" role="Turns probability into human narrative">
              <div className="space-y-4 text-sm">
                <div>
                  <p className="font-medium text-slate-200">Risk Narrative:</p>
                  <p className="text-slate-300">{data.executive_explanation.risk_narrative}</p>
                </div>
                <div>
                  <p className="font-medium text-slate-200">Recommended Actions:</p>
                  <p className="text-slate-300 whitespace-pre-wrap">{data.executive_explanation.action_brief}</p>
                </div>
                <div>
                  <p className="font-medium text-slate-200">Confidence Statement:</p>
                  <p className="text-slate-400">{data.executive_explanation.confidence_statement}</p>
                </div>
                {data.executive_explanation.ai_narrative && !data.executive_explanation.ai_narrative.includes("[LLM") && (
                  <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-3">
                    <p className="font-medium text-blue-300 text-xs mb-1">🤖 AI Narrative (Google Gemini)</p>
                    <p className="text-slate-200">{data.executive_explanation.ai_narrative}</p>
                  </div>
                )}
              </div>
            </AgentSection>

            {/* Recommendations */}
            <section className="bg-slate-900 border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-bold mb-4">💡 Final Recommendations (Policy-Approved)</h3>
              <div className="space-y-4">
                {data.recommendations.map((r) => (
                  <div key={r.id} className="bg-slate-800 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <h4 className="font-semibold">{r.title}</h4>
                      <span className="text-green-400 font-bold text-sm">ROI: {r.roi_pct}%</span>
                    </div>
                    <p className="text-slate-300 text-sm mt-1">{r.explanation}</p>
                    <div className="flex gap-6 mt-3 text-xs text-slate-400">
                      <span>Cost: ${r.cost_usd.toLocaleString()}</span>
                      <span>Savings: ${r.savings_usd.toLocaleString()}</span>
                      <span>Urgency: {r.urgency}</span>
                    </div>
                    <p className="text-xs text-yellow-500 mt-2">⚠️ Requires human approval</p>
                  </div>
                ))}
              </div>
            </section>

            {/* Chatbot */}
            <section className="bg-slate-900 border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-bold mb-4">💬 AI Chatbot (Gemini-powered)</h3>
              <p className="text-slate-400 text-sm mb-4">Ask about signals, scenarios, supply chain risks, or recommendations.</p>
              <div className="bg-slate-800 rounded-lg p-4 h-64 overflow-y-auto mb-3 space-y-2">
                {chatHistory.length === 0 && <p className="text-slate-500 text-sm">No messages yet. Ask a question below.</p>}
                {chatHistory.map((m, i) => (
                  <div key={i} className={`text-sm ${m.role === "user" ? "text-blue-300" : "text-slate-200"}`}>
                    <span className="font-bold">{m.role === "user" ? "You" : "MCCS"}:</span> {m.content}
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={chatMsg}
                  onChange={(e) => setChatMsg(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendChat()}
                  placeholder="Ask MCCS anything..."
                  className="flex-1 bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-blue-500"
                />
                <button onClick={sendChat} className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-sm font-medium">Send</button>
              </div>
            </section>

            {/* Alternatives Agent */}
            {data.alternatives && (
              <AgentSection id="NEW" name="Alternatives Agent" role="Finds alternative paths when disruptions block routes, suppliers, or resources">
                <p className="text-sm text-slate-300 mb-3">{data.alternatives.summary}</p>
                {data.alternatives.alternatives?.length > 0 ? (
                  <div className="space-y-3">
                    {data.alternatives.alternatives.map((alt: any) => (
                      <div key={alt.id} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-semibold text-sm">{alt.title}</h4>
                            <span className="text-xs bg-slate-700 text-slate-300 px-2 py-0.5 rounded-full">{alt.category}</span>
                          </div>
                          <div className="text-right text-xs">
                            <span className="text-green-400">Feasibility: {(alt.feasibility_score * 100).toFixed(0)}%</span><br/>
                            <span className="text-blue-400">Risk reduction: {alt.risk_reduction_pct}%</span>
                          </div>
                        </div>
                        <p className="text-slate-300 text-sm mt-2">{alt.description}</p>
                        <div className="flex gap-4 mt-2 text-xs text-slate-400">
                          <span>Cost impact: {alt.cost_impact_pct > 0 ? "+" : ""}{alt.cost_impact_pct}%</span>
                          <span>Time: {alt.time_impact_days > 0 ? "+" : ""}{alt.time_impact_days} days</span>
                          <a href={alt.proof_link} target="_blank" className="text-blue-400 hover:underline">🔗 Source proof</a>
                        </div>
                        {alt.trade_offs?.length > 0 && (
                          <div className="mt-2 text-xs text-yellow-400/80">
                            Trade-offs: {alt.trade_offs.join(" • ")}
                          </div>
                        )}
                        <p className="text-xs text-slate-500 mt-1">Triggered by: {alt.triggered_by}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-green-400 text-sm">✅ No disruptions requiring alternatives at this time.</p>
                )}
              </AgentSection>
            )}

            {/* Email Summary */}
            {data.email_summary && (
              <section className="bg-slate-900 border border-slate-700 rounded-xl p-6">
                <h3 className="text-lg font-bold mb-2">📧 Email Summary (Auto-Generated)</h3>
                <p className="text-slate-400 text-sm mb-4">Ready to send to business team when disruptions are detected.</p>
                <div className="bg-slate-800 rounded-lg p-4 mb-3">
                  <p className="text-xs text-slate-400">To: {data.email_summary.to}</p>
                  <p className="text-sm font-medium mt-1">{data.email_summary.subject}</p>
                </div>
                <details className="bg-slate-800 rounded-lg">
                  <summary className="p-3 cursor-pointer text-sm text-blue-400 hover:text-blue-300">View full email content</summary>
                  <div className="p-4 border-t border-slate-700">
                    <pre className="text-xs text-slate-300 whitespace-pre-wrap overflow-x-auto">{data.email_summary.body_text}</pre>
                  </div>
                </details>
              </section>
            )}

            {/* Data Sources */}
            <section className="bg-slate-900 border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-bold mb-4">🔗 Source of Truth — Live API Connections</h3>
              <div className="grid md:grid-cols-3 gap-3">
                {Object.entries(data.data_sources).map(([key, src]) => (
                  <a key={key} href={src.url} target="_blank" className="bg-slate-800 border border-slate-700 rounded-lg p-3 hover:border-blue-500 transition">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                      <span className="font-medium text-sm">{src.name}</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{src.url}</p>
                  </a>
                ))}
                <a href={data.ai_engine.url} target="_blank" className="bg-slate-800 border border-slate-700 rounded-lg p-3 hover:border-blue-500 transition">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
                    <span className="font-medium text-sm">{data.ai_engine.provider} ({data.ai_engine.model})</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">{data.ai_engine.url}</p>
                </a>
              </div>
              <p className="text-xs text-slate-500 mt-4">Analysis timestamp: {data.timestamp}</p>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}

function AgentSection({ id, name, role, children }: { id: string; name: string; role: string; children: React.ReactNode }) {
  return (
    <section className="bg-slate-900 border border-slate-700 rounded-xl p-6">
      <div className="flex items-center gap-3 mb-4">
        <span className="bg-slate-700 text-slate-300 text-xs font-mono px-2 py-1 rounded">{id}</span>
        <div>
          <h3 className="font-bold">{name}</h3>
          <p className="text-slate-400 text-sm">{role}</p>
        </div>
      </div>
      {children}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: any }) {
  return (
    <div className="bg-slate-800 rounded-lg p-3 text-center">
      <p className="text-xs text-slate-400">{label}</p>
      <p className="text-lg font-bold">{value}</p>
    </div>
  );
}
