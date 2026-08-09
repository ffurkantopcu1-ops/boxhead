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
        
        self.dead = False
        self.is_recharging = False
        self.recharge_timer = 0
        # minionMaxHp ÇARPAN, minionMaxHpFlat DÜZ can (F3): eskiden ikisi de tek
        # anahtarda toplanıp 100 ile çarpılıyordu (851 -> 85.100 can).
        hp_mult = owner.stats.get("minionMaxHp", 1.0) if owner else 1.0
        hp_flat = owner.stats.get("minionMaxHpFlat", 0) if owner else 0
        self.max_hp = max(1.0, 100 * hp_mult + hp_flat)
        self.hp = self.max_hp
        self.armor = owner.stats.get("minionArmor", 0) if owner else 0
        
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

        # Pet İmparatoru evrimi (wind_minions): minyonlar %40 daha hızlı hareket
        # eder ve %30 daha sık saldırır.
        # DİKKAT: self.speed / self.attack_cooldown'a KALICI çarpan uygulanmaz.
        # Bu değerler __init__'te bir kez kuruluyor; her karede çarpmak onları
        # üstel olarak bozar, "bir kez uygula" bayrağı ise evrim öncesi doğan
        # minyonlarda ya da stat yeniden hesaplamasında tutarsız kalır.
        # Bunun yerine çarpan KULLANIM ANINDA uygulanır (idempotent).
        wind = getattr(self.owner, 'evolution_passive', '') == 'wind_minions'
        move_speed = self.speed * (1.4 if wind else 1.0)


        if self.lifetime is not None:
            self.lifetime -= dt
            if self.lifetime <= 0:
                self.hp = 0
                
        # 0. RECHARGE KONTROLÜ: Minyon canı biterse 5 sn devre dışı kalır,
        # sonra yarı canla döner (kalıcı ölümsüzlük EHP'yi tanımsız yapıyordu, F5)
        if self.is_recharging:
            self.recharge_timer -= dt
            if self.recharge_timer <= 0:
                self.is_recharging = False
                self.hp = self.max_hp * 0.5
        elif self.hp <= 0:
            self.is_recharging = True
            self.recharge_timer = 5.0

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
            
        # CAN YERİLEME (Oyuncu regenine bağlı)
        # regen -999 (Berserker Öfkesi / Lanetli Kan) minyonları sürekli
        # is_recharging'e kilitliyordu; negatif regen minyona yansımaz (H13)
        p_regen = max(0, self.owner.stats.get("regen", 0))
        self.hp = min(self.max_hp, self.hp + dt * (2 + p_regen * 0.5))
            
        # 2. TOXIC AURA (Alan Hasarı)
        self.aura_timer += dt
        if self.aura_timer >= 1.0: # Her saniye
            self.aura_timer = 0
            aura_dmg = self.owner.stats.get("toxicAura", 0)
            if aura_dmg > 0:
                for e in game.iter_enemies_near(self.x, self.y, 150):
                    dx = e.x - self.x
                    dy = e.y - self.y
                    if not e.dead and dx * dx + dy * dy < 150 * 150:
                        # minion_kills görevi: bayrak yalnızca bu çağrı boyunca
                        # açık (bkz. entities/projectile.py -> on_hit)
                        e.last_hit_by_minion = True
                        try:
                            e.take_damage(aura_dmg, game, from_player=True)
                            vfx.hit(game, e.x, e.y, 'poison')
                        finally:
                            e.last_hit_by_minion = False
                        game.add_event("damage_text", e.x, e.y - 10, value=aura_dmg, color=(46, 204, 113), scale=0.6)
            
        # 3. HEDEF BUL (En yakın düşman)
        self.find_target(game)
        
        # 3. SALDIRI
        current_time = pygame.time.get_ticks()
        
        # Attack Speed hesaplaması
        # minionRate her karede taze okunur (bkz. __init__ notu); böylece
        # dalga ortasında alınan aura/skill mevcut sürüye de işler.
        rate_mult = max(0.1, self.owner.stats.get("minionRate", 1.0))
        self.attack_cooldown = self.base_cd / rate_mult
        eff_cooldown = self.attack_cooldown / (1.0 + self.owner.stats.get("minionAttackSpeed", 0))
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
        m_range_mult = self.owner.stats.get("minionRange", 1.0)
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
        
        # --- STAT MİRASI (Minyon Statları) ---
        minion_dmg_mult = self.owner.stats.get("minionDamage", 0.0)
        minion_phys_mult = self.owner.stats.get("minionPhysDmgMult", 0)
        minion_fire_mult = self.owner.stats.get("minionFireDmgMult", 0)
        minion_frost_mult = self.owner.stats.get("minionFrostDmgMult", 0)
        
        total_mult = 1.0 + minion_dmg_mult + minion_phys_mult + minion_fire_mult + minion_frost_mult
        
        # BEASTMASTER BONUS (SPIRIT TAMER)
        # Eğer Ruh Terbiyecisi değilse, minyonlar çok daha güçsüz olur (Nerf Artırıldı)
        eff_mult = 1.0
        # Drone eşya affix'inden gelir (pet değil); Beastmaster dışı sınıf
        # cezasına tabi tutulursa affix pratikte yine ölü kalır.
        if self.type != "drone" and self.owner and getattr(self.owner, 'class_id', '') != 'beastmaster':
            eff_mult = 0.15
            
        # IMPOSSIBLE ZORLUK CEZASI (%50 Hasar Kaybı)
        if game.wave.get("current_diff") == "Impossible":
            eff_mult *= 0.5
            
        flat_dmg = self.owner.stats.get("minionPhysDmgFlat", 0)
        final_dmg_base = ((self.base_dmg * total_mult) + flat_dmg) * eff_mult
        
        # Yeni Mermi Statları (Mermi sayısı, sekiş, deliş)
        # Terbiyeci Sopası silahı da hesaba katılır
        local_stats = self.owner.inv_manager.get_item_local_stats("weapon") if getattr(self.owner, "inv_manager", None) else {}
        proj_count = int(self.owner.stats.get("minionProjectileCount", 1)) + int(local_stats.get("projectileCount", 0))
        
        # Çoklu atış hasar cezası (%15 hasar kaybı per ekstra mermi, min %30)
        penalty = max(0.3, 1.0 - (proj_count - 1) * 0.15)
        final_dmg_base *= penalty
        
        bounce = int(self.owner.stats.get("minionBounce", 0)) + int(local_stats.get("bounce", 0))
        pierce = int(self.owner.stats.get("minionPierce", 0)) + int(local_stats.get("pierce", 0))
        
        # Kritik Şans
        # minionCrit (Vahşi Bağı kartı + pet itemleri) hiçbir yerde okunmuyordu (P3)
        crit_chance = self.owner.stats.get("critChance", 0.05) + self.owner.stats.get("minionCrit", 0)
        is_crit = random.random() < crit_chance
        # Krit tabanı oyuncuyla aynı (2.0) olacak şekilde hizalandı
        final_dmg = final_dmg_base * (2.0 + self.owner.stats.get("critDmg", 0)) if is_crit else final_dmg_base

        from entities.projectile import Projectile
        angle_to_target = math.atan2(self.target.y - self.y, self.target.x - self.x)
        
        # Çoklu Atış Yayılımı
        spread = 0.25
        start_angle = angle_to_target - (spread * (proj_count - 1) / 2)
        
        for i in range(proj_count):
            angle = start_angle + (i * spread)
            vx, vy = math.cos(angle) * 12, math.sin(angle) * 12
            
            p_type = 'katana' if self.type == "wolf" else 'fire'
            
            # Wolf için kısa ömürlü (Katana), Dragon için uzun ömürlü (Mermi)
            # Menzil statı hem Wolf (Slash mesafesi) hem Dragon (Mermi mesafesi) için çalışır
            m_range_mult = self.owner.stats.get("minionRange", 1.0)
            if self.type == "wolf":
                lifetime = int(45 * m_range_mult) # Base 45 frame (~540 birim)
            else:
                lifetime = int(180 * m_range_mult) # Base 180 frame
            
            # AOE Hesabı (Dragon mermileri varsayılan olarak biraz alan hasarı verir)
            aoe_stat = self.owner.stats.get("aoe", 1.0)
            final_aoe = 0
            if self.type == "dragon":
                # Dragon mermileri 40 base AOE + item bonusları alır
                final_aoe = (40 + self.owner.stats.get("minionFireDmgFlat", 0)) * aoe_stat
            
            proj = Projectile(game.entity_id_counter, self.x, self.y, vx, vy, 
                              final_dmg, bounce=bounce, pierce=pierce, 
                              p_type=p_type, aoe=final_aoe, lifetime=lifetime)
            proj.is_crit = is_crit
            proj.is_minion_proj = True
            
            # Elemental Statlar (Poison vb.)
            proj.poison_dps = self.owner.stats.get("minionPoisonDpsFlat", 0) * total_mult
            proj.fire_dmg = self.owner.stats.get("minionFireDmgFlat", 0) * total_mult
            proj.frost_dmg = self.owner.stats.get("minionFrostDmgFlat", 0) * total_mult
            
            game.projectiles.append(proj)
            game.entity_id_counter += 1
            
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
