import json
import logging
import os
from src.llm_client import LLMClient

logger = logging.getLogger(__name__)

class PromptRefiner:
    def __init__(self):
        self.llm = LLMClient()
        self.max_rounds = 3
        self.prompts = self._load_prompts()

    def _load_prompts(self):
        """Loads prompts from the unified JSON file."""
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            prompt_path = os.path.join(base_path, "data", "prompts.json")
            with open(prompt_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load prompts.json: {e}")
            raise

    def run_refinement_stream(self, user_prompt: str):
        # ... (same as before) ...
        """
        Executes the Synthesis Prime refinement protocol as a generator.
        Yields (current_stage_message, history_list, current_draft).
        """
        history = []
        current_draft = ""
        
        # 1. Inception: Density Scan & Strategy Mapping
        yield "🔍 Phase 1: Analyzing Intent & Strategy...", history, current_draft
        logger.info("Phase 1: Inception & Strategy")
        strategy_response = self._agent_strategist(user_prompt)
        history.append({"role": "Strategist", "content": strategy_response})
        yield "✅ Strategy Developed. Drafting Initial Prompt...", history, current_draft
        
        # 2. Initial Draft
        logger.info("Phase 2: Initial Draft")
        current_draft = self._agent_architect(user_prompt, strategy_response)
        history.append({"role": "Architect", "content": current_draft})
        yield "✅ Initial Draft Created. Starting Adversarial Refinement...", history, current_draft
        
        # 3. Adversarial Refinement Loop
        for i in range(self.max_rounds):
            logger.info(f"Phase 3: Refinement Round {i+1}")
            
            # Critique
            yield f"🤔 Round {i+1}: Critic is analyzing the draft...", history, current_draft
            critique = self._agent_critic(user_prompt, current_draft, history)
            history.append({"role": f"Critic_Round_{i+1}", "content": critique})
            
            if "NO_ISSUES_FOUND" in critique:
                logger.info("Critic found no issues. Converged.")
                yield "🏆 Perfection Achieved. Finalizing...", history, current_draft
                break
                
            # Refine
            yield f"✨ Round {i+1}: Refiner is optimizing based on feedback...", history, current_draft
            current_draft = self._agent_refiner(user_prompt, current_draft, critique)
            history.append({"role": f"Refiner_Round_{i+1}", "content": current_draft})
            
        yield "🎉 Process Complete!", history, current_draft

    def run_refinement(self, user_prompt: str) -> dict:
        """
        Legacy synchronous method.
        """
        final_draft = ""
        final_history = []
        for _, hist, draft in self.run_refinement_stream(user_prompt):
            final_history = hist
            final_draft = draft
        
        return {
            "original_prompt": user_prompt,
            "final_prompt": final_draft,
            "discussion_history": final_history
        }

    def _agent_strategist(self, original_prompt: str) -> str:
        p = self.prompts["strategist"]
        user_msg = p["user_template"].format(prompt=original_prompt)
        return self.llm.generate_content(f"{p['system']}\n\n{user_msg}")

    def _agent_architect(self, original_prompt: str, strategy: str) -> str:
        p = self.prompts["architect"]
        user_msg = p["user_template"].format(strategy=strategy, prompt=original_prompt)
        return self.llm.generate_content(f"{p['system']}\n\n{user_msg}")

    def _agent_critic(self, original_prompt: str, current_draft: str, history: list) -> str:
        p = self.prompts["critic"]
        user_msg = p["user_template"].format(prompt=original_prompt, draft=current_draft)
        return self.llm.generate_content(f"{p['system']}\n\n{user_msg}")

    def _agent_refiner(self, original_prompt: str, current_draft: str, critique: str) -> str:
        p = self.prompts["refiner"]
        user_msg = p["user_template"].format(critique=critique, draft=current_draft)
        return self.llm.generate_content(f"{p['system']}\n\n{user_msg}")
