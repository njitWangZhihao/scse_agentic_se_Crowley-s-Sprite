def decide_next_move(state):
    if state['goal_ahead'] and not state['front_blocked']:
        return "FORWARD"
    elif state['goal_on_left'] and not state['left_blocked']:
        return "LEFT"
    elif state['goal_on_right'] and not state['right_blocked']:
        return "RIGHT"
    else:
        return "STOP"