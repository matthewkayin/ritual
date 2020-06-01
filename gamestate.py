import math
import animations
import spells

# Input Names
INPUT_UP = 0
INPUT_DOWN = 1
INPUT_RIGHT = 2
INPUT_LEFT = 3
INPUT_SPELLCAST = 4

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

player_pending_spells = []
player_equipped_spells = []
player_selected_spell = []
player_spell_cooldown_timers = []
spell_instances = []

map_colliders = []


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


def create_player():
    player_input_queue.append([])
    player_input_state.append([False, False, False, False, False])
    player_input_direction.append([0, 0])

    player_animation_idle.append(animations.instance_create(animations.ANIMATION_PLAYER_IDLE))
    player_animation_run.append(animations.instance_create(animations.ANIMATION_PLAYER_RUN))
    player_animation_state.append(0)
    player_animation_flipped.append(False)

    player_position.append([128, 400])
    player_velocity.append([0, 0])

    player_pending_spells.append(None)
    player_equipped_spells.append([0, -1, -1, -1])
    player_selected_spell.append(0)
    player_spell_cooldown_timers.append([-1, -1, -1, -1])


def player_input_queue_append(player_index, input_event):
    player_input_queue[player_index].append(input_event)


def player_input_handle(player_index, input_event):
    event_is_keydown = input_event[0]
    input_event_name = input_event[1]
    mouse_pos = None
    if len(input_event) > 2:
        mouse_pos = input_event[2]
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
        elif input_event_name == INPUT_SPELLCAST:
            spell_name = player_equipped_spells[player_index][player_selected_spell[player_index]]
            if player_spell_cooldown_timers[player_index][player_selected_spell[player_index]] == -1:
                new_spell_instance = spells.instance_create(spell_name)
                player_pending_spells[player_index] = new_spell_instance
                if spells.instance_can_instant_cast(new_spell_instance):
                    player_spell_cast(player_index, mouse_pos)
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
        elif input_event_name == INPUT_SPELLCAST:
            if player_pending_spells[player_index] is not None:
                if spells.instance_cast_ready(player_pending_spells[player_index]):
                    player_spell_cast(player_index, mouse_pos)
                else:
                    player_pending_spells[player_index] = None
        player_input_state[player_index][input_event_name] = False

    if update_player_velocity:
        player_velocity[player_index] = scale_vector(player_input_direction[player_index], PLAYER_SPEED)


def player_spell_cast(player_index, mouse_pos):
    spell_instance = player_pending_spells[player_index]
    player_rect = player_rect_get(player_index)
    player_center = (player_rect[0] + (player_rect[2] // 2), player_rect[1] + (player_rect[3] // 2))

    spell_distance_from_player = player_rect[3]
    aim_vector = [mouse_pos[0] - player_center[0], mouse_pos[1] - player_center[1]]

    spell_origin = scale_vector(aim_vector, spell_distance_from_player)
    spell_origin[0] += player_center[0]
    spell_origin[1] += player_center[1]
    instance_aim_vector = scale_vector(aim_vector, spells.instance_speed_on_cast_get(spell_instance))

    spells.instance_cast(spell_instance, spell_origin, instance_aim_vector)
    spell_rect = spells.instance_rect_get(spell_instance)
    for collider in map_colliders:
        if collision_check_rectangles(spell_rect, collider):
            player_pending_spells[player_index] = None
            return
    spell_instances.append(spell_instance)
    player_pending_spells[player_index] = None
    player_spell_cooldown_timers[player_index][player_selected_spell[player_index]] = 0


def player_input_mouse_position_set(new_mouse_x, new_mouse_y):
    global player_input_mouse_position

    player_input_mouse_position = [new_mouse_x, new_mouse_y]


def player_input_offset_mouse_position_get(mouse_x, mouse_y):
    return [int(mouse_x + player_camera_offset[0]), int(mouse_y + player_camera_offset[1])]


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

        # Update player pending spell
        if player_pending_spells[player_index] is not None:
            spells.instance_update(player_pending_spells[player_index], delta, False)

        # Update spell cooldown timers
        for i in range(0, 4):
            if player_spell_cooldown_timers[player_index][i] != -1:
                player_spell_cooldown_timers[player_index][i] += delta
                spell_name = player_equipped_spells[player_index][player_selected_spell[player_index]]
                if player_spell_cooldown_timers[player_index][i] >= spells.spell_cooldown_time[spell_name]:
                    player_spell_cooldown_timers[player_index][i] = -1

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

    # Update spells
    spell_indexes_deleted_this_frame = []
    for spell_index in range(0, len(spell_instances)):
        spells.instance_update(spell_instances[spell_index], delta)
        if spell_instances[spell_index][0] == spells.SPELL_DELETE_ME:
            spell_indexes_deleted_this_frame.append(spell_index)
        else:
            spell_rect = spells.instance_rect_get(spell_instances[spell_index])
            for collider in map_colliders:
                if collision_check_rectangles(spell_rect, collider):
                    old_spell_velocity = spells.instance_velocity_get(spell_instances[spell_index])
                    collision_still_happening = True
                    while collision_still_happening:
                        spell_rect[0] -= old_spell_velocity[0] * delta
                        spell_rect[1] -= old_spell_velocity[1] * delta
                        collision_still_happening = collision_check_rectangles(spell_rect, collider)
                    collision_direction = collision_get_from_which_sides(spell_rect, collider)
                    if collision_direction[0] != 0:
                        old_spell_velocity[0] *= -1
                    elif collision_direction[1] != 0:
                        old_spell_velocity[1] *= -1
                    spells.instance_velocity_set(spell_instances[spell_index], old_spell_velocity)
                    break
    for index in spell_indexes_deleted_this_frame:
        del spell_instances[index]


def player_camera_position_set(player_index):
    global player_position, player_input_mouse_position, player_input_mouse_sensitivity, player_camera_offset, screen_center

    mouse_offset = [(player_input_mouse_position[0] - screen_center[0]) * player_input_mouse_sensitivity, (player_input_mouse_position[1] - screen_center[1]) * player_input_mouse_sensitivity]
    player_camera_offset = [player_position[player_index][0] - screen_center[0] + mouse_offset[0], player_position[player_index][1] - screen_center[1] + mouse_offset[1]]


def state_data_get():
    state_data = []

    player_data = []
    for player_index in range(0, player_count_get()):
        player_data_entry = []

        player_data_entry.append(int(player_position[player_index][0]))
        player_data_entry.append(int(player_position[player_index][1]))
        player_data_entry.append(round(player_velocity[player_index][0], 2))
        player_data_entry.append(round(player_velocity[player_index][1], 2))

        player_data.append(player_data_entry)
    state_data.append(player_data)

    spell_data = []
    for player_index in range(0, player_count_get()):
        if player_pending_spells[player_index] is not None:
            spell_data_entry = []

            spell_data_entry.append(int(player_index))
            spell_data_entry.append(int(player_pending_spells[player_index][0]))
            spell_data_entry.append(int(player_pending_spells[player_index][1]))

            spell_data.append(spell_data_entry)
    for spell_index in range(0, spell_count_get()):
        spell_data_entry = []

        spell_data_entry.append(int(spell_instances[spell_index][0]))
        spell_data_entry.append(int(spell_instances[spell_index][1]))
        spell_data_entry.append(int(spell_instances[spell_index][2]))
        spell_data_entry.append(int(spell_instances[spell_index][3]))
        spell_data_entry.append(round(spell_instances[spell_index][4], 2))
        spell_data_entry.append(round(spell_instances[spell_index][5], 2))

        spell_data.append(spell_data_entry)
    state_data.append(spell_data)

    return state_data


def state_data_set(state_data):
    global spell_instances

    player_data = state_data[0]
    for player_index in range(0, len(state_data)):
        if player_index == player_count_get():
            create_player()
        player_position[player_index][0] = int(player_data[player_index][0])
        player_position[player_index][1] = int(player_data[player_index][1])
        player_velocity[player_index][0] = float(player_data[player_index][2])
        player_velocity[player_index][1] = float(player_data[player_index][3])

    spell_data = state_data[1]
    spell_instances = []
    for player_index in range(0, len(state_data)):
        player_pending_spells[player_index] = None
    # This if statement happens when there is no spell data, we set the array to empty to skip this whole section
    if spell_data[0] == [""]:
        spell_data = []
    instance_index = 0
    for spell_index in range(0, len(spell_data)):
        if len(spell_data[spell_index]) == 3:
            player_index = int(spell_data[spell_index][0])
            player_pending_spells[player_index] = spells.instance_create(int(spell_data[spell_index][1]))
            spells.instance_timer_set(player_pending_spells[player_index], int(spell_data[spell_index][2]))
        else:
            spell_instances.append(spells.instance_create(int(spell_data[spell_index][0])))
            spell_values = []
            spell_values.append(int(spell_data[spell_index][1]))
            spell_values.append(int(spell_data[spell_index][2]))
            spell_values.append(int(spell_data[spell_index][3]))
            spell_values.append(float(spell_data[spell_index][4]))
            spell_values.append(float(spell_data[spell_index][5]))
            spells.instance_values_set(spell_instances[instance_index], spell_values)
            instance_index += 1


def spell_instances_remove(indexes):
    for index in indexes:
        del spell_instances[index]


def player_count_get():
    return len(player_position)


def spell_count_get():
    return len(spell_instances)


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


def player_spell_charge_percentage_get(player_index):
    if player_pending_spells[player_index] is None:
        return 0
    else:
        return spells.instance_timer_percentage_get(player_pending_spells[player_index])


def player_spell_render_coordinates_get(spell_index):
    spell_rect = spells.instance_rect_get(spell_instances[spell_index])

    spell_rect[0] -= player_camera_offset[0]
    spell_rect[1] -= player_camera_offset[1]

    return spell_rect


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


def collision_get_from_which_sides(rect_first, rect_second):
    left = rect_first[0] + rect_first[2] > rect_second[0]
    right = rect_second[0] + rect_second[2] > rect_first[0]
    top = rect_first[1] + rect_first[3] > rect_second[1]
    bottom = rect_second[1] + rect_second[3] > rect_first[1]

    x_direction = 0
    if left and not right:
        x_direction = -1
    elif right and not left:
        x_direction = 1
    y_direction = 0
    if top and not bottom:
        y_direction = -1
    elif bottom and not top:
        y_direction = 1

    return [x_direction, y_direction]
