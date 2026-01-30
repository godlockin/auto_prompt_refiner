# 🔮 Synthesis Prime: Auto Prompt Refiner

> **The Ultimate Cognitive Engine for Prompt Engineering**
>
> *Eliminating semantic entropy, one prompt at a time.*

**Synthesis Prime** is an automated Prompt Refinement System based on the "System 2" slow-thinking cognitive architecture. It is not just an optimization tool, but a "Refinement Council" composed of AI experts who transform vague user intentions into **SOTA (State-of-the-Art)** System Prompts through Adversarial Refinement.

This project offers two interfaces:

1. **Python CLI**: For local, terminal-based usage.
2. **Cloudflare Pages**: A full-stack web application (React Frontend + Serverless Functions) for a zero-setup browser experience.

## 🌟 Key Features

* **🧠 Cognitive Architecture**: Based on `P-M-O-S` (Persona, Mission, Operations, Standards) framework.
* **⚔️ Adversarial Refinement**: Built-in agents – `Strategist`, `Architect`, `Critic`, `Refiner` – for multi-round optimization.
* **🛡️ Dual-Engine Fallback**:
  * **Primary**: Google Gemini 2.0/3.0 (Precision)
  * **Fallback**: Vertex AI Gemini (Enterprise Stability) – *Automatic circuit breaker.*
* **🌊 Streaming Experience**: Real-time visibility into the AI's "thought process".
* **📜 Mission Log**: Sidebar history of previous refinements (Toggleable).
* **🔌 Cloudflare Unified Deployment**: A single directory (`cloudflare/frontend`) that deploys both the UI and the Backend API to Cloudflare Pages.

## ⚙️ App Configuration

### Environment Variables (Cloudflare Pages)

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `GOOGLE_API_KEY` | Your Gemini API Key. | **Yes** | - |
| `GEMINI_MODEL` | Specific model to use (e.g., `gemini-2.5-pro`). | No | `gemini-2.5-pro` |
| `INVITE_CODE` | Optional password protection. | No | - |
| `VITE_DEFAULT_SHOW_HISTORY` | Set to `true` to show Mission Log sidebar by default. | No | `false` |

## 🚀 Quick Start (Python CLI)

### 1. Environment Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file and set your API keys:

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 3. Usage

```bash
# Basic usage
python src/cli.py --prompt "Help me write a Snake game in Python"

# Export result to file
python src/cli.py --prompt "Help me write a Snake game" --output "./snake_prompt.md"
```

## ☁️ Quick Start (Cloudflare Pages)

**Deploy the fully unified web application.** The backend logic lives in `functions/` and deploys automatically with the frontend.

### 1. Setup

```bash
cd cloudflare/frontend
npm install
```

### 2. Development

```bash
# Run local development server (Frontend + Functions)
npx wrangler pages dev
```

*Note: You will need to bind your generic `GOOGLE_API_KEY` in `wrangler.toml` or via the dashboard.*

### 3. Deployment

```bash
npm run build
npx wrangler pages deploy dist --project-name synthesis-prime
```

## 📂 Project Structure

```text
.
├── src/                 # Python Core Logic & CLI
│   ├── cli.py           # Command Line Interface
│   ├── config.py        # Configuration
│   ├── llm_client.py    # LLM & Fallback Logic
│   └── refiner.py       # Core Refinement Protocol
├── data/                # Data & Prompts
│   └── prompts.json     # System Prompts (Shared)
├── cloudflare/          # Web Application
│   └── frontend/        # Unified Pages Project
│       ├── src/         # React UI
│       └── functions/   # Serverless API (Backend)
├── tasks/               # Output Artifacts (Local)
└── requirements.txt     # Python Dependencies
```

## 📜 License

[MIT License](LICENSE)
