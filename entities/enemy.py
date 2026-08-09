import pygame
import math
import random
import time

import vfx

# Düşman üzerindeki durum etkisinin görsel karşılığı: (renk, doku).
# Etki adları logic/status_effects.py'daki apply_* fonksiyonlarından gelir.
_STATUS_FX = {
    "Burn":       ((255, 130, 40),  "flame"),
    "Poison":     ((120, 230, 90),  "smoke"),
    "Slow":       ((110, 200, 255), "spark"),
    "DeepFreeze": ((150, 220, 255), "spark"),
    "IceMage":    ((110, 200, 255), "spark"),
    "FrostAura":  ((110, 200, 255), "spark"),
    "Frostbite":  ((110, 200, 255), "spark"),
    "Stun":       ((255, 215, 70),  "crit"),
    "Silence":    ((170, 170, 180), "smoke"),
    "Paladin":    ((255, 235, 170), "glow"),
}

class Enemy:
    def __init__(self, id, x, y, game, type="normal", wave_level=1):
        self.id = id
        # Denge: Wave ölçeklemesi artık kill_enemy'de (reward_step_mult) uygulanıyor;
        # xp_reward tip bazlı taban değerdir (risk/ödül dengesi için).
        xp_mult = 1.0
        self.x = x
        self.y = y
        self.type = type
        self.radius = 24
        # apply_dot() gibi `game` almayan yollardan oyuncu statlarına
        # (statusDuration) erişebilmek için referans saklanır.
        self.game = game
        
        # --- BASE STATS (Initialize first!) ---
        # --- ZORLUK ÖLÇEKLENDİRMESİ ---
        diff_name = game.wave.get("current_diff", "Normal")
        
        # Step-based Wave Scaling (Her 10 wave'de bir boss sonrası zorlaşır)
        # Denge: 1.35 basamağı tek dalgada +%38 sıçrama yaratıyordu; 1.25'e yumuşatıldı
        step_level = (wave_level - 1) // 10
        wave_scale = (1.25 ** step_level) * (1.0 + wave_level * 0.05)
        
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
            self.dmg = 21.25 * wave_scale
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
            # Denge: Sabit 45 erken oyunda ölümcül, geç oyunda önemsizdi; wave ile ölçeklenir
            self.dmg = 15 * wave_scale
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
            # Rusher: en hızlı düşman OLMALI ama en hızlı sınıfı (ninja 7.2)
            # GEÇMEMELI — yoksa geç oyunda kimse kaçamaz, konumlama karşı-oyunu
            # yok olur. Tavan 3.0->2.2 ile üst hız 8.0->7.2'ye çekildi.
            self.speed = 5.0 + min(wave_level * 0.12, 2.2)
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
            self.dmg = 35 * wave_scale   # Denge: 60 tabanı temas halinde anlık ölüm demekti
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
            self.lava_spawned = 0           # Denge: Sınırsız lav çukuru üretimi kapatıldı
            self.max_lava_pits = 4
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
            
        elif self.type == "mimic":
            self.max_hp = 350 * wave_scale
            self.hp = self.max_hp
            self.speed = 0.0 # Başlangıçta sabit
            self.base_mimic_speed = 4.0 # Uyanınca hızı
            self.radius = 24
            self.dmg = 40 * wave_scale
            self.color = (139, 69, 19) # Ahşap kahverengi
            self.xp_reward = 100 * xp_mult
            self.is_awake = False
            
        elif self.type == "web_weaver":
            self.max_hp = 140 * wave_scale
            self.hp = self.max_hp
            self.speed = 2.5
            self.radius = 28
            self.dmg = 8 * wave_scale
            self.color = (169, 169, 169) # Açık gri
            self.xp_reward = 45 * xp_mult
            self.web_timer = 2.0 # Her 2 saniyede bir ağ bırakır

        elif self.type == "spider_egg":
            self.max_hp = 30 * wave_scale
            self.hp = self.max_hp
            self.speed = 0.0
            self.radius = 16
            self.dmg = 0
            self.color = (255, 255, 255) # Beyaz
            self.xp_reward = 0
            self.egg_timer = 3.0 # 3 saniye kuluçka süresi

        elif self.type == "war_tower":
            self.max_hp = 800 * wave_scale
            self.hp = self.max_hp
            self.speed = 0.0
            self.radius = 35
            self.dmg = 30 * wave_scale
            self.color = (80, 80, 80) # Koyu Taş Rengi
            self.xp_reward = 150 * xp_mult
            self.tower_shoot_timer = 1.5 # Her 1.5 saniyede bir ateş eder
            self.aura_radius = 300
            
        elif self.type == "mad_scientist":
            self.max_hp = 200 * wave_scale
            self.hp = self.max_hp
            self.speed = 1.8
            self.radius = 24
            self.dmg = 15 * wave_scale
            self.color = (155, 255, 155) # Soluk fosforlu yeşil
            self.xp_reward = 80 * xp_mult
            self.mutate_timer = 5.0 # Her 5 saniyede bir buff atar
            
        elif self.type == "parasite":
            self.max_hp = 60 * wave_scale
            self.hp = self.max_hp
            self.speed = 4.5
            self.radius = 12
            self.dmg = 5 * wave_scale
            self.color = (255, 100, 200) # Pembe
            self.xp_reward = 30 * xp_mult

        elif self.type == "pickpocket_imp":
            self.max_hp = 100 * wave_scale
            self.hp = self.max_hp
            self.speed = 5.0
            self.radius = 18
            self.dmg = 5 * wave_scale
            self.color = (139, 0, 139) # Koyu mor
            self.xp_reward = 40 * xp_mult
            self.stolen_gold = 0
            self.is_escaping = False
            self.has_dodged = False # İlk vuruş dodge
            self.escape_timer = 10.0 # Kaçış süresi

        self.base_max_hp = self.max_hp
        self.base_dmg = self.dmg
        self.base_speed = self.speed
        self.base_armor = getattr(self, 'armor', 0)
        # Knockback vektorleri ve boss-minion bayragi: apply_difficulty'yi
        # override eden bosslar bunlari kaybetmesin diye burada da kurulur
        self.kb_x = 0.0
        self.kb_y = 0.0
        self._is_boss_minion = False
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
        self._is_boss_minion = False
        
        # Knockback (Savrulma) Vektörleri
        self.kb_x = 0.0
        self.kb_y = 0.0
        
        # --- Zırh ve Boss Scaling ---

    def update(self, dt, game):
        if self.dead: return
        self.effect_manager.update(dt, self, game)

        # --- DURUM ETKİSİ GERİ BİLDİRİMİ ---
        # Yanan/zehirlenen/donmuş/sersemlemiş düşman eskiden normal görünüyordu;
        # oyuncu uyguladığı etkinin işe yarayıp yaramadığını göremiyordu.
        # Seyrek parçacık: kare başına değil, ~%8 ihtimalle bir tane.
        if self.effect_manager.effects and random.random() < 0.08:
            _st = self.effect_manager.effects[0].name
            _sc = _STATUS_FX.get(_st)
            if _sc is not None:
                vfx.emit(game, self.x, self.y - 6, count=1, color=_sc[0],
                         speed=(0.2, 0.9), size=(2, 4), life=(0.3, 0.55),
                         tex=_sc[1], gravity=-0.02)
        
        # Knockback Uygulama ve Sönümleme
        if abs(self.kb_x) > 0.1 or abs(self.kb_y) > 0.1:
            self.x += self.kb_x * dt * 60
            self.y += self.kb_y * dt * 60
            # Sürtünme (Friction)
            self.kb_x *= 0.85
            self.kb_y *= 0.85
        else:
            self.kb_x = 0
            self.kb_y = 0

        # Pack Leader hız buff'ının süresi dolunca hızı normale döndür
        if getattr(self, '_pack_buff_timer', 0) > 0:
            self._pack_buff_timer -= dt
            if self._pack_buff_timer <= 0 and hasattr(self, '_pack_base_speed'):
                self.speed = self._pack_base_speed
                del self._pack_base_speed
                
        # War Tower Aura
        if getattr(self, 'war_tower_aura_timer', 0) > 0:
            self.war_tower_aura_timer -= dt
            if self.war_tower_aura_timer <= 0:
                if hasattr(self, '_war_tower_base_speed'):
                    self.speed = self._war_tower_base_speed
                    del self._war_tower_base_speed
                if hasattr(self, '_war_tower_base_dmg'):
                    self.dmg = self._war_tower_base_dmg
                    del self._war_tower_base_dmg
        
        # Target player
        p = game.players[game.local_player_id]
        dist = math.hypot(p.x - self.x, p.y - self.y)

        # --- ELİT ❄️ DONDURUCU / BUZ BİYOMU (frost_aura) ---
        # Bayrak elite_system ve biome_system tarafından kuruluyordu ama
        # hiçbir yerde okunmuyordu: 200 birim yarıçapta oyuncuyu yavaşlatır.
        if getattr(self, 'frost_aura', False) and dist < 200:
            from logic.status_effects import apply_slow
            apply_slow(p.effect_manager, duration=0.5, mult=0.65, name="FrostAura")

        # Tum hareket satirlari icin tek efektif hiz: yavaslatma (speed_mod)
        # ve sersemletme yalnizca tek bir satirda okunuyordu (H2)
        eff_speed = 0.0 if getattr(self, "is_stunned", False) else self.speed * self.speed_mod

        # "🔇 GÜRÜLTÜ YASAĞI" dalga olayı: ateş etmek düşmanları çeker.
        # sound_aggro anahtarı tanımlıydı ama HİÇ okunmuyordu; olay yalnızca
        # afiş gösteriyordu. Artık son 1.5 sn içinde ateş edildiyse düşmanlar
        # "sesi duyar": daha hızlı gelirler ve görünmezlik onları şaşırtmaz.
        _ev = game.wave.get("event")
        _noisy = False
        if _ev and _ev.get("sound_aggro"):
            _since = pygame.time.get_ticks() - getattr(p, "last_shot_time", -99999)
            _noisy = _since < 1500
            if _noisy:
                eff_speed *= 1.35

        # Görünmezlik Kontrolü
        if p.is_invisible and not _noisy:
             # Eğer görünmezse rastgele küçük hareketler yap (Wander)
             self.x += random.uniform(-1, 1) * eff_speed * dt * 20
             self.y += random.uniform(-1, 1) * eff_speed * dt * 20
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
                        self.x += math.cos(final_angle) * eff_speed * dt * 60
                        self.y += math.sin(final_angle) * eff_speed * dt * 60
                else:
                    # Dash Hareket
                    self.dash_timer -= dt
                    self.dash_speed_mult = 4.0 # 5.5'ten 4.0'a düşürüldü
                    self.x += math.cos(self.dash_angle) * (eff_speed * self.dash_speed_mult) * dt * 60
                    self.y += math.sin(self.dash_angle) * (eff_speed * self.dash_speed_mult) * dt * 60
                    
                    # Varil Çarpışması (Burst Hasar ve i-frame)
                    # Hitbox biraz daraltıldı (%80) "değmeden vurdu" hissini kaldırmak için
                    if dist < (self.radius + p.radius) * 0.8:
                        if p.i_frame_timer <= 0:
                            self.hit_player(p, self.dmg * 2, force=False) # i-frame'e saygı duyar
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
                    self.x += math.cos(angle) * eff_speed * dt * 60
                    self.y += math.sin(angle) * eff_speed * dt * 60
                elif dist < 500:
                    self.x -= math.cos(angle) * eff_speed * dt * 60
                    self.y -= math.sin(angle) * eff_speed * dt * 60
                
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
                self.x += math.cos(angle + offset) * eff_speed * dt * 60
                self.y += math.sin(angle + offset) * eff_speed * dt * 60

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
                                self.hit_player(p, self.dmg)
                            for e in game.iter_enemies_near(self.x, self.y, 50):
                                if not e.dead and not e.is_trap and e != self:
                                    dx = e.x - self.x
                                    dy = e.y - self.y
                                    if dx * dx + dy * dy < 50 * 50:
                                        e.take_damage(self.dmg * 0.5, game)
                            self.has_exploded = True
                            self.hp = 0
                            self.dead = True
                            game.kill_enemy(self)
                            return
                    elif dist > 5:
                        # Yaklaşırken hızlan (Denge: x2.0 kaçınılmazdı, x1.5'e indirildi)
                        speed_mult = 1.5 if dist < 200 else 1.0
                        self.x += math.cos(angle) * eff_speed * speed_mult * dt * 60
                        self.y += math.sin(angle) * eff_speed * speed_mult * dt * 60

            # --- KALKAN TAŞIYICI ---
            elif self.type == "shieldbearer":
                # Yavaş ama düz yaklaşım
                self.x += math.cos(angle) * eff_speed * dt * 60
                self.y += math.sin(angle) * eff_speed * dt * 60
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
                    self.x += (dx / d) * eff_speed * dt * 60
                    self.y += (dy / d) * eff_speed * dt * 60

            # --- ATEŞ ŞAMANI ---
            elif self.type == "fire_shaman":
                # Yavaş yaklaşım (kamp yapar)
                if dist > 300:
                    self.x += math.cos(angle) * eff_speed * dt * 60
                    self.y += math.sin(angle) * eff_speed * dt * 60

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
                self.x += math.cos(angle) * eff_speed * dt * 60
                self.y += math.sin(angle) * eff_speed * dt * 60
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
                self.x += math.cos(angle + offset) * eff_speed * dt * 60
                self.y += math.sin(angle + offset) * eff_speed * dt * 60
                # Buff: Yakındaki düşmanlara hız ve hasar artışı
                for e in game.iter_enemies_near(self.x, self.y, self.buff_radius):
                    if not e.dead and e != self and e.type not in ["pack_leader", "lava_pit"]:
                        dx = e.x - self.x
                        dy = e.y - self.y
                        if dx * dx + dy * dy < self.buff_radius * self.buff_radius:
                            # Denge: Buff artık süreli; lider ölünce/uzaklaşınca hız normale döner
                            if not hasattr(e, '_pack_base_speed'):
                                e._pack_base_speed = e.speed
                            e.speed = min(e._pack_base_speed * 1.3, e.speed + e._pack_base_speed * 0.6 * dt)
                            e._pack_buff_timer = 0.5

            # --- ZEHİRLİ ÖRÜMCEK ---
            elif self.type == "venom_spider":
                if dist > 200:
                    self.x += math.cos(angle) * eff_speed * dt * 60
                    self.y += math.sin(angle) * eff_speed * dt * 60
                elif dist < 120:
                    # Hafif uzaklaş
                    self.x -= math.cos(angle) * eff_speed * 0.5 * dt * 60
                    self.y -= math.sin(angle) * eff_speed * 0.5 * dt * 60
                
                self.shoot_timer -= dt
                if self.shoot_timer <= 0 and dist < 500:
                    vx = math.cos(angle) * 9
                    vy = math.sin(angle) * 9
                    from entities.projectile import Projectile
                    proj = Projectile(game.entity_id_counter, self.x, self.y, vx, vy, self.dmg, is_hostile=True)
                    proj.poison_dps = self.dmg * 0.5  # Zehir özelliği (wave ile ölçeklenir)
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
                            self.hit_player(p, self.dmg)
                        self.tp_warning = False
                        self.tp_timer = self.tp_cooldown
                else:
                    self.tp_timer -= dt
                    # Normal yavaş takip
                    self.x += math.cos(angle) * eff_speed * 0.5 * dt * 60
                    self.y += math.sin(angle) * eff_speed * 0.5 * dt * 60
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
                self.x += math.cos(angle) * eff_speed * dt * 60
                self.y += math.sin(angle) * eff_speed * dt * 60
                
                # Belirli aralıklarla geçtiği yere Lav Çukuru bırakır (juggernaut başına max 4)
                self.lava_timer -= dt
                if self.lava_timer <= 0 and self.lava_spawned < self.max_lava_pits:
                    self.lava_spawned += 1
                    game.entity_id_counter += 1
                    # Spawn new lava pit with high wave level for high damage
                    lava = Enemy(game.entity_id_counter, self.x, self.y, game, type="lava_pit", wave_level=game.wave["level"])
                    game.enemies.append(lava)
                    self.lava_timer = self.lava_cooldown

            # --- SÜRÜ EFENDİSİ (SWARM LORD) ---
            elif self.type == "swarm_lord":
                # Oyuncudan uzakta durmaya çalış (Kite)
                if dist < 400:
                    self.x -= math.cos(angle) * eff_speed * dt * 60
                    self.y -= math.sin(angle) * eff_speed * dt * 60
                elif dist > 600:
                    self.x += math.cos(angle) * eff_speed * dt * 60
                    self.y += math.sin(angle) * eff_speed * dt * 60
                
                # Sürekli Sürü Yarasası çağırır
                self.spawn_timer -= dt
                if self.spawn_timer <= 0 and game.can_spawn_summoned_enemy():
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
                    self.x -= math.cos(angle) * eff_speed * dt * 60
                    self.y -= math.sin(angle) * eff_speed * dt * 60
                elif dist > 600:
                    self.x += math.cos(angle) * eff_speed * dt * 60
                    self.y += math.sin(angle) * eff_speed * dt * 60
                
                self.spawn_timer -= dt
                if self.spawn_timer <= 0 and game.can_spawn_summoned_enemy():
                    game.entity_id_counter += 1
                    zombie = Enemy(game.entity_id_counter, self.x + random.uniform(-30, 30), self.y + random.uniform(-30, 30), game, type="zombie", wave_level=game.wave["level"])
                    game.enemies.append(zombie)
                    game.add_event("explosion", zombie.x, zombie.y, radius=20, color=(127, 140, 141), timer=0.2)
                    self.spawn_timer = self.spawn_cooldown

            # --- GANİMET GOBLİN'İ (LOOT GOBLIN) ---
            elif self.type == "loot_goblin":
                # Sürekli oyuncunun tersi yönünde kaçar
                self.x -= math.cos(angle) * eff_speed * dt * 60
                self.y -= math.sin(angle) * eff_speed * dt * 60
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
                    self.x += math.cos(angle) * eff_speed * 1.5 * dt * 60
                    self.y += math.sin(angle) * eff_speed * 1.5 * dt * 60
                    if self.worm_timer <= 0:
                        # Yüzeye çık
                        self.is_underground = False
                        self.is_invulnerable = False
                        self.worm_timer = 3.0 # 3 saniye yüzeyde kalır
                        game.add_event("explosion", self.x, self.y, radius=40, color=(211, 84, 0), timer=0.4)
                        game.trigger_shake(10)
                        if math.hypot(p.x - self.x, p.y - self.y) < 50:
                            self.hit_player(p, self.dmg)
                else:
                    # Yüzeydeyken çok yavaş hareket et
                    self.x += math.cos(angle) * eff_speed * 0.2 * dt * 60
                    self.y += math.sin(angle) * eff_speed * 0.2 * dt * 60
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
                    self.x -= math.cos(angle) * eff_speed * dt * 60
                    self.y -= math.sin(angle) * eff_speed * dt * 60
                elif dist > 500:
                    self.x += math.cos(angle) * eff_speed * dt * 60
                    self.y += math.sin(angle) * eff_speed * dt * 60
                
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

            # --- MIMIC ---
            elif self.type == "mimic":
                if not getattr(self, "is_awake", False):
                    # Uyku halinde (Hareket etmez, oyuncu yaklaşınca uyanır)
                    if dist < 150: # Aggro range
                        self.is_awake = True
                        self.speed = getattr(self, "base_mimic_speed", 4.0)
                        game.add_event("damage_text", self.x, self.y - 20, value="!!!", color=(255, 50, 50), timer=1.0)
                else:
                    # Uyanık ve agresif (düz takip)
                    self.x += math.cos(angle) * eff_speed * dt * 60
                    self.y += math.sin(angle) * eff_speed * dt * 60
            
            # --- WEB WEAVER ---
            elif self.type == "web_weaver":
                self.x += math.cos(angle) * eff_speed * dt * 60
                self.y += math.sin(angle) * eff_speed * dt * 60
                self.web_timer -= dt
                if self.web_timer <= 0:
                    self.web_timer = 2.0
                    from entities.cloud import Cloud
                    game.entity_id_counter += 1
                    web = Cloud(game.entity_id_counter, self.x, self.y, radius=40, duration=8.0, frost_dmg=0, is_web=True)
                    game.clouds.append(web)

            # --- SPIDER EGG ---
            elif self.type == "spider_egg":
                self.egg_timer -= dt
                if self.egg_timer <= 0:
                    self.take_damage(self.max_hp * 999, game) # Yumurta patlar
                    if not hasattr(game, '_pending_spawns'):
                        game._pending_spawns = []
                    # 3 swarm bat çıkar
                    for _ in range(3):
                        game.entity_id_counter += 1
                        bat = Enemy(game.entity_id_counter, self.x + random.uniform(-10, 10), self.y + random.uniform(-10, 10), game, type="swarm_bat", wave_level=game.wave["level"])
                        game._pending_spawns.append(bat)

            # --- WAR TOWER ---
            elif self.type == "war_tower":
                self.tower_shoot_timer -= dt
                if self.tower_shoot_timer <= 0:
                    self.tower_shoot_timer = 1.5
                    from entities.projectile import Projectile
                    game.entity_id_counter += 1
                    base_angle = math.atan2(p.y - self.y, p.x - self.x)
                    # 3 mermi (spread)
                    for spread in [-0.2, 0, 0.2]:
                        proj_angle = base_angle + spread
                        vx = math.cos(proj_angle) * 300
                        vy = math.sin(proj_angle) * 300
                        game.projectiles.append(Projectile(
                            game.entity_id_counter, self.x, self.y, vx, vy,
                            dmg=self.dmg, p_type="normal", is_hostile=True, lifetime=120
                        ))
                        game.entity_id_counter += 1
                
                # Aura Etkisi: Yakındaki düşmanları buffla
                for e in game.iter_enemies_near(self.x, self.y, self.aura_radius):
                    if not e.dead and e.type != "war_tower" and not getattr(e, "is_trap", False):
                        if getattr(e, "war_tower_aura_timer", 0) <= 0:
                            e._war_tower_base_speed = e.speed
                            e._war_tower_base_dmg = e.dmg
                            e.speed = e.speed * 1.15
                            e.dmg = e.dmg * 1.25
                        e.war_tower_aura_timer = 0.5 # 0.5 saniye sürer, kule yaşadıkça yenilenir

            # --- MAD SCIENTIST ---
            elif self.type == "mad_scientist":
                # Kiting AI
                if dist < 300:
                    self.x -= math.cos(angle) * eff_speed * dt * 60
                    self.y -= math.sin(angle) * eff_speed * dt * 60
                elif dist > 450:
                    self.x += math.cos(angle) * eff_speed * dt * 60
                    self.y += math.sin(angle) * eff_speed * dt * 60
                
                self.mutate_timer -= dt
                if self.mutate_timer <= 0:
                    self.mutate_timer = 5.0
                    targets = []
                    for e in game.iter_enemies_near(self.x, self.y, 400):
                        if not e.dead and e != self and not getattr(e, "is_mutated", False) and e.type != "war_tower" and not getattr(e, "is_trap", False):
                            targets.append(e)
                    if targets:
                        target = random.choice(targets)
                        target.is_mutated = True
                        target.max_hp *= 1.5
                        # Overheal: hp max_hp'yi aşabiliyordu (P4)
                        target.hp = min(target.max_hp, target.hp + target.max_hp * 0.5)
                        target.dmg *= 1.3
                        target.radius *= 1.3
                        target.color = (155, 255, 155) # Mutasyon Rengi
                        game.add_event("damage_text", target.x, target.y - 20, value="MUTATED!", color=(155, 255, 155), timer=1.5)

            # --- PICKPOCKET IMP ---
            elif self.type == "pickpocket_imp":
                if not getattr(self, "is_escaping", False):
                    # Oyuncuya koş ve çal
                    self.x += math.cos(angle) * eff_speed * dt * 60
                    self.y += math.sin(angle) * eff_speed * dt * 60
                    if dist < self.radius + 15:
                        steal_amount = min(p.gold, random.randint(50, 150))
                        if steal_amount > 0:
                            p.gold -= steal_amount
                            self.stolen_gold += steal_amount
                            game.add_event("damage_text", self.x, self.y - 20, value=f"-{steal_amount} Gold!", color=(255, 215, 0), timer=1.5)
                        self.is_escaping = True
                else:
                    # Kaçış modu (oyuncunun tersine)
                    self.x -= math.cos(angle) * eff_speed * dt * 60
                    self.y -= math.sin(angle) * eff_speed * dt * 60
                    self.escape_timer -= dt
                    if self.escape_timer <= 0:
                        self.hp = 0
                        self.dead = True
                        # Drop atmaması için game_logic'te kill_enemy tetiklenmeden ölecek, ya da no_drop flag
                        self.no_drop = True

            # --- STANDART AI ---
            else:
                offset = math.sin(self.id * 0.5 + time.time() * 2) * 0.2
                final_angle = angle + offset
                self.x += math.cos(final_angle) * eff_speed * dt * 60
                self.y += math.sin(final_angle) * eff_speed * dt * 60
            
        # Hasar ve Efekt Güncelleme
        # (self.effect_manager.update already called at start of update)
            
        # HASAR MANTIĞI
        # Saldırı menzilini biraz genişletiyoruz (radius + 10) çünkü kalabalık durumlarda yaratıklar birbirini ittiği için 
        # oyuncunun tam üstüne binemeyebiliyorlar, bu da hasar verememelerine sebep oluyordu.
        if dist < self.radius + p.radius + 10 and not getattr(self, 'is_invulnerable', False):
            # Temas Hasarı: Kullanıcı İsteği - AFK kalmayı önlemek için i-frame aşılır ve sürekli vurur
            # Denge: x3 çarpanı üst üste binen düşmanlarla anlık ölüm yaratıyordu, x2'ye indirildi
            self.hit_player(p, self.dmg * dt * 2, force=True)
            
        # Sınır dışına çıkmayı engelle (Map Boundaries)
        self.x = max(50, min(4950, self.x))
        self.y = max(50, min(4950, self.y))

    def hit_player(self, p, dmg, force=False):
        """Düşmanın oyuncuya hasar verdiği TEK nokta.

        Elit 🧛 Vampir modifikatörü (elite_lifesteal) burada tüketilir:
        elite_system bayrağı kuruyordu ama hiçbir yerde okunmuyordu.
        Can çalma İSTENEN hasara değil GERÇEKLEŞEN hasara bağlıdır; böylece
        dodge/i-frame ile boşa giden vuruş düşmanı iyileştirmez.
        """
        p.last_attacker_type = self.type
        ls = getattr(self, 'elite_lifesteal', 0)
        if ls <= 0:
            p.take_damage(dmg, force=force)
            return
        before = p.hp + getattr(p, 'energy_shield', 0)
        p.take_damage(dmg, force=force)
        dealt = before - (p.hp + getattr(p, 'energy_shield', 0))
        if dealt > 0:
            self.hp = min(self.max_hp, self.hp + dealt * ls)

    def _player_stats(self):
        """Oyuncunun stat sözlüğü (yoksa boş dict). Enemy bazı yollarda
        `game` almadığı için __init__'te saklanan referans kullanılır."""
        g = getattr(self, 'game', None)
        try:
            return g.players[g.local_player_id].stats
        except Exception:
            return {}

    def apply_dot(self, eff_type, dps, duration, slow=0.0):
        from logic.status_effects import apply_burn, apply_slow
        # statusDuration (affix + SET_VENOM 3pc + SET_ALCHEMIST 4pc) ve
        # juggernaut aurasının -0.5 cezası tanımlıydı ama hiç okunmuyordu.
        # Süre negatife düşmesin diye taban 0.1x ile kırpılır.
        sd = self._player_stats().get("statusDuration", 0)
        if sd:
            duration = duration * max(0.1, 1.0 + sd)
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
        # Negatif/sıfır hasar düşmanı iyileştiriyordu (H8)
        if amount <= 0: return
        if getattr(self, 'is_invulnerable', False): return
        # Lava pits remain invulnerable, pillars take damage.
        if getattr(self, 'is_trap', False) and self.type == "lava_pit": return
        
        # Hırsız Cin ilk vuruş garantili dodge
        if self.type == "pickpocket_imp" and not getattr(self, "has_dodged", False):
            self.has_dodged = True
            game.add_event("damage_text", self.x, self.y - 20, value="DODGE!", color=(200, 200, 200), timer=1.0)
            return
        
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

        # --- ACIMASIZ (brutal affix'i) ---
        # Silah ön-eki olarak üretiliyordu ama hiçbir yerde okunmuyordu.
        if from_player:
            final_dmg *= (1.0 + p_stats.get("brutal", 0))

        # --- KILL STREAK HASAR (Momentum) ---
        # Her kombo başına +%X hasar (Örn: 10 combo * %5 = %50)
        # TAVAN: combo sayacı 500+'a çıkabiliyor; "Kıyım Momentumu" aurası
        # (0.002/kill) tavansız halde +%100'ü aşıp katlanarak büyürdü.
        streak_bonus = min(2.0, game.kill_streak * p_stats.get("killComboDmg", 0))
        final_dmg *= (1.0 + streak_bonus)
        
        # Minimum Hasar (Zırh çok yüksek olsa bile %5 vur)
        final_dmg = max(amount * 0.05, final_dmg)
        
        # --- KALKAN KORUMASI (Shieldbearer): Gelen hasar %65 azalır ---
        # Denge: %80 azaltma açı kontrolü olmadan saf HP süngeri yaratıyordu
        if self.type == "shieldbearer" and not is_dot:
            final_dmg *= 0.35

        # --- ELİT ENERJİ KALKANI (🔮 Kalkanlı modifikatörü) ---
        elite_shield = getattr(self, 'elite_shield', 0)
        if elite_shield > 0 and not is_dot:
            absorbed = min(elite_shield, final_dmg)
            self.elite_shield -= absorbed
            final_dmg -= absorbed
            
        self.hp -= final_dmg

        # --- ELİT 🌵 DİKENLİ (thorny) ---
        # elite_system enemy.thorns bayrağını kuruyordu ama okunmuyordu.
        # DİKKAT: bu oyuncunun KENDİ thorns statından bağımsızdır (o
        # player.take_damage içinde ayrı bağlı). Ölümcül geri tepmeye karşı
        # tek vuruşta oyuncunun max canının %15'i ile sınırlanır.
        th = getattr(self, 'thorns', 0)
        if th > 0 and from_player and not is_dot:
            reflect = min(final_dmg * th, player.max_hp * 0.15)
            if reflect > 0:
                player.take_damage(reflect, force=True)

        # --- ÇALMA ŞANSI (thiefChance affix'i) ---
        if from_player and not is_dot and p_stats.get("thiefChance", 0) > 0:
            if random.random() < p_stats.get("thiefChance", 0):
                base_gold = getattr(self, 'gold_reward', self.xp_reward * 0.5)
                stolen = int(base_gold * 0.2)
                if stolen > 0:
                    player.gold += stolen
                    game.add_event("damage_text", self.x, self.y - 30,
                                   value=f"+{stolen} G", color=(241, 196, 15), timer=0.6)

        # --- SINGULARITY (blackHoleChance, corrupted orb) ---
        if from_player and not is_dot and p_stats.get("blackHoleChance", 0) > 0:
            if random.random() < p_stats.get("blackHoleChance", 0):
                from entities.cloud import Cloud
                game.entity_id_counter += 1
                game.clouds.append(Cloud(game.entity_id_counter, self.x, self.y,
                                         radius=120, duration=3.0, is_black_hole=True))
                game.add_event("explosion", self.x, self.y, radius=60,
                               color=(44, 62, 80), timer=0.3)

        if hasattr(game, 'record_damage_dealt'):
            game.record_damage_dealt(final_dmg, is_dot=is_dot)
        elif hasattr(game, 'stats'):
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
                # Kaotik İnfaz (Chaotic Execution) Sinerjisi
                if p_stats.get("executeExplosion", 0) > 0:
                    game.add_event("explosion", self.x, self.y, radius=120, color=(150, 0, 150), timer=0.5)
                    for e in game.iter_enemies_near(self.x, self.y, 120):
                        if not e.dead and not getattr(e, 'is_trap', False) and e != self:
                            e.take_damage(self.max_hp * 0.2, game, from_player=True)

        # --- STORM CALLER (Fırtına Çağrıcı) ---
        if from_player and getattr(player, "lightning_proc_hits", 0) > 0 and not is_dot:
            if not hasattr(player, "_lightning_hit_count"):
                player._lightning_hit_count = 0
            player._lightning_hit_count += 1
            if player._lightning_hit_count >= player.lightning_proc_hits:
                player._lightning_hit_count = 0
                # Yıldırım Hasarı
                self.take_damage(amount * 2, game, from_player=True)
                game.add_event("explosion", self.x, self.y, radius=40, color=(255, 255, 0), timer=0.2)
                game.add_event("damage_text", self.x, self.y - 60, value="YILDIRIM!", color=(255, 255, 0), timer=1.0)
                
                # Fırtına Birliği (Storm Freeze) Sinerjisi
                if p_stats.get("stormFreeze", 0) > 0:
                    from logic.status_effects import apply_slow
                    apply_slow(self.effect_manager, duration=3.0, mult=0.0)

        # --- EVRİM PASİFLERİ (vuruş tetikli) ---
        evo_p = getattr(player, 'evolution_passive', '')
        if from_player and not is_dot and evo_p and not self.dead:
            if evo_p == 'crit_ignite' and is_crit:
                self.apply_dot('fire', final_dmg * 0.30, 3.0)
            elif evo_p == 'freeze_on_hit':
                from logic.status_effects import apply_slow
                if random.random() < 0.10:
                    apply_slow(self.effect_manager, duration=1.0, mult=0.0, name="DeepFreeze")
                else:
                    apply_slow(self.effect_manager, duration=1.5, mult=0.55, name="IceMage")
            elif evo_p == 'fire_aoe':
                r = 120
                for e in list(game.iter_enemies_near(self.x, self.y, r)):
                    if e.dead or getattr(e, 'is_trap', False) or e is self:
                        continue
                    dx, dy = e.x - self.x, e.y - self.y
                    if dx * dx + dy * dy <= r * r:
                        e.apply_dot('fire', final_dmg * 0.35, 2.5)
            elif evo_p == 'chain_lightning':
                # Sıçrayan hasar yine take_damage çağırıyor; bayrak olmadan
                # her sıçrama yeni bir zincir açıp özyinelemeye giriyor
                if not getattr(game, '_chain_lightning_active', False) and random.random() < 0.25:
                    game._chain_lightning_active = True
                    try:
                        hops = 0
                        r = 220
                        for e in list(game.iter_enemies_near(self.x, self.y, r)):
                            if e.dead or getattr(e, 'is_trap', False) or e is self:
                                continue
                            dx, dy = e.x - self.x, e.y - self.y
                            if dx * dx + dy * dy > r * r:
                                continue
                            e.take_damage(final_dmg * 0.40, game, from_player=True)
                            game.add_event("explosion", e.x, e.y, radius=25, color=(120, 200, 255), timer=0.15)
                            hops += 1
                            if hops >= 2:
                                break
                    finally:
                        game._chain_lightning_active = False

        # --- KRİTİK SERSEMLETME (Kritik Aşırı Yük kartı) ---
        # Kart bayrağı tanımlıydı ama hiçbir yerde okunmuyordu (P3)
        stun_dur = getattr(player, "stun_on_crit", 0)
        if is_crit and from_player and stun_dur > 0 and not is_dot and not getattr(self, 'is_boss', False):
            from logic.status_effects import apply_stun
            apply_stun(self.effect_manager, duration=stun_dur)

        # --- LIFESTEAL (Can Çalma) ---
        # lifesteal_bonus (Kan Ateşi kartı) sabit HP katkısıdır (P3)
        ls_flat = getattr(player, "lifesteal_bonus", 0)
        if (p_stats.get("lifesteal", 0) > 0 or ls_flat > 0) and not is_dot and player.hp < player.max_hp and player.lifesteal_cooldown_timer <= 0:
            ls_perc = p_stats.get("lifesteal", 0)
            if game.wave.get("current_diff") == "Impossible":
                ls_perc *= 0.5 # Can çalma etkisi yarıya iner
            heal = final_dmg * ls_perc + ls_flat

            # Tüm sınıflar havuzda biriktirir (GDD 62) ve en fazla max_hp kadar biriktirebilir.
            # Bloodwalker'ın eski "anında heal" dalı 10k+ HP/s sonsuz sustain yaratıyordu (F3);
            # vampir kimliği artık hızlandırılmış havuz boşaltmayla korunur (player.py).
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
                                         radius=70, duration=2.0, frost_dmg=self.dmg * 1.5))
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
            
            # 4. Üstüne Hazard Sembolü (cache'li font; her karede SysFont
            # açmak sıcak çizim yolunda pahalı)
            from ui_elements import get_font
            txt = get_font(40, bold=True).render("!", True, self.color)
            screen.blit(txt, txt.get_rect(center=(draw_x, draw_y)))

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

        elif self.type in ["necromancer", "zombie", "black_hole_caster", "web_weaver", "mad_scientist"]:
            # Normal düşmanlar gibi ama kendi renkleriyle kare
            pygame.draw.rect(screen, self.color, (draw_x - self.radius, draw_y - self.radius, self.radius*2, self.radius*2), border_radius=4)
            pygame.draw.rect(screen, (255, 255, 255), (draw_x - self.radius, draw_y - self.radius, self.radius*2, self.radius*2), 2, border_radius=4)
            if getattr(self, "is_mutated", False):
                # Mutasyon glow'u
                pygame.draw.circle(screen, (155, 255, 155), (int(draw_x), int(draw_y)), int(self.radius + pulse + 5), 2)
            
        elif self.type == "war_tower":
            # Kule şeklinde çizim (Büyük Kare ve Taret Ucu)
            s_rect = (draw_x - self.radius, draw_y - self.radius, self.radius*2, self.radius*2)
            pygame.draw.rect(screen, self.color, s_rect)
            pygame.draw.rect(screen, (40, 40, 40), s_rect, 4)
            # Üzerine kule tepesi (X işareti veya mazgallar)
            pygame.draw.line(screen, (40, 40, 40), (draw_x - self.radius, draw_y - self.radius), (draw_x + self.radius, draw_y + self.radius), 3)
            pygame.draw.line(screen, (40, 40, 40), (draw_x + self.radius, draw_y - self.radius), (draw_x - self.radius, draw_y + self.radius), 3)
            # Aura Çemberi
            pygame.draw.circle(screen, (200, 50, 50), (int(draw_x), int(draw_y)), self.aura_radius, 1)
            
        elif self.type == "spider_egg":
            pygame.draw.ellipse(screen, self.color, (draw_x - self.radius, draw_y - self.radius*1.2, self.radius*2, self.radius*2.4))
            pygame.draw.ellipse(screen, (50, 200, 50), (draw_x - self.radius, draw_y - self.radius*1.2, self.radius*2, self.radius*2.4), 2)

        elif self.type == "parasite":
            # Küçük pembe parazit
            pygame.draw.circle(screen, self.color, (int(draw_x), int(draw_y)), int(self.radius + pulse))
            pygame.draw.circle(screen, (200, 50, 150), (int(draw_x), int(draw_y)), int(self.radius + pulse), 2)
            
        elif self.type == "pickpocket_imp":
            # Hırsız Cin - Ters Üçgen ve Kese
            points = [
                (draw_x, draw_y + self.radius),
                (draw_x - self.radius, draw_y - self.radius),
                (draw_x + self.radius, draw_y - self.radius)
            ]
            pygame.draw.polygon(screen, self.color, points)
            pygame.draw.polygon(screen, (255, 215, 0), points, 2)
            # Eğer çalınmış altını varsa arkasında altın bir kese çizer
            if getattr(self, "stolen_gold", 0) > 0:
                pygame.draw.circle(screen, (255, 215, 0), (int(draw_x + self.radius), int(draw_y)), 6)
            
        elif self.type == "mimic":
            # Sandık Şekli
            pygame.draw.rect(screen, self.color, (draw_x - self.radius, draw_y - self.radius*0.8, self.radius*2, self.radius*1.6), border_radius=2)
            pygame.draw.rect(screen, (255, 215, 0), (draw_x - self.radius, draw_y - self.radius*0.8, self.radius*2, self.radius*1.6), 2, border_radius=2)
            if getattr(self, "is_awake", False):
                # Gözler
                pygame.draw.circle(screen, (255, 50, 50), (int(draw_x - 8), int(draw_y - 4)), 4)
                pygame.draw.circle(screen, (255, 50, 50), (int(draw_x + 8), int(draw_y - 4)), 4)
                # Dişler
                for i in range(-12, 13, 6):
                    pygame.draw.polygon(screen, (255,255,255), [(draw_x + i - 3, draw_y + 4), (draw_x + i + 3, draw_y + 4), (draw_x + i, draw_y + 10)])
            
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
            import ui_theme
            bar_w = int(self.radius * 1.5)
            ui_theme.draw_world_bar(
                screen,
                pygame.Rect(int(draw_x - bar_w / 2), int(draw_y - self.radius - 12), bar_w, 4),
                self.hp / max(1, self.max_hp))

        # Efekt İkonları
        self.effect_manager.draw_icons(screen, draw_x, draw_y, self.radius)

        # Elite İsim Etiketi
        if getattr(self, 'is_elite', False) and hasattr(self, 'elite_mods'):
            import ui_theme
            from ui_elements import render_fit
            # render_fit: mod adlarındaki emoji fontta yoksa □ çizilmesin
            tag_text = " ".join(m['name'] for m in self.elite_mods)
            txt_surf = render_fit(tag_text, 13,
                                  ui_theme.readable(getattr(self, 'elite_color', (255, 215, 0))),
                                  220, bold=True)
            bg_rect = txt_surf.get_rect(center=(draw_x, draw_y - self.radius - 22))
            pygame.draw.rect(screen, ui_theme.DARK_OUT, bg_rect.inflate(8, 4), border_radius=3)
            screen.blit(txt_surf, bg_rect)
