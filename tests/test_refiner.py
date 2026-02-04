"""Tests for the refiner module."""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from typing import Generator

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAgentMessage:
    """Test cases for AgentMessage dataclass."""

    def test_agent_message_creation(self):
        """Test AgentMessage can be created with role and content."""
        from src.refiner import AgentMessage
        msg = AgentMessage(role="Strategist", content="Test content")
        assert msg.role == "Strategist"
        assert msg.content == "Test content"

    def test_agent_message_to_dict(self):
        """Test AgentMessage.to_dict() returns correct format."""
        from src.refiner import AgentMessage
        msg = AgentMessage(role="Architect", content="Draft content")
        result = msg.to_dict()
        assert isinstance(result, dict)
        assert result["role"] == "Architect"
        assert result["content"] == "Draft content"


class TestRefinementResult:
    """Test cases for RefinementResult dataclass."""

    def test_refinement_result_creation(self):
        """Test RefinementResult can be created."""
        from src.refiner import RefinementResult
        result = RefinementResult(
            original_prompt="Test prompt",
            final_prompt="Refined prompt"
        )
        assert result.original_prompt == "Test prompt"
        assert result.final_prompt == "Refined prompt"
        assert result.discussion_history == []
        assert result.converged is False
        assert result.error is None


class TestPromptRefiner:
    """Test cases for PromptRefiner class."""

    @pytest.fixture
    def mock_prompts(self):
        """Create mock prompts for testing."""
        return {
            "strategist": {
                "system": "You are a strategist.",
                "user_template": "User Input: {prompt}"
            },
            "architect": {
                "system": "You are an architect.",
                "user_template": "Strategy:\n{strategy}\n\nOriginal Request:\n{prompt}"
            },
            "critic": {
                "system": "You are a critic.",
                "user_template": "Original Request:\n{prompt}\n\nCurrent Draft:\n{draft}"
            },
            "refiner": {
                "system": "You are a refiner.",
                "user_template": "Critique:\n{critique}\n\nCurrent Draft:\n{draft}"
            }
        }

    def test_validate_prompt_empty(self):
        """Test that empty prompt raises ValueError."""
        from src.refiner import PromptRefiner
        refiner = PromptRefiner.__new__(PromptRefiner)
        with pytest.raises(ValueError, match="cannot be empty"):
            refiner._validate_prompt("")

    def test_validate_prompt_whitespace_only(self):
        """Test that whitespace-only prompt raises ValueError."""
        from src.refiner import PromptRefiner
        refiner = PromptRefiner.__new__(PromptRefiner)
        with pytest.raises(ValueError, match="cannot be empty"):
            refiner._validate_prompt("   \t\n  ")

    def test_validate_prompt_too_long(self):
        """Test that overly long prompt raises ValueError."""
        from src.refiner import PromptRefiner
        refiner = PromptRefiner.__new__(PromptRefiner)
        long_prompt = "x" * 100001
        with pytest.raises(ValueError, match="too long"):
            refiner._validate_prompt(long_prompt)

    def test_validate_prompt_valid(self):
        """Test that valid prompt doesn't raise."""
        from src.refiner import PromptRefiner
        refiner = PromptRefiner.__new__(PromptRefiner)
        refiner._validate_prompt("Valid prompt")
        refiner._validate_prompt("A" * 50000)

    def test_run_refinement_convergence(self, mock_prompts):
        """Test that refinement converges when Critic finds no issues."""
        from src.refiner import PromptRefiner

        mock_llm = MagicMock()
        mock_llm.generate_content.side_effect = [
            "Strategy response",
            "Architect draft",
            "NO_ISSUES_FOUND"
        ]

        with patch('src.refiner.LLMClient', return_value=mock_llm):
            with patch('src.refiner.PromptRefiner._load_prompts', return_value=mock_prompts):
                refiner = PromptRefiner()
                results = list(refiner.run_refinement_stream("Test prompt"))

                final_status = results[-1][0]
                assert "Complete" in final_status or "Perfection" in final_status

    def test_run_refinement_max_rounds(self, mock_prompts):
        """Test that refinement respects max_rounds."""
        from src.refiner import PromptRefiner

        mock_llm = MagicMock()
        mock_llm.generate_content.side_effect = [
            "Strategy response",
            "Architect draft",
        ] + ["Critique findings"] * 6 + ["Refined draft"] * 3

        with patch('src.refiner.LLMClient', return_value=mock_llm):
            with patch('src.refiner.PromptRefiner._load_prompts', return_value=mock_prompts):
                refiner = PromptRefiner(max_rounds=3)
                results = list(refiner.run_refinement_stream("Test prompt"))

                assert len(results) == 10

    def test_run_refinement_with_error(self, mock_prompts):
        """Test that errors are handled gracefully."""
        from src.refiner import PromptRefiner
        from src.llm_client import LLMServiceError

        mock_llm = MagicMock()
        mock_llm.generate_content.side_effect = LLMServiceError("API Error", "test")

        with patch('src.refiner.LLMClient', return_value=mock_llm):
            with patch('src.refiner.PromptRefiner._load_prompts', return_value=mock_prompts):
                refiner = PromptRefiner()
                result = refiner.run_refinement("Test prompt")

                assert result.error is not None


class TestRefinerAgentMethods:
    """Test individual agent methods."""

    @pytest.fixture
    def mock_prompts(self):
        """Create mock prompts for testing."""
        return {
            "strategist": {
                "system": "STRATEGIST_SYSTEM",
                "user_template": "User Input: {prompt}"
            },
            "architect": {
                "system": "ARCHITECT_SYSTEM",
                "user_template": "Strategy:\n{strategy}\n\nOriginal Request:\n{prompt}"
            },
            "critic": {
                "system": "CRITIC_SYSTEM",
                "user_template": "Original Request:\n{prompt}\n\nCurrent Draft:\n{draft}"
            },
            "refiner": {
                "system": "REFINER_SYSTEM",
                "user_template": "Critique:\n{critique}\n\nCurrent Draft:\n{draft}"
            }
        }

    def test_agent_strategist(self, mock_prompts):
        """Test _agent_strategist method."""
        from src.refiner import PromptRefiner

        mock_llm = MagicMock()
        mock_llm.generate_content.return_value = "Strategy response"

        refiner = PromptRefiner.__new__(PromptRefiner)
        refiner.llm = mock_llm
        refiner.prompts = mock_prompts

        result = refiner._agent_strategist("Test prompt")

        assert result == "Strategy response"
        mock_llm.generate_content.assert_called_once()

    def test_agent_architect(self, mock_prompts):
        """Test _agent_architect method."""
        from src.refiner import PromptRefiner

        mock_llm = MagicMock()
        mock_llm.generate_content.return_value = "Architect draft"

        refiner = PromptRefiner.__new__(PromptRefiner)
        refiner.llm = mock_llm
        refiner.prompts = mock_prompts

        result = refiner._agent_architect("Test prompt", "Test strategy")

        assert result == "Architect draft"
        mock_llm.generate_content.assert_called_once()

    def test_agent_critic(self, mock_prompts):
        """Test _agent_critic method."""
        from src.refiner import PromptRefiner

        mock_llm = MagicMock()
        mock_llm.generate_content.return_value = "Critique response"

        refiner = PromptRefiner.__new__(PromptRefiner)
        refiner.llm = mock_llm
        refiner.prompts = mock_prompts

        result = refiner._agent_critic("Test prompt", "Test draft", [])

        assert result == "Critique response"
        mock_llm.generate_content.assert_called_once()

    def test_agent_refiner(self, mock_prompts):
        """Test _agent_refiner method."""
        from src.refiner import PromptRefiner

        mock_llm = MagicMock()
        mock_llm.generate_content.return_value = "Refined draft"

        refiner = PromptRefiner.__new__(PromptRefiner)
        refiner.llm = mock_llm
        refiner.prompts = mock_prompts

        result = refiner._agent_refiner("Test prompt", "Test draft", "Test critique")

        assert result == "Refined draft"
        mock_llm.generate_content.assert_called_once()
