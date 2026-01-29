import argparse
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.refiner import PromptRefiner
from src.storage import TaskBox

def main():
    parser = argparse.ArgumentParser(description="Synthesis Prime: Auto Prompt Refiner CLI")
    parser.add_argument("--prompt", "-p", type=str, required=True, help="The original prompt to refine")
    parser.add_argument("--output", "-o", type=str, help="Optional custom path to export the result (e.g., ./my_prompt.md)")
    
    args = parser.parse_args()
    
    print("🔮 Synthesis Prime CLI Online")
    print(f"Original Prompt: {args.prompt[:50]}...")
    
    refiner = PromptRefiner()
    storage = TaskBox()
    
    try:
        # Use synchronous method for CLI
        result = refiner.run_refinement(args.prompt)
        
        # Save to default storage
        task_path = storage.save_task(result)
        print(f"✅ Task saved to internal storage: {task_path}")
        
        # Export if requested
        if args.output:
            success = storage.export_prompt(result['final_prompt'], args.output)
            if success:
                print(f"💾 Result exported to: {args.output}")
            else:
                print(f"❌ Failed to export result to: {args.output}")
        
        print("\n" + "="*50 + "\n")
        print("📜 FINAL PROMPT:")
        print(result['final_prompt'])
        print("\n" + "="*50 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
