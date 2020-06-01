SPELL_DELETE_ME = -1
SPELL_MAGIC_MISSILE = 0

CHARGE_INSTANT = 0
CHARGE_PARTIAL_CAST = 1
CHARGE_REQUIRES_FULL = 2

spell_charge_type = []
spell_charge_time = []
spell_cooldown_time = []
spell_time_to_live = []
spell_size = []
spell_speed = []
spell_damage = []


def spell_define(name, charge_type, charge_time, cooldown_time, time_to_live, size, speed, damage):
    spell_charge_type.append(charge_type)
    spell_charge_time.append(int(60 * charge_time))
    spell_cooldown_time.append(int(60 * cooldown_time))
    spell_time_to_live.append(int(60 * time_to_live))
    spell_size.append(size)
    spell_speed.append(speed)
    spell_damage.append(damage)


def spell_define_all():
    spell_define(SPELL_MAGIC_MISSILE, CHARGE_INSTANT, 0, 3.0, 3.0, (10, 10), 5, 60)


def spell_charge_type_get(spell_name):
    return spell_charge_type(spell_name)


def spell_speed_get(spell_name):
    return spell_speed[spell_name]


def instance_create(spell_name):
    # spell name = 0, timer = 1, x = 2, y = 3, vx = 4, vy = 5
    return [spell_name, 0, 0, 0, 0, 0]


def instance_values_set(spell_instance, values):
    for i in range(0, len(values)):
        spell_instance[1 + i] = values[i]


def instance_timer_set(spell_instance, value):
    spell_instance[1] = value


def instance_velocity_get(spell_instance):
    return [spell_instance[4], spell_instance[5]]


def instance_velocity_set(spell_instance, new_velocity):
    spell_instance[4] = new_velocity[0]
    spell_instance[5] = new_velocity[1]


def instance_cast(spell_instance, origin, aim_vector):
    spell_instance[1] = 0
    spell_rect = instance_rect_get(spell_instance)
    spell_instance[2] = origin[0] - (spell_rect[2] // 2)
    spell_instance[3] = origin[1] - (spell_rect[3] // 2)
    spell_instance[4] = aim_vector[0]
    spell_instance[5] = aim_vector[1]


def instance_cast_ready(spell_instance):
    instance_name = spell_instance[0]
    return (spell_charge_type[instance_name] == CHARGE_REQUIRES_FULL and spell_instance[1] >= spell_charge_time[instance_name]) or True


def instance_cast_cancel(spell_instance):
    spell_instance[0] = SPELL_DELETE_ME


def instance_update(spell_instance, delta, is_cast=True):
    spell_instance[1] += delta
    if is_cast:
        if spell_instance[1] >= spell_time_to_live[spell_instance[0]]:
            spell_instance[0] = SPELL_DELETE_ME
            return
        spell_instance[2] += spell_instance[4] * delta
        spell_instance[3] += spell_instance[5] * delta


def instance_rect_get(spell_instance):
    instance_size = spell_size[spell_instance[0]]
    return [int(spell_instance[2]), int(spell_instance[3]), instance_size[0], instance_size[1]]
