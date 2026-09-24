import json
from pathlib import Path
from planner_agent import run_planner


## Create a function/logic that reads the requirements from requirements.json, 
# then calls the run_planner function with the requirements as input, and finally writes the validated plan to plan.json. 
def main():
    requirements_path = Path("artifacts") / "requirements.json"
    if not requirements_path.exists():
        requirements_path = Path("requirements.json")
    if not requirements_path.exists():
        print(f"Error: {requirements_path} does not exist.")
        return

    print(f"Reading requirements from {requirements_path}...")
    with open(requirements_path, "r", encoding="utf-8") as f:
        requirements = json.load(f)
    validated_plan = run_planner(requirements)
    if validated_plan:
        plan_path = Path("plan.json")
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(validated_plan, f, indent=4, ensure_ascii=False)
        print(f"Validated plan written to {plan_path}.")
    else:
        print("Failed to generate a validated plan.")

if __name__ == "__main__":
    main()
            
