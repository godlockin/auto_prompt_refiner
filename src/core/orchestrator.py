"""
Dynamic Agent Orchestrator with proper priority-based scheduling.
All agents are scheduled based on priority, no hardcoded core agent order.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from src.core.types import TaskType, TaskComplexity, AgentConfig


class AgentType(Enum):
    """Agent type classification."""
    CORE = "core"
    CODE = "code"
    SECURITY = "security"
    PERFORMANCE = "performance"
    WRITING = "writing"
    DATA = "data"


@dataclass
class AgentTrigger:
    """Condition for triggering an agent."""
    task_types: List[TaskType] = field(default_factory=list)
    require_security_review: bool = False
    require_performance_review: bool = False
    complexity_min: Optional[int] = None


@dataclass
class AgentDefinition:
    """Complete agent definition for registry."""
    name: str
    agent_type: AgentType
    model: str
    priority: int
    trigger: Optional[AgentTrigger] = None


class DynamicAgentOrchestrator:
    """
    Orchestrates dynamic agent composition based on task.

    All agents are registered with priorities and triggered based on:
    - Task type (code, writing, analysis, etc.)
    - Complexity requirements
    - Security/performance review requirements

    No hardcoded core agent order - all agents sorted by priority.
    """

    _AGENT_REGISTRY: Dict[str, AgentDefinition] = {}

    @classmethod
    def _ensure_initialized(cls) -> None:
        """Initialize agent registry once."""
        if cls._AGENT_REGISTRY:
            return

        cls._AGENT_REGISTRY = {
            "strategist": AgentDefinition(
                name="strategist",
                agent_type=AgentType.CORE,
                model="fast",
                priority=10,
            ),
            "architect": AgentDefinition(
                name="architect",
                agent_type=AgentType.CORE,
                model="fast",
                priority=20,
            ),
            "critic": AgentDefinition(
                name="critic",
                agent_type=AgentType.CORE,
                model="fast",
                priority=30,
            ),
            "refiner": AgentDefinition(
                name="refiner",
                agent_type=AgentType.CORE,
                model="pro",
                priority=40,
            ),
            "code_expert": AgentDefinition(
                name="code_expert",
                agent_type=AgentType.CODE,
                model="pro",
                priority=50,
                trigger=AgentTrigger(
                    task_types=[TaskType.CODE_GENERATION, TaskType.TECHNICAL],
                ),
            ),
            "security_expert": AgentDefinition(
                name="security_expert",
                agent_type=AgentType.SECURITY,
                model="pro",
                priority=60,
                trigger=AgentTrigger(
                    require_security_review=True,
                ),
            ),
            "performance_expert": AgentDefinition(
                name="performance_expert",
                agent_type=AgentType.PERFORMANCE,
                model="pro",
                priority=70,
                trigger=AgentTrigger(
                    require_performance_review=True,
                ),
            ),
            "style_expert": AgentDefinition(
                name="style_expert",
                agent_type=AgentType.WRITING,
                model="fast",
                priority=80,
                trigger=AgentTrigger(
                    task_types=[TaskType.WRITING, TaskType.CREATIVE],
                ),
            ),
            "data_expert": AgentDefinition(
                name="data_expert",
                agent_type=AgentType.DATA,
                model="pro",
                priority=90,
                trigger=AgentTrigger(
                    task_types=[TaskType.DATA_ANALYSIS],
                ),
            ),
        }

    @classmethod
    def get_agents_for_task(
        cls,
        task_type: TaskType,
        complexity: TaskComplexity,
        prompt: str = "",
    ) -> List[AgentConfig]:
        """
        Get all agents for a task, sorted by priority.

        Args:
            task_type: The classified task type
            complexity: The assessed complexity
            prompt: Original prompt for additional context

        Returns:
            List of AgentConfig sorted by priority
        """
        cls._ensure_initialized()

        agents: List[AgentConfig] = []
        prompt_lower = prompt.lower() if prompt else ""

        for agent_def in cls._AGENT_REGISTRY.values():
            if cls._should_include_agent(agent_def, task_type, complexity, prompt_lower):
                agents.append(AgentConfig(
                    name=agent_def.name,
                    agent_type=agent_def.agent_type.value,
                    system_prompt="",
                    model=agent_def.model,
                    enabled=True,
                    priority=agent_def.priority,
                ))

        return sorted(agents, key=lambda x: x.priority)

    @classmethod
    def _should_include_agent(
        cls,
        agent_def: AgentDefinition,
        task_type: TaskType,
        complexity: TaskComplexity,
        prompt_lower: str,
    ) -> bool:
        """Determine if an agent should be included for this task."""
        trigger = agent_def.trigger

        if trigger is None:
            return True

        if trigger.task_types and task_type not in trigger.task_types:
            return False

        if trigger.require_security_review and not complexity.requires_security_review:
            return False

        if trigger.require_performance_review and not complexity.requires_performance_review:
            return False

        if trigger.complexity_min is not None and complexity.score < trigger.complexity_min:
            return False

        return True

    @classmethod
    def get_core_agents(cls) -> List[AgentConfig]:
        """Get only core agents (strategist, architect, critic, refiner)."""
        cls._ensure_initialized()

        return [
            AgentConfig(
                name=defn.name,
                agent_type=defn.agent_type.value,
                system_prompt="",
                model=defn.model,
                enabled=True,
                priority=defn.priority,
            )
            for defn in cls._AGENT_REGISTRY.values()
            if defn.agent_type == AgentType.CORE
        ]

    @classmethod
    def get_expert_agents(cls) -> List[AgentConfig]:
        """Get only expert agents (non-core)."""
        cls._ensure_initialized()

        return [
            AgentConfig(
                name=defn.name,
                agent_type=defn.agent_type.value,
                system_prompt="",
                model=defn.model,
                enabled=True,
                priority=defn.priority,
            )
            for defn in cls._AGENT_REGISTRY.values()
            if defn.agent_type != AgentType.CORE
        ]

    @classmethod
    def get_all_agent_names(cls) -> List[str]:
        """Get list of all registered agent names."""
        cls._ensure_initialized()
        return list(cls._AGENT_REGISTRY.keys())
