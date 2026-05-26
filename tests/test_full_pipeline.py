"""Integration test for the full MCCS pipeline."""

import asyncio
import pytest
from mccs.agents.orchestrator import MCCSOrchestrator
from mccs.cognitive.causal_graph import build_demo_graph, CausalGraph
from mccs.cognitive.simulation import SimulationEngine
from mccs.agents.signal_intelligence import SignalIntelligenceAgent
from mccs.agents.supply_chain import SupplyChainAgent
from mccs.agents.financial_impact import FinancialImpactAgent
from mccs.agents.explanation import ExplanationAgent
from mccs.models.signals import SeverityLevel


class TestCausalGraph:
    """Test the causal graph engine."""

    def test_build_demo_graph(self):
        graph = build_demo_graph()
        stats = graph.get_graph_stats()
        assert stats["total_nodes"] > 10
        assert stats["total_edges"] > 10
        assert stats["is_dag"] is True

    def test_risk_propagation(self):
        graph = build_demo_graph()
        result = graph.propagate_risk("supplier-electronics-cn", 0.9)
        assert result.total_nodes_affected > 0
        assert result.origin_node == "supplier-electronics-cn"
        assert all(n["risk_level"] <= 0.9 for n in result.affected_nodes)

    def test_downstream_nodes(self):
        graph = build_demo_graph()
        downstream = graph.get_downstream_nodes("supplier-electronics-cn")
        assert len(downstream) > 0
        assert "port-shanghai" in downstream

    def test_node_criticality_ranking(self):
        graph = build_demo_graph()
        ranking = graph.get_node_criticality_ranking()
        assert len(ranking) > 0
        assert all("centrality" in node for node in ranking)


class TestSignalIntelligence:
    """Test signal collection from MCP servers."""

    @pytest.fixture
    def agent(self):
        return SignalIntelligenceAgent()

    def test_collect_signals(self, agent):
        signals = asyncio.run(agent.collect_all_signals())
        assert len(signals) > 0
        # Should have signals from multiple categories
        categories = set(s.category.value for s in signals)
        assert len(categories) >= 3

    def test_signal_ranking(self, agent):
        signals = asyncio.run(agent.collect_all_signals())
        # First signal should be highest severity
        severities = [s.severity for s in signals]
        assert severities[0] in (SeverityLevel.CRITICAL, SeverityLevel.HIGH)

    def test_signal_summary(self, agent):
        asyncio.run(agent.collect_all_signals())
        summary = agent.get_signal_summary()
        assert summary["total_signals"] > 0
        assert "by_severity" in summary
        assert "by_category" in summary


class TestSimulation:
    """Test the counterfactual simulation engine."""

    @pytest.fixture
    def engine(self):
        graph = build_demo_graph()
        return SimulationEngine(graph)

    @pytest.fixture
    def signals(self):
        agent = SignalIntelligenceAgent()
        return asyncio.run(agent.collect_all_signals())

    def test_simulate_scenarios(self, engine, signals):
        scenarios = engine.simulate_scenarios(signals, num_scenarios=10)
        assert len(scenarios) > 0
        assert len(scenarios) <= 10
        # Should be sorted by revenue at risk
        for i in range(len(scenarios) - 1):
            assert scenarios[i].total_revenue_at_risk_usd >= scenarios[i + 1].total_revenue_at_risk_usd

    def test_generate_recommendations(self, engine, signals):
        scenarios = engine.simulate_scenarios(signals)
        recommendations = engine.generate_recommendations(scenarios)
        assert len(recommendations) > 0
        for rec in recommendations:
            assert rec.estimated_savings_usd > 0
            assert rec.requires_approval is True


class TestSupplyChain:
    """Test supply chain reasoning agent."""

    @pytest.fixture
    def agent(self):
        graph = build_demo_graph()
        return SupplyChainAgent(graph)

    @pytest.fixture
    def signals(self):
        si = SignalIntelligenceAgent()
        return asyncio.run(si.collect_all_signals())

    def test_assess_supplier_risk(self, agent, signals):
        risks = agent.assess_supplier_risk(signals)
        assert len(risks) > 0
        assert all("risk_score" in r for r in risks)

    def test_suggest_alternatives(self, agent):
        alts = agent.suggest_alternatives("supplier-electronics-cn")
        assert len(alts) > 0

    def test_evaluate_strategy(self, agent, signals):
        strategy = agent.evaluate_sourcing_strategy(signals)
        assert "total_suppliers_monitored" in strategy
        assert "diversification_score" in strategy


class TestFinancialImpact:
    """Test financial impact calculations."""

    @pytest.fixture
    def agent(self):
        return FinancialImpactAgent()

    @pytest.fixture
    def scenarios(self):
        graph = build_demo_graph()
        engine = SimulationEngine(graph)
        si = SignalIntelligenceAgent()
        signals = asyncio.run(si.collect_all_signals())
        return engine.simulate_scenarios(signals)

    def test_calculate_impact(self, agent, scenarios):
        impact = agent.calculate_impact(scenarios)
        assert impact["expected_loss_usd"] > 0
        assert impact["worst_case_usd"] >= impact["expected_loss_usd"]
        assert "mitigation_roi" in impact

    def test_cost_benefit(self, agent, scenarios):
        cba = agent.cost_benefit_analysis(scenarios)
        assert "mitigation_options" in cba
        assert len(cba["mitigation_options"]) > 0


class TestExplanation:
    """Test executive explanation generation."""

    @pytest.fixture
    def agent(self):
        return ExplanationAgent()

    def test_executive_briefing(self, agent):
        si = SignalIntelligenceAgent()
        signals = asyncio.run(si.collect_all_signals())

        graph = build_demo_graph()
        engine = SimulationEngine(graph)
        scenarios = engine.simulate_scenarios(signals)
        recommendations = engine.generate_recommendations(scenarios)

        fi = FinancialImpactAgent()
        financial = fi.calculate_impact(scenarios)

        briefing = agent.generate_executive_briefing(signals, scenarios, recommendations, financial)
        assert "headline" in briefing
        assert "situation_summary" in briefing
        assert "risk_narrative" in briefing
        assert "action_brief" in briefing
        assert len(briefing["headline"]) > 0


class TestFullPipeline:
    """End-to-end integration test."""

    def test_full_analysis(self):
        orchestrator = MCCSOrchestrator()
        result = asyncio.run(orchestrator.run_full_analysis(num_scenarios=5))

        # Verify all components produced output
        assert len(result.signals) > 0
        assert len(result.scenarios) > 0
        assert len(result.recommendations) > 0
        assert result.financial_impact["expected_loss_usd"] > 0
        assert result.executive_briefing["headline"] != ""
        assert result.graph_stats["total_nodes"] > 10

        # Verify Production Rebalancing Agent (8.3)
        assert result.production_rebalancing.get("status") == "plan_generated"
        assert "shift_plans" in result.production_rebalancing
        assert "affected_plants" in result.production_rebalancing

        # Verify Policy & Safety Agent (8.5)
        assert "approved_count" in result.policy_review
        assert "blocked_count" in result.policy_review
        assert "policy_summary" in result.policy_review

        # Verify human-in-the-loop
        for rec in result.recommendations:
            assert rec.requires_approval is True


class TestProductionRebalancing:
    """Test production rebalancing agent."""

    @pytest.fixture
    def agent(self):
        from mccs.agents.production_rebalancing import ProductionRebalancingAgent
        graph = build_demo_graph()
        return ProductionRebalancingAgent(graph)

    @pytest.fixture
    def signals(self):
        si = SignalIntelligenceAgent()
        return asyncio.run(si.collect_all_signals())

    def test_assess_capacity(self, agent):
        capacity = agent.assess_capacity()
        assert "plants" in capacity
        assert len(capacity["plants"]) > 0
        assert capacity["total_spare_capacity_units"] > 0

    def test_generate_rebalancing_plan(self, agent, signals):
        graph = build_demo_graph()
        engine = SimulationEngine(graph)
        scenarios = engine.simulate_scenarios(signals)
        plan = agent.generate_rebalancing_plan(signals, scenarios)
        assert plan["status"] == "plan_generated"
        assert plan["requires_approval"] is True

    def test_simulate_shift(self, agent):
        result = agent.simulate_shift("plant-detroit-assembly", "plant-monterrey", 100)
        assert result["feasible"] is True
        assert "cost_analysis" in result


class TestPolicySafety:
    """Test policy and safety agent."""

    @pytest.fixture
    def agent(self):
        from mccs.agents.policy_safety import PolicySafetyAgent
        return PolicySafetyAgent()

    @pytest.fixture
    def signals(self):
        si = SignalIntelligenceAgent()
        return asyncio.run(si.collect_all_signals())

    def test_review_recommendations(self, agent, signals):
        graph = build_demo_graph()
        engine = SimulationEngine(graph)
        scenarios = engine.simulate_scenarios(signals)
        recommendations = engine.generate_recommendations(scenarios)
        review = agent.review_recommendations(recommendations, signals, scenarios)
        assert "approved_count" in review
        assert "blocked_count" in review
        assert "policy_summary" in review

    def test_validate_sourcing_approved(self, agent):
        result = agent.validate_sourcing_decision("vietnam", "electronics")
        assert result["approved"] is True

    def test_validate_sourcing_banned(self, agent):
        result = agent.validate_sourcing_decision("north_korea", "minerals")
        assert result["approved"] is False
        assert result["severity"] == "block"

    def test_validate_sourcing_restricted(self, agent):
        result = agent.validate_sourcing_decision("russia", "titanium")
        assert result["approved"] is True
        assert result["severity"] == "warning"

    def test_check_production_safety(self, agent):
        # Should pass
        result = agent.check_production_safety("plant-detroit", 85.0, 45)
        assert result["safe"] is True

        # Should fail - over capacity
        result = agent.check_production_safety("plant-detroit", 98.0, 45)
        assert result["safe"] is False

        # Should fail - overtime
        result = agent.check_production_safety("plant-detroit", 80.0, 70)
        assert result["safe"] is False
