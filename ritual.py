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

# Fonts
font_small = pygame.font.SysFont("Serif", 11)

# Gamestates
GAMESTATE_EXIT = -1
GAMESTATE_MENU = 0
GAMESTATE_GAME = 1

connect_as_server = False


def menu():
    global connect_as_server

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

    while running:
        # Input
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.MOUSEMOTION:
                mouse_x, mouse_y = event.pos[0] // SCALE, event.pos[1] // SCALE
            elif event.type == pygame.MOUSEBUTTONUP:
                for i in range(0, len(button_rects)):
                    button_hovered = point_in_rect((mouse_x, mouse_y), button_rects[i])
                    if button_hovered:
                        if i == 0:
                            return_gamestate = GAMESTATE_GAME
                            running = False
                        elif i == 1:
                            connect_as_server = True
                            return_gamestate = GAMESTATE_GAME
                            running = False

        display_clear()

        for i in range(0, len(button_rects)):
            button_hovered = point_in_rect((mouse_x, mouse_y), button_rects[i])
            pygame.draw.rect(display, color_white, button_rects[i], not button_hovered)
            if button_hovered:
                display.blit(button_texts_offcolor[i], button_text_coords[i])
            else:
                display.blit(button_texts[i], button_text_coords[i])

        if show_fps:
            render_fps()

        display_flip()

        clock.tick(TARGET_FPS)

    return return_gamestate


def game():
    global connect_as_server, ping

    running = True
    return_gamestate = GAMESTATE_EXIT

    local_player_index = 0

    if connect_as_server:
        network.server_begin(3535)
    else:
        network.client_connect("127.0.0.1", 3535)
        while not network.client_connected:
            data = network.client_read()
            for command in data:
                if command[0] == "ack":
                    local_player_index = command[1]

    animations.load_all()
    spells.spell_define_all()
    gamestate.screen_dimensions_set((SCREEN_WIDTH, SCREEN_HEIGHT))
    gamestate.map_load()
    gamestate.create_player()

    before_time = pygame.time.get_ticks()
    ping_before_time = before_time

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
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_pos = gamestate.player_input_offset_mouse_position_get(event.pos[0] // SCALE, event.pos[1] // SCALE)
                    gamestate.player_input_queue_append(local_player_index, (False, gamestate.INPUT_SPELLCAST, mouse_pos))
                    if not connect_as_server:
                        network.client_event_queue.append((False, gamestate.INPUT_SPELLCAST, mouse_pos))
            elif event.type == pygame.MOUSEMOTION:
                gamestate.player_input_mouse_position_set(event.pos[0] // SCALE, event.pos[1] // SCALE)

        # Read network
        if connect_as_server:
            network.server_read()
            while len(network.server_event_queue) != 0:
                server_event = network.server_event_queue.pop(0)
                if server_event[0] == network.SERVER_EVENT_NEW_PLAYER:
                    gamestate.create_player()
                elif server_event[0] == network.SERVER_EVENT_PLAYER_INPUT:
                    gamestate.player_input_queue_append(server_event[1], server_event[2])
        else:
            server_data = network.client_read()

            ping = pygame.time.get_ticks() - ping_before_time

            for command in server_data:
                if command[0] == "set_state":
                    gamestate.state_data_set(command[1:])

        # Update gamestate
        delta = (pygame.time.get_ticks() - before_time) / UPDATE_TIME
        before_time = pygame.time.get_ticks()
        gamestate.update(delta)
        gamestate.player_camera_position_set(local_player_index)

        # Write network
        if connect_as_server:
            network.server_write(gamestate.state_data_get())
        else:
            ping_before_time = pygame.time.get_ticks()
            network.client_write()

        display_clear()

        # Draw map
        display.blit(animations.image_map, (0 - gamestate.player_camera_offset[0], 0 - gamestate.player_camera_offset[1]))

        # Draw players
        for player_index in range(0, gamestate.player_count_get()):
            player_coords = gamestate.player_render_coordinates_get(player_index)
            player_frame = gamestate.player_animation_frame_get(player_index)
            player_book_frame = gamestate.player_animation_frame_book_get(player_index)
            display.blit(player_frame, player_coords)
            if player_book_frame is not None:
                display.blit(player_book_frame, player_coords)

            # player_rect_raw = gamestate.player_rect_get(player_index)
            # player_rect_raw[0] -= gamestate.player_camera_offset[0]
            # player_rect_raw[1] -= gamestate.player_camera_offset[1]
            # pygame.draw.rect(display, color_red, player_rect_raw, 1)

        # Draw spells
        for spell_index in range(0, gamestate.spell_count_get()):
            spell_coords = gamestate.player_spell_render_coordinates_get(spell_index)
            pygame.draw.rect(display, color_red, spell_coords, False)

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
