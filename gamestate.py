import math
import animations

# Input Names
INPUT_UP = 0
INPUT_DOWN = 1
INPUT_RIGHT = 2
INPUT_LEFT = 3

player_input_mouse_position = [0, 0]
player_input_mouse_sensitivity = 0.15
player_input_queue = []
player_input_state = []
player_input_direction = []

screen_dimensions = []
screen_center = []

player_animation_idle = []
player_animation_run = []
player_animation_walk = []
player_animation_state = []
player_animation_flipped = []

player_size_idle = [4, 6, 15, 26]
player_size_run = [-10, 1, 20, 32]
player_size_walk = [1, 1, 24, 32]
PLAYER_SPEED = 3

player_camera_offset = [0, 0]
player_position = []
player_velocity = []

map_colliders = []
map_triangle_colliders = []


def screen_dimensions_set(screen_size):
    global screen_dimensions, screen_center

    screen_dimensions = screen_size
    screen_center = (screen_dimensions[0] // 2, screen_dimensions[1] // 2)


def map_load():
    global map_colliders

    # Walls
    map_colliders.append((0, 0, 1280, 64))
    map_colliders.append((0, 64, 64, 592))
    map_colliders.append((0, 656, 1280, 64))
    map_colliders.append((1216, 64, 64, 592))

    # Bookshelves
    map_colliders.append((128, 128, 400, 70))
    map_colliders.append((128, 262, 400, 70))

    # Triangle
    map_triangle_colliders.append((780, 1126, 321, 121))


def create_player():
    player_input_queue.append([])
    player_input_state.append([False, False, False, False])
    player_input_direction.append([0, 0])

    player_animation_idle.append(animations.instance_create(animations.ANIMATION_PLAYER_IDLE))
    player_animation_run.append(animations.instance_create(animations.ANIMATION_PLAYER_RUN))
    player_animation_state.append(0)
    player_animation_flipped.append(False)

    player_position.append([128, 400])
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


def player_input_mouse_position_set(new_mouse_x, new_mouse_y):
    global player_input_mouse_position

    player_input_mouse_position = [new_mouse_x, new_mouse_y]


def update(delta):
    for player_index in range(0, player_count_get()):
        # Handle input queue
        while len(player_input_queue[player_index]) != 0:
            input_event = player_input_queue[player_index].pop(0)
            player_input_handle(player_index, input_event)

        # Update player position
        player_position[player_index][0] += player_velocity[player_index][0] * delta
        player_position[player_index][1] += player_velocity[player_index][1] * delta

        # Check player map collisions
        stop_colliders = []
        for collider in map_colliders:
            stop_colliders.append(collider)
        for other_player_index in range(0, player_count_get()):
            if other_player_index != player_index:
                stop_colliders.append(player_rect_get(other_player_index))

        player_rect = player_rect_get(player_index)
        for collider in stop_colliders:
            if collision_check_rectangles(player_rect, collider):
                player_x_step = player_velocity[player_index][0] * delta
                player_y_step = player_velocity[player_index][1] * delta

                player_rect[1] -= player_y_step
                collision_caused_by_x = collision_check_rectangles(player_rect, collider)
                player_rect[1] += player_y_step

                player_rect[0] -= player_x_step
                collision_caused_by_y = collision_check_rectangles(player_rect, collider)
                player_rect[0] += player_x_step

                if collision_caused_by_x:
                    player_position[player_index][0] -= player_x_step
                    player_rect[0] -= player_x_step
                if collision_caused_by_y:
                    player_position[player_index][1] -= player_y_step
                    player_rect[1] -= player_x_step

        # Update player animations
        if player_animation_flipped[player_index] and player_velocity[player_index][0] > 0:
            player_animation_flipped[player_index] = False
        elif not player_animation_flipped[player_index] and player_velocity[player_index][0] < 0:
            player_animation_flipped[player_index] = True
        if player_animation_state[player_index] == 0:
            if player_velocity[player_index][0] == 0 and player_velocity[player_index][1] == 0:
                animations.instance_update(player_animation_idle[player_index], delta)
            else:
                animations.instance_reset(player_animation_idle[player_index])
                player_animation_state[player_index] = 1
                animations.instance_update(player_animation_run[player_index], delta)
        elif player_animation_state[player_index] == 1:
            if player_velocity[player_index][0] != 0 or player_velocity[player_index][1] != 0:
                animations.instance_update(player_animation_run[player_index], delta)
            else:
                animations.instance_reset(player_animation_run[player_index])
                player_animation_state[player_index] = 0
                animations.instance_update(player_animation_idle[player_index], delta)


def player_camera_position_set(player_index):
    global player_position, player_input_mouse_position, player_input_mouse_sensitivity, player_camera_offset, screen_center

    mouse_offset = [(player_input_mouse_position[0] - screen_center[0]) * player_input_mouse_sensitivity, (player_input_mouse_position[1] - screen_center[1]) * player_input_mouse_sensitivity]
    player_camera_offset = [player_position[player_index][0] - screen_center[0] + mouse_offset[0], player_position[player_index][1] - screen_center[1] + mouse_offset[1]]


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
    return [int(player_position[player_index][0]), int(player_position[player_index][1]), 15, 26]


def player_render_coordinates_get(player_index):
    player_rect = player_rect_get(player_index)
    player_rect[0] -= 4
    player_rect[1] -= 6

    if player_animation_state[player_index] == 1 and not player_animation_flipped[player_index]:
        player_rect[0] -= 8
    elif player_animation_state[player_index] == 0 and player_animation_flipped[player_index]:
        player_rect[0] += 3

    player_rect[0] -= player_camera_offset[0]
    player_rect[1] -= player_camera_offset[1]

    return [int(player_rect[0]), int(player_rect[1])]


def player_animation_frame_get(player_index):
    global player_animation_state, player_animation_flipped, player_animation_idle, player_animation_run, player_animation_walk

    if player_animation_state[player_index] == 0:
        return animations.instance_frame_get(player_animation_idle[player_index], player_animation_flipped[player_index])
    elif player_animation_state[player_index] == 1:
        return animations.instance_frame_get(player_animation_run[player_index], player_animation_flipped[player_index])

    return []


def scale_vector(old_vector, new_magnitude):
    old_magnitude = math.sqrt((old_vector[0] ** 2) + (old_vector[1] ** 2))
    if old_magnitude == 0:
        return [0, 0]
    scale = new_magnitude / old_magnitude
    return [old_vector[0] * scale, old_vector[1] * scale]


def collision_check_rectangles(rect_first, rect_second):
    return not (rect_first[0] + rect_first[2] <= rect_second[0] or rect_second[0] + rect_second[2] <= rect_first[0] or rect_first[1] + rect_first[3] <= rect_second[1] or rect_second[1] + rect_second[3] <= rect_first[1])
