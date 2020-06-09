import pygame
import sys
import os
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
player_teams = []


def menu():
    global connect_as_server, local_player_index, player_usernames

    running = True
    return_gamestate = GAMESTATE_EXIT

    mouse_x, mouse_y = (0, 0)

    button_rects = []
    button_text_coords = []
    button_texts = []
    button_texts_offcolor = []
    button_width = 50
    button_height = 20
    button_padding = 10
    button_text_strings = ("Join", "Host")
    for i in range(0, len(button_text_strings)):
        button_x = (DISPLAY_WIDTH // 2) - (button_width // 2)
        button_y = 100 + ((button_height + button_padding) * i)
        button_rects.append((button_x, button_y, button_width, button_height))
        button_texts.append(font_small.render(button_text_strings[i], False, color_white))
        button_texts_offcolor.append(font_small.render(button_text_strings[i], False, color_black))
        button_text_x = button_x + (button_width // 2) - (button_texts[i].get_width() // 2)
        button_text_y = button_y + (button_height // 2) - (button_texts[i].get_height() // 2)
        button_text_coords.append((button_text_x, button_text_y))

    ip_box_width = 200
    ip_box_height = 20
    ip_box_rect = [(DISPLAY_WIDTH // 2) - (ip_box_width // 2), 100, ip_box_width, ip_box_height]
    ip_box_label = font_small.render("Enter Host IP: ", False, color_white)
    ip_label_coords = [ip_box_rect[0] + 10, ip_box_rect[1] - 16]
    ip_box_number_keys = [pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]
    ip_box_numpad_keys = [pygame.K_KP0, pygame.K_KP1, pygame.K_KP2, pygame.K_KP3, pygame.K_KP4, pygame.K_KP5, pygame.K_KP6, pygame.K_KP7, pygame.K_KP8, pygame.K_KP9]
    ip_box_input = ""

    connecting_label = font_small.render("Connecting... ", False, color_white)
    connecting_label_coords = [(DISPLAY_WIDTH // 2) - (connecting_label.get_width() // 2), 100]
    connecting_timeout_label = font_small.render("Connection timed out", False, color_white)
    connecting_timeout_label_coords = [(DISPLAY_WIDTH // 2) - (connecting_timeout_label.get_width() // 2), 100]
    cancel_label = font_small.render("Cancel", False, color_white)
    cancel_label_offcolor = font_small.render("Cancel", False, color_black)
    cancel_label_coords = [button_rects[1][0] + 5, button_rects[1][1] + 2]
    connection_ping_timer = 0
    connection_ping_delay = 60
    connection_ping_attempts = 5

    input_username = ""
    username_label = font_small.render("Enter username: ", False, color_white)

    team_box_rect = [[10, 10, 200, DISPLAY_HEIGHT - 20]]
    team_box_rect.append([team_box_rect[0][0] + team_box_rect[0][2] + team_box_rect[0][0], team_box_rect[0][1], team_box_rect[0][2], team_box_rect[0][3]])
    team_box_buttons = [[team_box_rect[1][0] + team_box_rect[0][0] + team_box_rect[0][2], team_box_rect[0][0], 100, 50]]
    team_box_buttons.append([team_box_buttons[0][0], team_box_buttons[0][1] + team_box_buttons[0][3] + team_box_buttons[0][1], team_box_buttons[0][2], team_box_buttons[0][3]])
    team_box_labels = [font_small.render("Change Team", False, color_white), font_small.render("Start Game", False, color_white)]
    team_box_labels_offcolor = [font_small.render("Change Team", False, color_black), font_small.render("Start Game", False, color_black)]
    team_box_label_coords = [(team_box_buttons[0][0] + 10, team_box_buttons[0][1] + 15), (team_box_buttons[1][0] + 10, team_box_buttons[1][1] + 15)]
    client_should_request_team_swap = False

    menu_state = 0

    while running:
        # Input
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.MOUSEMOTION:
                mouse_x, mouse_y = event.pos[0] // SCALE, event.pos[1] // SCALE
            elif event.type == pygame.MOUSEBUTTONUP:
                if menu_state == 0:
                    for i in range(0, len(button_rects)):
                        button_hovered = point_in_rect((mouse_x, mouse_y), button_rects[i])
                        if button_hovered:
                            if i == 0:
                                menu_state = 1
                            elif i == 1:
                                connect_as_server = True
                                network.server_begin(3535)
                                menu_state = 3
                elif menu_state == 2:
                    if point_in_rect((mouse_x, mouse_y), button_rects[1]):
                        menu_state = 0
                elif menu_state == 4:
                    if point_in_rect((mouse_x, mouse_y), team_box_buttons[0]):
                        if connect_as_server:
                            network.server_team = not network.server_team
                        else:
                            client_should_request_team_swap = True
                    elif point_in_rect((mouse_x, mouse_y), team_box_buttons[1]):
                        network.server_start_game()
                        running = False
                        return_gamestate = GAMESTATE_GAME
            elif event.type == pygame.KEYDOWN:
                if menu_state == 1:
                    if event.key in ip_box_number_keys:
                        ip_box_input += str(ip_box_number_keys.index(event.key))
                    elif event.key in ip_box_numpad_keys:
                        ip_box_input += str(ip_box_numpad_keys.index(event.key))
                    elif event.key == pygame.K_PERIOD or event.key == pygame.K_KP_PERIOD:
                        ip_box_input += "."
                    elif event.key == pygame.K_BACKSPACE:
                        ip_box_input = ip_box_input[:len(ip_box_input) - 1]
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        menu_state = 2
                        connection_ping_timer = connection_ping_delay
                        connection_ping_attempts = 5
                        network.client_connect(ip_box_input, 3535)
                elif menu_state == 3:
                    if event.key >= pygame.K_a and event.key <= pygame.K_z:
                        if len(input_username) < 35:
                            keystates = pygame.key.get_pressed()
                            if keystates[pygame.K_LSHIFT] or keystates[pygame.K_RSHIFT]:
                                input_username += str(chr(event.key)).upper()
                            else:
                                input_username += chr(event.key)
                    elif event.key == pygame.K_SPACE:
                        if len(input_username) < 35:
                            input_username += " "
                    elif event.key == pygame.K_BACKSPACE:
                        input_username = input_username[:len(input_username) - 1]
                    elif event.key == pygame.K_RETURN:
                        if connect_as_server:
                            network.server_set_username(input_username)
                            menu_state = 4
                        else:
                            network.client_send_username(input_username)

        display_clear()

        if menu_state == 0:
            for i in range(0, len(button_rects)):
                button_hovered = point_in_rect((mouse_x, mouse_y), button_rects[i])
                pygame.draw.rect(display, color_white, button_rects[i], not button_hovered)
                if button_hovered:
                    display.blit(button_texts_offcolor[i], button_text_coords[i])
                else:
                    display.blit(button_texts[i], button_text_coords[i])
        elif menu_state == 1:
            display.blit(ip_box_label, ip_label_coords)
            pygame.draw.rect(display, color_white, ip_box_rect, 1)
            ip_input_label = font_small.render(ip_box_input, False, color_white)
            display.blit(ip_input_label, (ip_box_rect[0] + 5, ip_box_rect[1] + 2))
        elif menu_state == 2:
            if connection_ping_attempts != 0:
                display.blit(connecting_label, connecting_label_coords)
            else:
                display.blit(connecting_timeout_label, connecting_timeout_label_coords)
            button_hovered = point_in_rect((mouse_x, mouse_y), button_rects[1])
            if button_hovered:
                pygame.draw.rect(display, color_white, button_rects[1], False)
                display.blit(cancel_label_offcolor, cancel_label_coords)
            else:
                pygame.draw.rect(display, color_white, button_rects[1], 1)
                display.blit(cancel_label, cancel_label_coords)
            if connection_ping_attempts != 0:
                connection_ping_timer -= 1
                if connection_ping_timer <= 0:
                    connection_ping_attempts -= 1
                    if connection_ping_attempts != 0:
                        connection_ping_timer = connection_ping_delay
                        network.client_connect(ip_box_input, 3535)

            if network.client_check_response():
                menu_state = 3
        elif menu_state == 3:
            display.blit(username_label, ip_label_coords)
            pygame.draw.rect(display, color_white, ip_box_rect, 1)
            username_input_label = font_small.render(input_username, False, color_white)
            display.blit(username_input_label, (ip_box_rect[0] + 5, ip_box_rect[1] + 2))
            if not connect_as_server:
                player_index = network.client_check_response()
                if player_index != 0:
                    local_player_index = player_index
                    menu_state = 4
        elif menu_state == 4:
            for index in range(0, len(team_box_rect)):
                pygame.draw.rect(display, color_white, team_box_rect[index], 1)
            for index in range(0, len(team_box_buttons)):
                if index == 1 and not connect_as_server:
                    break
                button_hovered = point_in_rect((mouse_x, mouse_y), team_box_buttons[index])
                if button_hovered:
                    pygame.draw.rect(display, color_white, team_box_buttons[index], False)
                    display.blit(team_box_labels_offcolor[index], team_box_label_coords[index])
                else:
                    pygame.draw.rect(display, color_white, team_box_buttons[index], 1)
                    display.blit(team_box_labels[index], team_box_label_coords[index])
            if connect_as_server:
                network.server_read()
                player_usernames = [network.server_username] + list(network.server_client_usernames.values())
                player_teams = [network.server_team] + list(network.server_client_userteams.values())
                network.server_lobby_write()
            else:
                read_data = network.client_lobby_read()
                if read_data == "start":
                    running = False
                    return_gamestate = GAMESTATE_GAME
                else:
                    if read_data != []:
                        player_teams, player_usernames = read_data
                    network.client_lobby_write(client_should_request_team_swap)
                    client_should_request_team_swap = False
            left_display_index = 1
            right_display_index = 1
            left_label = font_small.render("Purple Team", False, color_white)
            display.blit(left_label, (team_box_rect[0][0] + 5, team_box_rect[0][1] + 2))
            right_label = font_small.render("Green Team", False, color_white)
            display.blit(right_label, (team_box_rect[1][0] + 5, team_box_rect[0][1] + 2))
            for i in range(0, len(player_usernames)):
                username_label = font_small.render(player_usernames[i], False, color_white)
                if player_teams[i]:
                    display.blit(username_label, (team_box_rect[1][0] + 5, team_box_rect[0][1] + 2 + (20 * right_display_index)))
                    right_display_index += 1
                else:
                    display.blit(username_label, (team_box_rect[0][0] + 5, team_box_rect[0][1] + 2 + (20 * left_display_index)))
                    left_display_index += 1

        if show_fps:
            render_fps()

        display_flip()

        clock.tick(TARGET_FPS)

    return return_gamestate


def game():
    global connect_as_server, ping

    running = True
    return_gamestate = GAMESTATE_EXIT

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

    text_death = font_big.render("You Died", False, color_red)
    text_victory = font_big.render("You Won!", False, color_green)
    game_is_over = False

    before_time = pygame.time.get_ticks()
    ping_before_time = before_time
    pinging = False

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
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_pos = gamestate.player_input_offset_mouse_position_get(event.pos[0] // SCALE, event.pos[1] // SCALE)
                    gamestate.player_input_queue_append(local_player_index, (True, gamestate.INPUT_SPELLCAST, mouse_pos))
                    if not connect_as_server:
                        network.client_event_queue.append((True, gamestate.INPUT_SPELLCAST, mouse_pos))
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

            ping = pygame.time.get_ticks() - ping_before_time
            pinging = False

            for command in server_data:
                if command[0] == "set_state":
                    gamestate.state_data_set(command[1:])

        # Update gamestate
        delta = (pygame.time.get_ticks() - before_time) / UPDATE_TIME
        before_time = pygame.time.get_ticks()
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
                network.client_write()

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
        display.blit(animations.image_toolbar, (0, 0))
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
        player_cooldown_timers = gamestate.player_cooldown_percents_get(local_player_index)
        if player_cooldown_timers[0] is None:
            pygame.draw.rect(display, color_yellow, (38, 7, 20, 20), False)
        else:
            pygame.draw.rect(display, color_red, (38, 7 + int(20 * (1 - player_cooldown_timers[0])), 20, int(20 * player_cooldown_timers[0])), False)
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
    text_fps = font_small.render("FPS: " + str(round(clock.get_fps())) + "  Ping: " + str(ping), False, color_yellow)
    display.blit(text_fps, (0, 0))


if __name__ == "__main__":
    current_gamestate = GAMESTATE_MENU
    while current_gamestate != GAMESTATE_EXIT:
        if current_gamestate == GAMESTATE_MENU:
            current_gamestate = menu()
        elif current_gamestate == GAMESTATE_GAME:
            current_gamestate = game()
    pygame.quit()
