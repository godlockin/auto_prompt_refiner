import os
import json
import time
import uuid
from src.config import Config

class TaskBox:
    def __init__(self):
        self.tasks_dir = Config.TASKS_DIR
        if not os.path.exists(self.tasks_dir):
            os.makedirs(self.tasks_dir)

    def save_task(self, task_data: dict) -> str:
        """
        Saves the task result to the file system.
        Returns the path to the saved task directory.
        """
        timestamp = int(time.time())
        task_id = str(uuid.uuid4())[:8]
        folder_name = f"{timestamp}_{task_id}"
        folder_path = os.path.join(self.tasks_dir, folder_name)
        
        os.makedirs(folder_path, exist_ok=True)
        
        file_path = os.path.join(folder_path, "task_details.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(task_data, f, indent=4, ensure_ascii=False)
            
        # Also save the final prompt as a separate Markdown file for easy copying
        prompt_path = os.path.join(folder_path, "final_prompt.md")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(task_data.get("final_prompt", ""))
            
        return folder_path

    def list_tasks(self):
        """Returns a list of task directories."""
        if not os.path.exists(self.tasks_dir):
            return []
        return sorted(os.listdir(self.tasks_dir), reverse=True)

    def load_task(self, folder_name):
        path = os.path.join(self.tasks_dir, folder_name, "task_details.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def export_prompt(self, content: str, output_path: str):
        """Exports the prompt content to a specific path."""
        try:
            # Ensure directory exists
            output_dir = os.path.dirname(os.path.abspath(output_path))
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False
