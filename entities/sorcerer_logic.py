import math
import random

class Sorcerer:
    """
    Büyücü (Sorcerer) - 3 element rotasyonlu uzak saldırı sınıfı (cam top).
    - Her atış sırayla fire -> frost -> poison; her 4. atış otomatik kritik + 2x AoE.
    - +%60 element hasarı (elementDmgMult) — tüm ateş/buz/zehir hasarlarını güçlendirir.
    - Bedeli: -%30 maksimum can (70 HP) - en kırılgan sınıf.
    """
    def __init__(self):
        self.attack_cooldown = 400  # Orta hız
        self.shot_cycle = ['fire', 'frost', 'poison']
        self.shot_index = 0         # Hangi elementte olduğumuzu takip eder
        self.shot_count = 0         # Toplam atış sayısı (4. atış kritiği için)

    def execute_attack(self, player, game):
        weapon = player.inv_manager.equipped.get("weapon")
        
        # Yakın Dövüş Modu veya SİLAHSIZ (Yumruk)
        if not weapon or weapon.get("isMelee"):
            is_punch = (weapon is None)
            self.execute_melee(player, game, is_punch)
            return

        # Mevcut element
        current_element = self.shot_cycle[self.shot_index % 3]
        self.shot_index += 1
        self.shot_count += 1

        # 4. atışta garantili kritik + AoE boost
        force_crit = (self.shot_count % 4 == 0)
        force_aoe  = force_crit

        # Geçici olarak mermi tipini ve AoE'yi override et
        orig_aoe = player.stats.get("aoe", 1.0)
        if force_aoe:
            player.stats["aoe"] = orig_aoe * 2.0  # 4. atışta 2x alan

        player._sorcerer_override_element = current_element
        player._sorcerer_force_crit       = force_crit
        player.shoot(game)

        # Override temizle
        player._sorcerer_override_element = None
        player._sorcerer_force_crit       = False
        player.stats["aoe"] = orig_aoe

    def execute_melee(self, player, game, is_punch=False):
        angle = player.facing_angle
        dmg_base = 20 if not is_punch else 5
        phys_flat = player.stats.get("physDmgFlat", 0)
        dmg = (dmg_base + phys_flat) * player.stats["dmgMult"] * player.get_conditional_dmg_mult()
        visual_color = (52, 152, 219) if not is_punch else (255, 255, 255)
        visual_timer = 0.1 if not is_punch else 0.08
        
        # Sihirli kılıç efekti (Mavi parıltı) veya beyaz yumruk
        game.add_event("slash", player.x, player.y, angle=angle, range=90, arc=1.0, timer=visual_timer, color=visual_color)
        
        for e in game.iter_enemies_near(player.x, player.y, 110):
            dx, dy = e.x - player.x, e.y - player.y
            if not e.dead and dx * dx + dy * dy < 110 * 110:
                e.take_damage(dmg, game)
                if random.random() < 0.2: # Şans eseri rastgele element yavaşlatması
                    e.apply_dot('frost', 5, 2.0)

    def update(self, dt, player, game):
        # Kan öfkesi gibi pasif yoktur ama ilerde eklenebilir
        pass

    def draw_visuals(self, screen, camera_x, camera_y):
        pass
