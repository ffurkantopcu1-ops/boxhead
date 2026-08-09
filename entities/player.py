import pygame
import math
import time
import random

import vfx

# Simyacı şişesi imlecin bulunduğu yere düşer. BOMB_THROW_RANGE bunun ÜST
# SINIRI: imleç daha uzaktaysa şişe menzilin sonuna kadar gider. Alt sınır,
# menzilin sıfıra düşüp şişenin normal mermiye dönmesini engeller.
BOMB_THROW_RANGE = 460
BOMB_MIN_THROW_RANGE = 60

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
from logic.skill_tree import SkillTree
from logic.ascendancy import Ascendancy
import audio

class Player:
    def __init__(self, id, x, y, class_id="warrior"):
        self.id = id
        self.x = x
        self.y = y
        self.radius = 24
        self.facing_angle = 0
        # Dünya koordinatında nişan noktası; update() içinde fareden güncellenir.
        # None ise (test/başlık öncesi) şişe maksimum menzile atılır.
        self.aim_x = None
        self.aim_y = None
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

        # --- META PROGRESSION UPGRADES (CrystalShop) ---
        # DİKKAT: Bu blok yukarıdaki varsayılan atamalardan SONRA çalışmalı;
        # eskiden önce çalıştığı için revive_count/shop_discount/skills_permanent
        # gibi tüm kristal yükseltmeleri hemen ardından sıfırlanıyordu.
        try:
            meta = SaveManager.load_meta()
            crystal_shop = CrystalShop()
            crystal_shop.apply_to_player(meta, self)
        except Exception as e:
            print("Meta load error:", e)


        # --- ARTIFACT & ACTIVE EFFECTS ---
        self.artifact_cooldown = 0
        # Taret yeteneği (Mühendis, R tuşu): şarj sayısı ve dolum sayacı
        self.turret_charges = self.TURRET_BASE_CHARGES
        self.turret_recharge = 0.0
        self.artifact_timer = 0 # Aktif efekt süresi (Görünmezlik, Kalkan vb.)
        # Süreli stat çarpanları (örn. Kan Ritüeli). recalculate_stats bunları
        # kalıcı statların ÜSTÜNE uygular; böylece araya giren bir yeniden
        # hesaplama buff'ı silmez (F7).
        self.temp_buffs = {}
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
            { 'name': '🛡 Kalkan (+30 Max ES)', 'stat': 'maxEnergyShield', 'val': 30, 'lvl': 0, 'max': 10, 'group': 'HAYATTA KALMA' },
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
            { 'name': '🧠 Alim (+10% XP Kazanımı)', 'stat': 'xpGain', 'val': 0.10, 'lvl': 0, 'max': 5, 'group': 'YARDIMCI' },
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
            # Düz can veriyor; çarpan statını beslerse minyon canı 85.000'e çıkıyordu (F3)
            { 'name': '💖 Fedai (+80 Minyon Canı)', 'stat': 'minionMaxHpFlat', 'val': 80, 'lvl': 0, 'max': 10, 'group': 'MİNYON' },
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
        # Karakterin KENDİ (kalıcı) sınıfı. class_id yalnızca FARKLI savaş
        # ailesinden bir silah takılınca (ör. ninja -> arbalet) geçici değişir;
        # aynı aileden silah (ninja -> kan/vampir kılıcı) sınıfı değiştirmez.
        # Bkz. inventory_manager.recalculate_stats + WEAPON_FAMILIES.
        self.base_class_id = class_id
        # --- YETENEK AĞACI (koşu-kapsamlı, yollu) ---
        # Sınıfın başlangıç düğümü bedava tahsis edilir; recalculate_stats bunu
        # kart havuzuyla aynı şekilde toplar. Eski düz "skills" ızgarası artık
        # yükseltilmez (bkz. SKILL_TREE.md); p.skills lvl 0'da kalır.
        self.allocated_nodes = set(SkillTree.start_nodes_for(class_id))
        # --- ASCENDANCY (alt-sınıf) — seviye 20 evrimiyle açılır ---
        # Ayrı para birimi: seviye 20'den itibaren seviye başına +1 puan.
        self.ascendancy_points = 0
        self.ascendancy_nodes = set()
        self.class_name = self.class_id
        self.evolution = ""
        self.evolution_passive = ""
        # --- EVRİM PASİFİ DURUMLARI ---
        # apply_evolution() yalnızca stat/max_hp uyguluyordu; pasiflerin kendi
        # sayaçları burada tanımlanır ki update()/shoot() getattr'a düşmesin.
        self._gladiator_timer = 0.0     # gladiator_rage: öldürme sonrası hız penceresi
        self._kill_invis_timer = 0.0    # kill_invisible: öldürme sonrası görünmezlik
        self._ks_stacks = 0             # kill_speed_stack: öldürme yığını
        self._ks_timer = 0.0            # yığın sıfırlama sayacı
        self._paladin_tick = 1.0        # paladin_aura tick sayacı
        self._heal_turret_tick = 1.0    # heal_turret tick sayacı
        self._phantom_first_shot = False
        # Negatif baslangic: oyunun ilk saniyelerinde de "2sn beklendi" sayilsin
        # (pygame.time.get_ticks() acilista kucuk bir deger dondurur)
        self._last_phantom_shot = -10000
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
        
        # weaponClass: silah takıldığında sınıf mantığını belirler
        # (inventory_manager.recalculate_stats). Eksik olursa başka bir sınıf
        # silahından geri dönüldüğünde eski sınıfın saldırısı takılı kalıyor.
        if cn == "warrior":
            starting_weapon = {"name": "Eski Kılıç", "type": "weapon", "isMelee": True, "weaponClass": "warrior", "rarity": "Normal", "itemBase": {"physDmg": 12, "meleeRange": 50}, "prefixes": [], "suffixes": []}
        elif cn == "beastmaster":
            # minionMaxHp ÇARPAN'dır (pet itemleri 0.60-12.0 aralığında);
            # 50 değeri başlangıç kurduna 5100 can veriyordu (F3)
            starting_weapon = {"name": "Küçük Kurt", "type": "pet", "rarity": "Normal", "itemBase": {"minionDamage": 0, "minionMaxHp": 0.5}, "prefixes": [], "suffixes": []}
        elif cn == "sniper":
            starting_weapon = {"name": "Basit Arbalet", "type": "weapon", "isRanged": True, "weaponClass": "sniper", "rarity": "Normal", "itemBase": {"physDmg": 18}, "prefixes": [], "suffixes": []}
        elif cn == "ninja":
            starting_weapon = {"name": "Paslı Katana", "type": "weapon", "isMelee": True, "weaponClass": "ninja", "rarity": "Magic", "itemBase": {"physDmg": 15, "attackCooldown": 450, "meleeRange": 20}, "prefixes": [], "suffixes": []}
        elif cn == "alchemist":
            starting_weapon = {"name": "Zehir Şişesi", "type": "weapon", "isBomb": True, "weaponClass": "alchemist", "rarity": "Normal", "itemBase": {"poisonDps": 4}, "prefixes": [], "suffixes": []}
        elif cn == "bomber":
            # Bomba hasarı poisonDps üzerinden hesaplanır (shoot(): is_bomb dalı);
            # physDmg bomba yolunda okunmadığı için taban stat olarak verilmez.
            # item_system'deki "El Bombası Çantası (T4)" tabanıyla birebir aynı.
            starting_weapon = {"name": "El Bombası Çantası", "type": "weapon", "isBomb": True, "weaponClass": "bomber", "rarity": "Normal", "itemBase": {"poisonDps": 8}, "prefixes": [], "suffixes": []}
        elif cn == "sorcerer":
            # elementDmgMult 0.2: T4 baz (item_system.py) ile hizalı; 0.6 başlangıçta T2 gücü veriyordu (F6).
            # physDmg 8->12: erken oyunda büyücü çok zayıftı — elementDmgMult
            # (sınıf kimliği) düz element hasarı olmadan uykuda kaldığı için
            # başlangıçta yalnızca 8 fiziksel vuruyordu. Taban 12'ye çekildi.
            starting_weapon = {"name": "Sihir Asası", "type": "weapon", "isRanged": True, "weaponClass": "sorcerer", "rarity": "Magic", "itemBase": {"physDmg": 12, "elementDmgMult": 0.2}, "prefixes": [], "suffixes": []}
        elif cn == "bloodwalker":
            starting_weapon = {"name": "Kan Kılıcı", "type": "weapon", "isMelee": True, "weaponClass": "bloodwalker", "rarity": "Normal", "itemBase": {"physDmg": 14, "lifesteal": 0.15, "meleeRange": 50}, "prefixes": [], "suffixes": []}
        elif cn == "engineer":
            # Taret artık R yeteneği; taret kiti ise "vurmayan ekipman".
            # Mühendis onunla başlayınca HİÇ doğrudan hasar veremiyordu.
            # Başlangıç silahı sınıfın gerçek hasar kolu olan alev silahı.
            starting_weapon = {"name": "Sızdıran Alev Tabancası", "type": "weapon", "isFlamethrower": True, "weaponClass": "engineer", "rarity": "Normal", "itemBase": {"fireDamage": 4, "attackCooldown": 115}, "prefixes": [], "suffixes": []}

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

    # Gösterim adları: class_id ham kimliktir, arayüzde "bloodwalker" yazıyordu
    CLASS_NAMES = {
        "warrior": "Savaşçı",
        "beastmaster": "Ruh Terbiyecisi",
        "sniper": "Keskin Nişancı",
        "engineer": "Mühendis",
        "ninja": "Gölge Ninja",
        "alchemist": "Simyacı",
        "sorcerer": "Kadim Büyücü",
        "bloodwalker": "Vampir",
        "bomber": "Bombacı",
    }

    def sync_class_name(self):
        """Görünen sınıf adını mevcut sınıfla eşitler.

        Evrim geçirilmişse ve evrim şu anki sınıfa aitse evrim adı korunur;
        aksi halde sınıfın gösterim adı yazılır. (class_name yalnızca gösterim
        içindir; kalıcı kimlik class_id'dir.)
        """
        evo = self.EVOLUTIONS.get(getattr(self, "evolution", "") or "")
        if evo and evo.get("class_base") == self.class_id:
            self.class_name = evo["name"]
        else:
            self.class_name = self.CLASS_NAMES.get(self.class_id, self.class_id)

    def reinit_specialization(self):
        """Sınıf ID'sine göre yetenek setini, rengini ve görünen adını günceller."""
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
        elif cn == "bomber":
            self.specialization = Bomber()
            self.color = (211, 84, 0)
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

        self.sync_class_name()

    def update(self, dt, game):
        self.game = game # Reference for difficulty checks
        # --- STATUS EFFECTS ---
        self.effect_manager.update(dt, self, game)
        
        # --- SILENCE TIMER ---
        if getattr(self, "silence_timer", 0) > 0:
            self.silence_timer -= dt
            if self.silence_timer <= 0:
                self.is_silenced = False
        
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
        if self.is_engineer():
            self.update_turret_charges(dt)
            
        if self.artifact_timer > 0:
            self.artifact_timer -= dt
            if self.artifact_timer <= 0:
                # Süreli efektleri kapat.
                # Ölüm Gölgesi (kill_invisible) evrimi de görünmezlik veriyor;
                # onun kendi sayacı doluyken artifact bitişi görünmezliği kesmez.
                if self.is_invisible and getattr(self, '_kill_invis_timer', 0) <= 0:
                    self.is_invisible = False
                    print("Görünmezlik Bitti")
                if self.is_invulnerable and not getattr(game, 'cheat_mode', False):
                    self.is_invulnerable = False
                # Süreli buff'lar bitti: havuzu boşalt ve statları yeniden kur (F7)
                if getattr(self, 'temp_buffs', None):
                    self.temp_buffs.clear()
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
        # Slot anahtarı var ama değeri None olabildiği için .get default'u devreye
        # girmiyor; "or {}" gerekli (C7)
        if self.artifact_timer > 0 and (self.inv_manager.equipped.get("artifact") or {}).get("artifactId") == "blood_ritual":
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
            # Adrenalin kartı: 5sn boyunca +%30 hız (P3)
            if getattr(self, '_adrenaline_timer', 0) > 0:
                speed *= 1.3
            # Gladyatör (+%30) ve Fırtına Bıçağı (yığın başına +%4) hız pasifleri
            if getattr(self, '_gladiator_timer', 0) > 0:
                speed *= 1.3
            speed *= 1.0 + 0.04 * getattr(self, '_ks_stacks', 0)
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
        # Nişan noktası: fırlatılan şişe tam buraya düşsün diye saklanıyor
        # (shoot() sırasında fare tekrar okunmaz, atış anındaki hedef kullanılır)
        self.aim_x, self.aim_y = world_mx, world_my
            
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
        
        # --- GÖLGE KLONU SPAM ---
        if getattr(self, "has_shadow_clone", False):
            if not hasattr(self, "shadow_clone_timer"):
                self.shadow_clone_timer = 15.0 # İlk doğuş gecikmeli
            
            self.shadow_clone_timer -= dt
            if self.shadow_clone_timer <= 0:
                self.shadow_clone_timer = 15.0
                shadow_clones = [m for m in game.minions if m.owner == self and m.type == "shadow_clone"]
                if len(shadow_clones) < 2:
                    from entities.minion import Minion
                    new_m = Minion(game.entity_id_counter, self.x, self.y, m_type="shadow_clone", owner=self)
                    game.minions.append(new_m)
                    game.entity_id_counter += 1
            
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
            # hpRegen (eşya/aura/kart/evrim) + combatRegen (skill/SET_PALADIN/affix).
            # combatRegen yalnızca HUD'da gösteriliyordu, regene girmiyordu (P3)
            regen = self.stats["regen"] + self.stats.get("hpRegen", 0) + self.stats.get("combatRegen", 0)
            if game.wave.get("current_diff") == "Impossible":
                regen *= 0.5 # Can yenileme etkisi yarıya iner
            # "✨ LÜTUF" dalga olayı: XP yarıya iner, can yenilenmesi 2x.
            # İkinci yarısının hiç anahtarı yoktu, sadece açıklamada yazıyordu.
            _ev = game.wave.get("event")
            if _ev:
                regen *= _ev.get("regen_mult", 1.0)
            self.heal(regen * dt)

        # --- CAN ÇALMA GÜNCELLEMELERİ ---
        if self.lifesteal_cooldown_timer > 0:
            self.lifesteal_cooldown_timer -= dt
                
        # Havuzdan can yenileme (Sadece cooldown yoksa)
        if self.lifesteal_buffer > 0 and self.lifesteal_cooldown_timer <= 0:
            # Saniyede 10 HP yenileme (Bloodwalker sınıf kimliği: 3x hızlı boşaltma)
            heal_rate = 30 if getattr(self, "class_id", "") == "bloodwalker" else 10
            heal_amount = heal_rate * dt
            
            can_heal = min(self.lifesteal_buffer, heal_amount)
            actual_healed, overheal = self.heal(can_heal)
            
            self.lifesteal_buffer -= can_heal
            if self.hp >= self.max_hp:
                self.lifesteal_buffer = 0
        # NOT: else dalında havuzu sıfırlamak yok — take_damage 0.2sn cooldown
        # kurduğu için havuz bir sonraki karede hep siliniyordu (H1)

        # --- PASİF KART EFEKTLERİ ---
        # Death Wish: Her saniye HP drain
        if self.passive_hp_drain > 0:
            self.hp = max(1, self.hp - self.passive_hp_drain * dt)

        # Adrenalin Kartı: 20s CD, 5s aktif
        if self.adrenaline_active:
            # Init timer mantığının ALTINDAYDI: ilk kare boşa tetikleniyordu (P4)
            if not hasattr(self, '_adrenaline_initialized'):
                self._adrenaline_cd = 20.0
                self._adrenaline_timer = 0.0
                self._adrenaline_initialized = True
            if self._adrenaline_cd > 0:
                self._adrenaline_cd -= dt
                if self._adrenaline_cd <= 0:
                    # Buff penceresi açılıyor
                    self._adrenaline_timer = 5.0
                    game.add_event("damage_text", self.x, self.y-50, value="⚡ ADRENALİN!", color=(255, 200, 0), timer=1.0)
            else:
                self._adrenaline_timer -= dt
                if self._adrenaline_timer <= 0:
                    # Döngüyü yeniden başlat
                    self._adrenaline_cd = 20.0
                    self._adrenaline_timer = 0.0

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

        # --- AURA VE ALAN ETKİLERİ ---
        if not hasattr(self, '_aura_tick_timer'):
            self._aura_tick_timer = 1.0

        self._aura_tick_timer -= dt
        if self._aura_tick_timer <= 0:
            self._aura_tick_timer = 1.0
            
            decay = self.stats.get("decayAura", 0)
            static_dmg = self.stats.get("static_field", 0)
            starfall = self.stats.get("starfallAura", 0)
            chaos = getattr(self, "has_chaos_field", False)
            
            if decay > 0 or static_dmg > 0 or chaos:
                from logic.status_effects import apply_slow
                for e in game.iter_enemies_near(self.x, self.y, 400):
                    if e.dead or getattr(e, 'is_trap', False): continue
                    if decay > 0:
                        e.take_damage(self.max_hp * 0.05 * decay, game, from_player=True)
                    if static_dmg > 0:
                        e.take_damage(static_dmg, game, from_player=True)
                        game.add_event("explosion", e.x, e.y, radius=20, color=(100, 200, 255), timer=0.1)
                    if chaos:
                        if random.random() < 0.30:
                            effect_type = random.choice(['slow', 'poison', 'fire'])
                            if effect_type == 'slow':
                                apply_slow(e.effect_manager, duration=2.0, mult=0.5)
                            elif effect_type == 'poison':
                                e.apply_dot('poison', 25.0, 3.0)
                            elif effect_type == 'fire':
                                e.apply_dot('fire', 35.0, 2.0)
                                
            # Starfall Aura
            if starfall > 0:
                targets = list(game.iter_enemies_near(self.x, self.y, 600))
                if targets:
                    target = random.choice(targets)
                    game.add_event("explosion", target.x, target.y, radius=80, color=(255, 100, 0), timer=0.3)
                    target.take_damage(150 * starfall, game, from_player=True)
                    for e in game.iter_enemies_near(target.x, target.y, 80):
                        if not e.dead and e != target:
                            e.take_damage(75 * starfall, game, from_player=True)

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
            mult_bonus = max(0, (1.0 - ratio) * 1.0)  # max +1.0 (2x toplam)
            self._low_hp_rage_mult = 1.0 + mult_bonus

        # --- EVRİM PASİFLERİ (zamanlayıcılar) ---
        evo_p = getattr(self, 'evolution_passive', '')

        # Gladyatör: her öldürmede 1sn hız
        if self._gladiator_timer > 0:
            self._gladiator_timer -= dt

        # Ölüm Gölgesi: öldürünce kısa görünmezlik
        if self._kill_invis_timer > 0:
            self._kill_invis_timer -= dt
            if self._kill_invis_timer <= 0:
                self._kill_invis_timer = 0.0
                # Artifact görünmezliği hâlâ aktifse ona dokunma
                if self.artifact_timer <= 0:
                    self.is_invisible = False

        # Fırtına Bıçağı: öldürme yığını (max 10, 3sn'de sıfırlanır)
        if self._ks_timer > 0:
            self._ks_timer -= dt
            if self._ks_timer <= 0:
                self._ks_timer = 0.0
                self._ks_stacks = 0

        # Paladin: 1sn'lik kutsal aura (küçük şifa + çevreyi yavaşlat)
        if evo_p == 'paladin_aura':
            self._paladin_tick -= dt
            if self._paladin_tick <= 0:
                self._paladin_tick = 1.0
                from logic.status_effects import apply_slow
                self.heal(self.max_hp * 0.02)
                r = 260
                for e in game.iter_enemies_near(self.x, self.y, r):
                    if e.dead or getattr(e, 'is_trap', False):
                        continue
                    dx, dy = e.x - self.x, e.y - self.y
                    if dx * dx + dy * dy <= r * r:
                        apply_slow(e.effect_manager, duration=1.2, mult=0.8, name="Paladin")

        # Kale Mimarı: her taret saniyede %0.5 max HP yeniler
        if evo_p == 'heal_turret':
            self._heal_turret_tick -= dt
            if self._heal_turret_tick <= 0:
                self._heal_turret_tick = 1.0
                mine = [t for t in getattr(game, 'turrets', [])
                        if getattr(t, 'owner', None) is self and not getattr(t, 'dead', False)]
                if mine:
                    self.heal(self.max_hp * 0.005 * len(mine))

    def get_conditional_dmg_mult(self):
        """Koşullu hasar çarpanları: Berserker Rage kartı ve Şehit (low_hp_rage) evrimi.
        Bu bayraklar update() içinde hesaplanıyordu ama hiçbir hasar formülü okumuyordu (S6)."""
        m = 1.0
        if getattr(self, '_berserker_active', False):
            m *= 1.8
        m *= getattr(self, '_low_hp_rage_mult', 1.0)
        # Adrenalin kartı: timer dönüyordu ama hiçbir buff uygulanmıyordu (P3)
        if getattr(self, '_adrenaline_timer', 0) > 0:
            m *= 1.2
        # Asil Vampir: tam canda hasar bonusu
        if getattr(self, 'evolution_passive', '') == 'full_hp_bonus':
            if self.hp >= self.max_hp * 0.95:
                m *= 1.5
        # Fırtına Bıçağı: öldürme yığını başına +%3 hasar
        m *= 1.0 + 0.03 * getattr(self, '_ks_stacks', 0)
        return m

    def get_elemental_mults(self):
        """Element hasar çarpanlarını TOPLAMSAL birleştirir (F1).

        elementDmgMult ve fireDmgMult/frostDmgMult'ın ikisi de "yüzde hasar"
        statı; eskiden çarpımsal uygulandıkları için tek bir mermide
        (1+1.3)*(1+1.0) = 4.6x gibi çarpanlar çıkıyor, dmgMult ve dotDmgMult ile
        birlikte 17x'e ulaşıyordu. Artık aynı havuzda toplanırlar:
        1.0 + elementDmgMult + <tipe özel>.

        Dönüş: (fire, frost, other) — other zehir/yıldırım gibi tipe özel
        çarpanı olmayan elementler için.
        """
        elem = self.stats.get("elementDmgMult", 0.0)
        fire = max(0.0, 1.0 + elem + self.stats.get("fireDmgMult", 0.0))
        frost = max(0.0, 1.0 + elem + self.stats.get("frostDmgMult", 0.0))
        other = max(0.0, 1.0 + elem)
        return fire, frost, other

    def gain_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_to_next_level:
            self.level_up()

    def level_up(self):
        # XP eşiği HARCANIR, sonra ortak seviye kazanımı uygulanır
        self.xp -= self.xp_to_next_level
        self._apply_level_gain()

    def grant_free_level(self):
        """Bedava seviye verir (kart ekranındaki 'Atla' ödülü gibi).

        Dışarıdan `p.level += 1` yapıldığında xp_to_next_level güncellenmediği
        için oyuncu sonraki seviyeye 250 XP erken ulaşıyor, ardından eğri
        zıplıyordu; ayrıca can tazeleme ve Mutasyon kartı tetiklemesi
        atlanıyordu (F9). Bu metot XP eğrisini senkron tutar.
        """
        self._apply_level_gain()

    def _apply_level_gain(self):
        """level_up ve grant_free_level'ın ortak gövdesi (XP düşümü hariç)."""
        self.level += 1
        if hasattr(self, 'game') and hasattr(self.game, 'track_quest'):
            self.game.track_quest("reach_level", self.level)
        # YENİ DENGELEME: Katlanarak değil doğrusal artış (Wave 10 -> L14, Wave 20 -> L30 hedefine uygun)
        self.xp_to_next_level = 100 + self.level * 250
        self.skill_points += 1
        # Ascendancy puanı: seviye 20'den itibaren her seviyede +1 (evrim
        # seviye 20'de seçilir; sonraki seviyeler alt-sınıf ağacını besler).
        if self.level >= 20:
            self.ascendancy_points += 1
        self.hp = self.max_hp # Can tazele
        self.level_up_timer = 2.0 # 2 saniye ekranda yazı kalsın
        # Seviye atlamanın tek göstergesi bir yazıydı; artık görsel patlama var
        if hasattr(self, 'game') and self.game is not None:
            audio.play('level_up')
            vfx.level_up(self.game, self.x, self.y)
        print(f"LEVEL UP! Yeni Seviye: {self.level}")
        
        # Mutation Kartı Kontrolü
        if getattr(self, "has_mutation", False):
            if not hasattr(self, 'skills_permanent'):
                self.skills_permanent = {}
            stat_options = ["dmgMult", "attack_speed_bonus", "max_hp", "armor", "speed"]
            buff_stat = random.choice(stat_options)
            debuff_stat = random.choice([s for s in stat_options if s != buff_stat])
            
            # Buff (+20%)
            if buff_stat == "dmgMult": self.skills_permanent["dmgMult"] = self.skills_permanent.get("dmgMult", 0) + 0.20
            elif buff_stat == "attack_speed_bonus": self.skills_permanent["attack_speed_bonus"] = self.skills_permanent.get("attack_speed_bonus", 0) + 0.20
            elif buff_stat == "max_hp": self.skills_permanent["max_hp"] = self.skills_permanent.get("max_hp", 0) + 20
            elif buff_stat == "armor": self.skills_permanent["armor"] = self.skills_permanent.get("armor", 0) + 20
            elif buff_stat == "speed": self.skills_permanent["speed"] = self.skills_permanent.get("speed", 0) + 0.20
            
            # Debuff (-15%)
            if debuff_stat == "dmgMult": self.skills_permanent["dmgMult"] = self.skills_permanent.get("dmgMult", 0) - 0.15
            elif debuff_stat == "attack_speed_bonus": self.skills_permanent["attack_speed_bonus"] = self.skills_permanent.get("attack_speed_bonus", 0) - 0.15
            elif debuff_stat == "max_hp": self.skills_permanent["max_hp"] = self.skills_permanent.get("max_hp", 0) - 15
            elif debuff_stat == "armor": self.skills_permanent["armor"] = self.skills_permanent.get("armor", 0) - 15
            elif debuff_stat == "speed": self.skills_permanent["speed"] = self.skills_permanent.get("speed", 0) - 0.15
            
            self.inv_manager.recalculate_stats()
            self.hp = min(self.hp, self.max_hp)
            if hasattr(self, 'game') and self.game:
                self.game.add_event("damage_text", self.x, self.y - 40, value=f"Mutasyon: +{buff_stat} / -{debuff_stat}", color=(200, 50, 200), timer=2.0)
        
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

    def _consume_phantom_crit(self):
        """Hayalet Nişancı (first_shot_invisible): 2sn beklemeden sonraki ilk atış
        garantili kritiktir. Atış BAŞINA bir kez çağrılır (mermi başına değil),
        yoksa çoklu atışta yalnızca ilk mermi kritik olurdu."""
        if not getattr(self, '_phantom_first_shot', False):
            return False
        now = pygame.time.get_ticks()
        ready = (now - getattr(self, '_last_phantom_shot', -10000)) > 2000
        self._last_phantom_shot = now
        return ready

    SHOCKWAVE_RADIUS = 90

    def emit_shockwave(self, game):
        """'Şok Dalgası' (shockwave) affix'i: her saldırıda oyuncunun etrafında
        sabit hasarlı bir darbe. Stat tanımlıydı ama hiçbir yerde okunmuyordu."""
        sw = self.stats.get("shockwave", 0)
        if sw <= 0:
            return
        r = self.SHOCKWAVE_RADIUS
        for e in game.iter_enemies_near(self.x, self.y, r):
            if e.dead or getattr(e, 'is_trap', False):
                continue
            dx = e.x - self.x
            dy = e.y - self.y
            if dx * dx + dy * dy <= r * r:
                e.take_damage(sw, game, from_player=True)
        game.add_event("shockwave", self.x, self.y, radius=r,
                       color=(255, 220, 120), timer=0.25)

    def shoot(self, game, is_bomb=None):
        # Silah kontrolü
        weapon = self.inv_manager.equipped.get("weapon")
        if weapon and weapon.get('isCommander'):
            # Komuta silahı ateş etmez, sadece buff verir.
            return
            
        if weapon and weapon.get('isTrapItem'):
            from entities.cloud import Cloud
            trap_dmg = self.stats.get("trapDmg", 100) * self.stats.get("dmgMult", 1.0)
            trap_radius = self.stats.get("trapRadius", 80)
            # Mayını oyuncunun olduğu yere bırakıyoruz (5 dakika kalır)
            mine = Cloud(game.entity_id_counter, self.x, self.y, radius=trap_radius, duration=300, is_mine=True, mine_dmg=trap_dmg)
            game.clouds.append(mine)
            game.entity_id_counter += 1
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
            # physDmgMult SADECE fiziksel tarafa uygulanır (yumruk saf fiziksel)
            final_dmg = ((20 + phys_flat) * self.stats.get("dmgMult", 1.0)
                         * self.get_conditional_dmg_mult()
                         * (1.0 + self.stats.get("physDmgMult", 0)))
            game.add_event("damage_text", self.x, self.y - 20, value="YUMRUK!", color=(200, 200, 200), timer=0.3)
            # Görsel Efekt
            r_val = (80 + self.stats.get("meleeRangeFlat", 0)) * self.stats.get("meleeRangeMult", 1.0)
            game.add_event("slash", self.x, self.y, angle=self.facing_angle, range=r_val, arc=1.0, timer=0.1)
            for e in game.iter_enemies_near(self.x, self.y, r_val):
                dx = e.x - self.x
                dy = e.y - self.y
                if not e.dead and dx * dx + dy * dy < r_val * r_val:
                    e.take_damage(final_dmg, game, from_player=True)
            return

        # --- RANGET/PROJECTILE ATTACK LOGIC ---
        # (Moved from execute_fallback_melee to solve class shooting issues)
        
        # Base Statlar (Phys, Poison vb.) zaten recalculate_stats ile toplandı
        base_phys = max(0, self.stats.get("physDmg", 20))  # negatif hasar guard'i (H8)
        base_poison = self.stats.get("poisonDps", 0)
        
        # Çarpanlar
        mult = self.stats.get("dmgMult", 1.0) * self.get_conditional_dmg_mult()
        # Element hasar çarpanları (Sorcerer sınıf kimliği + Elementalist skill +
        # auralar). fire/frost yüzdeleri elementDmgMult ile TOPLANIR, çarpılmaz (F1).
        fire_mult, frost_mult, elem_mult = self.get_elemental_mults()

        # physDmgMult (eşya/affix "Fiziksel Hasar %") YALNIZCA fiziksel hasara
        # uygulanır. `mult` aşağıda ateş/buz/zehir hasarlarını da besliyor;
        # oraya karıştırılırsa element hasarı da şişerdi. Bu yüzden ayrı
        # bir phys_mult tutulur (stat 0 iken phys_mult == mult).
        phys_mult = mult * (1.0 + self.stats.get("physDmgMult", 0))

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
            final_dmg_base = (base_phys + phys_flat) * phys_mult
            p_type = 'katana'
        else:
            final_dmg_base = (base_phys + phys_flat) * phys_mult
            p_type = 'poison' if getattr(self, "poison_convert", False) else 'normal'
            if not getattr(self, "poison_convert", False):
                if self.stats.get("fireDmgMult", 0) > 0.2: p_type = 'fire'
                if self.stats.get("frostDmgMult", 0) > 0.2: p_type = 'frost'
        
        # Çoklu Atış (Multi-shot)
        count = int(self.stats.get("projectileCount", 1))
        
        if is_katana:
            # Katana yakın dövüş: piksel taban + piksel bonus, sonra çarpan (F4)
            range_val = (180 + self.stats.get("meleeRangeFlat", 0) * 1.5) * self.stats.get("meleeRangeMult", 1.0)
            
            # --- KRİTİK VURUŞ ---
            force_crit = getattr(self, '_sorcerer_force_crit', False) or self._consume_phantom_crit()
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
                # Katana elementleri SADECE DoT olarak uygulanır; dot_mult burada
                # yerinde (anlık hasara değil, süreli hasara giriyor) - F1
                sorcerer_elem = getattr(self, '_sorcerer_override_element', None)
                if sorcerer_elem == 'fire':
                    fire_dmg = (self.stats.get("fireDamage", 0) + self.stats.get("fireDmgFlat", 0) + 15) * mult * dot_mult * fire_mult
                    e.apply_dot('fire', fire_dmg, 4.0)
                elif sorcerer_elem == 'frost':
                    frost_dmg = (self.stats.get("frostDamage", 0) + self.stats.get("frostDmgFlat", 0) + 15) * mult * dot_mult * frost_mult
                    e.apply_dot('frost', frost_dmg * 0.5, 4.0)
                elif sorcerer_elem == 'poison':
                    poison_dps = (base_poison + 15) * mult * dot_mult * elem_mult
                    e.apply_dot('poison', poison_dps, 5.0)
                else:
                    poison_dps = base_poison * mult * dot_mult * elem_mult
                    if poison_dps > 0: e.apply_dot('poison', poison_dps, 5.0)
                    fire_dmg = (self.stats.get("fireDamage", 0) + self.stats.get("fireDmgFlat", 0)) * mult * dot_mult * fire_mult
                    if fire_dmg > 0: e.apply_dot('fire', fire_dmg, 4.0)
                    frost_dmg = (self.stats.get("frostDamage", 0) + self.stats.get("frostDmgFlat", 0)) * mult * dot_mult * frost_mult
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
            self.emit_shockwave(game)
            return # Katana atışı bitti, normal mermi koduna geçme

        # Mermi hızı: bullet_speed (yetenek ağacı, düz +hız) ve rangedSpeed
        # (SET_LIGHTNING 3pc, yüzde) statları tanımlıydı ama okunmuyordu.
        proj_speed = (15 + self.stats.get("bullet_speed", 0)) \
            * (1.0 + self.stats.get("rangedSpeed", 0))
        # Menzilli merminin ömrü yakın dövüş menzil statına bağlıydı (F4);
        # yakın dövüş statının menzilli silaha etkisi kaldırıldı.
        proj_lifetime = 180
        
        # Fırın (Furnace) Kartı Kontrolü
        if getattr(self, "has_furnace", False):
            p_type = 'fire'
        
        # Mermi Stats
        if is_bomb:
            bounce = 0
            pierce = 0
        else:
            bounce = int(self.stats.get("bounce", 0))
            pierce = int(self.stats.get("pierce", 0))
            
            # Sekme Ustası (Ricochet Master)
            if getattr(self, "has_ricochet_master", False):
                bounce += 1
                pierce = max(0, pierce - 1)
                proj_speed *= 0.85
                
        count = int(self.stats.get("projectileCount", 1))
        # AOE Hesabı (Radius 50 = ~2x Karakter Boyutu)
        aoe = 50 * self.stats.get("aoe", 1.0)
        
        # Çoklu Atış (Multi-shot) - Açılı
        # Taban 15° (~0.26 rad, eski sabit değer). spreadAngle affix'i /
        # SET_SHOTGUN 3pc yayılımı genişletir; stat 0 iken davranış aynıdır.
        spread = math.radians(15 + self.stats.get("spreadAngle", 0))
        start_angle = self.facing_angle - (spread * (count - 1) / 2)
        
        bounce_mult = 1.3 if getattr(self, "has_ricochet_master", False) else 1.0

        # Hayalet Nişancı garantili kritiği: atış başına bir kez tüketilir,
        # salvo'daki tüm mermilere uygulanır
        phantom_crit = self._consume_phantom_crit()

        from entities.projectile import Projectile
        for i in range(count):
            angle = start_angle + (i * spread)
            vx = math.cos(angle) * proj_speed
            vy = math.sin(angle) * proj_speed
            
            # Namlu çıkış noktası
            sx = self.x + math.cos(angle) * 20
            sy = self.y + math.sin(angle) * 20
            
            # --- KRİTİK VURUŞ ---
            force_crit = getattr(self, '_sorcerer_force_crit', False) or phantom_crit
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
            
            is_boomerang = False
            weapon_dict = self.inv_manager.equipped.get("weapon")
            if weapon_dict:
                is_boomerang = weapon_dict.get("isBoomerang", False)

            # Şişe imlecin olduğu yere düşer, maksimum menzille sınırlı.
            # Menzil "aoe" statına bağlanmıyor: aoe patlama ALANINI büyütür,
            # atış mesafesini değil.
            throw_range = 0
            if p_type_final == 'bomb':
                throw_range = BOMB_THROW_RANGE
                if self.aim_x is not None:
                    # Mesafe namlu çıkışından ölçülür, yoksa şişe imlecin
                    # 20px gerisine düşer
                    aim_dist = math.hypot(self.aim_x - sx, self.aim_y - sy)
                    throw_range = max(BOMB_MIN_THROW_RANGE,
                                      min(aim_dist, BOMB_THROW_RANGE))

            p = Projectile(game.entity_id_counter, sx, sy, vx, vy,
                                             final_dmg, bounce, pierce,
                                             p_type=p_type_final, aoe=aoe, is_crit=is_crit, lifetime=proj_lifetime, is_returning=is_boomerang, bounce_dmg_mult=bounce_mult,
                                             throw_range=throw_range)
            
            if is_katana:
                p.is_melee = True
                p.pierce = 99
            
            # Elementel Statları Aktar
            # DİKKAT (F1): p.fire_dmg hem DoT'a hem de explode()'un ANLIK alan
            # hasarına besleniyor. dotDmgMult "süreli hasar" statı olduğu için
            # burada UYGULANMAZ; mermi üzerinde p.dot_mult olarak taşınır ve
            # yalnızca DoT tarafında çarpılır.
            p.dot_mult = dot_mult
            if self.stats.get("omniElement", 0) > 0:
                p.fire_dmg  = (self.stats.get("fireDamage", 0) + self.stats.get("fireDmgFlat", 0) + 15) * mult * max(1.0, fire_mult)
                p.frost_dmg = (self.stats.get("frostDamage", 0) + self.stats.get("frostDmgFlat", 0) + 15) * mult * max(1.0, frost_mult)
                p.poison_dps = (base_poison + 15) * mult * elem_mult
            else:
                if sorcerer_elem == 'fire':
                    p.fire_dmg  = (self.stats.get("fireDamage", 0) + self.stats.get("fireDmgFlat", 0) + 15) * mult * fire_mult
                elif sorcerer_elem == 'frost':
                    p.frost_dmg  = (self.stats.get("frostDamage", 0) + self.stats.get("frostDmgFlat", 0) + 15) * mult * frost_mult
                elif sorcerer_elem == 'poison' or (is_bomb and base_poison > 0):
                    p.poison_dps = (base_poison + 15) * mult * elem_mult
                else:
                    p.poison_dps = base_poison * mult * elem_mult
                    p.fire_dmg   = (self.stats.get("fireDamage", 0) + self.stats.get("fireDmgFlat", 0)) * mult * fire_mult
                    p.frost_dmg  = (self.stats.get("frostDamage", 0) + self.stats.get("frostDmgFlat", 0)) * mult * frost_mult
            
            game.projectiles.append(p)
            game.entity_id_counter += 1
            
            # Namlu Ateşi: dokulu parlama + kıvılcım konisi
            if i == 0:
                audio.play('shoot')
                vfx.muzzle(game, sx, sy, angle)
            vfx.emit(game, sx, sy, count=3, color=(255, 235, 180),
                     speed=(5.0, 10.0), size=(2, 5), life=(0.08, 0.14),
                     tex="spark", spread=1.0, angle=angle, drag=0.12)

        self.emit_shockwave(game)

    def execute_fallback_melee(self, game, weapon):
        """Melee silahı varken specialization hatası/eksikliği durumunda temel savurma yapar."""
        base_phys = self.stats.get("physDmg", 20)
        phys_flat = self.stats.get("physDmgFlat", 0)
        base_poison = self.stats.get("poisonDps", 0)
        mult = self.stats.get("dmgMult", 1.0)
        # physDmgMult yalnızca fiziksel vuruşa; aşağıdaki zehir DoT'u `mult`
        # üzerinden hesaplandığı için ayrı tutulur.
        phys_mult = mult * (1.0 + self.stats.get("physDmgMult", 0))

        if getattr(self, "poison_convert", False):
            base_poison += (base_phys + phys_flat)
            base_phys = 0
            phys_flat = 0

        final_dmg = (base_phys + phys_flat) * phys_mult

        range_val = (100 + self.stats.get("meleeRangeFlat", 0)) * self.stats.get("meleeRangeMult", 1.0)
        angle = self.facing_angle
        
        is_flail = weapon.get("isFlail", False) if weapon else False
        
        # Görsel
        if is_flail:
            game.add_event("sweep", self.x, self.y, angle=angle, range=range_val, arc=math.pi*2, timer=0.15)
        else:
            game.add_event("sweep", self.x, self.y, angle=angle, range=range_val, arc=1.2, timer=0.15)
        
        for e in game.iter_enemies_near(self.x, self.y, range_val + 160):
            if not e.dead and not e.is_trap:
                dx = e.x - self.x
                dy = e.y - self.y
                hit_range = range_val + e.radius
                if dx * dx + dy * dy < hit_range * hit_range:
                    # Basit Açı Kontrolü (Flail için 360 derece, yani açı sınırı yok)
                    angle_to_e = math.atan2(e.y - self.y, e.x - self.x)
                    if is_flail or abs(angle_to_e - angle) < 0.6: # Yaklaşık 70 derece
                        e.take_damage(final_dmg, game, from_player=True)
                        
                        # Knockback Uygula
                        kb_mult = weapon.get("knockbackMult", 0.0) if weapon else 0.0
                        if kb_mult > 0:
                            push_force = 150 * kb_mult
                            e.kb_x = math.cos(angle_to_e) * push_force
                            e.kb_y = math.sin(angle_to_e) * push_force
                        
                        # Flail için Kendine Çekme (Reverse Knockback)
                        if is_flail:
                            pull_force = 200 # Sabit çekim gücü
                            e.kb_x = math.cos(angle_to_e) * -pull_force
                            e.kb_y = math.sin(angle_to_e) * -pull_force
                        
                        if base_poison > 0:
                            e.apply_dot('poison', base_poison * mult * (1.0 + self.stats.get("dotDmgMult", 0)), 5.0)

        self.emit_shockwave(game)

    # --- TARET YETENEĞİ (R) ---
    # ŞARJ SİSTEMİ: tek bekleme yerine biriken şarj. Taban 2 şarj; biri
    # harcandığında dolum sayacı işlemeye başlar, dolunca bir şarj geri gelir.
    # Böylece oyuncu iki tareti arka arkaya kurup sonra bekleyebilir.
    TURRET_BASE_CD = 5.0        # bir şarjın dolum süresi (saniye)
    TURRET_BASE_CHARGES = 2     # taban şarj kapasitesi

    def get_turret_cooldown(self):
        """Bir şarjın dolum süresi (cooldownReduction kısaltır)."""
        cdr = min(0.7, self.stats.get("cooldownReduction", 0))
        return self.TURRET_BASE_CD * (1.0 - cdr)

    def get_turret_max_charges(self):
        """Şarj kapasitesi. turretCharges statı kartlarla artar."""
        return max(1, self.TURRET_BASE_CHARGES + int(self.stats.get("turretCharges", 0)))

    def is_engineer(self):
        return getattr(self, 'base_class_id', getattr(self, 'class_id', '')) == "engineer"

    def update_turret_charges(self, dt):
        """Şarjları doldurur. Her karede player.update'ten çağrılır."""
        cap = self.get_turret_max_charges()
        if self.turret_charges >= cap:
            # Dolu: sayaç boşta beklesin, bir sonraki harcamada baştan işlesin
            self.turret_charges = cap
            self.turret_recharge = 0.0
            return
        self.turret_recharge += dt
        need = self.get_turret_cooldown()
        while self.turret_recharge >= need and self.turret_charges < cap:
            self.turret_recharge -= need
            self.turret_charges += 1
        if self.turret_charges >= cap:
            self.turret_recharge = 0.0

    def can_place_turret(self):
        """Taret kurulabilir mi? (sınıf + şarj + susturulma)"""
        if not self.is_engineer():
            return False
        if getattr(self, 'is_silenced', False):
            return False
        return self.turret_charges >= 1

    def try_place_turret(self, game):
        """R yeteneği: taret kur. Başarılıysa True döner."""
        if not self.can_place_turret():
            return False
        self.place_turret(game)
        self.turret_charges -= 1
        return True

    def place_turret(self, game):
        limit = int(self.stats.get("turretLimit", 1))

        # Limit kontrolü (En eski tareti sil)
        if len(game.turrets) >= limit:
            old = game.turrets.pop(0)
            # Eskiden sessizce yok oluyordu; oyuncu hangi taretin gittiğini
            # göremiyordu. Artık sökülme efekti var.
            game.add_event("fx", old.x, old.y, tex="smoke", size=56, grow=1.1,
                           color=(150, 150, 160), timer=0.45)
            vfx.emit(game, old.x, old.y, count=6, color=(170, 170, 180),
                     speed=(0.8, 2.4), size=(2, 5), life=(0.3, 0.6),
                     tex="debris", gravity=0.05)

        from entities.turret import Turret
        # SADECE SİLAH SLOTUNDAKİ TARET KİTİNİN STATLARINI AL (Global yetenekleri alma)
        local_stats = self.inv_manager.get_item_local_stats("weapon")
        
        # Aşırı Yükleme kartının bedeli: taretler daha kırılgan
        _hp_pen = getattr(self, "turret_hp_penalty", 1.0)
        new_turret = Turret(game.entity_id_counter, self.x, self.y,
                           hp=self.stats.get("turretMaxHp", 150) * _hp_pen,
                           dmg_mult=self.stats.get("turretDmg", 1.0),
                           fire_rate=self.stats.get("turretRate", 1.0),
                           local_stats=local_stats,
                           owner=self)
        game.turrets.append(new_turret)
        game.entity_id_counter += 1
        # Kurulum geri bildirimi
        audio.play('turret')
        game.add_event("shockwave", self.x, self.y, radius=70,
                       color=(120, 200, 255), timer=0.3)
        game.add_event("fx", self.x, self.y, tex="magic", size=64, grow=0.5,
                       color=(150, 220, 255), timer=0.35, curve="flash")
        vfx.emit(game, self.x, self.y, count=10, color=(160, 220, 255),
                 speed=(1.0, 3.0), size=(2, 4), life=(0.25, 0.5), tex="spark")
        print("Taret Kuruldu!")
            
    def check_minions(self, game):
        # Kuşanılan Pet'e bak
        pet = self.inv_manager.equipped.get("pet")
        
        if not pet:
            # Pet yoksa sadece pet minyonlarını (wolf, dragon) sil
            game.minions = [m for m in game.minions if m.owner != self or m.type not in ["wolf", "dragon"]]
        else:
            # Pet varsa tipini ve sayısını belirle
            m_type = "dragon" if "Ejder" in pet['name'] else "wolf"
            
            # SADECE PET SLOTUNDAKİ MODİFİERLARI AL
            local_stats = self.inv_manager.get_item_local_stats("pet")
            
            count = 1 + int(local_stats.get("projectileCount", 0))
            count += int(self.stats.get("minionCount", 0))
            # Alfa Bağı kartı: yalnızca 1 aktif pet (C5)
            if getattr(self, 'alpha_mode', False):
                count = 1
            # Alt sınır: negatif minionCount pop() IndexError'ı yaratıyordu (C5)
            count = max(0, min(count, 8))  # Sürü tavanı

            my_pet_minions = [m for m in game.minions if m.owner == self and m.type in ["wolf", "dragon"]]
            
            # TİP KONTROLÜ
            if my_pet_minions and my_pet_minions[0].type != m_type:
                 game.minions = [m for m in game.minions if m.owner != self or m.type not in ["wolf", "dragon"]]
                 my_pet_minions = []
            
            if len(my_pet_minions) < count:
                from entities.minion import Minion
                for _ in range(count - len(my_pet_minions)):
                    new_m = Minion(game.entity_id_counter, self.x, self.y, m_type=m_type, owner=self, local_stats=local_stats)
                    game.minions.append(new_m)
                    game.entity_id_counter += 1
            elif len(my_pet_minions) > count:
                for _ in range(max(0, len(my_pet_minions) - count)):
                    if not my_pet_minions:
                        break
                    m = my_pet_minions.pop()
                    if m in game.minions:
                        game.minions.remove(m)
                    
        # --- YÖRÜNGE DRONU (orbitDrones affix'i) ---
        # Stat tanımlıydı ama hiç minyon doğurmuyordu. Affix değerleri ondalık
        # (0.2 - 1.2) geldiği için int() ile kırpmak T3 rulolarını (0.2-0.5)
        # tamamen ölü bırakırdı; pozitif her değer en az 1 drone verir.
        orbit_val = self.stats.get("orbitDrones", 0)
        drone_count = 0
        if orbit_val > 0:
            drone_count = min(4, max(1, int(round(orbit_val))))
        drones = [m for m in game.minions if m.owner == self and m.type == "drone"]
        if len(drones) < drone_count:
            from entities.minion import Minion
            for _ in range(drone_count - len(drones)):
                new_m = Minion(game.entity_id_counter, self.x, self.y, m_type="drone", owner=self)
                game.minions.append(new_m)
                game.entity_id_counter += 1
        elif len(drones) > drone_count:
            for _ in range(len(drones) - drone_count):
                m = drones.pop()
                if m in game.minions:
                    game.minions.remove(m)

        # --- Doppelganger ---
        if getattr(self, "has_doppelganger", False):
            dop_minions = [m for m in game.minions if m.owner == self and m.type == "doppelganger"]
            if not dop_minions:
                from entities.minion import Minion
                new_m = Minion(game.entity_id_counter, self.x, self.y, m_type="doppelganger", owner=self)
                game.minions.append(new_m)
                game.entity_id_counter += 1

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
            "desc": "Dev zırh (+50), +80 can ve saniyede 3 can yenileme."
        },
        # BEASTMASTER
        "beastmaster_emperor": {
            "name": "👑 Pet İmparatoru", "class_base": "beastmaster",
            "stats": {"minionCount": 2, "minionDamage": 0.3, "minionMaxHp": 0.4, "minionRange": 0.2},
            "max_hp_delta": -20,
            "passive": "wind_minions",
            "desc": "+2 minyon sayısı ve sürü genelinde hasar/can bonusu. Can -20."
        },
        "beastmaster_hunter": {
            "name": "🦅 Avcı", "class_base": "beastmaster",
            "stats": {"minionDamage": 2.0, "minionMaxHp": 1.0, "minionRange": 0.6},
            "max_hp_delta": 0,
            "passive": "alpha_pet",
            "desc": "Az sayıda ama devasa güçte pet: minyon hasarı 3x, canı 2x."
        },
        # SNIPER
        "sniper_marksman": {
            "name": "💥 Tetikçi", "class_base": "sniper",
            "stats": {"critChance": 0.25, "critDmg": 1.5, "fireRate": 0.3},
            "max_hp_delta": -20,
            "passive": "crit_ignite",
            "desc": "Krit şans +%25, krit hasarı +%150 ve +%30 atış hızı. Can -20."
        },
        "sniper_phantom": {
            "name": "🌑 Hayalet Nişancı", "class_base": "sniper",
            "stats": {"critDmg": 2.0, "dodgeChance": 0.1},
            "max_hp_delta": -30,
            "passive": "first_shot_invisible",
            "desc": "Kritik vuruşlar 4x hasar verir; +%10 kaçınma. Can -30."
        },
        # ENGINEER
        "engineer_architect": {
            "name": "🏰 Kale Mimarı", "class_base": "engineer",
            "stats": {"turretLimit": 3, "turretDmg": 0.3, "cooldownReduction": 0.2},
            "max_hp_delta": 0,
            "passive": "heal_turret",
            "desc": "+3 taret slotu ve +%30 taret hasarı."
        },
        "engineer_electrician": {
            "name": "⚡ Elektrikçi", "class_base": "engineer",
            "stats": {"turretDmg": 0.8, "turretRate": 0.5, "cooldownReduction": 0.4},
            "max_hp_delta": 0,
            "passive": "chain_lightning",
            "desc": "+%80 taret hasarı ve +%50 taret atış hızı."
        },
        # BOMBER
        "bomber_nuclear": {
            "name": "☢️ Nükleer Bombacı", "class_base": "bomber",
            "stats": {"dmgMult": 0.8, "aoe_bonus": 0.5},
            "max_hp_delta": -30,
            "passive": "chain_explosion",
            "desc": "+%80 hasar ve +%50 patlama alanı. Can -30."
        },
        # Eski hâli "🌊 Kimyager" idi (poisonDps + toxic_cloud) — bu, Simyacı'nın
        # "Zehir Tanrısı" kimliğinin kopyasıydı. Bombacı'nın mayın kimliğine
        # uygun şekilde yeniden temalandı; zehir tamamen Simyacı'ya bırakıldı.
        "bomber_chemist": {
            "name": "🧨 Mayın Uzmanı", "class_base": "bomber",
            "stats": {"dmgMult": 0.4, "aoe_bonus": 0.3},
            "max_hp_delta": 10,
            "passive": "mine_master",
            "desc": "Mayınlar +%35 hasar, +%40 yarıçap ve aynı anda 4 fazla mayın. +%40 hasar."
        },
        # NINJA
        "ninja_shadow": {
            "name": "🗡️ Ölüm Gölgesi", "class_base": "ninja",
            "stats": {"critChance": 0.3, "critDmg": 2.5, "dodgeChance": 0.15},
            "max_hp_delta": -20,
            "passive": "kill_invisible",
            "desc": "Suikastçı: +%30 krit şansı, +%250 krit hasarı, +%15 kaçınma. Can -20."
        },
        "ninja_storm": {
            "name": "🌀 Fırtına Bıçağı", "class_base": "ninja",
            "stats": {"critDmg": 1.0, "dodgeChance": 0.2, "speed": 2, "fireRate": 0.3},
            "max_hp_delta": 0,
            "passive": "kill_speed_stack",
            "desc": "+%30 saldırı hızı, +2 hareket hızı ve +%20 kaçınma."
        },
        # ALCHEMIST
        "alchemist_grandmaster": {
            "name": "🧪 Çılgın Simyacı", "class_base": "alchemist",
            "stats": {"projectileCount": 2, "aoe": 0.3, "attack_speed_bonus": 0.2, "combatRegen": 2.0},
            "max_hp_delta": 20,
            "passive": "mad_bomber",
            "desc": "Aynı anda +2 bomba fırlatır! Atış hızı ve patlama alanı artar."
        },
        "alchemist_poison_god": {
            "name": "🍄 Zehir Tanrısı", "class_base": "alchemist",
            "stats": {"poisonDps": 25, "toxicAura": 50, "dotDmgMult": 0.5},
            "max_hp_delta": -30,
            "passive": "death_cloud",
            "desc": "+25 zehir DPS ve +%50 süreli hasar (DoT) bonusu. Can -30."
        },
        # SORCERER
        "sorcerer_firelord": {
            "name": "🌋 Ateş Başbüyücüsü", "class_base": "sorcerer",
            "stats": {"fireDamage": 60, "fireDmgFlat": 30, "elementDmgMult": 0.8},
            "max_hp_delta": -20,
            "passive": "fire_aoe",
            "desc": "+90 ateş hasarı ve +%80 element hasarı. Can -20."
        },
        "sorcerer_icemage": {
            "name": "❄️ Buz Büyücüsü", "class_base": "sorcerer",
            "stats": {"frostDamage": 40, "frostDmgFlat": 20, "elementDmgMult": 0.6},
            "max_hp_delta": 0,
            "passive": "freeze_on_hit",
            "desc": "+60 buz hasarı (yavaşlatır) ve +%60 element hasarı."
        },
        # BLOODWALKER
        "bloodwalker_noble": {
            "name": "🧛 Asil Vampir", "class_base": "bloodwalker",
            "stats": {"lifesteal": 0.2, "dmgMult": 0.2, "hpRegen": 2.0},
            "max_hp_delta": 30,
            "passive": "full_hp_bonus",
            "desc": "Can çalma +%20, +30 can ve saniyede 2 can yenileme."
        },
        "bloodwalker_martyr": {
            "name": "💔 Şehit", "class_base": "bloodwalker",
            "stats": {"lifesteal": 0.2, "dmgMult": 0.6},
            "max_hp_delta": -50,
            "passive": "low_hp_rage",
            "desc": "Yüksek hasar (+%60) karşılığında -50 can. Yüksek riskli."
        },
    }

    def apply_evolution(self, evo_id):
        evo = self.EVOLUTIONS.get(evo_id)
        if not evo:
            return

        self.evolution = evo_id
        self.evolution_passive = evo.get("passive", "")
        self.sync_class_name()

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

        # Ascendancy (alt-sınıf) ağacını AÇ: bu evrimin başlangıç düğümünü tohumla
        Ascendancy.seed_start(self)

        # Görev takibi: apply_evolution SADECE oyuncu evrim seçtiğinde çağrılır
        # (scenes/game_scene.py). Save yüklemesi evrimi doğrudan alan ataması
        # ile geri yükler (logic/save_manager.py), bu yüzden çift sayım olmaz.
        game = getattr(self, 'game', None)
        if game is not None and hasattr(game, 'track_quest'):
            game.track_quest("evolve", 1)

        print(f"EVRİM GEÇİRİLDİ: {self.class_name} | Pasif: {self.evolution_passive}")

    def dash(self):
        if self.dash_timer <= 0:
            self.dash_active_timer = self.dash_duration
            # Quantum Leap (dashCooldownReduc, corrupted orb) statı tanımlıydı
            # ama okunmuyordu. Artifact CDR ile aynı %80 tavanı kullanır.
            dash_cdr = min(0.8, self.stats.get("dashCooldownReduc", 0))
            self.dash_timer = self.dash_cooldown * (1.0 - dash_cdr)
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

        # Görev takibi: yalnızca artifact GERÇEKTEN kullanıldığında sayılır.
        # Cooldown/susturma/eşya yok durumlarında yukarıdaki return'ler
        # buraya gelmeyi engeller.
        if hasattr(game, "track_quest"):
            game.track_quest("use_artifact", 1)

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
                        e.take_damage(200, game, from_player=True)
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
                    e.take_damage(150, game, from_player=True)
                    
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
            # Geçici stat artışı temp_buffs havuzuna yazılır: doğrudan
            # self.stats'a yazılınca 10 saniye içinde tetiklenen herhangi bir
            # recalculate_stats (eşya, seviye, Kan Öfkesi eşiği, kart) buff'ı
            # sessizce siliyordu (F7).
            if not hasattr(self, 'temp_buffs'):
                self.temp_buffs = {}
            self.temp_buffs["dmgMult"] = 2.5
            self.temp_buffs["speed"] = 1.6
            self.inv_manager.recalculate_stats()
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

    def heal(self, amount):
        """Oyuncuyu iyileştirir ve (gerçekleşen_şifa, overheal) döndürür."""
        if amount <= 0: return 0, 0
        
        needed = self.max_hp - self.hp
        actual_heal = min(amount, needed)
        overheal = max(0, amount - needed)
        
        self.hp += actual_heal

        # Şifa geri bildirimi (can çalma, regen, kart iyileştirmeleri).
        # Küçük tikleri boğmamak için eşik: yalnız hissedilir şifada göster.
        _g = getattr(self, 'game', None)
        if _g is not None and actual_heal >= max(2.0, self.max_hp * 0.01):
            audio.play('heal')
            vfx.heal(_g, self.x, self.y, actual_heal)

        # Kan Bankası (Blood Bank) overheal birikimi
        if getattr(self, "has_blood_bank", False):
            self.blood_bank_amount = getattr(self, "blood_bank_amount", 0) + overheal
            
        return actual_heal, overheal

    def take_damage(self, amount, force=False, is_self_damage=False):
        """Hasar alma mantığı. force=True ise i-frame'i yok sayıp direkt vurur (Sürekli temas hasarı)."""
        if self.is_invulnerable: return
        if self.dash_active_timer > 0: return # Dash sırasında dokunulmazlık
        if not force and self.i_frame_timer > 0: return
        
        # --- DODGE (Kaçınma) ---
        # Kullanım noktası clamp'i: recalc dışı geçici buff'lar bile %60'ı aşamaz (F2)
        if not is_self_damage and random.random() < min(0.60, self.stats.get("dodgeChance", 0)):
            # Sürekli hasarda (Tick damage) dodge şansını biraz azaltabiliriz veya aynı bırakabiliriz
            # Görev takibi: track_quest bellekteki meta cache'ini günceller,
            # disk yazımı yalnızca kristal kazanıldığında olur (P4). Yoğun
            # dalgada saniyede onlarca dodge tetiklense de I/O yapmaz.
            game = getattr(self, 'game', None)
            if game is not None and hasattr(game, 'track_quest'):
                game.track_quest("dodge_hits", 1)
            # Görsel geri bildirim: eskiden hasarı savuşturduğun anlaşılmıyordu
            if game is not None:
                audio.play('dodge')
                vfx.dodge(game, self.x, self.y)
                game.add_event("damage_text", self.x, self.y - 46,
                               value="SIYIRDI", color=(190, 220, 255), timer=0.5)
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
                
            # Payda clamp'i: negatif zırhta sıfıra bölme / negatif hasar (can
            # kazanma) oluşuyordu (C3)
            final_dmg = amount * (100.0 / max(1.0, 100.0 + armor)) * getattr(self, "damage_taken_mult", 1.0)
            final_dmg = max(0.0, final_dmg)
            if final_dmg > 0:
                audio.play('player_hurt')
        else:
            final_dmg = amount
        
        if not is_self_damage:
            self.es_timer = max(1.0, 5.0 - self.stats.get("esDelayReduction", 0))
            
        if final_dmg > 0:
            if self.energy_shield > 0:
                shield_broke = False
                if self.energy_shield >= final_dmg:
                    self.energy_shield -= final_dmg
                    final_dmg = 0
                else:
                    final_dmg -= self.energy_shield
                    self.energy_shield = 0
                    shield_broke = True
                    
                # Statik Zırh
                if getattr(self, "has_static_armor", False) and not is_self_damage:
                    self.energy_shield = 0 # Tamamen sıfırlanır
                    if hasattr(self, 'game') and self.game:
                        from entities.cloud import Cloud
                        self.game.entity_id_counter += 1
                        elec_cloud = Cloud(self.game.entity_id_counter, self.x, self.y,
                                           radius=150, duration=0.5,
                                           fire_dmg=self.stats.get("physDmgFlat", 50) * 2)
                        self.game.clouds.append(elec_cloud)
                        self.game.add_event("damage_text", self.x, self.y - 40, value="STATİK PATLAMA!", color=(255, 255, 0), timer=1.5)
                        
                # Kan Bankası (Kalkan kırılınca)
                if shield_broke and getattr(self, "has_blood_bank", False) and not is_self_damage:
                    stored_blood = getattr(self, "blood_bank_amount", 0)
                    if stored_blood > 0:
                        if hasattr(self, 'game') and self.game:
                            from entities.cloud import Cloud
                            self.game.entity_id_counter += 1
                            blood_cloud = Cloud(self.game.entity_id_counter, self.x, self.y,
                                                radius=180, duration=1.0, poison_dps=stored_blood)
                            self.game.clouds.append(blood_cloud)
                            self.game.add_event("damage_text", self.x, self.y - 60, value=f"KAN PATLAMASI! (+{int(stored_blood)} HP)", color=(255, 0, 0), timer=1.5)
                        self.hp = min(self.max_hp, self.hp + stored_blood)
                        self.blood_bank_amount = 0
                        
                # Cam Kale (Shield Explosion)
                if shield_broke and self.stats.get("shieldExplosion", 0) > 0 and not is_self_damage:
                    if hasattr(self, 'game') and self.game:
                        from entities.cloud import Cloud
                        # Kalkanın maksimum değeri kadar DPS vuran kısa bir alan
                        self.game.entity_id_counter += 1
                        shield_cloud = Cloud(self.game.entity_id_counter, self.x, self.y,
                                             radius=200, duration=0.5,
                                             frost_dmg=self.max_energy_shield)
                        self.game.clouds.append(shield_cloud)
                        self.game.add_event("damage_text", self.x, self.y - 40, value="CAM KALE PATLAMASI!", color=(200, 200, 255), timer=1.5)

                # Iron Will CD Tetikleme
                if shield_broke and self.passive_shield_cd > 0:
                    cd_red = self.stats.get("shieldCdRed", 0)
                    self._shield_timer = max(1, self.passive_shield_cd * (1 - cd_red))
            
            # Ayna Kalkan (Reflection Aura)
            refl = self.stats.get("reflectionAura", 0)
            if refl > 0 and final_dmg > 0 and not is_self_damage:
                if hasattr(self, 'game') and self.game:
                    reflect_dmg = final_dmg * refl
                    for e in self.game.iter_enemies_near(self.x, self.y, 400):
                        if not e.dead and not getattr(e, 'is_trap', False):
                            e.take_damage(reflect_dmg, self.game, from_player=True)
                    self.game.add_event("explosion", self.x, self.y, radius=40, color=(200, 200, 255), timer=0.2)

            # Dikenler (Demir Kale sinerjisi / SET_TANK 4pc / affix) — sabit
            # yansıma hasarı; stat tanımlıydı ama hiçbir yerde okunmuyordu (P3)
            thorns = self.stats.get("thorns", 0)
            if thorns > 0 and final_dmg > 0 and not is_self_damage:
                if hasattr(self, 'game') and self.game:
                    for e in self.game.iter_enemies_near(self.x, self.y, 120):
                        if not e.dead and not getattr(e, 'is_trap', False):
                            e.take_damage(thorns, self.game, from_player=True)

            if final_dmg > 0:
                self.hp -= final_dmg

        # Kan Paktı: hasar alınca XP (kart bayrağı okunmuyordu, P3)
        xp_on_hit = getattr(self, "xp_on_hit_bonus", 0)
        if xp_on_hit > 0 and not is_self_damage and final_dmg > 0:
            self.gain_xp(xp_on_hit)

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
            art = self.inv_manager.equipped.get("artifact") or {}  # None olabilir (C7)
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
        # class_name evrimle değişen gösterim adıdır; kimlik kontrolü class_id ile.
        if self.class_id not in ["warrior", "beastmaster"]:
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
            
        import ui_theme
        from ui_elements import get_font
        ui_theme.draw_world_bar(
            screen, pygame.Rect(int(draw_x - 20), int(draw_y + y_offset), 40, 6),
            hp_ratio, "moss")

        if self.max_energy_shield > 0:
            es_ratio = self.energy_shield / max(1, self.max_energy_shield)
            ui_theme.draw_world_bar(
                screen, pygame.Rect(int(draw_x - 20), int(draw_y - 38), 40, 4),
                es_ratio, "night")

        # Sayısal Can Gösterimi (cache'li font; her karede SysFont açılıyordu)
        hp_text = f"{int(self.hp)}/{int(self.max_hp)}"
        hp_surf = get_font(11, bold=True).render(hp_text, True, ui_theme.TEXT_COL)
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

    # Kalıcı öz (essence) tavanları: sınırsız stat akışı geç oyunda tüm
    # denge zarflarını anlamsızlaştırıyordu (S9)
    ESSENCE_CAPS = {"max_hp": 200, "phys_dmg": 60, "element_dmg": 0.60, "armor": 60, "speed": 1.5}

    def consume_essence(self, essence_type, value):
        """Öz tüketerek kalıcı stat artışı sağlar."""
        if essence_type == "xp":
            self.gain_xp(value)
            return True

        if essence_type in self.essence_stats:
            cap = self.ESSENCE_CAPS.get(essence_type)
            if cap is not None:
                if self.essence_stats[essence_type] >= cap:
                    return False  # Tavana ulaşıldı
                value = min(value, cap - self.essence_stats[essence_type])
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
        
        count = 0
        for it in essences:
            # Tavana ulaşan özler tüketilmez ve envanterde kalır
            if self.consume_essence(it['essence_type'], it['val']):
                self.inventory.remove(it)
                count += 1

        return count
