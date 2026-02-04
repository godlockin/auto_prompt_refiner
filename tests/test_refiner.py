"""Tests for the refiner module with new architecture."""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTaskClassifier:
    """Test cases for TaskClassifier."""

    def test_classify_code_task(self):
        """Test task classification for code prompts."""
        from src.core.classifier import TaskClassifier
        task_type, complexity = TaskClassifier.classify(
            "Write a Python function to calculate fibonacci"
        )
        assert task_type.value == "code"
        assert complexity.score >= 1
        assert complexity.recommended_model in ["fast", "pro"]
        assert complexity.requires_code_expert == True

    def test_classify_writing_task(self):
        """Test task classification for writing prompts."""
        from src.core.classifier import TaskClassifier
        task_type, complexity = TaskClassifier.classify(
            "Create a creative story about space exploration"
        )
        assert task_type.value in ["writing", "creative"]
        assert complexity.score >= 1

    def test_classify_analysis_task(self):
        """Test task classification for data analysis prompts."""
        from src.core.classifier import TaskClassifier
        task_type, complexity = TaskClassifier.classify(
            "Analyze this dataset and provide insights about trends and patterns"
        )
        # "analyze" + "data" + "patterns" should trigger analysis
        assert task_type.value in ["analysis", "data_analysis"]
        assert complexity.score >= 1

    def test_classify_general_task(self):
        """Test task classification for general prompts."""
        from src.core.classifier import TaskClassifier
        task_type, complexity = TaskClassifier.classify(
            "Hello, how are you?"
        )
        assert task_type.value == "general"
        assert complexity.score == 1

    def test_pre_compiled_patterns(self):
        """Test that patterns are pre-compiled."""
        from src.core.classifier import TaskClassifier
        TaskClassifier._ensure_compiled()
        assert len(TaskClassifier._COMPILED_PATTERNS) > 0

    def test_batch_classification(self):
        """Test batch classification."""
        from src.core.classifier import TaskClassifier
        prompts = [
            "Write a Python function",
            "Create a story",
            "Analyze data",
        ]
        results = TaskClassifier.classify_batch(prompts)
        assert len(results) == 3
        for task_type, complexity in results:
            assert complexity.score >= 1


class TestDynamicAgentOrchestrator:
    """Test cases for DynamicAgentOrchestrator."""

    def test_get_core_agents(self):
        """Test getting core agents."""
        from src.core.orchestrator import DynamicAgentOrchestrator
        from src.core.types import TaskType
        from src.core.classifier import TaskClassifier

        task_type, complexity = TaskClassifier.classify("Write Python code")
        agents = DynamicAgentOrchestrator.get_agents_for_task(task_type, complexity, "Write Python code")

        agent_names = [a.name for a in agents]
        assert "strategist" in agent_names
        assert "architect" in agent_names
        assert "critic" in agent_names
        assert "refiner" in agent_names
        assert "code_expert" in agent_names

    def test_priority_ordering(self):
        """Test agents are sorted by priority."""
        from src.core.orchestrator import DynamicAgentOrchestrator
        from src.core.classifier import TaskClassifier

        task_type, complexity = TaskClassifier.classify("Write Python code")
        agents = DynamicAgentOrchestrator.get_agents_for_task(task_type, complexity, "Write Python code")

        priorities = [a.priority for a in agents]
        assert priorities == sorted(priorities)

    def test_expert_agents_for_code_task(self):
        """Test expert agents are included for code tasks."""
        from src.core.orchestrator import DynamicAgentOrchestrator
        from src.core.classifier import TaskClassifier

        task_type, complexity = TaskClassifier.classify("Write Python code")
        agents = DynamicAgentOrchestrator.get_agents_for_task(task_type, complexity, "Write Python code")

        agent_types = [a.agent_type for a in agents]
        assert "code" in agent_types
        assert "security" in agent_types

    def test_no_experts_for_general_task(self):
        """Test no expert agents for general tasks."""
        from src.core.orchestrator import DynamicAgentOrchestrator
        from src.core.classifier import TaskClassifier

        task_type, complexity = TaskClassifier.classify("Hello")
        agents = DynamicAgentOrchestrator.get_agents_for_task(task_type, complexity, "Hello")

        expert_types = ["code", "security", "performance", "writing", "data"]
        for agent in agents:
            if agent.agent_type in expert_types:
                pytest.fail(f"Unexpected expert agent: {agent.name}")


class TestPromptRefiner:
    """Test cases for PromptRefiner."""

    def test_refiner_init(self):
        """Test PromptRefiner can be initialized."""
        from src.refiner import PromptRefiner
        refiner = PromptRefiner()
        assert refiner is not None
        assert hasattr(refiner, 'llm')
        assert hasattr(refiner, 'prompts')
        assert hasattr(refiner, 'task_classifier')
        assert hasattr(refiner, 'orchestrator')

    def test_prompts_loaded(self):
        """Test that prompts are loaded correctly."""
        from src.refiner import PromptRefiner
        refiner = PromptRefiner()
        assert refiner.prompts is not None
        assert "strategist" in refiner.prompts
        assert "architect" in refiner.prompts
        assert "critic" in refiner.prompts
        assert "refiner" in refiner.prompts

    def test_analyze_task_returns_context(self):
        """Test task analysis creates proper context."""
        from src.refiner import PromptRefiner
        refiner = PromptRefiner()
        context = refiner.analyze_task("Write a Python function")
        assert context is not None
        assert hasattr(context, 'task_type')
        assert hasattr(context, 'complexity')
        assert hasattr(context, 'agents')
        assert hasattr(context, 'original_prompt')

    def test_health_check(self):
        """Test health check returns expected structure."""
        from src.refiner import PromptRefiner
        refiner = PromptRefiner()
        health = refiner.health_check()
        assert "status" in health
        assert "prompts_loaded" in health
        assert "prompts_count" in health


class TestProgressEvent:
    """Test cases for ProgressEvent."""

    def test_progress_event_creation(self):
        """Test ProgressEvent can be created."""
        from src.core.types import ProgressEvent
        event = ProgressEvent(
            phase="analyze",
            message="Testing",
            data={"key": "value"}
        )
        assert event.phase == "analyze"
        assert event.message == "Testing"
        assert event.data == {"key": "value"}


class TestConfigLoader:
    """Test cases for ConfigLoader."""

    def test_config_loader_init(self):
        """Test ConfigLoader can be initialized."""
        from src.core.config_loader import ConfigLoader
        loader = ConfigLoader()
        assert loader is not None

    def test_config_has_agents(self):
        """Test config has agent configurations."""
        from src.core.config_loader import ConfigLoader
        loader = ConfigLoader()
        agents = loader.agents
        assert "strategist" in agents
        assert "architect" in agents
        assert "critic" in agents

    def test_agent_enabled(self):
        """Test agent enabled check."""
        from src.core.config_loader import ConfigLoader
        loader = ConfigLoader()
        assert loader.is_agent_enabled("strategist") == True
