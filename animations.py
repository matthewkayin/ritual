import pygame

image_path = "res/"

ANIMATION_PLAYER_IDLE = 0
ANIMATION_PLAYER_RUN = 1
ANIMATION_PLAYER_WALK = 2

animation_frames = []
animation_frame_size = []
animation_frame_count = []
animation_frame_duration = []

animation_paths = ["idlewizard", "runwizard", "walkwizard"]

image_map = None


def load_all():
    global image_map

    load_from_file(ANIMATION_PLAYER_IDLE, (20, 32), 14, 1.5, True)
    load_from_file(ANIMATION_PLAYER_RUN, (31, 32), 4, 0.4, True)
    load_from_file(ANIMATION_PLAYER_WALK, (24, 32), 5, 1.2, True)

    image_map = pygame.image.load(image_path + "testmap.png").convert()


def load_from_file(animation_name, frame_size, frame_count, duration, has_alpha):
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
            animation_instance[2] = 0


def instance_frame_get(animation_instance, is_flipped):
    return [animation_instance[0], animation_instance[2], is_flipped]


def image_get_from_frame(animation_data):
    global animation_frames

    return pygame.transform.flip(animation_frames[animation_data[0]][animation_data[1]], animation_data[2], False)
