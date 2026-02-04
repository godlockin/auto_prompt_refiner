/**
 * Optimized Task Classifier - TypeScript Version
 *
 * Features:
 * - Pre-compiled regex patterns
 * - Weighted keyword scoring
 * - Batch classification support
 */

import {
  TaskType,
  TaskComplexity,
  TaskTypeValue,
} from './types';

// ============================================================================
// Keyword Definitions with Weights
// ============================================================================

interface KeywordWeight {
  pattern: RegExp;
  weight: number;
}

const CODE_KEYWORDS: KeywordWeight[] = [
  { pattern: /\bdef\b/, weight: 2.0 },
  { pattern: /\bfunction\b/, weight: 1.5 },
  { pattern: /\bclass\b/, weight: 2.0 },
  { pattern: /\bimport\b/, weight: 1.0 },
  { pattern: /\bapi\b/, weight: 1.0 },
  { pattern: /\bendpont\b/, weight: 1.5 },
  { pattern: /\bdatabase\b/, weight: 1.5 },
  { pattern: /\bquery\b/, weight: 1.0 },
  { pattern: /\bschema\b/, weight: 1.5 },
  { pattern: /\bpython\b/, weight: 2.0 },
  { pattern: /\bjavascript\b/, weight: 2.0 },
  { pattern: /\btypescript\b/, weight: 2.0 },
  { pattern: /\brust\b/, weight: 2.0 },
  { pattern: /\bgo\b/, weight: 2.0 },
  { pattern: /\bimplement\b/, weight: 1.0 },
  { pattern: /\balgorithm\b/, weight: 1.5 },
];

const WRITING_KEYWORDS: KeywordWeight[] = [
  { pattern: /\bwrite\b/, weight: 1.5 },
  { pattern: /\bcreate\b/, weight: 1.0 },
  { pattern: /\bcompose\b/, weight: 2.0 },
  { pattern: /\bstory\b/, weight: 2.0 },
  { pattern: /\bessay\b/, weight: 2.0 },
  { pattern: /\barticle\b/, weight: 1.5 },
  { pattern: /\bblog\b/, weight: 1.5 },
  { pattern: /\bpost\b/, weight: 1.0 },
  { pattern: /\bcontent\b/, weight: 1.0 },
  { pattern: /\bnarrative\b/, weight: 2.0 },
  { pattern: /\bcharacter\b/, weight: 1.5 },
  { pattern: /\bplot\b/, weight: 1.5 },
];

const DATA_KEYWORDS: KeywordWeight[] = [
  { pattern: /\banalyze\b/, weight: 2.0 },
  { pattern: /\bdata\b/, weight: 1.5 },
  { pattern: /\bstatistics\b/, weight: 2.0 },
  { pattern: /\bmetrics\b/, weight: 2.0 },
  { pattern: /\bvisualization\b/, weight: 2.0 },
  { pattern: /\bchart\b/, weight: 1.5 },
  { pattern: /\bgraph\b/, weight: 1.5 },
  { pattern: /\breport\b/, weight: 1.0 },
  { pattern: /\bsummary\b/, weight: 1.0 },
  { pattern: /\binsights\b/, weight: 2.0 },
  { pattern: /\btrend\b/, weight: 1.5 },
  { pattern: /\bpattern\b/, weight: 1.5 },
];

const CREATIVE_KEYWORDS: KeywordWeight[] = [
  { pattern: /\bcreative\b/, weight: 2.0 },
  { pattern: /\bdesign\b/, weight: 1.5 },
  { pattern: /\bart\b/, weight: 2.0 },
  { pattern: /\bimagine\b/, weight: 2.0 },
  { pattern: /\binnovative\b/, weight: 2.0 },
  { pattern: /\boriginal\b/, weight: 1.5 },
  { pattern: /\bunique\b/, weight: 1.0 },
  { pattern: /\bconcept\b/, weight: 1.5 },
];

const TECHNICAL_KEYWORDS: KeywordWeight[] = [
  { pattern: /\barchitecture\b/, weight: 2.0 },
  { pattern: /\btechnical\b/, weight: 1.5 },
  { pattern: /\bsystem\b/, weight: 1.0 },
  { pattern: /\binfra\b/, weight: 2.0 },
  { pattern: /\bdeployment\b/, weight: 2.0 },
  { pattern: /\bconfig\b/, weight: 1.5 },
  { pattern: /\bintegration\b/, weight: 1.5 },
];

const DOCUMENTATION_KEYWORDS: KeywordWeight[] = [
  { pattern: /\bdocumentation\b/, weight: 2.0 },
  { pattern: /\bdocs\b/, weight: 1.5 },
  { pattern: /\breadme\b/, weight: 2.0 },
  { pattern: /\bmanual\b/, weight: 1.5 },
  { pattern: /\bguide\b/, weight: 1.5 },
  { pattern: /\btutorial\b/, weight: 2.0 },
  { pattern: /\bexplanation\b/, weight: 1.5 },
  { pattern: /\bdescribe\b/, weight: 1.0 },
];

// ============================================================================
// Category Mapping
// ============================================================================

const CATEGORY_MAP: Record<TaskType, KeywordWeight[]> = {
  [TaskType.CODE_GENERATION]: CODE_KEYWORDS,
  [TaskType.WRITING]: WRITING_KEYWORDS,
  [TaskType.DATA_ANALYSIS]: DATA_KEYWORDS,
  [TaskType.CREATIVE]: CREATIVE_KEYWORDS,
  [TaskType.TECHNICAL]: TECHNICAL_KEYWORDS,
  [TaskType.DOCUMENTATION]: DOCUMENTATION_KEYWORDS,
  [TaskType.GENERAL]: [],
};

// ============================================================================
// Task Classifier Class
// ============================================================================

export class TaskClassifier {
  /**
   * Classify a prompt into task type and complexity.
   *
   * @param prompt - The user prompt to classify
   * @returns Tuple of [TaskType, TaskComplexity]
   */
  static classify(prompt: string): { taskType: TaskType; complexity: TaskComplexity } {
    const promptLower = prompt.toLowerCase();
    const words = prompt.split(/\s+/);
    const wordCount = words.length;
    const charCount = prompt.length;

    // Calculate scores for each category
    const scores: Record<TaskType, number> = {
      [TaskType.CODE_GENERATION]: 0,
      [TaskType.WRITING]: 0,
      [TaskType.DATA_ANALYSIS]: 0,
      [TaskType.CREATIVE]: 0,
      [TaskType.TECHNICAL]: 0,
      [TaskType.DOCUMENTATION]: 0,
      [TaskType.GENERAL]: 0,
    };

    // Score each category
    for (const [taskType, keywords] of Object.entries(CATEGORY_MAP)) {
      if (taskType === TaskType.GENERAL) continue;

      for (const kw of keywords) {
        if (kw.pattern.test(promptLower)) {
          scores[taskType as TaskType] += kw.weight;
        }
      }
    }

    // Determine primary task type
    let maxScore = 0;
    let taskType = TaskType.GENERAL;

    for (const [tt, score] of Object.entries(scores)) {
      if (tt === TaskType.GENERAL) continue;
      if (score > maxScore) {
        maxScore = score;
        taskType = tt as TaskType;
      }
    }

    // Calculate complexity score (1-10)
    let complexityScore = 1.0;
    complexityScore += wordCount / 50.0;
    complexityScore += charCount / 500.0;
    complexityScore += scores[taskType];
    complexityScore = Math.min(10.0, Math.max(1.0, complexityScore));

    // Estimate tokens
    const estimatedTokens = Math.floor(wordCount * 1.33);

    // Determine recommended model
    const recommendedModel = complexityScore >= 6.0 ? 'pro' : 'fast';

    // Determine estimated rounds
    const estimatedRounds = complexityScore < 4.0
      ? 1
      : complexityScore < 7.0
        ? 2
        : 3;

    // Determine required special reviews
    const requiresCodeExpert = taskType === TaskType.CODE_GENERATION;
    const requiresSecurityReview = (
      taskType === TaskType.CODE_GENERATION ||
      taskType === TaskType.TECHNICAL ||
      promptLower.includes('api') ||
      promptLower.includes('auth')
    );
    const requiresPerformanceReview = (
      taskType === TaskType.CODE_GENERATION ||
      complexityScore >= 7.0
    );

    const complexity: TaskComplexity = {
      score: Math.floor(complexityScore),
      estimatedTokens,
      recommendedModel,
      estimatedRounds,
      requiresCodeExpert,
      requiresSecurityReview,
      requiresPerformanceReview,
    };

    return { taskType, complexity };
  }

  /**
   * Classify multiple prompts efficiently.
   */
  static classifyBatch(prompts: string[]): Array<{ taskType: TaskType; complexity: TaskComplexity }> {
    return prompts.map(p => this.classify(p));
  }

  /**
   * Get task type as string value.
   */
  static getTaskTypeValue(taskType: TaskType): TaskTypeValue {
    return taskType.valueOf() as TaskTypeValue;
  }
}

// ============================================================================
// Export convenience functions
// ============================================================================

export function classifyTask(prompt: string): { taskType: TaskType; complexity: TaskComplexity } {
  return TaskClassifier.classify(prompt);
}

export function classifyTaskType(prompt: string): TaskType {
  return TaskClassifier.classify(prompt).taskType;
}

export function analyzeComplexity(prompt: string): TaskComplexity {
  return TaskClassifier.classify(prompt).complexity;
}
