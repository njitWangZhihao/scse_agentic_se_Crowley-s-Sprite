import json
import os
import shutil
import subprocess
import sys
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path

from test_agent import run_test_agent

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"
GENERATED = ROOT / "generated"
TRACE = ROOT / "trace.log"


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, value):
        for stream in self.streams:
            stream.write(value)

    def flush(self):
        for stream in self.streams:
            stream.flush()


def log(message):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    print(line)
    with open(TRACE, "a", encoding="utf-8") as file:
        file.write(line + "\n")


def read_json(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def run_script(label, script, arguments=None, allow_failure=False):
    if not script.startswith("-") and not (ROOT / script).is_file():
        raise FileNotFoundError(f"Cannot run {label}: {script} is missing")

    command = [sys.executable, script] + (arguments or [])
    log(f"START {label}: {' '.join(command)}")

    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONUTF8"] = "1"

    result = subprocess.run(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
    )

    if result.stdout:
        with open(TRACE, "a", encoding="utf-8") as file:
            file.write(result.stdout + "\n")
        print(result.stdout[-2500:])

    log(f"END {label}: return code {result.returncode}")

    if result.returncode != 0 and not allow_failure:
        raise RuntimeError(f"{label} failed with exit code {result.returncode}")

    return result.returncode == 0


def evaluate(use_saved_benchmark):
    requirements = read_json(ARTIFACTS / "requirements.json")
    plan = read_json(ARTIFACTS / "plan.json")

    log("START Test Agent")
    with open(TRACE, "a", encoding="utf-8") as trace_file:
        with redirect_stdout(Tee(sys.stdout, trace_file)):
            code = run_test_agent(requirements, plan)

    if not code:
        raise RuntimeError("Test Agent did not generate valid test code")

    tests_path = ARTIFACTS / "test_agent_generated.py"
    tests_path.write_text(code + "\n", encoding="utf-8")
    log(f"Test Agent created {tests_path}")

    tests_passed = run_script(
        "Pytest",
        "-m",
        ["pytest", "artifacts/test_agent_generated.py", "-v"],
        True,
    )

    if not tests_passed:
        log("WARNING: Generated pytest tests failed")

    run_script("Simulation Runner", "runner.py")
    simulation_report = read_json(ARTIFACTS / "simulation_report.json")

    simulation_passed = (
        simulation_report["total_scenarios"] > 0
        and simulation_report["passed_scenarios"] == simulation_report["total_scenarios"]
    )

    log(
        f"Simulation: {simulation_report['passed_scenarios']}/"
        f"{simulation_report['total_scenarios']} scenarios passed"
    )

    run_script("Reviewer Agent", "reviewer_agent.py")
    review = read_json(ARTIFACTS / "review_report.json")
    log(f"Reviewer needs_revision={review['needs_revision']}")

    benchmark_arguments = ["--saved"] if use_saved_benchmark else []
    run_script("IR-SIM Benchmark", "benchmark_irsim.py", benchmark_arguments)
    benchmark = read_json(ARTIFACTS / "irsim_benchmark_report.json")

    log(
        f"Benchmark: success_rate={benchmark['success_rate']}, "
        f"efficiency_rate={benchmark['efficiency_rate']}"
    )

    run_script("Benchmark Reviewer", "reviewer_benchmark_agent.py")
    benchmark_review = read_json(ARTIFACTS / "benchmark_review_report.json")
    log(f"Benchmark Reviewer needs_revision={benchmark_review['needs_revision']}")

    benchmark_passed = (
        benchmark["success_rate"] == 1.0
        and benchmark["efficiency_rate"] == 1.0
    )

    needs_revision = (
        bool(review["needs_revision"])
        or bool(benchmark_review["needs_revision"])
        or not simulation_passed
        or not benchmark_passed
    )

    return needs_revision, tests_passed, requirements, plan, review, benchmark


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    resume = "--resume" in sys.argv
    use_saved = "--saved" in sys.argv

    if resume and use_saved:
        raise ValueError("Use either --resume or --saved, not both")

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    GENERATED.mkdir(parents=True, exist_ok=True)

    if not resume:
        TRACE.write_text("", encoding="utf-8")

    navigation_path = GENERATED / "navigation_logic.py"
    backup_path = GENERATED / "navigation_logic_before_pipeline.py"

    log("Phase 4 Integration and Simulation started")

    try:
        if resume or use_saved:
            if resume:
                log("Resume mode: reusing completed Analyst, Planner and Developer artifacts")
                log("Resume mode: running fresh tests and all four IR-SIM worlds")
            else:
                log("Saved mode: reusing existing artifacts and saved IR-SIM reports")

            read_json(ARTIFACTS / "requirements.json")
            read_json(ARTIFACTS / "plan.json")

            if not navigation_path.exists():
                raise FileNotFoundError(f"Missing navigation code: {navigation_path}")

            log("Analyst, Planner and Developer artifacts loaded successfully")
        else:
            brief_path = ROOT / "brief.txt"

            if not brief_path.exists():
                raise FileNotFoundError("brief.txt is required for the full pipeline")

            log(
                f"Loaded brief.txt "
                f"({len(brief_path.read_text(encoding='utf-8'))} characters)"
            )

            if navigation_path.exists():
                shutil.copy2(navigation_path, backup_path)
                log(f"Backed up working navigation code to {backup_path}")

            run_script("Analyst Agent", "run_analyst.py")
            run_script("Planner Agent", "run_planner.py")
            run_script("Developer Agent", "run_developer.py")

            if not navigation_path.exists():
                raise FileNotFoundError(
                    "Developer did not create generated/navigation_logic.py"
                )

        needs_revision, tests_passed, requirements, plan, review, benchmark = evaluate(
            use_saved
        )

        if needs_revision and not use_saved:
            log("Review detected failures; starting Developer Revision")

            from developer_agent import run_developer_revision

            original_code = navigation_path.read_text(encoding="utf-8")
            benchmark_review = read_json(
                ARTIFACTS / "benchmark_review_report.json"
            )

            review_notes = {
                "simulation_review": review,
                "benchmark_review": benchmark_review,
            }

            with open(TRACE, "a", encoding="utf-8") as trace_file:
                with redirect_stdout(Tee(sys.stdout, trace_file)):
                    revised_code = run_developer_revision(
                        original_code,
                        review_notes,
                        benchmark,
                        requirements,
                        plan,
                    )

            if not revised_code:
                raise RuntimeError("Developer Revision failed")

            navigation_path.write_text(revised_code + "\n", encoding="utf-8")
            log("Developer Revision updated generated/navigation_logic.py")

            needs_revision, tests_passed, _, _, _, _ = evaluate(False)

        if needs_revision or not tests_passed:
            log("FINISHED WITH WARNINGS: review or generated tests reported issues")
        else:
            log("SUCCESS: completed requested stages and generated tests")

        if use_saved:
            log("Saved mode used historical IR-SIM data")
        elif resume:
            log("Resume mode used previously generated Analyst, Planner and Developer artifacts")

        log("Trace written to trace.log")

    except Exception as error:
        log(f"PIPELINE ERROR: {type(error).__name__}: {error}")
        log("Check trace.log for the preceding stage output")
        raise


if __name__ == "__main__":
    main()
