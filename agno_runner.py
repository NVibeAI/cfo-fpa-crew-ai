# agno_runner.py
from agno_config import get_agent_config, get_workflow, llm_client
import os
import json
from datetime import datetime

def run_agent_task(agent_key, task_description, context=None):
    """
    Run a single agent task using provider-agnostic LLM client.
    
    Args:
        agent_key: Key identifying the agent
        task_description: The task to perform
        context: Previous task outputs for context
    
    Returns:
        The agent's response
    """
    agent = get_agent_config(agent_key)
    
    # Build messages
    messages = [
        {"role": "system", "content": agent["system_prompt"]}
    ]
    
    # Add context from previous tasks if available
    if context:
        context_str = "\n\n".join([
            f"=== Output from {name} ===\n{output}" 
            for name, output in context.items()
        ])
        messages.append({
            "role": "user",
            "content": f"Previous Analysis Context:\n\n{context_str}\n\n---\n\nYour Task:\n{task_description}"
        })
    else:
        messages.append({
            "role": "user",
            "content": task_description
        })
    
    print(f"\n🤖 Running: {agent['name']}")
    print(f"📝 Task: {task_description[:100]}...")
    
    try:
        # Use provider-agnostic LLM client
        output = llm_client.chat_completion(messages)
        print(f"✅ Completed: {agent['name']}")
        
        return output
    
    except Exception as e:
        print(f"❌ Error in {agent['name']}: {e}")
        return f"Error: {str(e)}"

def run_agno_workflow(custom_tasks=None):
    """
    Executes the complete FP&A workflow.
    
    Args:
        custom_tasks: Optional dictionary with custom prompts for each agent
    """
    print("🚀 Starting FP&A Workflow...")
    print("="*60)
    
    try:
        workflow = get_workflow(custom_tasks)
        outputs = {}
        context = {}
        
        # Create outputs directory
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        
        # Run each task in sequence
        for i, task_config in enumerate(workflow):
            agent_key = task_config["agent"]
            task_description = task_config["task"]
            depends_on = task_config.get("depends_on", [])
            
            # Build context from dependencies
            task_context = {}
            if depends_on:
                for dep in depends_on:
                    if dep in context:
                        agent_config = get_agent_config(dep)
                        task_context[agent_config["name"]] = context[dep]
            
            # Run the task
            output = run_agent_task(agent_key, task_description, task_context)
            
            # Store output
            agent_config = get_agent_config(agent_key)
            agent_name = agent_config["name"]
            outputs[agent_name] = output
            context[agent_key] = output
            
            # Save individual output
            safe_name = agent_name.replace(" ", "_").lower()
            file_path = os.path.join(output_dir, f"{safe_name}_output.txt")
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"Agent: {agent_name}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"{'='*60}\n\n")
                f.write(output)
            
            print(f"💾 Saved: {file_path}")
        
        # Save complete workflow output
        complete_output = "\n\n".join([
            f"{'='*60}\n{name}\n{'='*60}\n\n{output}"
            for name, output in outputs.items()
        ])
        
        with open(os.path.join(output_dir, "complete_workflow_output.txt"), "w", encoding="utf-8") as f:
            f.write(f"FP&A Workflow - Complete Output\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"{'='*60}\n\n")
            f.write(complete_output)
        
        # Save metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "workflow_name": "FP&A CFO Workflow",
            "tasks_completed": len(workflow),
            "status": "success",
            "custom_tasks_used": custom_tasks is not None
        }
        
        with open(os.path.join(output_dir, "workflow_metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"✅ Workflow completed successfully!")
        print(f"📁 Outputs saved to: {output_dir}/")
        print(f"{'='*60}")
        
        return outputs
    
    except Exception as e:
        print(f"\n❌ Error running workflow: {e}")
        import traceback
        traceback.print_exc()
        
        # Save error log
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        
        with open(os.path.join(output_dir, "error_log.txt"), "w", encoding="utf-8") as f:
            f.write(f"Error occurred at: {datetime.now().isoformat()}\n")
            f.write(f"{'='*60}\n\n")
            f.write(str(e))
            f.write("\n\n")
            f.write(traceback.format_exc())
        
        raise

if __name__ == "__main__":
    results = run_agno_workflow()
    
    print("\n" + "="*60)
    print("WORKFLOW RESULTS SUMMARY")
    print("="*60)
    
    for agent_name, output in results.items():
        print(f"\n{'='*60}")
        print(f"Agent: {agent_name}")
        print(f"{'='*60}")
        preview = output[:300] + "..." if len(output) > 300 else output
        print(preview)