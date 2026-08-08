import pygame
import math
import time
import random

class Projectile:
    def __init__(self, id, x, y, vx, vy, dmg, bounce=0, pierce=0, p_type='normal', aoe=0, lifetime=180, is_hostile=False, is_crit=False, is_returning=False):
        self.id = id
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.dmg = dmg
        self.radius = 6
        self.lifetime = lifetime
        self.initial_lifetime = lifetime
        self.dead = False
        self.type = p_type # 'normal', 'bomb', 'fire', 'frost', 'poison'
        self.aoe = aoe
        self.is_hostile = is_hostile
        self.is_crit = is_crit
        self.is_returning = is_returning
        self.has_returned = False
        
        # New: Elemental Components
        self.poison_dps = 0
        self.fire_dmg = 0
        self.frost_dmg = 0
        
        # Renk Belirleme
        if p_type == 'bomb':
            self.color = (46, 204, 113) # Yeşil
        elif p_type == 'fire':
            self.color = (231, 76, 60) # Kırmızı
        elif p_type == 'frost':
            self.color = (52, 152, 219) # Mavi
        elif p_type == 'katana':
            self.color = (255, 255, 255) # Beyaz Parlama
            self.radius = 12 # Biraz daha geniş vuruş alanı
        else:
            self.color = (255, 255, 100) # Standart Sarı
            
        self.bounce = bounce
        self.pierce = pierce
        self.bounce_dmg_mult = bounce_dmg_mult
        self.hit_history = [] 
        self.is_katana = (p_type == 'katana')        
        
    def update(self, dt, game):
        # Bumerang Geri Dönme Mantığı
        if self.is_returning and not self.has_returned and self.lifetime <= self.initial_lifetime / 2:
            self.has_returned = True
            if not self.is_hostile:
                p = game.players[game.local_player_id]
                angle = math.atan2(p.y - self.y, p.x - self.x)
                speed = math.hypot(self.vx, self.vy)
                self.vx = math.cos(angle) * speed
                self.vy = math.sin(angle) * speed
            else:
                self.vx *= -1
                self.vy *= -1
            self.hit_history.clear() # Dönerken aynı hedeflere tekrar vurabilmesi için sıfırla

        if self.is_returning and self.has_returned and not self.is_hostile:
            p = game.players[game.local_player_id]
            dist = math.hypot(p.x - self.x, p.y - self.y)
            if dist < getattr(p, "radius", 15) + 15:
                self.dead = True
                return

        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.lifetime -= dt * 60
        
        # Sınır Kontrolü (Memory Leak Önlemi)
        if self.x < -100 or self.x > 5100 or self.y < -100 or self.y > 5100:
            self.dead = True
            return
        
        if self.lifetime <= 0:
            if self.type == 'bomb':
                self.explode(game)
            self.dead = True
            
        # --- BLACK HOLE LOGIC ---
        if self.type == 'black_hole':
            for e in game.iter_enemies_near(self.x, self.y, self.aoe):
                if not e.dead and not e.is_trap:
                    dx = e.x - self.x
                    dy = e.y - self.y
                    dist_sq = dx * dx + dy * dy
                    if dist_sq < self.aoe * self.aoe:
                        dist = math.sqrt(dist_sq)
                        # Çekim kuvveti (Merkeze doğru)
                        angle = math.atan2(self.y - e.y, self.x - e.x)
                        pull = (1.0 - (dist / self.aoe)) * 5 # Merkeze yaklaştıkça çekim artar
                        e.x += math.cos(angle) * dt * 60 * pull
                        e.y += math.sin(angle) * dt * 60 * pull
                        # Zamanla Hasar (Text spamini engellemek için %5 şansla görsel göster)
                        e.take_damage(self.dmg * dt * 3, game, is_dot=True, from_player=not self.is_hostile)
                        if random.random() < 0.05:
                            game.add_event("damage_text", e.x, e.y - 10, value=int(self.dmg), color=(142, 68, 173), timer=0.3, scale=0.7)
            
            # Görsel Pulsasyon
            if int(time.time() * 10) % 5 == 0:
                game.add_event("explosion", self.x, self.y, radius=self.aoe/2, color=(142, 68, 173), timer=0.1)

        # Düşman Çarpışma Kontrolü (Dost Mermiler için)
        if not self.is_hostile:
            # --- MANYETİK ALAN SAPTIRMASI (Magnetar) ---
            for e in game.iter_enemies_near(self.x, self.y, 400):
                if not e.dead and e.type == "magnetar":
                    dx = e.x - self.x
                    dy = e.y - self.y
                    if dx * dx + dy * dy < e.magnet_radius * e.magnet_radius:
                        if random.random() < 0.30 * dt * 60:  # dt normalize
                            self.vx += random.uniform(-4, 4)
                            self.vy += random.uniform(-4, 4)
                            break

            for e in game.iter_enemies_near(self.x, self.y, 160):
                if not e.dead and e.id not in self.hit_history:
                    dx = e.x - self.x
                    dy = e.y - self.y
                    hit_radius = self.radius + e.radius
                    if dx * dx + dy * dy < hit_radius * hit_radius:
                        self.on_hit(e, game)
                        break
        else:
            # Düşman Mermisi (Archer, Venom Spider vb.) Oyuncuya Çarptı mı?
            p = game.players[game.local_player_id]
            
            # MANYETİK AURA: Mermileri yavaşlat veya saptır
            mag_aura = p.stats.get("magneticAura", 0)
            if mag_aura > 0:
                dist = math.hypot(p.x - self.x, p.y - self.y)
                if dist < 300:
                    self.vx *= 0.95
                    self.vy *= 0.95
                    if random.random() < 0.1:
                        self.vx += random.uniform(-2, 2)
                        self.vy += random.uniform(-2, 2)
                        
            dist = math.hypot(p.x - self.x, p.y - self.y)
            if dist < (self.radius + p.radius):
                # Bloodwalker Kan Emme aktifse mermileri emerek HP'ye dönüştür
                absorb_active = (p.class_name == "bloodwalker" and 
                                 getattr(getattr(p, 'specialization', None), 'blood_absorb_active', False))
                if not absorb_active:
                    p.last_attacker_type = getattr(self, "owner_type", "bilinmeyen"); p.take_damage(self.dmg)
                # absorb_active ise bloodwalker_logic.update() zaten emer
                self.dead = True

    def on_hit(self, enemy, game):
        if self.type == 'bomb':
            self.explode(game)
            self.dead = True
            return
            
        # Apply Elemental Effects (NEW Standardized)
        if self.fire_dmg > 0:
            enemy.apply_dot('fire', self.fire_dmg * 0.5, 4.0)
            # Mini Patlama (AoE Pulse) on hit
            self.explode(game, small=True)
            
        if self.frost_dmg > 0:
            enemy.apply_dot('frost', self.frost_dmg * 0.5, 4.0)
            
        if self.poison_dps > 0:
            enemy.apply_dot('poison', self.poison_dps, 5.0)
        
        # Hasar Uygula
        enemy.take_damage(self.dmg, game, from_player=not self.is_hostile)
        self.hit_history.append(enemy.id)
        
        # Vampir İmparatorluğu (Minion Lifesteal)
        if getattr(self, "is_minion_proj", False) and game and hasattr(game, "players"):
            p = game.players[game.local_player_id]
            ls = p.stats.get("minionLifesteal", 0)
            if ls > 0:
                p.heal(self.dmg * ls)
        
        # Görsel Efekt (Renge göre Damage Text)
        txt_color = self.color
        if self.is_crit: txt_color = (255, 255, 0) # Krit hep sarı kalsın ya da elemental krit?
        game.add_event("damage_text", enemy.x, enemy.y - 20, value=self.dmg, color=txt_color, timer=0.5, is_crit=self.is_crit)
        
        # Bounce / Pierce Mantığı
        if self.bounce > 0:
            next_target = self.find_next_target(game, enemy.id)
            if next_target:
                self.reorient(next_target)
                self.bounce -= 1
                self.lifetime = max(self.lifetime, 40)
            elif self.pierce <= 0:
                self.dead = True
        elif self.pierce > 0:
            self.pierce -= 1
        else:
            self.dead = True

    def explode(self, game, small=False):
        # AOE Yerine BULUT (Cloud) Oluştur
        radius = self.aoe if not small else self.aoe * 0.4
        
        from entities.cloud import Cloud
        new_cloud = Cloud(game.entity_id_counter, self.x, self.y, 
                         radius=radius, 
                         duration=1.3, # Sabitlendi: 1.3 saniye yerde kalır
                         poison_dps=self.poison_dps, 
                         fire_dmg=self.fire_dmg, 
                         frost_dmg=self.frost_dmg)
        # --- AOE HASAR (Özellikle Ateş Patlaması için) ---
        if self.fire_dmg > 0:
            for e in game.iter_enemies_near(self.x, self.y, radius):
                if not e.dead and not e.is_trap:
                    dx = e.x - self.x
                    dy = e.y - self.y
                    if dx * dx + dy * dy < radius * radius:
                        # Patlama anlık hasarı (Ateş Hasarı * 1.5 gibi bir çarpan veya direkt fire_dmg)
                        e.take_damage(self.fire_dmg, game, from_player=not self.is_hostile)
                        # DoT da ekleyelim (Patlamadan etkilenen yanar)
                        e.apply_dot('fire', self.fire_dmg * 0.4, 3.0)

        game.clouds.append(new_cloud)
        game.entity_id_counter += 1
        
        # Ekran Sarsıntısı Tetikle
        game.trigger_shake(15)
        
        # Görsel Patlama Işığı
        game.add_event("explosion", self.x, self.y, radius=self.aoe, color=self.color, timer=0.2)

    def find_next_target(self, game, current_id):
        next_target = None
        min_d = 400
        for other in game.iter_enemies_near(self.x, self.y, min_d):
            if other.id != current_id and not other.dead and not other.is_trap and other.id not in self.hit_history:
                dx = other.x - self.x
                dy = other.y - self.y
                d_sq = dx * dx + dy * dy
                if d_sq < min_d * min_d:
                    min_d = math.sqrt(d_sq)
                    next_target = other
        return next_target

    def reorient(self, target):
        angle = math.atan2(target.y - self.y, target.x - self.x)
        speed = math.hypot(self.vx, self.vy)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def draw(self, screen, camera_x, camera_y):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        if self.type == 'bomb':
            # Bomba Görseli
            pygame.draw.circle(screen, (39, 174, 96), (int(draw_x), int(draw_y)), self.radius + 2)
            pygame.draw.circle(screen, (255, 255, 255), (int(draw_x), int(draw_y)), self.radius + 2, 1)
        elif self.type == 'black_hole':
            # Kara Delik Görseli (Büyük ve Karanlık)
            r = int(self.radius * 3)
            # Dış Halo
            h_r = r + random.randint(2, 6)
            pygame.draw.circle(screen, (142, 68, 173), (int(draw_x), int(draw_y)), h_r)
            # İç Karanlık
            pygame.draw.circle(screen, (20, 20, 30), (int(draw_x), int(draw_y)), r)
            # Parlama/Simge
            pygame.draw.circle(screen, (255, 255, 255), (int(draw_x), int(draw_y)), 2)
        elif self.is_katana:
            # Katana Görseli (X şeklinde hızlı bir effekt)
            import random
            offset = random.randint(-5, 5)
            pygame.draw.line(screen, (255, 255, 255), (draw_x - 15 + offset, draw_y - 15), (draw_x + 15 + offset, draw_y + 15), 3)
            pygame.draw.line(screen, (255, 255, 255), (draw_x + 15, draw_y - 15 + offset), (draw_x - 15, draw_y + 15 + offset), 3)
        else:
            p_color = self.color if not self.is_crit else (255, 255, 0)
            if self.is_hostile:
                # Düşman Mermisi: Elmas/Baklava Şekli (Kırmızı-Turuncu Tonları)
                p_color = (231, 76, 60) # Radikal Kırmızı
                points = [
                    (draw_x, draw_y - self.radius - 2),
                    (draw_x + self.radius + 2, draw_y),
                    (draw_x, draw_y + self.radius + 2),
                    (draw_x - self.radius - 2, draw_y)
                ]
                pygame.draw.polygon(screen, p_color, points)
                pygame.draw.polygon(screen, (255, 255, 255), points, 1) # Beyaz kenarlık
            else:
                # Oyuncu Mermisi: Standart Yuvarlak
                pygame.draw.circle(screen, p_color, (int(draw_x), int(draw_y)), self.radius)
                pygame.draw.circle(screen, (255, 255, 255), (int(draw_x), int(draw_y)), self.radius + 1, 1)
