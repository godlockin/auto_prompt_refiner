"""
Refined Prompt Refiner with clean architecture.

Features:
- Task type detection and classification
- Dynamic agent composition with priority-based scheduling
- Smart model selection (fast/pro based on complexity)
- Adaptive optimization rounds
- Domain-specific expert agents

Clean Architecture:
- core/: Core logic (types, classifier, orchestrator)
- agents/: Agent implementations
- api/: API layer
"""
import json
import logging
from typing import Dict, Any, List, Optional, Generator
from dataclasses import dataclass

from src.llm_client import LLMClient
from src.core.types import (
    TaskType, TaskComplexity, AgentConfig, TaskContext,
    RefinementResult, ProgressEvent
)
from src.core.classifier import TaskClassifier
from src.core.orchestrator import DynamicAgentOrchestrator

logger = logging.getLogger(__name__)


class PromptRefiner:
    """
    Advanced Prompt Refiner with Dynamic Agent Orchestration.

    Clean separation:
    - TaskClassifier: Determines task type and complexity
    - DynamicAgentOrchestrator: Selects and schedules agents
    - LLMClient: Handles LLM API calls
    """

    def __init__(
        self,
        max_rounds: Optional[int] = None,
        config_path: Optional[str] = None,
    ):
        self.llm = LLMClient()
        self.prompts = self._load_prompts()
        self.task_classifier = TaskClassifier()
        self.orchestrator = DynamicAgentOrchestrator()
        self._max_rounds = max_rounds

    def _load_prompts(self) -> Dict[str, Any]:
        """Load prompts from JSON file."""
        import os
        base_path = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(base_path, '..', 'data', 'prompts.json')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def analyze_task(self, prompt: str) -> TaskContext:
        """Analyze task and create optimized context."""
        task_type, complexity = self.task_classifier.classify(prompt)
        agents = self.orchestrator.get_agents_for_task(task_type, complexity, prompt)

        max_rounds = self._max_rounds or complexity.estimated_rounds

        return TaskContext(
            task_type=task_type,
            complexity=complexity,
            agents=agents,
            original_prompt=prompt
        )

    def run_refinement(
        self,
        user_prompt: str,
        stream: bool = False,
        callback: Optional[callable] = None,
    ) -> RefinementResult:
        """
        Execute full refinement process.

        Args:
            user_prompt: The prompt to refine
            stream: Whether to yield progress events
            callback: Optional callback for progress events

        Returns:
            RefinementResult with final prompt and metadata
        """
        context = self.analyze_task(user_prompt)
        history: List[Dict[str, str]] = []
        final_draft = ""

        if stream:
            generator = self._run_refinement_stream(context)
            for event in generator:
                if callback:
                    callback(event)
        else:
            final_draft = self._run_refinement_sync(context, history)

        enabled_agents = [a.name for a in context.agents if a.enabled]

        return RefinementResult(
            original_prompt=user_prompt,
            final_prompt=final_draft,
            task_type=context.task_type.value,
            complexity=context.complexity.score,
            model_used=context.complexity.recommended_model,
            rounds_completed=0,
            agents_used=enabled_agents,
            history=history,
        )

    def _run_refinement_stream(
        self,
        context: TaskContext,
    ) -> Generator[ProgressEvent, None, None]:
        """Run refinement with streaming progress events."""
        prompt = context.original_prompt

        yield ProgressEvent(
            phase="analyze",
            message="Analyzing task type and complexity...",
            data={
                "task_type": context.task_type.value,
                "complexity": context.complexity.score,
                "model": context.complexity.recommended_model,
                "rounds": context.complexity.estimated_rounds,
            }
        )

        enabled_experts = [
            a.name for a in context.agents
            if a.enabled and a.agent_type != "core"
        ]
        if enabled_experts:
            yield ProgressEvent(
                phase="select",
                message=f"Activating expert agents: {', '.join(enabled_experts)}",
                data={"experts": enabled_experts}
            )

        strategy = self._execute_agent("strategist", prompt, "", context)
        yield ProgressEvent(
            phase="strategy",
            message=f"Strategy: {strategy[:100]}...",
            data={"strategy": strategy}
        )

        draft = self._execute_agent("architect", prompt, strategy, context)
        yield ProgressEvent(
            phase="draft",
            message=f"Draft created ({len(draft)} chars)",
            data={"draft_length": len(draft)}
        )

        expert_reviews: Dict[str, str] = {}
        for agent in context.agents:
            if agent.agent_type in ["code", "security", "performance", "writing", "data"]:
                yield ProgressEvent(
                    phase="review",
                    message=f"{agent.name} review...",
                    data={"agent": agent.name}
                )
                review = self._execute_agent(agent.name, prompt, draft, context)
                expert_reviews[agent.name] = review

        critique = self._execute_agent("critic", self._build_critic_input(prompt, draft, expert_reviews), "", context)
        yield ProgressEvent(
            phase="critique",
            message="Critique complete",
            data={"critique_length": len(critique)}
        )

        if "NO_ISSUES_FOUND" in critique:
            yield ProgressEvent(
                phase="complete",
                message="Perfection achieved! No issues found.",
                data={"final_draft": draft, "converged": True}
            )
            return

        current_draft = draft
        for round_num in range(1, context.complexity.estimated_rounds + 1):
            yield ProgressEvent(
                phase="refine",
                message=f"Round {round_num} refinement...",
                data={"round": round_num}
            )

            current_draft = self._execute_agent(
                "refiner",
                f"Critique:\n{critique}\n\nCurrent Draft:\n{current_draft}",
                "",
                context,
            )

            yield ProgressEvent(
                phase="verify",
                message=f"Round {round_num} verification...",
                data={"draft_length": len(current_draft)}
            )

            critique = self._execute_agent(
                "critic",
                f"{prompt}\n\n{current_draft}",
                "",
                context,
            )

            if "NO_ISSUES_FOUND" in critique:
                yield ProgressEvent(
                    phase="complete",
                    message=f"Round {round_num} passed!",
                    data={"final_draft": current_draft, "converged": True}
                )
                return

            if round_num == context.complexity.estimated_rounds:
                yield ProgressEvent(
                    phase="complete",
                    message="Maximum rounds reached. Finalizing.",
                    data={"final_draft": current_draft, "converged": False}
                )
                return

        yield ProgressEvent(
            phase="complete",
            message="Process complete",
            data={"final_draft": current_draft, "converged": False}
        )

    def _run_refinement_sync(
        self,
        context: TaskContext,
        history: List[Dict[str, str]],
    ) -> str:
        """Run refinement synchronously without streaming."""
        prompt = context.original_prompt

        strategy = self._execute_agent("strategist", prompt, "", context)
        history.append({"role": "strategist", "content": strategy})

        draft = self._execute_agent("architect", prompt, strategy, context)
        history.append({"role": "architect", "content": draft})

        expert_reviews: Dict[str, str] = {}
        for agent in context.agents:
            if agent.agent_type in ["code", "security", "performance", "writing", "data"]:
                review = self._execute_agent(agent.name, prompt, draft, context)
                expert_reviews[agent.name] = review

        critique = self._execute_agent("critic", self._build_critic_input(prompt, draft, expert_reviews), "", context)
        history.append({"role": "critic", "content": critique})

        if "NO_ISSUES_FOUND" in critique:
            return draft

        current_draft = draft
        for round_num in range(1, context.complexity.estimated_rounds + 1):
            current_draft = self._execute_agent(
                "refiner",
                f"Critique:\n{critique}\n\nCurrent Draft:\n{current_draft}",
                "",
                context,
            )

            critique = self._execute_agent(
                "critic",
                f"{prompt}\n\n{current_draft}",
                "",
                context,
            )

            if "NO_ISSUES_FOUND" in critique:
                break

        return current_draft

    def _build_critic_input(
        self,
        prompt: str,
        draft: str,
        expert_reviews: Dict[str, str],
    ) -> str:
        """Build input for critic agent."""
        critic_input = f"Original Request:\n{prompt}\n\nCurrent Draft:\n{draft}"
        if expert_reviews:
            critic_input += "\n\nExpert Reviews:\n" + "\n".join(
                f"{k}: {v}" for k, v in expert_reviews.items()
            )
        return critic_input

    def _execute_agent(
        self,
        agent_name: str,
        user_input: str,
        strategy: str,
        context: TaskContext,
        model: Optional[str] = None,
    ) -> str:
        """Execute a specific agent."""
        prompt_config = self.prompts.get(agent_name, {})
        if not prompt_config:
            logger.warning(f"No prompt config for agent: {agent_name}")
            return ""

        system_prompt = prompt_config.get("system", "")
        template = prompt_config.get("user_template", "{input}")

        if agent_name == "strategist":
            prompt_text = f"{system_prompt}\n\nUser Input: {user_input}"
        elif agent_name == "architect":
            prompt_text = f"{system_prompt}\n\nStrategy:\n{strategy}\n\nOriginal Request:\n{user_input}"
        elif agent_name in ["critic", "refiner"]:
            prompt_text = f"{system_prompt}\n\n{user_input}"
        else:
            prompt_text = f"{system_prompt}\n\nTask:\n{user_input}\n\nContext:\n{context.original_prompt}"

        model_name = model or prompt_config.get("model", "fast")

        try:
            return self.llm.generate_content(prompt_text, model_name=model_name)
        except Exception as e:
            logger.error(f"Agent {agent_name} failed: {e}")
            return f"[Error in {agent_name}: {str(e)}]"

    def health_check(self) -> Dict[str, Any]:
        """Health check for the refiner service."""
        return {
            "status": "healthy",
            "prompts_loaded": bool(self.prompts),
            "prompts_count": len(self.prompts),
        }


def create_refiner(max_rounds: Optional[int] = None) -> PromptRefiner:
    """Factory function to create a PromptRefiner instance."""
    return PromptRefiner(max_rounds=max_rounds)
