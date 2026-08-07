import pygame
import time
import random
import math
from entities.player import Player
from entities.enemy import Enemy
from entities.projectile import Projectile
from entities.ground_item import GroundItem
from logic.item_system import ItemSystem
from logic.save_manager import SaveManager
from entities.projectile_pool import ProjectilePool
from logic.card_system import CardSystem
from logic.quest_system import QuestSystem
from logic.biome_system import BiomeSystem
from logic.elite_system import EliteSystem

class GameLogic:
    BIOMES = {
        "normal":  {"name": "Ova", "color": (24, 28, 35), "enemy_speed_mult": 1.0},
        "desert":  {"name": "Çöl", "color": (60, 45, 20), "enemy_speed_mult": 1.3},
        "ice":     {"name": "Buz Tundra", "color": (20, 40, 70), "enemy_speed_mult": 0.8},
        "volcano": {"name": "Yanardağ", "color": (50, 20, 10), "enemy_speed_mult": 1.1},
        "dark":    {"name": "Karanlık Vadi", "color": (10, 10, 15), "enemy_speed_mult": 1.2}
    }

    WAVE_EVENTS = [
        {"id": "fast_enemies", "desc": "⚡ HIZLI DALGA! Düşmanlar 2x hızlı!", "gold_mult": 1.5, "enemy_speed": 2.0},
        {"id": "elite_rain",   "desc": "💀 ELİTE YAĞMURU! Herkes elite!", "force_elite": True, "rare_drop": True},
        {"id": "swarm",        "desc": "🦇 SÜRÜ! 3x düşman sayısı!", "enemy_count_mult": 3},
        {"id": "no_shooting",  "desc": "🔇 GÜRÜLTÜ YASAĞI! Ateş edersen ses çıkar!", "sound_aggro": True},
        {"id": "boon",         "desc": "✨ LÜTUF! XP Yarıya iner ama can yenilenmesi 2x.", "invulnerable": False, "xp_mult": 0.5}
    ]

    SPECIAL_WAVES = {
        5:  {"type": "kill_race", "duration": 60, "name": "Hızlı Büyüme Yarışı"},
        15: {"type": "survival", "duration": 120, "name": "Hayatta Kalma"},
        25: {"type": "boss_rush", "duration": 180, "bosses": ["mini_boss_1", "mini_boss_2"], "name": "Boss Rush"}
    }

    def __init__(self, manager, width, height, class_id="warrior"):
        self.manager = manager
        self.width = width
        self.height = height
        
        self.item_system = ItemSystem()
        self.save_manager = SaveManager()
        
        self.state = "PLAYING"
        self.players = {
            "p1": Player("p1", 2500, 2500, class_id)
        }
        self.local_player_id = "p1"
        
        self.enemies = []
        self.projectiles = []
        self.items_on_ground = []
        self.turrets = []
        self.clouds = []
        self.minions = []
        self.particles = []
        self.events = []
        self.entity_id_counter = 0
        self.projectile_pool = ProjectilePool(size=2000)
        self.card_system = CardSystem()
        self.biome_system = BiomeSystem()
        self.pending_cards = [] # Kart seçimi beklerken kullanılacak

        # Günlük Görev Sistemi
        self.quest_system = QuestSystem()
        try:
            meta = self.save_manager.load_meta()
            meta = self.quest_system.load_or_reset(meta)
            self.save_manager.save_meta(meta)
        except Exception as e:
            print("Quest load error:", e)
        
        self.settings = {'shake': True, 'sound': True}
        self.shake_timer = 0
        
        self.hazards = []
        self.hazard_spawn_timer = 10.0 # 10 saniyede bir
        
        self.wave = {
            "level": 1,
            "enemies_to_spawn": 0,
            "total_to_spawn": 0,
            "spawn_timer": 0,
            "current_diff": "Normal", # İsim bazlı (Normal, Hard, Very Hard, Impossible)
            "is_blood_moon": False,
            "blood_moon_timer": 0,
            "biome": "normal",
            "event": None,
            "special": None,
            "special_timer": 0
        }
        
        # Market & Crafting (Wave bilgisinden sonra çağrılmalı!)
        self.refresh_market()
        # Sadece temel Orblar markette satılır, Özel ve Lanetli olanlar düşürülmeli (GDD 62)
        self.orb_market = [o for o in self.item_system.orbs if o['orb_id'] not in ['special_orb', 'corrupted_orb']] 
        for orb in self.orb_market: orb['price'] = orb.get('price', 500) # Sync prices

        self.stats = {
            'total_damage_dealt': 0,
            'total_damage_taken': 0,
            'enemies_killed': 0,
            'gold_earned': 0
        }

        self.kill_streak = 0
        self.streak_timer = 0
        self.entity_id_counter = 0
        self.arena_size = 5000
        
        # Grid System for Collision (Spatial Partitioning)
        self.grid_size = 128
        self.grid = {}
        self.cheat_mode = False # Hile Modu (GDD 42)

    def setup_boss_test(self):
        """Skip directly to the boss fight with decent gear."""
        self.enemies = [] 
        self.projectiles = []
        self.items_on_ground = []
        self.projectile_pool.clear()
        
        self.wave["level"] = 9
        self.wave["enemies_to_spawn"] = 0
        self.wave["total_to_spawn"] = 0
        self.wave["spawn_timer"] = 0
        
        p = self.players[self.local_player_id]
        
        # Give some items
        items_to_give = [
            self.item_system.generate(mf_value=5.0, is_shop=True, shop_rarity=4, difficulty=self.wave["current_diff"], wave_level=self.wave["level"]),
            self.item_system.generate(mf_value=5.0, is_shop=True, shop_rarity=3, difficulty=self.wave["current_diff"], wave_level=self.wave["level"]),
            self.item_system.generate(mf_value=5.0, is_shop=True, shop_rarity=3, difficulty=self.wave["current_diff"], wave_level=self.wave["level"])
        ]
        for it in items_to_give:
            p.add_item(it)
            p.inv_manager.equip(it) # Auto equip
        
        p.gold = 5000 # For skills/market
        p.hp = p.max_hp
        
        # Teleport player to the center arena
        p.x, p.y = 2500, 2800
        print("Boss Test Mode Prepared (Wave 9 -> 10 transition next frame)")

    def update(self, dt):
        if self.state != "PLAYING":
            return
            
        p = self.players[self.local_player_id]
        # Kill Streak (Combo) Update
        if self.kill_streak > 0:
            self.streak_timer -= dt
            if self.streak_timer <= 0:
                self.kill_streak = 0
                p._base_speed_mod = 1.0 # Hız bonusunu sıfırla
            else:
                # Combo hız bonusu (Max %50)
                p._base_speed_mod = 1.0 + min(0.5, self.kill_streak * 0.02)
        else:
            p._base_speed_mod = 1.0
        
        # 0. Tehlikeleri Güncelle (GDD 17)
        self.hazard_spawn_timer -= dt
        if self.hazard_spawn_timer <= 0:
            self.spawn_random_hazard()
            self.hazard_spawn_timer = random.uniform(10, 15)
            
        for h in self.hazards[:]:
            h.update(dt, list(self.players.values()), self.enemies, self)
            if not h.active:
                self.hazards.remove(h)
                
        # Kan Ayı Sayacı
        if self.wave["is_blood_moon"]:
            self.wave["blood_moon_timer"] -= dt
            if self.wave["blood_moon_timer"] <= 0:
                self.wave["is_blood_moon"] = False
            
        p = self.players[self.local_player_id]
        p.update(dt, self)
        
        # Sınıf Evrimi Kontrolü (Level 20)
        if p.level >= 20 and not getattr(p, "evolution", ""):
            self.state = "EVOLUTION_SELECT"
            return
        
        # Player Death Check (GDD 42)
        if p.hp <= 0 and self.state != "GAMEOVER":
            if not getattr(self, 'cheat_mode', False):
                self.state = "GAMEOVER"
                
                # META PROGRESSION: Earn crystals on death
                crystals_earned = self.wave["level"] * 5 + self.kill_streak * 2
                try:
                    meta = self.save_manager.load_meta()
                    meta["crystals"] = meta.get("crystals", 0) + crystals_earned
                    self.save_manager.save_meta(meta)
                    print(f"GAMEOVER! {crystals_earned} Kan Kristali kazanıldı.")
                except Exception as e:
                    print("Meta save error:", e)
            else:
                p.hp = 1 # Keep alive
                
        # Hile Modu Uygulama
        if getattr(self, 'cheat_mode', False):
            self.handle_cheat_mode(p)
        
        # Wave Management
        if self.wave["enemies_to_spawn"] > 0:
            self.wave["spawn_timer"] -= dt
            if self.wave["spawn_timer"] <= 0:
                spawned = self.spawn_enemy()
                if spawned is None: spawned = 1
                self.wave["enemies_to_spawn"] -= spawned
                # Tüm dalganın belirlenen süre içinde doğması için dinamik interval hesapla
                # İlk 5 wave için 20 saniye, sonrakiler için 10 saniye
                wave_duration = 20.0 if self.wave.get("level", 1) <= 5 else 10.0
                interval = wave_duration / max(1, self.wave["total_to_spawn"])
                self.wave["spawn_timer"] = interval * spawned
                
                if not self.wave.get("bounty_assigned"):
                    valid_enemies = [e for e in self.enemies if not getattr(e, 'is_trap', False) and not getattr(e, 'is_pillar', False) and getattr(e, 'type', '') != "boss"]
                    if valid_enemies:
                        bounty_target = random.choice(valid_enemies)
                        bounty_target.is_bounty = True
                        bounty_target.gold_reward = getattr(bounty_target, 'gold_reward', 10) * 2
                        bounty_target.max_hp *= 1.5
                        bounty_target.hp = bounty_target.max_hp
                        self.wave["bounty_assigned"] = True
        elif len([e for e in self.enemies if not e.dead and not getattr(e, 'is_trap', False) and not getattr(e, 'is_pillar', False)]) == 0:
            self.next_wave()

        # Update Enemies
        for e in self.enemies:
            e.update(dt, self)
            
        if hasattr(self, '_pending_spawns') and self._pending_spawns:
            self.enemies.extend(self._pending_spawns)
            self._pending_spawns.clear()
        
        for proj in self.projectiles:
            proj.update(dt, self)
        
        self.projectile_pool.update(dt, self)
            
        for it in self.items_on_ground:
            it.update(dt, self)
            
        for t in self.turrets:
            t.update(dt, self)
            
        # Update Clouds (AOE DOT)
        for cl in self.clouds[:]:
            cl.update(dt, self)
            if cl.dead:
                self.clouds.remove(cl)
            
        # Update Shake
        if self.shake_timer > 0:
            self.shake_timer -= dt
            
        # Update Minions
        for m in self.minions:
            m.update(dt, self)
            
        # Update Particles
        for p in self.particles[:]:
            p['x'] += p['vx'] * dt * 60
            p['y'] += p['vy'] * dt * 60
            p['timer'] -= dt
            if p['timer'] <= 0:
                self.particles.remove(p)
            
        # Update Visual Events
        for ev in self.events[:]:
            ev['timer'] -= dt
            if ev['timer'] <= 0:
                self.events.remove(ev)
            elif ev['type'] == 'damage_text':
                ev['y'] -= dt * 40 # Upward movement
            
        # Collision & Separation
        self.update_grid()
        self.apply_separation(dt)

        # Cleanup
        self.enemies = [e for e in self.enemies if not e.dead]
        self.projectiles = [p for p in self.projectiles if not p.dead]
        self.items_on_ground = [it for it in self.items_on_ground if not it.dead]
        self.turrets = [t for t in self.turrets if not t.dead]

    def spawn_random_hazard(self):
        from logic.hazards import Hazard
        types = ["mud", "fire", "ice", "lightning"]
        h_type = random.choice(types)
        hx = random.randint(300, 4700)
        hy = random.randint(300, 4700)
        self.hazards.append(Hazard(hx, hy, h_type))
        print(f"Hazard Spawned: {h_type} at {hx},{hy}")

    def trigger_shake(self, intensity):
        if self.settings['shake']:
            self.shake_timer = 0.1 # Sarsıntı süresini daha da azalttık
            self.shake_intensity = intensity * 0.15 # Şiddeti %85 azalttık (Çok hafif bir titreme)

    def _apply_global_modifiers(self, enemy):
        """Uygulanabilirse düşmana biyom, elit modifikatörleri ve wave eventleri ekler."""
        if hasattr(self, 'biome_system'):
            self.biome_system.apply_enemy_bonus(enemy, self.wave["level"])
        
        # Dalga Olayları (Wave Events)
        if self.wave.get("event"):
            evt = self.wave["event"]
            if evt.get("enemy_speed"): enemy.speed *= evt["enemy_speed"]
            if evt.get("gold_mult"): enemy.gold_reward = getattr(enemy, 'gold_reward', 10) * evt["gold_mult"]
            if evt.get("enemy_hp_mult"):
                enemy.max_hp *= evt["enemy_hp_mult"]
                enemy.hp = enemy.max_hp
            if evt.get("force_elite") and not getattr(enemy, 'is_trap', False) and enemy.type not in ["boss", "loot_goblin"]:
                enemy.type = "elite"
                enemy.max_hp *= 5
                enemy.hp = enemy.max_hp
                enemy.speed *= 0.8
                enemy.radius *= 1.5
                enemy.dmg *= 2
                enemy.color = (192, 57, 43)
                enemy.xp_reward *= 3
        
        # Boss, tuzak veya özel tiplere elit uygulamayalım (eğer event ile elit olmadıysa)
        if getattr(enemy, 'is_trap', False) or enemy.type in ["boss", "loot_goblin"]:
            return
            
        if EliteSystem.should_apply(self.wave["level"]):
            EliteSystem.apply_modifier(enemy, self.wave["level"])

    def spawn_enemy(self, enemy_type=None):
        # Wave 10 is strictly for EchelionFinrod
        if self.wave["level"] == 10 and enemy_type != "boss":
            return 0
            
        p = self.players[self.local_player_id]
        # Küresel Spawn: Haritanın her yerinde çıkabilirler
        # Oyuncunun çok yakınında (250 birim) çıkmasını engelle
        ex, ey = 0, 0
        while True:
            ex = random.randint(100, 4900)
            ey = random.randint(100, 4900)
            if math.hypot(ex - p.x, ey - p.y) > 250:
                break
        
        # Arena sınırlarına hapset (5000x5000)
        ex = max(100, min(4900, ex))
        ey = max(100, min(4900, ey))
        
        # Eğer tip belirtilmediyse dalga havuzundan seç
        if enemy_type is None:
            pool = self._get_wave_spawn_pool()
            enemy_type = random.choice(pool)

        wave_lvl = self.wave["level"]

        # SWARM BAT: Tek spawn yerine 5-7'li sürü
        if enemy_type == "swarm_bat":
            count = random.randint(5, 8)
            for i in range(count):
                self.entity_id_counter += 1
                # ex, ey merkezli rastgele dağılım
                bx = ex + random.uniform(-60, 60)
                by = ey + random.uniform(-60, 60)
                bat = Enemy(self.entity_id_counter, bx, by, self, type="swarm_bat", wave_level=wave_lvl)
                self._apply_global_modifiers(bat)
                # Her yarasa farklı orbit fazında başlasın
                bat.orbit_phase = random.uniform(0, math.pi * 2)
                self.enemies.append(bat)
            return count  # Tek spawn değil, grup spawn, çık

        # PACK LEADER: Beraberinde 3 normal düşman getir
        if enemy_type == "pack_leader":
            self.entity_id_counter += 1
            leader = Enemy(self.entity_id_counter, ex, ey, self, type="pack_leader", wave_level=wave_lvl)
            self._apply_global_modifiers(leader)
            self.enemies.append(leader)
            for _ in range(3):
                self.entity_id_counter += 1
                escort_angle = random.uniform(0, math.pi * 2)
                nx = ex + math.cos(escort_angle) * 60
                ny = ey + math.sin(escort_angle) * 60
                escort = Enemy(self.entity_id_counter, nx, ny, self, type="barrel", wave_level=wave_lvl)
                self._apply_global_modifiers(escort)
                self.enemies.append(escort)
            return 4

        # Normal tek spawn
        self.entity_id_counter += 1
        if enemy_type == "boss":
            from entities.boss import AbyssalLord
            new_enemy = AbyssalLord(self.entity_id_counter, ex, ey, self, wave_level=wave_lvl)
            # Boss modifikasyonu yok
        else:
            new_enemy = Enemy(self.entity_id_counter, ex, ey, self, type=enemy_type, wave_level=wave_lvl)
            self._apply_global_modifiers(new_enemy)
        self.enemies.append(new_enemy)
        return 1
        
    def add_projectile(self, x, y, vx, vy, dmg):
        self.entity_id_counter += 1
        self.projectiles.append(Projectile(self.entity_id_counter, x, y, vx, vy, dmg))
        
    def handle_cheat_mode(self, player):
        """Hile modu aktifken kaynakları maksimize eder."""
        player.gold = max(player.gold, 999999)
        player.skill_points = max(player.skill_points, 99)
        player.is_invulnerable = True # God Mode
        
    def kill_enemy(self, enemy):
        # NOT: enemy.dead kontrolü burada yapılmamalı çünkü projeyle vurulduğunda take_damage'de True yapılıyor
        # Sadece bir kere ödül vermek için yeni bir flag kullanalım
        if getattr(enemy, 'looted', False): return
        enemy.looted = True
        enemy.dead = True
        
        p = self.players[self.local_player_id]
        
        # Kill Speed Boost (On Kill temporary speed buff)
        speed_boost = p.stats.get("killSpeedBoost", 0)
        if speed_boost > 0:
            from logic.status_effects import StatusEffect
            p.effect_manager.add_effect(StatusEffect("Kill Speed", 2.0, speed_mult=(1.0 + speed_boost), color=(255, 255, 0)))
            
        # Minyon Dönüşümü (Ölümsüz Ordu vs.)
        respawn_chance = getattr(p, "minion_respawn_chance", 0.0)
        if respawn_chance > 0 and random.random() < respawn_chance:
            from entities.minion import Minion
            m = Minion(self.entity_id_counter, enemy.x, enemy.y)
            self.minions.append(m)
            self.entity_id_counter += 1
            self.add_event("damage_text", enemy.x, enemy.y - 20, value="DIRILDI!", color=(150, 50, 200), timer=0.8)
            
        # --- KAN PARTİKÜLLERİ ---
        for _ in range(8):
            angle = random.random() * math.pi * 2
            speed = random.uniform(2, 5)
            self.particles.append({
                'x': enemy.x, 'y': enemy.y,
                'vx': math.cos(angle) * speed, 'vy': math.sin(angle) * speed,
                'timer': random.uniform(0.3, 0.8),
                'color': (180, 0, 0), # Kan Kırmızısı
                'size': random.randint(2, 4)
            })

        # BARREL PATLAMASI (Menzil ve Hasar Nerflendi: 200->120, 50->20)
        if enemy.type == "barrel":
            if math.hypot(p.x - enemy.x, p.y - enemy.y) < 120:
                p.take_damage(20)
            self.add_event("shockwave", enemy.x, enemy.y, radius=80, timer=0.5, color=(255, 100, 0))

        # --- ÖDÜL SKALASI (Zorluk ve Wave Basamağına Göre) ---
        diff_rewards = {
            "Normal":    0.5,
            "Hard":      1.5,
            "Very Hard": 3.5,
            "Impossible": 10.0
        }
        r_mod = diff_rewards.get(self.wave["current_diff"], 0.5)
        
        # Basamak Çarpanı (Her 10 wave'de bir %20 artış)
        step_level = (self.wave["level"] - 1) // 10
        reward_step_mult = (1.2 ** step_level)

        # YENİ DÜŞMAN ÖZEL DURUMLARI
        if hasattr(enemy, 'slime_tier'):
            from entities.enemy import Enemy
            if not hasattr(self, '_pending_spawns'):
                self._pending_spawns = []
            if enemy.slime_tier == 3:
                self.entity_id_counter += 1
                m1 = Enemy(self.entity_id_counter, enemy.x - 20, enemy.y, self, type="splitting_slime_medium", wave_level=self.wave["level"])
                self._pending_spawns.append(m1)
                self.entity_id_counter += 1
                m2 = Enemy(self.entity_id_counter, enemy.x + 20, enemy.y, self, type="splitting_slime_medium", wave_level=self.wave["level"])
                self._pending_spawns.append(m2)
            elif enemy.slime_tier == 2:
                self.entity_id_counter += 1
                s1 = Enemy(self.entity_id_counter, enemy.x - 15, enemy.y, self, type="splitting_slime_small", wave_level=self.wave["level"])
                self._pending_spawns.append(s1)
                self.entity_id_counter += 1
                s2 = Enemy(self.entity_id_counter, enemy.x + 15, enemy.y, self, type="splitting_slime_small", wave_level=self.wave["level"])
                self._pending_spawns.append(s2)

        if getattr(enemy, 'no_drop', False):
            return

        if enemy.type == "loot_goblin":
            item_data = self.item_system.generate(
                    mf_value=p.stats.get("magicFind", 1.0), 
                    difficulty=self.wave["current_diff"], 
                    wave_level=self.wave["level"]
            )
            item_data['rarity'] = "Rare"
            self.entity_id_counter += 1
            self.items_on_ground.append(GroundItem(self.entity_id_counter, enemy.x, enemy.y, item_data))
            
            gold_value = int(500 * reward_step_mult * r_mod * (1.0 + p.stats.get("goldGain", 0)))
            self.entity_id_counter += 1
            self.items_on_ground.append(GroundItem(self.entity_id_counter, enemy.x + 20, enemy.y, 
                                                 {'type': 'gold', 'value': gold_value, 'rarity': 'Normal'}))

        # ALTIN DÜŞÜRME (Fiziksel Drop)
        if not enemy.is_trap:
            base_gold = 10 * r_mod * reward_step_mult
            gold_value = int(base_gold * (1.0 + p.stats.get("goldGain", 0)))
            self.entity_id_counter += 1
            self.items_on_ground.append(GroundItem(self.entity_id_counter, enemy.x, enemy.y, 
                                                 {'type': 'gold', 'value': gold_value, 'rarity': 'Normal'}))
            
            # İksir (Potion) Düşürme (%6 ihtimal)
            if random.random() < 0.06:
                self.entity_id_counter += 1
                self.items_on_ground.append(GroundItem(self.entity_id_counter, enemy.x + random.uniform(-30, 30), enemy.y + random.uniform(-30, 30), {'type': 'potion', 'rarity': 'Normal'}))
            
            # --- ÖZ (ESSENCE) DÜŞÜRME ---
            # Bosslar öldüğünde Aura sistemi açılır
            if enemy.type == "boss" and self.wave["level"] >= 10:
                if not p.is_essence_system_unlocked:
                    p.is_essence_system_unlocked = True
                    self.add_event("damage_text", enemy.x, enemy.y - 80, value="AURA SİSTEMİ AÇILDI!", color=(155, 89, 182), scale=1.5, timer=2.0)

            # Bosslar %100, Elitler %15 şansla Öz düşürür (Sadece Wave 10+)
            essence_chance = 0
            if self.wave["level"] >= 10:
                essence_chance = 1.0 if enemy.type == "boss" else (0.15 if enemy.type == "elite" else 0.0)
            
            if random.random() < essence_chance:
                essence_bases = [b for b in self.item_system.bases if b.get('type') == 'essence']
                if essence_bases:
                    base = random.choice(essence_bases)
                    self.entity_id_counter += 1
                    item_data = base.copy()
                    if 'rarity' not in item_data: item_data['rarity'] = 'Normal'
                    self.items_on_ground.append(GroundItem(self.entity_id_counter, enemy.x + 20, enemy.y + 20, item_data))
            
            # XP Kazanımı (Basamak çarpanıyla senkronize)
            xp_to_give = 20 * reward_step_mult * r_mod
            p.gain_xp(xp_to_give * (1.0 + p.stats.get("xpGain", 0)))
            
            # --- GÜNLÜK GÖREV TAKİBİ ---
            self.track_quest("kill", 1)
            if enemy.type == "elite":
                self.track_quest("kill_elite", 1)
            if enemy.type == "boss":
                self.track_quest("kill_boss", 1)
            # Low HP kill
            if p.hp / max(1, p.max_hp) < 0.20:
                self.track_quest("kill_while_low", 1)

            # --- KILL STREAK ---
            self.kill_streak += 1
            self.stats['enemies_killed'] = self.stats.get('enemies_killed', 0) + 1
            self.streak_timer = 3.5 # 3.5 saniye kill gelmezse biter
            
            if self.kill_streak % 10 == 0:
                self.add_event("damage_text", p.x, p.y - 60, value=f"{self.kill_streak} COMBO!", color=(255, 165, 0), timer=1.5)
                # Küçük bir can yenileme bonusu (GDD 62)
                p.hp = min(p.max_hp, p.hp + p.max_hp * 0.05)
                # Combo kristal milestone
                if self.kill_streak % 50 == 0:
                    try:
                        meta = self.save_manager.load_meta()
                        meta["crystals"] = meta.get("crystals", 0) + 1
                        self.save_manager.save_meta(meta)
                        self.add_event("damage_text", p.x, p.y - 80, value="+1💎 COMBO BONUS", color=(100, 220, 255), timer=1.5)
                    except Exception:
                        pass
                
            # --- EŞYA DÜŞÜRME (LOOT) ---
            mf_mult = 1 + math.sqrt(max(0, p.stats.get("magicFind", 1.0) - 1))
            # Eşya düşürme şansı da her 10 wave'de bir %20 artar
            base_drop = (0.20 if enemy.type == "elite" else 0.04) * r_mod * reward_step_mult
            drop_chance = base_drop * mf_mult
            
            if enemy.type == "boss":
                drop_chance = 1.0 # Boss %100 şans
                
            if random.random() < drop_chance:
                item_data = self.item_system.generate(
                    mf_value=p.stats.get("magicFind", 1.0), 
                    difficulty=self.wave["current_diff"], 
                    wave_level=self.wave["level"],
                    is_boss=(enemy.type == "boss")
                )
                
                # Oto-Satış ve Limit Mantığı
                rarities = ['Normal', 'Magic', 'Rare', 'Unique']
                r_idx = rarities.index(item_data.get('rarity', 'Normal')) if item_data.get('rarity') in rarities else -1
                
                # Özel Eşyalar: Setler, Orblar ve Özler asla otomatik satılmaz
                is_special = bool(item_data.get('setTag')) or item_data.get('type') in ['orb', 'essence'] or r_idx == -1
                auto_mode = getattr(p, 'auto_sell_mode', 0)
                
                # Kan Ayı Loot Bonusu (2x Loot)
                if self.wave["is_blood_moon"]:
                    self.entity_id_counter += 1
                    self.items_on_ground.append(GroundItem(self.entity_id_counter, enemy.x, enemy.y, self.item_system.generate(mf_value=p.stats.get("magicFind", 1.0), wave_level=self.wave["level"])))

                # Kümülatif Oto-Satış: Seçilen mod ve altındakileri sat
                should_auto_sell = not is_special and (r_idx >= 0 and r_idx < auto_mode)
                if len(self.items_on_ground) >= 150 and not is_special:
                    should_auto_sell = True
                    
                if should_auto_sell:
                    gold_val = max(1, item_data.get('price', 50) // 2)
                    p.gold += gold_val
                    self.add_event("damage_text", enemy.x, enemy.y - 20, value=f"+{gold_val} G", color=(241, 196, 15), timer=0.5)
                else:
                    self.entity_id_counter += 1
                    self.items_on_ground.append(GroundItem(self.entity_id_counter, enemy.x + random.uniform(-40, 40), enemy.y + random.uniform(-40, 40), item_data))

    def gold_to_crystal(self, amount=1000):
        p = self.players[self.local_player_id]
        if p.gold >= amount:
            p.gold -= amount
            try:
                meta = self.save_manager.load_meta()
                meta["crystals"] = meta.get("crystals", 0) + 5
                self.save_manager.save_meta(meta)
                self.add_event("damage_text", p.x, p.y-40, value="+5 Kristal", color=(255, 100, 100), timer=1.0)
                return True
            except Exception as e:
                print("Crystal conversion error:", e)
                return False
        return False

    def refresh_market(self):
        p = self.players[self.local_player_id]
        self.market_inventory = []
        shop_rarity = int(p.stats.get("shopRarity", 1))
        # Seviye bazlı + ShopRarity bazlı eşya sayısı
        count = 3 + shop_rarity
        for _ in range(count):
            item = self.item_system.generate(is_shop=True, shop_rarity=shop_rarity, difficulty=self.wave["current_diff"], wave_level=self.wave["level"])
            self.market_inventory.append(item.copy())
            
    def manual_reroll_market(self):
        p = self.players[self.local_player_id]
        wave_level = self.wave.get("level", 1)
        cost = 500 + max(0, (wave_level - 1) * 400)
        if p.gold >= cost:
            p.gold -= cost
            self.refresh_market()
            print("Pazar Yenilendi! (-500 Altın)")
            return True
        return False

    def buy_item(self, idx, tab="items"):
        market_list = self.market_inventory if tab == "items" else self.orb_market
        if idx < 0 or idx >= len(market_list): return False
        
        p = self.players[self.local_player_id]
        item = market_list[idx]
        
        if p.gold >= item.get('price', 500):
            # Eşyayı oyuncuya ekle (Kopya alarak)
            if p.add_item(item.copy()):
                p.gold -= item.get('price', 500)
                
                # Marketten eşyayı siliyoruz
                if tab == "items":
                    self.market_inventory.pop(idx)
                else:
                    self.orb_market.pop(idx)
                
                self.add_event("damage_text", p.x, p.y-40, value="Satın Alındı!", color=(46, 204, 113))
                return True
        return False

    def add_event(self, event_type, x, y, **kwargs):
        event = {"type": event_type, "x": x, "y": y, "timer": kwargs.get("timer", 0.5)}
        event.update(kwargs)
        self.events.append(event)

    def apply_enemy_modifiers(self, enemy):
        if hasattr(self, 'biome_system'):
            self.biome_system.apply_modifiers(enemy)
            
    def track_quest(self, event_type, value=1):
        """Helper to track quests and save meta"""
        try:
            meta = self.save_manager.load_meta()
            crystals_earned = self.quest_system.track(event_type, value, meta)
            if crystals_earned > 0:
                meta["crystals"] = meta.get("crystals", 0) + crystals_earned
                self.add_event("damage_text", self.width//2, self.height//2 + 80, value=f"+{crystals_earned} KRİSTAL (GÖREV)", color=(100, 220, 255), timer=2.0)
            meta = self.quest_system.save_to_meta(meta)
            self.save_manager.save_meta(meta)
        except Exception as e:
            print("Quest tracking error:", e)
        
    def next_wave(self):
        self.wave["level"] += 1
        
        # 1. Biyom Değişimi
        if hasattr(self, 'biome_system'):
            new_biome = self.biome_system.update_biome(self.wave["level"])
            if new_biome:
                self.wave["biome"] = self.biome_system.current_biome_id
                self.add_event("damage_text", self.width // 2, self.height // 2 - 100, value=f"🌍 Yeni Biyom: {new_biome['name']}", color=(100, 255, 100), timer=4.0)

        # 2. Özel Dalgalar (Special Waves)
        self.wave["special"] = None
        if self.wave["level"] in self.SPECIAL_WAVES:
            self.wave["special"] = self.SPECIAL_WAVES[self.wave["level"]]
            self.wave["special_timer"] = self.wave["special"]["duration"]

        # 3. Dalga Olayları (Wave Events) - %40 İhtimal (Özel dalga veya boss dalgası değilse)
        self.wave["event"] = None
        if not self.wave["special"] and self.wave["level"] % 10 != 0:
            if random.random() < 0.40:
                self.wave["event"] = random.choice(self.WAVE_EVENTS)

        # Yaratık sayısını 5 kat artır (15 -> 75 taban sayı)
        count = int((15 + self.wave["level"] * 8) * 5 * 0.85) 
        if self.wave["event"] and self.wave["event"].get("enemy_count_mult"):
            count *= self.wave["event"]["enemy_count_mult"]
            
        self.wave["enemies_to_spawn"] = count
        self.wave["total_to_spawn"] = count
        self.wave["spawn_timer"] = 1.0
        
        if self.wave["level"] % 5 == 0:
            self.wave["is_blood_moon"] = True
            self.wave["blood_moon_timer"] = 45.0 # 45 saniye sürer
            self.refresh_market()
            
        self.spawn_traps()
        
        # New Wave Notification
        txt = f"DALGA {self.wave['level']} BAŞLIYOR!"
        if self.wave["is_blood_moon"]:
            txt = "⚠️ LANETLİ KAN AYI BAŞLADI! ⚠️"
        if self.wave["special"]:
            txt = f"🌟 ÖZEL DALGA: {self.wave['special']['name']}! 🌟"
            
        self.add_event("damage_text", self.width // 2, self.height // 2, value=txt, color=(231, 76, 60), timer=3.0)
        
        if self.wave["event"]:
            self.add_event("damage_text", self.width // 2, self.height // 2 + 30, value=self.wave["event"]["desc"], color=(255, 165, 0), timer=4.0)
        
        # --- BOSS WAVE EVERY 10 ---
        if self.wave["level"] % 10 == 0:
            self.wave["enemies_to_spawn"] = 0
            self.spawn_enemy("boss")
            self.add_event("damage_text", self.width // 2, self.height // 2 + 50, value="⚠️ BOSS GELİYOR! ⚠️", color=(231, 76, 60), timer=3.0)
            
        # 4. Bounty (Wanted) Sistemi
        self.wave["bounty_assigned"] = False
            
        # 5. Pasif Kart Sistemi (Her 3 Dalgada Bir)
        if self.wave["level"] > 1 and self.wave["level"] % 3 == 0:
            cards = self.card_system.offer_cards()
            if cards:
                self.pending_cards = cards
                self.state = "CARD_SELECT"
                self.card_rerolls = 3

    def spawn_traps(self):
        self.enemies = [e for e in self.enemies if not getattr(e, 'is_trap', False)]
            
        # Lav Çukuru — Sadece tuzak olan tek varlık
        if self.wave["level"] >= 3:
            # Sayıları absürt artmasın diye max 6 ile sınırlandırıyoruz
            lava_count = min(6, max(1, self.wave["level"] // 4))
            for _ in range(lava_count):
                self.entity_id_counter += 1
                e = Enemy(self.entity_id_counter, 200 + random.random()*4600, 200 + random.random()*4600, self, type="lava_pit", wave_level=self.wave["level"])
                self.enemies.append(e)

    def _get_wave_spawn_pool(self):
        """Dalga seviyesine göre spawn havuzu oluştur."""
        wave = self.wave["level"]
        # 'normal' kaldırıldı, havuz okçu ve barrel (dash) ağırlıklı
        pool = ["barrel"] * 6 + ["toxic_pit"] * 4

        if wave >= 2:
            pool += ["swarm_bat"] * 4
            pool += ["frost_crawler"] * 3
        if wave >= 3:
            pool += ["kamikaze"] * 5
        if wave >= 4:
            pool += ["shieldbearer"] * 2
            pool += ["venom_spider"] * 3
        if wave >= 5:
            pool += ["elite"] * 2
            pool += ["splitting_slime"] * 3
            pool += ["loot_goblin"] * 1
            pool += ["fire_shaman"] * 2
        if wave >= 6:
            pool += ["burrowing_worm"] * 3
            pool += ["magnetar"] * 2
        if wave >= 7:
            pool += ["pack_leader"] * 1
        if wave >= 8:
            pool += ["necromancer"] * 2
        if wave >= 10:
            pool += ["black_hole_caster"] * 2
        
        # --- WAVE 30+ YENİ DÜŞMANLAR ---
        if wave >= 30:
            pool += ["void_walker"] * 3
            pool += ["juggernaut"] * 2
            pool += ["swarm_lord"] * 1

        return pool

    def update_grid(self):
        self.grid = {}
        for e in self.enemies:
            gx, gy = int(e.x // self.grid_size), int(e.y // self.grid_size)
            key = (gx, gy)
            if key not in self.grid: self.grid[key] = []
            self.grid[key].append(e)

    def apply_separation(self, dt):
        # Separation force to prevent overlapping (The Core Difficulty Fix)
        p = self.players[self.local_player_id]
        for e in self.enemies:
            if e.is_trap: continue
            # OPTIMIZATION: Skip separation for off-screen enemies
            if math.hypot(e.x - p.x, e.y - p.y) > 1200: continue
            
            gx, gy = int(e.x // self.grid_size), int(e.y // self.grid_size)
            
            # Check neighbor cells
            for ox in range(-1, 2):
                for oy in range(-1, 2):
                    key = (gx + ox, gy + oy)
                    if key in self.grid:
                        for other in self.grid[key]:
                            if e == other or other.is_trap: continue
                            # Özel yaratıklar (Kamikaze/Barrel) veya İtileyemez Objeler (Pillar)
                            if e.type in ["kamikaze", "barrel"] or other.type in ["kamikaze", "barrel"] or getattr(other, 'is_pillar', False): continue
                            
                            dist = math.hypot(e.x - other.x, e.y - other.y)
                            min_dist = e.radius + other.radius
                            if dist < min_dist and dist > 0:
                                overlap = min_dist - dist
                                nx = (e.x - other.x) / dist
                                ny = (e.y - other.y) / dist
                                # Sıkışmayı yumuşatmak için 0.85'i 0.15'e düşürdük, böylece oyuncuya daha çok yaklaşabilirler
                                e.x += nx * overlap * 0.15
                                e.y += ny * overlap * 0.15
                                other.x -= nx * overlap * 0.15
                                other.y -= ny * overlap * 0.15

    def update_difficulty(self, new_diff):
        if self.wave["current_diff"] == new_diff: return
        self.wave["current_diff"] = new_diff
        
        # Mevcut düşmanları anlık ölçeklendir
        for e in self.enemies:
            if not e.is_trap and hasattr(e, 'apply_difficulty'):
                e.apply_difficulty(new_diff)
                
        self.add_event("damage_text", self.width//2, self.height//2, value=f"ZORLUK: {new_diff}", color=(255, 255, 255), timer=1.5)

    def draw(self, screen, camera_x, camera_y):
        # Prosedürel Zemin Çizimi (Grid)
        # TODO: Optimize with TileSprites if needed
        pass
        
    def draw_floor(self, screen, camera_x, camera_y):
        # ... (Assuming draw_floor is actually in GameScene, checking GameLogic again)
        # TODO: Optimize with TileSprites if needed
        pass
