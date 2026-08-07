# MASTER PROMPT: Abyssal Lord Bullet Hell Patterns

**To the AI Assistant (Gemini Flash / Code Generator):**
Your task is to implement 6 unique, high-performance projectile patterns for a Bullet Hell Boss ("Abyssal Lord") in a Pygame project. 
The patterns must be mathematically driven (using `math.sin`, `math.cos`, `time.time()`) and must utilize an existing object pooling system.

### Core Requirements
1.  **Performance:** You MUST use the pre-allocated projectile pool. Do not create new lists dynamically. Use the syntax: 
    `game.projectile_pool.spawn(x, y, vx, vy, proj_id, color, status_effect, **kwargs)`
2.  **Safe Windows:** Every pattern must intentionally leave a "Safe Gap" for the player to dodge through. Bullet Hell is about precision, not impossible walls.

---

### Pattern Specifications

#### 🔥 FIRE PATTERNS (Red, Burn, Maze/Static based)
1.  **Labyrinth Wall (Maze/Static):** Fires a horizontal or vertical wall of slow-moving fire projectiles perpendicular to the player. **Safe Gap:** Leave a 3-projectile wide gap randomly in the wall.
2.  **Breathing Fire Ring (Expanding/Contracting):** Fires a 360-degree ring of fire. The speed of the ring varies based on a sine wave (`math.sin(time.time())`), creating dense waves and sparse waves. **Safe Gap:** The space between the slow and fast waves.
3.  **Fire Sweeper (Rotating Laser):** Shoots a continuous thick line of fire that sweeps in a circle. **Safe Gap:** Program a deliberate 1-second pause every 4 seconds so the player can cross the laser.

#### 🌌 VOID PATTERNS (Purple, Orbital/Dynamic based)
4.  **Void Flower (Flower Petals):** Fires a ring of outward-traveling projectiles. **Safe Gap:** These bullets must have a custom behavior (`behavior="split_on_timer"`) where they stop after 1.5 seconds and split into smaller bullets. The player dodges between the splits.
5.  **Orbital Singularity (Spirals):** Shoots spiral arms of void energy. Add a sine wave wobble to the rotation angle so the spirals wiggle like tentacles. **Safe Gap:** The organic spaces between the wiggling tentacles.
6.  **Geometric Pulse (Hexagon):** Fires projectiles forming an expanding Hexagon shape. **Safe Gap:** Intentionally skip spawning the bullet at the exact midpoint of each of the 6 sides.

---

### Starter Template / Reference Code

Below is the Python logic you should implement into the boss behavior file. Use this exact math and logic:

```python
import math
import random

class AbyssalLordPatterns:

    @staticmethod
    def fire_labyrinth_wall(boss, game, current_time):
        num_projectiles = 15
        gap_index = random.randint(2, num_projectiles - 4)
        gap_width = 3 
        
        direction_angle = math.atan2(game.player.y - boss.y, game.player.x - boss.x)
        wall_normal = direction_angle + (math.pi / 2) 
        speed = 80
        vx = math.cos(direction_angle) * speed
        vy = math.sin(direction_angle) * speed
        spacing = 40 
        start_x = boss.x - math.cos(wall_normal) * (num_projectiles * spacing / 2)
        start_y = boss.y - math.sin(wall_normal) * (num_projectiles * spacing / 2)

        for i in range(num_projectiles):
            if gap_index <= i <= gap_index + gap_width:
                continue # Safe Gap
            spawn_x = start_x + math.cos(wall_normal) * (i * spacing)
            spawn_y = start_y + math.sin(wall_normal) * (i * spacing)
            game.projectile_pool.spawn(x=spawn_x, y=spawn_y, vx=vx, vy=vy, proj_id="fire_orb", color="red", status_effect="burn")

    @staticmethod
    def breathing_fire_ring(boss, game, current_time):
        num_projectiles = 24
        speed_modifier = math.sin(current_time * 2.5) * 80 
        final_speed = 120 + speed_modifier
        angle_offset = current_time * 0.5
        for i in range(num_projectiles):
            angle = angle_offset + (i / num_projectiles) * 2 * math.pi
            vx = math.cos(angle) * final_speed
            vy = math.sin(angle) * final_speed
            game.projectile_pool.spawn(x=boss.x, y=boss.y, vx=vx, vy=vy, proj_id="fire_orb", color="red", status_effect="burn")

    @staticmethod
    def fire_sweeper(boss, game, current_time):
        if current_time % 4.0 < 1.0: # Safe Gap pause
            return 
        sweep_angle = current_time * 3.0 
        speed = 250
        for offset in [0, 0.1, 0.2]: 
            angle = sweep_angle + offset
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            game.projectile_pool.spawn(x=boss.x, y=boss.y, vx=vx, vy=vy, proj_id="fire_orb", color="dark_red", status_effect="burn")

    @staticmethod
    def void_flower_split(boss, game, current_time):
        num_petals = 8
        speed = 150
        angle_offset = math.sin(current_time) 
        for i in range(num_petals):
            angle = angle_offset + (i / num_petals) * 2 * math.pi
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            game.projectile_pool.spawn(x=boss.x, y=boss.y, vx=vx, vy=vy, proj_id="void_seed", color="purple", status_effect="silence", behavior="split_on_timer", timer=1.5)

    @staticmethod
    def orbital_singularity(boss, game, current_time):
        num_arms = 4
        speed = 180
        base_angle = current_time * 2.0
        wobble = math.sin(current_time * 5.0) * 0.5 
        for i in range(num_arms):
            angle = base_angle + wobble + (i / num_arms) * 2 * math.pi
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            game.projectile_pool.spawn(x=boss.x, y=boss.y, vx=vx, vy=vy, proj_id="void_tear", color="dark_purple", status_effect="silence")

    @staticmethod
    def geometric_pulse(boss, game, current_time):
        sides = 6
        projectiles_per_side = 5
        speed = 100
        radius = 20 
        rotation = current_time * 0.5
        for i in range(sides):
            corner_angle_1 = rotation + (i / sides) * 2 * math.pi
            corner_angle_2 = rotation + ((i + 1) / sides) * 2 * math.pi
            x1 = boss.x + math.cos(corner_angle_1) * radius
            y1 = boss.y + math.sin(corner_angle_1) * radius
            x2 = boss.x + math.cos(corner_angle_2) * radius
            y2 = boss.y + math.sin(corner_angle_2) * radius
            for j in range(projectiles_per_side):
                t = j / projectiles_per_side
                spawn_x = x1 + (x2 - x1) * t
                spawn_y = y1 + (y2 - y1) * t
                outward_angle = math.atan2(spawn_y - boss.y, spawn_x - boss.x)
                vx = math.cos(outward_angle) * speed
                vy = math.sin(outward_angle) * speed
                if j == projectiles_per_side // 2: # Safe gap in the middle
                    continue 
                game.projectile_pool.spawn(x=spawn_x, y=spawn_y, vx=vx, vy=vy, proj_id="void_crystal", color="magenta", status_effect="weakness")
```
