"""
Dynamic Model Selector - 根据任务智能选择模型

Features:
- 根据任务类型选择模型
- 根据复杂度调整模型
- 成本优化策略
- 质量保证策略
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from src.core.types import TaskType, TaskComplexity


class Model(Enum):
    """Available models."""
    FAST = "fast"      # 快速模型，成本低
    PRO = "pro"        # 专业模型，质量高
    ULTRA = "ultra"    # 顶级模型，最复杂任务


@dataclass
class ModelConfig:
    """Model configuration."""
    name: str
    cost_per_token: float
    latency_factor: float
    quality_score: float


@dataclass
class TaskModelStrategy:
    """Model selection strategy for a task."""
    strategist_model: str
    architect_model: str
    critic_model: str
    refiner_model: str
    expert_models: Dict[str, str]
    use_ultra_for_refiner: bool


class ModelSelector:
    """
    根据任务智能选择模型的策略引擎

    策略原则:
    1. 简单任务用fast，复杂任务用pro
    2. 核心Agent(Strategist/Architect/Critic)多用fast
    3. 关键Agent(Refiner/Experts)根据任务类型决定
    4. 高复杂度任务开启ultra模式
    """

    # 模型配置
    MODELS = {
        "fast": ModelConfig(
            name="gemini-2.5-flash",
            cost_per_token=0.00001,
            latency_factor=1.0,
            quality_score=0.8,
        ),
        "pro": ModelConfig(
            name="gemini-2.5-pro",
            cost_per_token=0.0001,
            latency_factor=2.5,
            quality_score=0.95,
        ),
        "ultra": ModelConfig(
            name="gemini-2.5-ultra",
            cost_per_token=0.0005,
            latency_factor=5.0,
            quality_score=0.99,
        ),
    }

    # 任务类型 -> 模型映射策略
    TASK_STRATEGIES: Dict[TaskType, Dict[str, Any]] = {
        TaskType.GENERAL: {
            "description": "通用任务",
            "use_ultra_refiner": False,
            "expert_threshold": 7,  # 复杂度>=7才启用专家
            "strategist": "fast",
            "architect": "fast",
            "critic": "fast",
            "refiner": {
                "low": "fast",
                "medium": "fast",
                "high": "pro",
            },
            "experts": {
                "code": "pro",
                "security": "pro",
                "performance": "pro",
                "writing": "fast",
                "data": "pro",
            }
        },
        TaskType.CODE_GENERATION: {
            "description": "代码生成任务",
            "use_ultra_refiner": True,
            "expert_threshold": 4,  # 代码任务更早启用专家
            "strategist": "fast",
            "architect": {
                "low": "fast",
                "medium": "pro",
                "high": "pro",
            },
            "critic": "fast",
            "refiner": {
                "low": "pro",
                "medium": "pro",
                "high": "ultra",
            },
            "experts": {
                "code": "pro",
                "security": "pro",
                "performance": "pro",
            }
        },
        TaskType.DATA_ANALYSIS: {
            "description": "数据分析任务",
            "use_ultra_refiner": False,
            "expert_threshold": 5,
            "strategist": "fast",
            "architect": "fast",
            "critic": "fast",
            "refiner": {
                "low": "fast",
                "medium": "pro",
                "high": "pro",
            },
            "experts": {
                "data": "pro",
            }
        },
        TaskType.WRITING: {
            "description": "写作任务",
            "use_ultra_refiner": False,
            "expert_threshold": 6,
            "strategist": "fast",
            "architect": "fast",
            "critic": "fast",
            "refiner": {
                "low": "fast",
                "medium": "fast",
                "high": "pro",
            },
            "experts": {
                "writing": "fast",
            }
        },
        TaskType.CREATIVE: {
            "description": "创意任务",
            "use_ultra_refiner": True,
            "expert_threshold": 7,
            "strategist": "pro",  # 创意任务需要更好的策略
            "architect": "pro",
            "critic": "fast",
            "refiner": {
                "low": "pro",
                "medium": "pro",
                "high": "ultra",
            },
            "experts": {
                "writing": "pro",
                "creative": "pro",
            }
        },
        TaskType.TECHNICAL: {
            "description": "技术任务",
            "use_ultra_refiner": True,
            "expert_threshold": 5,
            "strategist": "fast",
            "architect": "pro",
            "critic": "fast",
            "refiner": {
                "low": "pro",
                "medium": "pro",
                "high": "ultra",
            },
            "experts": {
                "code": "pro",
                "security": "pro",
                "performance": "pro",
            }
        },
        TaskType.DOCUMENTATION: {
            "description": "文档任务",
            "use_ultra_refiner": False,
            "expert_threshold": 7,
            "strategist": "fast",
            "architect": "fast",
            "critic": "fast",
            "refiner": {
                "low": "fast",
                "medium": "fast",
                "high": "pro",
            },
            "experts": {}
        },
    }

    @classmethod
    def get_complexity_level(cls, complexity: TaskComplexity) -> str:
        """根据复杂度评分获取复杂度等级"""
        score = complexity.score
        if score < 4:
            return "low"
        elif score < 7:
            return "medium"
        else:
            return "high"

    @classmethod
    def get_model_for_agent(
        cls,
        agent_name: str,
        task_type: TaskType,
        complexity: TaskComplexity,
    ) -> str:
        """
        根据任务和复杂度为特定Agent选择模型

        Args:
            agent_name: Agent名称
            task_type: 任务类型
            complexity: 复杂度

        Returns:
            模型名称 (fast/pro/ultra)
        """
        strategy = cls.TASK_STRATEGIES.get(task_type, cls.TASK_STRATEGIES[TaskType.GENERAL])
        complexity_level = cls.get_complexity_level(complexity)

        # Strategist
        if agent_name == "strategist":
            model = strategy.get("strategist", "fast")
            if isinstance(model, dict):
                return model.get(complexity_level, "fast")
            return model

        # Architect
        if agent_name == "architect":
            model = strategy.get("architect", "fast")
            if isinstance(model, dict):
                return model.get(complexity_level, "fast")
            return model

        # Critic - 始终用fast，减少延迟
        if agent_name == "critic":
            return "fast"

        # Refiner - 根据复杂度和任务类型
        if agent_name == "refiner":
            refiner_models = strategy.get("refiner", {})
            if isinstance(refiner_models, dict):
                model = refiner_models.get(complexity_level, "pro")
                # 复杂度>=8或创意任务用ultra
                if complexity.score >= 8 or strategy.get("use_ultra_refiner"):
                    if complexity_level == "high":
                        return "ultra"
                return model
            return refiner_models

        # Expert Agents
        if agent_name.endswith("_expert"):
            expert_type = agent_name.replace("_expert", "")
            expert_models = strategy.get("experts", {})

            # 默认使用fast，除非是特定专家
            if expert_type in ["code", "security", "performance", "data"]:
                # 高复杂度时升级为pro
                if complexity_level == "high":
                    return "pro"
                return expert_models.get(expert_type, "fast")
            else:
                return expert_models.get(expert_type, "fast")

        return "fast"

    @classmethod
    def get_task_strategy(
        cls,
        task_type: TaskType,
        complexity: TaskComplexity,
    ) -> TaskModelStrategy:
        """
        获取任务的完整模型策略

        Args:
            task_type: 任务类型
            complexity: 复杂度

        Returns:
            TaskModelStrategy - 包含所有Agent的模型配置
        """
        strategy = cls.TASK_STRATEGIES.get(task_type, cls.TASK_STRATEGIES[TaskType.GENERAL])
        complexity_level = cls.get_complexity_level(complexity)

        # 获取每个Agent的模型
        strategist = cls.get_model_for_agent("strategist", task_type, complexity)
        architect = cls.get_model_for_agent("architect", task_type, complexity)
        critic = cls.get_model_for_agent("critic", task_type, complexity)
        refiner = cls.get_model_for_agent("refiner", task_type, complexity)

        # 确定需要启用的专家及其模型
        expert_threshold = strategy.get("expert_threshold", 7)
        expert_models = {}

        if complexity.score >= expert_threshold:
            experts = strategy.get("experts", {})
            for expert_name in ["code", "security", "performance", "writing", "data"]:
                expert_models[expert_name] = cls.get_model_for_agent(
                    f"{expert_name}_expert", task_type, complexity
                )

        # 检查是否使用ultra
        use_ultra = complexity.score >= 8 or strategy.get("use_ultra_refiner")

        return TaskModelStrategy(
            strategist_model=strategist,
            architect_model=architect,
            critic_model=critic,
            refiner_model="ultra" if use_ultra and refiner == "pro" else refiner,
            expert_models=expert_models,
        )

    @classmethod
    def estimate_cost(
        cls,
        task_type: TaskType,
        complexity: TaskComplexity,
        estimated_tokens: int,
    ) -> Dict[str, Any]:
        """
        估算任务成本

        Args:
            task_type: 任务类型
            complexity: 复杂度
            estimated_tokens: 预估token数

        Returns:
            成本估算信息
        """
        strategy = cls.get_task_strategy(task_type, complexity)

        # 估算各阶段token
        phases = {
            "strategist": estimated_tokens * 0.2,
            "architect": estimated_tokens * 0.3,
            "critic": estimated_tokens * 0.1,
            "refiner": estimated_tokens * 0.5,
        }

        # 添加专家token
        for expert in strategy.expert_models:
            phases[expert] = estimated_tokens * 0.3

        # 计算成本
        total_cost = 0.0
        total_tokens = 0
        phase_details = []

        for phase, tokens in phases.items():
            if phase in ["strategist", "architect", "critic"]:
                model = cls.get_model_for_agent(phase, task_type, complexity)
            elif phase == "refiner":
                model = strategy.refiner_model
            else:
                model = strategy.expert_models.get(phase, "fast")

            config = cls.MODELS.get(model, cls.MODELS["fast"])
            phase_cost = tokens * config.cost_per_token

            phase_details.append({
                "phase": phase,
                "model": model,
                "tokens": int(tokens),
                "cost": round(phase_cost, 6),
            })

            total_cost += phase_cost
            total_tokens += int(tokens)

        return {
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(total_cost, 6),
            "phases": phase_details,
            "strategy": {
                "strategist": strategy.strategist_model,
                "architect": strategy.architect_model,
                "critic": strategy.critic_model,
                "refiner": strategy.refiner_model,
                "experts": strategy.expert_models,
            }
        }

    @classmethod
    def get_recommended_model(cls, task_type: TaskType, complexity: TaskComplexity) -> str:
        """
        获取推荐的默认模型

        Args:
            task_type: 任务类型
            complexity: 复杂度

        Returns:
            推荐模型
        """
        if complexity.score >= 8:
            return "ultra"
        elif complexity.score >= 5:
            return "pro"
        else:
            return "fast"

    @classmethod
    def should_parallelize_experts(
        cls,
        task_type: TaskType,
        complexity: TaskComplexity,
    ) -> bool:
        """
        判断是否应该并行执行专家

        Args:
            task_type: 任务类型
            complexity: 复杂度

        Returns:
            是否并行
        """
        # 高复杂度任务启用并行
        if complexity.score >= 6:
            return True

        # 某些任务类型默认并行
        parallel_by_default = [
            TaskType.CODE_GENERATION,
            TaskType.DATA_ANALYSIS,
            TaskType.TECHNICAL,
        ]

        return task_type in parallel_by_default


# 便捷函数
def select_model(agent_name: str, task_type: TaskType, complexity: TaskComplexity) -> str:
    """为Agent选择合适的模型"""
    return ModelSelector.get_model_for_agent(agent_name, task_type, complexity)


def get_task_model_strategy(task_type: TaskType, complexity: TaskComplexity) -> TaskModelStrategy:
    """获取任务的完整模型策略"""
    return ModelSelector.get_task_model_strategy(task_type, complexity)


def estimate_cost(task_type: TaskType, complexity: TaskComplexity, tokens: int) -> Dict[str, Any]:
    """估算任务成本"""
    return ModelSelector.estimate_cost(task_type, complexity, tokens)
