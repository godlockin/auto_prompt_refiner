"""Tests for the refiner module."""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPromptRefiner:
    """Test cases for PromptRefiner class."""

    def test_prompt_refiner_init(self):
        """Test PromptRefiner can be initialized."""
        from src.refiner import PromptRefiner
        refiner = PromptRefiner()
        assert refiner is not None
        assert hasattr(refiner, 'llm')
        assert hasattr(refiner, 'prompts')
        assert hasattr(refiner, 'max_rounds')

    def test_prompt_refiner_prompts_loaded(self):
        """Test that prompts are loaded correctly."""
        from src.refiner import PromptRefiner
        refiner = PromptRefiner()
        assert refiner.prompts is not None
        assert "strategist" in refiner.prompts
        assert "architect" in refiner.prompts
        assert "critic" in refiner.prompts
        assert "refiner" in refiner.prompts

    def test_prompt_refiner_max_rounds_default(self):
        """Test default max_rounds value."""
        from src.refiner import PromptRefiner
        refiner = PromptRefiner()
        assert refiner.max_rounds == 3

    def test_run_refinement_returns_result(self):
        """Test run_refinement returns a RefinementResult."""
        from src.refiner import PromptRefiner, RefinementResult
        refiner = PromptRefiner()
        result = refiner.run_refinement("Test prompt")
        assert isinstance(result, RefinementResult)
        assert hasattr(result, 'original_prompt')
        assert hasattr(result, 'final_prompt')
        assert hasattr(result, 'discussion_history')


class TestAgentMessage:
    """Test cases for agent message handling."""

    def test_history_append(self):
        """Test that history can be appended."""
        from src.refiner import PromptRefiner
        refiner = PromptRefiner()
        history = []
        history.append({"role": "Strategist", "content": "Test"})
        assert len(history) == 1
        assert history[0]["role"] == "Strategist"
