import pygame
import math
import random
import time

class Enemy:
    def __init__(self, id, x, y, game, type="normal", wave_level=1):
        self.id = id
        xp_mult = min(15.0, 1.1 ** wave_level)
        self.x = x
        self.y = y
        self.type = type
        self.radius = 24
        
        # --- BASE STATS (Initialize first!) ---
        # --- ZORLUK ÖLÇEKLENDİRMESİ ---
        diff_name = game.wave.get("current_diff", "Normal")
        
        # Step-based Wave Scaling (Her 10 wave'de bir boss sonrası zorlaşır)
        step_level = (wave_level - 1) // 10
        wave_scale = (1.35 ** step_level) * (1.0 + wave_level * 0.05)
        
        self.max_hp = 200 * wave_scale
        self.hp = self.max_hp
        self.dmg = 10 * wave_scale
        self.speed = 3.5 # Hız artık wave başına artmıyor (GDD Talebi)
        
        # Zırh Sistemi (Zırh da her 10 wave'de bir artar)
        self.armor = 5 * step_level
        self.xp_reward = 20 * xp_mult
        self.color = (231, 76, 60) # Standart Kırmızı
        
        self.dead = False
        self.is_trap = False
        self.speed_mod = 1.0 # Çevresel hız çarpanı
        
        # --- STATUS EFFECTS ---
        from logic.status_effects import StatusEffectManager
        self.effect_manager = StatusEffectManager()
        self.speed_mod = 1.0
        self.is_silenced = False
        self.is_stunned = False
        self.base_speed = self.speed
        
        # --- TYPE SCALING (Boss & Elite) ---
        if self.type == "elite":
            self.max_hp *= 5
            self.hp = self.max_hp
            self.speed *= 0.8
            self.radius *= 1.5
            self.dmg *= 2
            self.color = (192, 57, 43) # Koyu Kırmızı
            self.xp_reward *= 3
        elif self.type == "boss":
            self.max_hp *= 30
            self.hp = self.max_hp
            self.speed *= 0.6
            self.radius *= 3.0
            self.dmg *= 5
            self.color = (241, 196, 15) # Altın
            self.xp_reward *= 10
        elif self.type == "barrel":
            self.max_hp = 150 * wave_scale
            self.hp = self.max_hp
            self.speed = 2.2 # Hız sabitlendi
            self.radius = 24
            self.dmg = 25 * wave_scale
            self.color = (139, 69, 19) # Kahverengi
            self.is_trap = False
            self.xp_reward = 35 * xp_mult
            # Dash Ayarları
            self.dash_cooldown = random.uniform(2.0, 3.0)
            self.dash_timer = self.dash_cooldown
            self.is_dashing = False
            self.dash_duration = 0.6
            self.dash_speed_mult = 5.5
        elif self.type == "toxic_pit":
            # OKÇU DÜŞMAN (Eski Toksik Çukur)
            self.max_hp = 120 * wave_scale
            self.hp = self.max_hp
            self.speed = 1.8 # Hız sabitlendi
            self.radius = 24
            self.dmg = 15 * wave_scale
            self.color = (46, 204, 113) # Yeşil
            self.is_trap = False
            self.xp_reward = 25 * xp_mult
            # Okçu Ayarları
            self.shoot_cooldown = 2.0
            self.shoot_timer = 0
        elif self.type == "lava_pit":
            # Yerinde Duran Tehlike (Tuzak: Ölümsüz ve Hareketsiz)
            self.max_hp = 999999
            self.hp = 999999
            self.speed = 0
            self.radius = 60
            self.dmg = 45
            self.color = (211, 84, 0) # Turuncu
            self.is_trap = True
            self.xp_reward = 0
            self.base_speed = 0 # Kesinlikle durmalı

        elif self.type == "frost_crawler":
            self.max_hp = 80 * wave_scale
            self.hp = self.max_hp
            self.speed = 1.8 + min(wave_level * 0.04, 1.5)
            self.dmg = 8 * wave_scale
            self.color = (100, 200, 235)    # Buz Mavisi
            self.xp_reward = 20 * xp_mult

        elif self.type == "kamikaze":
            self.max_hp = 60 * wave_scale
            self.hp = self.max_hp
            self.speed = 5.0 + min(wave_level * 0.12, 3.0)
            self.dmg = 40 * wave_scale
            self.color = (230, 140, 30)     # Koyu Turuncu
            self.xp_reward = 25 * xp_mult
            self.explode_timer = -1.0       # <0 = henüz aktif değil
            self.has_exploded = False

        elif self.type == "shieldbearer":
            self.max_hp = 200 * wave_scale
            self.hp = self.max_hp
            self.speed = 1.5 + min(wave_level * 0.03, 1.0)
            self.radius = 28
            self.dmg = 20 * wave_scale
            self.color = (160, 160, 170)    # Gri
            self.xp_reward = 40 * xp_mult

        elif self.type == "swarm_bat":
            self.max_hp = 20 * wave_scale
            self.hp = self.max_hp
            self.speed = 3.0 + min(wave_level * 0.08, 2.0)
            self.radius = 12
            self.dmg = 5 * wave_scale
            self.color = (30, 20, 40)       # Siyah-Mor
            self.xp_reward = 8 * xp_mult
            # Orbit hareketi için faz açısı
            self.orbit_phase = random.uniform(0, math.pi * 2)

        elif self.type == "fire_shaman":
            self.max_hp = 150 * wave_scale
            self.hp = self.max_hp
            self.speed = 1.2                # Neredeyse durur
            self.dmg = 25 * wave_scale
            self.color = (220, 80, 20)      # Ateş Kırmızısı
            self.xp_reward = 50 * xp_mult
            self.cast_timer = 2.5           # 2.5 sn bekleme
            self.warning_active = False
            self.warning_timer = 0.0
            self.warning_x = 0.0
            self.warning_y = 0.0

        elif self.type == "magnetar":
            self.max_hp = 120 * wave_scale
            self.hp = self.max_hp
            self.speed = 1.6
            self.dmg = 12 * wave_scale
            self.color = (120, 80, 200)     # Mor-Mavi
            self.radius = 26
            self.xp_reward = 35 * xp_mult
            self.magnet_radius = 300        # Mermi saptırma alanı

        elif self.type == "pack_leader":
            self.max_hp = 300 * wave_scale
            self.hp = self.max_hp
            self.speed = 2.0 + min(wave_level * 0.04, 1.2)
            self.radius = 30
            self.dmg = 18 * wave_scale
            self.color = (220, 180, 20)     # Altın
            self.xp_reward = 80 * xp_mult
            self.buff_radius = 400

        elif self.type == "venom_spider":
            self.max_hp = 90 * wave_scale
            self.hp = self.max_hp
            self.speed = 2.2 + min(wave_level * 0.05, 1.5)
            self.radius = 18
            self.dmg = 10 * wave_scale
            self.color = (50, 160, 50)      # Koyu Yeşil
            self.xp_reward = 30 * xp_mult
            self.shoot_cooldown = 3.0
            self.shoot_timer = random.uniform(1.0, 3.0)

        # --- WAVE 30+ YENİ DÜŞMANLAR (ANTI-AFK) ---
        elif self.type == "void_walker":
            self.max_hp = 180 * wave_scale
            self.hp = self.max_hp
            self.speed = 3.5 + min(wave_level * 0.05, 1.5)
            self.radius = 22
            self.dmg = 60 * wave_scale
            self.color = (142, 68, 173)     # Mor
            self.xp_reward = 100 * xp_mult
            self.tp_cooldown = random.uniform(4.0, 6.0)
            self.tp_timer = self.tp_cooldown
            self.tp_warning = False
            self.tp_target_x = 0
            self.tp_target_y = 0

        elif self.type == "juggernaut":
            self.max_hp = 1000 * wave_scale
            self.hp = self.max_hp
            self.speed = 0.8                # Çok yavaş
            self.radius = 45
            self.dmg = 40 * wave_scale
            self.color = (192, 57, 43)      # Koyu Kırmızı / Bordo
            self.xp_reward = 250 * xp_mult
            self.armor += 150               # Ekstra Zırh
            self.lava_cooldown = 5.0
            self.lava_timer = self.lava_cooldown
            self.is_pillar = True           # İttirmelere karşı bağışıklık

        elif self.type == "swarm_lord":
            self.max_hp = 600 * wave_scale
            self.hp = self.max_hp
            self.speed = 1.5
            self.radius = 35
            self.dmg = 20 * wave_scale
            self.color = (41, 128, 185)     # Okyanus Mavisi
            self.xp_reward = 200 * xp_mult
            self.spawn_cooldown = 3.0
            self.spawn_timer = self.spawn_cooldown

        # --- YENİ MEKANİKLİ DÜŞMANLAR ---
        elif self.type == "splitting_slime":
            self.max_hp = 400 * wave_scale
            self.hp = self.max_hp
            self.speed = 1.0
            self.radius = 40
            self.dmg = 30 * wave_scale
            self.color = (46, 204, 113) # Açık Yeşil
            self.xp_reward = 100 * xp_mult
            self.slime_tier = 3 # 3 -> 2 -> 1 (ölünce bölünür)
        elif self.type == "splitting_slime_medium":
            self.max_hp = 150 * wave_scale
            self.hp = self.max_hp
            self.speed = 1.8
            self.radius = 25
            self.dmg = 15 * wave_scale
            self.color = (46, 204, 113)
            self.xp_reward = 40 * xp_mult
            self.slime_tier = 2
        elif self.type == "splitting_slime_small":
            self.max_hp = 50 * wave_scale
            self.hp = self.max_hp
            self.speed = 3.0
            self.radius = 15
            self.dmg = 5 * wave_scale
            self.color = (46, 204, 113)
            self.xp_reward = 15 * xp_mult
            self.slime_tier = 1

        elif self.type == "necromancer":
            self.max_hp = 250 * wave_scale
            self.hp = self.max_hp
            self.speed = 2.5
            self.radius = 24
            self.dmg = 10 * wave_scale
            self.color = (142, 68, 173) # Mor
            self.xp_reward = 150 * xp_mult
            self.spawn_cooldown = 4.0
            self.spawn_timer = self.spawn_cooldown

        elif self.type == "zombie":
            self.max_hp = 80 * wave_scale
            self.hp = self.max_hp
            self.speed = 1.2
            self.radius = 20
            self.dmg = 15 * wave_scale
            self.color = (127, 140, 141) # Gri/Ölü
            self.xp_reward = 0
            self.no_drop = True

        elif self.type == "loot_goblin":
            self.max_hp = 500 * wave_scale
            self.hp = self.max_hp
            self.speed = 4.5 + min(wave_level * 0.05, 1.5)
            self.radius = 20
            self.dmg = 0 # Hasar vermez
            self.color = (241, 196, 15) # Altın sarısı
            self.xp_reward = 500 * xp_mult
            self.escape_timer = 15.0 # 15 saniyede kaçar

        elif self.type == "burrowing_worm":
            self.max_hp = 200 * wave_scale
            self.hp = self.max_hp
            self.speed = 2.0 + min(wave_level * 0.04, 1.2)
            self.radius = 28
            self.dmg = 35 * wave_scale
            self.color = (211, 84, 0) # Turuncu/Kahverengi
            self.xp_reward = 80 * xp_mult
            self.is_underground = True
            self.is_invulnerable = True
            self.worm_timer = 5.0 # 5 saniye yer altı, 3 saniye yüzey

        elif self.type == "black_hole_caster":
            self.max_hp = 180 * wave_scale
            self.hp = self.max_hp
            self.speed = 1.8
            self.radius = 26
            self.dmg = 15 * wave_scale
            self.color = (44, 62, 80) # Koyu Mavi/Siyah
            self.xp_reward = 120 * xp_mult
            self.cast_cooldown = 6.0
            self.cast_timer = self.cast_cooldown

        self.base_max_hp = self.max_hp
        self.base_dmg = self.dmg
        self.base_speed = self.speed
        self.base_armor = getattr(self, 'armor', 0)
        self.apply_difficulty(diff_name)

    def apply_difficulty(self, diff_name):
        if diff_name == "Very Hard": diff_name = "Nightmare"
        
        diff_mults = {
            "Normal":    {"hp": 1.0,  "dmg": 1.0, "speed": 1.0, "armor": 1.0},
            "Hard":      {"hp": 5.0,  "dmg": 3.0, "speed": 1.0, "armor": 1.0},
            "Nightmare": {"hp": 20.0, "dmg": 7.0, "speed": 1.0, "armor": 2.0},
            "Impossible":{"hp": 100.0, "dmg": 20.0, "speed": 1.3, "armor": 5.0}
        }
        mult = diff_mults.get(diff_name, diff_mults["Normal"])
        
        ratio = self.hp / self.max_hp if getattr(self, "max_hp", 0) > 0 else 1.0
        self.max_hp = self.base_max_hp * mult["hp"]
        self.hp = self.max_hp * ratio
        self.dmg = self.base_dmg * mult["dmg"]
        self.speed = self.base_speed * mult["speed"]
        self.armor = self.base_armor * mult["armor"]

    def update(self, dt, game):
        if self.dead: return
        self.effect_manager.update(dt, self, game)
        
        # Target player
        p = game.players[game.local_player_id]
        dist = math.hypot(p.x - self.x, p.y - self.y)
        
        # Görünmezlik Kontrolü
        if p.is_invisible:
             # Eğer görünmezse rastgele küçük hareketler yap (Wander)
             self.x += random.uniform(-1, 1) * (self.speed * self.speed_mod) * dt * 20
             self.y += random.uniform(-1, 1) * (self.speed * self.speed_mod) * dt * 20
             return

        if dist > 5:
            # Doğrudan Takip (User Request: "direkt benim üstüme gelsin")
            angle = math.atan2(p.y - self.y, p.x - self.x)
            
            # --- DASH AI (BARELL / KAHVERENGİ) ---
            if self.type == "barrel":
                if not self.is_dashing:
                    self.dash_timer -= dt
                    if self.dash_timer <= 0 and dist < 2000:
                        self.is_dashing = True
                        self.dash_timer = self.dash_duration
                        self.dash_angle = angle
                    else:
                        # Normal Takip
                        offset = math.sin(game.entity_id_counter * 0.5 + time.time() * 2) * 0.2
                        final_angle = angle + offset
                        self.x += math.cos(final_angle) * self.speed * dt * 60
                        self.y += math.sin(final_angle) * self.speed * dt * 60
                else:
                    # Dash Hareket
                    self.dash_timer -= dt
                    self.x += math.cos(self.dash_angle) * (self.speed * self.dash_speed_mult) * dt * 60
                    self.y += math.sin(self.dash_angle) * (self.speed * self.dash_speed_mult) * dt * 60
                    
                    # Varil Çarpışması (Burst Hasar ve i-frame)
                    if dist < self.radius + p.radius:
                        if p.i_frame_timer <= 0:
                            p.take_damage(self.dmg * 2, force=False) # i-frame'e saygı duyar
                            self.is_dashing = False
                            self.dash_timer = self.dash_cooldown
                            # Geri sekme
                            self.x -= math.cos(self.dash_angle) * 50
                            self.y -= math.sin(self.dash_angle) * 50
                            
                    if self.dash_timer <= 0:
                        self.is_dashing = False
                        self.dash_timer = self.dash_cooldown
            
            # --- ARCHER AI (TOXIC_PIT / YEŞİL) ---
            elif self.type == "toxic_pit":
                # Buffed Range (2x)
                if dist > 700:
                    self.x += math.cos(angle) * self.speed * dt * 60
                    self.y += math.sin(angle) * self.speed * dt * 60
                elif dist < 500:
                    self.x -= math.cos(angle) * self.speed * dt * 60
                    self.y -= math.sin(angle) * self.speed * dt * 60
                
                # --- IMPOSSIBLE DASH FOR ARCHERS ---
                if game.wave["current_diff"] in ["Very Hard", "Impossible"]:
                    if not getattr(self, "is_dashing", False):
                        if not hasattr(self, "dash_timer_arch"): self.dash_timer_arch = 3.0
                        self.dash_timer_arch -= dt
                        if self.dash_timer_arch <= 0 and dist < 400:
                            self.is_dashing = True
                            self.dash_timer = 0.4 # Dash süresi
                            self.dash_angle = angle + math.pi # Geriye doğru dash
                            self.dash_timer_arch = 5.0 # Cooldown
                    
                self.shoot_timer -= dt
                if self.shoot_timer <= 0 and dist < 1200:
                    vx = math.cos(angle) * 10
                    vy = math.sin(angle) * 10
                    from entities.projectile import Projectile
                    game.projectiles.append(Projectile(game.entity_id_counter, self.x, self.y, vx, vy, self.dmg, is_hostile=True))
                    game.entity_id_counter += 1
                    self.shoot_timer = self.shoot_cooldown

            # --- BUZ YÜRÜYÜCÜSÜ ---
            elif self.type == "frost_crawler":
                # Normal takip — ölünce buz bulutu bırakmak kill_enemy'de yapılır
                offset = math.sin(self.id * 0.5 + time.time() * 2) * 0.3
                self.x += math.cos(angle + offset) * self.speed * dt * 60
                self.y += math.sin(angle + offset) * self.speed * dt * 60

            # --- KAMİKAZE ---
            elif self.type == "kamikaze":
                if not self.has_exploded:
                    if dist < 70 and self.explode_timer < 0:
                        self.explode_timer = 0.5  # Patlama geri sayımı başlat
                        # Titreme renk uyarısı
                        self.color = (255, 50, 50)
                    
                    if self.explode_timer > 0:
                        self.explode_timer -= dt
                        if self.explode_timer <= 0:
                            # PATLAMA! (Menzil Nerflendi: 60->50)
                            game.add_event("explosion", self.x, self.y, radius=50, color=(255, 100, 0), timer=0.4)
                            game.trigger_shake(20)
                            if math.hypot(p.x - self.x, p.y - self.y) < 50:
                                p.take_damage(self.dmg)
                            for e in game.enemies:
                                if not e.dead and not e.is_trap and e != self:
                                    if math.hypot(e.x - self.x, e.y - self.y) < 50:
                                        e.take_damage(self.dmg * 0.5, game)
                            self.has_exploded = True
                            self.hp = 0
                            self.dead = True
                            game.kill_enemy(self)
                            return
                    elif dist > 5:
                        # Yaklaşırken hızlan
                        speed_mult = 2.0 if dist < 200 else 1.0
                        self.x += math.cos(angle) * self.speed * speed_mult * dt * 60
                        self.y += math.sin(angle) * self.speed * speed_mult * dt * 60

            # --- KALKAN TAŞIYICI ---
            elif self.type == "shieldbearer":
                # Yavaş ama düz yaklaşım
                self.x += math.cos(angle) * self.speed * dt * 60
                self.y += math.sin(angle) * self.speed * dt * 60
                # take_damage override: açı kontrolü take_damage'de yapılır (flag: shield_angle)
                self.shield_angle = angle  # Şu an oyuncuya baktığı açı

            # --- SÜRÜ YARASASI ---
            elif self.type == "swarm_bat":
                # Orbit hareketi (oyuncunun etrafında çember çizer, yaklaşınca çarpar)
                self.orbit_phase += dt * 2.5
                orbit_r = max(40, dist - 30)
                target_x = p.x + math.cos(self.orbit_phase) * orbit_r
                target_y = p.y + math.sin(self.orbit_phase) * orbit_r
                dx = target_x - self.x
                dy = target_y - self.y
                d = math.hypot(dx, dy)
                if d > 1:
                    self.x += (dx / d) * self.speed * dt * 60
                    self.y += (dy / d) * self.speed * dt * 60

            # --- ATEŞ ŞAMANI ---
            elif self.type == "fire_shaman":
                # Yavaş yaklaşım (kamp yapar)
                if dist > 300:
                    self.x += math.cos(angle) * self.speed * dt * 60
                    self.y += math.sin(angle) * self.speed * dt * 60

                if self.warning_active:
                    self.warning_timer -= dt
                    # Zemin uyarısı göster
                    game.add_event("explosion", self.warning_x, self.warning_y,
                                   radius=80, color=(255, 60, 0, 80), timer=0.05)
                    if self.warning_timer <= 0:
                        # ATEŞ ÇAĞIR!
                        from entities.cloud import Cloud
                        game.entity_id_counter += 1
                        game.clouds.append(Cloud(game.entity_id_counter, self.warning_x, self.warning_y,
                                                  radius=80, duration=1.3,
                                                  fire_dmg=self.dmg))
                        game.trigger_shake(8)
                        self.warning_active = False
                        self.cast_timer = random.uniform(2.0, 3.5)
                else:
                    self.cast_timer -= dt
                    if self.cast_timer <= 0 and dist < 600:
                        self.warning_active = True
                        self.warning_timer = 1.0
                        self.warning_x = p.x + random.uniform(-30, 30)
                        self.warning_y = p.y + random.uniform(-30, 30)

            # --- MANYETİK ALAN ---
            elif self.type == "magnetar":
                # Normal yavaş takip
                self.x += math.cos(angle) * self.speed * dt * 60
                self.y += math.sin(angle) * self.speed * dt * 60
                # Mermi saptırması Projectile.update içinde kontrol edilir
                # Görsel halka efekti
                if random.random() < 0.05:
                    ring_angle = random.uniform(0, math.pi * 2)
                    game.add_event("explosion", 
                                   self.x + math.cos(ring_angle) * self.magnet_radius * 0.8,
                                   self.y + math.sin(ring_angle) * self.magnet_radius * 0.8,
                                   radius=15, color=(120, 80, 200), timer=0.15)

            # --- SÜRÜ LİDERİ ---
            elif self.type == "pack_leader":
                # Normal takip
                offset = math.sin(self.id * 0.3 + time.time()) * 0.2
                self.x += math.cos(angle + offset) * self.speed * dt * 60
                self.y += math.sin(angle + offset) * self.speed * dt * 60
                # Buff: Yakındaki düşmanlara hız ve hasar artışı
                for e in game.enemies:
                    if not e.dead and e != self and e.type not in ["pack_leader", "lava_pit"]:
                        if math.hypot(e.x - self.x, e.y - self.y) < self.buff_radius:
                            e.speed = min(e.base_speed * 1.3, e.speed + 0.01)
                            e.dmg = e.dmg  # dmg direkt değiştirmek yerine check bayrak kullanılabilir

            # --- ZEHİRLİ ÖRÜMCEK ---
            elif self.type == "venom_spider":
                if dist > 200:
                    self.x += math.cos(angle) * self.speed * dt * 60
                    self.y += math.sin(angle) * self.speed * dt * 60
                elif dist < 120:
                    # Hafif uzaklaş
                    self.x -= math.cos(angle) * self.speed * 0.5 * dt * 60
                    self.y -= math.sin(angle) * self.speed * 0.5 * dt * 60
                
                self.shoot_timer -= dt
                if self.shoot_timer <= 0 and dist < 500:
                    vx = math.cos(angle) * 9
                    vy = math.sin(angle) * 9
                    from entities.projectile import Projectile
                    proj = Projectile(game.entity_id_counter, self.x, self.y, vx, vy, self.dmg, is_hostile=True)
                    proj.poison_dps = 10.0  # Zehir özelliği
                    game.projectiles.append(proj)
                    game.entity_id_counter += 1
                    self.shoot_timer = self.shoot_cooldown

            # --- HİÇLİK GEZGİNİ (VOID WALKER) ---
            elif self.type == "void_walker":
                if self.tp_warning:
                    self.tp_timer -= dt
                    game.add_event("explosion", self.tp_target_x, self.tp_target_y, radius=self.radius, color=(142, 68, 173, 100), timer=0.05)
                    if self.tp_timer <= 0:
                        # Işınlanma gerçekleşiyor!
                        game.add_event("explosion", self.x, self.y, radius=self.radius, color=(142, 68, 173), timer=0.2)
                        self.x = self.tp_target_x
                        self.y = self.tp_target_y
                        game.add_event("explosion", self.x, self.y, radius=self.radius*2, color=(142, 68, 173), timer=0.3)
                        game.trigger_shake(10)
                        # Anlık Hasar (Eğer oyuncuya çok yakınsa)
                        if math.hypot(p.x - self.x, p.y - self.y) < self.radius*2:
                            p.take_damage(self.dmg)
                        self.tp_warning = False
                        self.tp_timer = self.tp_cooldown
                else:
                    self.tp_timer -= dt
                    # Normal yavaş takip
                    self.x += math.cos(angle) * self.speed * 0.5 * dt * 60
                    self.y += math.sin(angle) * self.speed * 0.5 * dt * 60
                    if self.tp_timer <= 1.0: # Işınlanmadan 1 sn önce uyarı
                        self.tp_warning = True
                        # Oyuncunun yanına veya arkasına ışınlanma noktası seç
                        offset_x = random.uniform(-50, 50)
                        offset_y = random.uniform(-50, 50)
                        self.tp_target_x = p.x + offset_x
                        self.tp_target_y = p.y + offset_y

            # --- YOK EDİCİ (JUGGERNAUT) ---
            elif self.type == "juggernaut":
                # Dümdüz yavaşça takip et (Separation'dan bağışık - is_pillar)
                self.x += math.cos(angle) * self.speed * dt * 60
                self.y += math.sin(angle) * self.speed * dt * 60
                
                # Belirli aralıklarla geçtiği yere Lav Çukuru bırakır
                self.lava_timer -= dt
                if self.lava_timer <= 0:
                    game.entity_id_counter += 1
                    # Spawn new lava pit with high wave level for high damage
                    lava = Enemy(game.entity_id_counter, self.x, self.y, game, type="lava_pit", wave_level=game.wave["level"])
                    game.enemies.append(lava)
                    self.lava_timer = self.lava_cooldown

            # --- SÜRÜ EFENDİSİ (SWARM LORD) ---
            elif self.type == "swarm_lord":
                # Oyuncudan uzakta durmaya çalış (Kite)
                if dist < 400:
                    self.x -= math.cos(angle) * self.speed * dt * 60
                    self.y -= math.sin(angle) * self.speed * dt * 60
                elif dist > 600:
                    self.x += math.cos(angle) * self.speed * dt * 60
                    self.y += math.sin(angle) * self.speed * dt * 60
                
                # Sürekli Sürü Yarasası çağırır
                self.spawn_timer -= dt
                if self.spawn_timer <= 0:
                    game.entity_id_counter += 1
                    spawn_type = "swarm_bat" if random.random() > 0.3 else "kamikaze"
                    minion = Enemy(game.entity_id_counter, self.x + random.uniform(-40, 40), self.y + random.uniform(-40, 40), game, type=spawn_type, wave_level=game.wave["level"])
                    game.enemies.append(minion)
                    game.add_event("explosion", minion.x, minion.y, radius=20, color=(41, 128, 185), timer=0.2)
                    self.spawn_timer = self.spawn_cooldown

            # --- NEKROMANSER ---
            elif self.type == "necromancer":
                # Kiting (Kaçma) ve zombi çağırma
                if dist < 400:
                    self.x -= math.cos(angle) * self.speed * dt * 60
                    self.y -= math.sin(angle) * self.speed * dt * 60
                elif dist > 600:
                    self.x += math.cos(angle) * self.speed * dt * 60
                    self.y += math.sin(angle) * self.speed * dt * 60
                
                self.spawn_timer -= dt
                if self.spawn_timer <= 0:
                    game.entity_id_counter += 1
                    zombie = Enemy(game.entity_id_counter, self.x + random.uniform(-30, 30), self.y + random.uniform(-30, 30), game, type="zombie", wave_level=game.wave["level"])
                    game.enemies.append(zombie)
                    game.add_event("explosion", zombie.x, zombie.y, radius=20, color=(127, 140, 141), timer=0.2)
                    self.spawn_timer = self.spawn_cooldown

            # --- GANİMET GOBLİN'İ (LOOT GOBLIN) ---
            elif self.type == "loot_goblin":
                # Sürekli oyuncunun tersi yönünde kaçar
                self.x -= math.cos(angle) * self.speed * dt * 60
                self.y -= math.sin(angle) * self.speed * dt * 60
                self.escape_timer -= dt
                if self.escape_timer <= 0:
                    # Kaçmayı başardı, hasar almadan kaybolur
                    game.add_event("damage_text", self.x, self.y, value="KAÇTI!", color=(241, 196, 15), timer=1.0)
                    game.add_event("explosion", self.x, self.y, radius=30, color=(241, 196, 15), timer=0.3)
                    self.dead = True # kill_enemy çağrılmıyor, loot düşmüyor

            # --- YER ALTI SOLUCANI (BURROWING WORM) ---
            elif self.type == "burrowing_worm":
                self.worm_timer -= dt
                if self.is_underground:
                    # Yer altındayken oyuncuya daha hızlı yaklaş
                    self.x += math.cos(angle) * self.speed * 1.5 * dt * 60
                    self.y += math.sin(angle) * self.speed * 1.5 * dt * 60
                    if self.worm_timer <= 0:
                        # Yüzeye çık
                        self.is_underground = False
                        self.is_invulnerable = False
                        self.worm_timer = 3.0 # 3 saniye yüzeyde kalır
                        game.add_event("explosion", self.x, self.y, radius=40, color=(211, 84, 0), timer=0.4)
                        game.trigger_shake(10)
                        if math.hypot(p.x - self.x, p.y - self.y) < 50:
                            p.take_damage(self.dmg)
                else:
                    # Yüzeydeyken çok yavaş hareket et
                    self.x += math.cos(angle) * self.speed * 0.2 * dt * 60
                    self.y += math.sin(angle) * self.speed * 0.2 * dt * 60
                    if self.worm_timer <= 0:
                        # Tekrar yer altına gir
                        self.is_underground = True
                        self.is_invulnerable = True
                        self.worm_timer = 5.0
                        game.add_event("explosion", self.x, self.y, radius=20, color=(100, 100, 100), timer=0.2)

            # --- HİÇLİK BÜYÜCÜSÜ (BLACK HOLE CASTER) ---
            elif self.type == "black_hole_caster":
                # Kiting
                if dist < 350:
                    self.x -= math.cos(angle) * self.speed * dt * 60
                    self.y -= math.sin(angle) * self.speed * dt * 60
                elif dist > 500:
                    self.x += math.cos(angle) * self.speed * dt * 60
                    self.y += math.sin(angle) * self.speed * dt * 60
                
                self.cast_timer -= dt
                if self.cast_timer <= 0 and dist < 800:
                    from entities.cloud import Cloud
                    game.entity_id_counter += 1
                    # Oyuncunun olduğu yere (veya yakınına) bir karadelik oluştur
                    bh_x = p.x + random.uniform(-20, 20)
                    bh_y = p.y + random.uniform(-20, 20)
                    bh_cloud = Cloud(game.entity_id_counter, bh_x, bh_y, radius=120, duration=4.0, frost_dmg=0, is_black_hole=True)
                    bh_cloud.dmg = self.dmg
                    game.clouds.append(bh_cloud)
                    game.add_event("explosion", bh_x, bh_y, radius=120, color=(44, 62, 80, 150), timer=0.5)
                    self.cast_timer = self.cast_cooldown

            # --- STANDART AI ---
            else:
                offset = math.sin(self.id * 0.5 + time.time() * 2) * 0.2
                final_angle = angle + offset
                self.x += math.cos(final_angle) * self.speed * dt * 60
                self.y += math.sin(final_angle) * self.speed * dt * 60
            
        # Hasar ve Efekt Güncelleme
        # (self.effect_manager.update already called at start of update)
            
        # HASAR MANTIĞI
        # Saldırı menzilini biraz genişletiyoruz (radius + 10) çünkü kalabalık durumlarda yaratıklar birbirini ittiği için 
        # oyuncunun tam üstüne binemeyebiliyorlar, bu da hasar verememelerine sebep oluyordu.
        if dist < self.radius + p.radius + 10:
            # Temas Hasarı: Kullanıcı İsteği - AFK kalmayı önlemek için i-frame aşılır ve sürekli vurur
            p.take_damage(self.dmg * dt * 3, force=True)
            
        # Sınır dışına çıkmayı engelle (Map Boundaries)
        self.x = max(50, min(4950, self.x))
        self.y = max(50, min(4950, self.y))

    def apply_dot(self, eff_type, dps, duration, slow=0.0):
        from logic.status_effects import apply_burn, apply_slow
        if eff_type == 'fire' or eff_type == 'burn':
            apply_burn(self.effect_manager, duration, dps)
        elif eff_type == 'frost' or eff_type == 'slow':
            apply_slow(self.effect_manager, duration, slow if slow > 0 else 0.5)
        elif eff_type == 'poison':
            # Poison is just a type of DoT in new system, we can use a custom status if needed 
            # or just call apply_burn with green color (handled by StatusEffect color)
            from logic.status_effects import StatusEffect
            self.effect_manager.add_effect(StatusEffect("Poison", duration, dps=dps, color=(46, 204, 113)))


    def take_damage(self, amount, game, is_crit=False, is_dot=False, from_player=False):
        if self.dead: return
        if getattr(self, 'is_invulnerable', False): return
        # Lava pits remain invulnerable, pillars take damage.
        if getattr(self, 'is_trap', False) and self.type == "lava_pit": return
        
        # --- ZIRH HESABI ---
        player = game.players[game.local_player_id]
        p_stats = player.stats
        
        # Zırh Delme (Armor Pen) - Broken Stat
        armor_pen = p_stats.get("armorPen", 0)
        effective_armor = self.armor * (1.0 - min(1.0, armor_pen))
        
        # Hasar Azaltma Formülü: dmg * (100 / (100 + armor))
        damage_reduction = 100 / (100 + max(0, effective_armor))
        final_dmg = amount * damage_reduction

        # Impossible Zorlukta Oyuncu Hasarı Nerfi (%50)
        if game.wave.get("current_diff") == "Impossible":
            final_dmg *= 0.5
            
        # Double Edge (Çift Ağız) - Hasar vurunca kendine de hasar vur (DoT hariç)
        if not is_dot and from_player and getattr(player, "self_dmg_on_hit", 0.0) > 0:
            sd = player.max_hp * player.self_dmg_on_hit
            player.take_damage(sd, force=True, is_self_damage=True)
        
        # --- BOSS HASAR ÇARPANI (Broken Stat) ---
        if self.type == "boss":
            final_dmg *= (1.0 + p_stats.get("bossDmgMult", 0))
            
        # --- KILL STREAK HASAR (Momentum) ---
        # Her kombo başına +%X hasar (Örn: 10 combo * %5 = %50)
        streak_bonus = game.kill_streak * p_stats.get("killComboDmg", 0)
        final_dmg *= (1.0 + streak_bonus)
        
        # Minimum Hasar (Zırh çok yüksek olsa bile %5 vur)
        final_dmg = max(amount * 0.05, final_dmg)
        
        # --- KALKAN KORUMASI (Shieldbearer): Önden gelen hasar %80 azalır ---
        if self.type == "shieldbearer" and not is_dot:
            final_dmg *= 0.20
            
        self.hp -= final_dmg
        if hasattr(game, 'stats'):
            game.stats['total_damage_dealt'] += final_dmg

        # Görsel Hasar Text (Boş geçmeyelim)
        if not is_dot:
            game.add_event("damage_text", self.x, self.y - 20, value=int(final_dmg), color=(255, 100, 100), timer=0.5)
        
        # --- EXECUTION (İnfazcı) ---
        exec_threshold = p_stats.get("lowHpExec", 0)
        if exec_threshold > 0 and self.hp > 0:
            if (self.hp / self.max_hp) < exec_threshold:
                self.hp = 0
                game.add_event("damage_text", self.x, self.y - 40, value="EXECUTED!", color=(255, 0, 0), timer=0.8)

        # --- LIFESTEAL (Can Çalma) ---
        if p_stats.get("lifesteal", 0) > 0 and not is_dot and player.hp < player.max_hp and player.lifesteal_cooldown_timer <= 0:
            ls_perc = p_stats["lifesteal"]
            if game.wave.get("current_diff") == "Impossible":
                ls_perc *= 0.5 # Can çalma etkisi yarıya iner
            heal = final_dmg * ls_perc
            
            if getattr(player, "class_id", "") == "bloodwalker":
                # Vampir (Bloodwalker) anında can çalar
                player.hp = min(player.max_hp, player.hp + heal)
            else:
                # Diğer sınıflar havuzda biriktirir (GDD 62) ve en fazla max_hp kadar biriktirebilir
                player.lifesteal_buffer = min(player.max_hp, player.lifesteal_buffer + heal)
                
            # AYNI ANDA ÇOKLU CAN ÇALMAYI ENGELLE (Sadece 1 hedeften can çalar)
            player.lifesteal_cooldown_timer = 0.2
            
        if self.hp <= 0:
            self.dead = True
            # --- BUZ YÜRÜYÜCÜSÜ Ölüm Bulutu ---
            if self.type == "frost_crawler":
                from entities.cloud import Cloud
                game.entity_id_counter += 1
                game.clouds.append(Cloud(game.entity_id_counter, self.x, self.y,
                                         radius=70, duration=2.0, frost_dmg=20))
                game.add_event("explosion", self.x, self.y, radius=70, color=(100, 200, 235), timer=0.3)
            game.kill_enemy(self)

            
    def draw(self, screen, camera_x, camera_y):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        # Ekranda değilse çizme
        if not (-self.radius*4 < draw_x < screen.get_width() + self.radius*4 and 
                -self.radius*4 < draw_y < screen.get_height() + self.radius*4):
            return

        time_val = time.time()
        pulse = math.sin(time_val * 10) * 2
        rotate_angle = time_val * 4 # Dönen şekiller için

        # --- PREMIUM GEOMETRIC DESIGNS (GDD 42) ---
        
        if self.type == "boss":
            # BOSS: Katmanlı Elmas ve Dış Halka
            # 1. Glow
            s = pygame.Surface((self.radius*4, self.radius*4), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, 40), (self.radius*2, self.radius*2), self.radius*1.5 + pulse*2)
            screen.blit(s, (draw_x - self.radius*2, draw_y - self.radius*2))
            
            # 2. Dönen Kare (Diamond)
            points = []
            for i in range(4):
                ang = rotate_angle + i * (math.pi/2)
                points.append((draw_x + math.cos(ang) * self.radius, draw_y + math.sin(ang) * self.radius))
            pygame.draw.polygon(screen, self.color, points)
            pygame.draw.polygon(screen, (255, 255, 255), points, 3)
            
            # 3. İç Çekirdek
            pygame.draw.circle(screen, (255, 255, 255), (int(draw_x), int(draw_y)), self.radius // 2)

        elif self.type == "elite":
            # ELITE: Altıgen (Hexagon)
            points = []
            for i in range(6):
                ang = i * (math.pi/3)
                points.append((draw_x + math.cos(ang) * (self.radius + pulse), draw_y + math.sin(ang) * (self.radius + pulse)))
            pygame.draw.polygon(screen, self.color, points)
            pygame.draw.polygon(screen, (255, 255, 255), points, 2)

        elif self.type == "swarm_bat":
            # BAT: Keskin Üçgen
            points = []
            for i in range(3):
                ang = self.orbit_phase + i * (2*math.pi/3)
                points.append((draw_x + math.cos(ang) * self.radius, draw_y + math.sin(ang) * self.radius))
            pygame.draw.polygon(screen, self.color, points)
            pygame.draw.polygon(screen, (255, 255, 255), points, 1)

        elif self.type == "kamikaze":
            # KAMIKAZE: Patlamaya hazır dikenli daire
            pygame.draw.circle(screen, self.color, (int(draw_x), int(draw_y)), int(self.radius + pulse))
            # Dikenler
            for i in range(8):
                ang = rotate_angle * 2 + i * (math.pi/4)
                pygame.draw.line(screen, (255, 255, 255), 
                                 (draw_x, draw_y), 
                                 (draw_x + math.cos(ang) * (self.radius + 10), draw_y + math.sin(ang) * (self.radius + 10)), 2)

        elif self.type == "shieldbearer":
            # SHIELDBEARER: Kare ve önünde kalkan (Yay)
            s_rect = (draw_x - self.radius, draw_y - self.radius, self.radius*2, self.radius*2)
            pygame.draw.rect(screen, self.color, s_rect, border_radius=4)
            # Kalkan
            s_ang = getattr(self, 'shield_angle', 0)
            pygame.draw.arc(screen, (200, 200, 220), 
                            (draw_x - self.radius - 5, draw_y - self.radius - 5, self.radius*2+10, self.radius*2+10),
                            -s_ang - 0.8, -s_ang + 0.8, 6)


        elif self.type == "lava_pit":
            # LAVA PIT: Tehlikeli Tuzak (Tırtıklı / Hazard Kare)
            # 1. Taban rengi
            rect = pygame.Rect(draw_x - self.radius, draw_y - self.radius, self.radius*2, self.radius*2)
            pygame.draw.rect(screen, (30, 30, 30), rect, border_radius=4) # İç siyah zemin
            
            # 2. Tırtıklı Kenarlar (Diagonal pattern)
            for i in range(-self.radius, self.radius + 10, 15):
                pygame.draw.line(screen, self.color, (draw_x + i, draw_y - self.radius), (draw_x + i + 10, draw_y + self.radius), 3)
            
            # 3. Kenarlık (Glow / Border)
            pygame.draw.rect(screen, self.color, rect, width=4, border_radius=4)
            
            # 4. Üstüne Hazard Sembolü
            try:
                font = pygame.font.SysFont("Arial", 40, bold=True)
                txt = font.render("!", True, self.color)
                screen.blit(txt, txt.get_rect(center=(draw_x, draw_y)))
            except: pass

        elif "splitting_slime" in self.type:
            # SLIME: Dalgalanan daire
            pygame.draw.circle(screen, self.color, (int(draw_x), int(draw_y)), int(self.radius + pulse))
            pygame.draw.circle(screen, (255, 255, 255), (int(draw_x), int(draw_y)), int(self.radius + pulse), 2)

        elif self.type == "burrowing_worm":
            if getattr(self, 'is_underground', False):
                # Yer altındayken sadece gölge/iz çiz (şeffaf daire)
                s = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.color, 50), (self.radius, self.radius), self.radius)
                screen.blit(s, (draw_x - self.radius, draw_y - self.radius))
            else:
                pygame.draw.circle(screen, self.color, (int(draw_x), int(draw_y)), self.radius)
                pygame.draw.circle(screen, (255, 255, 255), (int(draw_x), int(draw_y)), self.radius, 2)

        elif self.type in ["necromancer", "zombie", "black_hole_caster"]:
            # Normal düşmanlar gibi ama kendi renkleriyle kare
            pygame.draw.rect(screen, self.color, (draw_x - self.radius, draw_y - self.radius, self.radius*2, self.radius*2), border_radius=4)
            pygame.draw.rect(screen, (255, 255, 255), (draw_x - self.radius, draw_y - self.radius, self.radius*2, self.radius*2), 2, border_radius=4)
            
        elif self.type == "loot_goblin":
            # GOBLİN: Altın sarısı elmas (diamond)
            points = [
                (draw_x, draw_y - self.radius - pulse),
                (draw_x + self.radius + pulse, draw_y),
                (draw_x, draw_y + self.radius + pulse),
                (draw_x - self.radius - pulse, draw_y)
            ]
            pygame.draw.polygon(screen, self.color, points)
            pygame.draw.polygon(screen, (255, 255, 255), points, 2)

        else:
            # STANDART: Köşeli baklava / Dönen Kare
            size = self.radius + pulse
            points = [
                (draw_x, draw_y - size),
                (draw_x + size, draw_y),
                (draw_x, draw_y + size),
                (draw_x - size, draw_y)
            ]
            pygame.draw.polygon(screen, self.color, points)
            pygame.draw.polygon(screen, (255, 255, 255), points, 1)

        # Can Barı (Küçük ve Şık) - Tuzaklar için gizle
        if not self.is_trap:
            hp_ratio = max(0, self.hp / self.max_hp)
            bar_w = self.radius * 1.5
            pygame.draw.rect(screen, (30, 30, 40), (draw_x - bar_w/2, draw_y - self.radius - 12, bar_w, 4), border_radius=2)
            pygame.draw.rect(screen, (231, 76, 60), (draw_x - bar_w/2, draw_y - self.radius - 12, bar_w * hp_ratio, 4), border_radius=2)
        
        # Efekt İkonları
        self.effect_manager.draw_icons(screen, draw_x, draw_y, self.radius)

        # Elite İsim Etiketi
        if getattr(self, 'is_elite', False) and hasattr(self, 'elite_mods'):
            if not hasattr(Enemy, '_elite_font'):
                Enemy._elite_font = pygame.font.SysFont("segoeui", 13, bold=True)
            
            mod_names = [m['name'] for m in self.elite_mods]
            tag_text = " ".join(mod_names)
            txt_surf = Enemy._elite_font.render(tag_text, True, getattr(self, 'elite_color', (255, 215, 0)))
            
            bg_rect = txt_surf.get_rect(center=(draw_x, draw_y - self.radius - 22))
            pygame.draw.rect(screen, (20, 20, 20), bg_rect.inflate(6, 4), border_radius=3)
            screen.blit(txt_surf, bg_rect)
