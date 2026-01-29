import json
import logging
from src.llm_client import LLMClient

logger = logging.getLogger(__name__)

class PromptRefiner:
    def __init__(self):
        self.llm = LLMClient()
        self.max_rounds = 3

    def run_refinement_stream(self, user_prompt: str):
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
        # ... existing implementation wrapper if needed, but we'll use stream mostly
        # Re-implement using stream to avoid code duplication
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
        sys_prompt = """
        You are the **Chief Cognitive Architect** of the Synthesis Prime system.
        Your goal is to analyze the user's input prompt and determine the best optimization strategy.
        
        Output Analysis:
        1. **Information Density**: High/Low.
        2. **Core Intent**: What is the user really trying to achieve?
        3. **Missing Variables**: What context is missing?
        4. **Recommended Strategy**: 
           - Mode A (Cognitive Handshake) or Mode B (Deep Delivery)?
           - Specific Techniques: CoT, Few-Shot, Role-Play, etc.
        """
        return self.llm.generate_content(f"{sys_prompt}\n\nUser Input: {original_prompt}")

    def _agent_architect(self, original_prompt: str, strategy: str) -> str:
        sys_prompt = """
        You are the **Lead Prompt Engineer**. Based on the strategy provided, create the FIRST DRAFT of the System Prompt.
        
        Follow the **Synthesis Prime Standards**:
        1. **Structure Obsession**: Use Markdown H1/H2 headers (## Role, ## Mission, ## Workflow, ## Constraints).
        2. **Language Lock**: Use Simplified Chinese for explanations, English for code/variables if needed.
        3. **Mechanism**: Implement the strategy (e.g., if CoT is requested, add <thinking> tags).
        """
        return self.llm.generate_content(f"{sys_prompt}\n\nStrategy:\n{strategy}\n\nOriginal Request:\n{original_prompt}")

    def _agent_critic(self, original_prompt: str, current_draft: str, history: list) -> str:
        sys_prompt = """
        You are the **Adversarial Critic (Red Team)**.
        Your job is to TEAR APART the current prompt draft. Find every weakness.
        
        Check for:
        1. **Ambiguity**: Is anything open to interpretation?
        2. **Hallucination Risks**: Are there guardrails?
        3. **Constraint Loopholes**: Can the user bypass rules?
        4. **Alignment**: Does it meet the original intent?
        
        If the prompt is SOTA (State-of-the-Art) and perfect, output "NO_ISSUES_FOUND".
        Otherwise, list specific, actionable changes.
        """
        return self.llm.generate_content(f"{sys_prompt}\n\nOriginal Request:\n{original_prompt}\n\nCurrent Draft:\n{current_draft}")

    def _agent_refiner(self, original_prompt: str, current_draft: str, critique: str) -> str:
        sys_prompt = """
        You are the **Senior Optimization Specialist**.
        Refine the prompt based on the Critic's feedback.
        
        Rules:
        1. Address EVERY point in the critique.
        2. Maintain the structural integrity (Markdown).
        3. Do not regress on previous improvements.
        
        Output the FULL, UPDATED prompt only.
        """
        return self.llm.generate_content(f"{sys_prompt}\n\nCritique:\n{critique}\n\nCurrent Draft:\n{current_draft}")
