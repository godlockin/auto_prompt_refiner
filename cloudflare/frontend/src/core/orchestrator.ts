/**
 * Dynamic Agent Orchestrator - TypeScript Version
 *
 * Features:
 * - Priority-based agent scheduling
 * - Trigger-based activation
 * - No hardcoded core agent order
 */

import {
  TaskType,
  TaskComplexity,
  AgentConfig,
  AgentType,
  TaskTypeValue,
} from './types';

// ============================================================================
// Agent Trigger Conditions
// ============================================================================

interface AgentTrigger {
  taskTypes?: TaskTypeValue[];
  requireSecurityReview?: boolean;
  requirePerformanceReview?: boolean;
}

// ============================================================================
// Agent Definition
// ============================================================================

interface AgentDefinition {
  name: string;
  agentType: AgentType;
  model: 'fast' | 'pro' | 'ultra';
  priority: number;
  trigger?: AgentTrigger;
}

// ============================================================================
// Agent Registry
// ============================================================================

const AGENT_REGISTRY: Record<string, AgentDefinition> = {
  // Core agents (always active, sorted by priority)
  strategist: {
    name: 'strategist',
    agentType: AgentType.CORE,
    model: 'fast',
    priority: 10,
  },
  architect: {
    name: 'architect',
    agentType: AgentType.CORE,
    model: 'fast',
    priority: 20,
  },
  critic: {
    name: 'critic',
    agentType: AgentType.CORE,
    model: 'fast',
    priority: 30,
  },
  refiner: {
    name: 'refiner',
    agentType: AgentType.CORE,
    model: 'pro',
    priority: 40,
  },

  // Expert agents (conditionally activated)
  code_expert: {
    name: 'code_expert',
    agentType: AgentType.CODE,
    model: 'pro',
    priority: 50,
    trigger: {
      taskTypes: ['code', 'technical'],
    },
  },
  security_expert: {
    name: 'security_expert',
    agentType: AgentType.SECURITY,
    model: 'pro',
    priority: 60,
    trigger: {
      requireSecurityReview: true,
    },
  },
  performance_expert: {
    name: 'performance_expert',
    agentType: AgentType.PERFORMANCE,
    model: 'pro',
    priority: 70,
    trigger: {
      requirePerformanceReview: true,
    },
  },
  style_expert: {
    name: 'style_expert',
    agentType: AgentType.WRITING,
    model: 'fast',
    priority: 80,
    trigger: {
      taskTypes: ['writing', 'creative'],
    },
  },
  data_expert: {
    name: 'data_expert',
    agentType: AgentType.DATA,
    model: 'pro',
    priority: 90,
    trigger: {
      taskTypes: ['analysis'],
    },
  },
};

// ============================================================================
// Orchestrator Class
// ============================================================================

export class DynamicAgentOrchestrator {
  /**
   * Get all agents for a task, sorted by priority.
   *
   * @param taskType - The classified task type
   * @param complexity - The assessed complexity
   * @param prompt - Original prompt for additional context
   * @returns Array of AgentConfig sorted by priority
   */
  static getAgentsForTask(
    taskType: TaskType,
    complexity: TaskComplexity,
    prompt: string = '',
  ): AgentConfig[] {
    const promptLower = prompt.toLowerCase();
    const agents: AgentConfig[] = [];

    for (const [name, def] of Object.entries(AGENT_REGISTRY)) {
      if (this.shouldIncludeAgent(def, taskType, complexity, promptLower)) {
        agents.push({
          name: def.name,
          agentType: def.agentType.valueOf() as AgentConfig['agentType'],
          systemPrompt: '', // Loaded from prompts.json
          model: def.model,
          enabled: true,
          priority: def.priority,
        });
      }
    }

    // Sort by priority
    return agents.sort((a, b) => a.priority - b.priority);
  }

  /**
   * Determine if an agent should be included for this task.
   */
  private static shouldIncludeAgent(
    def: AgentDefinition,
    taskType: TaskType,
    complexity: TaskComplexity,
    promptLower: string,
  ): boolean {
    const trigger = def.trigger;

    if (!trigger) {
      return true; // Core agents always included
    }

    if (trigger.taskTypes && trigger.taskTypes.length > 0) {
      const taskTypeValue = taskType.valueOf() as TaskTypeValue;
      if (!trigger.taskTypes.includes(taskTypeValue)) {
        return false;
      }
    }

    if (trigger.requireSecurityReview && !complexity.requiresSecurityReview) {
      return false;
    }

    if (trigger.requirePerformanceReview && !complexity.requiresPerformanceReview) {
      return false;
    }

    return true;
  }

  /**
   * Get only core agents (strategist, architect, critic, refiner).
   */
  static getCoreAgents(): AgentConfig[] {
    return Object.values(AGENT_REGISTRY)
      .filter(def => def.agentType === AgentType.CORE)
      .map(def => ({
        name: def.name,
        agentType: def.agentType.valueOf() as AgentConfig['agentType'],
        systemPrompt: '',
        model: def.model,
        enabled: true,
        priority: def.priority,
      }))
      .sort((a, b) => a.priority - b.priority);
  }

  /**
   * Get only expert agents (non-core).
   */
  static getExpertAgents(): AgentConfig[] {
    return Object.values(AGENT_REGISTRY)
      .filter(def => def.agentType !== AgentType.CORE)
      .map(def => ({
        name: def.name,
        agentType: def.agentType.valueOf() as AgentConfig['agentType'],
        systemPrompt: '',
        model: def.model,
        enabled: true,
        priority: def.priority,
      }))
      .sort((a, b) => a.priority - b.priority);
  }

  /**
   * Get list of all registered agent names.
   */
  static getAllAgentNames(): string[] {
    return Object.keys(AGENT_REGISTRY);
  }

  /**
   * Get agent definition by name.
   */
  static getAgentDefinition(name: string): AgentDefinition | undefined {
    return AGENT_REGISTRY[name];
  }
}

// ============================================================================
// Export convenience functions
// ============================================================================

export function getAgentsForTask(
  taskType: TaskType,
  complexity: TaskComplexity,
  prompt?: string,
): AgentConfig[] {
  return DynamicAgentOrchestrator.getAgentsForTask(taskType, complexity, prompt);
}

export function getCoreAgents(): AgentConfig[] {
  return DynamicAgentOrchestrator.getCoreAgents();
}

export function getExpertAgents(): AgentConfig[] {
  return DynamicAgentOrchestrator.getExpertAgents();
}
