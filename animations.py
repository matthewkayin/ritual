import pygame

image_path = "res/"

ANIMATION_PLAYER_IDLE = 0
ANIMATION_PLAYER_RUN = 1
ANIMATION_PLAYER_WALK = 2
ANIMATION_PLAYER_CAST_MISSILE = 3
ANIMATION_PLAYER_IDLE_BOOK_MISSILE = 4
ANIMATION_PLAYER_RUN_BOOK_MISSILE = 5
ANIMATION_PLAYER_WALK_BOOK_MISSILE = 6
ANIMATION_PLAYER_IDLE_CHARGE_BOOK_MISSILE = 7
ANIMATION_PLAYER_TELEPORT_ENTER = 8
ANIMATION_PLAYER_TELEPORT_EXIT = 9

animation_frames = []
animation_frame_size = []
animation_frame_count = []
animation_frame_duration = []
animation_loops = []

animation_paths = ["idlewizard", "runwizard", "walkwizard", "castmagicmissile", "idlebookmagicmissile", "runbookmagicmissile", "walkbookmagicmissile", "idlebookmagicmissilecharge", "teleportenter", "teleportexit"]

image_map = None
image_map_alpha = None
image_health_full = None
image_health_empty = None
image_toolbar = None
image_chargebar_full = None
image_chargebar_empty = None
image_magic_missile = None
image_hurt_wizard = None


def load_all():
    global image_map, image_map_alpha, image_health_full, image_health_empty, image_toolbar, image_chargebar_full, image_chargebar_empty, image_magic_missile, image_hurt_wizard

    load_from_file(ANIMATION_PLAYER_IDLE, (22, 32), 14, 1.5, True, True)
    load_from_file(ANIMATION_PLAYER_RUN, (31, 32), 4, 0.4, True, True)
    load_from_file(ANIMATION_PLAYER_WALK, (27, 32), 5, 0.5, True, True)
    load_from_file(ANIMATION_PLAYER_CAST_MISSILE, (31, 31), 7, 0.8, False, True)
    load_from_file(ANIMATION_PLAYER_IDLE_BOOK_MISSILE, (22, 32), 14, 1.5, True, True)
    load_from_file(ANIMATION_PLAYER_RUN_BOOK_MISSILE, (31, 32), 4, 0.4, True, True)
    load_from_file(ANIMATION_PLAYER_WALK_BOOK_MISSILE, (27, 32), 5, 0.5, True, True)
    load_from_file(ANIMATION_PLAYER_IDLE_CHARGE_BOOK_MISSILE, (22, 32), 14, 1.5, True, True)
    load_from_file(ANIMATION_PLAYER_TELEPORT_ENTER, (31, 32), 6, 0.5, False, True)
    load_from_file(ANIMATION_PLAYER_TELEPORT_EXIT, (28, 32), 6, 0.5, False, True)

    image_map = pygame.image.load(image_path + "testmap.png").convert()
    image_map_alpha = pygame.image.load(image_path + "testmap.png").convert()
    image_health_full = pygame.image.load(image_path + "uifullheart.png").convert_alpha()
    image_health_empty = pygame.image.load(image_path + "uiemptyheart.png").convert_alpha()
    image_toolbar = pygame.image.load(image_path + "uitoolbar.png").convert_alpha()
    image_chargebar_full = pygame.image.load(image_path + "uichargebarfull.png").convert_alpha()
    image_chargebar_empty = pygame.image.load(image_path + "uichargebar.png").convert_alpha()
    image_magic_missile = pygame.image.load(image_path + "magicmissile.png").convert_alpha()
    image_hurt_wizard = pygame.image.load(image_path + "hurtwizard.png").convert_alpha()


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


def instance_create_with_timer(animation_name, timer):
    frames_passed = timer % animation_frame_duration[animation_name]
    current_frame = frames_passed % animation_frame_count[animation_name]
    time_left = timer - (frames_passed * animation_frame_duration[animation_name])

    return [animation_name, time_left, current_frame]


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


def instance_finished(animation_instance):
    return (not animation_loops[animation_instance[0]]) and animation_instance[2] >= animation_frame_count[animation_instance[0]] - 1


def instance_cast_animation_ready(animation_instance):
    if animation_instance[0] == ANIMATION_PLAYER_CAST_MISSILE:
        return animation_instance[2] >= 3
    else:
        return False


def instance_get_frame_image(animation_instance, is_flipped):
    global animation_frames

    return pygame.transform.flip(animation_frames[animation_instance[0]][animation_instance[2]], is_flipped, False)


def get_flipped_image(image, is_flipped):
    return pygame.transform.flip(image, is_flipped, False)


def instance_get_rotated_frame_image(animation_instance, angle, origin_pos=None):
    image = animation_frames[animation_instance[0]][animation_instance[2]]
    return get_rotated_image(image, angle, origin_pos)


def get_rotated_image(image, angle, origin_pos=None):
    if origin_pos is None:
        origin_pos = image.get_rect().center

    # calculate the axis aligned bounding box of the rotated image
    w, h = image.get_size()
    box = [pygame.math.Vector2(p) for p in [(0, 0), (w, 0), (w, -h), (0, -h)]]
    box_rotate = [p.rotate(angle) for p in box]
    min_box = (min(box_rotate, key=lambda p: p[0])[0], min(box_rotate, key=lambda p: p[1])[1])
    max_box = (max(box_rotate, key=lambda p: p[0])[0], max(box_rotate, key=lambda p: p[1])[1])

    # calculate the translation of the pivot
    pivot = pygame.math.Vector2(origin_pos[0], -origin_pos[1])
    pivot_rotate = pivot.rotate(angle)
    pivot_move = pivot_rotate - pivot

    rotated_image = pygame.transform.rotate(image, angle)
    offset = (int(min_box[0] - origin_pos[0] - pivot_move[0]), int(pivot_move[1] - max_box[1] - origin_pos[1]))

    return rotated_image, offset
