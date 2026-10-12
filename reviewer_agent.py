import json
from pathlib import Path
from ollama import chat

SYSTEM_PROMPT = """
You are a Reviewer Agent for a robot navigation software system.
Review the simulation report and identify navigation problems.
Explain the likely cause and recommend specific improvements.

Return only a valid JSON object with exactly these four keys:
"issue": a string describing the problem or the absence of problems.
"likely_cause": a string explaining the possible cause.
"recommendation": a string describing what should be improved.
"needs_revision": a boolean, true or false.

If all simulated scenarios passed, say no issues were detected in the basic simulation
and set needs_revision to false.
If any scenarios failed, explain the failures and set needs_revision to true.
Do not claim that physical IR-SIM performance has been verified.
Do not include markdown, comments, or any text outside the JSON object.
"""


def validate_review(data):
    if not isinstance(data, dict):
        print("Validation Error: The review must be a JSON object.")
        return False

    required_keys = ["issue", "likely_cause", "recommendation", "needs_revision"]

    if set(data.keys()) != set(required_keys):
        print("Validation Error: The review has missing or unexpected keys.")
        return False

    for key in ["issue", "likely_cause", "recommendation"]:
        if not isinstance(data[key], str):
            print(f"Validation Error: {key} must be a string.")
            return False

    if not isinstance(data["needs_revision"], bool):
        print("Validation Error: needs_revision must be a boolean.")
        return False

    return True


def run_reviewer(simulation_report):
    if not isinstance(simulation_report, dict):
        print("Reviewer Error: The simulation report must be a dictionary.")
        return None

    failed_cases = [
        result
        for result in simulation_report.get("results", [])
        if result.get("passed") is False
    ]

    report_summary = {
        "total_scenarios": simulation_report.get("total_scenarios", 0),
        "passed_scenarios": simulation_report.get("passed_scenarios", 0),
        "failed_scenarios": simulation_report.get("failed_scenarios", 0),
        "success_rate": simulation_report.get("success_rate", 0),
        "failed_cases": failed_cases,
    }

    prompt_content = (
        "Review the following navigation simulation results:\n"
        + json.dumps(report_summary, indent=4, ensure_ascii=False)
    )

    print("Calling Qwen3:8b model via Ollama for simulation review...")

    try:
        response = chat(
            model="qwen3:8b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt_content},
            ],
        )
    except Exception as error:
        print(f"Reviewer Error: {error}")
        return None

    raw_content = (response.message.content or "").strip()

    if raw_content.startswith("```json"):
        raw_content = raw_content[7:-3].strip()
    elif raw_content.startswith("```"):
        raw_content = raw_content[3:-3].strip()

    try:
        review = json.loads(raw_content)
    except json.JSONDecodeError as error:
        print(f"Reviewer Error: Invalid JSON response: {error}")
        return None

    if not validate_review(review):
        return None

    return review


def main():
    report_path = Path("artifacts/simulation_report.json")

    if not report_path.exists():
        print(f"Error: {report_path} does not exist.")
        return

    with open(report_path, "r", encoding="utf-8") as file:
        simulation_report = json.load(file)

    review = run_reviewer(simulation_report)

    if review is None:
        print("Failed to generate a valid simulation review.")
        return

    output_path = Path("artifacts/review_report.json")

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(review, file, indent=4, ensure_ascii=False)

    print(json.dumps(review, indent=4, ensure_ascii=False))
    print(f"Review report saved to {output_path}")


if __name__ == "__main__":
    main()
