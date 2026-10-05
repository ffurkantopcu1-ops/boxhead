import pygame
import math
import random
import vfx

class Minion:
    def __init__(self, id, x, y, m_type="wolf", owner=None, local_stats=None):
        self.id = id
        self.x = x
        self.y = y
        self.type = m_type # "wolf" or "dragon"
        self.owner = owner
        self.local_stats = local_stats if local_stats else {}
        self.radius = 16
        
        # Base stats (Don't multiply yet, will do in attack)
        if m_type == "doppelganger":
            self.base_dmg = 30
            self.speed = 5.0
            base_range = 400
            self.color = (138, 43, 226) # Purple
            base_cd = 400
        elif m_type == "shadow_clone":
            self.base_dmg = 20
            self.speed = 6.0
            base_range = 400
            self.color = (50, 50, 50) # Dark gray
            base_cd = 300
        elif m_type == "wolf":
            self.base_dmg = 15
            self.speed = 4.0
            base_range = 350
            self.color = (149, 165, 166)
            base_cd = 500
        elif m_type == "drone":
            # 'orbitDrones' affix'inin doğurduğu yörünge dronu. Pet slotuna
            # bağlı değildir, bu yüzden check_minions'ın wolf/dragon
            # temizliğine takılmaz.
            self.base_dmg = 20
            self.speed = 6.0
            base_range = 450
            self.color = (120, 200, 255)
            base_cd = 700
        elif m_type == "undead":
            # Ölümsüz Ordu kartıyla dirilen düşman: pet slotuna bağlı olmadığı
            # için check_minions'ın wolf/dragon temizliğine takılmaz (H12)
            self.base_dmg = 18
            self.speed = 4.5
            base_range = 350
            self.color = (150, 50, 200)
            base_cd = 600
        else: # dragon
            self.base_dmg = 25
            self.speed = 3.0
            base_range = 600
            self.color = (231, 76, 60)
            base_cd = 800
            
        range_mult = owner.stats.get("minionRange", 1.0) if owner else 1.0
        self.range = base_range * range_mult
        self.base_range = base_range
        
        self.dead = False
        self.is_recharging = False
        self.recharge_timer = 0
        # Compatibility fields for helper targeting; pets do not take damage.
        self.hp = self.max_hp = 1.0

        # minionRate __init__'te bir kez okunuyordu; sonradan alınan
        # aura/sinerji/skill mevcut minyonlara işlemiyordu (bayat stat).
        # Taban süre saklanır, çarpan KULLANIM ANINDA (update) uygulanır -
        # wind_minions çarpanıyla aynı idempotent desen.
        self.base_cd = base_cd
        rate_mult = owner.stats.get("minionRate", 1.0) if owner else 1.0
        # Geriye dönük uyum: eski kodu okuyan yerler için alan korunur.
        self.attack_cooldown = base_cd / max(0.1, rate_mult)

        self.aura_timer = 0
        self.last_attack_time = 0
        self.target = None
        self.priority_target = None
        
        self.offset_x = random.uniform(-80, 80)
        self.offset_y = random.uniform(-80, 80)
        
        self.lifetime = 10.0 if m_type == "shadow_clone" else None

    def update(self, dt, game):
        if not self.owner: return
        from logic.minion_inheritance import combat_stats
        stats = combat_stats(self.owner)
        self.range = self.base_range * max(.1, stats.get('minionRange', 1.0)) + stats.get("minionExtraRange", 0)

        # Pet İmparatoru evrimi (wind_minions): minyonlar %40 daha hızlı hareket
        # eder ve %30 daha sık saldırır.
        # DİKKAT: self.speed / self.attack_cooldown'a KALICI çarpan uygulanmaz.
        # Bu değerler __init__'te bir kez kuruluyor; her karede çarpmak onları
        # üstel olarak bozar, "bir kez uygula" bayrağı ise evrim öncesi doğan
        # minyonlarda ya da stat yeniden hesaplamasında tutarsız kalır.
        # Bunun yerine çarpan KULLANIM ANINDA uygulanır (idempotent).
        wind = getattr(self.owner, 'evolution_passive', '') == 'wind_minions'
        move_speed = self.speed * (1.4 if wind else 1.0) * stats.get("minionMoveMult", 1)


        if self.dead:
            return
        if self.lifetime is not None:
            self.lifetime -= dt
            if self.lifetime <= 0:
                self.dead = True
                return

        # 1. HAREKET SENKRONİZASYONU (Sync)
        # Oyuncunun anlık yer değiştirmesini minyona aktar (Yetişme sorunu çözümü)
        self.x += self.owner.vx * dt
        self.y += self.owner.vy * dt
        
        target_x = self.owner.x + self.offset_x
        target_y = self.owner.y + self.offset_y
        dist_to_owner = math.hypot(target_x - self.x, target_y - self.y)
        
        # TASMA (LEASH): 500 birimden uzaktaysa her şeyi bırakıp oyuncuya odaklan
        is_too_far = dist_to_owner > 500
        if is_too_far:
            self.target = None
            self.priority_target = None
        
        # Offset konumunu korumak için küçük düzeltme hareketi
        if dist_to_owner > 10:
            angle = math.atan2(target_y - self.y, target_x - self.x)
            # Eğer çok uzaktaysa 'turbo' hızla yetiş
            catchup_speed = move_speed * (2.0 if is_too_far else 1.2)
            self.x += math.cos(angle) * catchup_speed * dt * 60
            self.y += math.sin(angle) * catchup_speed * dt * 60
            
        # 2. TOXIC AURA (Alan Hasarı)
        self.aura_timer += dt
        if self.aura_timer >= 1.0: # Her saniye
            self.aura_timer = 0
            inherited = getattr(self.owner, "has_minion_inheritance", False)
            packets = [("poison", stats.get("toxicAura", 0))]
            if inherited:
                packets.extend((("physical", self.owner.max_hp*.05*stats.get("decayAura", 0)),
                                ("lightning", stats.get("static_field", 0)),
                                ("fire", 75*stats.get("starfallAura", 0))))
            for enemy in list(game.iter_enemies_near(self.x, self.y, 150)):
                if enemy.dead or enemy.is_trap or (enemy.x-self.x)**2+(enemy.y-self.y)**2 >= 150**2:
                    continue
                if inherited and getattr(self.owner, "has_chaos_field", False):
                    from logic.status_effects import StatusEffect
                    enemy.effect_manager.add_effect(StatusEffect("ChaosArmor", 1.5))
                enemy.last_hit_by_minion = True
                try:
                    for kind, amount in packets:
                        if amount > 0 and not enemy.dead:
                            enemy.take_damage(amount, game, from_player=True, damage_type=kind)
                finally:
                    enemy.last_hit_by_minion = False

        # 3. HEDEF BUL (En yakın düşman)
        self.find_target(game)
        
        # 3. SALDIRI
        current_time = pygame.time.get_ticks()
        
        # Attack Speed hesaplaması
        # minionRate her karede taze okunur (bkz. __init__ notu); böylece
        # dalga ortasında alınan aura/skill mevcut sürüye de işler.
        rate_mult = max(0.1, stats.get("minionRate", 1.0))
        self.attack_cooldown = self.base_cd / rate_mult
        eff_cooldown = self.attack_cooldown / max(.1, 1.0 + stats.get("minionAttackSpeed", 0))
        eff_cooldown *= stats.get("minionCooldownMult", 1)
        if wind:
            eff_cooldown *= 0.7


        if self.target and current_time - self.last_attack_time >= eff_cooldown:
            # RANGE KONTROLÜ: Minyonun hedefe olan mesafesi
            dist_to_target = math.hypot(self.target.x - self.x, self.target.y - self.y)
            if dist_to_target < self.range:
                self.attack(game)
                self.last_attack_time = current_time

    def find_target(self, game):
        # Oyuncu mesafesini kontrol et (Sadece oyuncu yakınındayken hedef ara)
        dist_to_owner = math.hypot(self.owner.x - self.x, self.owner.y - self.y)
        
        # 1. ÖNCELİKLİ HEDEF KONTROLÜ (Kamçıyla işaretlenen)
        if self.priority_target:
            d = math.hypot(self.priority_target.x - self.owner.x, self.priority_target.y - self.owner.y)
            # Öncelikli hedef çok uzaktaysa (800 birim) bırak
            if self.priority_target.dead or d > 800 or self.priority_target.is_trap:
                self.priority_target = None
            else:
                self.target = self.priority_target
                return

        # 2. YENİ HEDEFLEME MANTIĞI
        from logic.minion_inheritance import combat_stats
        m_range_mult = combat_stats(self.owner).get("minionRange", 1.0)
        leash_dist = 800 * m_range_mult
        
        if dist_to_owner > leash_dist:
            self.target = None
            return

        self.target = None
        pri1_target = None
        pri1_dist_sq = float('inf')
        closest_target = None
        closest_dist_sq = float('inf')
        cone_target = None
        best_angle_diff = math.pi
        p_angle = getattr(self.owner, "facing_angle", 0)
        
        for e in game.iter_enemies_near(self.owner.x, self.owner.y, 700 * m_range_mult):
            if not e.dead and not e.is_trap:
                dx = e.x - self.owner.x
                dy = e.y - self.owner.y
                dist_sq = dx * dx + dy * dy
                if dist_sq < closest_dist_sq:
                    closest_dist_sq = dist_sq
                    closest_target = e
                if dist_sq < 200 * 200 and dist_sq < pri1_dist_sq:
                    pri1_dist_sq = dist_sq
                    pri1_target = e

                angle_to_e = math.atan2(dy, dx)
                diff = abs((angle_to_e - p_angle + math.pi) % (2 * math.pi) - math.pi)
                if diff < best_angle_diff and diff < math.radians(45):
                    best_angle_diff = diff
                    cone_target = e

        if pri1_target:
            self.target = pri1_target
            return
        self.target = cone_target or closest_target

    def attack(self, game):
        if not self.target or self.is_recharging: return
        
        from logic.minion_inheritance import combat_stats
        stats = combat_stats(self.owner)
        damage = stats.get("minionDamage", 0)
        total_mult = max(0, 1+damage+stats.get("minionPhysDmgMult", 0))
        conditional = stats.get("minionConditionalMult", 1)
        element = stats.get("minionElementDmgMult", 0)
        fire_mult = max(0, 1+damage+element+stats.get("minionFireDmgMult", 0))
        frost_mult = max(0, 1+damage+element+stats.get("minionFrostDmgMult", 0))

        # BEASTMASTER BONUS (SPIRIT TAMER)
        # Eğer Ruh Terbiyecisi değilse, minyonlar çok daha güçsüz olur (Nerf Artırıldı)
        eff_mult = 1.0
        # Drone eşya affix'inden gelir (pet değil); Beastmaster dışı sınıf
        # cezasına tabi tutulursa affix pratikte yine ölü kalır.
        if self.type != "drone" and self.owner and getattr(self.owner, 'class_id', '') != 'beastmaster':
            eff_mult = 0.15
            
        # Difficulty mitigation is applied once by Enemy.take_damage.
            
        flat_dmg = stats.get("minionPhysDmgFlat", 0)
        final_dmg_base = ((self.base_dmg + flat_dmg) * total_mult) * eff_mult * conditional
        
        # Yeni Mermi Statları (Mermi sayısı, sekiş, deliş)
        # Terbiyeci Sopası silahı da hesaba katılır
        proj_count = max(1, int(stats.get("minionProjectileCount", 1)))

        if self.owner.stats.get('treeSingleShot', 0): proj_count = 1
        # Çoklu atış hasar cezası (%15 hasar kaybı per ekstra mermi, min %30)
        penalty = max(0.3, 1.0 - (proj_count - 1) * 0.15)
        final_dmg_base *= penalty
        
        bounce = int(stats.get("minionBounce", 0))
        pierce = int(stats.get("minionPierce", 0))
        
        if self.owner.stats.get('treeSingleShot', 0): bounce = pierce = 0
        # Kritik Şans
        # minionCrit (Vahşi Bağı kartı + pet itemleri) hiçbir yerde okunmuyordu (P3)
        crit_chance = min(1, max(0, .05 + stats.get("minionCrit", 0)))
        is_crit = not self.owner.stats.get('treeNoCrit', 0) and random.random() < crit_chance
        # Krit tabanı oyuncuyla aynı (2.0) olacak şekilde hizalandı
        crit_mult = 2+min(1.5, max(-1, stats.get("minionCritDmg", 0)))
        final_dmg = final_dmg_base * crit_mult if is_crit else final_dmg_base

        from entities.projectile import Projectile
        angle_to_target = math.atan2(self.target.y - self.y, self.target.x - self.x)
        
        # Çoklu Atış Yayılımı
        spread = math.radians(max(1, 14+stats.get("spreadAngle", 0)))
        start_angle = angle_to_target - (spread * (proj_count - 1) / 2)
        
        for i in range(proj_count):
            angle = start_angle + (i * spread)
            vx, vy = math.cos(angle) * 12, math.sin(angle) * 12
            
            p_type = 'katana' if self.type == "wolf" else 'fire'
            
            # Wolf için kısa ömürlü (Katana), Dragon için uzun ömürlü (Mermi)
            # Menzil statı hem Wolf (Slash mesafesi) hem Dragon (Mermi mesafesi) için çalışır
            m_range_mult = stats.get("minionRange", 1.0)
            if self.type == "wolf":
                lifetime = int(45 * m_range_mult + stats.get("minionExtraRange", 0)/12) # Base 45 frame (~540 birim)
            else:
                lifetime = int(180 * m_range_mult + stats.get("minionExtraRange", 0)/12) # Base 180 frame
            
            # AOE Hesabı (Dragon mermileri varsayılan olarak biraz alan hasarı verir)
            aoe_stat = self.owner.stats.get("aoe", 1.0)
            final_aoe = 0
            if self.type == "dragon" or (getattr(self.owner, "has_minion_inheritance", False) and aoe_stat > 1):
                final_aoe = 40 * aoe_stat
            
            proj = Projectile(game.entity_id_counter, self.x, self.y, vx, vy, 
                              final_dmg, bounce=bounce, pierce=pierce, 
                              p_type=p_type, aoe=final_aoe, lifetime=lifetime)
            proj.is_crit = is_crit
            proj.is_minion_proj = True
            proj.hit_crit_mult = crit_mult if is_crit else 1
            proj.dot_mult = max(0, 1+stats.get("minionDotDmgMult", 0))
            proj.bounce_dmg_mult = 1.3 if getattr(self.owner, "has_minion_inheritance", False) and getattr(self.owner, "has_ricochet_master", False) else 1.0
            
            # Elemental Statlar (Poison vb.)
            proj.poison_dps = stats.get("minionPoisonDpsFlat", 0) * max(0, 1+damage+element) * conditional * eff_mult
            proj.fire_dmg = stats.get("minionFireDmgFlat", 0) * fire_mult * conditional * eff_mult
            proj.frost_dmg = stats.get("minionFrostDmgFlat", 0) * frost_mult * conditional * eff_mult
            if self.owner.stats.get('treeFireOnly', 0) or getattr(self.owner, 'has_furnace', False):
                proj.damage_type = 'fire'
                proj.poison_dps = proj.frost_dmg = 0
                converted_mult = fire_mult
                if self.owner.stats.get('treeFireOnly', 0) and not getattr(self.owner, 'has_minion_inheritance', False):
                    converted_mult += self.owner.stats.get('fireDmgMult', 0)
                proj.dmg = (self.base_dmg+flat_dmg)*max(0, converted_mult)*eff_mult*conditional*penalty*(crit_mult if is_crit else 1)
            elif self.type == 'dragon':
                proj.damage_type = 'fire'
                proj.dmg = (self.base_dmg+flat_dmg)*fire_mult*eff_mult*conditional*penalty*(crit_mult if is_crit else 1)

            game.projectiles.append(proj)
            game.entity_id_counter += 1
            
        if getattr(self.owner, "has_minion_inheritance", False) and stats.get('shockwave', 0) > 0:
            for nearby in list(game.iter_enemies_near(self.x, self.y, 90)):
                if not nearby.dead and not nearby.is_trap and (nearby.x-self.x)**2+(nearby.y-self.y)**2 <= 90**2:
                    nearby.take_damage(stats['shockwave'], game, from_player=True, is_secondary=True,
                                       damage_type='fire' if self.owner.stats.get('treeFireOnly', 0) else 'physical')
            game.add_event('shockwave', self.x, self.y, radius=90, color=self.color, timer=.25)

        # Görsel Efekt
        if self.type == "wolf":
            game.add_event("slash", self.target.x, self.target.y, timer=0.2)
        else:
            # Dragon için küçük ateş patlaması (Ateş mermisi olduğunu belli eder)
            game.add_event("explosion", self.target.x, self.target.y, radius=30, color=(231, 76, 60), timer=0.15)
        
        game.add_event("damage_text", self.target.x, self.target.y - 20, value=int(final_dmg), color=self.color, timer=0.5, is_crit=is_crit)

    def take_damage(self, amount, game, *args, **kwargs):
        # MİNYONLAR ARTIK HASAR ALMAZ (Ölümsüzlük Aktif)
        return


    def draw(self, screen, camera_x, camera_y):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        # Görünürlük (Recharging iken şeffaf)
        alpha = 100 if self.is_recharging else 255
        
        # Minion Çemberi
        s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (self.radius, self.radius), self.radius)
        # Gözler
        eye_color = (255, 255, 255, alpha)
        pygame.draw.circle(s, eye_color, (self.radius + 6, self.radius - 2), 3)
        pygame.draw.circle(s, eye_color, (self.radius - 6, self.radius - 2), 3)
        # Highlight/Glow
        pygame.draw.circle(s, (255, 255, 255, alpha), (self.radius, self.radius), self.radius, 1)
        
        screen.blit(s, (draw_x - self.radius, draw_y - self.radius))
