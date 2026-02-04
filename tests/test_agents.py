"""Tests for Agent implementations."""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBaseAgent:
    """Test cases for BaseAgent."""

    def test_agent_factory_creates_agents(self):
        """Test that AgentFactory can create all agents."""
        from src.agents.base import AgentFactory

        agent_names = AgentFactory.get_agent_names()
        expected = [
            "strategist", "architect", "critic", "refiner",
            "code_expert", "security_expert", "performance_expert",
            "style_expert", "data_expert"
        ]

        for name in expected:
            assert name in agent_names, f"Missing agent: {name}"
            agent = AgentFactory.create_agent(name)
            assert agent.name == name

    def test_strategist_agent_creation(self):
        """Test StrategistAgent creation."""
        from src.agents.base import StrategistAgent
        agent = StrategistAgent()
        assert agent.name == "strategist"
        assert agent.default_model == "fast"

    def test_architect_agent_creation(self):
        """Test ArchitectAgent creation."""
        from src.agents.base import ArchitectAgent
        agent = ArchitectAgent()
        assert agent.name == "architect"
        assert agent.default_model == "fast"

    def test_critic_agent_creation(self):
        """Test CriticAgent creation."""
        from src.agents.base import CriticAgent
        agent = CriticAgent()
        assert agent.name == "critic"
        assert agent.default_model == "fast"

    def test_refiner_agent_creation(self):
        """Test RefinerAgent creation."""
        from src.agents.base import RefinerAgent
        agent = RefinerAgent()
        assert agent.name == "refiner"
        assert agent.default_model == "pro"

    def test_code_expert_agent_creation(self):
        """Test CodeExpertAgent creation."""
        from src.agents.base import CodeExpertAgent
        agent = CodeExpertAgent()
        assert agent.name == "code_expert"
        assert agent.default_model == "pro"

    def test_security_expert_agent_creation(self):
        """Test SecurityExpertAgent creation."""
        from src.agents.base import SecurityExpertAgent
        agent = SecurityExpertAgent()
        assert agent.name == "security_expert"
        assert agent.default_model == "pro"

    def test_performance_expert_agent_creation(self):
        """Test PerformanceExpertAgent creation."""
        from src.agents.base import PerformanceExpertAgent
        agent = PerformanceExpertAgent()
        assert agent.name == "performance_expert"
        assert agent.default_model == "pro"

    def test_style_expert_agent_creation(self):
        """Test StyleExpertAgent creation."""
        from src.agents.base import StyleExpertAgent
        agent = StyleExpertAgent()
        assert agent.name == "style_expert"
        assert agent.default_model == "fast"

    def test_data_expert_agent_creation(self):
        """Test DataExpertAgent creation."""
        from src.agents.base import DataExpertAgent
        agent = DataExpertAgent()
        assert agent.name == "data_expert"
        assert agent.default_model == "pro"

    def test_agent_factory_unknown_agent(self):
        """Test that AgentFactory raises error for unknown agents."""
        from src.agents.base import AgentFactory
        with pytest.raises(ValueError) as exc_info:
            AgentFactory.create_agent("unknown_agent")
        assert "Unknown agent" in str(exc_info.value)

    def test_agent_has(self):
        """Test AgentFactory.has_agent()."""
        from src.agents.base import AgentFactory
        assert AgentFactory.has_agent("strategist") == True
        assert AgentFactory.has_agent("unknown") == False

    def test_agent_result_creation(self):
        """Test AgentResult dataclass."""
        from src.agents.base import AgentResult

        success_result = AgentResult(
            success=True,
            content="Test content",
            tokens_used=100,
            latency_ms=500
        )
        assert success_result.success == True
        assert success_result.content == "Test content"
        assert success_result.error is None

        error_result = AgentResult(
            success=False,
            content="",
            error="Test error",
            tokens_used=0,
            latency_ms=100
        )
        assert error_result.success == False
        assert error_result.content == ""
        assert error_result.error == "Test error"

    def test_agent_str_representation(self):
        """Test agent string representation."""
        from src.agents.base import StrategistAgent
        agent = StrategistAgent()
        str_repr = str(agent)
        assert "StrategistAgent" in str_repr
        assert "strategist" in str_repr
