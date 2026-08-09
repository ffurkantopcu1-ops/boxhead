import math
import pygame
import random
import vfx

class Alchemist:
    """
    Simyacı (Alchemist) - Alan kontrolü ve süreli hasar (DoT) uzmanı.

    KİMLİK (Bombacı'dan ayrım):
      Şişe çarptığı yerde anında patlar ve geride UZUN SÜRELİ ZEHİR BULUTU
      bırakır. Hasar birikimlidir: tek vuruş zayıf, ama bulutun içinde kalan
      düşman erir. Oyun hissi: alanı zehirle, düşmanı bulutun içine sür.

      Bombacı ise patlamaz — yere tetiklemeli mayın bırakır ve tek seferlik
      büyük fiziksel patlama verir. İkisi aynı bomba yolunu kullanır; ayrım
      Projectile.cloud_duration_mult (Simyacı) ve becomes_mine (Bombacı) ile
      yapılır.
    """

    AOE_MULT = 1.4
    # Şişenin bıraktığı bulut normalin bu katı kadar yerde kalır (1.3s -> ~4.5s)
    CLOUD_DURATION_MULT = 3.5

    def __init__(self):
        # Bomber'dan (1500) daha hızlı
        self.attack_cooldown = 1200
        
    def execute_attack(self, player, game):
        weapon = player.inv_manager.equipped.get("weapon")
        
        # Yakın Dövüş Modu veya SİLAHSIZ (Yumruk)
        if not weapon or weapon.get("isMelee"):
            is_punch = (weapon is None)
            self.execute_melee(player, game, is_punch)
            return

        # Alchemist: Yüksek AOE Zehirli Patlama
        # Eğer elinde Arbalet/Asa varsa normal mermi ama Alchemist bonusu ile
        is_bomb = weapon.get("isBomb", False) or "şişe" in weapon.get("name", "").lower()
        
        orig_aoe = player.stats.get("aoe", 1.0)
        if is_bomb:
            player.stats["aoe"] = orig_aoe * self.AOE_MULT
            before = len(game.projectiles)
            try:
                player.shoot(game, is_bomb=True)
            finally:
                # İstisna çıksa bile aoe statı şişmiş kalmamalı
                player.stats["aoe"] = orig_aoe
            # Simyacı kimliği: geride kalan zehir bulutu çok daha uzun yaşar.
            # statusDuration statı buluta da yansır (set/affix bonusları işe yarar).
            dur_mult = self.CLOUD_DURATION_MULT * (1.0 + player.stats.get("statusDuration", 0))
            for p in game.projectiles[before:]:
                p.cloud_duration_mult = dur_mult
        else:
            # Ranged silah (Arbalet vb.)
            player.shoot(game)

    def execute_melee(self, player, game, is_punch=False):
        angle = player.facing_angle
        dmg_base = 20 if not is_punch else 5
        phys_flat = player.stats.get("physDmgFlat", 0)
        dmg = (dmg_base + phys_flat) * player.stats["dmgMult"] * player.get_conditional_dmg_mult()
        
        # Yumruk ise "slash", kılıç ise "slash" (Alchemist için ikisi de slash ama görsel süresi farklı)
        visual_type = "slash"
        visual_timer = 0.1 if not is_punch else 0.08
        
        game.add_event(visual_type, player.x, player.y, angle=angle, range=90, arc=1.0, timer=visual_timer)
        
        for e in game.iter_enemies_near(player.x, player.y, 110):
            dx, dy = e.x - player.x, e.y - player.y
            if not e.dead and dx * dx + dy * dy < 110 * 110:
                e.take_damage(dmg, game, from_player=True)
                vfx.hit(game, e.x, e.y, 'poison')
                if random.random() < 0.3: # Şans eseri zehirle
                    e.apply_dot('poison', 5 * player.stats["dmgMult"], 2.0)
        
    def update(self, dt, player, game):
        pass
        
    def draw_visuals(self, screen, camera_x, camera_y):
        pass
