import math
import pygame
import random

class Alchemist:
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
            player.stats["aoe"] = orig_aoe * 1.4 
            player.shoot(game, is_bomb=True)
            player.stats["aoe"] = orig_aoe
        else:
            # Ranged silah (Arbalet vb.)
            player.shoot(game)

    def execute_melee(self, player, game, is_punch=False):
        angle = player.facing_angle
        dmg_base = 20 if not is_punch else 5
        phys_flat = player.stats.get("physDmgFlat", 0)
        dmg = (dmg_base + phys_flat) * player.stats["dmgMult"]
        
        # Yumruk ise "slash", kılıç ise "slash" (Alchemist için ikisi de slash ama görsel süresi farklı)
        visual_type = "slash"
        visual_timer = 0.1 if not is_punch else 0.08
        
        game.add_event(visual_type, player.x, player.y, angle=angle, range=90, arc=1.0, timer=visual_timer)
        
        for e in game.iter_enemies_near(player.x, player.y, 110):
            dx, dy = e.x - player.x, e.y - player.y
            if not e.dead and dx * dx + dy * dy < 110 * 110:
                e.take_damage(dmg, game)
                if random.random() < 0.3: # Şans eseri zehirle
                    e.apply_dot('poison', 5 * player.stats["dmgMult"], 2.0)
        
    def update(self, dt, player, game):
        pass
        
    def draw_visuals(self, screen, camera_x, camera_y):
        pass
