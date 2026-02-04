"""Pytest configuration and fixtures."""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from typing import Generator

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_llm_response():
    """Mock LLM response."""
    response = MagicMock()
    response.text = "This is a mock response from the LLM."
    return response


@pytest.fixture
def mock_llm_client(mock_llm_response):
    """Mock LLM client for testing."""
    with patch('src.llm_client.genai') as mock_genai:
        mock_genai.configure = MagicMock()
        mock_genai.GenerativeModel.return_value = MagicMock()
        mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_llm_response

        with patch('src.llm_client.vertexai'):
            with patch('src.llm_client.service_account'):
                from src.llm_client import LLMClient
                client = LLMClient()
                client.generate_content = MagicMock(return_value="Mock response")
                yield client


@pytest.fixture
def sample_prompt():
    """Sample user prompt for testing."""
    return "Help me write a Python function to calculate fibonacci numbers efficiently."


@pytest.fixture
def sample_strategy_response():
    """Sample strategy response from Strategist agent."""
    return """
    ## Entropy Scan
    - Information Density: Medium
    - Ambiguity Vector: None detected
    - Signal-to-Noise Ratio: 85%

    ## Intent Decoding
    - Core Objective: Create efficient fibonacci calculation
    - Latent Desires: Performance optimization, error handling

    ## Gap Identification
    - Missing Variables: None
    - Failure Modes: Recursion stack overflow

    ## Strategic Architecture
    - Synthesis Mode: Mode B (Deep Delivery)
    - Engineering Frameworks: Iterative approach, memoization
    """


@pytest.fixture
def temp_env_file(tmp_path):
    """Create a temporary .env file for testing."""
    env_file = tmp_path / ".env"
    env_file.write_text("""
GOOGLE_API_KEY=test_key_12345
GEMINI_MODEL=test-model
GEMINI_MODEL_FAST=test-flash
VERTEX_CREDENTIALS_PATH=
VERTEX_PROJECT_ID=
VERTEX_LOCATION=us-central1
""")
    return str(env_file)
