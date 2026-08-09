import pygame
import math
import random

class BossProjectile:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.vx = 0
        self.vy = 0
        self.damage = 0
        self.radius = 6
        self.color = (255, 255, 255)
        self.active = False
        self.lifetime = 0
        self.status_effect = None
        self.type = 'normal'
        self.angle = 0
        self.speed = 0
        self.behavior = None
        self.behavior_timer = 0

    def reset(self, x, y, vx, vy, damage, radius=6, color=(255, 255, 255), lifetime=300, status_effect=None):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.radius = radius
        self.color = color
        self.lifetime = lifetime
        self.active = True
        self.status_effect = status_effect
        self.speed = math.hypot(vx, vy)
        self.behavior = None
        self.behavior_timer = 0

    def reset_ext(self, x, y, vx, vy, damage, radius=6, color=(255, 255, 255), lifetime=300, status_effect=None, behavior=None, timer=0):
        self.reset(x, y, vx, vy, damage, radius, color, lifetime, status_effect)
        self.behavior = behavior
        self.behavior_timer = timer

    def update(self, dt, game):
        if not self.active: return
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.lifetime -= dt * 60
        
        # Sınır Kontrolü (Memory Leak Önlemi)
        if self.x < -200 or self.x > 5200 or self.y < -200 or self.y > 5200:
            self.active = False
            return
            
        if self.lifetime <= 0:
            self.active = False
            return
        if self.behavior == "split_on_timer":
            self.behavior_timer -= dt
            if self.behavior_timer <= 0:
                self.active = False
                for i in range(4):
                    angle = (i / 4) * math.pi * 2
                    vx = math.cos(angle) * 4
                    vy = math.sin(angle) * 4
                    game.projectile_pool.spawn(self.x, self.y, vx, vy, damage=self.damage//2, color=self.color, lifetime=200)
                return
        p = game.players[game.local_player_id]
        dist_sq = (self.x - p.x)**2 + (self.y - p.y)**2
        if dist_sq < (self.radius + p.radius)**2:
            self.on_hit_player(p, game)

    def on_hit_player(self, player, game):
        player.take_damage(self.damage)
        if self.status_effect:
            from logic.status_effects import apply_burn, apply_slow, apply_silence, apply_stun
            if self.status_effect == "burn": apply_burn(player.effect_manager)
            elif self.status_effect == "slow": apply_slow(player.effect_manager)
            elif self.status_effect == "silence": apply_silence(player.effect_manager)
            elif self.status_effect == "stun": apply_stun(player.effect_manager)
        self.active = False

    def draw(self, screen, camera_x, camera_y):
        if not self.active: return
        draw_x = int(self.x - camera_x)
        draw_y = int(self.y - camera_y)
        # Dolu gövde + KALIN koyu kontur + parlak çekirdek. İnce 1px beyaz halka
        # dünya yüzeyi NEAREST ölçeklenirken piksel düşmesiyle "blink" ediyordu;
        # kalın dolu şekil ölçeklemede kaybolmaz.
        r = self.radius + 1
        pygame.draw.circle(screen, (18, 10, 12), (draw_x, draw_y), r + 1)     # koyu kontur
        pygame.draw.circle(screen, self.color, (draw_x, draw_y), r)           # gövde
        pygame.draw.circle(screen, (255, 240, 220), (draw_x, draw_y), max(2, r // 3))  # çekirdek

class ProjectilePool:
    def __init__(self, size=2000):
        self.pool = [BossProjectile() for _ in range(size)]
        self.active_objects = []
        self.size = size
        self.ptr = 0

    def spawn(self, x, y, vx, vy, damage, radius=6, color=(255, 255, 255), lifetime=300, status_effect=None):
        for _ in range(self.size):
            obj = self.pool[self.ptr]
            self.ptr = (self.ptr + 1) % self.size
            if not obj.active:
                obj.reset(x, y, vx, vy, damage, radius, color, lifetime, status_effect)
                if obj not in self.active_objects:
                    self.active_objects.append(obj)
                return obj
        return None

    def spawn_ext(self, x, y, vx, vy, damage, radius=6, color=(255, 255, 255), lifetime=300, status_effect=None, behavior=None, timer=0):
        for _ in range(self.size):
            obj = self.pool[self.ptr]
            self.ptr = (self.ptr + 1) % self.size
            if not obj.active:
                obj.reset_ext(x, y, vx, vy, damage, radius, color, lifetime, status_effect, behavior, timer)
                if obj not in self.active_objects:
                    self.active_objects.append(obj)
                return obj
        return None

    def update(self, dt, game):
        # Split davranışı update sırasında yeni mermi ekleyebilir; snapshot kullan.
        for obj in tuple(self.active_objects):
            if obj.active:
                obj.update(dt, game)
        self.active_objects = [obj for obj in self.active_objects if obj.active]

    def draw(self, screen, camera_x, camera_y):
        width, height = screen.get_size()
        for obj in self.active_objects:
            draw_x = obj.x - camera_x
            draw_y = obj.y - camera_y
            if -30 <= draw_x <= width + 30 and -30 <= draw_y <= height + 30:
                obj.draw(screen, camera_x, camera_y)
                
    def clear(self):
        for obj in self.active_objects:
            obj.active = False
        self.active_objects.clear()
