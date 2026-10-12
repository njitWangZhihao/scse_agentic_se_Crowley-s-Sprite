import ast
import json
from pathlib import Path
from ollama import chat

SYSTEM_PROMPT = """
You are a Test Agent for a robot navigation software system.
Generate a complete pytest test module for decide_next_move(state).

Use the requirements, the Planner Agent's plan, and the Developer Agent's code.
The input state has exactly six boolean keys:
goal_ahead, goal_on_left, goal_on_right, front_blocked, left_blocked, right_blocked.
The function returns FORWARD, LEFT, RIGHT, or STOP.

Import the function with this exact statement:
from generated.navigation_logic import decide_next_move

Create at least four test_ functions with assert statements.
Cover a clear path, a goal to either side, blocked preferred directions, safe alternatives,
and the case where all directions are blocked.
Use itertools.product with repeat=6 to test all 64 boolean input combinations.
For ambiguous combinations, check valid and safe actions rather than guessing
an exact action not defined by the requirements.
Never copy an incorrect decision from the Developer code as an expected result.

Return only executable Python source code.
Do not include markdown, emojis, check marks, arrows, explanations, or comments.
"""


def validate_test_code(code):
    if not isinstance(code, str) or not code.strip():
        print("Validation Error: Generated test code is empty.")
        return False

    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        print(f"Validation Error: {error}")
        return False

    tests = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    ]

    if len(tests) < 4:
        print("Validation Error: At least four test functions are required.")
        return False

    required_parts = [
        "from generated.navigation_logic import decide_next_move",
        "assert",
        "product",
        "decide_next_move("
    ]

    for part in required_parts:
        if part not in code:
            print(f"Validation Error: Missing required test content: {part}")
            return False

    return True


def clean_test_code(raw_content):
    code = (raw_content or "").strip()

    if "</think>" in code:
        code = code.split("</think>", 1)[1].strip()

    if "```" in code:
        sections = code.split("```")
        for section in sections[1::2]:
            section = section.strip()
            if section.lower().startswith("python\n"):
                section = section.split("\n", 1)[1].strip()
            if "def test_" in section:
                return section

    return code


def run_test_agent(requirements, plan):
    if not isinstance(requirements, dict) or not isinstance(plan, dict):
        print("Test Agent Error: Requirements and plan must be dictionaries.")
        return None

    navigation_path = Path("generated/navigation_logic.py")

    if not navigation_path.exists():
        print(f"Test Agent Error: {navigation_path} does not exist.")
        return None

    navigation_code = navigation_path.read_text(encoding="utf-8")

    prompt_content = (
        "Requirements:\n"
        f"{json.dumps(requirements, indent=4, ensure_ascii=False)}\n\n"
        "Plan:\n"
        f"{json.dumps(plan, indent=4, ensure_ascii=False)}\n\n"
        "Navigation code:\n"
        f"{navigation_code}\n\n"
        "Generate the complete Python pytest module following all instructions."
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt_content}
    ]

    print("Calling Qwen3:8b model via Ollama for test generation...")

    for attempt in range(1, 4):
        try:
            response = chat(model="qwen3:8b", messages=messages)
        except Exception as error:
            print(f"Test Agent Error: {error}")
            return None

        raw_content = response.message.content or ""
        generated_code = clean_test_code(raw_content)

        if validate_test_code(generated_code):
            print(f"Test code passed validation on attempt {attempt}.")
            return generated_code

        print(f"Test generation attempt {attempt} failed validation.")

        messages.append({
            "role": "assistant",
            "content": raw_content
        })

        messages.append({
            "role": "user",
            "content": (
                "The previous response was not a valid pytest module. "
                "Return the complete module using only valid Python syntax. "
                "Use at least four test functions, assert statements, "
                "and itertools.product with repeat=6. "
                "Do not include emojis, check marks, arrows, prose, comments, or markdown."
            )
        })

    failure_path = Path("artifacts/test_agent_failed_response.txt")
    failure_path.parent.mkdir(parents=True, exist_ok=True)
    failure_path.write_text(raw_content, encoding="utf-8")

    print(f"Test Agent failed after three attempts. Response saved to {failure_path}")
    return None


def main():
    requirements_path = Path("artifacts/requirements.json")

    if not requirements_path.exists():
        requirements_path = Path("requirements.json")

    plan_path = Path("artifacts/plan.json")

    if not requirements_path.exists() or not plan_path.exists():
        print("Error: Requirements or plan file is missing.")
        return

    with open(requirements_path, "r", encoding="utf-8") as file:
        requirements = json.load(file)

    with open(plan_path, "r", encoding="utf-8") as file:
        plan = json.load(file)

    generated_code = run_test_agent(requirements, plan)

    if generated_code is None:
        return

    output_path = Path("artifacts/test_agent_generated.py")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(generated_code + "\n", encoding="utf-8")

    print(f"Generated tests saved to {output_path}")


if __name__ == "__main__":
    main()
