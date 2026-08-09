import math
import pygame
import random
import vfx
import audio

class Ninja:
    """
    Ninja - Hızlı ve kaçınmacı yakın dövüş sınıfı.
    - +%30 saldırı hızı, %25 kaçınma (dodge) ve en yüksek hareket hızı (6.0).
    - Uzun menzilli (180) hızlı katana savurması; hasar katananın physDmg değeriyle ölçeklenir.
    - Kritik vuruş yapabilir (critChance/critDmg statları işler).
    - Dash sonrası ilk vuruş "Backstab": x2 hasar.
    """
    def __init__(self):
        # Warrior 600ms ise Ninja 420ms civarı (30% daha hızlı)
        self.attack_cooldown = 420
        
    def execute_attack(self, player, game):
        weapon = player.inv_manager.equipped.get("weapon")
        
        # Ninja: Yakın Dövüş Modu (Menzilliyi Player.py halleder)
        if weapon and not weapon.get("isMelee"):
            player.shoot(game)
            return
            
        angle = player.facing_angle
        is_punch = (weapon is None)
        # Denge: Sabit 35 yerine katananın physDmg değeri baz alınır (silahla ölçeklenir)
        dmg_base = (12 + player.stats.get("physDmg", 0)) if not is_punch else 5
        phys_flat = player.stats.get("physDmgFlat", 0)
        dmg = (dmg_base + phys_flat) * player.stats["dmgMult"] * player.get_conditional_dmg_mult()

        # Kritik Vuruş (Shadow/Storm evrimlerinin critDmg bonusları artık melee'de işler)
        is_crit = random.random() < player.stats.get("critChance", 0.05)
        if is_crit:
            dmg *= 2.0 + player.stats.get("critDmg", 0)
        
        # Hızlı kılıç savurma (Görsel ve Alan Buffed GDD 62)
        visual_type = "slash"
        visual_timer = 0.1 if not is_punch else 0.08
        # Menzil: piksel bonusu eklenir, sonra yüzde çarpanı uygulanır (F4)
        range_bonus = player.stats.get("meleeRangeFlat", 0)
        range_mult = player.stats.get("meleeRangeMult", 1.0)
        range_visual = (160 + range_bonus) * range_mult
        range_hitbox = (180 + range_bonus) * range_mult
        
        # --- Backstab (Dash Sonrası İlk Vuruş x2 Hasar) ---
        if getattr(player, "next_attack_is_backstab", False):
            dmg *= 2.0
            game.add_event("damage_text", player.x, player.y - 30, value="BACKSTAB!", color=(255, 50, 50), timer=0.5)
            player.next_attack_is_backstab = False
            
        audio.play('melee')
            
        game.add_event(visual_type, player.x, player.y, angle=angle, range=range_visual, arc=1.4, timer=visual_timer)
        
        hit_any = False
        for e in game.iter_enemies_near(player.x, player.y, range_hitbox):
            if not e.dead and not e.is_trap:
                dx, dy = e.x - player.x, e.y - player.y
                if dx * dx + dy * dy < range_hitbox * range_hitbox:
                    # Açı Kontrolü (~80 derece)
                    angle_to_e = math.atan2(e.y - player.y, e.x - player.x)
                    diff = abs(((angle_to_e - angle) + math.pi) % (2 * math.pi) - math.pi)
                    if diff < 0.7:
                        # --- Elementel Uygulama (Ninja Yetenek Ağacı Desteği) ---
                        # Ateş/Buz yüzde statları melee'de yok sayılıyordu (F6)
                        fire_mult, frost_mult, elem_mult = player.get_elemental_mults()
                        fire_dmg  = (player.stats.get("fireDmgFlat", 0) + player.stats.get("fireDamage", 0)) * player.stats.get("dmgMult", 1.0) * fire_mult
                        frost_dmg = (player.stats.get("frostDmgFlat", 0) + player.stats.get("frostDamage", 0)) * player.stats.get("dmgMult", 1.0) * frost_mult
                        p_dps     = player.stats.get("poisonDps", 0) * player.stats.get("dmgMult", 1.0) * elem_mult

                        if fire_dmg > 0:
                            game.add_event("explosion", e.x, e.y, radius=60, color=(255, 100, 0), timer=0.1)
                            e.apply_dot('fire', fire_dmg * 0.4, 3.0)
                        if frost_dmg > 0:
                            e.apply_dot('frost', frost_dmg * 0.5, 3.5)
                        if p_dps > 0:
                            e.apply_dot('poison', p_dps, 3.0)

                        # is_crit aktarımı: krite bağlı mekanikler melee'de de çalışsın
                        e.take_damage(dmg, game, is_crit=is_crit, from_player=True)
                        vfx.hit(game, e.x, e.y,
                                'fire' if fire_dmg > 0 else ('frost' if frost_dmg > 0
                                else ('poison' if p_dps > 0 else 'phys')), is_crit=is_crit)
                        hit_any = True
        
        if hit_any:
            game.trigger_shake(3)
        
    def update(self, dt, player, game):
        pass
        
    def draw_visuals(self, screen, camera_x, camera_y):
        pass
