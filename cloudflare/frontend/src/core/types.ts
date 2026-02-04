/**
 * Shared Type Definitions for Prompt Refiner
 * Used by both Python and TypeScript implementations
 */

// ============================================================================
// Task Types
// ============================================================================

export type TaskTypeValue =
  | 'code'
  | 'writing'
  | 'analysis'
  | 'creative'
  | 'general'
  | 'technical'
  | 'documentation';

export enum TaskType {
  CODE_GENERATION = 'code',
  WRITING = 'writing',
  DATA_ANALYSIS = 'analysis',
  CREATIVE = 'creative',
  GENERAL = 'general',
  TECHNICAL = 'technical',
  DOCUMENTATION = 'documentation',
}

// ============================================================================
// Task Complexity
// ============================================================================

export interface TaskComplexity {
  score: number;
  estimatedTokens: number;
  recommendedModel: 'fast' | 'pro' | 'ultra';
  estimatedRounds: number;
  requiresCodeExpert: boolean;
  requiresSecurityReview: boolean;
  requiresPerformanceReview: boolean;
}

// ============================================================================
// Agent Configuration
// ============================================================================

export type AgentTypeValue =
  | 'core'
  | 'code'
  | 'security'
  | 'performance'
  | 'writing'
  | 'data';

export enum AgentType {
  CORE = 'core',
  CODE = 'code',
  SECURITY = 'security',
  PERFORMANCE = 'performance',
  WRITING = 'writing',
  DATA = 'data',
}

export interface AgentConfig {
  name: string;
  agentType: AgentTypeValue;
  systemPrompt: string;
  model: 'fast' | 'pro' | 'ultra';
  enabled: boolean;
  priority: number;
}

// ============================================================================
// Task Context
// ============================================================================

export interface TaskContext {
  taskType: TaskType;
  complexity: TaskComplexity;
  agents: AgentConfig[];
  originalPrompt: string;
  strategy: string;
  currentDraft: string;
  history: Array<{ role: string; content: string }>;
}

// ============================================================================
// Refinement Result
// ============================================================================

export interface RefinementResult {
  originalPrompt: string;
  finalPrompt: string;
  taskType: string;
  complexity: number;
  modelUsed: string;
  roundsCompleted: number;
  agentsUsed: string[];
  history: Array<{ role: string; content: string }>;
}

// ============================================================================
// Progress Event (No Emoji!)
// ============================================================================

export type ProgressPhase =
  | 'analyze'
  | 'select'
  | 'strategy'
  | 'draft'
  | 'review'
  | 'critique'
  | 'refine'
  | 'verify'
  | 'complete'
  | 'error';

export interface ProgressEvent {
  phase: ProgressPhase;
  message: string;
  data?: Record<string, unknown>;
}

// ============================================================================
// Configuration Types
// ============================================================================

export interface AgentDefinition {
  type: AgentTypeValue;
  model: 'fast' | 'pro' | 'ultra';
  priority: number;
  enabled?: boolean;
  trigger?: {
    taskTypes?: TaskTypeValue[];
    requireSecurityReview?: boolean;
    requirePerformanceReview?: boolean;
    complexityMin?: number;
  };
}

export interface ClassifierConfig {
  keywordWeights: Record<TaskTypeValue, Record<string, number>>;
  complexityThresholds: {
    fastModelThreshold: number;
    multiRoundThreshold: number;
    maxRoundsThreshold: number;
  };
}

export interface RefinerConfig {
  defaultModel: 'fast' | 'pro' | 'ultra';
  maxRounds: number;
  minRounds: number;
  earlyTermination: boolean;
  earlyTerminationKeyword: string;
}

export interface FullConfig {
  version: string;
  agents: Record<string, AgentDefinition>;
  classifier: ClassifierConfig;
  refiner: RefinerConfig;
}

// ============================================================================
// LLM Types
// ============================================================================

export interface LLMResponse {
  text: string;
  model: string;
  tokensUsed: number;
  latencyMs: number;
}

export interface LLMError extends Error {
  model: string;
  retryable: boolean;
  statusCode?: number;
}

// ============================================================================
// Health Check Types
// ============================================================================

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  components: {
    llm: { status: string };
    config: { status: string; missingVars?: string[] };
    prompts: { status: string; count: number };
  };
}
