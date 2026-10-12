import pytest
from generated.navigation_logic import decide_next_move
import itertools

# Test case 1: Clear path ahead
def test_clear_path_ahead():
    state = {
        'goal_ahead': True,
        'goal_on_left': False,
        'goal_on_right': False,
        'front_blocked': False,
        'left_blocked': False,
        'right_blocked': False,
    }
    assert decide_next_move(state) == 'FORWARD'

# Test case 2: Goal on the left, not blocked
def test_goal_on_left_unblocked():
    state = {
        'goal_ahead': False,
        'goal_on_left': True,
        'goal_on_right': False,
        'front_blocked': False,
        'left_blocked': False,
        'right_blocked': False,
    }
    assert decide_next_move(state) == 'LEFT'

# Test case 3: Goal on the right, not blocked
def test_goal_on_right_unblocked():
    state = {
        'goal_ahead': False,
        'goal_on_left': False,
        'goal_on_right': True,
        'front_blocked': False,
        'left_blocked': False,
        'right_blocked': False,
    }
    assert decide_next_move(state) == 'RIGHT'

# Test case 4: All directions blocked
def test_all_blocked():
    state = {
        'goal_ahead': False,
        'goal_on_left': False,
        'goal_on_right': False,
        'front_blocked': True,
        'left_blocked': True,
        'right_blocked': True,
    }
    assert decide_next_move(state) == 'STOP'

# Test case 5: All possible combinations (comprehensive coverage)
def test_all_combinations():
    for state_tuple in itertools.product([True, False], repeat=6):
        state = {
            'goal_ahead': state_tuple[0],
            'goal_on_left': state_tuple[1],
            'goal_on_right': state_tuple[2],
            'front_blocked': state_tuple[3],
            'left_blocked': state_tuple[4],
            'right_blocked': state_tuple[5],
        }
        expected = None
        if state['goal_ahead'] and not state['front_blocked']:
            expected = 'FORWARD'
        elif state['goal_on_left'] and not state['left_blocked']:
            expected = 'LEFT'
        elif state['goal_on_right'] and not state['right_blocked']:
            expected = 'RIGHT'
        else:
            if not state['front_blocked']:
                expected = 'FORWARD'
            elif not state['left_blocked']:
                expected = 'LEFT'
            elif not state['right_blocked']:
                expected = 'RIGHT'
            else:
                expected = 'STOP'
        assert decide_next_move(state) == expected
