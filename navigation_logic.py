def navigate(current_position, goal, environment):
    if current_position == goal:
        return "STOP"
    forward_pos = (current_position[0], current_position[1] + 1)
    if not environment[forward_pos[0]][forward_pos[1]]:
        return "FORWARD"
    left_pos = (current_position[0] - 1, current_position[1])
    if not environment[left_pos[0]][left_pos[1]]:
        return "LEFT"
    right_pos = (current_position[0] + 1, current_position[1])
    if not environment[right_pos[0]][right_pos[1]]:
        return "RIGHT"
    return "STOP"