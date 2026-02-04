/**
 * Intelligent Prompt Refiner - Cloudflare Worker Version (Refactored)
 *
 * Architecture:
 * - src/core/types.ts: Shared type definitions
 * - src/core/classifier.ts: Optimized task classification
 * - src/core/orchestrator.ts: Priority-based agent scheduling
 *
 * Features:
 * - Task type detection and classification
 * - Dynamic agent composition
 * - Smart model selection (fast/pro)
 * - Adaptive optimization rounds
 * - Domain-specific expert agents
 *
 * No emoji in logs. Professional logging only.
 */

import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { handle } from 'hono/cloudflare-pages';

// ============================================================================
// Core Modules (No Duplication)
// ============================================================================

import {
  TaskType,
  TaskComplexity,
  AgentConfig,
  ProgressEvent,
} from '../../src/core/types';

import { TaskClassifier } from '../../src/core/classifier';
import { DynamicAgentOrchestrator } from '../../src/core/orchestrator';

// ============================================================================
// Environment Bindings
// ============================================================================

interface EnvBindings {
  GOOGLE_API_KEY: string;
  INVITE_CODE: string;
  TASKS: KVNamespace;
  GEMINI_MODEL: string;
  GEMINI_MODEL_FAST: string;
  VERTEX_PROJECT_ID?: string;
  VERTEX_CLIENT_EMAIL?: string;
  VERTEX_PRIVATE_KEY?: string;
  VERTEX_LOCATION?: string;
}

// ============================================================================
// Prompt Templates (Loaded from JSON)
// ============================================================================

const PROMPTS: Record<string, { system: string; user_template: string }> = {
  strategist: {
    system: `### SYSTEM IDENTITY: CHIEF COGNITIVE ARCHITECT // SYNTHESIS PRIME

[PRIME DIRECTIVE]
You are the Chief Cognitive Architect. Your function is to deconstruct, analyze, and architect the logic required to optimize user inputs.`,
    user_template: 'User Input: {prompt}'
  },
  architect: {
    system: `You are the Prime Architect. Your sole purpose is to transmute abstract strategic intent into executable, high-fidelity System Prompts.

[STRUCTURE]
## Role: Persona definition
## Mission: Core objective
## Workflow: Step-by-step algorithmic instruction
## Constraints: Negative constraints and safety boundaries`,
    user_template: 'Strategy:\n{strategy}\n\nOriginal Request:\n{prompt}'
  },
  critic: {
    system: `// SYSTEM IDENTITY: ADVERSARIAL_PRIME //

PRIME DIRECTIVE:
Execute ruthless stress testing of the target prompt.

[OUTPUT PROTOCOL]
If perfect: Output exactly "NO_ISSUES_FOUND"
If flaws exist: Generate DAMAGE REPORT:
**[SEVERITY: CRITICAL/MODERATE/MINOR]**
**[VECTOR]**: Specific mechanism of failure
**[PATCH]**: Exact verbatim text required to fix`,
    user_template: 'Original Request:\n{prompt}\n\nCurrent Draft:\n{draft}'
  },
  refiner: {
    system: `IDENTITY: You are the Prime Optimization Core.

MISSION: Synthesize critique and draft into SOTA iteration.

[RULES]
1. Treat Critic's feedback as immutable directives
2. Maintain Markdown architecture
3. Prior optimizations must be preserved
4. Maximize token economy

OUTPUT: Return ONLY the consolidated prompt text.`,
    user_template: 'Critique:\n{critique}\n\nCurrent Draft:\n{draft}'
  },
  code_expert: {
    system: `IDENTITY: Senior Code Review Expert

MISSION: Review code prompts for best practices

[REVIEW CRITERIA]
1. Code Style: Follow language-specific conventions
2. Error Handling: Robust exception management
3. Performance: Optimal algorithms and data structures
4. Security: Input validation, injection prevention
5. Documentation: Clear comments and docstrings

OUTPUT: Specific improvements with code snippets`,
    user_template: 'Task:\n{prompt}\n\nDraft:\n{draft}'
  },
  security_expert: {
    system: `IDENTITY: Security Architect

MISSION: Identify security vulnerabilities in prompts

[ATTACK VECTORS]
1. Prompt Injection: Malicious instruction overrides
2. Information Disclosure: Sensitive data leakage
3. Authentication Bypass: Weak auth requirements
4. Output Manipulation: Response exploitation

OUTPUT: Critical security findings with patches`,
    user_template: 'Task:\n{prompt}\n\nDraft:\n{draft}'
  },
  performance_expert: {
    system: `IDENTITY: Performance Engineer

MISSION: Optimize for speed and resource efficiency

[CRITERIA]
1. Time Complexity: O(n) or better preferred
2. Space Complexity: Minimal memory footprint
3. I/O Efficiency: Batch operations, caching
4. Concurrency: Parallel processing when beneficial

OUTPUT: Performance bottlenecks with optimization suggestions`,
    user_template: 'Task:\n{prompt}\n\nDraft:\n{draft}'
  },
  style_expert: {
    system: `IDENTITY: Editorial Style Expert

MISSION: Ensure writing quality and consistency

[CRITERIA]
1. Voice: Consistent tone and register
2. Clarity: Concise, unambiguous language
3. Structure: Logical flow, proper transitions
4. Grammar: Error-free prose

OUTPUT: Specific style improvements`,
    user_template: 'Task:\n{prompt}\n\nDraft:\n{draft}'
  },
  data_expert: {
    system: `IDENTITY: Data Analysis Specialist

MISSION: Ensure data analysis prompts are rigorous

[CRITERIA]
1. Statistical Validity: Proper statistical methods
2. Visualization: Clear, informative charts
3. Interpretation: Accurate, nuanced insights
4. Reproducibility: Clear methodology

OUTPUT: Data analysis quality issues with fixes`,
    user_template: 'Task:\n{prompt}\n\nDraft:\n{draft}'
  }
};

// ============================================================================
// LLM Client with Fallback
// ============================================================================

async function generateWithFallback(
  env: EnvBindings,
  prompt: string,
  modelOverride?: string
): Promise<string> {
  const modelName = modelOverride || env.GEMINI_MODEL || 'gemini-2.5-pro';

  if (!env.GOOGLE_API_KEY) {
    throw new Error('Missing GOOGLE_API_KEY');
  }

  try {
    const { GoogleGenerativeAI } = await import('@google/generative-ai');
    const genAI = new GoogleGenerativeAI(env.GOOGLE_API_KEY);
    const model = genAI.getGenerativeModel({ model: modelName });
    const result = await model.generateContent(prompt);
    return result.response.text();
  } catch (primaryError: any) {
    console.error(`Primary model (${modelName}) failed:`, primaryError?.message || primaryError);

    if (env.VERTEX_PROJECT_ID && env.VERTEX_CLIENT_EMAIL && env.VERTEX_PRIVATE_KEY) {
      try {
        const { VertexAIClient } = await import('./vertex');
        const vertex = new VertexAIClient({
          projectId: env.VERTEX_PROJECT_ID,
          clientEmail: env.VERTEX_CLIENT_EMAIL,
          privateKey: env.VERTEX_PRIVATE_KEY,
          location: env.VERTEX_LOCATION
        });
        return await vertex.generateContent('gemini-2.5-pro', prompt);
      } catch (fallbackError: any) {
        throw new Error(`All models failed. Primary: ${primaryError?.message || primaryError}. Fallback: ${fallbackError?.message || fallbackError}`);
      }
    }

    throw new Error(`Gemini API Failed (${modelName}): ${primaryError?.message || primaryError}`);
  }
}

// ============================================================================
// Utility Functions
// ============================================================================

function buildPrompt(agent: string, template: string, params: Record<string, string>): string {
  return template.replace(/\{(\w+)\}/g, (_, key) => params[key] || '');
}

function truncate(text: string, maxLength: number = 100): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

function sanitizePrompt(input: string): string {
  return input
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/javascript:/gi, '')
    .replace(/on\w+=/gi, '')
    .trim();
}

function checkEnv(env: EnvBindings): string[] {
  const missing = [];
  if (!env.GOOGLE_API_KEY) missing.push('GOOGLE_API_KEY');
  if (!env.TASKS) missing.push('TASKS (KV Binding)');
  return missing;
}

// ============================================================================
// API Routes
// ============================================================================

const app = new Hono<{ Bindings: EnvBindings }>();

app.use('/*', cors());

app.use('/api/*', async (c, next) => {
  const authHeader = c.req.header('x-invite-code');
  const envCode = c.env.INVITE_CODE;
  if (envCode && authHeader !== envCode) {
    return c.json({ error: 'Unauthorized: Invalid Invite Code' }, 401);
  }
  await next();
});

app.get('/api/analyze', async (c) => {
  const prompt = c.req.query('prompt');
  if (!prompt) {
    return c.json({ error: 'Prompt required' }, 400);
  }

  const { taskType, complexity } = TaskClassifier.classify(prompt);
  const agents = DynamicAgentOrchestrator.getAgentsForTask(taskType, complexity, prompt);

  return c.json({
    taskType: taskType.valueOf(),
    complexity,
    agents: agents.filter(a => a.enabled).map(a => ({
      name: a.name,
      type: a.agentType,
      model: a.model
    })),
    recommendedModel: complexity.recommendedModel,
    estimatedRounds: complexity.estimatedRounds
  });
});

app.post('/api/refine', async (c) => {
  try {
    const body = await c.req.json();
    const rawPrompt = body.prompt;

    if (!rawPrompt || typeof rawPrompt !== 'string') {
      return c.json({ error: 'Prompt is required' }, 400);
    }

    const prompt = sanitizePrompt(rawPrompt);
    if (!prompt) {
      return c.json({ error: 'Prompt contains no valid content after sanitization' }, 400);
    }

    const missingVars = checkEnv(c.env);
    if (missingVars.length > 0) {
      return c.json({ error: `Server Configuration Error: Missing ${missingVars.join(', ')}` }, 500);
    }

    const { readable, writable } = new TransformStream();
    const writer = writable.getWriter();
    const encoder = new TextEncoder();

    c.executionCtx.waitUntil((async () => {
      try {
        // Task Analysis
        const { taskType, complexity } = TaskClassifier.classify(prompt);
        const info = {
          taskType: taskType.valueOf(),
          complexity: complexity.score,
          model: complexity.recommendedModel,
          rounds: complexity.estimatedRounds
        };
        writer.write(encoder.encode(JSON.stringify({ type: 'log', content: `Analyzing task: ${JSON.stringify(info)}` }) + '\n'));

        // Dynamic Agent Selection
        const agents = DynamicAgentOrchestrator.getAgentsForTask(taskType, complexity, prompt);
        const expertNames = agents.filter(a => a.agentType !== 'core' && a.enabled).map(a => a.name);
        if (expertNames.length > 0) {
          writer.write(encoder.encode(JSON.stringify({ type: 'log', content: `Activating experts: ${expertNames.join(', ')}` }) + '\n'));
        }

        // Phase 1: Strategy
        const strategyPrompt = buildPrompt('strategist', PROMPTS.strategist.user_template, { prompt });
        const strategy = await generateWithFallback(c.env, PROMPTS.strategist.system + '\n\n' + strategyPrompt, c.env.GEMINI_MODEL_FAST);
        writer.write(encoder.encode(JSON.stringify({ type: 'log', content: `Strategy: ${truncate(strategy)}` }) + '\n'));

        // Phase 2: Architecture
        const architectPrompt = buildPrompt('architect', PROMPTS.architect.user_template, { strategy, prompt });
        const draft = await generateWithFallback(c.env, PROMPTS.architect.system + '\n\n' + architectPrompt, c.env.GEMINI_MODEL_FAST);
        writer.write(encoder.encode(JSON.stringify({ type: 'chunk', content: draft }) + '\n'));
        writer.write(encoder.encode(JSON.stringify({ type: 'log', content: `Draft created: ${draft.length} chars` }) + '\n'));

        // Expert Reviews
        const expertReviews: Record<string, string> = {};
        for (const agent of agents) {
          if (['code_expert', 'security_expert', 'performance_expert', 'style_expert', 'data_expert'].includes(agent.name)) {
            const agentPrompts = PROMPTS[agent.name as keyof typeof PROMPTS];
            if (agentPrompts) {
              const reviewPrompt = buildPrompt(agent.name, agentPrompts.user_template, { prompt, draft });
              const review = await generateWithFallback(c.env, agentPrompts.system + '\n\n' + reviewPrompt, agent.model);
              expertReviews[agent.name] = review;
              writer.write(encoder.encode(JSON.stringify({ type: 'log', content: `${agent.name}: ${truncate(review)}` }) + '\n'));
            }
          }
        }

        // Phase 3: Adversarial Critique
        let criticInput = `Original Request:\n${prompt}\n\nCurrent Draft:\n${draft}`;
        if (Object.keys(expertReviews).length > 0) {
          criticInput += '\n\nExpert Reviews:\n' + Object.entries(expertReviews)
            .map(([name, review]) => `${name}: ${review}`)
            .join('\n');
        }
        const critic = await generateWithFallback(c.env, PROMPTS.critic.system + '\n\n' + criticInput, c.env.GEMINI_MODEL_FAST);

        if (critic.includes('NO_ISSUES_FOUND')) {
          writer.write(encoder.encode(JSON.stringify({ type: 'log', content: 'Perfection achieved - no issues found' }) + '\n'));
          writer.write(encoder.encode(JSON.stringify({ type: 'final', content: draft }) + '\n'));
          await saveTask(c.env, prompt, draft, strategy, taskType.valueOf());
          await writer.close();
          return;
        }

        // Adaptive Refinement Rounds
        let currentDraft = draft;
        for (let round = 1; round <= complexity.estimatedRounds; round++) {
          writer.write(encoder.encode(JSON.stringify({ type: 'log', content: `Round ${round}: Refinement in progress` }) + '\n'));

          currentDraft = await generateWithFallback(c.env,
            PROMPTS.refiner.system + '\n\nCritique:\n' + critic + '\n\nCurrent Draft:\n' + currentDraft,
            c.env.GEMINI_MODEL
          );
          writer.write(encoder.encode(JSON.stringify({ type: 'chunk', content: currentDraft }) + '\n'));

          const verification = await generateWithFallback(c.env,
            PROMPTS.critic.system + '\n\nOriginal Request:\n' + prompt + '\n\nCurrent Draft:\n' + currentDraft,
            c.env.GEMINI_MODEL_FAST
          );

          if (verification.includes('NO_ISSUES_FOUND')) {
            writer.write(encoder.encode(JSON.stringify({ type: 'log', content: `Round ${round}: Passed verification` }) + '\n'));
            break;
          }

          if (round === complexity.estimatedRounds) {
            writer.write(encoder.encode(JSON.stringify({ type: 'log', content: 'Maximum rounds reached' }) + '\n'));
          }
        }

        writer.write(encoder.encode(JSON.stringify({ type: 'log', content: 'Refinement complete' }) + '\n'));
        writer.write(encoder.encode(JSON.stringify({ type: 'final', content: currentDraft }) + '\n'));
        await saveTask(c.env, prompt, currentDraft, strategy, taskType.valueOf());

      } catch (e: any) {
        console.error('Refinement Error:', e);
        writer.write(encoder.encode(JSON.stringify({ type: 'error', content: `Error: ${e?.message || e}` }) + '\n'));
      } finally {
        await writer.close();
      }
    })());

    return new Response(readable, {
      headers: { 'Content-Type': 'text/event-stream' }
    });

  } catch (reqError: any) {
    return c.json({ error: `Request Failed: ${reqError?.message || 'Unknown error'}` }, 500);
  }
});

async function saveTask(env: EnvBindings, original: string, final: string, strategy: string, taskType: string) {
  const taskId = Date.now().toString();
  try {
    await env.TASKS.put(taskId, JSON.stringify({
      id: taskId,
      original,
      final,
      strategy,
      taskType,
      timestamp: new Date().toISOString()
    }));
  } catch (kvError: any) {
    console.error('KV Save Failed:', kvError);
  }
}

app.get('/api/history', async (c) => {
  try {
    const list = await c.env.TASKS.list({ limit: 20 });
    const tasks = [];
    for (const key of list.keys) {
      const value = await c.env.TASKS.get(key.name);
      if (value) tasks.push(JSON.parse(value));
    }
    return c.json(tasks.sort((a: any, b: any) => b.id - a.id));
  } catch (e: any) {
    return c.json({ error: e?.message || 'Unknown error' }, 500);
  }
});

app.get('/api/health', async (c) => {
  const missingVars = checkEnv(c.env);
  return c.json({
    status: missingVars.length === 0 ? 'healthy' : 'degraded',
    timestamp: new Date().toISOString(),
    components: {
      api: { status: 'healthy' },
      kv: { status: c.env.TASKS ? 'healthy' : 'unhealthy' },
      config: { status: missingVars.length === 0 ? 'healthy' : 'unhealthy', missing_vars: missingVars }
    }
  });
});

// ============================================================================
// MCP Protocol Support
// ============================================================================

app.get('/api/mcp', async (c) => {
  const accept = c.req.header('Accept');
  if (accept && !accept.includes('text/event-stream')) {
    return c.text('MCP JSON-RPC Endpoint Active');
  }

  const { readable, writable } = new TransformStream();
  const writer = writable.getWriter();
  const encoder = new TextEncoder();
  const sessionId = crypto.randomUUID();

  c.executionCtx.waitUntil((async () => {
    try {
      const postUrl = `/api/mcp?sessionId=${sessionId}`;
      writer.write(encoder.encode(`event: endpoint\ndata: ${postUrl}\n\n`));

      const startTime = Date.now();
      while (Date.now() - startTime < 50000) {
        const msgKey = `mcp:msg:${sessionId}`;
        const message = await c.env.TASKS.get(msgKey);

        if (message) {
          writer.write(encoder.encode(`event: message\ndata: ${message}\n\n`));
          await c.env.TASKS.delete(msgKey);
        }

        await new Promise(resolve => setTimeout(resolve, 200));
      }
    } catch (e) {
      console.error('SSE Error:', e);
    } finally {
      await writer.close();
    }
  })());

  return new Response(readable, {
    headers: { 'Content-Type': 'text/event-stream', 'X-Session-ID': sessionId }
  });
});

app.post('/api/mcp', async (c) => {
  const authHeader = c.req.header('Authorization');
  const envCode = c.env.INVITE_CODE;
  const token = authHeader?.startsWith('Bearer ') ? authHeader.slice(7) : authHeader;

  if (envCode && token !== envCode) {
    return c.json({ jsonrpc: '2.0', error: { code: -32000, message: 'Unauthorized' } }, 401);
  }

  try {
    const body = await c.req.json();
    const sessionId = c.req.query('sessionId');

    if (body.jsonrpc !== '2.0') {
      return c.json({ jsonrpc: '2.0', error: { code: -32600, message: 'Invalid Request' } }, 400);
    }

    let response = null;

    if (body.method === 'initialize') {
      response = {
        jsonrpc: '2.0',
        result: {
          protocolVersion: '2024-11-05',
          capabilities: { tools: { listChanged: false } },
          serverInfo: { name: 'synthesis-prime', version: '1.0.0' }
        },
        id: body.id
      };
    } else if (body.method === 'ping') {
      response = { jsonrpc: '2.0', result: {}, id: body.id };
    } else if (body.method === 'tools/list') {
      response = {
        jsonrpc: '2.0',
        result: {
          tools: [{
            name: 'refine_prompt',
            description: 'Refines user prompts with intelligent optimization',
            inputSchema: {
              type: 'object',
              properties: { prompt: { type: 'string', description: 'The original prompt' } },
              required: ['prompt']
            }
          }]
        },
        id: body.id
      };
    } else if (body.method === 'tools/call') {
      const { name, arguments: args } = body.params;

      if (name === 'refine_prompt') {
        const prompt = args.prompt;
        if (!prompt) {
          response = { jsonrpc: '2.0', error: { code: -32602, message: "Missing 'prompt' argument" }, id: body.id };
        } else {
          const { taskType, complexity } = TaskClassifier.classify(prompt);
          const strategy = await generateWithFallback(c.env,
            PROMPTS.strategist.system + '\n\nUser Input: ' + prompt,
            c.env.GEMINI_MODEL_FAST
          );
          let draft = await generateWithFallback(c.env,
            PROMPTS.architect.system + '\n\nStrategy:\n' + strategy + '\n\nOriginal Request:\n' + prompt,
            c.env.GEMINI_MODEL_FAST
          );
          let critique = await generateWithFallback(c.env,
            PROMPTS.critic.system + '\n\nOriginal Request:\n' + prompt + '\n\nCurrent Draft:\n' + draft,
            c.env.GEMINI_MODEL_FAST
          );

          if (!critique.includes('NO_ISSUES_FOUND')) {
            draft = await generateWithFallback(c.env,
              PROMPTS.refiner.system + '\n\nCritique:\n' + critique + '\n\nCurrent Draft:\n' + draft,
              c.env.GEMINI_MODEL
            );
          }

          const taskId = Date.now().toString();
          c.executionCtx.waitUntil(c.env.TASKS.put(taskId, JSON.stringify({
            id: taskId,
            original: prompt,
            final: draft,
            strategy,
            taskType: taskType.valueOf(),
            timestamp: new Date().toISOString(),
            source: 'mcp'
          })));

          response = { jsonrpc: '2.0', result: { content: [{ type: 'text', text: draft }] }, id: body.id };
        }
      } else {
        response = { jsonrpc: '2.0', error: { code: -32601, message: 'Method not found' }, id: body.id };
      }
    } else {
      response = { jsonrpc: '2.0', error: { code: -32601, message: 'Method not supported' }, id: body.id };
    }

    if (sessionId) {
      await c.env.TASKS.put(`mcp:msg:${sessionId}`, JSON.stringify(response));
      return c.text('Accepted', 202);
    }
    return c.json(response);
  } catch (e: any) {
    const errorResponse = { jsonrpc: '2.0', error: { code: -32000, message: `Internal Error: ${e?.message || e}` }, id: null };
    const sessionId = c.req.query('sessionId');
    if (sessionId) {
      await c.env.TASKS.put(`mcp:msg:${sessionId}`, JSON.stringify(errorResponse));
      return c.text('Error Queued', 202);
    }
    return c.json(errorResponse, 500);
  }
});

export const onRequest = handle(app);
