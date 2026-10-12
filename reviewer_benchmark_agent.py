import json
from pathlib import Path
from ollama import chat

SYSTEM_PROMPT = """
You are a Benchmark Reviewer Agent for a robot navigation software system.

Review the IR-SIM benchmark results and evaluate:
1. Safety: whether the robot avoided unsafe termination.
2. Goal completion: whether all environments reached their goals.
3. Efficiency: whether all environments completed within the efficient step limit.

You will receive the benchmark report and a deterministic review.
The deterministic review contains pass/fail decisions calculated from actual measurements.
You must follow those decisions and must not invent benchmark results.

Return only a valid JSON object with exactly these seven keys:
"issue": string
"likely_cause": string
"recommendation": string
"safety_passed": boolean
"goal_completion_passed": boolean
"efficiency_passed": boolean
"needs_revision": boolean

Explain the specific problems and recommend improvements.
If all quality checks passed, report that no issues were detected and no revision is required.
Do not include markdown or explanations outside the JSON object.
"""


def validate_benchmark_review(data):
    required_keys = [
        "issue",
        "likely_cause",
        "recommendation",
        "safety_passed",
        "goal_completion_passed",
        "efficiency_passed",
        "needs_revision"
    ]

    if not isinstance(data, dict):
        raise ValueError("Benchmark review must be a JSON object.")

    if set(data.keys()) != set(required_keys):
        raise ValueError("Benchmark review has missing or unexpected keys.")

    for key in ["issue", "likely_cause", "recommendation"]:
        if not isinstance(data[key], str):
            raise ValueError(f"{key} must be a string.")

    for key in [
        "safety_passed",
        "goal_completion_passed",
        "efficiency_passed",
        "needs_revision"
    ]:
        if not isinstance(data[key], bool):
            raise ValueError(f"{key} must be a boolean.")

    return True


def build_deterministic_review(benchmark_report):
    results = benchmark_report.get("results", [])

    if not isinstance(results, list):
        results = []

    safety_passed = len(results) > 0

    for result in results:
        if not isinstance(result, dict):
            safety_passed = False
            continue

        if "collision_or_done" not in result or "reached_goal" not in result:
            safety_passed = False
        elif result["collision_or_done"] and not result["reached_goal"]:
            safety_passed = False

    success_rate = benchmark_report.get("success_rate", 0)
    efficiency_rate = benchmark_report.get("efficiency_rate", 0)
    inefficient_count = benchmark_report.get("inefficient_success_worlds", 0)

    goal_completion_passed = success_rate >= 1.0
    efficiency_passed = efficiency_rate >= 1.0 and inefficient_count == 0

    needs_revision = not (
        safety_passed and goal_completion_passed and efficiency_passed
    )

    issues = []
    causes = []
    recommendations = []

    if not safety_passed:
        issues.append("Unsafe benchmark behavior detected")
        causes.append("One or more environments reported unsafe termination or missing safety data")
        recommendations.append("Improve obstacle detection and collision avoidance")

    if not goal_completion_passed:
        issues.append("Goal completion failure")
        causes.append("The robot failed to reach its goal in some environments")
        recommendations.append("Improve navigation decisions and alternative path selection")

    if not efficiency_passed:
        issues.append("Successful but inefficient navigation")
        causes.append("Some runs exceeded the efficient step limit or failed to complete efficiently")
        recommendations.append("Reduce unnecessary turns and improve path efficiency")

    if not needs_revision:
        issue = "No issues detected in the IR-SIM benchmark"
        likely_cause = "All environments reached their goals safely and efficiently"
        recommendation = "No code revision is required based on the benchmark results"
    else:
        issue = "; ".join(issues)
        likely_cause = "; ".join(causes)
        recommendation = "; ".join(recommendations)

    review = {
        "issue": issue,
        "likely_cause": likely_cause,
        "recommendation": recommendation,
        "safety_passed": safety_passed,
        "goal_completion_passed": goal_completion_passed,
        "efficiency_passed": efficiency_passed,
        "needs_revision": needs_revision
    }

    return review


def run_benchmark_reviewer(benchmark_report):
    if not isinstance(benchmark_report, dict):
        raise ValueError("Benchmark report must be a dictionary.")

    deterministic_review = build_deterministic_review(benchmark_report)

    prompt_content = (
        "IR-SIM benchmark report:\n"
        f"{json.dumps(benchmark_report, indent=4, ensure_ascii=False)}\n\n"
        "Deterministic review:\n"
        f"{json.dumps(deterministic_review, indent=4, ensure_ascii=False)}\n\n"
        "Review the benchmark and return the required JSON object."
    )

    print("Calling Qwen3:8b model via Ollama for Benchmark Review...")

    try:
        response = chat(
            model="qwen3:8b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt_content}
            ]
        )

        raw_content = response.message.content.strip()

        if raw_content.startswith("```json"):
            raw_content = raw_content[7:-3].strip()
        elif raw_content.startswith("```"):
            raw_content = raw_content[3:-3].strip()

        review = json.loads(raw_content)
        validate_benchmark_review(review)

        for key in [
            "safety_passed",
            "goal_completion_passed",
            "efficiency_passed",
            "needs_revision"
        ]:
            review[key] = deterministic_review[key]

        if not review["needs_revision"]:
            review["issue"] = deterministic_review["issue"]
            review["likely_cause"] = deterministic_review["likely_cause"]
            review["recommendation"] = deterministic_review["recommendation"]

        return review

    except Exception as error:
        print(f"Benchmark Reviewer Error: {error}")
        print("Using deterministic benchmark review.")
        return deterministic_review


def main():
    report_path = Path("artifacts/irsim_benchmark_report.json")

    if not report_path.exists():
        print(f"Error: {report_path} does not exist.")
        return

    with open(report_path, "r", encoding="utf-8") as file:
        benchmark_report = json.load(file)

    review = run_benchmark_reviewer(benchmark_report)

    output_path = Path("artifacts/benchmark_review_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(review, file, indent=4, ensure_ascii=False)

    print(json.dumps(review, indent=4, ensure_ascii=False))
    print(f"Benchmark review saved to {output_path}")


if __name__ == "__main__":
    main()







