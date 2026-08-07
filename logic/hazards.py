import pygame
import random
import math

class Hazard:
    def __init__(self, x, y, h_type, duration=10.0):
        self.x = x
        self.y = y
        self.type = h_type # "lightning", "mud", "fire", "ice"
        self.duration = duration
        self.timer = 0
        self.radius = 80
        if h_type == "lightning": self.radius = 40
        
        self.active = True
        self.tick_timer = 0
        
    def update(self, dt, players, enemies, game):
        self.timer += dt
        if self.timer >= self.duration:
            self.active = False
            return
            
        # Etki Alanı Kontrolü
        for target in players:
            dx = target.x - self.x
            dy = target.y - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < self.radius:
                self.apply_effect(target, dt, game, is_enemy=False)
                
        nearby_enemies = (
            game.iter_enemies_near(self.x, self.y, self.radius)
            if getattr(game, 'grid', None) else enemies
        )
        for target in nearby_enemies:
            dx = target.x - self.x
            dy = target.y - self.y
            if dx * dx + dy * dy < self.radius * self.radius:
                self.apply_effect(target, dt, game, is_enemy=True)

    def apply_effect(self, target, dt, game, is_enemy=False):
        if self.type == "mud":
            target.speed_mod = 0.5 # %50 Yavaşlat
        elif self.type == "fire":
            # Saniyede 5 Hasar
            if hasattr(target, 'take_damage'):
                if is_enemy:
                    target.take_damage(5 * dt, game)
                else:
                    target.take_damage(5 * dt)
        elif self.type == "ice":
            target.speed_mod = 0.1 # Neredeyse durdur
        elif self.type == "lightning":
            # Yıldırım anlık çarpar, tick ile yönetilir
            self.tick_timer += dt
            if self.tick_timer >= 1.0:
                if hasattr(target, 'take_damage'):
                    if is_enemy:
                        target.take_damage(20, game)
                    else:
                        target.take_damage(20)
                self.tick_timer = 0

    def draw(self, screen, cam_x, cam_y):
        dx = self.x - cam_x
        dy = self.y - cam_y
        
        # Görsel Efektler (Basit Şekiller)
        if self.type == "mud":
            pygame.draw.circle(screen, (101, 67, 33, 100), (int(dx), int(dy)), self.radius)
        elif self.type == "fire":
            pygame.draw.circle(screen, (231, 76, 60, 150), (int(dx), int(dy)), self.radius)
        elif self.type == "ice":
            pygame.draw.circle(screen, (52, 152, 219, 120), (int(dx), int(dy)), self.radius)
        elif self.type == "lightning":
            if random.random() > 0.5:
                pygame.draw.circle(screen, (241, 196, 15), (int(dx), int(dy)), self.radius)
