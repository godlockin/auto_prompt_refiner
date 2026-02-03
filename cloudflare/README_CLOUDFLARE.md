# Synthesis Prime: Cloudflare Deployment Guide

Upgraded to a Serverless Architecture suitable for Cloudflare Workers (Backend) & Pages (Frontend).

## 🚀 Prerequisites

1.  **Node.js**: `npm` installed.
2.  **Wrangler CLI**: `npm install -g wrangler`
3.  **Cloudflare Account**: Login via `wrangler login`

## 🛠️ Configuration

### 1. Secrets Setup
Set your API keys securely in Cloudflare:

```bash
cd cloudflare/worker

# Google AI Studio API Key (Gemini)
wrangler secret put GOOGLE_API_KEY
# Enter your key: ...

# Invite Code (Password Protection)
wrangler secret put INVITE_CODE
# Enter your code: (e.g., "synthesis-2024")

# --- Vertex AI Fallback Setup (Optional) ---
# If you want automatic fallback to Vertex AI when Gemini AI Studio fails,
# you need to extract credentials from your Service Account JSON file.

# 1. Project ID & Location (Set in wrangler.toml)
# [vars]
# VERTEX_PROJECT_ID = "your-project-id"
# VERTEX_LOCATION = "us-central1"

# 2. Client Email
wrangler secret put VERTEX_CLIENT_EMAIL
# Enter the "client_email" field from your JSON file (e.g., "service-account@project.iam.gserviceaccount.com")

# 3. Private Key
# IMPORTANT: You must copy the ENTIRE string including "-----BEGIN PRIVATE KEY-----" and "\n" characters.
# The worker will handle the formatting.
wrangler secret put VERTEX_PRIVATE_KEY
# Enter the "private_key" field from your JSON file
```

### 2. KV Namespace (History Storage)
Create a KV namespace for storing task history:

```bash
wrangler kv:namespace create TASKS
```

Update `wrangler.toml` with the generated ID:
```toml
[[kv_namespaces]]
binding = "TASKS"
id = "YOUR_ID_FROM_ABOVE"
```

## 📦 Deployment

### Backend (Worker)
```bash
cd cloudflare/worker
npm install
npm run deploy
```
*Note the URL of your deployed worker (e.g., https://prompt-refiner.your-subdomain.workers.dev)*

### Frontend (Pages)
1. Update API URL:
   Open `cloudflare/frontend/src/main.tsx` and ensure `API_BASE` points to your worker URL if not using custom domains. (Or use Cloudflare Pages Functions integration).
   *For simple separation:*
   Replace `'/api'` in `main.tsx` with your worker URL if they are on different domains (and ensure Worker CORS is set).

2. Deploy:
```bash
cd cloudflare/frontend
npm install
npm run build
# Deploy 'dist' folder to Cloudflare Pages via Dashboard or Wrangler
npx wrangler pages deploy dist --project-name synthesis-prime
```

## ✨ Features
*   **Stronger UI**: React + Tailwind + Lucide Icons + Markdown Rendering.
*   **Auth**: Invite Code protection via Middleware.
*   **Streaming**: Real-time "Cognitive Trace" logs.
*   **History**: Persistent mission logs via Cloudflare KV.

## 🤖 Use as MCP Tool (Cursor/Trae Integration)

Synthesis Prime can be used as a **Remote Tool** in AI IDEs like Cursor or Trae via the Model Context Protocol (MCP).

### 1. Configuration
Add the following to your IDE's MCP settings (e.g., `~/.cursor/mcp.json` or project-specific config):

```json
{
  "mcpServers": {
    "synthesis-prime": {
      "url": "https://<YOUR_WORKER_URL>/api/mcp",
      "headers": {
        "Authorization": "Bearer <YOUR_INVITE_CODE>"
      }
    }
  }
}
```

### 2. Usage
Once configured, you can ask your IDE Agent:
> "Use the refine_prompt tool to optimize this prompt: 'Help me write a snake game'"

The agent will call your Cloudflare Worker, execute the refinement protocol, and return the SOTA result directly in your chat.
