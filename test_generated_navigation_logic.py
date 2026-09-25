import sys
from pathlib import Path

sys.path.append(str(Path("generated").absolute()))
from navigation_logic import decide_next_move

def run_tests():
    print("Running tests for decide_next_move function...")
    test_state_1 = {
        "goal_ahead": True, "goal_on_left": False, "goal_on_right": False,
        "front_blocked": False, "left_blocked": False, "right_blocked": False 
    }
    action1 = decide_next_move(test_state_1)
    print(f"Test 1 (Goal Ahead, Front Clear) - Expected: FORWARD, Got: {action1}")
    assert action1 == "FORWARD", "Test 1 Failed"

    test_state_2 = {
        "goal_ahead": False, "goal_on_left": True, "goal_on_right": False,
        "front_blocked": True, "left_blocked": False, "right_blocked": False
    }
    action2 = decide_next_move(test_state_2)
    print(f"Test 2 (Front Blocked, Goal Left) - Expected: LEFT, Got: {action2}")
    assert action2 == "LEFT", "Test 2 Failed"

    test_state_3 = {
        "goal_ahead": True, "goal_on_left": False, "goal_on_right": False,
        "front_blocked": True, "left_blocked": True, "right_blocked": True
    }
    action3 = decide_next_move(test_state_3)
    print(f"Test 3 (All Blocked) - Expected: STOP, Got: {action3}")
    assert action3 == "STOP", "Test 3 Failed"

    print("All tests passed successfully!")

if __name__ == "__main__":
    run_tests()
