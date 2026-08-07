import re

with open('c:/Users/PC/Desktop/py/boxhead/Pygame_Versiyonu/entities/enemy.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add xp_mult definition at the start of __init__
init_pattern = r'def __init__\(self, id, x, y, game, type="normal", wave_level=1\):\n        self\.id = id'
replacement_init = 'def __init__(self, id, x, y, game, type="normal", wave_level=1):\n        self.id = id\n        xp_mult = min(15.0, 1.1 ** wave_level)'
content = re.sub(init_pattern, replacement_init, content)

# Replace all xp_reward lines using regex
content = re.sub(r'self\.xp_reward = (\d+) \* \(1\.1 \*\* wave_level\)', r'self.xp_reward = \1 * xp_mult', content)
content = re.sub(r'self\.xp_reward = (\d+) \* \(1\.15 \*\* wave_level\)', r'self.xp_reward = \1 * xp_mult', content)

with open('c:/Users/PC/Desktop/py/boxhead/Pygame_Versiyonu/entities/enemy.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Replacement done.")
