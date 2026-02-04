"""
Optimized Task Classifier with pre-compiled patterns.
Replaces regex-based keyword matching with efficient pattern matching.
"""
import re
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
from enum import Enum

from src.core.types import TaskType, TaskComplexity


@dataclass
class KeywordWeight:
    """Keyword with its weight for scoring."""
    pattern: str
    weight: float = 1.0


class TaskClassifier:
    """
    Intelligent task type classifier using pre-compiled patterns.

    Optimizations:
    - Pre-compile all regex patterns at class level
    - Use set operations for fast lookups
    - Calculate scores in single pass
    """

    CODE_KEYWORDS = [
        KeywordWeight(r'\bdef\b', 2.0),
        KeywordWeight(r'\bfunction\b', 1.5),
        KeywordWeight(r'\bclass\b', 2.0),
        KeywordWeight(r'\bimport\b', 1.0),
        KeywordWeight(r'\bapi\b', 1.0),
        KeywordWeight(r'\bendpont\b', 1.5),
        KeywordWeight(r'\bdatabase\b', 1.5),
        KeywordWeight(r'\bquery\b', 1.0),
        KeywordWeight(r'\bschema\b', 1.5),
        KeywordWeight(r'\bpython\b', 2.0),
        KeywordWeight(r'\bjavascript\b', 2.0),
        KeywordWeight(r'\btypescript\b', 2.0),
        KeywordWeight(r'\brust\b', 2.0),
        KeywordWeight(r'\bgo\b', 2.0),
        KeywordWeight(r'\bimplement\b', 1.0),
        KeywordWeight(r'\balgorithm\b', 1.5),
    ]

    WRITING_KEYWORDS = [
        KeywordWeight(r'\bwrite\b', 1.5),
        KeywordWeight(r'\bcreate\b', 1.0),
        KeywordWeight(r'\bcompose\b', 2.0),
        KeywordWeight(r'\bstory\b', 2.0),
        KeywordWeight(r'\bessay\b', 2.0),
        KeywordWeight(r'\barticle\b', 1.5),
        KeywordWeight(r'\bblog\b', 1.5),
        KeywordWeight(r'\bpost\b', 1.0),
        KeywordWeight(r'\bcontent\b', 1.0),
        KeywordWeight(r'\bnarrative\b', 2.0),
        KeywordWeight(r'\bcharacter\b', 1.5),
        KeywordWeight(r'\bplot\b', 1.5),
    ]

    DATA_KEYWORDS = [
        KeywordWeight(r'\banalyze\b', 2.0),
        KeywordWeight(r'\bdata\b', 1.5),
        KeywordWeight(r'\bstatistics\b', 2.0),
        KeywordWeight(r'\bmetrics\b', 2.0),
        KeywordWeight(r'\bvisualization\b', 2.0),
        KeywordWeight(r'\bchart\b', 1.5),
        KeywordWeight(r'\bgraph\b', 1.5),
        KeywordWeight(r'\breport\b', 1.0),
        KeywordWeight(r'\bsummary\b', 1.0),
        KeywordWeight(r'\binsights\b', 2.0),
        KeywordWeight(r'\btrend\b', 1.5),
        KeywordWeight(r'\bpattern\b', 1.5),
    ]

    CREATIVE_KEYWORDS = [
        KeywordWeight(r'\bcreative\b', 2.0),
        KeywordWeight(r'\bdesign\b', 1.5),
        KeywordWeight(r'\bart\b', 2.0),
        KeywordWeight(r'\bimagine\b', 2.0),
        KeywordWeight(r'\binnovative\b', 2.0),
        KeywordWeight(r'\boriginal\b', 1.5),
        KeywordWeight(r'\bunique\b', 1.0),
        KeywordWeight(r'\bconcept\b', 1.5),
    ]

    TECHNICAL_KEYWORDS = [
        KeywordWeight(r'\barchitecture\b', 2.0),
        KeywordWeight(r'\btechnical\b', 1.5),
        KeywordWeight(r'\bsystem\b', 1.0),
        KeywordWeight(r'\binfra\b', 2.0),
        KeywordWeight(r'\bdeployment\b', 2.0),
        KeywordWeight(r'\bconfig\b', 1.5),
        KeywordWeight(r'\bintegration\b', 1.5),
    ]

    DOCUMENTATION_KEYWORDS = [
        KeywordWeight(r'\bdocumentation\b', 2.0),
        KeywordWeight(r'\bdocs\b', 1.5),
        KeywordWeight(r'\breadme\b', 2.0),
        KeywordWeight(r'\bmanual\b', 1.5),
        KeywordWeight(r'\bguide\b', 1.5),
        KeywordWeight(r'\btutorial\b', 2.0),
        KeywordWeight(r'\bexplanation\b', 1.5),
        KeywordWeight(r'\bdescribe\b', 1.0),
    ]

    _CATEGORY_PATTERNS: Dict[TaskType, List[KeywordWeight]] = {}
    _COMPILED_PATTERNS: Dict[str, re.Pattern] = {}
    _CATEGORY_MAP: Dict[TaskType, str] = {}  # Maps TaskType to pattern prefix

    @classmethod
    def _ensure_compiled(cls) -> None:
        """Pre-compile all regex patterns at class level."""
        if cls._CATEGORY_PATTERNS:
            return

        # Define category mappings (TaskType -> pattern prefix)
        cls._CATEGORY_MAP = {
            TaskType.CODE_GENERATION: "code",
            TaskType.WRITING: "writing",
            TaskType.DATA_ANALYSIS: "data",
            TaskType.CREATIVE: "creative",
            TaskType.TECHNICAL: "technical",
            TaskType.DOCUMENTATION: "docs",
        }

        cls._CATEGORY_PATTERNS = {
            TaskType.CODE_GENERATION: cls.CODE_KEYWORDS,
            TaskType.WRITING: cls.WRITING_KEYWORDS,
            TaskType.DATA_ANALYSIS: cls.DATA_KEYWORDS,
            TaskType.CREATIVE: cls.CREATIVE_KEYWORDS,
            TaskType.TECHNICAL: cls.TECHNICAL_KEYWORDS,
            TaskType.DOCUMENTATION: cls.DOCUMENTATION_KEYWORDS,
        }

        for category, keywords in cls._CATEGORY_PATTERNS.items():
            prefix = cls._CATEGORY_MAP[category]
            for kw in keywords:
                cls._COMPILED_PATTERNS[f"{prefix}_{kw.pattern}"] = re.compile(kw.pattern)

    @classmethod
    def classify(cls, prompt: str) -> Tuple[TaskType, TaskComplexity]:
        """
        Classify task type and assess complexity in O(n) time.

        Args:
            prompt: The user prompt to classify

        Returns:
            Tuple of (TaskType, TaskComplexity)
        """
        cls._ensure_compiled()

        prompt_lower = prompt.lower()
        words = prompt.split()
        word_count = len(words)
        char_count = len(prompt)

        scores: Dict[TaskType, float] = {
            TaskType.CODE_GENERATION: 0.0,
            TaskType.WRITING: 0.0,
            TaskType.DATA_ANALYSIS: 0.0,
            TaskType.CREATIVE: 0.0,
            TaskType.TECHNICAL: 0.0,
            TaskType.DOCUMENTATION: 0.0,
        }

        for task_type, keywords in cls._CATEGORY_PATTERNS.items():
            category = cls._CATEGORY_MAP[task_type]
            for kw in keywords:
                pattern = cls._COMPILED_PATTERNS.get(f"{category}_{kw.pattern}")
                if pattern and pattern.search(prompt_lower):
                    scores[task_type] += kw.weight

        max_score = max(scores.values())
        if max_score <= 0:
            task_type = TaskType.GENERAL
        else:
            task_type = max(scores.items(), key=lambda x: x[1])[0]

        complexity_score = 1.0
        complexity_score += word_count / 50.0
        complexity_score += char_count / 500.0
        complexity_score += scores.get(task_type, 0)
        complexity_score = min(10.0, max(1.0, complexity_score))

        estimated_tokens = int(word_count * 1.33)
        recommended_model = "pro" if complexity_score >= 6.0 else "fast"
        estimated_rounds = 1 if complexity_score < 4.0 else 2 if complexity_score < 7.0 else 3

        requires_code_expert = task_type == TaskType.CODE_GENERATION
        requires_security_review = (
            task_type == TaskType.CODE_GENERATION or
            task_type == TaskType.TECHNICAL or
            "api" in prompt_lower or
            "auth" in prompt_lower
        )
        requires_performance_review = (
            task_type == TaskType.CODE_GENERATION or
            complexity_score >= 7.0
        )

        complexity = TaskComplexity(
            score=int(complexity_score),
            estimated_tokens=estimated_tokens,
            recommended_model=recommended_model,
            estimated_rounds=estimated_rounds,
            requires_code_expert=requires_code_expert,
            requires_security_review=requires_security_review,
            requires_performance_review=requires_performance_review,
        )

        return task_type, complexity

    @classmethod
    def classify_batch(cls, prompts: List[str]) -> List[Tuple[TaskType, TaskComplexity]]:
        """Classify multiple prompts efficiently."""
        return [cls.classify(p) for p in prompts]
