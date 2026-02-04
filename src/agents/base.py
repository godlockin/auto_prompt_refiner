"""
Base Agent Abstract Class and Implementations.

This module provides:
- BaseAgent abstract base class
- Concrete agent implementations
- Strategy pattern for agent execution
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

from src.core.types import TaskContext, AgentConfig
from src.llm_client import LLMClient

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Result of agent execution."""
    success: bool
    content: str
    error: Optional[str] = None
    tokens_used: int = 0
    latency_ms: int = 0


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, name: str, default_model: str = "fast"):
        self.name = name
        self.default_model = default_model
        self._llm: Optional[LLMClient] = None

    @property
    def llm(self) -> LLMClient:
        """Lazy initialization of LLM client."""
        if self._llm is None:
            self._llm = LLMClient()
        return self._llm

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass

    @abstractmethod
    def build_prompt(self, user_input: str, context: TaskContext) -> str:
        """Build the full prompt for this agent."""
        pass

    def execute(
        self,
        user_input: str,
        context: TaskContext,
        model: Optional[str] = None,
    ) -> AgentResult:
        """
        Execute the agent's logic.

        Args:
            user_input: The user input or previous output
            context: The task context
            model: Override model selection

        Returns:
            AgentResult with execution outcome
        """
        try:
            model = model or self.default_model
            prompt = self.build_prompt(user_input, context)
            system_prompt = self.get_system_prompt()

            full_prompt = f"{system_prompt}\n\n{prompt}"

            import time
            start = time.time()
            content = self.llm.generate_content(full_prompt, model_name=model)
            latency = int((time.time() - start) * 1000)

            return AgentResult(
                success=True,
                content=content,
                tokens_used=len(content.split()),
                latency_ms=latency,
            )

        except Exception as e:
            logger.error(f"Agent {self.name} failed: {e}")
            return AgentResult(
                success=False,
                content="",
                error=str(e),
            )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"

    def __repr__(self) -> str:
        return self.__str__()


class StrategistAgent(BaseAgent):
    """Agent responsible for strategy development."""

    def __init__(self):
        super().__init__("strategist", "fast")

    def get_system_prompt(self) -> str:
        return """### SYSTEM IDENTITY: CHIEF COGNITIVE ARCHITECT // SYNTHESIS PRIME

[PRIME DIRECTIVE]
You are the Chief Cognitive Architect. Your function is to deconstruct, analyze, and architect the logic required to optimize user inputs.

[ANALYSIS PROTOCOL]
Analyze user input and generate optimization blueprint:
1. ENTROPY SCAN: Information Density, Ambiguity Vector, Signal-to-Noise Ratio
2. INTENT DECODING: Core Objective, Latent Desires
3. GAP IDENTIFICATION: Missing Variables, Failure Modes
4. STRATEGIC ARCHITECTURE: Synthesis Mode, Engineering Frameworks"""

    def build_prompt(self, user_input: str, context: TaskContext) -> str:
        return f"User Input: {user_input}"


class ArchitectAgent(BaseAgent):
    """Agent responsible for architecture design."""

    def __init__(self):
        super().__init__("architect", "fast")

    def get_system_prompt(self) -> str:
        return """You are the Prime Architect. Your sole purpose is to transmute abstract strategic intent into executable, high-fidelity System Prompts.

[STRUCTURE]
## Role: Persona definition
## Mission: Core objective
## Workflow: Step-by-step algorithmic instruction
## Constraints: Negative constraints and safety boundaries

[QUALITY STANDARD]
Output must be "State-of-the-Art". Use strong imperative verbs (Execute, Synthesize, Validate). Eliminate passive voice."""

    def build_prompt(self, user_input: str, context: TaskContext) -> str:
        return f"Strategy:\n{context.strategy}\n\nOriginal Request:\n{user_input}"


class CriticAgent(BaseAgent):
    """Agent responsible for adversarial critique."""

    def __init__(self):
        super().__init__("critic", "fast")

    def get_system_prompt(self) -> str:
        return """// SYSTEM IDENTITY: ADVERSARIAL_PRIME //

PRIME DIRECTIVE:
Execute ruthless stress testing of the target prompt.

[OUTPUT PROTOCOL]
If perfect: Output exactly "NO_ISSUES_FOUND"
If flaws exist: Generate DAMAGE REPORT:
**[SEVERITY: CRITICAL/MODERATE/MINOR]**
**[VECTOR]**: Specific mechanism of failure
**[PATCH]**: Exact verbatim text required to fix"""

    def build_prompt(self, user_input: str, context: TaskContext) -> str:
        return f"Original Request:\n{context.original_prompt}\n\nCurrent Draft:\n{user_input}"


class RefinerAgent(BaseAgent):
    """Agent responsible for refining and optimizing."""

    def __init__(self):
        super().__init__("refiner", "pro")

    def get_system_prompt(self) -> str:
        return """IDENTITY: You are the Prime Optimization Core.

MISSION: Synthesize critique and draft into SOTA iteration.

[RULES]
1. Treat Critic's feedback as immutable directives
2. Maintain Markdown architecture
3. Prior optimizations must be preserved
4. Maximize token economy

OUTPUT: Return ONLY the consolidated prompt text."""

    def build_prompt(self, user_input: str, context: TaskContext) -> str:
        return f"Critique:\n{context.current_draft}\n\nCurrent Draft:\n{user_input}"


class CodeExpertAgent(BaseAgent):
    """Expert agent for code-related tasks."""

    def __init__(self):
        super().__init__("code_expert", "pro")

    def get_system_prompt(self) -> str:
        return """IDENTITY: Senior Code Review Expert

MISSION: Review code prompts for best practices

[REVIEW CRITERIA]
1. Code Style: Follow language-specific conventions
2. Error Handling: Robust exception management
3. Performance: Optimal algorithms and data structures
4. Security: Input validation, injection prevention
5. Documentation: Clear comments and docstrings

OUTPUT: Specific improvements with code snippets"""

    def build_prompt(self, user_input: str, context: TaskContext) -> str:
        return f"Task:\n{context.original_prompt}\n\nDraft:\n{user_input}"


class SecurityExpertAgent(BaseAgent):
    """Expert agent for security-related tasks."""

    def __init__(self):
        super().__init__("security_expert", "pro")

    def get_system_prompt(self) -> str:
        return """IDENTITY: Security Architect

MISSION: Identify security vulnerabilities in prompts

[ATTACK VECTORS]
1. Prompt Injection: Malicious instruction overrides
2. Information Disclosure: Sensitive data leakage
3. Authentication Bypass: Weak auth requirements
4. Output Manipulation: Response exploitation

OUTPUT: Critical security findings with patches"""

    def build_prompt(self, user_input: str, context: TaskContext) -> str:
        return f"Task:\n{context.original_prompt}\n\nDraft:\n{user_input}"


class PerformanceExpertAgent(BaseAgent):
    """Expert agent for performance optimization."""

    def __init__(self):
        super().__init__("performance_expert", "pro")

    def get_system_prompt(self) -> str:
        return """IDENTITY: Performance Engineer

MISSION: Optimize for speed and resource efficiency

[CRITERIA]
1. Time Complexity: O(n) or better preferred
2. Space Complexity: Minimal memory footprint
3. I/O Efficiency: Batch operations, caching
4. Concurrency: Parallel processing when beneficial

OUTPUT: Performance bottlenecks with optimization suggestions"""

    def build_prompt(self, user_input: str, context: TaskContext) -> str:
        return f"Task:\n{context.original_prompt}\n\nDraft:\n{user_input}"


class StyleExpertAgent(BaseAgent):
    """Expert agent for writing style."""

    def __init__(self):
        super().__init__("style_expert", "fast")

    def get_system_prompt(self) -> str:
        return """IDENTITY: Editorial Style Expert

MISSION: Ensure writing quality and consistency

[CRITERIA]
1. Voice: Consistent tone and register
2. Clarity: Concise, unambiguous language
3. Structure: Logical flow, proper transitions
4. Grammar: Error-free prose

OUTPUT: Specific style improvements"""

    def build_prompt(self, user_input: str, context: TaskContext) -> str:
        return f"Task:\n{context.original_prompt}\n\nDraft:\n{user_input}"


class DataExpertAgent(BaseAgent):
    """Expert agent for data analysis."""

    def __init__(self):
        super().__init__("data_expert", "pro")

    def get_system_prompt(self) -> str:
        return """IDENTITY: Data Analysis Specialist

MISSION: Ensure data analysis prompts are rigorous

[CRITERIA]
1. Statistical Validity: Proper statistical methods
2. Visualization: Clear, informative charts
3. Interpretation: Accurate, nuanced insights
4. Reproducibility: Clear methodology

OUTPUT: Data analysis quality issues with fixes"""

    def build_prompt(self, user_input: str, context: TaskContext) -> str:
        return f"Task:\n{context.original_prompt}\n\nDraft:\n{user_input}"


# Agent Factory
class AgentFactory:
    """Factory for creating agent instances."""

    _AGENTS = {
        "strategist": StrategistAgent,
        "architect": ArchitectAgent,
        "critic": CriticAgent,
        "refiner": RefinerAgent,
        "code_expert": CodeExpertAgent,
        "security_expert": SecurityExpertAgent,
        "performance_expert": PerformanceExpertAgent,
        "style_expert": StyleExpertAgent,
        "data_expert": DataExpertAgent,
    }

    @classmethod
    def create_agent(cls, name: str) -> BaseAgent:
        """Create an agent by name."""
        agent_class = cls._AGENTS.get(name)
        if agent_class is None:
            raise ValueError(f"Unknown agent: {name}")
        return agent_class()

    @classmethod
    def get_agent_names(cls) -> list:
        """Get list of available agent names."""
        return list(cls._AGENTS.keys())

    @classmethod
    def has_agent(cls, name: str) -> bool:
        """Check if an agent exists."""
        return name in cls._AGENTS
