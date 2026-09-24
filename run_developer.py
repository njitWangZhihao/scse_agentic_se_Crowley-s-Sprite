import json
from pathlib import Path
from developer_agent import run_developer

def main():
    # Load the artifact from the Planner Agent
    plan_path = Path("plan.json")
    
    if not plan_path.exists():
        print(f"Error: {plan_path} does not exist. Please run the Planner Agent first.")
        return

    print(f"Reading plan from {plan_path}...")
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)
        
    # Call the developer agent with the plan
    validated_code = run_developer(plan)
    
    if validated_code:
        # Save the generated code to navigation_logic.py
        output_path = Path("navigation_logic.py")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(validated_code)
        print(f"Success! The validated Python code has been saved to '{output_path}'.")
    else:
        print("Failed to generate a validated Python code file.")

if __name__ == "__main__":
    main()