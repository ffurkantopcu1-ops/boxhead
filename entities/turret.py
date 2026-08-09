import pygame
import math
import time

class Turret:
    def __init__(self, id, x, y, hp=150, dmg_mult=1.0, fire_rate=1.0, local_stats=None, owner=None):
        self.id = id
        self.owner = owner
        self.x = x
        self.y = y
        self.max_hp = hp
        self.hp = hp
        self.dmg_mult = dmg_mult
        self.fire_rate = fire_rate
        self.local_stats = local_stats if local_stats else {}
        self.radius = 20
        self.fire_timer = 0
        
        # Menzili owner statından al
        base_range = 500
        owner_range_bonus = getattr(self.owner, "stats", {}).get("turretRange", 0) if self.owner else 0
        self.range = base_range * (1 + owner_range_bonus)
        
        self.dead = False
        self.color = (52, 73, 94) # Koyu gri/mavi taret rengi
        self.armor = 20
        self.invulnerable_timer = 0
        
    def update(self, dt, game):
        self.fire_timer += dt
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= dt
        
        # Atış hızı kontrolü (Yaklaşık 0.25 saniyede bir JS'deki gibi - 2 kat hızlandırıldı)
        cooldown = 0.25 / max(0.1, self.fire_rate)
        if self.fire_timer >= cooldown:
            self.fire_timer = 0
            self.shoot(game)
            
        # Düşmanların tarete hasar vermesi (Basit çarpışma)
        if self.invulnerable_timer <= 0:
            for e in game.enemies:
                if not e.dead:
                    d = math.hypot(e.x - self.x, e.y - self.y)
                    if d < self.radius + e.radius:
                        # Düşman öldürücü ama taret de hasar alır
                        actual_dmg = max(1, e.dmg - self.armor)
                        self.hp -= actual_dmg
                        self.invulnerable_timer = 0.5
                        break
                    
        if self.hp <= 0:
            self.dead = True

    def shoot(self, game):
        # En yakın düşmanı bul
        target = None
        min_d = self.range
        for e in game.enemies:
            if not e.dead and not e.is_trap:
                d = math.hypot(e.x - self.x, e.y - self.y)
                if d < min_d:
                    min_d = d
                    target = e
                    
        if target:
            # Mermiyi hedefe fırlat
            angle = math.atan2(target.y - self.y, target.x - self.x)
            
            # --- LOCAL STATS VE GLOBAL STATS BİRLEŞİMİ ---
            owner_stats = getattr(self.owner, "stats", {}) if self.owner else {}
            # Taret kitinin kendi statı hem local'de hem de global toplamda yer
            # alıyor (+ global'in tabanı 1). Çift sayımı önlemek için global'den
            # taban ve kitin kendi katkısı düşülür; kalan diğer kaynaklardır (H9)
            local_count = int(self.local_stats.get("projectileCount", 0))
            count = max(1, local_count) + max(0, int(owner_stats.get("projectileCount", 1)) - 1 - local_count)
            local_bounce = int(self.local_stats.get("bounce", 0))
            bounce = local_bounce + max(0, int(owner_stats.get("bounce", 0)) - local_bounce)
            pierce = int(self.local_stats.get("pierce", 0))
            # Denge: Taret hasarı sahibin silah gücüyle (physDmg) ölçeklenir; geç oyunda geride kalmaz
            owner_phys = owner_stats.get("physDmg", 0) + owner_stats.get("physDmgFlat", 0)
            dmg = (12 + owner_phys * 0.4) * self.dmg_mult * (1 + self.local_stats.get("dmgMult", 0))
            
            # IMPOSSIBLE ZORLUK CEZASI (%50 Hasar Kaybı)
            if game.wave.get("current_diff") == "Impossible":
                dmg *= 0.5
            
            # Çoklu Atış (Spread)
            spread = 0.2
            start_angle = angle - (spread * (count - 1) / 2)
            
            from entities.projectile import Projectile
            for i in range(count):
                p_angle = start_angle + (i * spread)
                vx = math.cos(p_angle) * 12
                vy = math.sin(p_angle) * 12
                
                game.projectiles.append(Projectile(game.entity_id_counter, self.x, self.y, vx, vy, dmg, bounce, pierce))
                game.entity_id_counter += 1

    def draw(self, screen, camera_x, camera_y):
        dx = self.x - camera_x
        dy = self.y - camera_y
        
        # Taret Gövdesi (Kare)
        pygame.draw.rect(screen, self.color, (dx - 15, dy - 15, 30, 30), border_radius=3)
        pygame.draw.rect(screen, (255, 255, 255), (dx - 15, dy - 15, 30, 30), border_radius=3, width=1)
        
        # Namlu (Dönen) - Şimdilik merkeze küçük bir yuvarlak
        pygame.draw.circle(screen, (44, 62, 80), (int(dx), int(dy)), 8)
        
        # Can Barı (ortak dünya barı: renkler paletten)
        import ui_theme
        ui_theme.draw_world_bar(
            screen, pygame.Rect(int(dx - 15), int(dy - 25), 30, 4),
            self.hp / max(1, self.max_hp), "moss")
