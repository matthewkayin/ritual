import pygame
import sys
import os

# Handle cli flags
windowed = "--windowed" in sys.argv
show_fps = "--showfps" in sys.argv
if "--debug" in sys.argv:
    windowed = True
    show_fps = True

# Resolution variables
# Display stretches to Screen. Screen is set by user
DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

SCALE = SCREEN_WIDTH / DISPLAY_WIDTH

# Timing variables

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

# Colors
color_black = (0, 0, 0) 
color_yellow = (255, 255, 0) 

# Fonts
font_small = pygame.font.SysFont("Serif", 11)

# Game states
GAMESTATE_EXIT = 0


def game():

    # Timing variables
    TARGET_FPS = 60
    SECOND = 1000
    UPDATE_TIME = SECOND / 60.0
    fps = 0
    frames = 0
    delta_time = 0
    frame_before_time = 0
    second_before_time = 0

    running = True

    while running:
        # Input
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()

        # Update

        # Render

        # Clear display
        pygame.draw.rect(display, color_black, (0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT), False)

        if show_fps:
            text_fps = font_small.render("FPS: " + str(fps), False, color_yellow)
            display.blit(text_fps, (0, 0))

        # Flip display
        pygame.transform.scale(display, (SCREEN_WIDTH, SCREEN_HEIGHT), screen)
        pygame.display.flip()
        frames += 1

        # Timekeep
        frame_after_time = pygame.time.get_ticks()
        delta_time = (frame_after_time - frame_before_time) / UPDATE_TIME

        if frame_after_time - second_before_time >= SECOND:
            fps = frames
            frames = 0
            second_before_time += SECOND
        frame_before_time = pygame.time.get_ticks()

        clock.tick(TARGET_FPS)

    return GAMESTATE_EXIT


if __name__ == "__main__":
    frame_before_time = pygame.time.get_ticks()
    second_before_time = frame_before_time
    
    next_gamestate = game()

    if next_gamestate == GAMESTATE_EXIT:
        pygame.quit()
