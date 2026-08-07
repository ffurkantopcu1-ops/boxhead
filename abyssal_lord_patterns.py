import math
import random
import time

class AbyssalLordPatterns:
    """
    Bullet Hell Projectile Patterns for the Abyssal Lord Boss.
    Designed for high-performance Pygame object pooling.
    All patterns use math.sin/math.cos and time.time() for dynamic vectors.
    """

    # ==========================================
    # FIRE PATTERNS (Red, Burn, Maze/Static based)
    # ==========================================

    @staticmethod
    def fire_labyrinth_wall(boss, game, current_time):
        """
        Pattern 1: Labyrinth Wall
        Fires a wide horizontal or vertical wall of slow-moving fire projectiles.
        Always leaves a clear 'safe gap' for the player to slip through.
        """
        num_projectiles = 15
        gap_index = random.randint(2, num_projectiles - 4) # Random gap position
        gap_width = 3 # 3 projectiles wide safe window
        
        # Target player direction, but align the wall perpendicular to it
        direction_angle = math.atan2(game.player.y - boss.y, game.player.x - boss.x)
        wall_normal = direction_angle + (math.pi / 2) 
        
        speed = 80
        vx = math.cos(direction_angle) * speed
        vy = math.sin(direction_angle) * speed
        
        spacing = 40 # Pixels between projectiles
        start_x = boss.x - math.cos(wall_normal) * (num_projectiles * spacing / 2)
        start_y = boss.y - math.sin(wall_normal) * (num_projectiles * spacing / 2)

        for i in range(num_projectiles):
            if gap_index <= i <= gap_index + gap_width:
                continue # This creates the Safe Window
            
            spawn_x = start_x + math.cos(wall_normal) * (i * spacing)
            spawn_y = start_y + math.sin(wall_normal) * (i * spacing)
            
            game.projectile_pool.spawn(
                x=spawn_x, y=spawn_y, 
                vx=vx, vy=vy, 
                proj_id="fire_orb", color="red", status_effect="burn"
            )

    @staticmethod
    def breathing_fire_ring(boss, game, current_time):
        """
        Pattern 2: Breathing Fire Ring
        Fires a 360-degree ring of fire. The speed of the ring varies based on a sine wave,
        creating "waves" of fire that bunch up and spread out.
        Safe Gap: The space between the slow-moving and fast-moving waves.
        """
        num_projectiles = 24
        base_speed = 120
        # Speed oscillates between 40 and 200 based on time
        speed_modifier = math.sin(current_time * 2.5) * 80 
        final_speed = base_speed + speed_modifier
        
        # Add a slight rotation to the ring over time
        angle_offset = current_time * 0.5

        for i in range(num_projectiles):
            angle = angle_offset + (i / num_projectiles) * 2 * math.pi
            vx = math.cos(angle) * final_speed
            vy = math.sin(angle) * final_speed
            
            game.projectile_pool.spawn(
                x=boss.x, y=boss.y, 
                vx=vx, vy=vy, 
                proj_id="fire_orb", color="red", status_effect="burn"
            )

    @staticmethod
    def fire_sweeper(boss, game, current_time):
        """
        Pattern 3: Fire Sweeper (Rotating Laser)
        Shoots a continuous line of fire that sweeps in a circle. 
        It deliberately pauses firing every few seconds to create a dodgeable window.
        Safe Gap: The 1-second pause window in the rotation.
        """
        # Stop firing for 1 second every 4 seconds to create a safe gap
        if current_time % 4.0 < 1.0:
            return 
            
        # Fast rotation
        sweep_angle = current_time * 3.0 
        speed = 250
        
        # Fire 3 projectiles in a tight line to form a thick laser
        for offset in [0, 0.1, 0.2]: 
            angle = sweep_angle + offset
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            game.projectile_pool.spawn(
                x=boss.x, y=boss.y, 
                vx=vx, vy=vy, 
                proj_id="fire_orb", color="dark_red", status_effect="burn"
            )


    # ==========================================
    # VOID PATTERNS (Purple, Orbital/Dynamic based)
    # ==========================================

    @staticmethod
    def void_flower_split(boss, game, current_time):
        """
        Pattern 4: Void Flower
        Fires a ring of projectiles that travel outward. 
        Safe Gap: Timing the split and standing between the secondary bullets.
        *Note: The projectile_pool update logic must handle 'behavior="split_on_timer"'
        """
        num_petals = 8
        speed = 150
        angle_offset = math.sin(current_time) # Wobbly spawn angle
        
        for i in range(num_petals):
            angle = angle_offset + (i / num_petals) * 2 * math.pi
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            # Spawn a special "seed" projectile that splits later
            game.projectile_pool.spawn(
                x=boss.x, y=boss.y, 
                vx=vx, vy=vy, 
                proj_id="void_seed", color="purple", status_effect="silence",
                behavior="split_on_timer", timer=1.5 # Custom kwargs for pool logic
            )

    @staticmethod
    def orbital_singularity(boss, game, current_time):
        """
        Pattern 5: Orbital Singularity (Wobbly Spirals)
        Shoots spiral arms of void energy. The angle of the arms wobbles using sine waves.
        Safe Gap: Weaving through the expanding organic tentacles.
        """
        num_arms = 4
        speed = 180
        
        # Base rotation + sine wave wobble
        base_angle = current_time * 2.0
        wobble = math.sin(current_time * 5.0) * 0.5 
        
        for i in range(num_arms):
            angle = base_angle + wobble + (i / num_arms) * 2 * math.pi
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            game.projectile_pool.spawn(
                x=boss.x, y=boss.y, 
                vx=vx, vy=vy, 
                proj_id="void_tear", color="dark_purple", status_effect="silence"
            )

    @staticmethod
    def geometric_pulse(boss, game, current_time):
        """
        Pattern 6: Geometric Pulse (Hexagon)
        Fires a shape (Hexagon) of projectiles. 
        Safe Gap: The intentional gaps left at the exact midpoint of each hexagon edge.
        """
        sides = 6
        projectiles_per_side = 5
        speed = 100
        radius = 20 # Start slightly away from boss center
        
        # The hexagon rotates slowly
        rotation = current_time * 0.5
        
        for i in range(sides):
            # Calculate the corners of the hexagon
            corner_angle_1 = rotation + (i / sides) * 2 * math.pi
            corner_angle_2 = rotation + ((i + 1) / sides) * 2 * math.pi
            
            x1 = boss.x + math.cos(corner_angle_1) * radius
            y1 = boss.y + math.sin(corner_angle_1) * radius
            x2 = boss.x + math.cos(corner_angle_2) * radius
            y2 = boss.y + math.sin(corner_angle_2) * radius
            
            for j in range(projectiles_per_side):
                # Interpolate between corners to form a line of projectiles
                t = j / projectiles_per_side
                spawn_x = x1 + (x2 - x1) * t
                spawn_y = y1 + (y2 - y1) * t
                
                # Direction is outward from center
                outward_angle = math.atan2(spawn_y - boss.y, spawn_x - boss.x)
                vx = math.cos(outward_angle) * speed
                vy = math.sin(outward_angle) * speed
                
                # Leave a gap in the exact middle of the side
                if j == projectiles_per_side // 2:
                    continue 
                
                game.projectile_pool.spawn(
                    x=spawn_x, y=spawn_y, 
                    vx=vx, vy=vy, 
                    proj_id="void_crystal", color="magenta", status_effect="weakness"
                )
