import math

# Input Names
INPUT_UP = 0
INPUT_DOWN = 1
INPUT_RIGHT = 2
INPUT_LEFT = 3

player_input_queue = []
player_input_state = []
player_input_direction = []

PLAYER_WIDTH = 20
PLAYER_HEIGHT = 40
PLAYER_SPEED = 3

player_position = []
player_velocity = []


def create_player():
    player_input_queue.append([])
    player_input_state.append([False, False, False, False])
    player_input_direction.append([0, 0])

    player_position.append([100, 100])
    player_velocity.append([0, 0])


def player_input_queue_append(player_index, input_event):
    player_input_queue[player_index].append(input_event)


def player_input_handle(player_index, input_event):
    event_is_keydown = input_event[0]
    input_event_name = input_event[1]
    update_player_velocity = False
    if event_is_keydown:
        if input_event_name == INPUT_UP:
            player_input_direction[player_index][1] = -1
            update_player_velocity = True
        elif input_event_name == INPUT_DOWN:
            player_input_direction[player_index][1] = 1
            update_player_velocity = True
        elif input_event_name == INPUT_RIGHT:
            player_input_direction[player_index][0] = 1
            update_player_velocity = True
        elif input_event_name == INPUT_LEFT:
            player_input_direction[player_index][0] = -1
            update_player_velocity = True
        player_input_state[player_index][input_event_name] = True
    else:
        if input_event_name == INPUT_UP:
            if player_input_state[player_index][INPUT_DOWN]:
                player_input_direction[player_index][1] = 1
            else:
                player_input_direction[player_index][1] = 0
            update_player_velocity = True
        elif input_event_name == INPUT_DOWN:
            if player_input_state[player_index][INPUT_UP]:
                player_input_direction[player_index][1] = -1
            else:
                player_input_direction[player_index][1] = 0
            update_player_velocity = True
        elif input_event_name == INPUT_RIGHT:
            if player_input_state[player_index][INPUT_LEFT]:
                player_input_direction[player_index][0] = -1
            else:
                player_input_direction[player_index][0] = 0
            update_player_velocity = True
        elif input_event_name == INPUT_LEFT:
            if player_input_state[player_index][INPUT_RIGHT]:
                player_input_direction[player_index][0] = 1
            else:
                player_input_direction[player_index][0] = 0
            update_player_velocity = True
        player_input_state[player_index][input_event_name] = False

    if update_player_velocity:
        player_velocity[player_index] = scale_vector(player_input_direction[player_index], PLAYER_SPEED)


def update(delta):
    for player_index in range(0, player_count_get()):
        # Handle input queue
        while len(player_input_queue[player_index]) != 0:
            input_event = player_input_queue[player_index].pop(0)
            player_input_handle(player_index, input_event)

        # Update player position
        player_position[player_index][0] += player_velocity[player_index][0] * delta
        player_position[player_index][1] += player_velocity[player_index][1] * delta


def state_data_get():
    state_data = []
    for player_index in range(0, player_count_get()):
        state_data_entry = []

        state_data_entry.append(int(player_position[player_index][0]))
        state_data_entry.append(int(player_position[player_index][1]))
        state_data_entry.append(round(player_velocity[player_index][0], 2))
        state_data_entry.append(round(player_velocity[player_index][1], 2))

        state_data.append(state_data_entry)

    return state_data


def state_data_set(state_data):
    for player_index in range(0, len(state_data)):
        if player_index == player_count_get():
            create_player()
        player_position[player_index][0] = int(state_data[player_index][0])
        player_position[player_index][1] = int(state_data[player_index][1])
        player_velocity[player_index][0] = float(state_data[player_index][2])
        player_velocity[player_index][1] = float(state_data[player_index][3])


def player_count_get():
    return len(player_position)


def player_rect_get(player_index):
    return [int(player_position[player_index][0]), int(player_position[player_index][1]), PLAYER_WIDTH, PLAYER_HEIGHT]


def scale_vector(old_vector, new_magnitude):
    old_magnitude = math.sqrt((2 ** old_vector[0]) + (2 ** old_vector[1]))
    scale = new_magnitude / old_magnitude
    if scale == 0:
        return [0, 0]
    return [old_vector[0] * scale, old_vector[1] * scale]
