"""Tests for the config module."""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestConfig:
    """Test cases for the Config class."""

    def test_config_structure(self):
        """Test Config class has required attributes."""
        from src.config import Config
        assert hasattr(Config, 'GOOGLE_API_KEY')
        assert hasattr(Config, 'GEMINI_MODEL_PRIMARY')
        assert hasattr(Config, 'VERTEX_PROJECT_ID')
        assert hasattr(Config, 'BASE_DIR')
        assert hasattr(Config, 'TASKS_DIR')

    def test_config_default_values(self):
        """Test that default configuration values are set correctly."""
        from src.config import Config
        assert Config.GEMINI_MODEL_PRIMARY == "gemini-2.5-pro"
        assert Config.VERTEX_LOCATION == "us-central1"
