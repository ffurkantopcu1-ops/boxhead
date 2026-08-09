import math
import pygame

class Engineer:
    """
    Mühendis (Engineer) - Taret odaklı savunma sınıfı.
    - +1 taret limiti (toplam 2) ve +10 zırh ile başlar.
    - 5 saniyede bir taret kurabilir; taret hasarı sahibinin silah gücüyle
      (physDmg) ve turretDmg/turretRate statlarıyla ölçeklenir.
    - Taretler düşman saldırısını üstüne çeker (aggro emer).
    """
    def __init__(self):
        self.attack_range = 300
        self.turret_cooldown = 0
        
    def execute_attack(self, player, game):
        weapon = player.inv_manager.equipped.get("weapon")
        
        # Menzilli / Bomba Kontrolü
        if weapon and (weapon.get("isRanged") or weapon.get("isBomb")):
            player.shoot(game)
            return

        # Sadece Taret Kiti Varsa Taret Kur
        if weapon and weapon.get("isTurret"):
            current_time = pygame.time.get_ticks()
            if current_time - self.turret_cooldown >= 5000:
                player.place_turret(game)
                self.turret_cooldown = current_time
            return

        # Yakın Dövüş Modu (Silah varsa Keser, yoksa Yumruk)
        angle = player.facing_angle
        is_punch = (weapon is None)
        dmg = 25 * player.stats["dmgMult"] * player.get_conditional_dmg_mult() if not is_punch else 5
        
        game.add_event("slash", player.x, player.y, angle=angle, range=90, arc=1.0, timer=0.1)
        
        for e in game.iter_enemies_near(player.x, player.y, 110):
            dx, dy = e.x - player.x, e.y - player.y
            if not e.dead and dx * dx + dy * dy < 110 * 110:
                e.take_damage(dmg, game, from_player=True)
        
    def update(self, dt, player, game):
        pass
        
    def draw_visuals(self, screen, camera_x, camera_y):
        pass
        
