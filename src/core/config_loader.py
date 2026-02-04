"""
Configuration loader with YAML support.
Allows external configuration of agents, priorities, and thresholds.
"""
import os
import yaml
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Configuration error."""
    pass


@dataclass
class AgentConfigSpec:
    """Agent configuration specification."""
    name: str
    type: str
    model: str
    priority: int
    enabled: bool = True
    trigger: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClassifierConfigSpec:
    """Task classifier configuration."""
    keyword_weights: Dict[str, Dict[str, float]] = field(default_factory=dict)


@dataclass
class RefinerConfigSpec:
    """Refiner overall configuration."""
    default_model: str = "fast"
    max_rounds: int = 3
    min_rounds: int = 1
    early_termination: bool = True
    early_termination_threshold: str = "NO_ISSUES_FOUND"


class ConfigLoader:
    """
    Configuration loader supporting YAML files.

    Search order:
    1. $CONFIG_PATH environment variable
    2. ./config/refiner.yaml
    3. ./config.yaml
    4. Default values
    """

    _instance: Optional['ConfigLoader'] = None
    _config: Dict[str, Any] = {}

    def __new__(cls) -> 'ConfigLoader':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._config:
            self._load()

    def _find_config_file(self) -> Optional[str]:
        """Find config file in search order."""
        search_paths = [
            os.environ.get('CONFIG_PATH'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'refiner.yaml'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml'),
        ]

        for path in search_paths:
            if path and os.path.exists(path):
                return path
        return None

    def _load(self) -> None:
        """Load configuration from YAML file."""
        config_path = self._find_config_file()

        if config_path is None:
            logger.info("No config file found, using defaults")
            self._config = self._get_defaults()
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = yaml.safe_load(f) or {}
            self._config = self._merge_defaults(loaded_config)
            logger.info(f"Loaded config from {config_path}")
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config file: {e}")
            self._config = self._get_defaults()
        except IOError as e:
            logger.error(f"Error reading config file: {e}")
            self._config = self._get_defaults()

    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'agents': self._get_default_agents(),
            'classifier': self._get_default_classifier(),
            'refiner': self._get_default_refiner(),
        }

    def _get_default_agents(self) -> Dict[str, Any]:
        """Get default agent configuration."""
        return {
            'strategist': {'type': 'core', 'model': 'fast', 'priority': 10, 'enabled': True},
            'architect': {'type': 'core', 'model': 'fast', 'priority': 20, 'enabled': True},
            'critic': {'type': 'core', 'model': 'fast', 'priority': 30, 'enabled': True},
            'refiner': {'type': 'core', 'model': 'pro', 'priority': 40, 'enabled': True},
            'code_expert': {'type': 'code', 'model': 'pro', 'priority': 50, 'enabled': True},
            'security_expert': {'type': 'security', 'model': 'pro', 'priority': 60, 'enabled': True},
            'performance_expert': {'type': 'performance', 'model': 'pro', 'priority': 70, 'enabled': True},
            'style_expert': {'type': 'writing', 'model': 'fast', 'priority': 80, 'enabled': True},
            'data_expert': {'type': 'data', 'model': 'pro', 'priority': 90, 'enabled': True},
        }

    def _get_default_classifier(self) -> Dict[str, Any]:
        """Get default classifier configuration."""
        return {
            'keyword_weights': {
                'code': {
                    'def': 2.0, 'class': 2.0, 'python': 2.0, 'function': 1.5,
                    'import': 1.0, 'api': 1.0, 'algorithm': 1.5,
                },
                'writing': {
                    'write': 1.5, 'create': 1.0, 'story': 2.0, 'essay': 2.0,
                    'article': 1.5, 'narrative': 2.0,
                },
                'data': {
                    'analyze': 2.0, 'data': 1.5, 'statistics': 2.0, 'metrics': 2.0,
                    'visualization': 2.0, 'insights': 2.0,
                },
            },
        }

    def _get_default_refiner(self) -> Dict[str, Any]:
        """Get default refiner configuration."""
        return {
            'default_model': 'fast',
            'max_rounds': 3,
            'min_rounds': 1,
            'early_termination': True,
            'early_termination_keyword': 'NO_ISSUES_FOUND',
        }

    def _merge_defaults(self, loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded config with defaults."""
        defaults = self._get_defaults()

        merged = defaults.copy()
        for key in ['agents', 'classifier', 'refiner']:
            if key in loaded and isinstance(loaded[key], dict):
                merged[key].update(loaded[key])

        return merged

    def reload(self) -> None:
        """Reload configuration from file."""
        self._config = {}
        self._load()

    @property
    def agents(self) -> Dict[str, Any]:
        """Get agent configurations."""
        return self._config.get('agents', {})

    @property
    def classifier(self) -> Dict[str, Any]:
        """Get classifier configurations."""
        return self._config.get('classifier', {})

    @property
    def refiner(self) -> Dict[str, Any]:
        """Get refiner configurations."""
        return self._config.get('refiner', {})

    def get_agent_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific agent."""
        return self.agents.get(name)

    def get_agent_names(self) -> List[str]:
        """Get list of all configured agent names."""
        return list(self.agents.keys())

    def is_agent_enabled(self, name: str) -> bool:
        """Check if an agent is enabled."""
        config = self.get_agent_config(name)
        return config.get('enabled', True) if config else True

    def get_model_for_agent(self, name: str) -> str:
        """Get the model for a specific agent."""
        config = self.get_agent_config(name)
        return config.get('model', 'fast') if config else 'fast'

    def get_priority_for_agent(self, name: str) -> int:
        """Get the priority for a specific agent."""
        config = self.get_agent_config(name)
        return config.get('priority', 100) if config else 100


config_loader = ConfigLoader()
