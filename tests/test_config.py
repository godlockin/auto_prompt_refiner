"""Tests for the config module."""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestConfig:
    """Test cases for the Config class."""

    def test_config_validate_no_missing(self):
        """Test validation passes with required config."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            import importlib
            import src.config
            importlib.reload(src.config)
            from src.config import Config
            Config.GOOGLE_API_KEY = "test_key"
            missing = Config.validate()
            assert len(missing) == 0

    def test_config_validate_missing_api_key(self):
        """Test validation fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import src.config
            importlib.reload(src.config)
            from src.config import Config
            Config.GOOGLE_API_KEY = None
            missing = Config.validate()
            assert "GOOGLE_API_KEY" in missing

    def test_config_is_valid(self):
        """Test Config.is_valid() returns correct value."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "valid_key"}):
            import importlib
            import src.config
            importlib.reload(src.config)
            from src.config import Config
            Config.GOOGLE_API_KEY = "valid_key"
            assert Config.is_valid() is True

            Config.GOOGLE_API_KEY = None
            assert Config.is_valid() is False

    def test_config_default_values(self):
        """Test that default configuration values are set correctly."""
        import importlib
        import src.config
        importlib.reload(src.config)
        from src.config import Config
        assert Config.GEMINI_MODEL_PRIMARY == "gemini-2.5-pro"
        assert Config.GEMINI_MODEL_FAST == "gemini-2.5-flash"
        assert Config.VERTEX_LOCATION == "us-central1"

    def test_config_vertex_credentials_path(self):
        """Test vertex credentials path validation."""
        import importlib
        import src.config
        importlib.reload(src.config)
        from src.config import Config
        Config.VERTEX_CREDENTIALS_PATH = "/nonexistent/path.json"
        path = Config.get_vertex_credentials_path()
        assert path is None

    def test_config_class_attributes_are_class_variables(self):
        """Test that Config uses class variables, not instances."""
        import src.config
        from src.config import Config
        assert hasattr(Config, 'GOOGLE_API_KEY')
        assert hasattr(Config, 'GEMINI_MODEL_PRIMARY')
        assert hasattr(Config, 'VERTEX_PROJECT_ID')

    def test_config_structure(self):
        """Test Config class has required attributes."""
        from src.config import Config
        assert isinstance(Config.GOOGLE_API_KEY, str) or Config.GOOGLE_API_KEY is None
        assert isinstance(Config.GEMINI_MODEL_PRIMARY, str)
        assert isinstance(Config.VERTEX_LOCATION, str)
        assert isinstance(Config.BASE_DIR, str)
        assert isinstance(Config.TASKS_DIR, str)
