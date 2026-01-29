import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { VertexAIClient } from './vertex';
// Import unified prompts
import prompts from '../../../sys_init/prompts.json';

// Environment Bindings
type Bindings = {
  GOOGLE_API_KEY: string;
  INVITE_CODE: string;
  TASKS: KVNamespace;
  GEMINI_MODEL: string;
  // Vertex AI Config (Optional)
  VERTEX_PROJECT_ID?: string;
  VERTEX_CLIENT_EMAIL?: string;
  VERTEX_PRIVATE_KEY?: string;
  VERTEX_LOCATION?: string;
};

const app = new Hono<{ Bindings: Bindings }>();

// Helper for Model Generation with Fallback
async function generateWithFallback(env: Bindings, prompt: string): Promise<string> {
  // 1. Try Primary (Gemini AI Studio)
  try {
    if (!env.GOOGLE_API_KEY) throw new Error("Missing GOOGLE_API_KEY");
    const genAI = new GoogleGenerativeAI(env.GOOGLE_API_KEY);
    const model = genAI.getGenerativeModel({ model: env.GEMINI_MODEL || 'gemini-2.0-flash' });
    const result = await model.generateContent(prompt);
    return result.response.text();
  } catch (primaryError: any) {
    console.error("Primary Model Failed:", primaryError);
    
    // 2. Try Fallback (Vertex AI)
    if (env.VERTEX_PROJECT_ID && env.VERTEX_CLIENT_EMAIL && env.VERTEX_PRIVATE_KEY) {
      console.log("Switching to Vertex AI Fallback...");
      try {
        const vertex = new VertexAIClient({
          projectId: env.VERTEX_PROJECT_ID,
          clientEmail: env.VERTEX_CLIENT_EMAIL,
          privateKey: env.VERTEX_PRIVATE_KEY, // Ensure this is set via `wrangler secret`
          location: env.VERTEX_LOCATION
        });
        // Use a known stable model for fallback
        return await vertex.generateContent('gemini-1.5-pro-preview-0409', prompt);
      } catch (fallbackError: any) {
        throw new Error(`All models failed. Primary: ${primaryError.message}. Fallback: ${fallbackError.message}`);
      }
    }
    
    throw primaryError;
  }
}

// 1. Middleware: CORS & Auth
app.use('/*', cors());

app.use('/api/*', async (c, next) => {
  const authHeader = c.req.header('x-invite-code');
  const envCode = c.env.INVITE_CODE;
  
  // If invite code is configured in env, enforce it
  if (envCode && authHeader !== envCode) {
    return c.json({ error: 'Unauthorized: Invalid Invite Code' }, 401);
  }
  await next();
});

// 2. Core Logic: Refinement Protocol (Streaming)
app.post('/api/refine', async (c) => {
  const { prompt } = await c.req.json<{ prompt: string }>();
  
  if (!prompt) return c.json({ error: 'Prompt is required' }, 400);
  if (!c.env.GOOGLE_API_KEY) return c.json({ error: 'Server Config Error: Missing API Key' }, 500);

  // Initialize Gemini (Replaced with Fallback Wrapper)
  // const genAI = new GoogleGenerativeAI(c.env.GOOGLE_API_KEY);
  // const model = genAI.getGenerativeModel({ model: c.env.GEMINI_MODEL || 'gemini-2.0-flash' });

  // Stream Response
  const { readable, writable } = new TransformStream();
  const writer = writable.getWriter();
  const encoder = new TextEncoder();

  // Background processing
  c.executionCtx.waitUntil((async () => {
    try {
      const log = (msg: string) => writer.write(encoder.encode(JSON.stringify({ type: 'log', content: msg }) + '\n'));
      const chunk = (msg: string) => writer.write(encoder.encode(JSON.stringify({ type: 'chunk', content: msg }) + '\n'));

      await log("🔍 Phase 1: Inception & Strategy Analysis...");
      
      // Step 1: Strategy
      const p1 = prompts.strategist;
      const strategyPrompt = `${p1.system}\n\n${p1.user_template.replace('{prompt}', prompt)}`;
      
      const strategyText = await generateWithFallback(c.env, strategyPrompt);
      await log(`✅ Strategy Developed: ${strategyText.slice(0, 50)}...`);

      // Step 2: Draft
      await log("Phase 2: Drafting Initial Prompt...");
      const p2 = prompts.architect;
      const draftPrompt = `${p2.system}\n\n${p2.user_template.replace('{strategy}', strategyText).replace('{prompt}', prompt)}`;
      
      const currentDraft = await generateWithFallback(c.env, draftPrompt);
      await chunk(currentDraft); // Send draft preview

      // Step 3: Refinement (Simplified 1 round for demo speed, can be loop)
      await log("Phase 3: Adversarial Refinement (Round 1)...");
      const p3 = prompts.critic;
      const critiquePrompt = `${p3.system}\n\n${p3.user_template.replace('{prompt}', prompt).replace('{draft}', currentDraft)}`;
      
      const critique = await generateWithFallback(c.env, critiquePrompt);
      await log("🤔 Critic Feedback Received. Optimizing...");

      const p4 = prompts.refiner;
      const refinePrompt = `${p4.system}\n\n${p4.user_template.replace('{critique}', critique).replace('{draft}', currentDraft)}`;
      
      const finalDraft = await generateWithFallback(c.env, refinePrompt);
      
      await log("🏆 Perfection Achieved. Finalizing...");
      await writer.write(encoder.encode(JSON.stringify({ type: 'final', content: finalDraft }) + '\n'));

      // Save to KV
      const taskId = Date.now().toString();
      await c.env.TASKS.put(taskId, JSON.stringify({
        id: taskId,
        original: prompt,
        final: finalDraft,
        strategy: strategyText,
        timestamp: new Date().toISOString()
      }));

    } catch (e: any) {
      await writer.write(encoder.encode(JSON.stringify({ type: 'error', content: e.message }) + '\n'));
    } finally {
      await writer.close();
    }
  })());

  return new Response(readable, {
    headers: { 'Content-Type': 'text/event-stream' }
  });
});

// 3. History API
app.get('/api/history', async (c) => {
  const list = await c.env.TASKS.list({ limit: 20 });
  const tasks = [];
  for (const key of list.keys) {
    const value = await c.env.TASKS.get(key.name);
    if (value) tasks.push(JSON.parse(value));
  }
  return c.json(tasks.sort((a: any, b: any) => b.id - a.id)); // Newest first
});

export default app;
