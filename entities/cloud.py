import pygame
import math
import random

class Cloud:
    def __init__(self, id, x, y, radius, duration, poison_dps=0, fire_dmg=0, frost_dmg=0, is_black_hole=False):
        self.id = id
        self.x = x
        self.y = y
        self.radius = radius
        self.duration = duration
        self.poison_dps = poison_dps
        self.fire_dmg = fire_dmg
        self.frost_dmg = frost_dmg
        self.dead = False
        
        self.is_black_hole = is_black_hole
        
        # Mixed color based on strength
        # Zehir (Yeşil), Ateş (Kırmızı), Buz (Mavi), Kara Delik (Koyu Mor)
        if self.is_black_hole: self.color = (44, 62, 80)
        elif fire_dmg > poison_dps and fire_dmg > frost_dmg: self.color = (231, 76, 60)
        elif frost_dmg > fire_dmg and frost_dmg > poison_dps: self.color = (52, 152, 219)
        else: self.color = (46, 204, 113)

        diameter = max(2, int(self.radius * 2))
        self._visual = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(
            self._visual, (*self.color, 100),
            (diameter // 2, diameter // 2), int(self.radius),
        )
        pygame.draw.circle(
            self._visual, (*self.color, 50),
            (diameter // 2, diameter // 2), int(self.radius), 10,
        )
            
    def update(self, dt, game):
        self.duration -= dt
        if self.duration <= 0:
            self.dead = True
            return
            
        # Düşmanlara DOT uygula
        for e in game.iter_enemies_near(self.x, self.y, self.radius):
            if not e.dead:
                dx = e.x - self.x
                dy = e.y - self.y
                if dx * dx + dy * dy < self.radius * self.radius:
                    # 1. Zehir Etkisi
                    if self.poison_dps > 0:
                        e.apply_dot('poison', self.poison_dps, 1.5)
                    
                    # 2. Ateş Etkisi
                    if self.fire_dmg > 0:
                        e.apply_dot('fire', self.fire_dmg, 1.5)
                        if random.random() < 0.05: # %5 şansla patlama tick'i
                            game.add_event("explosion", e.x, e.y, radius=40, color=(255, 100, 0), timer=0.15)
                            for other in game.iter_enemies_near(e.x, e.y, 40):
                                if not other.dead and not other.is_trap and other != e:
                                    odx = other.x - e.x
                                    ody = other.y - e.y
                                    if odx * odx + ody * ody < 40 * 40:
                                        other.take_damage(self.fire_dmg * 0.5, game)
                    
                    # 3. Buz Etkisi
                    if self.frost_dmg > 0:
                        e.apply_dot('frost', self.frost_dmg * 0.5, 1.5)

        # Kara Delik Etkisi
        if self.is_black_hole:
            p = game.players[game.local_player_id]
            dist_to_p = math.hypot(p.x - self.x, p.y - self.y)
            if dist_to_p < self.radius:
                # Oyuncuyu merkeze çek
                angle_to_center = math.atan2(self.y - p.y, self.x - p.x)
                pull_strength = 60 * dt
                p.x += math.cos(angle_to_center) * pull_strength
                p.y += math.sin(angle_to_center) * pull_strength
                # Hasar ver
                dmg = getattr(self, 'dmg', 10)
                p.take_damage(dmg * dt, force=True)

        # Oyuncuya Hasar Uygula - DEVRE DIŞI BIRAKILDI (GDD 62)
        # p = game.players[game.local_player_id]
        # if math.hypot(p.x - self.x, p.y - self.y) < self.radius:
        #     if self.fire_dmg > 0:
        #         p.take_damage(self.fire_dmg * dt, force=True)
        #     if self.poison_dps > 0:
        #         p.take_damage(self.poison_dps * dt, force=True)
        #     if self.frost_dmg > 0:
        #         p.take_damage(self.frost_dmg * 0.1 * dt, force=True) # Hafif dondurucu hasar
        #         p.speed_mod = min(p.speed_mod, 0.5) # Yavaşlat

    def draw(self, screen, camera_x, camera_y):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        # Geometri init'te önbelleğe alınır; burada yalnızca solma alfası değişir.
        self._visual.set_alpha(min(255, int(255 * (self.duration / 2.0))))
        screen.blit(self._visual, (draw_x - self.radius, draw_y - self.radius))
