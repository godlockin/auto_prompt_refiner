import json
import logging
import os
from typing import Dict, Any, List, Optional, Generator, Tuple
from dataclasses import dataclass, field

from src.llm_client import LLMClient

logger = logging.getLogger(__name__)


@dataclass
class AgentMessage:
    """Represents a message from an agent in the refinement process."""
    role: str
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class RefinementResult:
    """Result of a refinement process."""
    original_prompt: str
    final_prompt: str
    discussion_history: List[AgentMessage] = field(default_factory=list)
    strategy_text: str = ""
    rounds_completed: int = 0
    converged: bool = False
    error: Optional[str] = None


class PromptRefiner:
    """
    Core orchestrator for the Synthesis Prime prompt refinement protocol.
    """

    def __init__(self, max_rounds: int = 3):
        self.llm = LLMClient()
        self.max_rounds = max_rounds
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> Dict[str, Any]:
        """Loads prompts from the unified JSON file."""
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            prompt_path = os.path.join(base_path, "data", "prompts.json")

            if not os.path.exists(prompt_path):
                raise FileNotFoundError(f"Configuration file not found: {prompt_path}")

            with open(prompt_path, "r", encoding="utf-8") as f:
                prompts_data = json.load(f)

            logger.info(f"Successfully loaded prompts from: {prompt_path}")
            return prompts_data

        except FileNotFoundError as e:
            logger.error(str(e))
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in prompts.json: {e}")
            raise ValueError(f"Invalid JSON format in prompts.json: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error loading prompts.json: {e}")
            raise RuntimeError(f"Failed to load prompts: {e}") from e

    def _validate_prompt(self, prompt: str) -> None:
        """Validate input prompt."""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        if len(prompt) > 100000:
            raise ValueError(f"Prompt too long ({len(prompt)} chars). Maximum allowed is 100000 characters.")

    def run_refinement_stream(
        self,
        user_prompt: str
    ) -> Generator[Tuple[str, List[AgentMessage], str], None, None]:
        """
        Executes the Synthesis Prime refinement protocol as a generator.
        """
        self._validate_prompt(user_prompt)

        history: List[AgentMessage] = []
        current_draft = ""

        try:
            yield "🔍 Phase 1: Analyzing Intent & Strategy...", history, current_draft

            logger.info("Phase 1: Inception & Strategy")
            strategy_response = self._agent_strategist(user_prompt)
            history.append(AgentMessage(role="Strategist", content=strategy_response))

            yield "✅ Strategy Developed. Drafting Initial Prompt...", history, current_draft

            logger.info("Phase 2: Initial Draft")
            current_draft = self._agent_architect(user_prompt, strategy_response)
            history.append(AgentMessage(role="Architect", content=current_draft))

            yield "✅ Initial Draft Created. Starting Adversarial Refinement...", history, current_draft

            logger.info("Phase 3: Adversarial Refinement")
            converged = False

            for i in range(self.max_rounds):
                logger.info(f"Refinement Round {i+1}/{self.max_rounds}")

                yield f"🤔 Round {i+1}: Critic is analyzing the draft...", history, current_draft

                try:
                    critique = self._agent_critic(user_prompt, current_draft, history)
                except Exception as e:
                    logger.error(f"Critic failed in round {i+1}: {e}")
                    critique = f"[Error in critique generation: {str(e)}]"

                history.append(AgentMessage(role=f"Critic_Round_{i+1}", content=critique))

                if "NO_ISSUES_FOUND" in critique:
                    logger.info("Critic found no issues. Converged.")
                    converged = True
                    yield "🏆 Perfection Achieved. Finalizing...", history, current_draft
                    break

                yield f"✨ Round {i+1}: Refiner is optimizing based on feedback...", history, current_draft

                try:
                    current_draft = self._agent_refiner(user_prompt, current_draft, critique)
                except Exception as e:
                    logger.error(f"Refiner failed in round {i+1}: {e}")
                    current_draft = f"[Error in refinement: {str(e)}]"

                history.append(AgentMessage(role=f"Refiner_Round_{i+1}", content=current_draft))

            if not converged:
                logger.info(f"Max rounds ({self.max_rounds}) reached without convergence")

            yield "🎉 Process Complete!", history, current_draft

        except Exception as e:
            logger.error(f"LLM Service Error during refinement: {e}")
            yield f"❌ Error: {str(e)}", history, current_draft
            raise
        except Exception as e:
            logger.error(f"Unexpected error during refinement: {e}", exc_info=True)
            yield f"❌ Unexpected error: {str(e)}", history, current_draft
            raise

    def run_refinement(self, user_prompt: str) -> RefinementResult:
        """Execute the full refinement process synchronously."""
        result = RefinementResult(
            original_prompt=user_prompt,
            final_prompt="",
            discussion_history=[]
        )

        final_draft = ""
        final_history: List[AgentMessage] = []

        try:
            for status_msg, history, draft in self.run_refinement_stream(user_prompt):
                final_draft = draft
                final_history = history

                if "Error" in status_msg or "❌" in status_msg:
                    result.error = status_msg

            result.final_prompt = final_draft
            result.discussion_history = final_history
            result.rounds_completed = len([m for m in final_history if m.role.startswith("Refiner_Round")])
            result.converged = any(
                m.role.startswith("Critic") and "NO_ISSUES_FOUND" in m.content
                for m in final_history
            )

            if final_history:
                strategist_msg = next((m for m in final_history if m.role == "Strategist"), None)
                if strategist_msg:
                    result.strategy_text = strategist_msg.content

        except Exception as e:
            logger.error(f"Refinement failed: {e}")
            result.error = str(e)
            result.final_prompt = final_draft

        return result

    def _agent_strategist(self, original_prompt: str) -> str:
        """Execute the Strategist agent."""
        p = self.prompts.get("strategist", {})
        if not p:
            raise ValueError("Strategist prompt not found in prompts.json")

        user_msg = p["user_template"].format(prompt=original_prompt)
        prompt_text = f"{p['system']}\n\n{user_msg}"

        try:
            return self.llm.generate_content(prompt_text, model_name="fast")
        except Exception:
            return self.llm.generate_content(prompt_text)

    def _agent_architect(self, original_prompt: str, strategy: str) -> str:
        """Execute the Architect agent."""
        p = self.prompts.get("architect", {})
        if not p:
            raise ValueError("Architect prompt not found in prompts.json")

        user_msg = p["user_template"].format(strategy=strategy, prompt=original_prompt)
        prompt_text = f"{p['system']}\n\n{user_msg}"

        try:
            return self.llm.generate_content(prompt_text, model_name="fast")
        except Exception:
            return self.llm.generate_content(prompt_text)

    def _agent_critic(
        self,
        original_prompt: str,
        current_draft: str,
        history: List[AgentMessage]
    ) -> str:
        """Execute the Critic agent."""
        p = self.prompts.get("critic", {})
        if not p:
            raise ValueError("Critic prompt not found in prompts.json")

        user_msg = p["user_template"].format(prompt=original_prompt, draft=current_draft)
        prompt_text = f"{p['system']}\n\n{user_msg}"

        return self.llm.generate_content(prompt_text)

    def _agent_refiner(
        self,
        original_prompt: str,
        current_draft: str,
        critique: str
    ) -> str:
        """Execute the Refiner agent."""
        p = self.prompts.get("refiner", {})
        if not p:
            raise ValueError("Refiner prompt not found in prompts.json")

        user_msg = p["user_template"].format(critique=critique, draft=current_draft)
        prompt_text = f"{p['system']}\n\n{user_msg}"

        return self.llm.generate_content(prompt_text)

    def health_check(self) -> Dict[str, Any]:
        """Check the health of the refiner and its dependencies."""
        return {
            "llm_client": self.llm.health_check(),
            "prompts_loaded": bool(self.prompts),
            "prompts_available": list(self.prompts.keys()) if self.prompts else [],
            "max_rounds": self.max_rounds
        }
