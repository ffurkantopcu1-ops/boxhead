import math
import pygame
import random

class Beastmaster:
    """
    Canavar Efendisi (Beastmaster) - Minyon odaklı sınıf.
    - +%30 minyon hasarı ve +%10 maksimum can; kurt yoldaşıyla başlar.
    - Kamçı vuruşu hedefi hem hasarlar hem "işaretler": tüm minyonlar o hedefe
      kilitlenir ve saldırı bekleme süreleri sıfırlanır.
    """
    def __init__(self):
        pass
        
    def execute_attack(self, player, game):
        weapon = player.inv_manager.equipped.get("weapon")
        
        # Menzilli / Bomba Kontrolü
        if weapon and (weapon.get("isRanged") or weapon.get("isBomb")):
            player.shoot(game)
            return

        # Beastmaster Özel: Minyon Komutu
        is_punch = (weapon is None)
        dmg = 30 * player.stats.get("dmgMult", 1.0) if not is_punch else 5
        angle = player.facing_angle
        arc = 1.0
        range_val = 120 + player.stats.get("meleeRange", 0)
        
        # Görsel Efekt (Lila Kamçı / Beyaz Yumruk)
        color = (155, 89, 182) if not is_punch else (255, 255, 255)
        visual = "sweep" if not is_punch else "slash"
        game.add_event(visual, player.x, player.y, angle=angle, range=range_val, arc=arc, color=color, timer=0.15)
        
        target_enemy = None
        min_d = range_val + 50
        
        for e in game.iter_enemies_near(player.x, player.y, range_val + 160):
            if not e.dead and not e.is_trap:
                dx, dy = e.x - player.x, e.y - player.y
                d_sq = dx * dx + dy * dy
                if d_sq < (range_val + e.radius) ** 2:
                    # Açı Kontrolü
                    angle_to_e = math.atan2(e.y - player.y, e.x - player.x)
                    diff = abs(angle_to_e - angle)
                    if diff > math.pi: diff = math.pi * 2 - diff
                    if diff < arc / 2:
                        # Artık kamçı hasar vurmuyor, sadece "İŞARETLİYOR"
                        if d_sq < min_d * min_d:
                            min_d = math.sqrt(d_sq)
                            target_enemy = e
        
        # 2. Kamçı Hasarı + Minyonları Hedefe "Odakla" (Priority Target)
        if target_enemy:
            # Denge: Kamçı artık işaretlediği hedefe hasar da vurur (eskiden 0 hasar)
            target_enemy.take_damage(dmg, game)
            for m in game.minions:
                if m.owner == player:
                    m.priority_target = target_enemy
                    m.last_attack_time = 0 # Saldırı bekleme süresini sıfırla (Anında saldır)
                    game.add_event("slash", target_enemy.x, target_enemy.y, color=(155, 89, 182), timer=0.2)

    def update(self, dt, player, game):
        pass
        
    def draw_visuals(self, screen, camera_x, camera_y):
        pass
