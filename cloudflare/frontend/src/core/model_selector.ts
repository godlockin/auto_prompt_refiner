/**
 * Dynamic Model Selector - Intelligent Model Selection Based on Task
 *
 * Features:
 * - Task type-based model selection
 * - Complexity-adjusted models
 * - Cost optimization strategy
 * - Quality assurance strategy
 */

import {
  TaskType,
  TaskComplexity,
  ModelConfig,
  TaskModelStrategy,
} from './types';

// ============================================================================
// Model Configurations
// ============================================================================

export const MODELS: Record<'fast' | 'pro' | 'ultra', ModelConfig> = {
  fast: {
    name: 'gemini-2.5-flash',
    costPerToken: 0.00001,
    latencyFactor: 1.0,
    qualityScore: 0.8,
  },
  pro: {
    name: 'gemini-2.5-pro',
    costPerToken: 0.0001,
    latencyFactor: 2.5,
    qualityScore: 0.95,
  },
  ultra: {
    name: 'gemini-2.5-ultra',
    costPerToken: 0.0005,
    latencyFactor: 5.0,
    qualityScore: 0.99,
  },
};

// ============================================================================
// Task Strategy Definitions
// ============================================================================

interface TaskStrategy {
  description: string;
  useUltraRefiner: boolean;
  expertThreshold: number;
  strategist: 'fast' | 'pro' | 'ultra' | Record<string, 'fast' | 'pro' | 'ultra'>;
  architect: 'fast' | 'pro' | 'ultra' | Record<string, 'fast' | 'pro' | 'ultra'>;
  critic: 'fast' | 'pro' | 'ultra';
  refiner: Record<string, 'fast' | 'pro' | 'ultra'>;
  experts: Record<string, 'fast' | 'pro' | 'ultra'>;
}

export const TASK_STRATEGIES: Record<TaskType, TaskStrategy> = {
  [TaskType.GENERAL]: {
    description: 'General task',
    useUltraRefiner: false,
    expertThreshold: 7,
    strategist: 'fast',
    architect: 'fast',
    critic: 'fast',
    refiner: {
      low: 'fast',
      medium: 'fast',
      high: 'pro',
    },
    experts: {
      code: 'pro',
      security: 'pro',
      performance: 'pro',
      writing: 'fast',
      data: 'pro',
    },
  },
  [TaskType.CODE_GENERATION]: {
    description: 'Code generation task',
    useUltraRefiner: true,
    expertThreshold: 4,
    strategist: 'fast',
    architect: {
      low: 'fast',
      medium: 'pro',
      high: 'pro',
    },
    critic: 'fast',
    refiner: {
      low: 'pro',
      medium: 'pro',
      high: 'ultra',
    },
    experts: {
      code: 'pro',
      security: 'pro',
      performance: 'pro',
    },
  },
  [TaskType.DATA_ANALYSIS]: {
    description: 'Data analysis task',
    useUltraRefiner: false,
    expertThreshold: 5,
    strategist: 'fast',
    architect: 'fast',
    critic: 'fast',
    refiner: {
      low: 'fast',
      medium: 'pro',
      high: 'pro',
    },
    experts: {
      data: 'pro',
    },
  },
  [TaskType.WRITING]: {
    description: 'Writing task',
    useUltraRefiner: false,
    expertThreshold: 6,
    strategist: 'fast',
    architect: 'fast',
    critic: 'fast',
    refiner: {
      low: 'fast',
      medium: 'fast',
      high: 'pro',
    },
    experts: {
      writing: 'fast',
    },
  },
  [TaskType.CREATIVE]: {
    description: 'Creative task',
    useUltraRefiner: true,
    expertThreshold: 7,
    strategist: 'pro',
    architect: 'pro',
    critic: 'fast',
    refiner: {
      low: 'pro',
      medium: 'pro',
      high: 'ultra',
    },
    experts: {
      writing: 'pro',
      creative: 'pro',
    },
  },
  [TaskType.TECHNICAL]: {
    description: 'Technical task',
    useUltraRefiner: true,
    expertThreshold: 5,
    strategist: 'fast',
    architect: 'pro',
    critic: 'fast',
    refiner: {
      low: 'pro',
      medium: 'pro',
      high: 'ultra',
    },
    experts: {
      code: 'pro',
      security: 'pro',
      performance: 'pro',
    },
  },
  [TaskType.DOCUMENTATION]: {
    description: 'Documentation task',
    useUltraRefiner: false,
    expertThreshold: 7,
    strategist: 'fast',
    architect: 'fast',
    critic: 'fast',
    refiner: {
      low: 'fast',
      medium: 'fast',
      high: 'pro',
    },
    experts: {},
  },
};

// ============================================================================
// Model Selector Class
// ============================================================================

export class ModelSelector {
  /**
   * Get complexity level based on score
   */
  static getComplexityLevel(complexity: TaskComplexity): 'low' | 'medium' | 'high' {
    if (complexity.score < 4) return 'low';
    if (complexity.score < 7) return 'medium';
    return 'high';
  }

  /**
   * Get model for a specific agent based on task and complexity
   */
  static getModelForAgent(
    agentName: string,
    taskType: TaskType,
    complexity: TaskComplexity,
  ): 'fast' | 'pro' | 'ultra' {
    const strategy = TASK_STRATEGIES[taskType] || TASK_STRATEGIES[TaskType.GENERAL];
    const complexityLevel = this.getComplexityLevel(complexity);

    // Strategist
    if (agentName === 'strategist') {
      const model = strategy.strategist;
      if (typeof model === 'object') {
        return model[complexityLevel] || 'fast';
      }
      return model;
    }

    // Architect
    if (agentName === 'architect') {
      const model = strategy.architect;
      if (typeof model === 'object') {
        return model[complexityLevel] || 'fast';
      }
      return model;
    }

    // Critic - always use fast to reduce latency
    if (agentName === 'critic') {
      return 'fast';
    }

    // Refiner - based on complexity and task type
    if (agentName === 'refiner') {
      const refinerModels = strategy.refiner;
      let model = refinerModels[complexityLevel] || 'pro';

      // Use ultra for high complexity or special tasks
      if (complexity.score >= 8 || strategy.useUltraRefiner) {
        if (complexityLevel === 'high') {
          return 'ultra';
        }
      }
      return model;
    }

    // Expert Agents
    if (agentName.endsWith('_expert')) {
      const expertType = agentName.replace('_expert', '');
      const expertModels = strategy.experts;

      if (['code', 'security', 'performance', 'data'].includes(expertType)) {
        if (complexityLevel === 'high') {
          return 'pro';
        }
        return expertModels[expertType] || 'fast';
      } else {
        return expertModels[expertType] || 'fast';
      }
    }

    return 'fast';
  }

  /**
   * Get complete model strategy for a task
   */
  static getTaskStrategy(
    taskType: TaskType,
    complexity: TaskComplexity,
  ): TaskModelStrategy {
    const strategy = TASK_STRATEGIES[taskType] || TASK_STRATEGIES[TaskType.GENERAL];
    const complexityLevel = this.getComplexityLevel(complexity);

    const strategist = this.getModelForAgent('strategist', taskType, complexity);
    const architect = this.getModelForAgent('architect', taskType, complexity);
    const critic = this.getModelForAgent('critic', taskType, complexity);
    const refiner = this.getModelForAgent('refiner', taskType, complexity);

    // Determine experts to enable
    const expertThreshold = strategy.expertThreshold;
    const expertModels: Record<string, 'fast' | 'pro' | 'ultra'> = {};

    if (complexity.score >= expertThreshold) {
      const experts = strategy.experts;
      for (const expertName of Object.keys(experts)) {
        expertModels[expertName] = this.getModelForAgent(
          `${expertName}_expert`,
          taskType,
          complexity,
        );
      }
    }

    // Check if ultra should be used
    const useUltra = complexity.score >= 8 || strategy.useUltraRefiner;

    return {
      strategistModel: strategist,
      architectModel: architect,
      criticModel: critic,
      refinerModel: (useUltra && refiner === 'pro') ? 'ultra' : refiner,
      expertModels,
      useUltraForRefiner: useUltra,
    };
  }

  /**
   * Estimate task cost
   */
  static estimateCost(
    taskType: TaskType,
    complexity: TaskComplexity,
    estimatedTokens: number,
  ): {
    totalTokens: number;
    estimatedCostUsd: number;
    phases: Array<{
      phase: string;
      model: string;
      tokens: number;
      cost: number;
    }>;
    strategy: TaskModelStrategy;
  } {
    const strategy = this.getTaskStrategy(taskType, complexity);

    const phases: Array<{
      phase: string;
      model: string;
      tokens: number;
      cost: number;
    }> = [];

    let totalTokens = 0;
    let totalCost = 0;

    // Define phase token distributions
    const phaseConfigs = [
      { name: 'strategist', baseTokens: estimatedTokens * 0.2, model: strategy.strategistModel },
      { name: 'architect', baseTokens: estimatedTokens * 0.3, model: strategy.architectModel },
      { name: 'critic', baseTokens: estimatedTokens * 0.1, model: strategy.criticModel },
      { name: 'refiner', baseTokens: estimatedTokens * 0.5, model: strategy.refinerModel },
    ];

    for (const phase of phaseConfigs) {
      const tokens = Math.floor(phase.baseTokens);
      const modelConfig = MODELS[phase.model];
      const cost = tokens * modelConfig.costPerToken;

      phases.push({
        phase: phase.name,
        model: phase.model,
        tokens,
        cost: Math.round(cost * 1000000) / 1000000,
      });

      totalTokens += tokens;
      totalCost += cost;
    }

    // Add expert phases
    for (const [expert, model] of Object.entries(strategy.expertModels)) {
      const tokens = Math.floor(estimatedTokens * 0.3);
      const modelConfig = MODELS[model];
      const cost = tokens * modelConfig.costPerToken;

      phases.push({
        phase: expert,
        model,
        tokens,
        cost: Math.round(cost * 1000000) / 1000000,
      });

      totalTokens += tokens;
      totalCost += cost;
    }

    return {
      totalTokens,
      estimatedCostUsd: Math.round(totalCost * 1000000) / 1000000,
      phases,
      strategy,
    };
  }

  /**
   * Get recommended default model
   */
  static getRecommendedModel(taskType: TaskType, complexity: TaskComplexity): 'fast' | 'pro' | 'ultra' {
    if (complexity.score >= 8) return 'ultra';
    if (complexity.score >= 5) return 'pro';
    return 'fast';
  }

  /**
   * Determine if experts should be parallelized
   */
  static shouldParallelizeExperts(taskType: TaskType, complexity: TaskComplexity): boolean {
    if (complexity.score >= 6) return true;

    const parallelByDefault = [
      TaskType.CODE_GENERATION,
      TaskType.DATA_ANALYSIS,
      TaskType.TECHNICAL,
    ];

    return parallelByDefault.includes(taskType);
  }
}

// ============================================================================
// Convenience Exports
// ============================================================================

export function selectModel(
  agentName: string,
  taskType: TaskType,
  complexity: TaskComplexity,
): 'fast' | 'pro' | 'ultra' {
  return ModelSelector.getModelForAgent(agentName, taskType, complexity);
}

export function getTaskModelStrategy(
  taskType: TaskType,
  complexity: TaskComplexity,
): TaskModelStrategy {
  return ModelSelector.getTaskStrategy(taskType, complexity);
}

export function estimateCost(
  taskType: TaskType,
  complexity: TaskComplexity,
  tokens: number,
): ReturnType<typeof ModelSelector.estimateCost> {
  return ModelSelector.estimateCost(taskType, complexity, tokens);
}
