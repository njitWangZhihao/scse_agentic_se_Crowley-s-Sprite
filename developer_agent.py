import ast
import json
from pathlib import Path
from ollama import chat

SYSTEM_PROMPT = """
You are a Developer Agent for a robot navigation software system.
Your goal is to write Python code based on the provided JSON navigation plan.
You MUST output ONLY valid Python code. Do not include markdown formatting.
The code MUST define decide_next_move(state).
The state dictionary contains six boolean keys:
goal_ahead, goal_on_left, goal_on_right, front_blocked, left_blocked, right_blocked.
Return only FORWARD, LEFT, RIGHT, or STOP.
"""

REVISION_SYSTEM_PROMPT = SYSTEM_PROMPT + """
You are revising robot navigation code based on simulation failures.

Analyze the original code, requirements, plan, reviewer feedback, and IR-SIM report.

The robot must reach its destination while avoiding obstacles.

Important navigation rules:
1. If the goal is ahead and the front is clear, return FORWARD.
2. If the goal is on the left and the left direction is clear, prefer LEFT.
3. If the goal is on the right and the right direction is clear, prefer RIGHT.
4. If the preferred direction is blocked, choose another safe available direction.
5. If the front is blocked but the left is clear, the robot may turn LEFT.
6. If the front and left are blocked but the right is clear, turn RIGHT.
7. If the goal is on the right but the right is blocked, consider turning LEFT to avoid the obstacle.
8. If the goal is on the left but the left is blocked, consider turning RIGHT to avoid the obstacle.
9. Avoid repeatedly switching between LEFT and RIGHT near the same obstacle.
10. Return STOP when all three directions are blocked.
11. Never return a movement action toward a direction marked blocked.
12. Prefer continuing safe navigation instead of stopping prematurely.

Use a consistent direction preference when multiple safe actions are possible.
Do not introduce additional required state keys.
Keep the function compatible with the existing IR-SIM simulation.

The previous IR-SIM attempts failed because the robot stopped before reaching the goal.
The revision must improve obstacle avoidance and goal completion.

Keep the function name decide_next_move(state).
Keep the six existing boolean input keys.
Return only FORWARD, LEFT, RIGHT, or STOP.

Output only complete valid Python code.
Do not include markdown, explanations, comments, or diagrams.
"""


def validate_code(code_string):
    if not isinstance(code_string, str) or not code_string.strip():
        print("Validation Error: The output is empty or not a string.")
        return False

    try:
        tree = ast.parse(code_string)
    except SyntaxError as error:
        print(f"Validation Error: Invalid Python syntax. {error}")
        return False

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "decide_next_move":
            if len(node.args.args) == 1 and node.args.args[0].arg == "state":
                return True

    print("Validation Error: decide_next_move(state) is missing.")
    return False


def clean_code(raw_content):
    code = (raw_content or "").strip()

    if "</think>" in code:
        code = code.split("</think>", 1)[1].strip()

    if "```" in code:
        sections = code.split("```")
        for section in sections[1::2]:
            section = section.strip()
            if section.lower().startswith("python\n"):
                section = section.split("\n", 1)[1].strip()
            if "def decide_next_move(" in section:
                return section

    start = code.find("def decide_next_move(")
    if start >= 0:
        code = code[start:]

    return code.strip()



def run_developer(plan):
    prompt_content = (
        "Here is the navigation plan from the Planner Agent:\n"
        f"{json.dumps(plan, ensure_ascii=False)}\n\n"
        "Generate complete, valid Python code for decide_next_move(state).\n"
        "The function must return FORWARD, LEFT, RIGHT, or STOP.\n"
        "Prefer moving toward the goal when the direction is clear.\n"
        "If the preferred direction is blocked, choose another safe available direction.\n"
        "Never move toward a blocked direction.\n"
        "Return STOP when all directions are blocked.\n"
        "Return only Python code without markdown, explanations, or comments."
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt_content}
    ]

    print("Calling Qwen3:8b model via Ollama for Development...")

    for attempt in range(1, 4):
        try:
            response = chat(
                model="qwen3:8b",
                messages=messages
            )
        except Exception as error:
            raise RuntimeError(f"Developer Agent request failed: {error}") from error

        raw_content = response.message.content or ""
        generated_code = clean_code(raw_content)

        if validate_code(generated_code):
            print(f"Developer code passed validation on attempt {attempt}.")
            return generated_code

        print(f"Developer attempt {attempt} failed validation.")

        messages.append({
            "role": "assistant",
            "content": raw_content
        })

        messages.append({
            "role": "user",
            "content": (
                "Your previous response was not valid Python code. "
                "Generate the complete decide_next_move(state) function again. "
                "Use only valid Python statements. "
                "Do not include markdown, explanations, emojis, arrows, or comments."
            )
        })

    output_path = Path("artifacts/developer_failed_response.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(raw_content, encoding="utf-8")

    raise RuntimeError(
        "Developer Agent failed after three attempts. "
        f"Last model response saved to {output_path}"
    )



def run_developer_revision(original_code, review_notes, benchmark_report, requirements, plan):
    if not isinstance(original_code, str) or not original_code.strip():
        print("Revision Error: Original navigation code is missing.")
        return None

    prompt_content = (
        "Original navigation code:\n"
        f"{original_code}\n\n"
        "Review notes:\n"
        f"{json.dumps(review_notes, indent=4, ensure_ascii=False)}\n\n"
        "IR-SIM report:\n"
        f"{json.dumps(benchmark_report, indent=4, ensure_ascii=False)}\n\n"
        "Requirements:\n"
        f"{json.dumps(requirements, indent=4, ensure_ascii=False)}\n\n"
        "Navigation plan:\n"
        f"{json.dumps(plan, indent=4, ensure_ascii=False)}\n\n"
        "Generate a corrected, complete Python implementation of decide_next_move(state). "
        "Focus on avoiding premature STOP actions and improving obstacle avoidance."
    )

    messages = [
        {"role": "system", "content": REVISION_SYSTEM_PROMPT},
        {"role": "user", "content": prompt_content},
    ]

    print("Calling Qwen3:8b model via Ollama for Development Revision...")

    for attempt in range(1, 4):
        try:
            response = chat(model="qwen3:8b", messages=messages)
        except Exception as error:
            print(f"Revision Error: {error}")
            return None

        raw_content = response.message.content or ""
        revised_code = clean_code(raw_content)

        if validate_code(revised_code):
            output_path = Path("generated/navigation_logic_revised.py")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as file:
                file.write(revised_code + "\n")

            print(f"Revision passed validation on attempt {attempt}.")
            print(f"Revised navigation code saved to {output_path}")
            return revised_code

        print(f"Revision attempt {attempt} failed validation.")

        messages.append({
            "role": "assistant",
            "content": raw_content
        })

        messages.append({
            "role": "user",
            "content": (
                "The previous output was not valid Python code. "
                "Regenerate the complete decide_next_move(state) function. "
                "Use only Python statements and valid return values. "
                "Do not include arrows, explanations, markdown, or comments."
            ),
        })

    print("Revision Error: Failed after three attempts.")
    print("Last model response:\n", raw_content)
    return None


def main():
    requirements_path = Path("artifacts/requirements.json")

    if not requirements_path.exists():
        requirements_path = Path("requirements.json")

    plan_path = Path("artifacts/plan.json")
    review_path = Path("artifacts/review_report.json")
    benchmark_path = Path("artifacts/irsim_benchmark_report.json")

    if not benchmark_path.exists():
        benchmark_path = Path("artifacts/irsim_report.json")

    navigation_path = Path("generated/navigation_logic.py")

    for path in [
        requirements_path,
        plan_path,
        review_path,
        benchmark_path,
        navigation_path
    ]:
        if not path.exists():
            print(f"Revision Error: Required file not found: {path}")
            return

    with open(requirements_path, "r", encoding="utf-8") as file:
        requirements = json.load(file)

    with open(plan_path, "r", encoding="utf-8") as file:
        plan = json.load(file)

    with open(review_path, "r", encoding="utf-8") as file:
        review_notes = json.load(file)

    with open(benchmark_path, "r", encoding="utf-8") as file:
        benchmark_report = json.load(file)

    with open(navigation_path, "r", encoding="utf-8") as file:
        original_code = file.read()

    print(f"Using IR-SIM report: {benchmark_path}")

    run_developer_revision(
        original_code,
        review_notes,
        benchmark_report,
        requirements,
        plan
    )


if __name__ == "__main__":
    main()

