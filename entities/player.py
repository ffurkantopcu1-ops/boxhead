import pygame
import math
import time
import random
from entities.warrior_logic import Warrior
from entities.beastmaster_logic import Beastmaster
from entities.sniper_logic import Sniper
from entities.engineer_logic import Engineer
from entities.bomber_logic import Bomber
from entities.ninja_logic import Ninja
from entities.alchemist_logic import Alchemist
from entities.sorcerer_logic import Sorcerer
from entities.bloodwalker_logic import Bloodwalker
from logic.inventory_manager import InventoryManager
from logic.save_manager import SaveManager
from logic.crystal_shop import CrystalShop

class Player:
    def __init__(self, id, x, y, class_id="warrior"):
        self.id = id
        self.x = x
        self.y = y
        self.radius = 24
        self.facing_angle = 0
        self.hp = 100
        self.max_hp = 100
        
        self.energy_shield = 0
        self.max_energy_shield = 0
        self.es_timer = 0.0
        
        # --- INITIALIZE ALL ATTRIBUTES BEFORE SPECIALIZATION ---
        self.xp = 0
        self.xp_to_next_level = 100
        # Midnight Slate: Göz yormayan, mermilerin net göründüğü modern koyu tema
        self.tile_size = 128
        self.floor_color_1 = (24, 28, 35)
        self.floor_color_2 = (28, 32, 40)
        self.grid_line_color = (35, 40, 50)
        self.gold = 0
        self.level = 1
        self.skill_points = 0
        self.last_shot_time = 0
        self.inventory = [] # Yerden toplananlar
        self.auto_attack = False
        self.i_frame_timer = 0
        self.level_up_timer = 0 # Görsel efekt için
        
        # --- META PROGRESSION UPGRADES (CrystalShop) ---
        try:
            meta = SaveManager.load_meta()
            crystal_shop = CrystalShop()
            crystal_shop.apply_to_player(meta, self)
        except Exception as e:
            print("Meta load error:", e)

        # --- KART / LANET SİSTEMİ ATRİBÜTLERİ ---
        self.damage_taken_mult = 1.0       # Cam Top, Glass Bones vb.
        self.self_dmg_on_hit = 0.0         # Double Edge
        self.poison_convert = False        # Poison Heart
        self.stun_on_crit = 0.0           # Crit Overload (sn)
        self.execute_threshold = 0.0       # Executioner (%)
        self.revive_count = 0              # Zombie Skin
        self.death_explosion = False       # Phoenix Blood
        self.passive_hp_drain = 0.0        # Death Wish (HP/sn)
        self.passive_shield_cd = 0.0       # Iron Will
        self._shield_timer = 0.0
        self.adrenaline_active = False     # Adrenaline card
        self._adrenaline_timer = 0.0
        self._adrenaline_cd = 0.0
        self.lifesteal_bonus = 0.0         # Blood Fire
        self.xp_on_hit_bonus = 0.0        # Blood Pact
        self.kill_hp_bonus = 0.0          # Cursed Blood
        self.periodic_freeze_cd = 0.0     # Frozen Time
        self._freeze_timer = 0.0
        self.lightning_proc_hits = 0       # Storm Caller
        self._lightning_counter = 0
        self.void_armor_pen = False        # Void Touch (zırh yoksay)
        self.artifact_hp_cost = 0          # Mana Overload
        self.alpha_mode = False            # Alpha Bond
        self.minion_respawn_chance = 0.0   # Undead Army
        self.minion_death_transfer = 0.0   # Spirit Link
        self.shop_discount = 0.0           # Merchant Soul
        self.pact_devil_waves = 0          # Pact Devil
        self._meta_start_card = False
        self._early_evolution = False
        self.berserker_rage = False        # Berserker Rage card flag
        self.skills_permanent = {}         # Kalıcı stat havuzu
        
        # --- ARTIFACT & ACTIVE EFFECTS ---
        self.artifact_cooldown = 0
        self.artifact_timer = 0 # Aktif efekt süresi (Görünmezlik, Kalkan vb.)
        self.is_invisible = False
        self.is_invulnerable = False
        self.fire_breath_timer = 0
        self.kill_streak = 0
        self.kill_streak_timer = 0
        
        # --- VELOCITY TRACKING FOR AI ---
        self.vx = 0
        self.vy = 0
        self.lifesteal_buffer = 0 # Birikmiş can çalma havuzu (GDD 62)
        self.lifesteal_cooldown_timer = 0 # Hasar sonrası can çalma kilidi (3 sn)
        
        # --- 56 YETENEK (MİNYON VE ELEMENTAL GÜNCELLENMİŞ VERSİYON) ---
        self.skills = [
            # HAYATTA KALMA
            { 'name': '💖 Canlılık (+40 HP)', 'stat': 'max_hp', 'val': 40, 'lvl': 0, 'max': 10, 'group': 'HAYATTA KALMA' },
            { 'name': '🌱 Yenilenme (+1.0 Rej)', 'stat': 'regen', 'val': 1.0, 'lvl': 0, 'max': 10, 'group': 'HAYATTA KALMA' },
            { 'name': '🛡️ Deri (+4 Zırh)', 'stat': 'armor', 'val': 4, 'lvl': 0, 'max': 10, 'group': 'HAYATTA KALMA' },
            { 'name': '💨 Refleks (+3% Kaçınma)', 'stat': 'dodgeChance', 'val': 0.03, 'lvl': 0, 'max': 10, 'group': 'HAYATTA KALMA' },
            { 'name': '🦇 Vampir (+2% Can Çalma)', 'stat': 'lifesteal', 'val': 0.02, 'lvl': 0, 'max': 10, 'group': 'HAYATTA KALMA' },
            { 'name': '🩺 Savaş Refleksi (+0.5 Savaş Rej)', 'stat': 'combatRegen', 'val': 0.5, 'lvl': 0, 'max': 10, 'group': 'HAYATTA KALMA' },
            { 'name': '⚡ Kalkan (+100 Max ES)', 'stat': 'maxEnergyShield', 'val': 100, 'lvl': 0, 'max': 10, 'group': 'HAYATTA KALMA' },
            { 'name': '🔋 Şarj (+20.0 ES Rej)', 'stat': 'esRegen', 'val': 20.0, 'lvl': 0, 'max': 10, 'group': 'HAYATTA KALMA' },
            { 'name': '⏱️ Adaptasyon (+0.2s ES Hızı)', 'stat': 'esDelayReduction', 'val': 0.2, 'lvl': 0, 'max': 5, 'group': 'HAYATTA KALMA' },
            
            # SALDIRI (GLOBAL VE ELEMENTEL)
            { 'name': '⚔️ Savaşçı (+15% Hasar)', 'stat': 'dmgMult', 'val': 0.15, 'lvl': 0, 'max': 10, 'group': 'SALDIRI' },
            { 'name': '📏 Menzil (+30 Yakın Menzil)', 'stat': 'meleeRange', 'val': 30, 'lvl': 0, 'max': 10, 'group': 'SALDIRI' },
            { 'name': '👊 Sert Vuruş (+10 Fiziksel Hasar)', 'stat': 'physDmgFlat', 'val': 10, 'lvl': 0, 'max': 10, 'group': 'SALDIRI' },
            { 'name': '🔥 Kıvılcım (+2 Ateş Hasarı)', 'stat': 'fireDmgFlat', 'val': 2, 'lvl': 0, 'max': 10, 'group': 'SALDIRI' },
            { 'name': '🌋 Alevin Ruhu (+10% Ateş Hasarı)', 'stat': 'fireDmgMult', 'val': 0.1, 'lvl': 0, 'max': 10, 'group': 'SALDIRI' },
            { 'name': '❄️ Buz Kristali (+2 Buz Hasarı)', 'stat': 'frostDmgFlat', 'val': 2, 'lvl': 0, 'max': 10, 'group': 'SALDIRI' },
            { 'name': 'Dondurucu Soğuk (+10% Buz Hasarı)', 'stat': 'frostDmgMult', 'val': 0.1, 'lvl': 0, 'max': 10, 'group': 'SALDIRI' },
            { 'name': '🎯 Kritik Ustası (+5% Krit Şans)', 'stat': 'critChance', 'val': 0.05, 'lvl': 0, 'max': 10, 'group': 'SALDIRI' },
            { 'name': '🗡️ Seri Vuruş (+10% Saldırı Hızı)', 'stat': 'attack_speed_bonus', 'val': 0.1, 'lvl': 0, 'max': 5, 'group': 'SALDIRI' },
            { 'name': '🏹 Delici (+1 Pierce)', 'stat': 'pierce', 'val': 1, 'lvl': 0, 'max': 5, 'group': 'SALDIRI' },
            { 'name': '☄️ Seken Mermiler (+1 Sekme)', 'stat': 'bounce', 'val': 1, 'lvl': 0, 'max': 6, 'group': 'SALDIRI' },
            { 'name': '🏹 Gerilim (+1 Mermi Hızı)', 'stat': 'bullet_speed', 'val': 1, 'lvl': 0, 'max': 5, 'group': 'SALDIRI' },
            { 'name': '🌪️ Geniş Alan (+15% AoE)', 'stat': 'aoe_bonus', 'val': 0.15, 'lvl': 0, 'max': 10, 'group': 'SALDIRI' },
            { 'name': '🔀 Çok Namlulu (+1 Mermi)', 'stat': 'projectileCount', 'val': 1, 'lvl': 0, 'max': 4, 'group': 'SALDIRI' },
            { 'name': '💀 Kıyım Zevki (+30% Kill Speed)', 'stat': 'killSpeedBoost', 'val': 0.3, 'lvl': 0, 'max': 5, 'group': 'SALDIRI' },
            
            # YARDIMCI
            { 'name': '🌋 Elementalist (+15% Elem. Hasar)', 'stat': 'elementDmgMult', 'val': 0.15, 'lvl': 0, 'max': 10, 'group': 'YARDIMCI' },
            { 'name': '🦠 Zehirkâr (+15% DoT Hasarı)', 'stat': 'dotDmgMult', 'val': 0.15, 'lvl': 0, 'max': 10, 'group': 'YARDIMCI' },
            { 'name': '👟 Atletizm (+0.2 Hız)', 'stat': 'speed', 'val': 0.2, 'lvl': 0, 'max': 10, 'group': 'YARDIMCI' },
            { 'name': '🍀 Talih (+15% Eşya Bulma)', 'stat': 'magicFind', 'val': 0.15, 'lvl': 0, 'max': 5, 'group': 'YARDIMCI' },
            { 'name': '🛝 Kervan Nadirliği (+1 Kervan Nadir.)', 'stat': 'shopRarity', 'val': 1, 'lvl': 0, 'max': 10, 'group': 'YARDIMCI' },
            { 'name': '📜 Alim (+15% XP Kazanımı)', 'stat': 'xpGain', 'val': 0.15, 'lvl': 0, 'max': 5, 'group': 'YARDIMCI' },
            { 'name': '💰 Tüccâr (+20% Altın Kazanımı)', 'stat': 'goldGain', 'val': 0.2, 'lvl': 0, 'max': 5, 'group': 'YARDIMCI' },
            { 'name': '🧲 Mıknatıs (+50 Toplama Alanı)', 'stat': 'magnetRadius', 'val': 50, 'lvl': 0, 'max': 10, 'group': 'YARDIMCI' },
            
            # TARET
            { 'name': '🤖 Mühendis (+50 Taret HP)', 'stat': 'turretMaxHp', 'val': 50, 'lvl': 0, 'max': 10, 'group': 'TARET' },
            { 'name': '🔫 Gelişmiş Taret (+20% Taret Hasar)', 'stat': 'turretDmg', 'val': 0.2, 'lvl': 0, 'max': 10, 'group': 'TARET' },
            { 'name': '⚙️ Otomatik Mekanizma (+15% Taret Hızı)', 'stat': 'turretRate', 'val': 0.15, 'lvl': 0, 'max': 10, 'group': 'TARET' },
            { 'name': '📡 Kapasite (+1 Taret Limiti)', 'stat': 'turretLimit', 'val': 1, 'lvl': 0, 'max': 3, 'group': 'TARET' },
            
            # MİNYON (YOLDAŞLAR)
            { 'name': '💂 Ordulu (+1 Minyon Sayı)', 'stat': 'minionCount', 'val': 1, 'lvl': 0, 'max': 2, 'group': 'MİNYON' },
            { 'name': '🎖️ Komutan (+25% Minyon Hasar)', 'stat': 'minionDamage', 'val': 0.25, 'lvl': 0, 'max': 10, 'group': 'MİNYON' },
            { 'name': '⚡ Çevik Pençeler (+20% Minyon Hızı)', 'stat': 'minionRate', 'val': 0.2, 'lvl': 0, 'max': 10, 'group': 'MİNYON' },
            { 'name': '💖 Fedai (+80 Minyon Canı)', 'stat': 'minionMaxHp', 'val': 80, 'lvl': 0, 'max': 10, 'group': 'MİNYON' },
            { 'name': '📏 Keskin Gözler (+15% Minyon Menzil)', 'stat': 'minionRange', 'val': 0.15, 'lvl': 0, 'max': 10, 'group': 'MİNYON' },
            { 'name': '👊 Pençe Eğitimi (+5 Minyon Fiz. Hasar)', 'stat': 'minionPhysDmgFlat', 'val': 5, 'lvl': 0, 'max': 10, 'group': 'MİNYON' },
            { 'name': '⚔️ Keskin Pençe (+10% Minyon Fiz. Hasar)', 'stat': 'minionPhysDmgMult', 'val': 0.1, 'lvl': 0, 'max': 10, 'group': 'MİNYON' },
            { 'name': '🔥 Kor Pençe (+2 Minyon Ateş Hasarı)', 'stat': 'minionFireDmgFlat', 'val': 2, 'lvl': 0, 'max': 10, 'group': 'MİNYON' },
            { 'name': '🌋 Volkanik Öfke (+10% Minyon Ateş Hasarı)', 'stat': 'minionFireDmgMult', 'val': 0.1, 'lvl': 0, 'max': 10, 'group': 'MİNYON' },
            { 'name': '❄️ Buzul Pençe (+2 Minyon Buz Hasarı)', 'stat': 'minionFrostDmgFlat', 'val': 2, 'lvl': 0, 'max': 10, 'group': 'MİNYON' },
            { 'name': '🧊 Arktik Av (+10% Minyon Buz Hasarı)', 'stat': 'minionFrostDmgMult', 'val': 0.1, 'lvl': 0, 'max': 10, 'group': 'MİNYON' },
            { 'name': '☄️ Minyon Sekmesi (+1 Sekme)', 'stat': 'minionBounce', 'val': 1, 'lvl': 0, 'max': 5, 'group': 'MİNYON' },
            { 'name': '🏹 Minyon Delmesi (+1 Delme)', 'stat': 'minionPierce', 'val': 1, 'lvl': 0, 'max': 5, 'group': 'MİNYON' },
            { 'name': '🐉 Minyon Mermisi (+1 Mermi)', 'stat': 'minionProjectileCount', 'val': 1, 'lvl': 0, 'max': 2, 'group': 'MİNYON' }
        ]
        
        self.class_id = class_id
        self.class_name = self.class_id
        self.inv_manager = InventoryManager(self)
        self.stats = {} 
        
        # --- DASH (ATILMA) ---
        self.dash_timer = 0.0
        self.dash_active_timer = 0.0 # Atılma anı sayacı
        self.dash_cooldown = 6.0    # 6 saniye bekleme
        self.dash_duration = 0.15   # 0.15 saniye atılma hızı
        
        from logic.status_effects import StatusEffectManager
        self.effect_manager = StatusEffectManager()
        self.speed_mod = 1.0
        self.is_silenced = False
        self.is_stunned = False
        
        self.init_class_specialization()
        
    def init_class_specialization(self):
        # --- BAŞLANGIÇ EKİPMANLARI ---
        cn = self.class_id
        starting_weapon = None
        
        if cn == "warrior":
            starting_weapon = {"name": "Eski Kılıç", "type": "weapon", "isMelee": True, "rarity": "Normal", "itemBase": {"physDmg": 12, "meleeRange": 50}, "prefixes": [], "suffixes": []}
        elif cn == "beastmaster":
            starting_weapon = {"name": "Küçük Kurt", "type": "pet", "rarity": "Normal", "itemBase": {"minionDamage": 0, "minionMaxHp": 50}, "prefixes": [], "suffixes": []}
        elif cn == "sniper":
            starting_weapon = {"name": "Basit Arbalet", "type": "weapon", "isRanged": True, "rarity": "Normal", "itemBase": {"physDmg": 18}, "prefixes": [], "suffixes": []}
        elif cn == "ninja":
            starting_weapon = {"name": "Paslı Katana", "type": "weapon", "isMelee": True, "rarity": "Magic", "itemBase": {"physDmg": 15, "attackCooldown": 450}, "prefixes": [], "suffixes": []}
        elif cn == "alchemist":
            starting_weapon = {"name": "Zehir Şişesi", "type": "weapon", "isBomb": True, "rarity": "Normal", "itemBase": {"poisonDps": 8}, "prefixes": [], "suffixes": []}
        elif cn == "sorcerer":
            starting_weapon = {"name": "Sihir Asası", "type": "weapon", "isRanged": True, "rarity": "Magic", "itemBase": {"physDmg": 8, "elementDmgMult": 0.6}, "prefixes": [], "suffixes": []}
        elif cn == "bloodwalker":
            starting_weapon = {"name": "Kan Kılıcı", "type": "weapon", "isMelee": True, "rarity": "Normal", "itemBase": {"physDmg": 14, "lifesteal": 0.15, "meleeRange": 50}, "prefixes": [], "suffixes": []}
        elif cn == "engineer":
            starting_weapon = {"name": "Taret Kiti", "type": "weapon", "isTurret": True, "rarity": "Magic", "itemBase": {"turretDmg": 1.0}, "prefixes": [], "suffixes": []}

        # Sınıf mantığını kur (Renk vb.)
        # --- POWER SCALING SYSTEMS ---
        self.is_essence_system_unlocked = False
        self.essence_stats = {
            "max_hp": 0,
            "phys_dmg": 0,
            "element_dmg": 0,
            "armor": 0,
            "speed": 0
        }
        self.purchased_auras = [] # Satın alınan aura ID'leri
        self.active_auras = []    # Kuşanılmış aura ID'leri
        self.aura_limit = 1       # Başlangıç aura sınırı
        
        self.reinit_specialization()

        # Silahı Otomatik Slotuna Yerleştir
        if starting_weapon:
            slot = starting_weapon["type"]
            self.inv_manager.equipped[slot] = starting_weapon
            
        # Statları Hesapla
        self.inv_manager.recalculate_stats()

    def reinit_specialization(self):
        """Sınıf ID'sine göre yetenek setini ve rengini günceller."""
        cn = self.class_id
        if cn == "warrior":
            self.specialization = Warrior()
            self.color = (46, 204, 113)
        elif cn == "beastmaster":
            self.specialization = Beastmaster()
            self.color = (155, 89, 182)
        elif cn == "sniper":
            self.specialization = Sniper()
            self.color = (230, 126, 34)
        elif cn == "ninja":
            self.specialization = Ninja()
            self.color = (44, 62, 80)
        elif cn == "alchemist":
            self.specialization = Alchemist()
            self.color = (241, 196, 15)
        elif cn == "sorcerer":
            self.specialization = Sorcerer()
            self.color = (148, 88, 230)
        elif cn == "bloodwalker":
            self.specialization = Bloodwalker()
            self.color = (192, 40, 40)
        elif cn == "engineer":
            self.specialization = Engineer()
            self.color = (52, 152, 219)
        else:
            self.specialization = Warrior() # Fallback
            self.color = (255, 255, 255)
        
    def update(self, dt, game):
        self.game = game # Reference for difficulty checks
        # --- STATUS EFFECTS ---
        self.effect_manager.update(dt, self, game)
        
        if self.i_frame_timer > 0:
            self.i_frame_timer -= dt
        if self.level_up_timer > 0:
            self.level_up_timer -= dt
            
        # --- DASH TIMERS ---
        if self.dash_timer > 0:
            self.dash_timer -= dt
        if self.dash_active_timer > 0:
            self.dash_active_timer -= dt
            # Görsel Efekt (İz Bırakma)
            if random.random() < 0.4:
                game.particles.append({
                    'x': self.x, 'y': self.y,
                    'vx': 0, 'vy': 0,
                    'timer': 0.2, 'color': (*self.color, 150),
                    'size': self.radius, 'is_ghost': True
                })

        # --- ARTIFACT & EFFECT TIMERS ---
        if self.artifact_cooldown > 0:
            self.artifact_cooldown -= dt
            
        if self.artifact_timer > 0:
            self.artifact_timer -= dt
            if self.artifact_timer <= 0:
                # Süreli efektleri kapat
                if self.is_invisible:
                    self.is_invisible = False
                    print("Görünmezlik Bitti")
                if self.is_invulnerable and not getattr(game, 'cheat_mode', False):
                    self.is_invulnerable = False
                # Kan Ritüeli bittiyse statları geri çek (Recalculate ile temizle)
                self.inv_manager.recalculate_stats()
                
        if self.fire_breath_timer > 0:
            self.fire_breath_timer -= dt
            if random.random() < 0.3:
                from entities.projectile import Projectile
                p_angle = self.facing_angle + random.uniform(-0.4, 0.4)
                vx = math.cos(p_angle) * 12
                vy = math.sin(p_angle) * 12
                game.projectiles.append(Projectile(game.entity_id_counter, self.x, self.y, vx, vy, 
                                                 self.stats.get("dmgMult", 1.0) * 40, p_type='fire', aoe=80, lifetime=25))
                game.entity_id_counter += 1

        # Kan Ritüeli HP Kaybı (Saniyede %2)
        if self.artifact_timer > 0 and self.inv_manager.equipped.get("artifact", {}).get("artifactId") == "blood_ritual":
            self.hp -= self.max_hp * 0.02 * dt
            
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_s]: dy += 1
        if keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_d]: dx += 1
        
        if (dx != 0 or dy != 0) and not self.is_stunned:
            mag = math.hypot(dx, dy)
            speed = self.stats["speed"] * self.speed_mod
            # DASH SPEED BOOST (%350)
            if self.dash_active_timer > 0:
                speed *= 3.5
            
            new_x = self.x + (dx / mag) * speed * dt * 60
            new_y = self.y + (dy / mag) * speed * dt * 60
            
            # Update Velocity
            self.vx = (new_x - self.x) / dt if dt > 0 else 0
            self.vy = (new_y - self.y) / dt if dt > 0 else 0
            
            self.x = new_x
            self.y = new_y
            is_moving = True
        else:
            is_moving = False
            self.vx = 0
            self.vy = 0
            
        # Screen bounds (5000x5000)
        self.x = max(50, min(4950, self.x))
        self.y = max(50, min(4950, self.y))
        
        # Facing Angle (Mouse)
        mx, my = pygame.mouse.get_pos()
        # World Mouse Pos hesaplama (Zoom fix)
        zoom = game.manager.current_scene.zoom_level
        world_mx = (mx / zoom) + game.manager.current_scene.camera_x
        world_my = (my / zoom) + game.manager.current_scene.camera_y
        self.facing_angle = math.atan2(world_my - self.y, world_mx - self.x)
            
        # Shooting / Special Attack
        mouse_buttons = pygame.mouse.get_pressed()
        if (mouse_buttons[0] or self.auto_attack) and not self.is_silenced: # Sol Tık veya Otomatik
            weapon = self.inv_manager.equipped.get("weapon")
            if weapon and weapon.get('isCommander'):
                # Komuta silahı saldırı yapmaz, sadece buff verir.
                pass
            else:
                current_time = pygame.time.get_ticks()
                if current_time - self.last_shot_time >= self.stats["attack_cooldown"]:
                    # --- CLASS-BASED ATTACK LOGIC ---
                    if hasattr(self.specialization, 'execute_attack'):
                        self.specialization.execute_attack(self, game)
                    else:
                        self.shoot(game)
                    
                    self.last_shot_time = current_time

        # --- Q TUŞU: Bloodwalker Kan Emme ---
        keys_event = getattr(game.manager.current_scene, '_pending_keys', [])
        # (Q basışı game_scene.py üzerinden tetiklenir; burası pasif update)

        # Update Specialization (Stamina vb.)
        if hasattr(self.specialization, 'update'):
            self.specialization.update(dt, self, game)
            
        # --- MİNYON KONTROLÜ ---
        self.check_minions(game)
            
        # Regen
        # Energy Shield Regen (5s timer)
        if self.es_timer > 0:
            self.es_timer -= dt
        else:
            if self.energy_shield < self.max_energy_shield:
                regen = self.stats.get("esRegen", 0) + 10.0 # Base regen
                if game.wave.get("current_diff") == "Impossible":
                    regen *= 0.5
                self.energy_shield = min(self.max_energy_shield, self.energy_shield + regen * dt)
                
        if self.hp < self.max_hp:
            regen = self.stats["regen"]
            if game.wave.get("current_diff") == "Impossible":
                regen *= 0.5 # Can yenileme etkisi yarıya iner
            self.hp = min(self.max_hp, self.hp + regen * dt)

        # --- CAN ÇALMA GÜNCELLEMELERİ ---
        if self.lifesteal_cooldown_timer > 0:
            self.lifesteal_cooldown_timer -= dt
                
        # Havuzdan can yenileme (Sadece cooldown yoksa ve can eksikse)
        if self.lifesteal_buffer > 0 and self.lifesteal_cooldown_timer <= 0:
            if self.hp < self.max_hp:
                # Saniyede 10 HP yenileme
                heal_rate = 10 
                heal_amount = heal_rate * dt
                
                can_heal = min(self.lifesteal_buffer, heal_amount)
                needed = self.max_hp - self.hp
                final_heal = min(can_heal, needed)
                
                self.hp += final_heal
                self.lifesteal_buffer -= final_heal
                
                if self.hp >= self.max_hp:
                    self.lifesteal_buffer = 0
            else:
                self.lifesteal_buffer = 0

        # --- PASİF KART EFEKTLERİ ---
        # Death Wish: Her saniye HP drain
        if self.passive_hp_drain > 0:
            self.hp = max(1, self.hp - self.passive_hp_drain * dt)

        # Adrenalin Kartı: 20s CD, 5s aktif
        if self.adrenaline_active:
            if self._adrenaline_cd > 0:
                self._adrenaline_cd -= dt
            else:
                self._adrenaline_timer -= dt
                if self._adrenaline_timer <= 0:
                    # Döngüyü yeniden başlat
                    self._adrenaline_cd = 20.0
                    self._adrenaline_timer = 5.0
                    game.add_event("damage_text", self.x, self.y-50, value="⚡ ADRENALİN!", color=(255, 200, 0), timer=1.0)
            if not hasattr(self, '_adrenaline_initialized'):
                self._adrenaline_cd = 20.0
                self._adrenaline_timer = 5.0
                self._adrenaline_initialized = True

        # Donmuş Zaman Kartı: Her periodic_freeze_cd saniyede tüm düşmanları dondur
        if self.periodic_freeze_cd > 0:
            self._freeze_timer -= dt
            if self._freeze_timer <= 0:
                self._freeze_timer = self.periodic_freeze_cd
                from logic.status_effects import apply_slow
                for e in game.enemies:
                    if not e.dead and not getattr(e, 'is_trap', False):
                        apply_slow(e.effect_manager, duration=3.0, mult=0.0)
                game.add_event("damage_text", self.x, self.y-60, value="❄️ DONDURULDU!", color=(100, 200, 255), timer=1.5)

        # Iron Will Kalkan CD
        if self.passive_shield_cd > 0 and self._shield_timer > 0:
            self._shield_timer -= dt

        # Pact Devil: İlk N wave ölümsüzlük
        if self.pact_devil_waves > 0:
            current_wave = game.wave.get("level", 1)
            if current_wave <= self.pact_devil_waves:
                self.is_invulnerable = True
            elif self.is_invulnerable and not getattr(self, '_pact_expired', False):
                self.is_invulnerable = False
                self._pact_expired = True
                sp = getattr(self, 'skills_permanent', {})
                sp['dmgMult'] = sp.get('dmgMult', 0) - 0.4
                self.skills_permanent = sp
                self.inv_manager.recalculate_stats()
                game.add_event("damage_text", self.x, self.y-60, value="😈 ŞEYTAN PAKTI BİTTİ!", color=(255, 50, 50), timer=2.0)

        # Berserker Rage: %40 HP altında dmgMult boost (geçici)
        if self.berserker_rage:
            ratio = self.hp / max(1, self.max_hp)
            self._berserker_active = ratio < 0.40

        # Low HP Rage (Bloodwalker Martyr evrimi)
        if getattr(self, 'evolution_passive', '') == 'low_hp_rage':
            ratio = self.hp / max(1, self.max_hp)
            mult_bonus = max(0, (1.0 - ratio) * 2.0)  # max +2.0 (3x toplam)
            self._low_hp_rage_mult = 1.0 + mult_bonus

    def gain_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_to_next_level:
            self.level_up()

    def level_up(self):
        self.level += 1
        if hasattr(self, 'game') and hasattr(self.game, 'track_quest'):
            self.game.track_quest("reach_level", self.level)
        self.xp -= self.xp_to_next_level
        # YENİ DENGELEME: Katlanarak değil doğrusal artış (Wave 10 -> L14, Wave 20 -> L30 hedefine uygun)
        self.xp_to_next_level = 100 + self.level * 250
        self.skill_points += 1
        self.hp = self.max_hp # Can tazele
        self.level_up_timer = 2.0 # 2 saniye ekranda yazı kalsın
        print(f"LEVEL UP! Yeni Seviye: {self.level}")
        
        # Sınıf Evrimi Tetikleyicisi
        if self.level == 20:
            self.ready_for_evolution = True

    def add_item(self, item):
        """Envantere eşya ekler. Orb ise istifler, değilse yer varsa ekler."""
        if item.get('type') == 'orb':
            # Önce envanterde aynı orbdan var mı bak
            for inv_item in self.inventory:
                if inv_item.get('type') == 'orb' and inv_item.get('orb_id') == item.get('orb_id'):
                    inv_item['stack'] = inv_item.get('stack', 1) + 1
                    return True
            # Yoksa yeni ekle
            item['stack'] = 1
            self.inventory.append(item)
            return True
        else:
            # Normal eşya: Slot kontrolü
            if len(self.inventory) < self.stats.get("maxInventorySlots", 24):
                self.inventory.append(item)
                return True
        return False

    def shoot(self, game, is_bomb=None):
        # Silah kontrolü
        weapon = self.inv_manager.equipped.get("weapon")
        if weapon and weapon.get('isCommander'):
            # Komuta silahı ateş etmez, sadece buff verir.
            return
        
        is_katana = False
        if weapon:
            is_katana = "katana" in weapon.get("name", "").lower()
            
        # --- FALLBACK MELEE CHECK (If not handled by specialization) ---
        if weapon and weapon.get("isMelee") and not is_katana:
            self.execute_fallback_melee(game, weapon)
            return

        if not weapon:
            # EĞER SİLAH YOKSA: Yumruk
            phys_flat = self.stats.get("physDmgFlat", 0)
            final_dmg = (20 + phys_flat) * self.stats.get("dmgMult", 1.0)
            game.add_event("damage_text", self.x, self.y - 20, value="YUMRUK!", color=(200, 200, 200), timer=0.3)
            # Görsel Efekt
            r_val = 80 + self.stats.get("meleeRange", 0)
            game.add_event("slash", self.x, self.y, angle=self.facing_angle, range=r_val, arc=1.0, timer=0.1)
            for e in game.iter_enemies_near(self.x, self.y, r_val):
                dx = e.x - self.x
                dy = e.y - self.y
                if not e.dead and dx * dx + dy * dy < r_val * r_val:
                    e.take_damage(final_dmg, game)
            return

        # --- RANGET/PROJECTILE ATTACK LOGIC ---
        # (Moved from execute_fallback_melee to solve class shooting issues)
        
        # Base Statlar (Phys, Poison vb.) zaten recalculate_stats ile toplandı
        base_phys = self.stats.get("physDmg", 20) 
        base_poison = self.stats.get("poisonDps", 0)
        
        # Çarpanlar
        mult = self.stats.get("dmgMult", 1.0)
        
        # Sabit Hasar Bonusunu (Flat) ekle
        phys_flat = self.stats.get("physDmgFlat", 0)
        
        # Poison Convert: Fiziksel -> Zehir
        if getattr(self, "poison_convert", False):
            base_poison += (base_phys + phys_flat)
            base_phys = 0
            phys_flat = 0

        # Eğer bomba/şişe fırlatılıyorsa PoisonDps baz alınır
        if is_bomb:
            final_dmg_base = ((base_poison if base_poison > 0 else 10) + phys_flat) * mult
            p_type = 'bomb'
        elif is_katana:
            final_dmg_base = (base_phys + phys_flat) * mult
            p_type = 'katana'
        else:
            final_dmg_base = (base_phys + phys_flat) * mult
            p_type = 'poison' if getattr(self, "poison_convert", False) else 'normal'
            if not getattr(self, "poison_convert", False):
                if self.stats.get("fireDmgMult", 0) > 0.2: p_type = 'fire'
                if self.stats.get("frostDmgMult", 0) > 0.2: p_type = 'frost'
        
        # Çoklu Atış (Multi-shot)
        count = int(self.stats.get("projectileCount", 1))
        
        if is_katana:
            range_val = 180 + self.stats.get("meleeRange", 0) * 1.5
            
            # --- KRİTİK VURUŞ ---
            force_crit = getattr(self, '_sorcerer_force_crit', False)
            is_crit = force_crit or (random.random() < self.stats.get("critChance", 0.05))
            crit_mult = 2.0 + self.stats.get("critDmg", 0)
            final_dmg = final_dmg_base * crit_mult if is_crit else final_dmg_base
            dot_mult = 1.0 + self.stats.get("dotDmgMult", 0.0)
            
            # Hedefleri bul (en yakın N hedef)
            candidates = game.iter_enemies_near(self.x, self.y, range_val)
            targets = sorted(
                (e for e in candidates if not e.dead),
                key=lambda e: (e.x - self.x) ** 2 + (e.y - self.y) ** 2,
            )[:count]
            
            for e in targets:
                e.take_damage(final_dmg, game, is_crit=is_crit, from_player=True)
                
                # Element Etkileri
                sorcerer_elem = getattr(self, '_sorcerer_override_element', None)
                if sorcerer_elem == 'fire':
                    fire_dmg = (self.stats.get("fireDamage", 0) + self.stats.get("fireDmgFlat", 0) + 15) * mult * dot_mult
                    e.apply_dot('fire', fire_dmg, 4.0)
                elif sorcerer_elem == 'frost':
                    frost_dmg = (self.stats.get("frostDamage", 0) + self.stats.get("frostDmgFlat", 0) + 15) * mult * dot_mult
                    e.apply_dot('frost', frost_dmg * 0.5, 4.0)
                elif sorcerer_elem == 'poison':
                    poison_dps = (base_poison + 15) * mult * dot_mult
                    e.apply_dot('poison', poison_dps, 5.0)
                else:
                    poison_dps = base_poison * mult * dot_mult
                    if poison_dps > 0: e.apply_dot('poison', poison_dps, 5.0)
                    fire_dmg = (self.stats.get("fireDamage", 0) + self.stats.get("fireDmgFlat", 0)) * mult * dot_mult
                    if fire_dmg > 0: e.apply_dot('fire', fire_dmg, 4.0)
                    frost_dmg = (self.stats.get("frostDamage", 0) + self.stats.get("frostDmgFlat", 0)) * mult * dot_mult
                    if frost_dmg > 0: e.apply_dot('frost', frost_dmg * 0.5, 4.0)
            
            # Görsel
            game.add_event("sweep", self.x, self.y, angle=self.facing_angle, range=range_val, arc=1.5, timer=0.15)
            # Katana hit particles
            for e in targets:
                for _ in range(5):
                    p_angle = random.uniform(0, math.pi * 2)
                    p_v = random.uniform(5, 15)
                    game.particles.append({
                        'x': e.x, 'y': e.y,
                        'vx': math.cos(p_angle) * p_v, 'vy': math.sin(p_angle) * p_v,
                        'timer': 0.2, 'color': (200, 0, 0), 'size': random.randint(2, 6)
                    })
            return # Katana atışı bitti, normal mermi koduna geçme
            
        proj_speed = 15
        proj_lifetime = 180 + int(self.stats.get("meleeRange", 0) * 1.5)
        
        # Mermi Stats
        bounce = int(self.stats.get("bounce", 0))
        pierce = int(self.stats.get("pierce", 0))
        count = int(self.stats.get("projectileCount", 1))
        # AOE Hesabı (Radius 50 = ~2x Karakter Boyutu)
        aoe = 50 * self.stats.get("aoe", 1.0)
        
        # Çoklu Atış (Multi-shot) - Açılı
        spread = 0.26 
        start_angle = self.facing_angle - (spread * (count - 1) / 2)
        
        from entities.projectile import Projectile
        for i in range(count):
            angle = start_angle + (i * spread)
            vx = math.cos(angle) * proj_speed
            vy = math.sin(angle) * proj_speed
            
            # Namlu çıkış noktası
            sx = self.x + math.cos(angle) * 20
            sy = self.y + math.sin(angle) * 20
            
            # --- KRİTİK VURUŞ ---
            force_crit = getattr(self, '_sorcerer_force_crit', False)
            is_crit = force_crit or (random.random() < self.stats.get("critChance", 0.05))
            crit_mult = 2.0 + self.stats.get("critDmg", 0)
            final_dmg = final_dmg_base * crit_mult if is_crit else final_dmg_base
            
            # Mermi Tipi Belirleme
            p_type_final = p_type
            sorcerer_elem = getattr(self, '_sorcerer_override_element', None)
            if sorcerer_elem:
                p_type_final = sorcerer_elem
            elif p_type_final not in ['bomb', 'katana']:
                if self.stats.get("fireDmgFlat", 0) > 0 or self.stats.get("fireDmgMult", 0) > 0:
                    p_type_final = 'fire'
                elif self.stats.get("frostDmgFlat", 0) > 0 or self.stats.get("frostDmgMult", 0) > 0:
                    p_type_final = 'frost'
            
            dot_mult = 1.0 + self.stats.get("dotDmgMult", 0.0)

            p = Projectile(game.entity_id_counter, sx, sy, vx, vy, 
                                             final_dmg, bounce, pierce, 
                                             p_type=p_type_final, aoe=aoe, is_crit=is_crit, lifetime=proj_lifetime)
            
            if is_katana:
                p.is_melee = True
                p.pierce = 99
            
            # Elementel Statları Aktar
            if sorcerer_elem == 'fire':
                p.fire_dmg  = (self.stats.get("fireDamage", 0) + self.stats.get("fireDmgFlat", 0) + 15) * mult * dot_mult
            elif sorcerer_elem == 'frost':
                p.frost_dmg  = (self.stats.get("frostDamage", 0) + self.stats.get("frostDmgFlat", 0) + 15) * mult * dot_mult
            elif sorcerer_elem == 'poison' or (is_bomb and base_poison > 0):
                p.poison_dps = (base_poison + 15) * mult * dot_mult
            else:
                p.poison_dps = base_poison * mult * dot_mult
                p.fire_dmg   = (self.stats.get("fireDamage", 0) + self.stats.get("fireDmgFlat", 0)) * mult * dot_mult
                p.frost_dmg  = (self.stats.get("frostDamage", 0) + self.stats.get("frostDmgFlat", 0)) * mult * dot_mult
            
            game.projectiles.append(p)
            game.entity_id_counter += 1
            
            # Namlu Ateşi
            for _ in range(3):
                p_angle = angle + random.uniform(-0.5, 0.5)
                p_v = random.uniform(5, 10)
                game.particles.append({
                    'x': sx, 'y': sy,
                    'vx': math.cos(p_angle) * p_v, 'vy': math.sin(p_angle) * p_v,
                    'timer': 0.1, 'color': (255, 255, 200), 'size': random.randint(2, 5)
                })

    def execute_fallback_melee(self, game, weapon):
        """Melee silahı varken specialization hatası/eksikliği durumunda temel savurma yapar."""
        base_phys = self.stats.get("physDmg", 20)
        phys_flat = self.stats.get("physDmgFlat", 0)
        base_poison = self.stats.get("poisonDps", 0)
        mult = self.stats.get("dmgMult", 1.0)
        
        if getattr(self, "poison_convert", False):
            base_poison += (base_phys + phys_flat)
            base_phys = 0
            phys_flat = 0
            
        final_dmg = (base_phys + phys_flat) * mult
        
        range_val = 100 + self.stats.get("meleeRange", 0)
        angle = self.facing_angle
        
        # Görsel
        game.add_event("sweep", self.x, self.y, angle=angle, range=range_val, arc=1.2, timer=0.15)
        
        for e in game.iter_enemies_near(self.x, self.y, range_val + 160):
            if not e.dead and not e.is_trap:
                dx = e.x - self.x
                dy = e.y - self.y
                hit_range = range_val + e.radius
                if dx * dx + dy * dy < hit_range * hit_range:
                    # Basit Açı Kontrolü
                    angle_to_e = math.atan2(e.y - self.y, e.x - self.x)
                    if abs(angle_to_e - angle) < 0.6: # Yaklaşık 70 derece
                        e.take_damage(final_dmg, game)
                        if base_poison > 0:
                            e.apply_dot('poison', base_poison * mult * (1.0 + self.stats.get("dotDmgMult", 0)), 5.0)
        
    def place_turret(self, game):
        limit = int(self.stats.get("turretLimit", 1))
        
        # Limit kontrolü (En eski tareti sil)
        if len(game.turrets) >= limit:
            game.turrets.pop(0)
            
        from entities.turret import Turret
        # SADECE SİLAH SLOTUNDAKİ TARET KİTİNİN STATLARINI AL (Global yetenekleri alma)
        local_stats = self.inv_manager.get_item_local_stats("weapon")
        
        new_turret = Turret(game.entity_id_counter, self.x, self.y, 
                           hp=self.stats.get("turretMaxHp", 150),
                           dmg_mult=self.stats.get("turretDmg", 1.0),
                           fire_rate=self.stats.get("turretRate", 1.0),
                           local_stats=local_stats,
                           owner=self)
        game.turrets.append(new_turret)
        game.entity_id_counter += 1
        print("Taret Kuruldu!")
            
    def check_minions(self, game):
        # Kuşanılan Pet'e bak
        pet = self.inv_manager.equipped.get("pet")
        if not pet:
            # Pet yoksa bendeki tüm minyonları sil
            game.minions = [m for m in game.minions if m.owner != self]
            return
            
        # Pet varsa tipini ve sayısını belirle
        m_type = "dragon" if "Ejder" in pet['name'] else "wolf"
        
        # SADECE PET SLOTUNDAKİ MODİFİERLARI AL
        local_stats = self.inv_manager.get_item_local_stats("pet")
        
        # Sayı: 1 (Temel) + Local ProjectileCount + Global 'minionCount' skilli (Özel minyon skilli hariç tutulmaz genellikle ama kullanıcı 'skill tree' dediği için onu da ayırabiliriz. Şimdilik sadece local alalım.)
        count = 1 + int(local_stats.get("projectileCount", 0))
        # Eğer Ordulu (minionCount) skilli varsa onu ekleyelim çünkü o ÖZEL minyon skilli
        count += int(self.stats.get("minionCount", 0))
        
        # Mevcut minyon sayım
        my_minions = [m for m in game.minions if m.owner == self]
        
        # TİP KONTROLÜ (Bug Fix): Eğer bendeki minyonların tipi mevcut pet tipinden farklıysa temizle
        if my_minions and my_minions[0].type != m_type:
             game.minions = [m for m in game.minions if m.owner != self]
             my_minions = []
        
        if len(my_minions) < count:
            from entities.minion import Minion
            for _ in range(count - len(my_minions)):
                new_m = Minion(game.entity_id_counter, self.x, self.y, m_type=m_type, owner=self, local_stats=local_stats)
                game.minions.append(new_m)
                game.entity_id_counter += 1
        elif len(my_minions) > count:
            # Fazla olanları sil
            for _ in range(len(my_minions) - count):
                m = my_minions.pop()
                game.minions.remove(m)

    # --- 18 SINIF EVRİMİ (9 Sınıf × 2 Yol) ---
    EVOLUTIONS = {
        # WARRIOR
        "warrior_gladiator": {
            "name": "🏟️ Gladyatör", "class_base": "warrior",
            "stats": {"dmgMult": 0.8, "armor": 10, "killSpeedBoost": 1.5},
            "max_hp_delta": -20,
            "passive": "gladiator_rage",
            "desc": "Her öldürmede 1s %30 hız. Hasar çok yüksek ama can az."
        },
        "warrior_paladin": {
            "name": "🛡️ Paladin", "class_base": "warrior",
            "stats": {"armor": 50, "regen": 3.0, "dmgMult": 0.2},
            "max_hp_delta": 80,
            "passive": "paladin_aura",
            "desc": "Dev zırh ve can yenileme. 5s'de bir ışık dalgası."
        },
        # BEASTMASTER
        "beastmaster_emperor": {
            "name": "👑 Pet İmparatoru", "class_base": "beastmaster",
            "stats": {"minionCount": 4, "minionDamage": 0.3, "minionMaxHp": 0.4, "minionRange": 0.2},
            "max_hp_delta": 0,
            "passive": "wind_minions",
            "desc": "+4 minyon sayısı. Tüm minyon hasarı rüzgar elementine döner."
        },
        "beastmaster_hunter": {
            "name": "🦅 Avcı", "class_base": "beastmaster",
            "stats": {"minionDamage": 1.5, "minionMaxHp": 1.0, "minionRange": 0.6},
            "max_hp_delta": 0,
            "passive": "alpha_pet",
            "desc": "Yalnızca 1 pet ama devasa güç. Pet hızı ve hasarı 2.5x."
        },
        # SNIPER
        "sniper_marksman": {
            "name": "💥 Tetikçi", "class_base": "sniper",
            "stats": {"critChance": 0.4, "critDmg": 2.0, "fireRate": 0.3},
            "max_hp_delta": -20,
            "passive": "crit_ignite",
            "desc": "Krit şans +%40, kritik vuruş → ateş patlaması."
        },
        "sniper_phantom": {
            "name": "🌑 Hayalet Nişancı", "class_base": "sniper",
            "stats": {"critDmg": 3.0, "dodgeChance": 0.3},
            "max_hp_delta": 0,
            "passive": "first_shot_invisible",
            "desc": "İlk atış görünmezden 2x hasar verir (8s CD)."
        },
        # ENGINEER
        "engineer_architect": {
            "name": "🏰 Kale Mimarı", "class_base": "engineer",
            "stats": {"turretCount": 3, "turretDamage": 0.3, "cooldownReduction": 0.2},
            "max_hp_delta": 0,
            "passive": "heal_turret",
            "desc": "+3 taret slotu. Taretler aralıklı iyileştirici ışın atar."
        },
        "engineer_electrician": {
            "name": "⚡ Elektrikçi", "class_base": "engineer",
            "stats": {"turretDamage": 0.8, "turretFireRate": 0.5, "cooldownReduction": 0.4},
            "max_hp_delta": 0,
            "passive": "chain_lightning",
            "desc": "Taret atışları 3 hedefe zincirleme çarpar."
        },
        # BOMBER
        "bomber_nuclear": {
            "name": "☢️ Nükleer Bombacı", "class_base": "bomber",
            "stats": {"dmgMult": 0.8, "aoe_bonus": 0.5},
            "max_hp_delta": -30,
            "passive": "chain_explosion",
            "desc": "Patlama zincirleme (%50 hasar komşulara). Dev AoE."
        },
        "bomber_chemist": {
            "name": "🌊 Kimyager", "class_base": "bomber",
            "stats": {"poisonDps": 40, "dmgMult": 0.4, "aoe_bonus": 0.3},
            "max_hp_delta": 10,
            "passive": "toxic_cloud",
            "desc": "Patlama sonrası 5s zehir bulutu bırakır."
        },
        # NINJA
        "ninja_shadow": {
            "name": "🗡️ Ölüm Gölgesi", "class_base": "ninja",
            "stats": {"critDmg": 3.5, "dodgeChance": 0.35},
            "max_hp_delta": 0,
            "passive": "kill_invisible",
            "desc": "Backstab x3 hasar. Her öldürmede 3s görünmezlik."
        },
        "ninja_storm": {
            "name": "🌀 Fırtına Bıçağı", "class_base": "ninja",
            "stats": {"critDmg": 1.0, "dodgeChance": 0.2, "speed": 2},
            "max_hp_delta": 0,
            "passive": "kill_speed_stack",
            "desc": "Her saldırıda 4 vuruş. Öldürdükçe ateş hızı artar (max %150)."
        },
        # ALCHEMIST
        "alchemist_grandmaster": {
            "name": "🧪 Büyük Usta", "class_base": "alchemist",
            "stats": {"poisonDps": 20, "toxicAura": 30, "cooldownReduction": 0.3},
            "max_hp_delta": 0,
            "passive": "double_potion",
            "desc": "İksir etkileri 2x. İksirler müttefikinize de etki eder."
        },
        "alchemist_poison_god": {
            "name": "🍄 Zehir Tanrısı", "class_base": "alchemist",
            "stats": {"poisonDps": 80, "toxicAura": 60, "dotDmgMult": 0.5},
            "max_hp_delta": 0,
            "passive": "death_cloud",
            "desc": "Öldürülen düşmanlar 3s zehirli alan bırakır."
        },
        # SORCERER
        "sorcerer_firelord": {
            "name": "🌋 Ateş Başbüyücüsü", "class_base": "sorcerer",
            "stats": {"fireDamage": 60, "fireDmgFlat": 30, "elementDmgMult": 1.0},
            "max_hp_delta": -20,
            "passive": "fire_aoe",
            "desc": "Ateş büyüleri patlama AoE'ye döner. +60 ateş hasarı."
        },
        "sorcerer_icemage": {
            "name": "❄️ Buz Büyücüsü", "class_base": "sorcerer",
            "stats": {"frostDamage": 40, "frostDmgFlat": 20, "elementDmgMult": 0.6},
            "max_hp_delta": 0,
            "passive": "freeze_on_hit",
            "desc": "Buz büyüleri 1s dondurur. +40 buz hasarı."
        },
        # BLOODWALKER
        "bloodwalker_noble": {
            "name": "🧛 Asil Vampir", "class_base": "bloodwalker",
            "stats": {"lifesteal": 0.4, "dmgMult": 0.3, "hpRegen": 2.0},
            "max_hp_delta": 50,
            "passive": "full_hp_bonus",
            "desc": "Can çalma +%40. Max HP'deyken hasar +%30."
        },
        "bloodwalker_martyr": {
            "name": "💔 Şehit", "class_base": "bloodwalker",
            "stats": {"lifesteal": 0.2, "dmgMult": 1.0},
            "max_hp_delta": -50,
            "passive": "low_hp_rage",
            "desc": "Az HP iken hasar katlanır (max 3x). Yüksek riskli."
        },
    }

    def apply_evolution(self, evo_id):
        evo = self.EVOLUTIONS.get(evo_id)
        if not evo:
            return

        self.evolution = evo_id
        self.class_name = evo["name"]
        self.evolution_passive = evo.get("passive", "")

        if not hasattr(self, 'skills_permanent'):
            self.skills_permanent = {}

        # İstatistik bonuslarını uygula
        for stat, val in evo["stats"].items():
            self.skills_permanent[stat] = self.skills_permanent.get(stat, 0) + val

        # Max HP delta'sı doğrudan uygulanır
        delta = evo.get("max_hp_delta", 0)
        if delta != 0:
            self.skills_permanent["max_hp"] = self.skills_permanent.get("max_hp", 0) + delta
            self.hp = min(self.hp, self.max_hp + delta)

        # Hunter path: 1 pet modu
        if evo.get("passive") == "alpha_pet":
            self.alpha_mode = True

        # Shadow Sniper: ilk atış görünmezlik flag
        if evo.get("passive") == "first_shot_invisible":
            self._phantom_first_shot = True

        self.inv_manager.recalculate_stats()
        print(f"EVRİM GEÇİRİLDİ: {self.class_name} | Pasif: {self.evolution_passive}")

    def dash(self):
        if self.dash_timer <= 0:
            self.dash_active_timer = self.dash_duration
            self.dash_timer = self.dash_cooldown
            if getattr(self, "class_id", "") == "ninja":
                self.next_attack_is_backstab = True
            return True
        return False

    def use_artifact(self, game):
        # Kuşanılan artifact'i bul
        art = self.inv_manager.equipped.get("artifact")
        if not art or self.artifact_cooldown > 0 or self.is_silenced:
            return
            
        a_id = art.get("artifactId")
        if not a_id: return
        
        # Cooldown başlat (Capped at 80% reduction)
        base_cd = art.get("cooldown", 30)
        reduction = self.stats.get("cooldownReduction", 0)
        self.artifact_cooldown = base_cd * (1 - min(0.8, reduction))
        
        if a_id == "time_sand":
            # Zaman Kumu: Düşmanları dondur/yavaşlat
            from logic.status_effects import apply_slow
            for e in game.enemies:
                if not e.dead and not e.is_trap:
                    apply_slow(e.effect_manager, duration=6.0, mult=0.15)
            game.add_event("damage_text", self.x, self.y - 40, value="ZAMAN DURDU!", color=(52, 152, 219))
            
        elif a_id == "midas_hand":
            # Midasın Eli: Yakındaki düşmanlardan altın çal ve onları sars
            for e in game.enemies:
                if not e.dead and not e.is_trap:
                    dist = math.hypot(e.x - self.x, e.y - self.y)
                    if dist < 500:
                        gold = 25 + int(game.wave["level"] * 5)
                        self.gold += gold
                        e.take_damage(200, game)
                        game.add_event("damage_text", e.x, e.y, value=f"+{gold} G", color=(241, 196, 15))
            game.trigger_shake(20)
            
        elif a_id == "phoenix_wing":
            self.hp = self.max_hp
            game.trigger_shake(30)
            game.add_event("explosion", self.x, self.y, radius=300, color=(231, 76, 60), timer=0.4)
            # Çevredeki düşmanları it
            for e in game.enemies:
                d = math.hypot(e.x - self.x, e.y - self.y)
                if d < 300:
                    angle = math.atan2(e.y - self.y, e.x - self.x)
                    e.x += math.cos(angle) * 120
                    e.y += math.sin(angle) * 120
                    e.take_damage(150, game)
                    
        elif a_id == "titan_shield":
            self.artifact_timer = 5.0
            self.is_invulnerable = True
            game.add_event("damage_text", self.x, self.y - 60, value="ÖLÜMSÜZ!", color=(255, 255, 255))
            
        elif a_id == "storm_eye":
            # Fırtına Gözü: 6 saniye sürecek
            self.artifact_timer = 6.0
            game.add_event("damage_text", self.x, self.y - 40, value="FIRTINA!", color=(236, 240, 241))
            
        elif a_id == "shadow_cloak":
            self.artifact_timer = 8.0
            self.is_invisible = True
            game.add_event("damage_text", self.x, self.y - 60, value="GÖRÜNMEZ!", color=(149, 165, 166))
            
        elif a_id == "blood_ritual":
            self.artifact_timer = 10.0
            # Geçici stat artışı (Direkt override edelim, süre sonunda recalcStats düzeltecek)
            self.stats["dmgMult"] *= 2.5
            self.stats["speed"] *= 1.6
            game.add_event("damage_text", self.x, self.y - 40, value="KAN RİTÜELİ!", color=(192, 57, 43))
            
        elif a_id == "dragon_breath":
            self.fire_breath_timer = 6.0
            game.add_event("damage_text", self.x, self.y - 40, value="EJDER NEFESİ!", color=(230, 126, 34))
            
        elif a_id == "void_staff":
            # Kara Delik fırlat
            from entities.projectile import Projectile
            vx = math.cos(self.facing_angle) * 8
            vy = math.sin(self.facing_angle) * 8
            game.projectiles.append(Projectile(game.entity_id_counter, self.x, self.y, vx, vy, 
                                             50, p_type='black_hole', aoe=280, lifetime=300))
            game.entity_id_counter += 1

    def take_damage(self, amount, force=False, is_self_damage=False):
        """Hasar alma mantığı. force=True ise i-frame'i yok sayıp direkt vurur (Sürekli temas hasarı)."""
        if self.is_invulnerable: return
        if self.dash_active_timer > 0: return # Dash sırasında dokunulmazlık
        if not force and self.i_frame_timer > 0: return
        
        # --- DODGE (Kaçınma) ---
        if not is_self_damage and random.random() < self.stats.get("dodgeChance", 0):
            # Sürekli hasarda (Tick damage) dodge şansını biraz azaltabiliriz veya aynı bırakabiliriz
            return
            
        # --- ARMOR (Zırh) ---
        if not is_self_damage:
            armor = self.stats.get("armor", 0)
            # Impossible zorlukta zırh etkisi yarıya iner
            current_diff = "Normal"
            if hasattr(self, 'game') and self.game:
                current_diff = self.game.wave.get("current_diff", "Normal")
                
            if current_diff == "Impossible":
                armor *= 0.5
                
            final_dmg = amount * (100.0 / (100.0 + armor)) * getattr(self, "damage_taken_mult", 1.0)
        else:
            final_dmg = amount
        
        if not is_self_damage:
            self.es_timer = max(1.0, 5.0 - self.stats.get("esDelayReduction", 0))
            
        if final_dmg > 0:
            if self.energy_shield > 0:
                if self.energy_shield >= final_dmg:
                    self.energy_shield -= final_dmg
                    final_dmg = 0
                else:
                    final_dmg -= self.energy_shield
                    self.energy_shield = 0
            
            if final_dmg > 0:
                self.hp -= final_dmg

        if hasattr(self, 'game') and hasattr(self.game, 'stats'):
            self.game.stats['total_damage_taken'] += final_dmg
        
        # Hasar alınınca can çalma kilitlenmesi kaldırıldı (Kullanıcı İsteği)
        # if not is_self_damage:
        #     self.lifesteal_cooldown_timer = 3.0
        
        # Sadece normal (büyük) vuruşlarda i-frame ver
        if not force:
            self.i_frame_timer = 0.5 # 0.5 saniye dokunulmazlık
        
    def reset_skills(self):
        """Tüm yetenekleri sıfırlar ve harcanan SP'leri iade eder."""
        wave_level = 1
        if hasattr(self, 'game') and self.game:
            wave_level = self.game.wave.get("level", 1)
        cost = 2000 + max(0, (wave_level - 1) * 400)
        
        if self.gold < cost:
            return False
            
        self.gold -= cost
        total_refund = 0
        for sk in self.skills:
            total_refund += sk['lvl']
            sk['lvl'] = 0
            
        self.skill_points += total_refund
        self.inv_manager.recalculate_stats()
        # Canı yeni max_hp'ye göre sınırla
        self.hp = min(self.hp, self.max_hp)
        print(f"Yetenekler Sıfırlandı! {total_refund} SP iade edildi. {cost} Gold harcandı.")
        return True


    def draw(self, screen, camera_x, camera_y):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        # Yanıp sönme efekti (I-Frame iken)
        alpha = 255
        if self.i_frame_timer > 0:
            alpha = 128 if int(time.time() * 10) % 2 == 0 else 255
            
        # Oyuncu Çemberi
        pygame.draw.circle(screen, (52, 152, 219), (int(draw_x), int(draw_y)), self.radius)
        
        # --- ARTIFACT AURA (Görsel Efekt) ---
        if getattr(self, 'artifact_timer', 0) > 0:
            art = self.inv_manager.equipped.get("artifact", {})
            a_id = art.get("artifactId")
            aura_color = None
            if a_id == "shadow_cloak": aura_color = (149, 165, 166, 120)  # Gri
            elif a_id == "blood_ritual": aura_color = (192, 57, 43, 120)  # Kırmızı
            elif a_id == "titan_shield": aura_color = (241, 196, 15, 120) # Altın
            elif a_id == "storm_eye": aura_color = (52, 152, 219, 120)    # Mavi
            elif self.fire_breath_timer > 0: aura_color = (230, 126, 34, 120) # Turuncu

            if aura_color:
                aura_surf = pygame.Surface((self.radius*4, self.radius*4), pygame.SRCALPHA)
                pulse = math.sin(time.time() * 8) * 5
                pygame.draw.circle(aura_surf, aura_color, (self.radius*2, self.radius*2), self.radius + 10 + pulse)
                pygame.draw.circle(aura_surf, (255,255,255,100), (self.radius*2, self.radius*2), self.radius + 10 + pulse, 2)
                screen.blit(aura_surf, (int(draw_x) - self.radius*2, int(draw_y) - self.radius*2))

        # Uzmanlık/Silah Görseli
        if self.specialization:
            self.specialization.draw_visuals(screen, camera_x, camera_y)
        
        # Gun (Namlu) - Sadece Uzak Dövüşçüler ve Mühendis için (Eğer silahı varsa)
        if self.class_name not in ["warrior", "beastmaster"]:
            gun_len = 20
            gun_w = 8
            gun_surf = pygame.Surface((gun_len, gun_w), pygame.SRCALPHA)
            pygame.draw.rect(gun_surf, (189, 195, 199), (0, 0, gun_len, gun_w), border_radius=2)
            
            rotated_gun = pygame.transform.rotate(gun_surf, -math.degrees(self.facing_angle))
            gun_rect = rotated_gun.get_rect(center=(draw_x + math.cos(self.facing_angle) * 25, draw_y + math.sin(self.facing_angle) * 25))
            screen.blit(rotated_gun, gun_rect)
        
        # Health Bar (Overhead)
        hp_ratio = self.hp / max(1, self.max_hp)
        
        y_offset = -40
        if self.max_energy_shield > 0:
            y_offset = -45
            
        pygame.draw.rect(screen, (0, 0, 0), (draw_x - 20, draw_y + y_offset, 40, 6))
        pygame.draw.rect(screen, (46, 204, 113), (draw_x - 20, draw_y + y_offset, 40 * hp_ratio, 6))
        
        if self.max_energy_shield > 0:
            es_ratio = self.energy_shield / max(1, self.max_energy_shield)
            pygame.draw.rect(screen, (0, 0, 0), (draw_x - 20, draw_y - 38, 40, 4))
            pygame.draw.rect(screen, (52, 152, 219), (draw_x - 20, draw_y - 38, 40 * es_ratio, 4))
        
        # Sayısal Can Gösterimi
        hp_font = pygame.font.SysFont("Arial", 11, bold=True)
        hp_text = f"{int(self.hp)}/{int(self.max_hp)}"
        hp_surf = hp_font.render(hp_text, True, (255, 255, 255))
        screen.blit(hp_surf, (draw_x - hp_surf.get_width() // 2, draw_y + y_offset - 15))
        
        # Status Effects
        self.effect_manager.draw_icons(screen, draw_x, draw_y, self.radius)

    def toggle_aura(self, aura_id):
        """Aura limitine göre aurayı aktif eder veya kapatır."""
        if aura_id in self.active_auras:
            self.active_auras.remove(aura_id)
        else:
            if len(self.active_auras) < self.aura_limit:
                self.active_auras.append(aura_id)
        
        # Statları güncelle
        self.inv_manager.recalculate_stats()

    def consume_essence(self, essence_type, value):
        """Öz tüketerek kalıcı stat artışı sağlar."""
        if essence_type == "xp":
            self.gain_xp(value)
            return True

        if essence_type in self.essence_stats:
            self.essence_stats[essence_type] += value
            # HP ise anlık canı da güncelle
            if essence_type == "max_hp":
                self.hp += value
            
            self.inv_manager.recalculate_stats()
            return True
        return False

    def consume_all_essences(self):
        """Envanterdeki tüm özleri (essence) tek seferde tüketir."""
        essences = [it for it in self.inventory if it.get('type') == 'essence']
        if not essences:
            return 0
        
        count = len(essences)
        for it in essences:
            self.consume_essence(it['essence_type'], it['val'])
            self.inventory.remove(it)
            
        return count
