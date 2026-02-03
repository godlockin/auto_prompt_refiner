import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { handle } from 'hono/cloudflare-pages';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { VertexAIClient } from './vertex';
// Import unified prompts
// Path: functions/api/[[route]].ts -> functions/prompts.json = ../prompts.json
import prompts from '../prompts.json';

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
    const modelName = env.GEMINI_MODEL || 'gemini-2.5-pro';
    const keyPreview = env.GOOGLE_API_KEY ? `${env.GOOGLE_API_KEY.slice(0, 4)}...${env.GOOGLE_API_KEY.slice(-4)}` : 'MISSING';

    // 1. Try Primary (Gemini AI Studio)
    try {
        if (!env.GOOGLE_API_KEY) throw new Error("Missing GOOGLE_API_KEY");

        console.log(`[DEBUG] Initializing Gemini. Model: ${modelName}, Key: ${keyPreview}`);

        const genAI = new GoogleGenerativeAI(env.GOOGLE_API_KEY);
        const model = genAI.getGenerativeModel({ model: modelName });

        console.log(`[DEBUG] Calling generateContent...`);
        const result = await model.generateContent(prompt);
        console.log(`[DEBUG] Response received.`);

        return result.response.text();
    } catch (primaryError: any) {
        console.error("Primary Model Failed Full Error:", JSON.stringify(primaryError, Object.getOwnPropertyNames(primaryError)));
        console.error("Primary Model Failed Message:", primaryError.message);

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
                return await vertex.generateContent('gemini-2.5-pro', prompt);
            } catch (fallbackError: any) {
                throw new Error(`All models failed. Primary: ${primaryError.message}. Fallback: ${fallbackError.message}`);
            }
        }

        // Re-throw with more context if no fallback
        throw new Error(`Gemini API Failed (${modelName}): ${primaryError.message || primaryError}`);
    }
}

// 1. Middleware: CORS & Auth
// app.use('/*', cors()); // Cors might be handled by Pages automatically or header merging, but explicit is fine if needed. 
// Pages Functions are same origin as the frontend, so CORS is technically not needed for the frontend itself, 
// BUT if you call it from elsewhere, needed. Since this is a unified project, we can relax it or keep it.
app.use('/*', cors());

app.use('/api/*', async (c, next) => {
    // Skip auth middleware for MCP endpoint as it handles its own auth with JSON-RPC errors
    if (c.req.path === '/api/mcp') {
        return next();
    }

    const authHeader = c.req.header('x-invite-code');
    const envCode = c.env.INVITE_CODE;

    // If invite code is configured in env, enforce it
    if (envCode && authHeader !== envCode) {
        return c.json({ error: 'Unauthorized: Invalid Invite Code' }, 401);
    }
    await next();
});

// 2. Core Logic: Refinement Protocol (Streaming)
// Helper to check critical env vars
function checkEnv(env: Bindings) {
    const missing = [];
    if (!env.GOOGLE_API_KEY) missing.push("GOOGLE_API_KEY");
    if (!env.TASKS) missing.push("TASKS (KV Binding)");
    return missing;
}

app.post('/api/refine', async (c) => {
    try {
        const { prompt } = await c.req.json<{ prompt: string }>();
        if (!prompt) return c.json({ error: 'Prompt is required' }, 400);

        // Pre-flight check
        const missingVars = checkEnv(c.env);
        if (missingVars.length > 0) {
            return c.json({ error: `Server Configuration Error: Missing ${missingVars.join(', ')}` }, 500);
        }

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
                await log(`[Setup] Model: ${c.env.GEMINI_MODEL || 'gemini-2.5-pro'}`);
                await log(`[Setup] Key: ${c.env.GOOGLE_API_KEY ? c.env.GOOGLE_API_KEY.slice(0, 4) + '...' : 'MISSING'}`);

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
                try {
                    await c.env.TASKS.put(taskId, JSON.stringify({
                        id: taskId,
                        original: prompt,
                        final: finalDraft,
                        strategy: strategyText,
                        timestamp: new Date().toISOString()
                    }));
                } catch (kvError: any) {
                    console.error("KV Save Failed:", kvError);
                    await log(`⚠️ Warning: Failed to save history: ${kvError.message}`);
                }

            } catch (e: any) {
                console.error("Stream Error:", e);
                // Send detailed error to frontend
                const errorMessage = e.message || "Unknown Error";
                const errorStack = e.stack || "";
                await writer.write(encoder.encode(JSON.stringify({
                    type: 'error',
                    content: `System Error: ${errorMessage}. Check logs.`
                }) + '\n'));
            } finally {
                await writer.close();
            }
        })());

        return new Response(readable, {
            headers: { 'Content-Type': 'text/event-stream' }
        });

    } catch (reqError: any) {
        return c.json({ error: `Request Failed: ${reqError.message}` }, 500);
    }
});

// 4. MCP API Implementation
app.get('/api/mcp', (c) => {
    return c.text('MCP JSON-RPC Endpoint Active. Please use POST requests with JSON-RPC 2.0 payload.');
});

app.post('/api/mcp', async (c) => {
    // Check Authorization: Bearer <INVITE_CODE>
    const authHeader = c.req.header('Authorization');
    const envCode = c.env.INVITE_CODE;
    
    // MCP clients usually use Bearer tokens
    const token = authHeader?.startsWith('Bearer ') ? authHeader.slice(7) : authHeader;
    
    if (envCode && token !== envCode) {
        return c.json({
            jsonrpc: "2.0",
            error: {
                code: -32000,
                message: "Unauthorized: Invalid Bearer Token"
            },
            id: null
        }, 401);
    }

    try {
        const body = await c.req.json();
        
        // Basic JSON-RPC 2.0 Validation
        if (body.jsonrpc !== '2.0') {
            return c.json({ jsonrpc: "2.0", error: { code: -32600, message: "Invalid Request" }, id: body.id }, 400);
        }

        // Handle 'tools/list'
        if (body.method === 'tools/list') {
            return c.json({
                jsonrpc: "2.0",
                result: {
                    tools: [{
                        name: "refine_prompt",
                        description: "Refines a user's prompt using the Synthesis Prime cognitive architecture. It analyzes, critiques, and optimizes the prompt to be SOTA (State-of-the-Art).",
                        inputSchema: {
                            type: "object",
                            properties: {
                                prompt: {
                                    type: "string",
                                    description: "The original prompt to be refined."
                                }
                            },
                            required: ["prompt"]
                        }
                    }]
                },
                id: body.id
            });
        }

        // Handle 'tools/call'
        if (body.method === 'tools/call') {
            const { name, arguments: args } = body.params;

            if (name === 'refine_prompt') {
                const prompt = args.prompt;
                if (!prompt) {
                    return c.json({ jsonrpc: "2.0", error: { code: -32602, message: "Missing 'prompt' argument" }, id: body.id });
                }

                // Execute Refinement (Non-streaming for MCP)
                // Reuse the generation logic but await the final result
                
                // Step 1: Strategy
                const p1 = prompts.strategist;
                const strategyPrompt = `${p1.system}\n\n${p1.user_template.replace('{prompt}', prompt)}`;
                const strategyText = await generateWithFallback(c.env, strategyPrompt);

                // Step 2: Draft
                const p2 = prompts.architect;
                const draftPrompt = `${p2.system}\n\n${p2.user_template.replace('{strategy}', strategyText).replace('{prompt}', prompt)}`;
                const currentDraft = await generateWithFallback(c.env, draftPrompt);

                // Step 3: Critique
                const p3 = prompts.critic;
                const critiquePrompt = `${p3.system}\n\n${p3.user_template.replace('{prompt}', prompt).replace('{draft}', currentDraft)}`;
                const critique = await generateWithFallback(c.env, critiquePrompt);

                // Step 4: Refine
                const p4 = prompts.refiner;
                const refinePrompt = `${p4.system}\n\n${p4.user_template.replace('{critique}', critique).replace('{draft}', currentDraft)}`;
                const finalDraft = await generateWithFallback(c.env, refinePrompt);

                // Save to KV (Optional for MCP, but good for history)
                const taskId = Date.now().toString();
                c.executionCtx.waitUntil(c.env.TASKS.put(taskId, JSON.stringify({
                    id: taskId,
                    original: prompt,
                    final: finalDraft,
                    strategy: strategyText,
                    timestamp: new Date().toISOString(),
                    source: 'mcp'
                })));

                return c.json({
                    jsonrpc: "2.0",
                    result: {
                        content: [{
                            type: "text",
                            text: finalDraft
                        }]
                    },
                    id: body.id
                });
            }
            
            return c.json({ jsonrpc: "2.0", error: { code: -32601, message: "Method not found" }, id: body.id });
        }

        return c.json({ jsonrpc: "2.0", error: { code: -32601, message: "Method not supported" }, id: body.id });

    } catch (e: any) {
        return c.json({
            jsonrpc: "2.0",
            error: {
                code: -32000,
                message: `Internal Error: ${e.message}`
            },
            id: null
        }, 500);
    }
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

// Export the request handler specifically for Pages Functions
export const onRequest = handle(app);
