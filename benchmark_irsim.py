import ast
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = PROJECT_DIR / "artifacts"

WORLD_FILES = {
    "easy": "irsim_worlds/world_easy.yaml",
    "medium": "irsim_worlds/world_medium.yaml",
    "hard": "irsim_worlds/world_hard.yaml",
    "custom": "irsim_worlds/world_custom.yaml",
}


def run_world(world_name, world_file):
    environment = os.environ.copy()
    environment["MPLBACKEND"] = "Agg"

    result = subprocess.run(
        [sys.executable, "test_irsim_with_agent.py", world_file],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        timeout=180,
    )

    log_path = ARTIFACTS_DIR / f"irsim_{world_name}_benchmark.log"

    with open(log_path, "w", encoding="utf-8") as file:
        file.write(result.stdout)
        file.write(result.stderr)

    if result.returncode != 0:
        raise RuntimeError(f"{world_name} simulation failed. Check {log_path}")

    if "IR-SIM report:" not in result.stdout:
        raise ValueError(f"No IR-SIM report found for {world_name}. Check {log_path}")

    report_text = result.stdout.rsplit("IR-SIM report:", 1)[1].strip().splitlines()[0]
    report = ast.literal_eval(report_text)

    if not isinstance(report, dict):
        raise ValueError(f"Invalid IR-SIM report for {world_name}")

    report_path = ARTIFACTS_DIR / f"irsim_{world_name}_report.json"

    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    return report


def load_saved_report(world_name):
    report_path = ARTIFACTS_DIR / f"irsim_{world_name}_report.json"

    with open(report_path, "r", encoding="utf-8") as file:
        return json.load(file)


def main():
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    use_saved_reports = "--saved" in sys.argv
    results = []

    for world_name, world_file in WORLD_FILES.items():
        print(f"Processing {world_name} world...")

        if use_saved_reports:
            report = load_saved_report(world_name)
        else:
            report = run_world(world_name, world_file)

        report["world"] = world_name
        results.append(report)

        print(f"Goal reached: {report['reached_goal']}, Steps: {report['steps_taken']}")

    total = len(results)
    reached_goal_count = sum(1 for result in results if result["reached_goal"])
    efficient_count = sum(
        1 for result in results
        if result["reached_goal"] and result["efficiency_status"] == "efficient"
    )
    inefficient_success_count = reached_goal_count - efficient_count
    failed_count = total - reached_goal_count
    average_steps = sum(result["steps_taken"] for result in results) / total

    benchmark_report = {
        "total_worlds": total,
        "goals_reached": reached_goal_count,
        "success_rate": reached_goal_count / total,
        "efficient_worlds": efficient_count,
        "inefficient_success_worlds": inefficient_success_count,
        "failed_worlds": failed_count,
        "efficiency_rate": efficient_count / total,
        "average_steps_taken": average_steps,
        "results": results,
    }

    output_path = ARTIFACTS_DIR / "irsim_benchmark_report.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(benchmark_report, file, indent=4)

    print(f"\nSuccess rate: {benchmark_report['success_rate']:.0%}")
    print(f"Efficiency rate: {benchmark_report['efficiency_rate']:.0%}")
    print(f"Average steps: {benchmark_report['average_steps_taken']}")
    print(f"Benchmark report saved to {output_path}")


if __name__ == "__main__":
    main()
