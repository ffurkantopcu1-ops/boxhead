import math
import pygame

class Warrior:
    """
    Savaşçı (Warrior) - Dayanıklı yakın dövüş sınıfı.
    - +%20 hasar ve +%20 maksimum can (en tanky başlangıç).
    - Geniş koni (~70°) kılıç savurması; hasar silahın physDmg değeriyle ölçeklenir.
    - Ateş/buz/zehir statlarını yakın dövüşte uygular; ateş vuruşları alana sıçrar.
    """
    def __init__(self):
        self.attack_range = 100
        self.attack_arc = 1.2 # ~70 derece
        
    def execute_attack(self, player, game):
        weapon = player.inv_manager.equipped.get("weapon")
        
        # Menzilli veya Bomba ise: Menzilli saldırı yap
        if weapon and (weapon.get("isRanged") or weapon.get("isBomb")):
            player.shoot(game)
            return

        # Warrior: Kılıç Savurma (Melee) veya Yumruk
        range_val = (self.attack_range + player.stats.get("meleeRange", 0)) * player.stats.get("meleeRangeMult", 1.0)
        angle = player.facing_angle
        
        # Hasar ve Görsel Belirleme
        # Denge: Sabit 45 yerine silahın physDmg değeri baz alınır (silahla ölçeklenir)
        is_punch = weapon is None
        dmg_base = (18 + player.stats.get("physDmg", 0)) if not is_punch else 5
        visual_type = "sweep" if not is_punch else "slash"
        visual_timer = 0.15 if not is_punch else 0.1
        
        # Görsel Efekt
        game.add_event(visual_type, player.x, player.y, angle=angle, range=range_val, arc=self.attack_arc, timer=visual_timer)
        
        # Hasar Kontrolü
        hit_any = False
        phys_flat = player.stats.get("physDmgFlat", 0)
        dmg = (dmg_base + phys_flat) * player.stats["dmgMult"] * player.get_conditional_dmg_mult()
        
        for e in game.iter_enemies_near(player.x, player.y, range_val + 160):
            if not e.dead and not e.is_trap:
                dx = e.x - player.x
                dy = e.y - player.y
                hit_range = range_val + e.radius
                if dx * dx + dy * dy < hit_range * hit_range:
                    # Açı Kontrolü (±π sınırında normalize edilir)
                    angle_to_e = math.atan2(e.y - player.y, e.x - player.x)
                    diff = abs(((angle_to_e - angle) + math.pi) % (2 * math.pi) - math.pi)
                    if diff < self.attack_arc / 2:
                        import random
                        is_crit = random.random() < player.stats.get("critChance", 0.05)
                        crit_mult = 2.0 + player.stats.get("critDmg", 0)
                        final_dmg = dmg * crit_mult if is_crit else dmg
                        elem_mult = 1.0 + player.stats.get("elementDmgMult", 0.0)

                        # --- ELEMENTEL UYGULAMA (NEW!) ---
                        # 1. Zehir
                        p_dps = player.stats.get("poisonDps", 0) * player.stats["dmgMult"] * elem_mult
                        if p_dps > 0: e.apply_dot('poison', p_dps, 3.0)

                        # 2. Buz (Sadece DoT, Yavaşlatma Kaldırıldı v1.0.6.6)
                        f_dmg = (player.stats.get("frostDmgFlat", 0) + player.stats.get("frostDamage", 0)) * player.stats["dmgMult"] * elem_mult
                        if f_dmg > 0: e.apply_dot('frost', f_dmg * 0.5, 3.5)

                        # 3. Ateş (Patlama + Yanma)
                        fire_dmg = (player.stats.get("fireDmgFlat", 0) + player.stats.get("fireDamage", 0)) * player.stats["dmgMult"] * elem_mult
                        if fire_dmg > 0:
                            # Vuruş anında mini patlama (AoE Pulse)
                            game.add_event("explosion", e.x, e.y, radius=80, color=(255, 100, 0), timer=0.15)
                            # Yakındaki düşmanlara sıçra (Splash)
                            splash_count = 0
                            for other in game.iter_enemies_near(e.x, e.y, 80):
                                if not other.dead and not other.is_trap and other != e:
                                    odx = other.x - e.x
                                    ody = other.y - e.y
                                    if odx * odx + ody * ody < 80 * 80:
                                        other.take_damage(fire_dmg, game)
                                        other.apply_dot('fire', fire_dmg * 0.4, 3.0)
                                        splash_count += 1
                                        if splash_count >= 10:
                                            break
                            # Ana hedefe Yanma
                            e.apply_dot('fire', fire_dmg * 0.4, 3.0)

                        e.take_damage(final_dmg, game)
                        hit_any = True
        
        # Dash kaldırıldı (İsteğe bağlı sarsıntı eklenebilir ama dash artık yok)
        pass
        
    def draw_visuals(self, screen, camera_x, camera_y):
        # Warrior özel görseli (Kılıç izi vb. eventler ile yönetiliyor)
        pass
