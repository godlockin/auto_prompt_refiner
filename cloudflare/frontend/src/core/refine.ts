/**
 * Prompt Refiner - Main Processing Logic
 *
 * Implements the complete refinement workflow:
 * 1. Task analysis and classification
 * 2. Dynamic agent orchestration with model selection
 * 3. Multi-expert parallel processing
 * 4. Critique and refinement cycles
 * 5. Result output
 */

import {
  TaskType,
  TaskComplexity,
  AgentConfig,
  TaskContext,
  RefinementResult,
  ProgressEvent,
  TaskTypeValue,
} from './types';
import { TaskClassifier } from './classifier';
import { DynamicAgentOrchestrator, getAgentsForTask } from './orchestrator';
import { ModelSelector, selectModel, getTaskModelStrategy } from './model_selector';

// ============================================================================
// Prompts Loading
// ============================================================================

interface PromptConfig {
  system: string;
  user_template: string;
}

const PROMPTS_CACHE: Record<string, PromptConfig> | null = null;

async function loadPrompts(): Promise<Record<string, PromptConfig>> {
  if (PROMPTS_CACHE) return PROMPTS_CACHE;

  try {
    const response = await fetch('/functions/prompts.json');
    if (!response.ok) throw new Error('Failed to load prompts');
    const prompts = await response.json();
    return prompts;
  } catch (error) {
    console.error('Failed to load prompts:', error);
    return {};
  }
}

// ============================================================================
// Prompt Refiner Class
// ============================================================================

export class PromptRefiner {
  private prompts: Record<string, PromptConfig> | null = null;
  private classifier: TaskClassifier;
  private orchestrator: DynamicAgentOrchestrator;

  constructor() {
    this.classifier = new TaskClassifier();
    this.orchestrator = new DynamicAgentOrchestrator();
  }

  private async getPrompts(): Promise<Record<string, PromptConfig>> {
    if (!this.prompts) {
      this.prompts = await loadPrompts();
    }
    return this.prompts;
  }

  async analyzeTask(prompt: string): Promise<TaskContext> {
    const prompts = await this.getPrompts();
    const { taskType, complexity } = this.classifier.classify(prompt);

    const agents = getAgentsForTask(taskType, complexity, prompt);

    return {
      taskType,
      complexity,
      agents,
      originalPrompt: prompt,
    };
  }

  async runRefinement(
    userPrompt: string,
    onProgress?: (event: ProgressEvent) => void,
  ): Promise<RefinementResult> {
    const context = await this.analyzeTask(userPrompt);
    const history: Array<{ role: string; content: string }> = [];
    let finalDraft = '';

    if (onProgress) {
      for await (const event of this.runRefinementStream(context)) {
        onProgress(event);
      }
    } else {
      finalDraft = await this.runRefinementSync(context, history);
    }

    const enabledAgents = context.agents.filter(a => a.enabled).map(a => a.name);

    return {
      originalPrompt: userPrompt,
      finalPrompt: finalDraft,
      taskType: context.taskType.value as string,
      complexity: context.complexity.score,
      modelUsed: context.complexity.recommendedModel,
      roundsCompleted: 0,
      agentsUsed: enabledAgents,
      history,
    };
  }

  async *runRefinementStream(
    context: TaskContext,
  ): AsyncGenerator<ProgressEvent, void, unknown> {
    const prompt = context.originalPrompt;
    const prompts = await this.getPrompts();

    yield {
      phase: 'analyze',
      message: 'Analyzing task type and complexity...',
      data: {
        taskType: context.taskType.value as string,
        complexity: context.complexity.score,
        model: context.complexity.recommendedModel,
        rounds: context.complexity.estimatedRounds,
      },
    };

    const enabledExperts = context.agents
      .filter(a => a.enabled && a.agentType !== 'core')
      .map(a => a.name);

    if (enabledExperts.length > 0) {
      yield {
        phase: 'select',
        message: `Activating expert agents: ${enabledExperts.join(', ')}`,
        data: { experts: enabledExperts },
      };
    }

    const strategy = await this.executeAgent(
      'strategist',
      prompt,
      '',
      context,
      prompts,
    );

    yield {
      phase: 'strategy',
      message: `Strategy: ${strategy.substring(0, 100)}...`,
      data: { strategy },
    };

    const draft = await this.executeAgent(
      'architect',
      prompt,
      strategy,
      context,
      prompts,
    );

    yield {
      phase: 'draft',
      message: `Draft created (${draft.length} chars)`,
      data: { draftLength: draft.length },
    };

    const expertReviews: Record<string, string> = {};

    for (const agent of context.agents) {
      if (['code', 'security', 'performance', 'writing', 'data'].includes(agent.agentType)) {
        if (!agent.enabled) continue;

        yield {
          phase: 'review',
          message: `${agent.name} review...`,
          data: { agent: agent.name },
        };

        const review = await this.executeAgent(
          agent.name,
          prompt,
          draft,
          context,
          prompts,
        );
        expertReviews[agent.name] = review;
      }
    }

    const critique = await this.executeAgent(
      'critic',
      this.buildCriticInput(prompt, draft, expertReviews),
      '',
      context,
      prompts,
    );

    yield {
      phase: 'critique',
      message: 'Critique complete',
      data: { critiqueLength: critique.length },
    };

    if (critique.includes('NO_ISSUES_FOUND')) {
      yield {
        phase: 'complete',
        message: 'Perfection achieved! No issues found.',
        data: { finalDraft: draft, converged: true },
      };
      return;
    }

    let currentDraft = draft;

    for (let roundNum = 1; roundNum <= context.complexity.estimatedRounds; roundNum++) {
      yield {
        phase: 'refine',
        message: `Round ${roundNum} refinement...`,
        data: { round: roundNum },
      };

      currentDraft = await this.executeAgent(
        'refiner',
        `Critique:\n${critique}\n\nCurrent Draft:\n${currentDraft}`,
        '',
        context,
        prompts,
      );

      yield {
        phase: 'verify',
        message: `Round ${roundNum} verification...`,
        data: { draftLength: currentDraft.length },
      };

      const newCritique = await this.executeAgent(
        'critic',
        `${prompt}\n\n${currentDraft}`,
        '',
        context,
        prompts,
      );

      if (newCritique.includes('NO_ISSUES_FOUND')) {
        yield {
          phase: 'complete',
          message: `Round ${roundNum} passed!`,
          data: { finalDraft: currentDraft, converged: true },
        };
        return;
      }

      if (roundNum === context.complexity.estimatedRounds) {
        yield {
          phase: 'complete',
          message: 'Maximum rounds reached. Finalizing.',
          data: { finalDraft: currentDraft, converged: false },
        };
        return;
      }
    }

    yield {
      phase: 'complete',
      message: 'Process complete',
      data: { finalDraft: currentDraft, converged: false },
    };
  }

  async runRefinementSync(
    context: TaskContext,
    history: Array<{ role: string; content: string }>,
  ): Promise<string> {
    const prompt = context.originalPrompt;
    const prompts = await this.getPrompts();

    const strategy = await this.executeAgent('strategist', prompt, '', context, prompts);
    history.push({ role: 'strategist', content: strategy });

    const draft = await this.executeAgent('architect', prompt, strategy, context, prompts);
    history.push({ role: 'architect', content: draft });

    const expertReviews: Record<string, string> = {};

    for (const agent of context.agents) {
      if (['code', 'security', 'performance', 'writing', 'data'].includes(agent.agentType)) {
        if (!agent.enabled) continue;

        const review = await this.executeAgent(
          agent.name,
          prompt,
          draft,
          context,
          prompts,
        );
        expertReviews[agent.name] = review;
      }
    }

    const critique = await this.executeAgent(
      'critic',
      this.buildCriticInput(prompt, draft, expertReviews),
      '',
      context,
      prompts,
    );
    history.push({ role: 'critic', content: critique });

    if (critique.includes('NO_ISSUES_FOUND')) {
      return draft;
    }

    let currentDraft = draft;

    for (let roundNum = 1; roundNum <= context.complexity.estimatedRounds; roundNum++) {
      currentDraft = await this.executeAgent(
        'refiner',
        `Critique:\n${critique}\n\nCurrent Draft:\n${currentDraft}`,
        '',
        context,
        prompts,
      );

      const newCritique = await this.executeAgent(
        'critic',
        `${prompt}\n\n${currentDraft}`,
        '',
        context,
        prompts,
      );

      if (newCritique.includes('NO_ISSUES_FOUND')) {
        break;
      }
    }

    return currentDraft;
  }

  private buildCriticInput(
    prompt: string,
    draft: string,
    expertReviews: Record<string, string>,
  ): string {
    let criticInput = `Original Request:\n${prompt}\n\nCurrent Draft:\n${draft}`;

    if (Object.keys(expertReviews).length > 0) {
      criticInput += '\n\nExpert Reviews:\n' +
        Object.entries(expertReviews)
          .map(([k, v]) => `${k}: ${v}`)
          .join('\n');
    }

    return criticInput;
  }

  private async executeAgent(
    agentName: string,
    userInput: string,
    strategy: string,
    context: TaskContext,
    prompts: Record<string, PromptConfig>,
  ): Promise<string> {
    const promptConfig = prompts[agentName];
    if (!promptConfig) {
      console.warn(`No prompt config for agent: ${agentName}`);
      return '';
    }

    const systemPrompt = promptConfig.system;
    const template = promptConfig.user_template;

    let promptText: string;

    if (agentName === 'strategist') {
      promptText = `${systemPrompt}\n\nUser Input: ${userInput}`;
    } else if (agentName === 'architect') {
      promptText = `${systemPrompt}\n\nStrategy:\n${strategy}\n\nOriginal Request:\n${userInput}`;
    } else if (agentName === 'critic' || agentName === 'refiner') {
      promptText = `${systemPrompt}\n\n${userInput}`;
    } else {
      promptText = `${systemPrompt}\n\nTask:\n${userInput}\n\nContext:\n${context.originalPrompt}`;
    }

    const model = selectModel(agentName, context.taskType, context.complexity);

    try {
      return await this.callLLM(promptText, model);
    } catch (error) {
      console.error(`Agent ${agentName} failed:`, error);
      return `[Error in ${agentName}: ${error instanceof Error ? error.message : 'Unknown error'}]`;
    }
  }

  private async callLLM(prompt: string, model: string): Promise<string> {
    const response = await fetch('/functions/api/vertex', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, model }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`LLM call failed: ${error}`);
    }

    const data = await response.json();
    return data.result || data.text || '';
  }

  async healthCheck(): Promise<{ status: string; promptsLoaded: boolean }> {
    const prompts = await this.getPrompts();
    return {
      status: 'healthy',
      promptsLoaded: Object.keys(prompts).length > 0,
    };
  }
}

// ============================================================================
// Factory Function
// ============================================================================

export function createRefiner(): PromptRefiner {
  return new PromptRefiner();
}

// ============================================================================
// Convenience Functions
// ============================================================================

export async function analyzeTask(prompt: string): Promise<TaskContext> {
  const refiner = createRefiner();
  return refiner.analyzeTask(prompt);
}

export async function refinePrompt(
  prompt: string,
  onProgress?: (event: ProgressEvent) => void,
): Promise<RefinementResult> {
  const refiner = createRefiner();
  return refiner.runRefinement(prompt, onProgress);
}

export function getModelForAgent(
  agentName: string,
  taskType: TaskType,
  complexity: TaskComplexity,
): 'fast' | 'pro' | 'ultra' {
  return selectModel(agentName, taskType, complexity);
}

export function getStrategy(
  taskType: TaskType,
  complexity: TaskComplexity,
) {
  return getTaskModelStrategy(taskType, complexity);
}
