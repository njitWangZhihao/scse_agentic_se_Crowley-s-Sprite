import json
from ollama import chat

def validate_requirements(data):
    """
    Validates that the Qwen output is a proper JSON dictionary
    and contains exactly the required keys and types.
    """
    if not isinstance(data, dict):
        raise ValueError("Validation Failed: Output is not a valid dictionary.")

    expected_keys = {"goal", "allowed_actions", "safe_stop", "avoid_obstacles"}
    actual_keys = set(data.keys())
    if expected_keys != actual_keys:
        raise ValueError(f"Validation Failed: Keys mismatch. Expected {expected_keys}, got {actual_keys}.")
    if not isinstance(data["goal"], str):
        raise ValueError("Validation Failed: 'goal' must be a string.")    
    if not isinstance(data["allowed_actions"], list):
        raise ValueError("Validation Failed: 'allowed_actions' must be a list.")        
    if not isinstance(data["safe_stop"], bool):
        raise ValueError("Validation Failed: 'safe_stop' must be a boolean.")        
    if not isinstance(data["avoid_obstacles"], bool):
        raise ValueError("Validation Failed: 'avoid_obstacles' must be a boolean.")

    valid_actions = {"FORWARD", "LEFT", "RIGHT", "STOP"}
    for action in data["allowed_actions"]:
        if action not in valid_actions:
            raise ValueError(f"Validation Failed: Invalid action found - '{action}'. Only FORWARD, LEFT, RIGHT, STOP are allowed.")

    return True

def run_analyst(brief_text):
    """
    Sends the brief text to Qwen with specific prompts,
    receives JSON, and validates it.
    """
    system_prompt = """
    You are an Analyst Agent. Your only responsibility is to analyze the customer's brief text and convert it into explicit software requirements.
    
    CRITICAL RULES:
    1. You must output ONLY a raw, valid JSON object. Do not include markdown tags (like ```json), explanations, or conversational text.
    2. The 'allowed_actions' list can ONLY contain actions exactly from this list: "FORWARD", "LEFT", "RIGHT", "STOP". No other actions exist.
    3. The final output must strictly follow this exact JSON structure:
    {
        "goal": "string describing the navigation objective",
        "allowed_actions": ["list", "of", "allowed", "actions"],
        "safe_stop": true or false,
        "avoid_obstacles": true or false
    }
    """

    user_prompt = f"""
    Convert the following human brief into the required JSON software requirements:
    
    {brief_text}
    """

    try:
        response = chat(
            model="qwen3:8b",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            format="json" 
        )
        
        raw_json_text = response.message.content

        parsed_data = json.loads(raw_json_text)
        
        if validate_requirements(parsed_data):
            return parsed_data

    except json.JSONDecodeError:
        print("Error: Qwen failed to produce valid JSON format.")
        print(f"Raw output was:\n{response.message.content}")
        return None
    except ValueError as e:
        print(e)
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None