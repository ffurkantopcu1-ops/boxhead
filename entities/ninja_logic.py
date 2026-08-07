import math
import pygame
import random

class Ninja:
    def __init__(self):
        # Warrior 600ms ise Ninja 420ms civarı (30% daha hızlı)
        self.attack_cooldown = 420
        
    def execute_attack(self, player, game):
        weapon = player.inv_manager.equipped.get("weapon")
        
        # Ninja: Yakın Dövüş Modu (Menzilliyi Player.py halleder)
        angle = player.facing_angle
        is_punch = (weapon is None)
        dmg_base = 35 if not is_punch else 5
        phys_flat = player.stats.get("physDmgFlat", 0)
        dmg = (dmg_base + phys_flat) * player.stats["dmgMult"]
        
        # Hızlı kılıç savurma (Görsel ve Alan Buffed GDD 62)
        visual_type = "slash"
        visual_timer = 0.1 if not is_punch else 0.08
        range_bonus = player.stats.get("meleeRange", 0)
        range_visual = 160 + range_bonus
        range_hitbox = 180 + range_bonus
        
        # --- Backstab (Dash Sonrası İlk Vuruş x2 Hasar) ---
        if getattr(player, "next_attack_is_backstab", False):
            dmg *= 2.0
            game.add_event("damage_text", player.x, player.y - 30, value="BACKSTAB!", color=(255, 50, 50), timer=0.5)
            player.next_attack_is_backstab = False
            
        game.add_event(visual_type, player.x, player.y, angle=angle, range=range_visual, arc=1.4, timer=visual_timer)
        
        hit_any = False
        for e in game.enemies:
            if not e.dead and not e.is_trap:
                dist = math.hypot(e.x - player.x, e.y - player.y)
                if dist < range_hitbox:
                    # Açı Kontrolü (~80 derece)
                    angle_to_e = math.atan2(e.y - player.y, e.x - player.x)
                    diff = abs(((angle_to_e - angle) + math.pi) % (2 * math.pi) - math.pi)
                    if diff < 0.7:
                        # --- Elementel Uygulama (Ninja Yetenek Ağacı Desteği) ---
                        fire_dmg  = (player.stats.get("fireDmgFlat", 0) + player.stats.get("fireDamage", 0)) * player.stats.get("dmgMult", 1.0)
                        frost_dmg = (player.stats.get("frostDmgFlat", 0) + player.stats.get("frostDamage", 0)) * player.stats.get("dmgMult", 1.0)
                        p_dps     = player.stats.get("poisonDps", 0) * player.stats.get("dmgMult", 1.0)

                        if fire_dmg > 0:
                            game.add_event("explosion", e.x, e.y, radius=60, color=(255, 100, 0), timer=0.1)
                            e.apply_dot('fire', fire_dmg * 0.4, 3.0)
                        if frost_dmg > 0:
                            e.apply_dot('frost', frost_dmg * 0.5, 3.5)
                        if p_dps > 0:
                            e.apply_dot('poison', p_dps, 3.0)

                        e.take_damage(dmg, game)
                        hit_any = True
        
        if hit_any:
            game.trigger_shake(3)
        
    def update(self, dt, player, game):
        pass
        
    def draw_visuals(self, screen, camera_x, camera_y):
        pass
