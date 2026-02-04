"""
Shared type definitions for Prompt Refiner.
Used by both Python and TypeScript implementations.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class TaskType(Enum):
    """Task type classification."""
    CODE_GENERATION = "code"
    WRITING = "writing"
    DATA_ANALYSIS = "analysis"
    CREATIVE = "creative"
    GENERAL = "general"
    TECHNICAL = "technical"
    DOCUMENTATION = "documentation"


@dataclass
class TaskComplexity:
    """Task complexity assessment."""
    score: int
    estimated_tokens: int
    recommended_model: str
    estimated_rounds: int
    requires_code_expert: bool
    requires_security_review: bool
    requires_performance_review: bool


@dataclass
class AgentConfig:
    """Configuration for a specific agent."""
    name: str
    agent_type: str
    system_prompt: str
    model: str
    enabled: bool = True
    priority: int = 0


@dataclass
class TaskContext:
    """Context for task execution."""
    task_type: TaskType
    complexity: TaskComplexity
    agents: List[AgentConfig]
    original_prompt: str
    strategy: str = ""
    current_draft: str = ""
    history: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class RefinementResult:
    """Result of a refinement operation."""
    original_prompt: str
    final_prompt: str
    task_type: str
    complexity: int
    model_used: str
    rounds_completed: int
    agents_used: List[str]
    history: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class ProgressEvent:
    """Progress event for streaming output."""
    phase: str
    message: str
    data: Optional[Dict[str, Any]] = None
