import json
from itertools import product
from pathlib import Path
from generated.navigation_logic import decide_next_move

STATE_KEYS = [
    "goal_ahead",
    "goal_on_left",
    "goal_on_right",
    "front_blocked",
    "left_blocked",
    "right_blocked",
]

VALID_ACTIONS = ["FORWARD", "LEFT", "RIGHT", "STOP"]


def expected_action(state):
    if state["front_blocked"] and state["left_blocked"] and state["right_blocked"]:
        return "STOP"

    if state["goal_ahead"] and not state["goal_on_left"] and not state["goal_on_right"]:
        if not state["front_blocked"]:
            return "FORWARD"

    if state["goal_on_left"] and not state["goal_ahead"] and not state["goal_on_right"]:
        if state["front_blocked"] and not state["left_blocked"] and state["right_blocked"]:
            return "LEFT"

    if state["goal_on_right"] and not state["goal_ahead"] and not state["goal_on_left"]:
        if state["front_blocked"] and state["left_blocked"] and not state["right_blocked"]:
            return "RIGHT"

    return None


def is_safe_action(state, action):
    if action not in VALID_ACTIONS:
        return False

    if action == "FORWARD" and state["front_blocked"]:
        return False
    if action == "LEFT" and state["left_blocked"]:
        return False
    if action == "RIGHT" and state["right_blocked"]:
        return False

    return True


def run_simulation():
    results = []

    for number, values in enumerate(product([False, True], repeat=6), start=1):
        state = dict(zip(STATE_KEYS, values))
        expected = expected_action(state)
        error = None

        try:
            actual = decide_next_move(state)
            if expected is None:
                passed = is_safe_action(state, actual)
            else:
                passed = actual == expected
        except Exception as exception:
            actual = None
            passed = False
            error = str(exception)

        result = {
            "scenario": number,
            "state": state,
            "expected": expected if expected is not None else "VALID_SAFE_ACTION",
            "actual": actual,
            "passed": passed,
        }

        if error is not None:
            result["error"] = error

        results.append(result)

    total = len(results)
    passed_count = sum(result["passed"] for result in results)
    failed_count = total - passed_count

    return {
        "total_scenarios": total,
        "passed_scenarios": passed_count,
        "failed_scenarios": failed_count,
        "success_rate": passed_count / total,
        "results": results,
    }


def main():
    report = run_simulation()
    output_path = Path("artifacts/simulation_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    print(f"Total scenarios: {report['total_scenarios']}")
    print(f"Passed scenarios: {report['passed_scenarios']}")
    print(f"Failed scenarios: {report['failed_scenarios']}")
    print(f"Success rate: {report['success_rate']:.2%}")
    print(f"Simulation report saved to {output_path}")


if __name__ == "__main__":
    main()
