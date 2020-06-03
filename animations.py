import pygame

image_path = "res/"

ANIMATION_PLAYER_IDLE = 0
ANIMATION_PLAYER_RUN = 1
ANIMATION_PLAYER_WALK = 2
ANIMATION_PLAYER_CAST_MISSILE = 3

animation_frames = []
animation_frame_size = []
animation_frame_count = []
animation_frame_duration = []
animation_loops = []

animation_paths = ["idlewizard", "runwizard", "walkwizard", "castmagicmissile"]

image_map = None
image_health_full = None
image_health_empty = None
image_toolbar = None


def load_all():
    global image_map, image_health_full, image_health_empty, image_toolbar

    load_from_file(ANIMATION_PLAYER_IDLE, (20, 32), 14, 1.5, True, True)
    load_from_file(ANIMATION_PLAYER_RUN, (31, 32), 4, 0.4, True, True)
    load_from_file(ANIMATION_PLAYER_WALK, (27, 32), 5, 0.5, True, True)
    load_from_file(ANIMATION_PLAYER_CAST_MISSILE, (31, 31), 7, 0.8, False, True)

    image_map = pygame.image.load(image_path + "testmap.png").convert()
    image_health_full = pygame.image.load(image_path + "uifullheart.png").convert_alpha()
    image_health_empty = pygame.image.load(image_path + "uiemptyheart.png").convert_alpha()
    image_toolbar = pygame.image.load(image_path + "uitoolbar.png").convert_alpha()


def load_from_file(animation_name, frame_size, frame_count, duration, looping, has_alpha):
    global image_path, animation_paths, animation_frames, animation_frame_size, animation_frame_count

    path = animation_paths[animation_name]

    source_image = None
    if has_alpha:
        source_image = pygame.image.load(image_path + path + ".png").convert_alpha()
    else:
        source_image = pygame.image.load(image_path + path + ".png").convert()

    animation_frame_size.append(frame_size)
    animation_frame_count.append(frame_count)
    animation_frame_duration.append(int((60 * duration) / frame_count))
    animation_frames.append([])
    coords = [0, 0]
    for i in range(0, frame_count):
        animation_frames[animation_name].append(source_image.subsurface(coords[0], coords[1], frame_size[0], frame_size[1]))
        coords[0] += frame_size[0]
        if coords[0] >= source_image.get_width():
            coords[0] = 0
            coords[1] += frame_size[1]
    animation_loops.append(looping)


def instance_create(animation_name):
    return [animation_name, 0, 0]


def instance_reset(animation_instance):
    animation_instance[1] = 0
    animation_instance[2] = 0


def instance_update(animation_instance, delta):
    global animation_frame_count, animation_frame_duration

    animation_instance[1] += delta
    if animation_instance[1] >= animation_frame_duration[animation_instance[0]]:
        animation_instance[1] -= animation_frame_duration[animation_instance[0]]
        animation_instance[2] += 1
        if animation_instance[2] >= animation_frame_count[animation_instance[0]]:
            if animation_loops[animation_instance[0]]:
                animation_instance[2] = 0
            else:
                animation_instance[2] -= 1


def instance_frame_get(animation_instance, is_flipped):
    return [animation_instance[0], animation_instance[2], is_flipped]


def instance_finished(animation_instance):
    return (not animation_loops[animation_instance[0]]) and animation_instance[2] >= animation_frame_count[animation_instance[0]] - 1


def instance_cast_animation_ready(animation_instance):
    if animation_instance[0] == ANIMATION_PLAYER_CAST_MISSILE:
        return animation_instance[2] >= 3
    else:
        return False


def image_get_from_frame(animation_data):
    global animation_frames

    return pygame.transform.flip(animation_frames[animation_data[0]][animation_data[1]], animation_data[2], False)
