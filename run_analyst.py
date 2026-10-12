import os
import json
from analyst_agent import run_analyst

def main():
    try:
        with open("brief.txt", "r", encoding="utf-8") as file:
            brief_text = file.read()
    except FileNotFoundError:
        print("Error: Could not find 'brief.txt'. Cannot proceed.")
        return

    print("Analyzing brief text via Qwen Analyst Agent...")

    validated_requirements = run_analyst(brief_text)

    if validated_requirements:
        os.makedirs("artifacts", exist_ok=True)
        save_path = os.path.join("artifacts", "requirements.json")
        with open(save_path, "w", encoding="utf-8") as out_file:
            json.dump(validated_requirements, out_file, indent=4, ensure_ascii=False)            
        print(f"Success! Requirements validated and saved to '{save_path}'.")
    else:
        print("Failed to generate valid requirements. Please check errors above and run again.")

if __name__ == "__main__":
    main()