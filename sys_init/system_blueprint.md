# Synthesis Prime: System Blueprint (全景设计蓝图)

本文档是 **Synthesis Prime** 系统的工程实现蓝图。结合 `goal_settings.md` (顶层愿景) 与 `prompt_enhancer.md` (认知协议)，构成了系统的完整定义。依据本文档，工程师应能从零还原整个系统。

## 1. 工程架构 (Engineering Architecture)

系统采用模块化分层设计，确保各组件松耦合且易于扩展。

### 1.1 目录结构
```text
auto_prompt_refiner/
├── src/                    # 源代码核心
│   ├── app.py              # Presentation Layer (Web UI)
│   ├── cli.py              # Presentation Layer (CLI)
│   ├── llm_client.py       # Infrastructure Layer (LLM Gateway)
│   ├── refiner.py          # Domain Layer (Core Business Logic)
│   ├── storage.py          # Infrastructure Layer (Persistence)
│   └── config.py           # Configuration
├── sys_init/               # System Definitions (The "DNA")
│   ├── goal_settings.md    # Vision & Mission
│   ├── prompt_enhancer.md  # Cognitive Protocol (Prompts)
│   └── system_blueprint.md # This File
├── tasks/                  # Data Store (Local File System)
└── requirements.txt        # Dependencies
```

### 1.2 核心模块职责

*   **`llm_client.py` (双引擎网关)**:
    *   **职责**: 统一封装 LLM 调用，屏蔽底层 API 差异。
    *   **关键逻辑**: 
        *   **Primary**: Google Gemini 3.0 Pro Preview (via `google-generativeai`).
        *   **Fallback**: Vertex AI Gemini 2.5/1.5 Pro (via `google-cloud-aiplatform`).
        *   **Circuit Breaker (熔断器)**: 一旦 Primary 调用失败（如 404/500），设置 `self.primary_broken = True`，后续所有请求**直接**路由至 Fallback，避免无谓等待。

*   **`refiner.py` (认知精炼引擎)**:
    *   **职责**: 实现 "Synthesis Prime" 协议，编排多智能体协作。
    *   **运行模式**: **Generator (生成器)**。通过 `yield` 关键字实时输出进度、日志和中间草稿，支持流式前端。
    *   **智能体编排**:
        1.  `Strategist`: 分析意图，决定策略 (Mode A/B)。
        2.  `Architect`: 起草初始 Prompt。
        3.  `Critic` & `Refiner`: 进入 `while` 循环进行对抗性优化 (默认 Max Rounds = 3)。

*   **`storage.py` (持久化层)**:
    *   **职责**: 管理任务数据的读写。
    *   **数据结构**:
        *   `task_details.json`: 包含原始 Prompt、完整对话历史 (List of Dicts)、元数据。
        *   `final_prompt.md`: 纯净的最终交付物，便于用户直接使用。
    *   **导出功能**: 支持将最终 Prompt 导出到任意指定路径。

## 2. 交互层规范 (Presentation Layer)

### 2.1 Gradio Web UI (`app.py`)
*   **布局**: 双栏布局 (Input/Output) + 折叠式日志区 (Accordion)。
*   **流式更新**: 监听 `refiner.run_refinement_stream()`，实时更新：
    *   `Status`: 当前正在进行的步骤 (e.g., "🤔 Critic is analyzing...")。
    *   `History`: 委员会的讨论记录。
    *   `Draft`: 当前版本的 Prompt 预览。
*   **下载功能**: 生成完成后，通过 `gr.DownloadButton` 提供 `final_prompt.md` 的下载。

### 2.2 CLI (`cli.py`)
*   **命令**: `python src/cli.py`
*   **参数**:
    *   `--prompt "..."`: 原始提示词 (必填)。
    *   `--output "./path/to/file.md"`: 导出路径 (选填)。
*   **输出**: 打印进度日志至 stdout，最终结果保存至文件。

## 3. 数据流向 (Data Flow)

1.  **Input**: 用户输入原始 Prompt。
2.  **Strategy**: `Strategist` 分析并生成策略文档。
3.  **Drafting**: `Architect` 基于策略生成 Draft v1。
4.  **Refinement Loop**:
    *   `Critic` 评估 Draft vX -> 输出 Critique。
    *   `Refiner` 基于 Critique 修改 -> 输出 Draft v(X+1)。
5.  **Persistence**: `Storage` 保存最终状态到 `tasks/{timestamp}_{uuid}/`。
6.  **Export**: 用户下载或导出 `.md` 文件。

## 4. 限制与边界 (Constraints)

*   **并发性**: 当前基于本地文件系统存储，不支持高并发写入。
*   **上下文窗口**: 依赖 LLM 的 Context Window，极长对话可能会被截断（当前未做自动截断处理）。
*   **网络依赖**: 必须可访问 Google AI Studio 或 Vertex AI 服务端点。

## 5. 重建指南 (Reconstruction Guide)

1.  **环境**: Python 3.10+, Conda 推荐。
2.  **依赖**: `pip install -r requirements.txt` (含 `gradio`, `google-generativeai`, `google-cloud-aiplatform`)。
3.  **配置**: 复制 `sys_init/.env.example` 为 `sys_init/.env` 并填入 API Key。
4.  **运行**: 启动 `src/app.py` 即可恢复服务。
