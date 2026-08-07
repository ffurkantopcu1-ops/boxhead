import math
import random

class Bloodwalker:
    """
    Vampir (Bloodwalker) - Risk-reward sınıfı.
    - Her vuruşta %20 can çalar (Lifesteal).
    - HP %30 altına düşünce "Kan Öfkesi" aktif: +%40 hasar ve hız.
    - Q tuşuyla "Kan Emme": 1.5 sn kendine çarpan mermileri emerek HP'ye dönüştürür.
    """
    def __init__(self):
        self.attack_cooldown = 350  # Warrior'dan biraz hızlı

        # Kan Emme yeteneği
        self.blood_absorb_cooldown = 20.0   # 20 sn cooldown
        self.blood_absorb_timer    = 0.0    # Geri sayım
        self.blood_absorb_active   = False
        self.blood_absorb_duration = 1.5

    # ---- Melee saldırı (Warrior mantığına benzer) ----
    def execute_attack(self, player, game):
        weapon = player.inv_manager.equipped.get("weapon")
        
        # Menzilli / Bomba Kontrolü
        if weapon and (weapon.get("isRanged") or weapon.get("isBomb")):
            player.shoot(game)
            return

        # Yakın Dövüş Hesapla (Silah yoksa Yumruk)
        is_punch = (weapon is None)
        dmg_base = player.stats.get("physDmg", 20) if not is_punch else 5
        phys_flat = player.stats.get("physDmgFlat", 0)
        range_val = (100 + player.stats.get("meleeRange", 0)) * player.stats.get("meleeRangeMult", 1.0)
        
        # Görsel Efekt
        visual = "sweep" if not is_punch else "slash"
        game.add_event(visual, player.x, player.y, angle=player.facing_angle, range=range_val, arc=0.9, timer=0.12)

        dmg = (dmg_base + phys_flat) * player.stats.get("dmgMult", 1.0)
        is_crit = random.random() < player.stats.get("critChance", 0.05)
        final_dmg = dmg * 2 if is_crit else dmg
        
        angle = player.facing_angle
        hit_any = False
        
        # (Aşağıdaki düşman döngüsü devam eder...)
        for e in game.iter_enemies_near(player.x, player.y, range_val + 160):
            if e.dead or e.is_trap:
                continue
            dx = e.x - player.x
            dy = e.y - player.y
            hit_range = range_val + e.radius
            if dx * dx + dy * dy < hit_range * hit_range:
                angle_to_e = math.atan2(e.y - player.y, e.x - player.x)
                diff = abs(((angle_to_e - angle) + math.pi) % (2 * math.pi) - math.pi)
                if diff < 0.9:  # ~100 derece yay
                    e.take_damage(final_dmg, game)
                    hit_any = True

                    # Lifesteal — her vuruşta %20 can al
                    if player.hp < player.max_hp and player.lifesteal_cooldown_timer <= 0:
                        lifesteal = player.stats.get("lifesteal", 0.20)
                        heal = final_dmg * lifesteal
                        player.hp = min(player.max_hp, player.hp + heal)

                    # Elementel uygulama (Warrior ile aynı mantık)
                    fire_dmg  = (player.stats.get("fireDmgFlat", 0) + player.stats.get("fireDamage", 0)) * player.stats.get("dmgMult", 1.0)
                    frost_dmg = (player.stats.get("frostDmgFlat", 0) + player.stats.get("frostDamage", 0)) * player.stats.get("dmgMult", 1.0)
                    p_dps     = player.stats.get("poisonDps", 0) * player.stats.get("dmgMult", 1.0)

                    if fire_dmg > 0:
                        game.add_event("explosion", e.x, e.y, radius=70, color=(200, 60, 0), timer=0.12)
                        for other in game.iter_enemies_near(e.x, e.y, 70):
                            if not other.dead and not other.is_trap and other != e:
                                odx = other.x - e.x
                                ody = other.y - e.y
                                if odx * odx + ody * ody < 70 * 70:
                                    other.take_damage(fire_dmg, game)
                                    other.apply_dot('fire', fire_dmg * 0.4, 3.0)
                        e.apply_dot('fire', fire_dmg * 0.4, 3.0)
                    if frost_dmg > 0:
                        e.apply_dot('frost', frost_dmg * 0.5, 3.5)
                    if p_dps > 0:
                        e.apply_dot('poison', p_dps, 3.0)

        if hit_any:
            game.trigger_shake(5)

    # ---- Kan Emme aktifleştir (Q tuşu) ----
    def activate_blood_absorb(self, player):
        if self.blood_absorb_timer <= 0 and not self.blood_absorb_active:
            self.blood_absorb_active   = True
            self.blood_absorb_timer    = self.blood_absorb_cooldown
            self._absorb_remaining     = self.blood_absorb_duration
            return True
        return False

    def update(self, dt, player, game):
        # Cooldown geri sayım
        if self.blood_absorb_timer > 0:
            self.blood_absorb_timer -= dt

        # Kan Emme süresi
        if self.blood_absorb_active:
            self._absorb_remaining -= dt
            if self._absorb_remaining <= 0:
                self.blood_absorb_active = False

            # Emme sırasında kendine çarpan mermileri HP'ye dönüştür
            for proj in game.projectiles[:]:
                if proj.is_hostile:
                    dist = math.hypot(proj.x - player.x, proj.y - player.y)
                    if dist < player.radius + proj.radius + 10 and player.hp < player.max_hp and player.lifesteal_cooldown_timer <= 0:
                        heal = proj.dmg * 1.5  # Hasar yerine can geri al
                        player.hp = min(player.max_hp, player.hp + heal)
                        proj.dead = True
                        game.add_event("damage_text", player.x, player.y - 25,
                                       value=f"+{int(heal)}", color=(255, 80, 80), timer=0.5)

        # --- KAN ÖFKESİ (Rage) Pasifi ---
        rage_active = player.hp < player.max_hp * 0.30
        if rage_active != getattr(player, '_bloodwalker_rage_active', False):
            player._bloodwalker_rage_active = rage_active
            player.inv_manager.recalculate_stats()

    def draw_visuals(self, screen, camera_x, camera_y):
        pass
