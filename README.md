# 🔮 Synthesis Prime: Auto Prompt Refiner

> **The Ultimate Cognitive Engine for Prompt Engineering**
> 
> *Eliminating semantic entropy, one prompt at a time.*

**Synthesis Prime** 是一个基于 "System 2" 慢思考认知架构的自动化 Prompt 精炼系统。它不仅仅是一个优化工具，更是一个由 AI 专家组成的“精炼委员会”，通过对抗性演练（Adversarial Refinement）将用户的模糊意图转化为 **SOTA (State-of-the-Art)** 级别的 System Prompt。

## 🌟 核心特性 (Key Features)

*   **🧠 认知架构 (Cognitive Architecture)**: 基于 `P-M-O-S` (Persona, Mission, Operations, Standards) 框架，深度解构用户需求。
*   **⚔️ 对抗性精炼 (Adversarial Refinement)**: 内置 `Strategist` (策略家), `Architect` (架构师), `Critic` (批评家), `Refiner` (精炼师) 四大智能体，进行多轮红蓝对抗优化。
*   **🛡️ 双引擎容错 (Dual-Engine Fallback)**: 
    *   **Primary**: Google Gemini 3.0 Pro Preview (追求极致推理)
    *   **Fallback**: Vertex AI Gemini 2.5/1.5 Pro (企业级稳定性保障) - *自动熔断机制，零延迟切换。*
*   **🌊 流式交互 (Streaming Experience)**: 支持实时展示 AI 的思考过程与中间迭代版本，拒绝黑盒等待。
*   **💾 资产管理 (Asset Management)**: 自动归档每一次优化任务，支持一键导出 Markdown 格式的最终交付物。

## 🏗️ 系统架构 (Architecture)

```mermaid
graph TD
    User[User Input] --> Strategist[🕵️ Strategist]
    Strategist --> Architect[🏗️ Architect]
    Architect --> Draft[Initial Draft]
    Draft --> Critic[⚖️ Critic (Red Team)]
    Critic --> Refiner[✨ Refiner]
    Refiner --> Draft
    Refiner --> Final[SOTA Prompt]
    
    subgraph "Cognitive Layer"
    Strategist
    Architect
    Critic
    Refiner
    end
    
    subgraph "Engine Layer"
    Gemini3[Gemini 3.0 Pro] --Fallback--> Vertex[Vertex AI]
    end
```

## 🚀 快速开始 (Quick Start)

### 1. 环境准备

```bash
# 创建 Conda 环境
conda create -n prompt_refiner python=3.11 -y
conda activate prompt_refiner

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置密钥

在 `sys_init/` 目录下创建或配置 `.env` 文件（已在 `.gitignore` 中排除，需手动配置）：

```ini
# Google AI Studio API Key
GOOGLE_API_KEY=your_api_key_here

# Vertex AI 配置 (可选，用于 Fallback)
# 需确保 sys_init/ 目录下存在对应的 service_account.json
```

### 3. 启动 GUI (Web Interface)

推荐使用图形界面，体验完整的流式交互与历史记录管理。

```bash
python src/app.py
```

访问: `http://localhost:7860`

*   **Refine Prompt**: 输入原始提示词，点击 "Ignite Refinement Protocol"。
*   **Download**: 生成完成后，点击 "Save Result to Local" 下载 `.md` 文件。
*   **History**: 查看过往的所有优化记录与演进过程。

### 4. 使用 CLI (Command Line)

适合集成到自动化工作流中。

```bash
# 基本用法
python src/cli.py --prompt "帮我写一个贪吃蛇游戏"

# 导出结果到指定文件
python src/cli.py --prompt "帮我写一个贪吃蛇游戏" --output "./snake_prompt.md"
```

## 📂 项目结构 (Structure)

```text
.
├── src/
│   ├── app.py           # Gradio Web UI 入口
│   ├── cli.py           # 命令行接口
│   ├── config.py        # 配置加载
│   ├── llm_client.py    # 双引擎 LLM 客户端 (含熔断机制)
│   ├── refiner.py       # Synthesis Prime 核心协议实现
│   └── storage.py       # 任务存储与导出模块
├── tasks/               # 任务存档 (自动生成)
├── sys_init/            # 系统初始化配置 (Git Ignored)
├── requirements.txt     # 依赖列表
└── README.md            # 项目文档
```

## 📜 许可证 (License)

[MIT License](LICENSE)
