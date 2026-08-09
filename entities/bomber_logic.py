import math
import pygame
import random

class Bomber:
    """
    Bombacı (Bomber) - Patlayıcı ve alan hasarı uzmanı.
    - Şişe/bomba fırlatırken alan yarıçapını x1.5 büyütür.
    - Taban saldırı süresi 1500ms: oyunun en yavaş ama en geniş vuruşu.

    NOT: Sınıf henüz sınıf seçim ekranında yok. Etkinleştirmek için gereken
    değişiklikler rapordaki DEVİR bölümündedir (class_select_scene.py,
    player.reinit_specialization, InventoryManager.CLASS_IDS, başlangıç silahı).
    """

    AOE_MULT = 1.5

    def __init__(self):
        self.attack_cooldown = 1500

    def execute_attack(self, player, game):
        weapon = player.inv_manager.equipped.get("weapon")

        # Yakın dövüş silahı veya silahsız: temel savurma/yumruk
        if not weapon or weapon.get("isMelee"):
            self.execute_melee(player, game, is_punch=(weapon is None))
            return

        # Menzilli (arbalet/asa) silahlar bomba mantığına girmez
        is_bomb = (weapon.get("isBomb", False)
                   or "şişe" in weapon.get("name", "").lower()
                   or "bomba" in weapon.get("name", "").lower())
        if not is_bomb:
            player.shoot(game)
            return

        # Bombacı: normal atıştan daha büyük alan hasarı (AoE)
        orig_aoe = player.stats.get("aoe", 1.0)
        player.stats["aoe"] = orig_aoe * self.AOE_MULT
        try:
            player.shoot(game, is_bomb=True)
        finally:
            # İstisna çıksa bile aoe statı şişmiş kalmamalı
            player.stats["aoe"] = orig_aoe

    def execute_melee(self, player, game, is_punch=False):
        """Silah yoksa/melee silahtayken kısa menzilli patlayıcı savurma."""
        angle = player.facing_angle
        dmg_base = 22 if not is_punch else 5
        phys_flat = player.stats.get("physDmgFlat", 0)
        dmg = ((dmg_base + phys_flat)
               * player.stats.get("dmgMult", 1.0)
               * player.get_conditional_dmg_mult())

        range_val = 110 * player.stats.get("aoe", 1.0)
        game.add_event("explosion", player.x + math.cos(angle) * 40,
                       player.y + math.sin(angle) * 40,
                       radius=int(range_val * 0.6), color=(255, 140, 40), timer=0.15)

        for e in game.iter_enemies_near(player.x, player.y, range_val):
            dx, dy = e.x - player.x, e.y - player.y
            if not e.dead and not getattr(e, 'is_trap', False) and dx * dx + dy * dy < range_val * range_val:
                e.take_damage(dmg, game, from_player=True)
                if random.random() < 0.25:
                    e.apply_dot('fire', 8 * player.stats.get("dmgMult", 1.0), 2.0)

    def update(self, dt, player, game):
        pass

    def draw_visuals(self, screen, camera_x, camera_y):
        pass
