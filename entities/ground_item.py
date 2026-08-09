import pygame
import math
from ui_elements import ImageLoader

class GroundItem:
    def __init__(self, id, x, y, item_data):
        self.id = id
        self.x = x
        self.y = y
        self.item_data = item_data # ItemSystem'den gelen dict
        self.type = item_data.get('type', 'weapon')
        self.is_gold = self.type == 'gold'
        self.radius = 12 if self.is_gold else 16
        self.dead = False
        self.age = 0.0
        self.max_lifetime = 60.0 if self.is_gold else (90.0 if self.type == 'potion' else None)
        # Günlük görev sayacı eşya başına bir kez işlensin (G1)
        self._quest_tracked = False
        
        # Nadirliğe göre renk belirle (Altın ise her zaman Sarı/Gold)
        self.colors = {
            "Normal": (255, 255, 255),
            "Magic": (52, 152, 219),
            "Rare": (241, 196, 15),
            "Unique": (231, 76, 60),
            "Gold": (241, 196, 15) # Altın Sikke Rengi
        }
        
        if self.is_gold:
            self.color = self.colors["Gold"]
        elif self.type == 'potion':
            self.color = (231, 76, 60) # Kırmızı
        else:
            self.color = self.colors.get(item_data.get('rarity', 'Normal'), (255, 255, 255))
        
        # Animasyon (Yüzme efekti)
        self.offset_y = 0
        self.time_passed = 0

        glow_size = self.radius * 4
        self._glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        alpha = 100 if item_data.get('rarity') == "Normal" else 150
        pygame.draw.circle(
            self._glow_surface, (*self.color, alpha),
            (glow_size // 2, glow_size // 2), glow_size // 2,
        )

    def slice_icons(self, sheet):
        return {}

    def update(self, dt, game):
        self.age += dt
        if self.max_lifetime is not None and self.age >= self.max_lifetime:
            self.dead = True
            return
        self.time_passed += dt * 5
        self.offset_y = math.sin(self.time_passed) * 6
        
        # Oyuncu ile etkileşim (Magnet + Pickup)
        p = game.players[game.local_player_id]
        dx = p.x - self.x
        dy = p.y - self.y
        dist_sq = dx * dx + dy * dy
        
        # --- MAGNET (Mıknatıs) ---
        # Altınlar her zaman biraz çekilir, eşyalar ise magnetRange kadar
        magnet_range = p.stats.get("magnetRadius", 100)
        if self.is_gold: magnet_range = max(magnet_range, 150) # Altınlar daha iştahlı çekilir
        
        if dist_sq < magnet_range * magnet_range:
            dist = math.sqrt(dist_sq)
            # Oyuncuya doğru çekil (Mesafe kısaldıkça hızlan)
            angle = math.atan2(p.y - self.y, p.x - self.x)
            pull_speed = (magnet_range - dist) * 0.15 + (10 if self.is_gold else 5)
            self.x += math.cos(angle) * pull_speed * dt * 60
            self.y += math.sin(angle) * pull_speed * dt * 60
            
        pickup_range = self.radius + p.radius
        if dist_sq < pickup_range * pickup_range:
            self.pickup(p, game)

    def _track_rarity_quest(self, game):
        """Nadirlik bazlı günlük görevleri besler (collect_rarity/collect_unique).

        Yalnızca eşya gerçekten toplandığında ve eşya başına BİR kez çalışır
        (envanter doluyken pickup her karede yeniden çağrılıyor).

        Not: track_quest meta'yı bellek üzerinde tutar (GameLogic.get_meta),
        her toplamada disk I/O yapılmaz; yazma dalga sonunda flush edilir.
        """
        if self._quest_tracked or not hasattr(game, 'track_quest'):
            return
        self._quest_tracked = True
        rarity = self.item_data.get('rarity', 'Normal')
        if rarity in ('Rare', 'Unique'):
            game.track_quest("collect_rarity", 1)
        if rarity == 'Unique':
            game.track_quest("collect_unique", 1)

    def pickup(self, player, game):
        if self.is_gold:
            amount = self.item_data.get('value', 10)
            player.gold += amount
            if hasattr(game, 'track_quest'):
                game.track_quest("earn_gold", amount)
            game.add_event("damage_text", self.x, self.y - 40, value=f"+{amount}G", color=(241, 196, 15), timer=0.8)
            self.dead = True
        elif self.type == 'potion':
            heal = int(player.max_hp * 0.20 * (1.0 + player.stats.get('orbHealMult', 0.0)))
            player.hp = min(player.max_hp, player.hp + heal)
            game.add_event("damage_text", self.x, self.y - 40, value=f"+{heal} Can", color=(46, 204, 113), timer=1.0)
            self.dead = True
        else:
            # --- OTO-SATIŞ KONTROLÜ (Pickup Aşamasında) ---
            rarities = ['Normal', 'Magic', 'Rare', 'Unique']
            r_idx = rarities.index(self.item_data.get('rarity', 'Normal')) if self.item_data.get('rarity') in rarities else -1
            
            # Özel Eşyalar: Setler, Orblar ve Özler asla otomatik satılmaz
            is_special = bool(self.item_data.get('setTag')) or self.item_data.get('type') in ['orb', 'essence'] or r_idx == -1
            auto_mode = getattr(player, 'auto_sell_mode', 0)
            
            # Kümülatif Oto-Satış: Seçilen mod ve altındakileri sat
            should_auto_sell = not is_special and (r_idx >= 0 and r_idx < auto_mode)
            
            if should_auto_sell:
                gold_val = max(1, self.item_data.get('price', 50) // 2)
                player.gold += gold_val
                self._track_rarity_quest(game)
                game.add_event("damage_text", self.x, self.y - 40, value=f"+{gold_val} G (Oto)", color=(241, 196, 15), timer=0.5)
                self.dead = True
                return

            # Envanter mantığı: Yerden alınan eşya ÇANTAYA düşer
            if player.add_item(self.item_data):
                self._track_rarity_quest(game)
                # Efekt: Eşya ismini süzülen bir yazı olarak göster
                game.add_event("damage_text", self.x, self.y - 40, value=self.item_data['name'], color=self.color, timer=1.0)
                self.dead = True
            else:
                # Envanter dolu uyarısı
                if int(pygame.time.get_ticks() / 1000) % 2 == 0:
                    game.add_event("damage_text", self.x, self.y - 60, value="ENVANTER DOLU!", color=(231, 76, 60), timer=0.5)
                return 

    def draw(self, screen, camera_x, camera_y):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y + self.offset_y
        
        # --- Parlama Efekti (Glow) ---
        glow_size = self.radius * 4
        screen.blit(self._glow_surface, (draw_x - glow_size // 2, draw_y - glow_size // 2))
        
        # --- İkon veya Geometrik Şekil ---
        icon_drawn = False
        if self.item_data.get('icon_id'):
            icon_img = ImageLoader.get_item_icon(self.item_data['icon_id'], (self.radius * 2, self.radius * 2))
            if icon_img:
                screen.blit(icon_img, (draw_x - self.radius, draw_y - self.radius))
                icon_drawn = True
        
        if not icon_drawn:
            # Ana Şekil (Geometrik - Fallback)
            pygame.draw.circle(screen, self.color, (int(draw_x), int(draw_y)), self.radius)
            pygame.draw.circle(screen, (0, 0, 0), (int(draw_x), int(draw_y)), self.radius, 2)
