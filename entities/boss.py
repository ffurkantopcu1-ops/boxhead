import pygame
import math
import random
import time
from entities.enemy import Enemy
from entities.projectile_pool import ProjectilePool
from logic.status_effects import StatusEffectManager

def draw_objective_arrow(screen, start_x, start_y, target_x, target_y, color, camera_x, camera_y):
    """Draws a navigation arrow pointing from source to target if target is off-screen."""
    # Screen boundaries
    sw, sh = screen.get_size()
    
    # Target screen position
    tx, ty = target_x - camera_x, target_y - camera_y
    
    # If target is on screen with a margin, don't draw arrow
    margin = 50
    if margin < tx < sw - margin and margin < ty < sh - margin:
        return

    # Calculate direction
    dx, dy = target_x - start_x, target_y - start_y
    angle = math.atan2(dy, dx)
    
    # Draw position (around the player)
    p_sx, p_sy = start_x - camera_x, start_y - camera_y
    dist = 120 # Distance from player
    ax, ay = p_sx + math.cos(angle) * dist, p_sy + math.sin(angle) * dist
    
    # Arrow shape
    points = [
        (ax + math.cos(angle) * 20, ay + math.sin(angle) * 20),
        (ax + math.cos(angle + 2.5) * 15, ay + math.sin(angle + 2.5) * 15),
        (ax + math.cos(angle - 2.5) * 15, ay + math.sin(angle - 2.5) * 15)
    ]
    pygame.draw.polygon(screen, color, points)
    pygame.draw.polygon(screen, (255, 255, 255), points, 2)

class SafeSpot:
    def __init__(self, x, y, radius, lifetime):
        self.x = x
        self.y = y
        self.radius = radius
        self.lifetime = lifetime
        self.timer = lifetime
        self.active = True

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            self.active = False

    def draw(self, screen, camera_x, camera_y):
        draw_x, draw_y = int(self.x - camera_x), int(self.y - camera_y)
        pulse = math.sin(time.time() * 10) * 5
        alpha = 100 + int(pulse * 10)
        s = pygame.Surface((self.radius*2 + 40, self.radius*2 + 40), pygame.SRCALPHA)
        # Glow
        pygame.draw.circle(s, (46, 204, 113, alpha), (self.radius + 20, self.radius + 20), self.radius + pulse)
        # Main Ring
        pygame.draw.circle(s, (255, 255, 255, 200), (self.radius + 20, self.radius + 20), self.radius + pulse, 3)
        screen.blit(s, (draw_x - self.radius - 20, draw_y - self.radius - 20))

class BossPillar(Enemy):
    def __init__(self, id, x, y, game, boss):
        super().__init__(id, x, y, game, type="minion", wave_level=boss.wave_level)
        self.max_hp = 2500 * (1.1 ** boss.wave_level)
        self.hp = self.max_hp
        self.radius = 40
        self.color = (231, 76, 60)
        self.boss = boss
        self.is_pillar = True
        
    def update(self, dt, game): pass

    def draw(self, screen, camera_x, camera_y):
        draw_x, draw_y = int(self.x - camera_x), int(self.y - camera_y)
        pygame.draw.rect(screen, self.color, (draw_x - 20, draw_y - 60, 40, 80))
        pygame.draw.rect(screen, (255, 255, 255), (draw_x - 20, draw_y - 60, 40, 80), 2)
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(screen, (0, 0, 0), (draw_x - 30, draw_y - 80, 60, 8))
        pygame.draw.rect(screen, (46, 204, 113), (draw_x - 30, draw_y - 80, 60 * hp_ratio, 8))

class BossPhase:
    def __init__(self, name, duration=0, invulnerable=False):
        self.name = name
        self.duration = duration
        self.timer = duration
        self.invulnerable = invulnerable

    def enter(self, boss):
        self.timer = self.duration
        boss.invulnerable = self.invulnerable

    def update(self, dt, boss, game):
        if self.duration > 0:
            self.timer -= dt
            if self.timer <= 0: boss.next_phase()

    def exit(self, boss): pass
    def draw(self, screen, camera_x, camera_y, boss): pass

class LabyrinthOfFire(BossPhase):
    def __init__(self, duration=0):
        super().__init__("Labyrinth of Fire", duration, invulnerable=True)
        self.attack_timer = 0
        self.pillars = []
        self.pattern_type = 0
        self.sweeper_count = 0

    def enter(self, boss):
        super().enter(boss)
        game = boss.game
        # SABİT PİLLAR KONUMLARI (Merkeze yakın, kare şeklinde)
        dist = 350
        arena_cx, arena_cy = 2500, 2500
        positions = [
            (arena_cx - dist, arena_cy - dist),
            (arena_cx + dist, arena_cy - dist),
            (arena_cx - dist, arena_cy + dist),
            (arena_cx + dist, arena_cy + dist)
        ]
        self.pillars = []
        for px, py in positions:
            pillar = BossPillar(game.entity_id_counter, px, py, game, boss)
            game.enemies.append(pillar)
            game.entity_id_counter += 1
            self.pillars.append(pillar)

    def update(self, dt, boss, game):
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            # Sweeper (Spiral) paternini faz başına 2 ile sınırla
            options = [0, 1]
            if self.sweeper_count < 2: options.append(2)
            
            self.pattern_type = random.choice(options)
            if self.pattern_type == 2: self.sweeper_count += 1
            
            # Pattern arası süre: Wave 10'da ~3.75s (Daha insaflı)
            self.attack_timer = max(1.5, 4.0 - (boss.wave_level / 40.0))
        current_time = time.time()
        if self.pattern_type == 0: self.fire_labyrinth_wall(boss, game, current_time)
        elif self.pattern_type == 1: self.breathing_fire_ring(boss, game, current_time)
        elif self.pattern_type == 2: self.fire_sweeper(boss, game, current_time)
        
        self.pillars = [p for p in self.pillars if not p.dead]
        boss.invulnerable = len(self.pillars) > 0

    def draw(self, screen, camera_x, camera_y, boss):
        p = boss.game.players[boss.game.local_player_id]
        for pillar in self.pillars:
            draw_objective_arrow(screen, p.x, p.y, pillar.x, pillar.y, (231, 76, 60), camera_x, camera_y)

    def fire_labyrinth_wall(self, boss, game, current_time):
        if int(current_time * 3) % 10 != 0: return
        num_projectiles = 10
        gap_index = random.randint(2, num_projectiles - 3)
        p = game.players[game.local_player_id]
        direction_angle = math.atan2(p.y - boss.y, p.x - boss.x)
        wall_normal = direction_angle + (math.pi / 2) 
        # Hız Ölçeklendirmesi
        speed = 2.5 + (boss.wave_level / 20.0)
        vx, vy = math.cos(direction_angle) * speed, math.sin(direction_angle) * speed
        spacing = 60 
        start_x = boss.x - math.cos(wall_normal) * (num_projectiles * spacing / 2)
        start_y = boss.y - math.sin(wall_normal) * (num_projectiles * spacing / 2)
        for i in range(num_projectiles):
            if gap_index <= i <= gap_index + 2: continue
            sx, sy = start_x + math.cos(wall_normal) * (i * spacing), start_y + math.sin(wall_normal) * (i * spacing)
            game.projectile_pool.spawn(sx, sy, vx, vy, damage=30, color=(231, 76, 60), status_effect="burn", lifetime=400)

    def breathing_fire_ring(self, boss, game, current_time):
        if int(current_time * 8) % 2 != 0: return
        num_projectiles = 12
        # Döngüsel boşluk (Her halkada bir açıklık bırak)
        gap_center = int((current_time * 4) % num_projectiles)
        final_speed = 3.5 + math.sin(current_time * 2.5) * 2.0
        for i in range(num_projectiles):
            # 3 mermilik bir boşluk bırak (Geçiş alanı)
            if gap_center <= i <= (gap_center + 2): continue
            angle = (current_time * 0.5) + (i / num_projectiles) * 2 * math.pi
            vx, vy = math.cos(angle) * final_speed, math.sin(angle) * final_speed
            game.projectile_pool.spawn(boss.x, boss.y, vx, vy, damage=30, color=(231, 76, 60), status_effect="burn", lifetime=400)

    def fire_sweeper(self, boss, game, current_time):
        # Sweeper paternine kesiklik ekle (Sürekli tarama yerine kesik kesik tarama)
        if current_time % 4.0 < 1.0: return
        if int(current_time * 20) % 4 == 0: return # Her 4 atıştan birini boş geç
        
        # HIZ AZALTILDI: Oyuncunun çevresinde dönebilmesi için mermiler aşırı yavaşlatıldı
        speed = 2.5 
        for offset in [0, 0.15]: 
            # Dönüş hızı da yavaşlatıldı
            angle = current_time * 1.0 + offset
            vx, vy = math.cos(angle) * speed, math.sin(angle) * speed
            game.projectile_pool.spawn(boss.x, boss.y, vx, vy, damage=30, color=(150, 40, 40), status_effect="burn", lifetime=600)

class StaticSilence(BossPhase):
    def __init__(self):
        super().__init__("Static Silence", duration=0, invulnerable=False)
        self.state = "SEARCHING"
        self.timer = 4.5
        self.cycle_count = 0
        self.safe_spots = []
        self.shot_timer = 0

    def enter(self, boss):
        super().enter(boss)
        boss.x, boss.y = 2500, 2500
        self.cycle_count = 0
        self.start_cycle(boss.game)

    def start_cycle(self, game):
        self.state = "SEARCHING"
        self.timer = 4.5
        self.safe_spots = []
        p = game.players[game.local_player_id]
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(300, 500)
        sx, sy = p.x + math.cos(angle) * dist, p.y + math.sin(angle) * dist
        sx = max(200, min(4800, sx))
        sy = max(200, min(4800, sy))
        self.safe_spots.append(SafeSpot(sx, sy, 90, 10.0))

    def update(self, dt, boss, game):
        self.timer -= dt
        p = game.players[game.local_player_id]
        from logic.status_effects import apply_silence
        apply_silence(p.effect_manager, duration=0.2)
        self.shot_timer -= dt
        if self.shot_timer <= 0:
            angle = math.atan2(p.y - boss.y, p.x - boss.x)
            for off in [-0.1, 0.1]:
                vx, vy = math.cos(angle + off) * 4.5, math.sin(angle + off) * 4.5
                game.projectile_pool.spawn(boss.x, boss.y, vx, vy, damage=20, color=(52, 152, 219), lifetime=600)
            self.shot_timer = 1.0
        if self.state == "SEARCHING":
            if self.timer <= 0:
                self.state = "STAYING"
                self.timer = 3.5
        else:
            if self.timer <= 0:
                self.cycle_count += 1
                if self.cycle_count >= 4:
                    boss.next_phase()
                    return
                self.start_cycle(game)
        if self.state == "STAYING":
            in_spot = any(math.hypot(p.x - ss.x, p.y - ss.y) < ss.radius for ss in self.safe_spots)
            if not in_spot:
                p.take_damage(15 * dt * 60)
                if int(time.time() * 10) % 2 == 0:
                    game.add_event("damage_text", p.x, p.y-20, value="OUT OF SAFE ZONE!", color=(231, 76, 60), scale=0.6)

    def draw(self, screen, camera_x, camera_y, boss):
        p = boss.game.players[boss.game.local_player_id]
        for ss in self.safe_spots:
            ss.draw(screen, camera_x, camera_y)
            if self.state == "SEARCHING":
                draw_objective_arrow(screen, p.x, p.y, ss.x, ss.y, (46, 204, 113), camera_x, camera_y)
        txt_color = (46, 204, 113) if self.state == "SEARCHING" else (231, 76, 60)
        label = "FIND SAFE ZONE!" if self.state == "SEARCHING" else "STAY INSIDE!"
        font = pygame.font.SysFont("Arial", 32, bold=True)
        surf = font.render(f"{label} {max(0, self.timer):.1f}s", True, txt_color)
        screen.blit(surf, (screen.get_width()//2 - surf.get_width()//2, 180))

class OrbitalChaos(BossPhase):
    def __init__(self):
        super().__init__("Orbital Chaos", duration=0, invulnerable=False)
        self.attack_timer, self.pattern_type = 0, 0

    def update(self, dt, boss, game):
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            self.pattern_type, self.attack_timer = random.randint(0, 2), 1.5
        current_time = time.time()
        if self.pattern_type == 0: self.void_flower_split(boss, game, current_time)
        elif self.pattern_type == 1: self.orbital_singularity(boss, game, current_time)
        elif self.pattern_type == 2: self.geometric_pulse(boss, game, current_time)

    def void_flower_split(self, boss, game, current_time):
        if int(current_time * 4) % 2 != 0: return
        num_petals, speed = 8, 4.5
        for i in range(num_petals):
            angle = math.sin(current_time * 2) + (i / num_petals) * 2 * math.pi
            vx, vy = math.cos(angle) * speed, math.sin(angle) * speed
            game.projectile_pool.spawn_ext(boss.x, boss.y, vx, vy, damage=0, color=(155, 89, 182), lifetime=600, status_effect="silence", behavior="split_on_timer", timer=1.0)

    def orbital_singularity(self, boss, game, current_time):
        num_arms, speed = 4, 6.0
        base_angle = current_time * 3.0
        wobble = math.sin(current_time * 3.0) * 0.4 
        for i in range(num_arms):
            angle = base_angle + wobble + (i / num_arms) * 2 * math.pi
            vx, vy = math.cos(angle) * speed, math.sin(angle) * speed
            game.projectile_pool.spawn(boss.x, boss.y, vx, vy, damage=0, color=(100, 30, 150), status_effect="silence", lifetime=800)

    def geometric_pulse(self, boss, game, current_time):
        if int(current_time * 4) % 3 != 0: return
        sides, speed, radius = 6, 4.5, 30
        for i in range(sides):
            corner_angle_1, corner_angle_2 = (i / sides) * 2 * math.pi, ((i + 1) / sides) * 2 * math.pi
            x1, y1 = boss.x + math.cos(corner_angle_1) * radius, boss.y + math.sin(corner_angle_1) * radius
            x2, y2 = boss.x + math.cos(corner_angle_2) * radius, boss.y + math.sin(corner_angle_2) * radius
            for j in range(4):
                t = j / 4
                sx, sy = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
                outward_angle = math.atan2(sy - boss.y, sx - boss.x)
                vx, vy = math.cos(outward_angle) * speed, math.sin(outward_angle) * speed
                game.projectile_pool.spawn(sx, sy, vx, vy, damage=25, color=(255, 0, 255), lifetime=800)

class AbyssalLord(Enemy):
    def __init__(self, id, x, y, game, wave_level=10):
        super().__init__(id, x, y, game, type="boss", wave_level=wave_level)
        self.game, self.wave_level = game, wave_level
        # BOSS HP NERF: Wave 10'da ~20-25k can olacak şekilde ayarlandı (Eski: 300k+)
        self.max_hp = 5000 * (1.15 ** wave_level)
        self.hp, self.radius = self.max_hp, 80
        self.color, self.invulnerable = (44, 62, 80), False
        self.effect_manager = StatusEffectManager()
        self.phase_pool = [LabyrinthOfFire(), StaticSilence(), OrbitalChaos()]
        self.phase_sequence = [0, 1, 2, 0, 1, 2, 0, 1, 2]
        self.phase_thresholds = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
        self.current_seq_idx = 0
        self.current_phase = self.phase_pool[self.phase_sequence[self.current_seq_idx]]
        self.current_phase.enter(self)

    def next_phase(self):
        self.current_phase.exit(self)
        self.current_seq_idx += 1
        if self.current_seq_idx < len(self.phase_sequence):
            self.current_phase = self.phase_pool[self.phase_sequence[self.current_seq_idx]]
            self.current_phase.enter(self)
        else:
            print("Boss Enraged!")

    def update(self, dt, game):
        if self.dead: return
        hp_percent = self.hp / self.max_hp
        if self.current_seq_idx < len(self.phase_thresholds):
            if hp_percent < self.phase_thresholds[self.current_seq_idx]:
                self.next_phase()
        self.current_phase.update(dt, self, game)
        self.effect_manager.update(dt, self, game)
        if not isinstance(self.current_phase, StaticSilence):
            p = game.players[game.local_player_id]
            angle, dist = math.atan2(p.y - self.y, p.x - self.x), math.hypot(p.x - self.x, p.y - self.y)
            if dist > 300:
                self.x += math.cos(angle) * self.speed * dt * 30
                self.y += math.sin(angle) * self.speed * dt * 30
                
        # Sınır dışına çıkmayı engelle (Map Boundaries)
        self.x = max(50, min(4950, self.x))
        self.y = max(50, min(4950, self.y))

    def take_damage(self, amount, game, is_crit=False, is_dot=False, from_player=False):
        if self.invulnerable:
            game.add_event("damage_text", self.x, self.y - 40, value="IMMUNE!", color=(200, 200, 255), scale=0.8)
            return
        super().take_damage(amount, game, is_crit, is_dot)

    def draw(self, screen, camera_x, camera_y):
        draw_x, draw_y = int(self.x - camera_x), int(self.y - camera_y)
        if hasattr(self.current_phase, 'draw'): self.current_phase.draw(screen, camera_x, camera_y, self)
        if self.invulnerable:
            pulse = math.sin(time.time() * 10) * 5
            s = pygame.Surface((self.radius*3, self.radius*3), pygame.SRCALPHA)
            pygame.draw.circle(s, (100, 200, 255, 60), (self.radius*1.5, self.radius*1.5), self.radius + 15 + pulse)
            pygame.draw.circle(s, (255, 255, 255, 150), (self.radius*1.5, self.radius*1.5), self.radius + 15 + pulse, 3)
            screen.blit(s, (draw_x - self.radius*1.5, draw_y - self.radius*1.5))
        super().draw(screen, camera_x, camera_y)
        try:
            name_font = pygame.font.SysFont("Arial", 28, bold=True)
            name_txt = name_font.render("EchelionFinrod", True, (255, 215, 0))
            screen.blit(name_txt, (draw_x - name_txt.get_width()//2, draw_y - self.radius - 75))
            hp_ratio = max(0, self.hp / self.max_hp)
            bar_w, bar_h = 240, 20
            bx, by = draw_x - bar_w // 2, draw_y - self.radius - 40
            pygame.draw.rect(screen, (30, 30, 30), (bx, by, bar_w, bar_h), border_radius=3)
            color = (231, 76, 60) if hp_ratio > 0.25 else (192, 57, 43)
            pygame.draw.rect(screen, color, (bx, by, int(bar_w * hp_ratio), bar_h), border_radius=3)
            pygame.draw.rect(screen, (255, 255, 255), (bx, by, bar_w, bar_h), 2, border_radius=3)
            hp_font = pygame.font.SysFont("Arial", 16, bold=True)
            hp_str = f"{int(self.hp):,} / {int(self.max_hp):,}"
            hp_txt = hp_font.render(hp_str, True, (255, 255, 255))
            screen.blit(hp_txt, (draw_x - hp_txt.get_width()//2, by + 1))
            
            # 4. Phase Name
            phase_font = pygame.font.SysFont("Arial", 22, bold=True)
            phase_txt = phase_font.render(f"PHASE: {self.current_phase.name}", True, (255, 255, 255))
            screen.blit(phase_txt, (draw_x - phase_txt.get_width()//2, draw_y + self.radius + 15))
        except: pass
