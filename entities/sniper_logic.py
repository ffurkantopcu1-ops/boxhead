import math
import pygame
import random

class Sniper:
    def __init__(self):
        self.attack_range = 800
        
    def execute_attack(self, player, game):
        weapon = player.inv_manager.equipped.get("weapon")
        
        # Eğer elde kılıç yoksa veya SİLAHSIZSA: Yakın dövüş moduna geç
        if not weapon or weapon.get("isMelee"):
            is_punch = (weapon is None)
            self.execute_melee(player, game, is_punch)
            return

        # Sniper Bonusu: +20% Kritik Şansı (Zaten baz statlarda mevcut, sadece ateş ediyoruz)
        player.shoot(game)

    def execute_melee(self, player, game, is_punch=False):
        # Basit kılıç savurma (Warrior'dan basitleştirildi)
        angle = player.facing_angle
        dmg_base = 25 if not is_punch else 5
        dmg = dmg_base * player.stats["dmgMult"]
        visual_timer = 0.1 if not is_punch else 0.08
        game.add_event("slash", player.x, player.y, angle=angle, range=100, arc=1.2, timer=visual_timer)
        
        for e in game.iter_enemies_near(player.x, player.y, 120):
            dx, dy = e.x - player.x, e.y - player.y
            if not e.dead and dx * dx + dy * dy < 120 * 120:
                e.take_damage(dmg, game)

    def update(self, dt, player, game):
        pass
        
    def draw_visuals(self, screen, camera_x, camera_y):
        pass
