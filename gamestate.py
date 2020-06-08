import math
import animations
import spells

# Input Names
INPUT_UP = 0
INPUT_DOWN = 1
INPUT_RIGHT = 2
INPUT_LEFT = 3
INPUT_SPELLCAST = 4
INPUT_TELEPORT = 5

player_input_mouse_position = [0, 0]
player_input_mouse_sensitivity = 0.15
player_input_queue = []
player_input_state = []
player_input_direction = []

screen_dimensions = []
screen_center = []

player_animations = []
player_animation_state = []
player_animation_flipped = []
player_animation_windup = []

player_size_idle = [4, 6, 15, 26]
player_size_run = [-10, 1, 20, 32]
player_size_walk = [1, 1, 24, 32]
PLAYER_SPEED = 3
PLAYER_WALK_SPEED = 1
PLAYER_CAMERA_SPEED = 8
PLAYER_MAX_TELEPORT_DIST = 200
PLAYER_HURT_DURATION = 7
PLAYER_HURT_SPEED = 15

player_camera_offset = [0, 0]
player_position = []
player_velocity = []
player_teleport_dest = []

player_health = []
player_display_health = []
player_hurt_timer = []

player_pending_spells = []
player_pending_spell_aim = []
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
    player_input_state.append([False, False, False, False, False, False])
    player_input_direction.append([0, 0])

    new_animations = []
    new_animations.append(animations.instance_create(animations.ANIMATION_PLAYER_IDLE))
    new_animations.append(animations.instance_create(animations.ANIMATION_PLAYER_RUN))
    new_animations.append(animations.instance_create(animations.ANIMATION_PLAYER_WALK))
    new_animations.append(animations.instance_create(animations.ANIMATION_PLAYER_CAST_MISSILE))
    new_animations.append(animations.instance_create(animations.ANIMATION_PLAYER_TELEPORT_ENTER))

    player_animations.append(new_animations)
    player_animation_state.append(0)
    player_animation_flipped.append(False)
    player_animation_windup.append(False)

    player_position.append([128, 400])
    player_velocity.append([0, 0])
    player_teleport_dest.append(None)

    player_health.append(100)
    player_display_health.append(100)
    player_hurt_timer.append(0)

    player_pending_spells.append(None)
    player_pending_spell_aim.append([0, 0])
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
                    player_animation_windup[player_index] = True
                    player_pending_spell_aim[player_index] = mouse_pos
                    update_player_velocity = True
                else:
                    update_player_velocity = True
        elif input_event_name == INPUT_TELEPORT:
            if player_pending_spells[player_index] is None and not player_animation_windup[player_index] and player_teleport_dest[player_index] is None:
                teleport_target = [mouse_pos[0], mouse_pos[1]]
                player_rect = player_rect_get(player_index)
                player_center = [player_rect[0] + (player_rect[2] // 2), player_rect[1] + (player_rect[3] // 2)]
                if point_distance(player_center, teleport_target) > PLAYER_MAX_TELEPORT_DIST:
                    dist_vector = [teleport_target[0] - player_center[0], teleport_target[1] - player_center[1]]
                    new_dist_vector = scale_vector(dist_vector, PLAYER_MAX_TELEPORT_DIST)
                    teleport_target = [player_center[0] + new_dist_vector[0], player_center[1] + new_dist_vector[1]]
                player_dest_rect = [teleport_target[0] - (player_rect[2] // 2), teleport_target[1] - (player_rect[3] // 2), player_rect[2], player_rect[3]]
                for collider in map_colliders:
                    if collision_check_rectangles(player_dest_rect, collider):
                        backstep = [player_center[0] - teleport_target[0], player_center[1] - teleport_target[1]]
                        backstep_magnitude = math.sqrt((backstep[0] ** 2) + (backstep[1] ** 2))
                        unit_backstep = [backstep[0] / backstep_magnitude, backstep[1] / backstep_magnitude]
                        while collision_check_rectangles(player_dest_rect, collider):
                            teleport_target[0] += unit_backstep[0]
                            teleport_target[1] += unit_backstep[1]
                            player_dest_rect = [teleport_target[0] - (player_rect[2] // 2), teleport_target[1] - (player_rect[3] // 2), player_rect[2], player_rect[3]]
                player_teleport_dest[player_index] = [teleport_target[0] - (player_rect[2] // 2), teleport_target[1] - (player_rect[3] // 2)]
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
        elif input_event_name == INPUT_SPELLCAST:
            if player_pending_spells[player_index] is not None:
                if spells.instance_cast_ready(player_pending_spells[player_index]):
                    player_animation_windup[player_index] = True
                    player_pending_spell_aim[player_index] = mouse_pos
                else:
                    player_pending_spells[player_index] = None
                update_player_velocity = True
        player_input_state[player_index][input_event_name] = False

    if update_player_velocity:
        player_velocity_update(player_index)


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


def player_velocity_update(player_index):
    if player_hurt_timer[player_index] != 0:
        return
    if player_animation_windup[player_index] or player_teleport_dest[player_index] is not None:
        player_velocity[player_index][0] = 0
        player_velocity[player_index][1] = 0
    else:
        speed_magnitude = PLAYER_SPEED
        if player_pending_spells[player_index] is not None:
            speed_magnitude = PLAYER_WALK_SPEED
        player_velocity[player_index] = scale_vector(player_input_direction[player_index], speed_magnitude)


def player_input_mouse_position_set(new_mouse_x, new_mouse_y):
    global player_input_mouse_position

    player_input_mouse_position = [new_mouse_x, new_mouse_y]


def player_input_offset_mouse_position_get(mouse_x, mouse_y):
    return [int(mouse_x + player_camera_offset[0]), int(mouse_y + player_camera_offset[1])]


def player_input_queue_pump_events(player_index=-1):
    if player_index == -1:
        for player_index in range(0, player_count_get()):
            while len(player_input_queue[player_index]) != 0:
                input_event = player_input_queue[player_index].pop(0)
                player_input_handle(player_index, input_event)
    elif player_index in range(0, player_count_get()):
        while len(player_input_queue[player_index]) != 0:
            input_event = player_input_queue[player_index].pop(0)
            player_input_handle(player_index, input_event)


def update(delta):
    for player_index in range(0, player_count_get()):
        player_input_queue_pump_events()

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

                if player_hurt_timer[player_index] != 0:
                    player_hurt_timer[player_index] = 0
                    player_velocity[player_index] = [0, 0]

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

        if player_hurt_timer[player_index] != 0:
            player_hurt_timer[player_index] -= delta
            if player_hurt_timer[player_index] <= 0:
                player_hurt_timer[player_index] = 0
                player_velocity[player_index] = [0, 0]

        desired_animation_state = 0
        if player_hurt_timer[player_index] > 0:
            desired_animation_state = -1
        elif player_teleport_dest[player_index] is not None:
            desired_animation_state = 4
        else:
            if player_velocity[player_index][0] != 0 or player_velocity[player_index][1] != 0:
                if player_pending_spells[player_index] is None:
                    desired_animation_state = 1
                else:
                    desired_animation_state = 2
            else:
                if player_animation_state[player_index] == 3:
                    if animations.instance_finished(player_animations[player_index][player_animation_state[player_index]]):
                        desired_animation_state = 0
                    else:
                        desired_animation_state = 3
                elif player_animation_windup[player_index] or player_animation_state[player_index] == 3:
                    desired_animation_state = 3

        if desired_animation_state != -1:
            current_animation_state = player_animation_state[player_index]
            if current_animation_state != desired_animation_state:
                animations.instance_reset(player_animations[player_index][current_animation_state])
                player_animation_state[player_index] = desired_animation_state
            animations.instance_update(player_animations[player_index][player_animation_state[player_index]], delta)

        if player_animation_windup[player_index]:
            if animations.instance_cast_animation_ready(player_animations[player_index][player_animation_state[player_index]]):
                player_spell_cast(player_index, player_pending_spell_aim[player_index])
                player_animation_windup[player_index] = False
                player_velocity_update(player_index)

        if player_teleport_dest[player_index] is not None:
            if animations.instance_finished(player_animations[player_index][player_animation_state[player_index]]):
                player_position[player_index][0] = player_teleport_dest[player_index][0]
                player_position[player_index][1] = player_teleport_dest[player_index][1]
                player_teleport_dest[player_index] = None
                player_velocity_update(player_index)

        # Player display health sliding
        if player_display_health[player_index] != player_health[player_index]:
            health_decreasing = player_display_health[player_index] > player_health[player_index]
            player_display_health[player_index] += 3 * delta * (-1 * health_decreasing)

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
            spell_rect = spells.instance_rect_get(spell_instances[spell_index])
            for player_index in range(0, player_count_get()):
                if player_teleport_dest[player_index] is not None:
                    continue
                player_rect = player_rect_get(player_index)
                if collision_check_rectangles(spell_rect, player_rect):
                    player_health[player_index] -= spells.instance_damage_get(spell_instances[spell_index])
                    player_hurt_timer[player_index] = PLAYER_HURT_DURATION
                    player_velocity[player_index] = scale_vector(spells.instance_velocity_get(spell_instances[spell_index]), PLAYER_HURT_SPEED)
                    player_pending_spells[player_index] = None
                    animations.instance_reset(player_animations[player_index][player_animation_state[player_index]])
                    player_animation_state[player_index] = 0
                    spell_instances[spell_index][0] = spells.SPELL_DELETE_ME

    for index in spell_indexes_deleted_this_frame:
        del spell_instances[index]


def player_camera_position_set(player_index):
    global player_position, player_input_mouse_position, player_input_mouse_sensitivity, player_camera_offset, screen_center

    mouse_offset = [(player_input_mouse_position[0] - screen_center[0]) * player_input_mouse_sensitivity, (player_input_mouse_position[1] - screen_center[1]) * player_input_mouse_sensitivity]
    desired_player_camera_offset = None
    if player_teleport_dest[player_index] is not None:
        desired_player_camera_offset = [player_teleport_dest[player_index][0] - screen_center[0] + mouse_offset[0], player_teleport_dest[player_index][1] - screen_center[1] + mouse_offset[1]]
    else:
        desired_player_camera_offset = [player_position[player_index][0] - screen_center[0] + mouse_offset[0], player_position[player_index][1] - screen_center[1] + mouse_offset[1]]
    camera_dist = point_distance(desired_player_camera_offset, player_camera_offset)
    if camera_dist <= PLAYER_CAMERA_SPEED:
        player_camera_offset = desired_player_camera_offset
    else:
        camera_offset_difference = [desired_player_camera_offset[0] - player_camera_offset[0], desired_player_camera_offset[1] - player_camera_offset[1]]
        camera_offset_step = scale_vector(camera_offset_difference, PLAYER_CAMERA_SPEED)
        player_camera_offset[0] += camera_offset_step[0]
        player_camera_offset[1] += camera_offset_step[1]


def state_data_get():
    state_data = []

    player_data = []
    for player_index in range(0, player_count_get()):
        player_data_entry = []

        player_data_entry.append(int(player_position[player_index][0]))
        player_data_entry.append(int(player_position[player_index][1]))
        player_data_entry.append(round(player_velocity[player_index][0], 2))
        player_data_entry.append(round(player_velocity[player_index][1], 2))
        player_data_entry.append(int(player_health[player_index]))
        player_data_entry.append(int(player_hurt_timer[player_index]))
        if player_teleport_dest[player_index] is not None:
            player_data_entry.append(int(player_teleport_dest[player_index][0]))
            player_data_entry.append(int(player_teleport_dest[player_index][1]))

        player_data.append(player_data_entry)
    state_data.append(player_data)

    spell_data = []
    for player_index in range(0, player_count_get()):
        if player_pending_spells[player_index] is not None:
            spell_data_entry = []

            spell_data_entry.append(int(player_index))
            spell_data_entry.append(int(player_pending_spells[player_index][0]))
            spell_data_entry.append(int(player_pending_spells[player_index][1]))
            spell_data_entry.append(int(player_animation_windup[player_index]))

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
    global spell_instances, spell_animation_instances

    player_data = state_data[0]
    for player_index in range(0, len(player_data)):
        if player_index == player_count_get():
            create_player()
        player_position[player_index][0] = int(player_data[player_index][0])
        player_position[player_index][1] = int(player_data[player_index][1])
        player_velocity[player_index][0] = float(player_data[player_index][2])
        player_velocity[player_index][1] = float(player_data[player_index][3])
        player_health[player_index] = int(player_data[player_index][4])
        player_hurt_timer[player_index] = int(player_data[player_index][5])
        if len(player_data[player_index]) == 8:
            player_teleport_dest[player_index] = [int(player_data[player_index][6]), int(player_data[player_index][7])]
        else:
            player_teleport_dest[player_index] = None

    spell_data = state_data[1]
    spell_instances = []
    spell_animation_instances = []
    for player_index in range(0, len(player_data)):
        player_pending_spells[player_index] = None
    # This if statement happens when there is no spell data, we set the array to empty to skip this whole section
    if spell_data[0] == [""]:
        spell_data = []
    instance_index = 0
    for spell_index in range(0, len(spell_data)):
        if len(spell_data[spell_index]) == 4:
            player_index = int(spell_data[spell_index][0])
            player_pending_spells[player_index] = spells.instance_create(int(spell_data[spell_index][1]))
            spells.instance_timer_set(player_pending_spells[player_index], int(spell_data[spell_index][2]))
            player_animation_windup[player_index] = bool(int(spell_data[spell_index][3]))
        else:
            spell_instances.append(spells.instance_create(int(spell_data[spell_index][0])))
            spell_values = []
            spell_values.append(int(spell_data[spell_index][1]))
            spell_values.append(int(spell_data[spell_index][2]))
            spell_values.append(int(spell_data[spell_index][3]))
            spell_values.append(float(spell_data[spell_index][4]))
            spell_values.append(float(spell_data[spell_index][5]))
            spells.instance_values_set(spell_instances[instance_index], spell_values)
            spell_animation_instances.append(animations.instance_create_with_timer(spells.spell_animation_name[spell_instances[instance_index][0]], spell_instances[instance_index][1]))
            instance_index += 1

    for player_index in range(0, len(state_data)):
        if player_animation_windup[player_index] and player_pending_spells[player_index] is None:
            player_animation_windup[player_index] = False


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

    animation_state = player_animation_state[player_index]
    if player_animation_flipped[player_index]:
        if animation_state == 0:
            player_rect[0] += 3
        elif animation_state == 3:
            player_rect[0] -= 3
    else:
        if animation_state == 1:
            player_rect[0] -= 8
        elif animation_state == 2:
            player_rect[0] -= 4
        elif animation_state == 3:
            player_rect[0] -= 5
        elif animation_state == 4:
            player_rect[0] -= 2

    player_rect[0] -= player_camera_offset[0]
    player_rect[1] -= player_camera_offset[1]

    return [int(player_rect[0]), int(player_rect[1])]


def player_teleport_render_coordinates_get(player_index):
    if player_teleport_dest[player_index] is None:
        return None
    else:
        return [player_teleport_dest[player_index][0] - 10 - player_camera_offset[0], player_teleport_dest[player_index][1] - 7 - player_camera_offset[1]]


def player_spell_charge_percentage_get(player_index):
    if player_pending_spells[player_index] is None:
        return 0
    else:
        return spells.instance_timer_percentage_get(player_pending_spells[player_index])


def player_health_percentage_get(player_index):
    return max(0, player_display_health[player_index]) / 100


def spell_render_coords_get(spell_index):
    spell_rect = spells.instance_rect_get(spell_instances[spell_index])
    spell_velocity = spells.instance_velocity_get(spell_instances[spell_index])
    angle = math.degrees(math.atan2(spell_velocity[1], spell_velocity[0])) * -1

    spell_rect = spells.instance_rect_get(spell_instances[spell_index])
    spell_rect[0] -= player_camera_offset[0]
    spell_rect[1] -= player_camera_offset[1]

    return spell_rect, angle


def spell_render_coordinates_get(spell_index):
    spell_rect = spells.instance_rect_get(spell_instances[spell_index])

    spell_rect[0] -= player_camera_offset[0]
    spell_rect[1] -= player_camera_offset[1]

    return spell_rect


def player_animation_frame_get(player_index):
    if player_hurt_timer[player_index] != 0:
        return animations.get_flipped_image(animations.image_hurt_wizard, not player_animation_flipped[player_index])
    return animations.instance_get_frame_image(player_animations[player_index][player_animation_state[player_index]], player_animation_flipped[player_index])


def player_animation_teleport_frame_get(player_index):
    if player_animation_state[player_index] != 4:
        return None
    else:
        animation_instance = player_animations[player_index][player_animation_state[player_index]]
        exit_instance = []
        for i in range(0, len(animation_instance)):
            exit_instance.append(animation_instance[i])
        exit_instance[0] += 1
        return animations.instance_get_frame_image(exit_instance, player_animation_flipped[player_index])


def player_animation_frame_book_get(player_index):
    if player_animation_state[player_index] == 3 or player_animation_state[player_index] == 4:
        return None
    animation_instance = player_animations[player_index][player_animation_state[player_index]]
    book_instance = []
    for i in range(0, len(animation_instance)):
        book_instance.append(animation_instance[i])
    book_instance[0] += 4
    if player_animation_state[player_index] == 0 and player_pending_spells[player_index] is not None:
        book_instance[0] += 3
    return animations.instance_get_frame_image(book_instance, player_animation_flipped[player_index])


def scale_vector(old_vector, new_magnitude):
    old_magnitude = math.sqrt((old_vector[0] ** 2) + (old_vector[1] ** 2))
    if old_magnitude == 0:
        return [0, 0]
    scale = new_magnitude / old_magnitude
    return [old_vector[0] * scale, old_vector[1] * scale]


def vector_angle_get(vector):
    if vector[0] == 0 and vector[1] == 0:
        return 0
    elif vector[0] == 0:
        if vector[1] > 0:
            return 90
        else:
            return 270
    elif vector[1] == 0:
        if vector[0] > 0:
            return 0
        else:
            return 180
    else:
        angle = math.degrees(math.atan(vector[1] / vector[0]))
        if vector[1] < 0:
            angle += 180
        return angle


def point_distance(first_point, second_point):
    x_dist = second_point[0] - first_point[0]
    y_dist = second_point[1] - first_point[1]
    return math.sqrt((x_dist ** 2) + (y_dist ** 2))


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
