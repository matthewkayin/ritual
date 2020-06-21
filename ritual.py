import pygame
import sys
import os
import time
import network
import gamestate
import animations
import spells


# Handle cli flags
windowed = "--windowed" in sys.argv
show_fps = "--showfps" in sys.argv
if "--debug" in sys.argv:
    windowed = True
    show_fps = True

# Resolution variables
# Display stretches to Screen. Screen is set by user
DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 360
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 360

SCALE = SCREEN_WIDTH / DISPLAY_WIDTH

# Init pygame
os.environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init()
global screen
if windowed:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
else:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.FULLSCREEN)
display = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT))
clock = pygame.time.Clock()

# Timing variables
before_time = 0
ping_before_time = 0
ping = 0
client_reping_count = 0
UPDATE_TIME = 1000 / 60.0
TARGET_FPS = 60

# Colors
color_black = (0, 0, 0)
color_white = (255, 255, 255)
color_red = (255, 0, 0)
color_yellow = (255, 255, 0)
color_green = (0, 255, 0)

# Fonts
font_small = pygame.font.SysFont("Serif", 11)
font_big = pygame.font.SysFont("Serif", 36)

# Gamestates
GAMESTATE_EXIT = -1
GAMESTATE_MENU = 0
GAMESTATE_GAME = 1

connect_as_server = False
local_player_index = 0
player_usernames = []


def menu():
    global connect_as_server, local_player_index, player_usernames

    running = True
    return_gamestate = GAMESTATE_EXIT

    mouse_x, mouse_y = (0, 0)

    menu_state = 0
    menu_labels = []
    menu_buttons = []
    menu_textbox_type = []
    menu_shows_playerlist = []

    textbox_rect = [(DISPLAY_WIDTH // 2) - 125, 100, 250, 20]
    textbox_input = ""
    playerlist_rect = [(DISPLAY_WIDTH // 2) - 200 - 20, (DISPLAY_HEIGHT // 2) - 150, 200, 300]

    # Menu state 0
    menu_labels.append([("Ritual", -1, 75)])
    menu_buttons.append([("Join", -1, 125, 50, 20), ("Host", -1, 150, 50, 20)])
    menu_textbox_type.append(0)
    menu_shows_playerlist.append(False)

    # Menu state 1
    menu_labels.append([("Enter your username: ", textbox_rect[0] + 20, textbox_rect[1] - 20)])
    menu_buttons.append([])
    menu_textbox_type.append(1)
    menu_shows_playerlist.append(False)

    # Menu state 2
    menu_labels.append([("Enter host IP: ", textbox_rect[0] + 20, textbox_rect[1] - 20)])
    menu_buttons.append([])
    menu_textbox_type.append(2)
    menu_shows_playerlist.append(False)

    # Menu state 3
    menu_labels.append([("Connecting... ", -1, 75)])
    menu_buttons.append([("Cancel", -1, 125, 50, 20)])
    menu_textbox_type.append(0)
    menu_shows_playerlist.append(False)

    # Menu state 4
    menu_labels.append([])
    menu_buttons.append([])
    menu_textbox_type.append(0)
    menu_shows_playerlist.append(True)

    while running:
        # Input
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.MOUSEMOTION:
                mouse_x, mouse_y = event.pos[0] // SCALE, event.pos[1] // SCALE
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Do nothing if there are no buttons to press
                if len(menu_buttons[menu_state]) == 0:
                    continue
                button_pressed = -1
                for button_index in range(0, len(menu_buttons[menu_state])):
                    button_rect = list(menu_buttons[menu_state][button_index][1:])
                    if button_rect[0] == -1:
                        button_rect[0] = (DISPLAY_WIDTH // 2) - (button_rect[2] // 2)
                    if button_rect[1] == -1:
                        button_rect[1] = (DISPLAY_HEIGHT // 2) - (button_rect[3] // 2)
                    if point_in_rect((mouse_x, mouse_y), button_rect):
                        button_pressed = button_index
                        break

                if menu_state == 0:
                    if button_pressed == 0:
                        menu_state = 2
                    elif button_pressed == 1:
                        connect_as_server = True
                        menu_state = 1
                elif menu_state == 3:
                    if button_pressed == 0:
                        menu_state = 2
                elif menu_state == 4:
                    if button_pressed == 0:
                        network.server_start_game()
                        return_gamestate = GAMESTATE_GAME
                        running = False
            elif event.type == pygame.KEYDOWN:
                if menu_textbox_type[menu_state] == 0:
                    continue
                if menu_textbox_type[menu_state] == 1 and event.key >= pygame.K_a and event.key <= pygame.K_z:
                    if pygame.key.get_pressed()[pygame.K_LSHIFT] or pygame.key.get_pressed()[pygame.K_RSHIFT]:
                        textbox_input += str(chr(event.key)).upper()
                    else:
                        textbox_input += chr(event.key)
                elif menu_textbox_type[menu_state] == 1 and event.key == pygame.K_MINUS and (pygame.key.get_pressed()[pygame.K_LSHIFT] or pygame.key.get_pressed()[pygame.K_RSHIFT]):
                    textbox_input += "_"
                elif menu_textbox_type[menu_state] == 2 and event.key >= pygame.K_0 and event.key <= pygame.K_9:
                    textbox_input += chr(event.key)
                elif menu_textbox_type[menu_state] == 2 and event.key >= pygame.K_KP0 and event.key <= pygame.K_KP9:
                    textbox_input += chr(int(event.key) - 208)
                elif menu_textbox_type[menu_state] == 2 and (event.key == pygame.K_PERIOD or event.key == pygame.K_KP_PERIOD):
                    textbox_input += "."
                elif event.key == pygame.K_BACKSPACE:
                    textbox_input = textbox_input[:len(textbox_input) - 1]
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    if menu_state == 1 and connect_as_server:
                        network.server_username = textbox_input
                        network.server_begin(3535)
                        menu_state = 4
                        menu_labels[menu_state].append(("Your IP is " + network.server_ip, (DISPLAY_WIDTH // 2) + 20, playerlist_rect[1]))
                        menu_buttons[menu_state].append(("Start", (DISPLAY_WIDTH // 2) + 20, playerlist_rect[1] + 30, 50, 20))
                    elif menu_state == 1 and not connect_as_server:
                        network.client_send_username(textbox_input)
                    if menu_state == 2:
                        network.client_connect(textbox_input, 3535)
                        menu_state = 3
                    textbox_input = ""

        if menu_state == 3:
            if network.client_check_response():
                menu_state = 1
        elif menu_state == 1 and not connect_as_server:
            response = network.client_check_response()
            if response != 0:
                local_player_index = response
                menu_state = 4
                menu_labels[menu_state].append(("Waiting on host", (DISPLAY_WIDTH // 2) + 20, playerlist_rect[1]))
        elif menu_state == 4:
            if connect_as_server:
                network.server_read()
                player_usernames = [network.server_username] + list(network.server_client_usernames.values())
                network.server_lobby_write()
            else:
                data = network.client_lobby_read()
                if data == "start":
                    return_gamestate = GAMESTATE_GAME
                    running = False
                elif data != []:
                    player_usernames = data
                network.client_lobby_write()

        display_clear()

        for label in menu_labels[menu_state]:
            label_texture = font_small.render(label[0], False, color_white)
            coords = [label[1], label[2]]
            if coords[0] == -1:
                coords[0] = (DISPLAY_WIDTH // 2) - (label_texture.get_width() // 2)
            if coords[1] == -1:
                coords[1] = (DISPLAY_HEIGHT // 2) - (label_texture.get_height() // 2)
            display.blit(label_texture, coords)

        for button in menu_buttons[menu_state]:
            button_rect = list(button[1:])
            if button_rect[0] == -1:
                button_rect[0] = (DISPLAY_WIDTH // 2) - (button_rect[2] // 2)
            if button_rect[1] == -1:
                button_rect[1] = (DISPLAY_HEIGHT // 2) - (button_rect[3] // 2)
            button_hovered = point_in_rect((mouse_x, mouse_y), button_rect)
            button_label_texture = None
            if button_hovered:
                button_label_texture = font_small.render(button[0], False, color_black)
            else:
                button_label_texture = font_small.render(button[0], False, color_white)
            label_coords = [button_rect[0] + (button_rect[2] // 2) - (button_label_texture.get_width() // 2), button_rect[1] + (button_rect[3] // 2) - (button_label_texture.get_height() // 2)]
            pygame.draw.rect(display, color_white, button_rect, not button_hovered)
            display.blit(button_label_texture, label_coords)

        if menu_textbox_type[menu_state] != 0:
            textbox_input_label = font_small.render(textbox_input, False, color_white)
            pygame.draw.rect(display, color_white, textbox_rect, 1)
            display.blit(textbox_input_label, (textbox_rect[0] + 5, textbox_rect[1] + (textbox_rect[3] // 2) - (textbox_input_label.get_height() // 2)))

        if menu_shows_playerlist[menu_state]:
            pygame.draw.rect(display, color_white, playerlist_rect, 1)
            username_render_y = playerlist_rect[1] + 5
            for username in player_usernames:
                username_label = font_small.render(username, False, color_white)
                display.blit(username_label, (playerlist_rect[0] + 5, username_render_y))
                username_render_y += username_label.get_height() + 5

        if show_fps:
            render_fps()

        display_flip()

        clock.tick(TARGET_FPS)

    return return_gamestate


def game():
    global connect_as_server, ping, client_reping_count

    running = True
    return_gamestate = GAMESTATE_EXIT
    gamestate.local_player_index = local_player_index

    display_render_loadscreen("Loading animations...")
    animations.load_all()
    display_render_loadscreen("Loading spells...")
    spells.spell_define_all()
    gamestate.screen_dimensions_set((SCREEN_WIDTH, SCREEN_HEIGHT))
    display_render_loadscreen("Generating map...")
    gamestate.map_load(animations.image_map, animations.image_map_alpha)

    display_render_loadscreen("Initializing players...")
    for username in player_usernames:
        gamestate.create_player()
    gamestate.player_camera_initial_position_set(local_player_index)

    display_render_loadscreen("Waiting for other players...")
    if connect_as_server:
        patience_timeout = 30 * 1000
        patience_before_time = pygame.time.get_ticks()
        patience_timer = 0
        while patience_timer < patience_timeout:
            if network.server_check_clients_ready():
                break
            patience_after_time = pygame.time.get_ticks()
            patience_timer += patience_after_time - patience_before_time
            patience_before_time = pygame.time.get_ticks()
        network.server_send_all_ready()
    else:
        patience_timeout = 60 * 1000
        patience_before_time = pygame.time.get_ticks()
        patience_timer = 0
        network.client_send_ready()
        got_server_ready = False
        while patience_timer < patience_timeout and not got_server_ready:
            if network.client_check_server_ready():
                got_server_ready = True
            time.sleep(1)
            patience_after_time = pygame.time.get_ticks()
            patience_timer += patience_after_time - patience_before_time
            patience_before_time = pygame.time.get_ticks()
        if not got_server_ready:
            return GAMESTATE_EXIT

    text_death = font_big.render("You Died", False, color_red)
    text_victory = font_big.render("You Won!", False, color_green)
    game_is_over = False

    before_time = pygame.time.get_ticks()
    ping_before_time = before_time
    pinging = False
    last_pings = []

    missed_delta = 0
    missed_packets = 0
    append_missing_delta = False
    input_cache = []

    # first flush out any input given during the loading screen
    for event in pygame.event.get():
        continue

    while running:
        # Input
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.KEYDOWN:
                input_name = None
                if event.key == pygame.K_w:
                    input_name = gamestate.INPUT_UP
                elif event.key == pygame.K_s:
                    input_name = gamestate.INPUT_DOWN
                elif event.key == pygame.K_d:
                    input_name = gamestate.INPUT_RIGHT
                elif event.key == pygame.K_a:
                    input_name = gamestate.INPUT_LEFT
                if input_name is not None:
                    gamestate.player_input_queue_append(local_player_index, (True, input_name))
                    if not connect_as_server:
                        network.client_event_queue.append((True, input_name))
                        input_cache.append((True, input_name))
            elif event.type == pygame.KEYUP:
                input_name = None
                if event.key == pygame.K_w:
                    input_name = gamestate.INPUT_UP
                elif event.key == pygame.K_s:
                    input_name = gamestate.INPUT_DOWN
                elif event.key == pygame.K_d:
                    input_name = gamestate.INPUT_RIGHT
                elif event.key == pygame.K_a:
                    input_name = gamestate.INPUT_LEFT
                if input_name is not None:
                    gamestate.player_input_queue_append(local_player_index, (False, input_name))
                    if not connect_as_server:
                        network.client_event_queue.append((False, input_name))
                        input_cache.append((False, input_name))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_pos = gamestate.player_input_offset_mouse_position_get(event.pos[0] // SCALE, event.pos[1] // SCALE)
                    gamestate.player_input_queue_append(local_player_index, (True, gamestate.INPUT_SPELLCAST, mouse_pos))
                    if not connect_as_server:
                        network.client_event_queue.append((True, gamestate.INPUT_SPELLCAST, mouse_pos))
                        input_cache.append((True, gamestate.INPUT_SPELLCAST, mouse_pos))
                elif event.button == 3:
                    mouse_pos = gamestate.player_input_offset_mouse_position_get(event.pos[0] // SCALE, event.pos[1] // SCALE)
                    gamestate.player_input_queue_append(local_player_index, (True, gamestate.INPUT_TELEPORT, mouse_pos))
                    if not connect_as_server:
                        network.client_event_queue.append((True, gamestate.INPUT_TELEPORT, mouse_pos))
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_pos = gamestate.player_input_offset_mouse_position_get(event.pos[0] // SCALE, event.pos[1] // SCALE)
                    gamestate.player_input_queue_append(local_player_index, (False, gamestate.INPUT_SPELLCAST, mouse_pos))
                    if not connect_as_server:
                        network.client_event_queue.append((False, gamestate.INPUT_SPELLCAST, mouse_pos))
                        input_cache.append((False, gamestate.INPUT_SPELLCAST, mouse_pos))
            elif event.type == pygame.MOUSEMOTION:
                gamestate.player_input_mouse_position_set(event.pos[0] // SCALE, event.pos[1] // SCALE)
        gamestate.player_input_queue_pump_events(local_player_index)

        # Read network
        if connect_as_server:
            network.server_read()
            while len(network.server_event_queue) != 0:
                server_event = network.server_event_queue.pop(0)
                if server_event[0] == network.SERVER_EVENT_PLAYER_INPUT:
                    gamestate.player_input_queue_append(server_event[1], server_event[2])
        else:
            server_data = network.client_read()

            if len(server_data) != 0:
                if len(last_pings) >= 10:
                    last_pings.pop(0)
                last_pings.append(pygame.time.get_ticks() - ping_before_time)
                ping = sum(last_pings) / len(last_pings)
                pinging = False

                if len(server_data) != 1:
                    print("that's weird we should only get one at a time")

                gamestate.state_data_set(server_data[0])

                input_cache = input_cache[network.client_received_inputs:]
                network.client_received_inputs = 0

                for input_event in input_cache:
                    gamestate.player_input_queue_append(local_player_index, input_event)
                gamestate.player_input_queue_pump_events(local_player_index)

                if missed_delta != 0:
                    gamestate.update(missed_delta, False)
                    missed_delta = 0
            else:
                append_missing_delta = True
                missed_packets += 1

        # Update gamestate
        delta = (pygame.time.get_ticks() - before_time) / UPDATE_TIME
        before_time = pygame.time.get_ticks()

        if append_missing_delta:
            missed_delta += delta
            append_missing_delta = False

        gamestate.update(delta)
        gamestate.player_camera_position_set(local_player_index)
        gamestate.gameover_timer_update(local_player_index, delta)

        if game_is_over and gamestate.gameover_state_get(local_player_index) == 0:
            gamestate.player_camera_position_set(local_player_index)
            game_is_over = False

        # Write network
        if connect_as_server:
            network.server_write(gamestate.state_data_get())
        else:
            if not pinging:
                ping_before_time = pygame.time.get_ticks()
                pinging = True
                network.client_write(pinging)
            else:
                if pygame.time.get_ticks() - ping_before_time >= 5000:
                    # Assume our packet got lost to the server
                    for input_event in input_cache:
                        network.client_event_queue.append(input_event)
                    missed_packets = 0
                    network.client_write(pinging)
                    client_reping_count += 1

        display_clear()

        # Draw map
        display.blit(animations.image_map, (0 - gamestate.player_camera_offset[0], 0 - gamestate.player_camera_offset[1]))

        # Draw players
        for player_index in range(0, gamestate.player_count_get()):
            if gamestate.player_health[player_index] <= 0:
                continue
            player_coords = gamestate.player_render_coordinates_get(player_index)
            player_frame = gamestate.player_animation_frame_get(player_index)
            player_book_frame = gamestate.player_animation_frame_book_get(player_index)
            display.blit(player_frame, player_coords)
            if player_book_frame is not None:
                display.blit(player_book_frame, player_coords)

            teleport_coords = gamestate.player_teleport_render_coordinates_get(player_index)
            if teleport_coords is not None:
                player_teleport_frame = gamestate.player_animation_teleport_frame_get(player_index)
                display.blit(player_teleport_frame, teleport_coords)

            player_rect_raw = gamestate.player_rect_get(player_index)
            player_rect_raw[0] -= gamestate.player_camera_offset[0]
            player_rect_raw[1] -= gamestate.player_camera_offset[1]
            # pygame.draw.rect(display, color_red, player_rect_raw, 1)

        # Draw spells
        for spell_index in range(0, gamestate.spell_count_get()):
            # spell_coords = gamestate.player_spell_render_coordinates_get(spell_index)
            spell_coords, spell_angle = gamestate.spell_render_coords_get(spell_index)
            spell_image, offset_coords = animations.get_rotated_image(animations.image_magic_missile, spell_angle)
            spell_coords[0] += offset_coords[0]
            spell_coords[1] += offset_coords[1]
            display.blit(spell_image, spell_coords)

        # Draw UI
        player_health = gamestate.player_health_percentage_get(local_player_index)
        if player_health == 1:
            display.blit(animations.image_health_full, (0, 0))
        elif player_health == 0:
            display.blit(animations.image_health_empty, (0, 0))
        else:
            heart_width = animations.image_health_full.get_width()
            heart_height = animations.image_health_full.get_height()
            empty_height = int(heart_height * (1 - player_health))
            display.blit(animations.image_health_empty.subsurface(0, 0, heart_width, empty_height), (0, 0))
            display.blit(animations.image_health_full.subsurface(0, empty_height, heart_width, heart_height - empty_height), (0, empty_height))

        player_charge_percent = gamestate.player_spell_charge_percentage_get(local_player_index)
        if player_charge_percent == 1:
            display.blit(animations.image_chargebar_full, (0, 0))
        if player_charge_percent == 0:
            display.blit(animations.image_chargebar_empty, (0, 0))
        else:
            charge_width = animations.image_chargebar_full.get_width()
            charge_height = animations.image_chargebar_full.get_height()
            full_width = int(charge_width * player_charge_percent)
            display.blit(animations.image_chargebar_full.subsurface(0, 0, full_width, charge_height), (0, 0))
            display.blit(animations.image_chargebar_empty.subsurface(full_width, 0, charge_width - full_width, charge_height), (full_width, 0))

        display.blit(animations.image_toolbar, (0, 0))
        player_cooldown_timers = gamestate.player_cooldown_percents_get(local_player_index)
        if player_cooldown_timers[0] == 0:
            pygame.draw.rect(display, color_yellow, (38, 7, 20, 20), False)
        else:
            pygame.draw.rect(display, color_red, (38, 7 + int(20 * player_cooldown_timers[0]), 20, int(20 * (1 - player_cooldown_timers[0]))), False)
        player_teleport_cooldown = gamestate.player_teleport_cooldown_percent_get(local_player_index)
        if player_teleport_cooldown is None:
            pygame.draw.rect(display, color_yellow, (61, 7, 20, 20), False)
        else:
            pygame.draw.rect(display, color_red, (61, 7 + int(20 * (1 - player_teleport_cooldown)), 20, int(20 * player_teleport_cooldown)), False)

        # Draw gameover
        if gamestate.gameover_state_get(local_player_index) == -1:
            display.blit(text_death, ((DISPLAY_WIDTH // 2) - (text_death.get_width() // 2), (DISPLAY_HEIGHT // 2) - (text_death.get_height() // 2)))
            game_is_over = True
        elif gamestate.gameover_state_get(local_player_index) == 1:
            display.blit(text_victory, ((DISPLAY_WIDTH // 2) - (text_victory.get_width() // 2), (DISPLAY_HEIGHT // 2) - (text_victory.get_height() // 2)))
            game_is_over = True

        if show_fps:
            render_fps()

        display_flip()

        clock.tick(TARGET_FPS)

    return return_gamestate


def point_in_rect(point, rect):
    return point[0] >= rect[0] and point[0] <= rect[0] + rect[2] and point[1] >= rect[1] and point[1] <= rect[1] + rect[3]


def display_clear():
    pygame.draw.rect(display, color_black, (0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT), False)


def display_flip():
    pygame.transform.scale(display, (SCREEN_WIDTH, SCREEN_HEIGHT), screen)
    pygame.display.flip()


def display_render_loadscreen(loadscreen_text):
    display_clear()
    loadscreen_surface = font_small.render(loadscreen_text, False, color_white)
    display.blit(loadscreen_surface, ((DISPLAY_WIDTH // 2) - (loadscreen_surface.get_width() // 2), (DISPLAY_HEIGHT // 2) - (loadscreen_surface.get_height())))
    display_flip()


def render_fps():
    ping_value = 0
    if connect_as_server:
        ping_value = network.server_last_ping_at_once
    else:
        ping_value = ping
    text_fps = font_small.render("FPS: " + str(round(clock.get_fps())) + "  Ping: " + str(ping_value), False, color_red)
    reping_text = font_small.render("Repings: " + str(client_reping_count), False, color_red)
    display.blit(text_fps, (0, DISPLAY_HEIGHT - 16))
    display.blit(reping_text, (0, DISPLAY_HEIGHT - 32))


if __name__ == "__main__":
    current_gamestate = GAMESTATE_MENU
    while current_gamestate != GAMESTATE_EXIT:
        if current_gamestate == GAMESTATE_MENU:
            current_gamestate = menu()
        elif current_gamestate == GAMESTATE_GAME:
            current_gamestate = game()
    pygame.quit()
