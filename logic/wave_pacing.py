"""Gradual density ramp; HP and fixed special-wave rules remain independent."""


def wave_count(level, difficulty, cap=600):
    level = max(1, int(level))
    if difficulty == 'Normal':
        early = (28, 40, 54, 70, 88)
        base = early[level-1] if level <= 5 else 88 + (level-5)*18
    else:
        base = (15 + level*8)*5*.85
    mult = {'Normal':1, 'Hard':1.25, 'Very Hard':1.6, 'Impossible':2}.get(difficulty,1)
    return min(cap, int(base*mult))


def active_cap(level, difficulty, default=220):
    if difficulty == 'Normal': return min(default, 10 + max(1, level)*6)
    return {'Hard':260,'Very Hard':320,'Impossible':400}.get(difficulty,default)


def spawn_duration(level, difficulty):
    # No wave 5->6 interval cliff; convergence to the old later-game tempo.
    if difficulty == 'Normal': return max(12., 28.-max(0,level-3)*1.5)
    return (20. if level<=5 else 10.)*{'Hard':.9,'Very Hard':.75,'Impossible':.6}.get(difficulty,1)
