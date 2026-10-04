"""One source of truth for run XP and the 100-point main passive budget."""
MAIN_POINT_CAP = 100


def xp_threshold(level):
    level = max(1, int(level))
    # First two levels arrive before the early crowd-control commitment.
    return 70 + 45 * (level - 1) + 4 * max(0, level - 12) ** 2


def earned_main_points(level):
    return min(MAIN_POINT_CAP, max(0, int(level) - 1) * 2)


def grant_main_points(player):
    target = earned_main_points(player.level)
    previous = getattr(player, 'main_points_earned', 0)
    reward = max(0, target - previous)
    player.main_points_earned = max(previous, target)
    player.skill_points += reward
    return reward


def base_life(level):
    """Life grows with a run; 100 at level 1, 1300 at level 51 before gear."""
    steps = max(0, min(100,int(level)) - 1)
    return round(100 + 12 * steps + .24 * steps * steps)


def enemy_wave_scale(wave):
    # Continuous growth avoids the old abrupt increase every tenth wave.
    wave = max(1,int(wave))
    return 1.25 ** ((wave-1)/10) * (1 + wave*.05)


def enemy_damage_growth(wave):
    return 1 + .035 * max(0,int(wave)-1)
