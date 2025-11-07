from crew_config import crew
import os

def run_all_tasks():
    print("🚀 Running all Crew AI tasks...")
    
    try:
        # In CrewAI 1.x, kickoff() returns a CrewOutput object
        result = crew.kickoff()
        outputs = {}

        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)

        # Access task outputs from the result
        for i, task in enumerate(crew.tasks):
            agent_role = task.agent.role
            
            # Get output from task
            if hasattr(task, 'output') and task.output:
                output_text = str(task.output.raw) if hasattr(task.output, 'raw') else str(task.output)
            else:
                output_text = "No output generated."
            
            # Clean filename from agent role
            safe_agent_name = agent_role.replace(" ", "_").replace(",", "").lower()
            safe_agent_name = ''.join(c for c in safe_agent_name if c.isalnum() or c == '_')
            file_path = os.path.join(output_dir, f"{safe_agent_name}_output.txt")

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(output_text)

            outputs[agent_role] = output_text
            print(f"✅ Saved output for: {agent_role}")

        # Also save the final crew output
        final_output = str(result.raw) if hasattr(result, 'raw') else str(result)
        with open(os.path.join(output_dir, "final_crew_output.txt"), "w", encoding="utf-8") as f:
            f.write(final_output)
        
        outputs["Final Crew Output"] = final_output

        return outputs
    
    except Exception as e:
        print(f"❌ Error running crew: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    results = run_all_tasks()
    for agent, output in results.items():
        print(f"\n{'='*60}")
        print(f"=== {agent} ===")
        print(f"{'='*60}")
        print(output)
        print()