import sys
import os

# Add project root to path to ensure absolute imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gradio as gr
from src.refiner import PromptRefiner
from src.storage import TaskBox
import json
import uuid

# Initialize core components
refiner = PromptRefiner()
storage = TaskBox()

def format_history(history):
    formatted = ""
    for entry in history:
        formatted += f"### 👤 {entry['role']}\n\n{entry['content']}\n\n---\n\n"
    return formatted

def process_prompt_stream(user_input):
    if not user_input.strip():
        yield "Please enter a prompt.", "", "", None
        return
    
    # Generator loop
    for status_msg, history, current_draft in refiner.run_refinement_stream(user_input):
        history_md = format_history(history)
        # Update UI with current status + partial history + current draft (as preview)
        # We put status_msg in the "Final System Prompt" box temporarily to show progress
        status_display = f"### ⏳ PROCESSING: {status_msg}\n\n---\n\n{current_draft if current_draft else 'Generating draft...'}"
        yield status_display, history_md, None, None

    # Final save
    result = {
        "original_prompt": user_input,
        "final_prompt": current_draft,
        "discussion_history": history
    }
    task_folder = storage.save_task(result)
    
    # Prepare downloadable file
    # storage.save_task saves 'final_prompt.md' inside the task folder
    final_md_path = os.path.join(task_folder, "final_prompt.md")
    
    history_md = format_history(history)
    # Return path to download_btn to make it ready for download
    yield current_draft, history_md, json.dumps(result, indent=2, ensure_ascii=False), final_md_path

def load_history():
    tasks = storage.list_tasks()
    return gr.Dropdown(choices=tasks, interactive=True)

def show_task_details(task_folder):
    if not task_folder:
        return "", "", ""
    task = storage.load_task(task_folder)
    if not task:
        return "Error loading task.", "", ""
    
    history_md = format_history(task.get('discussion_history', []))
    return task.get('final_prompt', ''), history_md, json.dumps(task, indent=2, ensure_ascii=False)

def save_to_local_file(content):
    if not content or "### ⏳ PROCESSING" in content:
        return None
    
    # Save to a temporary file for download
    tmp_path = os.path.join(storage.tasks_dir, f"prompt_export_{uuid.uuid4().hex[:6]}.md")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    return tmp_path

# UI Construction
with gr.Blocks(title="Synthesis Prime: Auto Prompt Refiner", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🔮 Synthesis Prime: Auto Prompt Refiner")
    gr.Markdown("> **Cognitive Layer Status**: Online | **Engine**: Gemini-3.0-Pro-Preview (Fallback: Vertex AI)")
    
    with gr.Tabs():
        with gr.Tab("🚀 Refine Prompt"):
            with gr.Row():
                with gr.Column(scale=1):
                    input_prompt = gr.Textbox(label="Original Prompt (Input)", lines=10, placeholder="Describe what you want the AI to do...")
                    refine_btn = gr.Button("🔮 Ignite Refinement Protocol", variant="primary")
                
                with gr.Column(scale=1):
                    final_output = gr.Markdown(label="Final System Prompt (SOTA)")
                    # Initialize download button as invisible or disabled until ready
                    download_btn = gr.DownloadButton("💾 Save Result to Local", visible=True)
            
            with gr.Accordion("🧠 Cognitive Trace (Committee Discussion)", open=True): # Auto open to show progress
                discussion_log = gr.Markdown()
                raw_json = gr.JSON(label="Raw Data")

            refine_btn.click(
                process_prompt_stream,
                inputs=[input_prompt],
                outputs=[final_output, discussion_log, raw_json, download_btn]
            )
            
            # Remove the separate click handler for download_btn as it's now updated directly by the main process


        with gr.Tab("📜 Task History"):
            refresh_btn = gr.Button("🔄 Refresh List")
            task_selector = gr.Dropdown(label="Select Past Task", choices=storage.list_tasks())
            
            with gr.Row():
                history_final = gr.Markdown(label="Archived Prompt")
                history_log = gr.Markdown(label="Archived Discussion")
            
            refresh_btn.click(load_history, outputs=[task_selector])
            task_selector.change(show_task_details, inputs=[task_selector], outputs=[history_final, history_log, gr.JSON(visible=False)])

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
