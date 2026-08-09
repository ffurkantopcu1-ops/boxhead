import pygame
import math
import random
from entities.enemy import Enemy
from entities.projectile import Projectile

class CrystalDragon(Enemy):
    def __init__(self, id, x, y, game, wave_level=20):
        super().__init__(id, x, y, game, type="crystal_dragon", wave_level=wave_level)
        self.game, self.wave_level = game, wave_level
        self.max_hp = 150000 * (1.25 ** (wave_level // 10))
        self.hp = self.max_hp
        self.speed = 2.5
        self.radius = 80
        self.dmg = 150
        self.color = (100, 200, 255) # Açık Mavi
        self.xp_reward = 5000
        self.is_boss = True

        self.phase = 1
        self.attack_timer = 2.0
        self.base_speed = self.speed
        # Boss statlari super().__init__ icindeki apply_difficulty'den SONRA
        # yazildigi icin zorluk carpani hic uygulanmiyordu (H4)
        self.apply_difficulty(game.wave.get("current_diff", "Normal"))

    def apply_difficulty(self, diff_name):
        # Enemy.apply_difficulty base_* tabaniyla boss HP'sini eziyordu (H4).
        # __init__ sirasindaki ilk cagri sessizce atlanir.
        if not hasattr(self, 'attack_timer'):
            return
        from entities.boss import get_boss_diff_mults
        hp_mult, dmg_mult = get_boss_diff_mults(self.game)
        ratio = self.hp / self.max_hp if self.max_hp > 0 else 1.0
        self.max_hp = 150000 * (1.25 ** (self.wave_level // 10)) * hp_mult
        self.hp = self.max_hp * ratio
        self.dmg = 150 * dmg_mult

    def update(self, dt, game):
        # Update status effects etc
        super().update(dt, game)
        if self.dead:
            return
            
        if self.hp < self.max_hp * 0.5 and self.phase == 1:
            self.phase = 2
            game.add_event("damage_text", self.x, self.y - 100, value="FAZ 2: KRISTAL LABIRENT!", color=(255, 255, 0), timer=2.0)
            self.create_crystal_maze(game)
            
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            if self.phase == 1:
                self.bullet_hell_attack(game)
                self.attack_timer = 3.0
            else:
                self.bullet_hell_attack(game)
                self.attack_timer = 2.0
                
    def bullet_hell_attack(self, game):
        # Saçılan mermiler (Bullet Hell)
        num_bullets = 12 if self.phase == 1 else 24
        angle_step = math.pi * 2 / num_bullets
        for i in range(num_bullets):
            angle = i * angle_step + random.uniform(-0.1, 0.1)
            vx = math.cos(angle) * 7
            vy = math.sin(angle) * 7
            game.entity_id_counter += 1
            proj = Projectile(game.entity_id_counter, self.x, self.y, vx, vy, self.dmg * 0.5, p_type='fire', aoe=0, lifetime=200, is_hostile=True)
            proj.color = (100, 200, 255) # Mavi ateş
            game.projectiles.append(proj)
            
    def create_crystal_maze(self, game):
        # Oyuncunun etrafına veya bossun etrafına trap tipli minyonlar bırakır (Geçilemez)
        num_crystals = 16
        radius = 300
        p = game.players[game.local_player_id]
        angle_step = math.pi * 2 / num_crystals
        for i in range(num_crystals):
            # Boşluklu labirent bırakmak için bazı açıları atla
            if i % 4 == 0: continue
            
            angle = i * angle_step
            cx = p.x + math.cos(angle) * radius
            cy = p.y + math.sin(angle) * radius
            
            # Kristal duvarlar (is_trap = True, hasar almaz)
            game.entity_id_counter += 1
            crystal = Enemy(game.entity_id_counter, cx, cy, game, type="crystal_wall", wave_level=game.wave.get("level", 20))
            crystal.max_hp = 999999
            crystal.hp = crystal.max_hp
            crystal.speed = 0
            crystal.radius = 30
            crystal.dmg = 0
            crystal.color = (50, 150, 250)
            crystal.is_trap = True
            crystal.is_invulnerable = True
            
            game.enemies.append(crystal)
        
    def draw(self, screen, camera_x, camera_y):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        # Kanatlar
        time_ms = pygame.time.get_ticks()
        wing_offset = math.sin(time_ms * 0.005) * 30
        pygame.draw.polygon(screen, (50, 150, 200), [(draw_x, draw_y), (draw_x - 80, draw_y - 80 + wing_offset), (draw_x - 40, draw_y - 20)])
        pygame.draw.polygon(screen, (50, 150, 200), [(draw_x, draw_y), (draw_x + 80, draw_y - 80 + wing_offset), (draw_x + 40, draw_y - 20)])
        
        # Gövde
        super().draw(screen, camera_x, camera_y)
