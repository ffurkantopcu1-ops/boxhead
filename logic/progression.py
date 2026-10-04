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
