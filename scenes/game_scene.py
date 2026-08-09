from scenes.base_scene import BaseScene
from logic.game_logic import GameLogic
from entities.player import Player
from ui_elements import (TabButton, EquippedRow, BackpackItemCard, SkillButton,
                         MarketCard, render_fit, shrink_to_width,
                         strip_unsupported, get_skull_crest)
from logic.skill_tree import SkillTree
import pygame
import math
import time
import random
import sys
import vfx

# --- Eşya tooltip: okunur stat etiketleri + kıyaslama ---
ITEM_STAT_LABEL = {
    "physDmg": "Fiziksel Hasar", "meleeRange": "Menzil", "attackCooldown": "Vuruş Süresi",
    "fireDamage": "Ateş Hasarı", "frostDamage": "Buz Hasarı", "poisonDps": "Zehir DPS",
    "elementDmgMult": "Element Hasarı", "fireDmgMult": "Ateş Hasarı", "frostDmgMult": "Buz Hasarı",
    "dmgMult": "Hasar", "physDmgFlat": "Fiziksel", "fireDmgFlat": "Ateş", "frostDmgFlat": "Buz",
    "aoe": "Alan", "lifesteal": "Can Çalma", "critChance": "Kritik Şans", "critDmg": "Kritik Hasar",
    "armor": "Zırh", "maxHp": "Can", "max_hp": "Can", "maxEnergyShield": "Kalkan",
    "dodgeChance": "Kaçınma", "pierce": "Delme", "bounce": "Sekme", "projectileCount": "Mermi",
    "attack_speed_bonus": "Saldırı Hızı", "attack_speed_mult": "Saldırı Hızı", "speed": "Hız",
    "regen": "Can Yenileme", "magicFind": "Eşya Bulma", "goldGain": "Altın", "xpGain": "Deneyim",
    "turretDmg": "Taret Hasarı", "turretRate": "Taret Hızı", "turretMaxHp": "Taret Canı",
    "turretLimit": "Taret Limiti", "minionDamage": "Minyon Hasarı", "minionCount": "Minyon Sayısı",
    "minionMaxHpFlat": "Minyon Canı", "aura_limit": "Aura Limiti", "armorPen": "Zırh Delme",
    "dotDmgMult": "DoT Hasarı", "cooldownReduction": "Bekleme Azaltma",
}
_PCT_STATS = {"elementDmgMult", "fireDmgMult", "frostDmgMult", "dmgMult", "aoe", "lifesteal",
              "critChance", "critDmg", "dodgeChance", "attack_speed_bonus", "attack_speed_mult",
              "magicFind", "goldGain", "xpGain", "turretDmg", "turretRate", "minionDamage",
              "armorPen", "dotDmgMult", "cooldownReduction"}
_LOWER_BETTER = {"attackCooldown"}   # düşük = daha iyi (kıyasta yön ters)
_EQUIP_SLOTS = {"weapon", "helmet", "chest", "amulet", "pet", "artifact"}


def _fmt_stat_val(stat, val):
    """Stat değerini okunur biçimle: yüzde statları %N, diğerleri düz sayı."""
    if stat in _PCT_STATS:
        return f"%{val * 100:.0f}"
    if isinstance(val, float) and val.is_integer():
        val = int(val)
    return f"{val:g}" if isinstance(val, (int, float)) else str(val)


SKILL_HELP = {
    'max_hp': 'Daha fazla hasara dayanmanı sağlar; mevcut canı da artırır.',
    'regen': 'Her saniye pasif olarak can yeniler.',
    'armor': 'Gelen doğrudan hasarı azaltır.',
    'dodgeChance': 'Bir saldırının hasarını tamamen yok sayma şansı verir.',
    'lifesteal': 'Verdiğin doğrudan hasarın bir bölümünü cana çevirir.',
    'combatRegen': 'Savaş sırasında da çalışan saniyelik can yenilenmesidir.',
    'maxEnergyShield': 'Canından önce tükenen ek enerji kalkanı sağlar.',
    'esRegen': 'Hasar almadığında enerji kalkanını daha hızlı doldurur.',
    'esDelayReduction': 'Enerji kalkanının yeniden dolmaya başlama süresini kısaltır.',
    'max_hp_pct': 'Maksimum canı yüzde olarak değiştirir; eksi değerler kart bedelidir.',
    'dmgMult': 'Tüm doğrudan ve element saldırılarının hasarını artırır.',
    'meleeRange': 'Yakın dövüş saldırılarının erişim mesafesini artırır.',
    'meleeRangeFlat': 'Yakın dövüş erişimine piksel cinsinden sabit mesafe ekler.',
    'meleeRangeMult': 'Yakın dövüş erişim mesafesini çarpan olarak büyütür.',
    'physDmgFlat': 'Her fiziksel vuruşa sabit hasar ekler.',
    'physDmgMult': 'Yalnızca fiziksel hasarı çarpan olarak artırır.',
    'fireDmgFlat': 'Vuruşlara sabit ateş hasarı ve yanma ekler.',
    'fireDmgMult': 'Mevcut ateş hasarının tamamını çarpan olarak artırır.',
    'frostDmgFlat': 'Vuruşlara sabit buz hasarı ekler.',
    'frostDmgMult': 'Mevcut buz hasarının tamamını çarpan olarak artırır.',
    'critChance': 'Vuruşların kritik hasar verme olasılığını artırır.',
    'attack_speed_bonus': 'Saldırılar arasındaki bekleme süresini azaltır.',
    'pierce': 'Merminin ek bir düşmanın içinden geçmesini sağlar.',
    'bounce': 'Merminin ilk hedeften sonra ek bir hedefe sekmesini sağlar.',
    'bullet_speed': 'Mermilerin hedefe ulaşma hızını artırır.',
    'aoe_bonus': 'Patlama ve alan saldırılarının yarıçapını büyütür.',
    'projectileCount': 'Her saldırıda aynı anda ek bir mermi oluşturur.',
    'killSpeedBoost': 'Öldürme serisi sırasında hareket hızını artırır.',
    'elementDmgMult': 'Ateş, buz ve zehir dahil tüm element hasarını artırır.',
    'dotDmgMult': 'Zehir ve yanma gibi zamanla verilen hasarı artırır.',
    'spreadAngle': 'Çok mermili atışların yayılma açısını genişletir.',
    'shockwave': 'Yakın dövüş vuruşlarında çevreye hasar veren şok dalgası yayar.',
    'rangedSpeed': 'Menzilli silahların atış hızını artırır.',
    'brutal': 'Düşmanlara verdiğin nihai hasarı topluca artırır.',
    'frost_slow': 'Vuruşların hedefi yavaşlatmasını sağlar.',
    'statusDuration': 'Düşmana uyguladığın etkilerin süresini uzatır.',
    'aura_effectiveness': 'Kuşandığın auraların tüm etkilerini güçlendirir.',
    'speed': 'Temel hareket hızını artırır.',
    'dashCooldownReduc': 'Atılma (dash) yeteneğinin bekleme süresini kısaltır.',
    'orbitDrones': 'Etrafında dönerek düşmanlara saldıran dron kazandırır.',
    'thiefChance': 'Vuruşlarında düşmandan altın çalma şansı verir.',
    'blackHoleChance': 'Vuruşlarında düşmanları içine çeken kara delik açma şansı verir.',
    'magicFind': 'Daha yüksek nadirlikte eşya bulma şansını artırır.',
    'shopRarity': 'Kervanda daha yüksek seviye eşya çıkma ihtimalini artırır.',
    'xpGain': 'Tüm kaynaklardan kazanılan deneyimi artırır.',
    'goldGain': 'Düşmanlardan ve ödüllerden kazanılan altını artırır.',
    'magnetRadius': 'Yerdeki eşya ve altınları daha uzaktan toplar.',
    'turretMaxHp': 'Taretlerin maksimum dayanıklılığını artırır.',
    'turretDmg': 'Taretlerin verdiği tüm hasarı artırır.',
    'turretRate': 'Taretlerin saldırılar arasındaki bekleme süresini azaltır.',
    'turretLimit': 'Aynı anda kurulabilecek taret sayısını artırır.',
    'minionCount': 'Aynı anda savaşabilecek minyon sayısını artırır.',
    'minionDamage': 'Tüm minyon saldırılarının hasarını artırır.',
    'minionRate': 'Minyonların daha sık saldırmasını sağlar.',
    'minionMaxHp': 'Minyonların maksimum canını çarpan olarak artırır.',
    'minionMaxHpFlat': 'Her minyona sabit miktarda maksimum can ekler.',
    'minionRange': 'Minyonların hedef alma mesafesini artırır.',
    'minionPhysDmgFlat': 'Her minyon vuruşuna sabit fiziksel hasar ekler.',
    'minionPhysDmgMult': 'Minyonların fiziksel hasarını çarpan olarak artırır.',
    'minionFireDmgFlat': 'Minyon vuruşlarına sabit ateş hasarı ekler.',
    'minionFireDmgMult': 'Minyonların ateş hasarını çarpan olarak artırır.',
    'minionFrostDmgFlat': 'Minyon vuruşlarına sabit buz hasarı ekler.',
    'minionFrostDmgMult': 'Minyonların buz hasarını çarpan olarak artırır.',
    'minionBounce': 'Minyon mermilerinin ek hedeflere sekmesini sağlar.',
    'minionPierce': 'Minyon mermilerinin ek düşmanları delmesini sağlar.',
    'minionProjectileCount': 'Her minyon saldırısına ek bir mermi ekler.',
}

CARD_CATEGORY_LABELS = {
    'survival': ('HAYATTA KALMA', (90, 200, 130)),
    'offense': ('SALDIRI', (230, 110, 90)),
    'support': ('DESTEK', (90, 170, 230)),
    'minion': ('MİNYON', (170, 120, 220)),
    'elemental': ('ELEMENT', (230, 170, 70)),
    'curse': ('LANET • YÜKSEK RİSK', (210, 80, 120)),
}

class GameScene(BaseScene):
    def on_enter(self):
        # Varsayılan sınıf 'warrior' eğer seçilmemişse
        selected_class = getattr(self, 'selected_class', 'warrior')
        
        # Gerçek oyun mantığını başlat
        self.logic = GameLogic(self.manager, self.width, self.height, selected_class)
        self.camera_x = 0
        self.camera_y = 0
        self.zoom_level = 1.0
        self.target_zoom = 1.0
        # Daha düşük değerler dev bir ara yüzey oluşturup fill/scale maliyetini
        # katlıyor. 0.65 geniş görüşü korurken piksel bütçesini güvenli tutar.
        self.min_zoom = 0.70
        self.max_zoom = 2.0
        self._world_surface = None
        self._world_surface_size = (0, 0)
        
        # --- APPLY GLOBAL SETTINGS ---
        if hasattr(self.manager, 'global_settings'):
            self.logic.settings.update(self.manager.global_settings)
            
        pending_slot = getattr(self, 'pending_save_slot', None)
        if pending_slot:
            self.logic.save_manager.load_game(self.logic, pending_slot)
            self.pending_save_slot = None
            
        # --- BOSS TEST MODE ---
        if getattr(self, 'is_boss_test', False):
            self.logic.setup_boss_test()
            self.is_boss_test = False # Reset
        
        # Warm Stone: sıcak gri zemin teması (geçerli olan tema — eski
        # "Midnight Slate" atamaları buranın hemen üstünde tekrarlanıyor ve
        # aynı satırlar tarafından eziliyordu).
        # NOT: floor_color_1 yalnızca YEDEKtir; draw_floor_to_surf zemin
        # rengini GameLogic.BIOMES[biome]["color"] üzerinden alır.
        self.tile_size = 128
        self.floor_color_1 = (140, 135, 125)
        self.floor_color_2 = (140, 135, 125)
        self.grid_line_color = (110, 105, 95)
        # Gotik temayla uyumlu serif (bkz. ui_elements.UI_FONT_NAME)
        _THEME_FONT = "Georgia, Times New Roman, serif"
        self.font_main = pygame.font.SysFont(_THEME_FONT, 48, bold=True)
        self.font_sub = pygame.font.SysFont(_THEME_FONT, 24)
        self.font_desc = pygame.font.SysFont(_THEME_FONT, 18)
        self.active_tab = "inventory" # inventory, hero, skills, market, aura
        
        # Aura & Essence UI State
        self.aura_page = 0
        self.synergy_scroll = 0        # sinerji listesi kaydırma ofseti (<= 0)
        self._synergy_max_scroll = 0
        self.aura_msg = ""
        self.aura_msg_timer = 0
        
        # Market & Crafting States
        self.market_tab = "items" # "items" or "orbs"
        self.show_craft_window = False
        self.show_inventory = False
        self.show_stats_panel = False
        # --- YETENEK AĞACI GÖRÜNÜMÜ (kaydır/yakınlaştır) ---
        self._tree_view = None       # {scale, ox, oy} — ilk çizimde fit'e kurulur
        self._tree_fit_scale = 1.0
        self._tree_area = None        # son çizilen grafik alanı (hit-test/pan için)
        self._tree_drag = None        # {start, last, moved} sürükleme durumu
        self.crafting_target = None
        # Craft hata mesajı yalnız pencere açılırken atanıyordu; çizim buna
        # koşulsuz bakıyor, farklı bir yol pencereyi açarsa AttributeError olur.
        self.craft_error_msg = ""
        self.craft_error_timer = 0.0

        # Önceki oyundan kalan rect'ler yeni sahnede yanlış tıklamaya yol
        # açıyordu (bayat hitbox). Her girişte temizlenir.
        self.card_rects = []
        self.evo_rects = []
        self.evo_btn_rects = []
        self.craft_orb_use_rects = []
        self.game_over_restart_rect = pygame.Rect(0, 0, 0, 0)

        # Blood Moon Filter
        self.blood_moon_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.blood_moon_surf.fill((200, 0, 0, 45)) 

        # --- PERF: Preallocate Surfaces & Fonts ---
        self._overlay_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Süpürme efekti yüzeyi: efektin sınırlayıcı kutusu kadar büyür.
        # Eskiden 3840x2160 sabitti ve her efektte ~8.3M piksel fill ediliyordu.
        self._sweep_surface = pygame.Surface((256, 256), pygame.SRCALPHA)
        self.font_combo = pygame.font.SysFont("Georgia, Times New Roman, serif", 28, bold=True)
        # font_boss_name / font_boss_hp kaldırıldı: boss barı artık render_fit
        # kullanıyor (tek metin yardımcısı, otomatik sığdırma).
        
        self.stats_tracker = {
            'total_damage_dealt': 0,
            'total_damage_taken': 0,
            'enemies_killed': 0,
            'highest_hit': 0,
            'gold_earned': 0,
            'items_found': 0,
            'survival_time': 0,
            'waves_survived': 0
        }

        self.init_ui_components()

    def init_ui_components(self):
        from ui_elements import TabButton, EquippedRow, BackpackItemCard, MarketCard
        
        # TABLAR
        _tabs = [("ENVANTER", "inventory"), ("KAHRAMAN", "hero"), ("YETENEK", "skills"),
                 ("YÜKSELİŞ", "ascendancy"), ("KERVAN", "market"), ("AURA", "aura"),
                 ("SİNERJİ", "synergy")]
        _tw, _gap = 138, 6
        _x0 = self.width // 2 - (len(_tabs) * (_tw + _gap) - _gap) // 2
        self.tab_buttons = [
            TabButton(_x0 + i * (_tw + _gap), 40, _tw, 50, lbl, tid)
            for i, (lbl, tid) in enumerate(_tabs)
        ]
        
        # KUŞANILANLAR (SOL)
        self.equip_rows = []
        slot_types = ["weapon", "helmet", "chest", "amulet", "pet", "artifact"]
        for i, stype in enumerate(slot_types):
            # 6 slot için aralığı 75 yaptık
            self.equip_rows.append(EquippedRow(self.width // 2 - 450, 140 + i * 75, 400, 68, stype))
            
        # YETENEK BUTONLARI (3. Sekme) - Dinamik 2 Sütun
        self.skill_btns = []
        self.skill_sub_tabs = ["HAYATTA KALMA", "SALDIRI", "YARDIMCI", "TARET", "MİNYON"]
        self.active_skill_sub_tab = "HAYATTA KALMA"
        
        self.reset_btn_rect = pygame.Rect(self.width // 2 + 250, 85, 150, 40)
        self.refresh_btn_rect = pygame.Rect(self.width // 2 + 250, 105, 180, 45)
        
        # Player.skills'deki tüm yetenekler için buton üret (Grup bazlı yerleştirme)
        p_template = Player("tmp", 0, 0)
        # Butonları draw sırasında filtreleyeceğiz, burada sadece listeyi hazır tutuyoruz
        for i, sk in enumerate(p_template.skills):
            self.skill_btns.append(SkillButton(0, 0, 340, 75, sk['name'], i))
        # ÇANTA (SAĞ) - 6x2 Izgara (12 Slot)
        self.bp_cards = []
        self.inventory_page = 0
        for i in range(12):
            col = i % 2
            row = i // 2
            bx = self.width // 2 + 20 + (col * 290)
            by = 150 + (row * 85)
            self.bp_cards.append(BackpackItemCard(bx, by, 280, 80, i))
            
        # Sayfalama Butonları
        inventory_pager_y = min(665, self.height - 45)
        self.inv_prev_rect = pygame.Rect(self.width // 2 + 20, inventory_pager_y, 120, 35)
        self.inv_next_rect = pygame.Rect(self.width - 160, inventory_pager_y, 120, 35)
        
        # Craft Sayfalama
        self.craft_orb_prev_rect = pygame.Rect(self.width // 2 - 430, self.height // 2 + 250, 100, 35)
        self.craft_orb_next_rect = pygame.Rect(self.width // 2 - 200, self.height // 2 + 250, 100, 35)
        self.craft_mkt_prev_rect = pygame.Rect(self.width // 2 + 170, self.height // 2 + 250, 100, 35)
        self.craft_mkt_next_rect = pygame.Rect(self.width // 2 + 350, self.height // 2 + 250, 100, 35)
        
        self.show_settings = False # ESC Menüsü
        self.setting_tab = "main" # main, save, load
        self.selected_setting_idx = 0
        self.save_slots = []
        
        # MARKET TAB BUTONLARI
        self.market_tab_btns = [
            TabButton(self.width // 2 - 200, 105, 180, 40, "EŞYALAR", "items"),
            TabButton(self.width // 2 + 20, 105, 180, 40, "ORBLAR ∞", "orbs")
        ]
            
        # MARKET (4. Sekme) - 6x2 Izgara (12 Slot)
        self.market_cards = []
        self.market_page = 0
        for i in range(12):
            col = i % 2
            row = i // 2
            mx = self.width // 2 - 400 + (col * 410)
            my = 150 + (row * 85)
            self.market_cards.append(MarketCard(mx, my, 400, 80, i))

        # Market Sayfalama Butonları
        self.mkt_prev_rect = pygame.Rect(self.width // 2 - 400, 150 + 6 * 85 + 5, 120, 35)
        self.mkt_next_rect = pygame.Rect(self.width // 2 + 10, 150 + 6 * 85 + 5, 120, 35)
            
        # SAVAŞA DÖN BUTONU
        self.exit_btn_rect = pygame.Rect(self.width - 220, 40, 180, 50)
        
        # ZORLUK BUTONLARI (Hero Tab)
        # Zorluk butonu rect'leri _diff_button_rects() ile panelden türetilir
        # (sabit liste, panel taşınınca hitbox'ı çizimden ayırıyordu).

        # CRAFT SAYFALAMA
        self.orb_inv_page = 0
        self.orb_market_page = 0
        # self.craft_orb_prev_rect'ler init_ui_components içinde

        # ENVANTER FİLTRELEME & TOPLU SATIŞ
        self.inv_filter_rarity = "TÜMÜ" # TÜMÜ, Normal, Magic, Rare, Unique, Set
        self.inv_filter_type = "TÜMÜ"   # TÜMÜ, weapon, armor, accessory, special
        
        self.rarity_filters = ["TÜMÜ", "Normal", "Magic", "Rare", "Unique", "SET"]
        self.type_filters = ["TÜMÜ", "weapon", "armor", "accessory", "special"]
        
        # Filtre Buton Alanları (SAĞ ÜST)
        # 1. satır: 6 nadirlik, 2. satır: 5 tip (+ ORB toggle). Eskiden 10 rect
        # 2x5 diziliyordu: SET nadirliği tip filtresinin rect'ine biniyor ve
        # hiç seçilemiyordu.
        self.filter_rects = []
        filter_start_x = self.width // 2 + 20
        filter_gap = 4
        filter_available = self.width - filter_start_x - 20
        filter_width = min(110, (filter_available - filter_gap * 5) // 6)
        rarity_count = len(self.rarity_filters)
        for i in range(rarity_count + len(self.type_filters)):
            row = 0 if i < rarity_count else 1
            col = i if i < rarity_count else i - rarity_count
            self.filter_rects.append(pygame.Rect(
                filter_start_x + col * (filter_width + filter_gap),
                110 + row * 40,
                filter_width,
                35,
            ))
            
        # Toplu Satış Butonları (SAĞ ALT)
        # color_key: ui_theme.COLORS anahtarı (ham RGB gömülmez)
        self.mass_sell_btns = [
            {"label": "NORMAL SAT", "rarity": "Normal", "color_key": "steel"},
            {"label": "MAGIC SAT", "rarity": "Magic", "color_key": "night"},
            {"label": "RARE SAT", "rarity": "Rare", "color_key": "gold"},
            {"label": "ÖZLERİ TÜKET", "action": "consume_essences", "color_key": "arcane"}
        ]
        self.mass_sell_rects = []
        mass_gap = 6
        mass_width = min(140, (filter_available - mass_gap * 3) // 4)
        mass_y = min(710, self.height - 45)
        for i in range(4):
            self.mass_sell_rects.append(pygame.Rect(
                filter_start_x + i * (mass_width + mass_gap),
                mass_y,
                mass_width,
                40,
            ))

        # ORB GİZLEME toggle (EŞYA TİPİ FİLTRELERİNİN SONUNA)
        self.orb_toggle_rect = pygame.Rect(
            filter_start_x + 5 * (filter_width + filter_gap),
            150,
            filter_width,
            35,
        )
        self.hide_orbs = True 

        # Savaş sırasında anlık toplamları açan kompakt HUD kontrolü.
        self.stats_button_rect = pygame.Rect(self.width - 270, 75, 250, 36)

    def update(self, dt, events):
        p = self.logic.players[self.logic.local_player_id]
        # Envanter açıksa oyun "Pause" olur
        if not self.show_inventory and not self.show_settings:
            self.logic.update(dt)
            if hasattr(self, 'stats_tracker'):
                self.stats_tracker['survival_time'] += dt
                self.stats_tracker['waves_survived'] = max(0, self.logic.wave.get('level', 1) - 1)

        # Durum bu karede değiştiyse (ör. tam öldüğün kare) ekran henüz
        # çizilmemiştir; o karedeki tık bayat/görünmeyen butonlara düşüp
        # ölüm ekranını atlıyor ya da yanlış evrimi seçtiriyordu.
        state_entered_now = (self.logic.state != getattr(self, '_prev_state', None))
        self._prev_state = self.logic.state

        # ZOOM CALCULATION (Lerp)
        self.zoom_level += (self.target_zoom - self.zoom_level) * 0.1
        if abs(self.zoom_level - self.target_zoom) < 0.002:
            self.zoom_level = self.target_zoom
        
        # Kamera Oyuncuyu Takip Etsin (Zoom'a duyarlı)
        internal_w = self.width / self.zoom_level
        internal_h = self.height / self.zoom_level
        
        target_cam_x = p.x - internal_w / 2
        target_cam_y = p.y - internal_h / 2
        
        # Smooth follow (Lerp)
        self.camera_x += (target_cam_x - self.camera_x) * 0.1
        self.camera_y += (target_cam_y - self.camera_y) * 0.1
        
        # World Bounds (Harita dışına çıkmasın kamera - Zoom'a duyarlı)
        self.camera_x = max(0, min(5000 - internal_w, self.camera_x))
        self.camera_y = max(0, min(5000 - internal_h, self.camera_y))

        # --- 1. OLAY KONTROLÜ (EVENTS) ---
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        mouse_rclicked = False

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                mouse_rclicked = True

            if (
                event.type == pygame.MOUSEWHEEL
                and not self.show_inventory
                and not self.show_settings
                and self.logic.state == "PLAYING"
            ):
                # Zoom hızı ve limitleri
                self.target_zoom += event.y * 0.1
                self.target_zoom = max(self.min_zoom, min(self.max_zoom, self.target_zoom))

            # Sinerji listesi ekrana sığmıyor: tekerlekle kaydırılır
            if (event.type == pygame.MOUSEWHEEL and self.show_inventory
                    and self.active_tab == "synergy"):
                self.synergy_scroll = max(
                    -getattr(self, "_synergy_max_scroll", 0),
                    min(0, self.synergy_scroll + event.y * 45))

            # YETENEK AĞACI: sol tık sürükle = kaydır, tekerlek = yakınlaştır.
            # Düğüm tahsisi mouse-UP'ta (sürükleme değilse) yapılır.
            if self.show_inventory and self.active_tab == "skills":
                if event.type == pygame.MOUSEWHEEL:
                    self._tree_zoom_at(pygame.mouse.get_pos(), event.y)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._tree_area and self._tree_area.collidepoint(event.pos):
                        self._tree_drag = {"start": event.pos, "last": event.pos, "moved": False}
                elif event.type == pygame.MOUSEMOTION and self._tree_drag:
                    lx, ly = self._tree_drag["last"]
                    self._tree_drag["last"] = event.pos
                    if self._tree_view:
                        self._tree_view["ox"] += event.pos[0] - lx
                        self._tree_view["oy"] += event.pos[1] - ly
                        self._tree_clamp_view()
                    if (abs(event.pos[0] - self._tree_drag["start"][0])
                            + abs(event.pos[1] - self._tree_drag["start"][1]) > 6):
                        self._tree_drag["moved"] = True
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self._tree_drag:
                    _drag = self._tree_drag
                    self._tree_drag = None
                    if not _drag["moved"]:
                        self._tree_click_node(pygame.mouse.get_pos(), p)

            if event.type == pygame.KEYDOWN:
                # ESC: Menüyü aç/kapat
                if event.key == pygame.K_ESCAPE:
                    if self.show_craft_window:
                        # Craft penceresi ESC ile kapanmıyordu (P4)
                        self.show_craft_window = False
                        self.crafting_target = None
                        self.craft_error_msg = ""
                        continue
                    if self.show_settings:
                        if self.setting_tab != "main": self.setting_tab = "main"
                        else: self.show_settings = False
                    else:
                        self.show_settings = True
                        self.setting_tab = "main"
                        self.selected_setting_idx = 0
                        self.show_inventory = False
                    continue

                # --- AYARLAR MENÜSÜ KLAVYE KONTROLÜ ---
                if self.show_settings:
                    if self.setting_tab == "main":
                        # Satır sayısı sabit yazılmıştı; ses satırı eklenince
                        # son satır klavyeyle seçilemez hale geliyordu.
                        n_rows = len(self._pause_labels())
                        if event.key == pygame.K_UP: self.selected_setting_idx = (self.selected_setting_idx - 1) % n_rows
                        elif event.key == pygame.K_DOWN: self.selected_setting_idx = (self.selected_setting_idx + 1) % n_rows
                        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT) \
                                and self.selected_setting_idx == self.SOUND_ROW:
                            self.adjust_volume(self.VOLUME_STEP if event.key == pygame.K_RIGHT
                                               else -self.VOLUME_STEP)
                        elif event.key == pygame.K_RETURN:
                            self._trigger_setting_action(self.selected_setting_idx)
                    elif self.setting_tab == "save":
                        if event.key == pygame.K_UP: self.selected_setting_idx = (self.selected_setting_idx - 1) % 2
                        elif event.key == pygame.K_DOWN: self.selected_setting_idx = (self.selected_setting_idx + 1) % 2
                        elif event.key == pygame.K_RETURN:
                            if self.selected_setting_idx == 0:
                                slot_name = f"save_{len(self.logic.save_manager.get_save_slots()) + 1}"
                                self.logic.save_manager.save_game(self.logic, slot_name)
                            else: self.logic.save_manager.save_game(self.logic, "last_save")
                            self.setting_tab = "main"
                    elif self.setting_tab == "load":
                        if self.save_slots:
                            if event.key == pygame.K_UP: self.selected_setting_idx = (self.selected_setting_idx - 1) % len(self.save_slots)
                            elif event.key == pygame.K_DOWN: self.selected_setting_idx = (self.selected_setting_idx + 1) % len(self.save_slots)
                            elif event.key == pygame.K_RETURN:
                                slot = self.save_slots[self.selected_setting_idx]
                                self.logic.save_manager.load_game(self.logic, slot['filename'])
                                self.show_settings = False
                            elif event.key == pygame.K_DELETE:
                                slot = self.save_slots[self.selected_setting_idx]
                                self.logic.save_manager.delete_save(slot['filename'])
                                # Liste açılışta [:5] ile kırpılıyor; yenilerken
                                # kırpmayı atlayınca klavye ekranda görünmeyen
                                # satıra gidebiliyordu.
                                self.save_slots = self.logic.save_manager.get_save_slots()[:5]
                                if self.selected_setting_idx >= len(self.save_slots): self.selected_setting_idx = max(0, len(self.save_slots)-1)
                            elif event.key == pygame.K_x:
                                for s in self.save_slots:
                                    self.logic.save_manager.delete_save(s['filename'])
                                self.save_slots = self.logic.save_manager.get_save_slots()[:5]
                                self.selected_setting_idx = 0
                    continue

                # --- OYUN İÇİ DİĞER KONTROLLER (Sadece menü kapalıyken) ---
                if not self.show_settings:
                    if event.key in (pygame.K_TAB, pygame.K_i) and self.logic.state == "PLAYING":
                        # Craft penceresi açıkken TAB de onu kapatmalı (P4)
                        if self.show_craft_window:
                            self.show_craft_window = False
                            self.crafting_target = None
                            self.craft_error_msg = ""
                        else:
                            self.show_inventory = not self.show_inventory
                    if event.key == pygame.K_c and self.logic.state == "PLAYING" and not self.show_inventory:
                        self.show_stats_panel = not self.show_stats_panel
                    if event.key == pygame.K_f:
                        self._toggle_auto_sell(p)
                    if event.key == pygame.K_z:
                        p.auto_attack = not p.auto_attack
                    # Envanter/craft açıkken oyun duruyor (logic.update atlanıyor);
                    # yetenek tuşları burada da kilitli olmalı, yoksa yetenek
                    # harcanıp cooldown'a giriyordu.
                    modal_open = self.show_inventory or self.show_craft_window
                    if event.key == pygame.K_q and not modal_open:
                        # Efekt yalnız yetenek gerçekten kullanıldıysa (cooldown
                        # bitmişse) oynatılır: use_artifact sessizce dönebiliyor
                        art_ready = (p.inv_manager.equipped.get("artifact")
                                     and getattr(p, "artifact_cooldown", 0) <= 0
                                     and not p.is_silenced)
                        p.use_artifact(self.logic)
                        if art_ready:
                            self._cast_fx(p, "artifact")
                    if event.key == pygame.K_r and not modal_open:
                        self._use_r_ability(p)
                    if event.key == pygame.K_SPACE and not modal_open:
                        if p.dash():
                            self._cast_fx(p, "dash")

        # --- 2. AYARLAR MENÜSÜ FARE KONTROLÜ (MOUSE) ---
        settings_was_open = self.show_settings
        if settings_was_open:
            panel = self._pause_panel_rect()
            if mouse_clicked and not panel.collidepoint(mouse_pos):
                self.show_settings = False

            # Satır rect'leri çizimle aynı kaynaktan (_pause_rows)
            rows = self._pause_rows()
            if self.setting_tab == "main":
                for i, opt_rect in enumerate(rows):
                    if opt_rect.collidepoint(mouse_pos):
                        self.selected_setting_idx = i
                        if mouse_clicked:
                            if i == self.SOUND_ROW:
                                # Ses satırı bir kaydırıcı gibi: sol yarı (<)
                                # AZALTIR, sağ yarı (>) ARTIRIR. Eskiden tıklama
                                # yalnız artırıyordu (sesi kısmak imkânsızdı).
                                self.adjust_volume(
                                    -self.VOLUME_STEP if mouse_pos[0] < opt_rect.centerx
                                    else self.VOLUME_STEP)
                            else:
                                self._trigger_setting_action(i)
            elif self.setting_tab == "save":
                for i, opt_rect in enumerate(rows):
                    if opt_rect.collidepoint(mouse_pos):
                        self.selected_setting_idx = i
                        if mouse_clicked:
                            if i == 0:
                                name = f"save_{len(self.logic.save_manager.get_save_slots()) + 1}"
                                self.logic.save_manager.save_game(self.logic, name)
                            else: self.logic.save_manager.save_game(self.logic, "last_save")
                            self.setting_tab = "main"
            elif self.setting_tab == "load":
                for i, opt_rect in enumerate(rows):
                    if opt_rect.collidepoint(mouse_pos):
                        self.selected_setting_idx = i
                        if mouse_clicked:
                            self.logic.save_manager.load_game(self.logic, self.save_slots[i]['filename'])
                            self.show_settings = False

            # Modal arkasındaki kart veya oyun sonu butonlarına aynı tıklamanın
            # ulaşmasını engelle.
            return

        if (
            mouse_clicked
            and not self.show_inventory
            and self.logic.state == "PLAYING"
            and self.stats_button_rect.collidepoint(mouse_pos)
        ):
            self.show_stats_panel = not self.show_stats_panel
            return

        # --- 3. ENVANTER FARE KONTROLÜ (Yüksekliklerden bağımsız) ---
        if self.show_inventory and (mouse_clicked or mouse_rclicked):
            if mouse_rclicked:
                self._handle_inventory_mouse(p, mouse_pos, right_click=True)
            if mouse_clicked:
                self._handle_inventory_mouse(p, mouse_pos)
            return
            
        # Ekran bir kez çizilmeden bu ekranların tıklaması işlenmez
        if state_entered_now:
            return

        # --- 4. GAME OVER FARE KONTROLÜ ---
        if self.logic.state == "GAMEOVER" and mouse_clicked:
            self._handle_game_over_mouse(mouse_pos)

        # --- 5. KART VE EVRİM SEÇİM FARE KONTROLÜ ---
        if self.logic.state == "CARD_SELECT" and mouse_clicked:
            if hasattr(self, 'card_rects'):
                # Bayat rect'ler pending_cards'tan uzun olabiliyordu -> IndexError
                for i, rect in enumerate(self.card_rects[:len(self.logic.pending_cards)]):
                    if rect.collidepoint(mouse_pos):
                        card = self.logic.pending_cards[i]
                        self.logic.card_system.apply_card(card["id"], p)
                        # Görev takibi burada; card_system.apply_card save
                        # yüklemesinde de çağrılıyor (logic/save_manager.py),
                        # oraya konulsa her yüklemede sahte ilerleme olurdu.
                        self.logic.track_quest("pick_cards", 1)
                        self.logic.state = "PLAYING"
                        self.logic.pending_cards = []
                        break
                        
            if hasattr(self, 'card_skip_rect') and self.card_skip_rect.collidepoint(mouse_pos):
                # F9: ham "level += 1" xp_to_next_level'i güncellemiyordu (XP
                # eğrisi desenkron), canı tazelemiyor ve Mutasyon kartını
                # tetiklemiyordu. grant_free_level skill_point'i de kendisi
                # verir; buradaki elle artırım kaldırıldı (çift sayım olurdu).
                p.grant_free_level()
                self.logic.state = "PLAYING"
                self.logic.pending_cards = []
            
            if hasattr(self, 'card_reroll_rect') and self.card_reroll_rect.collidepoint(mouse_pos):
                if getattr(self.logic, 'card_rerolls', 0) > 0:
                    self.logic.card_rerolls -= 1
                    _pc = getattr(p, "base_class_id", None)
                    cards = self.logic.card_system.offer_cards(player_class=_pc)
                    if cards:
                        self.logic.pending_cards = cards
                        
        if self.logic.state == "EVOLUTION_SELECT" and mouse_clicked:
            # Hem kartın kendisi hem SEÇ butonu tıklanabilir (buton eskiden
            # çizilip hiçbir tıklama testine girmiyordu)
            for rect, evo_id in (list(getattr(self, 'evo_btn_rects', []))
                                 + list(getattr(self, 'evo_rects', []))):
                if rect.collidepoint(mouse_pos):
                    p.apply_evolution(evo_id)
                    self.logic.state = "PLAYING"
                    break

    def _get_sweep_surface(self, w, h):
        """Süpürme efekti için yeniden kullanılan yüzey (yalnız gereken kadar
        temizlenir; tam ekran fill() maliyeti kalktı)."""
        surf = self._sweep_surface
        if surf.get_width() < w or surf.get_height() < h:
            surf = pygame.Surface((max(w, surf.get_width()),
                                   max(h, surf.get_height())), pygame.SRCALPHA)
            self._sweep_surface = surf
        surf.fill((0, 0, 0, 0), pygame.Rect(0, 0, w, h))
        return surf

    def _handle_game_over_mouse(self, pos):
        # "Yeniden Başla" butonu (çizimde saklanan rect kullanılır)
        restart_rect = getattr(self, 'game_over_restart_rect', None) or \
            pygame.Rect(self.width // 2 - 200, self.height // 2 + 80, 400, 60)

        if restart_rect.collidepoint(pos):
            self.manager.change_scene("MainMenu") # New Game için geri at


    SOUND_ROW = 0       # ayarlar listesindeki ses satırının indeksi
    VOLUME_STEP = 10    # ok tuşu / tıklama başına yüzde adımı

    def adjust_volume(self, delta):
        """Sesi yüzde olarak değiştirir, kaydeder ve örnek ses çalar."""
        import audio
        vol = max(0, min(100, audio.get_volume() + delta))
        audio.set_volume(vol)
        self.logic.settings['sound'] = vol
        self.manager.global_settings['sound'] = vol
        self.manager.save_settings()
        if vol > 0:
            audio.play('ui_click')      # yeni seviyeyi duyarak ayarla

    def _trigger_setting_action(self, idx):
        if idx == self.SOUND_ROW:
            # Tıklama sesi artırır; sıfıra gelince başa döner (tek tuşla
            # gezinilebilir olsun, ok tuşları da ayrıca çalışıyor)
            import audio
            self.adjust_volume(self.VOLUME_STEP if audio.get_volume() < 100
                               else -100)
        elif idx == 1:
            self.logic.settings['shake'] = not self.logic.settings['shake']
            self.manager.global_settings['shake'] = self.logic.settings['shake']
            self.manager.save_settings()
        elif idx == 2:
            self.manager.cycle_display_mode()
        elif idx == 3:
            self.logic.cheat_mode = not self.logic.cheat_mode
            status = "AÇIK" if self.logic.cheat_mode else "KAPALI"
            self.logic.add_event("damage_text", self.width//2, self.height//2, value=f"HİLE MODU: {status}", color=(241, 196, 15), timer=1.5)
        elif idx == 4: self.setting_tab = "save"; self.selected_setting_idx = 0
        elif idx == 5:
            self.save_slots = self.logic.save_manager.get_save_slots()[:5]
            self.setting_tab = "load"; self.selected_setting_idx = 0
        elif idx == 6:
            self.logic.save_manager.save_game(self.logic, "last_save")
            self.manager.change_scene("MainMenu")
        elif idx == 7: self.manager.change_scene("MainMenu")
        elif idx == 8: self.show_settings = False

    def _toggle_auto_sell(self, p):
        modes = ["KAPALI", "BEYAZ", "MAVİ", "SARI", "TÜMÜ"]
        p.auto_sell_mode = (getattr(p, 'auto_sell_mode', 0) + 1) % 5
        m_str = modes[p.auto_sell_mode]
        self.logic.add_event("damage_text", p.x, p.y-80, value=f"OTO-SATIŞ: {m_str}", color=(241, 196, 15), timer=1.0)

    def _use_r_ability(self, p):
        """R tuşu: sınıfa göre yetenek. Bloodwalker kan emer, Mühendis taret kurar."""
        # class_name evrimle değişir; kalıcı kimlik class_id'dir (Bloodwalker Q evrim sonrası da çalışsın)
        if getattr(p, 'class_id', '') == "bloodwalker" and hasattr(p.specialization, 'activate_blood_absorb'):
            if p.specialization.activate_blood_absorb(p):
                self.logic.add_event("damage_text", p.x, p.y - 60, value="KAN EMME!", color=(255, 50, 50), timer=1.0)
                self._cast_fx(p, "blood_absorb")
            return

        # Mühendis: taret kurma yeteneği (eskiden saldırı tuşuna bağlıydı ve
        # taret kiti takılıyken oyuncunun hiç hasar vermesini engelliyordu)
        if p.can_place_turret():
            if p.try_place_turret(self.logic):
                self.logic.add_event("damage_text", p.x, p.y - 60,
                                     value="TARET KURULDU!", color=(120, 200, 255), timer=0.9)
        elif p.is_engineer():
            left = max(0.0, p.get_turret_cooldown() - getattr(p, 'turret_recharge', 0))
            self.logic.add_event("damage_text", p.x, p.y - 60,
                                 value=f"TARET DOLUYOR: {left:.1f}s",
                                 color=(160, 160, 170), timer=0.6)

    def _handle_inventory_mouse(self, p, pos, right_click=False):
        # 0. SAĞ TIK: yalnızca kuşanılan eşyayı çıkarır (etiket "SAĞ TIKLA ÇIKAR"
        # diyordu ama çıkarma sol tıka bağlıydı; tooltip okurken eşya düşüyordu)
        if right_click:
            if self.show_craft_window or self.active_tab != "inventory":
                return
            self._apply_inventory_layout()
            for row in self.equip_rows:
                if row.rect.collidepoint(pos) and row.item:
                    p.inv_manager.unequip(row.slot_type)
                    return
            return

        # 1. CRAFTİNG PENCERESİ AÇIKSA (Öncelikli)
        if self.show_craft_window:
            # Rect'ler çizimle AYNI kaynaktan (_craft_layout)
            L = self._craft_layout()

            # Kapatma Butonu
            if L["close"].collidepoint(pos):
                self.show_craft_window = False
                return

            # ORB SATIN ALMA (Dükkan - Sağ)
            market_list = self.logic.orb_market
            offset_m = self.orb_market_page * self.MARKET_ROWS_PER_PAGE
            for i in range(min(self.MARKET_ROWS_PER_PAGE, len(market_list) - offset_m)):
                actual_idx = offset_m + i
                orb = market_list[actual_idx]
                buy_btn = L["mkt_buy"][i]
                if buy_btn.collidepoint(pos):
                    if p.gold >= orb['price']:
                        if p.add_item(orb.copy()):
                            p.gold -= orb['price']
                            self.logic.track_quest("spend_gold", orb['price'])
                            self.logic.add_event("damage_text", p.x, p.y-40, value="Satın Alındı!", color=(46, 204, 113))
                    return

            # ORB KULLANMA (Envanterdeki Orblar - Sol; çizimde saklanan rect'ler)
            orbs_in_inv = [x for x in p.inventory if x.get('type') == 'orb']
            for actual_idx, use_btn in getattr(self, 'craft_orb_use_rects', []):
                if actual_idx >= len(orbs_in_inv):
                    continue
                orb = orbs_in_inv[actual_idx]
                if use_btn.collidepoint(pos):
                    # Orb bas!
                    err = self.logic.item_system.apply_orb(self.crafting_target, orb['orb_id'])
                    if err:
                        self.craft_error_msg = err
                        self.craft_error_timer = 2.0
                    else:
                        # Başarılı: Orbu tüket
                        orb['stack'] = orb.get('stack', 1) - 1
                        if orb['stack'] <= 0:
                            p.inventory.remove(orb)
                        p.inv_manager.recalculate_stats()
                        self.logic.add_event("damage_text", p.x, p.y-40, value="Craft Başarılı!", color=(46, 204, 113))
                    return

            # SAYFALAMA KONTROLLERİ (CRAFT)
            orb_pages = self.ORB_ROWS_PER_PAGE
            mkt_pages = self.MARKET_ROWS_PER_PAGE
            if L["orb_prev"].collidepoint(pos) and self.orb_inv_page > 0: self.orb_inv_page -= 1; return
            if L["orb_next"].collidepoint(pos) and (self.orb_inv_page + 1) * orb_pages < len(orbs_in_inv): self.orb_inv_page += 1; return
            if L["mkt_prev"].collidepoint(pos) and self.orb_market_page > 0: self.orb_market_page -= 1; return
            if L["mkt_next"].collidepoint(pos) and (self.orb_market_page + 1) * mkt_pages < len(market_list): self.orb_market_page += 1; return

            # GERİ AL (Hedef Eşyayı Envantere Çek)
            take_back_btn = L["take_back"]
            if take_back_btn.collidepoint(pos):
                # Craft penceresi acilirken esya envanterden CIKARILMIYOR;
                # burada tekrar add_item cagirmak esyayi cogaltiyordu (H6)
                self.crafting_target = None
                self.show_craft_window = False
                self.craft_error_msg = ""
                return
            return # Craft penceresi dışındakileri blockla

        # 2. ANA TABLAR
        for btn in self.tab_buttons:
            if btn.rect.collidepoint(pos):
                # Yetenek ağacına her girişte görünümü fit'e sıfırla
                if btn.tab_id == "skills":
                    self._tree_view = None
                self.active_tab = btn.tab_id
                return

        # 3. SAVAŞA DÖN / ÇIKIŞ
        if self.exit_btn_rect.collidepoint(pos):
            self.show_inventory = False
            return

        # 4. SEKME İÇERİĞİ
        if self.active_tab == "inventory":
            # Hitbox'lar çizimle aynı kaynaktan konumlansın
            self._apply_inventory_layout()

            # --- FİLTRE TIKLAMALARI ---
            rarity_count = len(self.rarity_filters)
            for i, rect in enumerate(self.filter_rects):
                if rect.collidepoint(pos):
                    if i < rarity_count: # Rarity
                        self.inv_filter_rarity = self.rarity_filters[i]
                    else: # Type
                        self.inv_filter_type = self.type_filters[i - rarity_count]
                    self.inventory_page = 0
                    return
            
            # --- ORB GİZLEME TIKLAMASI ---
            if self.orb_toggle_rect.collidepoint(pos):
                self.hide_orbs = not self.hide_orbs
                self.inventory_page = 0
                return

            # --- TOPLU İŞLEM TIKLAMALARI (SATIŞ & TÜKETİM) ---
            for i, rect in enumerate(self.mass_sell_rects):
                if rect.collidepoint(pos):
                    btn = self.mass_sell_btns[i]
                    if btn.get('action') == "consume_essences":
                        count = p.consume_all_essences()
                        if count > 0:
                            self.logic.add_event("damage_text", p.x, p.y-100, value=f"{count} Öz Tüketildi!", color=(155, 89, 182))
                    else:
                        count, gold = p.inv_manager.mass_sell(btn['rarity'])
                        if count > 0:
                            self.logic.add_event("damage_text", p.x, p.y-100, value=f"{count} Eşya Satıldı! (+{gold} G)", color=(46, 204, 113))
                    return

            # Filtrelenmiş Liste (Hangi eşyaya tıklandığını bulmak için)
            filtered_inv = self._filtered_inventory(p)

            # Sayfalama Kontrolü
            if self.inv_prev_rect.collidepoint(pos) and self.inventory_page > 0:
                self.inventory_page -= 1
                return
            if self.inv_next_rect.collidepoint(pos) and (self.inventory_page + 1) * 12 < len(filtered_inv):
                self.inventory_page += 1
                return

            # Kuşanılanlar: çıkarma SAĞ tıkla (yukarıdaki right_click bloğu).
            # Sol tık yalnızca tooltip okumak içindir, eşyayı düşürmez.

            # Çanta Butonları (Sayfa Ofsetli - Filtreleme Destekli)
            offset = self.inventory_page * 12
            for card in self.bp_cards:
                actual_idx = offset + card.idx
                if actual_idx < len(filtered_inv):
                    target_item = filtered_inv[actual_idx]
                    
                    # Orijinal listedeki gerçek indeksi bul
                    orig_idx = -1
                    for idx, oi in enumerate(p.inventory):
                        if oi is target_item:
                            orig_idx = idx
                            break
                    if orig_idx == -1: continue

                    # KULLAN / TÜKET
                    if card.use_rect.collidepoint(pos):
                        if target_item.get('type') == 'essence':
                            # ÖZ TÜKETME
                            if p.consume_essence(target_item['essence_type'], target_item['val']):
                                p.inventory.pop(orig_idx)
                                self.logic.add_event("damage_text", p.x, p.y-60, value="ÖZ TÜKETİLDİ!", color=(155, 89, 182))
                        else:
                            # NORMAL EKİPMAN — önce equip dene; orb gibi slotu
                            # olmayan eşyalarda equip False döner ve eşya
                            # envanterden silinmemelidir (H5)
                            if p.inv_manager.equip(target_item):
                                p.inventory.pop(orig_idx)
                        return
                    # SAT
                    elif card.sell_rect.collidepoint(pos):
                        p.inv_manager.sell_item(orig_idx)
                        return
                    # CRAFT
                    elif target_item.get('type') in ['weapon', 'helmet', 'chest', 'amulet', 'pet', 'artifact'] and card.craft_rect.collidepoint(pos):
                        self.show_craft_window = True
                        self.orb_inv_page = 0
                        self.orb_market_page = 0
                        self.crafting_target = target_item
                        self.craft_error_msg = ""
                        return

        elif self.active_tab == "skills":
            # YETENEK AĞACI: SIFIRLA tıklamada işlenir; düğüm tahsisi ise
            # sürükleme(pan) ayrımı için mouse-UP'ta yapılır (event döngüsü,
            # _tree_click_node). Böylece kaydırma yanlışlıkla düğüm almaz.
            if self.reset_btn_rect.collidepoint(pos):
                if self.reset_skill_tree(p):
                    self.logic.add_event("damage_text", p.x, p.y-60, value="Yetenek Ağacı Sıfırlandı!", color=(46, 204, 113))
                else:
                    self.logic.add_event("damage_text", p.x, p.y-60, value="Yetersiz Altın!", color=(231, 76, 60))
                return

        elif self.active_tab == "ascendancy":
            from logic.ascendancy import Ascendancy
            if getattr(self, 'asc_reset_rect', None) and self.asc_reset_rect.collidepoint(pos):
                wave_level = self.logic.wave.get("level", 1)
                cost = 1500 + max(0, (wave_level - 1) * 300)
                if p.gold >= cost:
                    p.gold -= cost
                    Ascendancy.refund_all(p)
                    self.logic.add_event("damage_text", p.x, p.y-60, value="Yükseliş Sıfırlandı!", color=(46, 204, 113))
                else:
                    self.logic.add_event("damage_text", p.x, p.y-60, value="Yetersiz Altın!", color=(231, 76, 60))
                return
            for nid, rect in getattr(self, 'ascendancy_node_hit', []):
                if rect.collidepoint(pos):
                    ok, msg = Ascendancy.allocate(p, nid)
                    self.logic.add_event("damage_text", p.x, p.y-60, value=msg,
                                         color=(241, 196, 15) if ok else (231, 76, 60))
                    return

        elif self.active_tab == "hero":
            diff_names = ["Normal", "Hard", "Very Hard", "Impossible"]
            for i, rect in enumerate(self._diff_button_rects()):
                if rect.collidepoint(pos):
                    self.logic.update_difficulty(diff_names[i])
                    return

        elif self.active_tab == "market":
            # Pazar Sekmeleri
            for btn in self.market_tab_btns:
                if btn.rect.collidepoint(pos):
                    self.market_tab = btn.tab_id
                    self.market_page = 0 # Sekme değişince sayfayı sıfırla
                    return
            
            # Pazar Sayfalama Kontrolü
            market_list = self.logic.market_inventory if self.market_tab == "items" else self.logic.orb_market
            if self.mkt_prev_rect.collidepoint(pos) and self.market_page > 0:
                self.market_page -= 1
                return
            if self.mkt_next_rect.collidepoint(pos) and (self.market_page + 1) * 12 < len(market_list):
                self.market_page += 1
                return

            # Yenile
            if self.market_tab == "items" and self.refresh_btn_rect.collidepoint(pos):
                wave_level = self.logic.wave.get("level", 1)
                cost = 500 + max(0, (wave_level - 1) * 400)
                if p.gold >= cost:
                    p.gold -= cost
                    self.logic.track_quest("spend_gold", cost)
                    self.logic.refresh_market()
                    self.market_page = 0
            
            # Satın Al (Sayfa Ofsetli)
            offset = self.market_page * 12
            for i, card in enumerate(self.market_cards):
                actual_idx = offset + i
                if actual_idx < len(market_list):
                    if card.buy_rect.collidepoint(pos):
                        self.logic.buy_item(actual_idx, self.market_tab)
            return
            
        elif self.active_tab == "aura":
            if self.update_aura_clicks(pos, p): return
                        
    def handle_mouse_wheel(self, y):
        self.zoom_level = max(self.min_zoom, min(self.max_zoom, self.zoom_level + y * 0.1))

    def draw(self):
        # --- ZOOM & CAMERA SETUP ---
        internal_w = int(self.width / self.zoom_level)
        internal_h = int(self.height / self.zoom_level)
        
        # Zoom sabitken aynı büyük yüzeyi her kare yeniden ayırma.
        surface_size = (internal_w, internal_h)
        if self._world_surface is None or self._world_surface_size != surface_size:
            self._world_surface = pygame.Surface(surface_size).convert()
            self._world_surface_size = surface_size
        world_surf = self._world_surface
        
        cam_off_x, cam_off_y = 0, 0
        if self.logic.shake_timer > 0:
            s = self.logic.shake_intensity
            cam_off_x = random.randint(-int(s), int(s))
            cam_off_y = random.randint(-int(s), int(s))
            
        final_cam_x = self.camera_x + cam_off_x
        final_cam_y = self.camera_y + cam_off_y
        
        # 1. Zemini çiz (World Surface'a)
        self.draw_floor_to_surf(world_surf, final_cam_x, final_cam_y, internal_w, internal_h)
        
        def visible(obj, margin=100):
            return (
                final_cam_x - margin <= obj.x <= final_cam_x + internal_w + margin
                and final_cam_y - margin <= obj.y <= final_cam_y + internal_h + margin
            )

        # 2. Boss Mermileri
        self.logic.projectile_pool.draw(world_surf, final_cam_x, final_cam_y)
        
        # 3. Objeleri çiz
        for it in self.logic.items_on_ground:
            if visible(it, 80): it.draw(world_surf, final_cam_x, final_cam_y)
        for h in self.logic.hazards:
            if visible(h, h.radius): h.draw(world_surf, final_cam_x, final_cam_y)
        for cl in getattr(self.logic, 'clouds', []):
            if visible(cl, cl.radius): cl.draw(world_surf, final_cam_x, final_cam_y)
        for m in getattr(self.logic, 'minions', []):
            if visible(m, 60): m.draw(world_surf, final_cam_x, final_cam_y)
        for t in self.logic.turrets:
            if visible(t, 80): t.draw(world_surf, final_cam_x, final_cam_y)
        for pr in self.logic.projectiles:
            if visible(pr, 30): pr.draw(world_surf, final_cam_x, final_cam_y)
        for e in self.logic.enemies:
            if visible(e, max(80, e.radius * 4)): e.draw(world_surf, final_cam_x, final_cam_y)
        
        # Partiküller
        # VFX katmanı: parçacıklar ve efektler buraya çizilir, kare sonunda
        # tek seferde toplamalı (additive) basılır. Bkz. vfx.begin_frame.
        fx = vfx.begin_frame(world_surf.get_size(), world_surf)
        for part in getattr(self.logic, 'particles', []):
            if not (
                final_cam_x - 20 <= part['x'] <= final_cam_x + internal_w + 20
                and final_cam_y - 20 <= part['y'] <= final_cam_y + internal_h + 20
            ):
                continue
            px, py = part['x'] - final_cam_x, part['y'] - final_cam_y
            vfx.draw_particle(fx, part, px, py)
            
        # Görsel Efektler (Events)
        for ev in self.logic.events:
            dx, dy = ev['x'] - final_cam_x, ev['y'] - final_cam_y
            if dx < -200 or dy < -200 or dx > internal_w + 200 or dy > internal_h + 200:
                continue
            if ev['type'] == 'damage_text':
                v_str = str(int(ev['value'])) if isinstance(ev['value'], (int, float)) else str(ev['value'])
                txt = self.font_sub.render(v_str, True, ev.get('color', (255, 255, 255)))
                world_surf.blit(txt, (dx, dy))
            elif ev['type'] == 'slash':
                vfx.draw_slash(fx, ev, dx, dy)
            elif ev['type'] == 'sweep':
                vfx.draw_sweep(fx, ev, dx, dy, self._get_sweep_surface)
            elif ev['type'] == 'explosion':
                vfx.draw_explosion(fx, ev, dx, dy)
            elif ev['type'] == 'shockwave':
                vfx.draw_shockwave(fx, ev, dx, dy)
            elif ev['type'] == 'fx':
                # Genel dokulu efekt (isabet, kritik, dodge, şifa, toplama...)
                vfx.draw_fx(fx, ev, dx, dy)

        # Efekt katmanını dünyaya bas (kare başına tek toplamalı işlem)
        vfx.end_frame(world_surf)

        # Oyuncuyu çiz
        p = self.logic.players[self.logic.local_player_id]
        p.draw(world_surf, final_cam_x, final_cam_y)
        
        # --- WORLD SURF'Ü EKRANA BAS (ZOOM) ---
        final_scaled = pygame.transform.scale(world_surf, (self.width, self.height))
        self.screen.blit(final_scaled, (0, 0))

        # 4. Gece/Gündüz Döngüsü
        is_night = (self.logic.wave["level"] % 2 == 0)
        if is_night:
            self._overlay_surface.fill((0, 0, 20, 120))  # Yarı saydam mavi-siyah
            self.screen.blit(self._overlay_surface, (0, 0))

        # --- HUD & UI (Zoomsuz, direkt ekrana) ---
        if p.level_up_timer > 0:
            lvl_text = self.font_main.render("SEVİYE ATLADIN!", True, (241, 196, 15))
            self.screen.blit(lvl_text, (self.width // 2 - lvl_text.get_width() // 2, 200))
            
        # HUD: SALDIRI DURUMU
        mode_text = "OTOMATİK" if p.auto_attack else "MANUEL"
        atk_surf = self.font_sub.render(f"SALDIRI: {mode_text} (Z)", True, (46, 204, 113) if p.auto_attack else (255, 255, 255))
        self.screen.blit(atk_surf, (20, 150))
        
        # HUD: OTO-SATIŞ DURUMU
        sm = getattr(p, 'auto_sell_mode', 0)
        sell_text = ["KAPALI", "BEYAZ", "MAVİ", "SARI", "TÜMÜ"][sm]
        sell_surf = self.font_sub.render(f"OTO-SATIŞ (F): {sell_text}", True, (241, 196, 15) if sm > 0 else (150, 150, 150))
        self.screen.blit(sell_surf, (20, 180))
        
        # Artifact (tema plakası + gotik bar; eskiden çıplak rect'ti ve
        # draw.rect'e verilen RGBA'nın alfası sessizce yok sayılıyordu)
        import ui_theme
        import ui_nineslice as n9
        art = p.inv_manager.equipped.get("artifact")
        # y=226: üstteki OTO-SATIŞ satırı 32pt fontla ~212'ye kadar iniyor,
        # plakanın üst süsü 215'te onun üstüne biniyordu.
        art_rect = pygame.Rect(20, 226, 250, 46)
        if art:
            art_name, max_cd = art.get("name", "Artifact").upper(), max(1, art.get("cooldown", 30))
            ready = p.artifact_cooldown <= 0
            ui_theme.draw_plate(self.screen, art_rect, "hover" if ready else "normal",
                                ui_theme.COLORS["arcane"])
            txt = f"{art_name} (HAZIR)" if ready else f"{art_name} ({int(p.artifact_cooldown)}s)"
            clr = ui_theme.TEXT_COL if ready else (176, 170, 158)
            art_surf = render_fit(txt, 19, clr, art_rect.width - 40, bold=ready)
            self.screen.blit(art_surf, (art_rect.x + 20, art_rect.y + 5))

            bar = pygame.Rect(art_rect.x + 20, art_rect.bottom - 15, art_rect.width - 40, 10)
            ratio = 1.0 if ready else 1.0 - (p.artifact_cooldown / max_cd)
            if not n9.draw_bar(self.screen, "bar_frame.png", bar,
                               "bar_fill_green.png" if ready else "bar_fill_mana.png", ratio):
                pygame.draw.rect(self.screen, ui_theme.METAL_LO, bar, border_radius=3)
                pygame.draw.rect(self.screen, ui_theme.readable(ui_theme.COLORS["arcane"]),
                                 (bar.x, bar.y, int(bar.width * ratio), bar.height), border_radius=3)
        else:
            empty_rect = pygame.Rect(20, 226, 250, 34)
            ui_theme.draw_plate(self.screen, empty_rect, "disabled")
            art_surf = render_fit("ARTIFACT: EKSİK", 18, (140, 134, 124), empty_rect.width - 40)
            self.screen.blit(art_surf, art_surf.get_rect(center=empty_rect.center))


        # 4. Kan Ayı Filtresi
        if self.logic.wave.get("is_blood_moon"):
            self.screen.blit(self.blood_moon_surf, (0, 0))

        # Üst-orta HUD bandını tahsis et (WAVE / boss / dalga olayı / combo
        # hepsi buraya çiziliyor ve sabit y'lerle üst üste biniyorlardı)
        self._layout_top_hud()

        # 🟢 KILL STREAK HUD
        # 4. Kill Streak (Combo) - Minimalist Tasarım
        if self.logic.kill_streak > 1:
            import ui_theme
            streak = self.logic.kill_streak
            key = "gold" if streak < 20 else "blood"

            txt = ui_theme.render_title(f"COMBO: {streak}", 26,
                                        ui_theme.readable(ui_theme.COLORS[key]))
            txt_rect = txt.get_rect(midtop=(self.width // 2, self._hud_combo_y))
            self.screen.blit(txt, txt_rect)

            # Streak Zaman Çubuğu (ortak dünya barı yardımcısı)
            bar_w = 120
            ratio = max(0, min(1.0, self.logic.streak_timer / 3.5))
            ui_theme.draw_world_bar(
                self.screen,
                pygame.Rect(self.width // 2 - bar_w // 2, txt_rect.bottom + 4, bar_w, 5),
                ratio, key)

        # 5. Boss HP Barı (GDD 31)
        self.draw_boss_healthbar()

        # 6. HUD (Arayüz)
        self.draw_hud()
        
        # 7. Envanter Overlay (TAB veya I)
        if self.show_inventory:
            self.draw_inventory()
            
        # 8. Ayarlar Menüsü (ESC basıldığında)
        if self.show_settings:
            self.draw_settings_menu()

        # 9. Crafting Penceresi (En Üstte)
        if self.show_craft_window:
            self.draw_craft_window()
            
        # 🟢 10. TOOLTIPS (Arayüzün En Üstünde Görünmeli)
        if self.show_inventory or self.show_craft_window:
            self.handle_tooltips(self.logic.players[self.logic.local_player_id])
            
        # 11. Game Over Ekranı
        if self.logic.state == "GAMEOVER":
            self.draw_game_over_screen()
        elif self.logic.state == "CARD_SELECT":
            self.draw_card_select_screen()
        elif self.logic.state == "EVOLUTION_SELECT":
            self.draw_evolution_select_screen()


    # --- Duraklatma menüsü geometrisi (çizim ve tıklama TEK kaynak) ---
    # Satır rect'leri hem draw_settings_menu hem update() tarafından buradan
    # alınır; iki yerde ayrı hesaplanınca hizalama sürekli kayıyordu.

    # Satır sırası _pause_labels() ile birebir aynı olmalı (0: SES)
    PAUSE_OPTION_COLORS = ["steel", "steel", "steel", "steel", "moss",
                           "night", "night", "ember", "blood"]

    def _pause_panel_rect(self):
        return pygame.Rect(self.width // 2 - 260, self.height // 2 - 290, 520, 580)

    def _pause_rows(self):
        """Aktif sekmedeki satır rect'lerini döndürür.

        Satır aralığı plaka yüksekliğinden 12px fazla: buton plakasının alt/üst
        kenarındaki mühür taşları bitişik satırlarda üst üste biniyordu.
        """
        panel = self._pause_panel_rect()
        if self.setting_tab == "main":
            # Satır sayısı sabit 8 yazılmıştı; ses satırı eklenince son satır
            # ("OYUNA GERİ DÖN") ne çiziliyor ne tıklanabiliyordu.
            return [pygame.Rect(panel.centerx - 210, panel.y + 104 + i * 50, 420, 40)
                    for i in range(len(self._pause_labels()))]
        if self.setting_tab == "save":
            return [pygame.Rect(panel.centerx - 210, panel.y + 170 + i * 80, 420, 56)
                    for i in range(2)]
        return [pygame.Rect(panel.centerx - 235, panel.y + 130 + i * 60, 470, 46)
                for i in range(len(self.save_slots[:5]))]

    def _pause_labels(self):
        """Aktif sekmedeki satır metinleri (main/save); load kendi çizer."""
        if self.setting_tab == "main":
            import audio
            vol = audio.get_volume()
            # Yüzdeyi çubukla da göster: sayı tek başına "ne kadar yüksek"
            # hissini vermiyor. NOT: '█' ve '·' arayüz fontunda YOK, kutu
            # olarak veya hiç çizilmiyordu — yalnızca ASCII kullanılıyor.
            bars = int(round(vol / 10))
            meter = "|" * bars + "." * (10 - bars)
            vol_txt = "[KAPALI]" if vol <= 0 else f"{meter}  %{vol}"
            if not audio.is_ready():
                vol_txt = "[SES YOK]"
            return [
                f"SES: {vol_txt}",
                f"EKRAN SARSINTISI: {'[AÇIK]' if self.logic.settings['shake'] else '[KAPALI]'}",
                f"EKRAN MODU: [{self.manager.get_display_mode_label()}]",
                f"HİLE MODU: {'[AÇIK]' if self.logic.cheat_mode else '[KAPALI]'}",
                "OYUNU KAYDET",
                "KAYITLI OYUNLAR",
                "KAYDET VE ANA MENÜYE DÖN",
                "ANA MENÜYE DÖN (Kaydetmeden)",
                "OYUNA GERİ DÖN",
            ]
        return ["YENİ KAYIT (FARKLI KAYDET)", "SON KAYDI GÜNCELLE"]

    def draw_settings_menu(self):
        import ui_theme

        self._overlay_surface.fill((0, 0, 0, 180))
        self.screen.blit(self._overlay_surface, (0, 0))

        panel = self._pause_panel_rect()
        ui_theme.draw_panel(self.screen, panel)

        titles = {"main": "DURAKLATILDI", "save": "KAYDET", "load": "KAYITLAR"}
        title = ui_theme.render_title(titles[self.setting_tab], 40)
        tx = panel.centerx - title.get_width() // 2
        self.screen.blit(title, (tx, panel.y + 26))
        crest = get_skull_crest(34)
        if crest is not None:
            cy = panel.y + 26 + title.get_height() // 2 - crest.get_height() // 2
            self.screen.blit(crest, (tx - crest.get_width() - 16, cy))
            self.screen.blit(crest, (tx + title.get_width() + 16, cy))

        rows = self._pause_rows()
        mouse_pos = pygame.mouse.get_pos()

        if self.setting_tab in ("main", "save"):
            labels = self._pause_labels()
            for i, (row, label) in enumerate(zip(rows, labels)):
                active = i == self.selected_setting_idx or row.collidepoint(mouse_pos)
                key = self.PAUSE_OPTION_COLORS[i] if self.setting_tab == "main" else "moss"
                ui_theme.draw_plate(self.screen, row,
                                    "hover" if active else "normal",
                                    ui_theme.COLORS[key])
                col = ui_theme.TEXT_COL if active else (176, 170, 158)
                txt = render_fit(label, 20, col, row.width - 60, bold=active)
                self.screen.blit(txt, txt.get_rect(center=row.center))
                # Ses satırında sol/sağ ok afordansı (tıklanabilir yarımlar)
                if self.setting_tab == "main" and i == self.SOUND_ROW:
                    lt = render_fit("<", 26, col, 28, bold=True)
                    gt = render_fit(">", 26, col, 28, bold=True)
                    self.screen.blit(lt, (row.x + 14, row.centery - lt.get_height() // 2))
                    self.screen.blit(gt, (row.right - 14 - gt.get_width(),
                                          row.centery - gt.get_height() // 2))
            return

        # --- load ---
        if not self.save_slots:
            info = render_fit("HENÜZ KAYIT YOK", 24, (150, 145, 135), panel.width - 60)
            self.screen.blit(info, info.get_rect(center=(panel.centerx, panel.centery)))
            return

        for i, (row, slot) in enumerate(zip(rows, self.save_slots[:5])):
            active = i == self.selected_setting_idx or row.collidepoint(mouse_pos)
            ui_theme.draw_plate(self.screen, row, "hover" if active else "normal",
                                ui_theme.COLORS["night"])
            col = ui_theme.TEXT_COL if active else (176, 170, 158)
            # 30px pay: plakanın uç kapakları/mühür taşları 26px insets içinde
            date_txt = render_fit(slot['date'], 15, (140, 134, 122), 130)
            slot_txt = f"SEVİYE {slot['level']}  •  DALGA {slot['wave']}  •  {slot['class'].upper()}"
            txt = render_fit(slot_txt, 19, col,
                             row.width - date_txt.get_width() - 76, bold=active)
            self.screen.blit(txt, (row.x + 30, row.centery - txt.get_height() // 2))
            self.screen.blit(date_txt, (row.right - date_txt.get_width() - 30,
                                        row.centery - date_txt.get_height() // 2))

        info_txt = render_fit("[DEL]: SİL  |  [X]: HEPSİNİ TEMİZLE", 18,
                              ui_theme.readable(ui_theme.COLORS["blood"]), panel.width - 60)
        self.screen.blit(info_txt, (panel.centerx - info_txt.get_width() // 2,
                                    panel.bottom - 44))

    def draw_floor_to_surf(self, surf, camera_x, camera_y, width, height):
        # Sadece ekranda görünen karoları çiz (Optimizasyon)
        start_x = int(camera_x // self.tile_size)
        start_y = int(camera_y // self.tile_size)
        end_x = int((camera_x + width) // self.tile_size) + 1
        end_y = int((camera_y + height) // self.tile_size) + 1
        
        # Biyom Rengini Çek
        biome_id = self.logic.wave.get("biome", "normal")
        floor_color = self.logic.BIOMES.get(biome_id, {}).get("color", self.floor_color_1)
        
        for tx in range(start_x, end_x):
            for ty in range(start_y, end_y):
                rect = (tx * self.tile_size - camera_x, ty * self.tile_size - camera_y, self.tile_size, self.tile_size)
                # Checkerboard kaldırıldı, tek renk zemin çiziliyor
                pygame.draw.rect(surf, floor_color, rect)
                pygame.draw.rect(surf, self.grid_line_color, rect, 1)

    def _draw_hud_bar(self, x, y, w, h, ratio, fill_asset, flat_color, label):
        """Gotik çerçeveli durum çubuğu; varlık yoksa eski düz çizime düşer."""
        import ui_nineslice as n9
        rect = pygame.Rect(x, y, w, h)
        if not n9.draw_bar(self.screen, "bar_frame.png", rect, fill_asset, ratio):
            pygame.draw.rect(self.screen, (30, 30, 45), rect, border_radius=6)
            pygame.draw.rect(self.screen, flat_color,
                             (x, y, int(w * max(0.0, min(1.0, ratio))), h),
                             border_radius=6)
        txt = self.font_desc.render(label, True, (255, 255, 255))
        self.screen.blit(txt, (x + w + 10, y + h // 2 - txt.get_height() // 2))

    def _layout_top_hud(self):
        """Üst-orta HUD bandını yukarıdan aşağıya tahsis eder.

        WAVE sayacı, boss adı+barı, dalga olayı şeridi ve combo sayacı hepsi
        ekranın üst ortasına sabit y'lerle çiziliyordu (20 / 55 / 74 / 80) ve
        boss varken hepsi üst üste biniyordu. Artık her biri sırayla yer alır.
        """
        y = 20
        self._hud_wave_y = y
        y += 34

        self._hud_boss = next((e for e in self.logic.enemies if e.type == "boss"), None)
        self._hud_phase_warning_y = None
        if self._hud_boss:
            self._hud_boss_name_y = y
            y += 32
            self._hud_boss_bar_y = y
            y += 34
            # Boss faz uyarısı (ör. "FIND SAFE ZONE!") — sabit ekran y'sinde
            # dururken boss'un kafa üstü barıyla çakışıyordu.
            self._hud_phase_warning_y = y + 22
            y += 48

        if self.logic.wave.get("event"):
            self._hud_event_y = y + 14
            y += 42

        self._hud_combo_y = y + 6

    def draw_minimap(self, p):
        """Sağ-alt köşede dairesel gotik mini harita: oyuncu merkezde (altın),
        düşmanlar kırmızı nokta, iri düşman/boss mor. Ekrana (HUD) çizilir."""
        R = 92
        cx, cy = self.width - R - 34, self.height - R - 40
        # Koyu taş zemin (yarı saydam daire)
        bg = pygame.Surface((R * 2 + 10, R * 2 + 10), pygame.SRCALPHA)
        pygame.draw.circle(bg, (16, 13, 18, 232), (R + 5, R + 5), R + 2)
        self.screen.blit(bg, (cx - R - 5, cy - R - 5))

        # Dünya -> minimap ölçeği (oyuncunun ~1000px çevresini gösterir)
        world_r = 1000.0
        scale = R / world_r
        inner = (R - 6) * (R - 6)
        for e in self.logic.enemies:
            if getattr(e, 'dead', False):
                continue
            dx = (e.x - p.x) * scale
            dy = (e.y - p.y) * scale
            if dx * dx + dy * dy > inner:
                continue
            big = getattr(e, 'radius', 12) >= 28
            col = (178, 78, 224) if big else (231, 76, 60)
            pygame.draw.circle(self.screen, col, (int(cx + dx), int(cy + dy)), 5 if big else 3)

        # Oyuncu (merkez, altın) + koyu kontur
        pygame.draw.circle(self.screen, (255, 214, 96), (cx, cy), 5)
        pygame.draw.circle(self.screen, (20, 16, 14), (cx, cy), 5, 1)

        # Gotik metal çerçeve halkaları
        pygame.draw.circle(self.screen, (24, 20, 22), (cx, cy), R + 4, 4)   # koyu kontur
        pygame.draw.circle(self.screen, (122, 126, 134), (cx, cy), R + 1, 3)  # metal
        pygame.draw.circle(self.screen, (156, 160, 168), (cx, cy), R - 1, 1)  # parlak iç kenar

        # Üstte kurukafa arması
        crest = get_skull_crest(30)
        if crest is not None:
            self.screen.blit(crest, (cx - crest.get_width() // 2,
                                     cy - R - crest.get_height() // 2 - 2))

    def draw_hud(self):
        import ui_theme
        p = self.logic.players[self.logic.local_player_id]
        self.draw_minimap(p)
        # Wave Bilgisi
        wave_surf = render_fit(f"WAVE: {self.logic.wave['level']}", 26,
                               ui_theme.readable(ui_theme.COLORS["gold"]), 300, bold=True)
        self.screen.blit(wave_surf, (self.width // 2 - wave_surf.get_width() // 2,
                                     self._hud_wave_y))

        # Aktif ÖZEL DALGA şeridi: kalan süre ve (yarışta) skor.
        # Özel dalganın kuralı SÜRE olduğu için sayaç görünmezse oyuncu neyi
        # beklediğini bilmiyordu — eskiden yalnızca başlangıçta afiş çıkıyordu.
        sp = self.logic.wave.get("special")
        if sp and self.logic.wave.get("special_timer", 0) > 0:
            left = self.logic.wave["special_timer"]
            label = f"🌟 {sp['name']} — {int(left)}s"
            if sp.get("type") == "kill_race":
                label += f"  •  {self.logic.wave.get('special_kills', 0)} öldürme"
            sp_txt = render_fit(label, 20,
                                ui_theme.readable(ui_theme.COLORS["arcane"]),
                                self.width // 2, bold=True)
            sp_rect = sp_txt.get_rect(center=(self.width // 2, self._hud_event_y))
            ui_theme.draw_plate(self.screen, sp_rect.inflate(48, 16), "hover",
                                ui_theme.COLORS["arcane"])
            self.screen.blit(sp_txt, sp_rect)

        # Aktif dalga olayı şeridi (dalga boyunca görünür kalır)
        evt = self.logic.wave.get("event")
        if evt and not sp:
            strip_txt = render_fit(evt["desc"], 18,
                                   ui_theme.readable(ui_theme.COLORS["gold"]),
                                   self.width // 2, bold=True)
            strip_rect = strip_txt.get_rect(center=(self.width // 2, self._hud_event_y))
            ui_theme.draw_plate(self.screen, strip_rect.inflate(48, 16), "normal",
                                ui_theme.COLORS["gold"])
            self.screen.blit(strip_txt, strip_rect)

        # Dalga başı büyük duyuru banner'ı (ekran ortası, sona doğru söner)
        announce_t = self.logic.wave.get("announce_timer", 0)
        lines = self.logic.wave.get("announce_lines") or []
        if announce_t > 0 and lines:
            line_surfs = []
            for i, line in enumerate(lines):
                color = (231, 76, 60) if i == 0 else (255, 165, 0)
                line_surfs.append(self.font_sub.render(line, True, color))
            bw = max(s.get_width() for s in line_surfs) + 80
            bh = sum(s.get_height() for s in line_surfs) + 30 + 8 * (len(line_surfs) - 1)
            banner = pygame.Surface((bw, bh), pygame.SRCALPHA)
            # Tema paneli (prosedürel ince metal çerçeve; banner geçici ve dar)
            ui_theme.draw_panel(banner, banner.get_rect(), fill=(16, 13, 20),
                                alpha=225, nineslice=False)
            ly = 15
            for s in line_surfs:
                banner.blit(s, (bw // 2 - s.get_width() // 2, ly))
                ly += s.get_height() + 8
            banner.set_alpha(int(255 * min(1.0, announce_t)))  # Son 1 saniyede fade-out
            self.screen.blit(banner, (self.width // 2 - bw // 2, self.height // 4 - bh // 2))
        
        # Altın ve XP
        gold_str = f"GOLD: {p.gold}"
        gold_surf = self.font_sub.render(gold_str, True, (241, 196, 15))
        self.screen.blit(gold_surf, (20, 20))
        
        level_str = f"LVL: {p.level}"
        level_surf = self.font_sub.render(level_str, True, (52, 152, 219))
        self.screen.blit(level_surf, (20, 60))
        
        # HP / ES / XP Barları (Sol Üst)
        # Yükseklik 24: gotik bar çerçevesinin üst/alt rayları ~5px, oluğa
        # 14px kalıyor. 12px'te oluk 2px'e düşüp dolgu görünmez oluyordu.
        BAR_W, BAR_H, BAR_GAP = 220, 24, 30
        hp_ratio = p.hp / max(1, p.max_hp)
        self._draw_hud_bar(20, 95, BAR_W, BAR_H, hp_ratio,
                           "bar_fill_hp.png", (231, 76, 60),
                           f"HP: {int(p.hp)}/{int(p.max_hp)}")

        y_offset = 95 + BAR_GAP
        if p.max_energy_shield > 0:
            es_ratio = p.energy_shield / max(1, p.max_energy_shield)
            self._draw_hud_bar(20, y_offset, BAR_W, BAR_H, es_ratio,
                               "bar_fill_shield.png", (52, 152, 219),
                               f"ES: {int(p.energy_shield)}/{int(p.max_energy_shield)}")
            y_offset += BAR_GAP

        xp_ratio = p.xp / p.xp_to_next_level
        self._draw_hud_bar(20, y_offset, BAR_W, BAR_H, xp_ratio,
                           "bar_fill_green.png", (46, 204, 113),
                           f"XP: {p.xp:.1f}/{p.xp_to_next_level}")
        
        # --- HUD: YETENEK ÇUBUĞU (tuş + bekleme) ---
        self.draw_ability_bar(p)

        # Anlık stat paneli düğmesi ve açılır görünümü (tema: banner buton).
        import ui_theme
        stats_hovered = self.stats_button_rect.collidepoint(pygame.mouse.get_pos())
        stats_label = "İSTATİSTİKLER [C] • AÇIK" if self.show_stats_panel else "İSTATİSTİKLER [C]"
        stats_state = "hover" if (stats_hovered or self.show_stats_panel) else "normal"
        surf, overhang = ui_theme.render_banner_button(
            self.stats_button_rect.width, self.stats_button_rect.height,
            stats_label, ui_theme.COLORS["night"], state=stats_state, skull=False)
        self.screen.blit(surf, (self.stats_button_rect.centerx - surf.get_width() // 2,
                                self.stats_button_rect.y - overhang))

        if self.show_stats_panel and self.logic.state == "PLAYING":
            self.draw_live_stats_panel(p)

    def get_abilities(self, p):
        """Oyuncunun kullanabildiği yetenekler: tuş, ad, bekleme durumu.

        HUD burayı çizer; sınıfa/ekipmana göre liste değişir, tuşlar
        update()'teki bağlarla birebir aynı tutulmalıdır.
        """
        abilities = [{
            "key": "SPACE", "name": "Atılma", "color": "night",
            "left": max(0.0, p.dash_timer), "total": p.dash_cooldown,
        }]

        art = p.inv_manager.equipped.get("artifact")
        if art:
            abilities.append({
                "key": "Q", "name": art.get("name", "Eser"), "color": "arcane",
                "left": max(0.0, getattr(p, "artifact_cooldown", 0)),
                "total": max(1, art.get("cooldown", 30)),
            })

        spec = getattr(p, "specialization", None)
        if getattr(p, "class_id", "") == "bloodwalker" and hasattr(spec, "activate_blood_absorb"):
            abilities.append({
                "key": "R", "name": "Kan Emme", "color": "blood",
                "left": max(0.0, getattr(spec, "blood_absorb_timer", 0)),
                "total": max(1.0, getattr(spec, "blood_absorb_cooldown", 20.0)),
                "active": getattr(spec, "blood_absorb_active", False),
            })
        elif p.is_engineer():
            # Taret şarjlı bir yetenek: en az bir şarj varsa "hazır" sayılır,
            # bekleme göstergesi dolmakta olan bir sonraki şarjı gösterir.
            charges = getattr(p, "turret_charges", 0)
            cd = p.get_turret_cooldown()
            abilities.append({
                "key": "R", "name": "Taret", "color": "night",
                "left": 0.0 if charges > 0 else max(0.0, cd - getattr(p, "turret_recharge", 0)),
                "total": cd,
                "charges": charges,
                "max_charges": p.get_turret_max_charges(),
            })
        return abilities

    def draw_ability_bar(self, p):
        """Yetenek slotlarını ekranın alt ortasına çizer."""
        import ui_theme
        abilities = self.get_abilities(p)
        if not abilities:
            return

        slot, gap, label_h = 58, 14, 20
        total_w = len(abilities) * slot + (len(abilities) - 1) * gap
        x0 = self.width // 2 - total_w // 2
        y = self.height - slot - label_h - 18

        for i, ab in enumerate(abilities):
            rect = pygame.Rect(x0 + i * (slot + gap), y, slot, slot)
            ready = ab["left"] <= 0
            col = ui_theme.COLORS[ab["color"]]

            ui_theme.draw_item_slot(self.screen, rect)
            # Hazır yetenek aksan rengiyle çerçevelenir, bekleyende sönük kalır
            tint = tuple(int(c * (0.55 if ready else 0.18)) for c in col)
            overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(overlay, tint + (200 if ready else 90,),
                             overlay.get_rect(), width=3, border_radius=3)
            self.screen.blit(overlay, rect.topleft)

            # Tuş harfi slotun ortasında
            key_col = ui_theme.TEXT_COL if ready else (140, 134, 124)
            key_txt = render_fit(ab["key"], 22 if len(ab["key"]) <= 2 else 15,
                                 key_col, rect.width - 8, bold=True)
            self.screen.blit(key_txt, key_txt.get_rect(center=rect.center))

            # Bekleme: karartma + kalan saniye
            if not ready:
                ratio = min(1.0, ab["left"] / max(0.001, ab["total"]))
                shade = pygame.Surface((rect.width, int(rect.height * ratio)), pygame.SRCALPHA)
                shade.fill((0, 0, 0, 165))
                self.screen.blit(shade, (rect.x, rect.y))
                cd_txt = render_fit(f"{ab['left']:.0f}", 20, (238, 226, 200),
                                    rect.width - 8, bold=True)
                self.screen.blit(cd_txt, cd_txt.get_rect(center=rect.center))
            elif ab.get("active"):
                pulse = int((math.sin(time.time() * 9) + 1) * 50 + 90)
                glow = pygame.Surface((rect.width + 10, rect.height + 10), pygame.SRCALPHA)
                pygame.draw.rect(glow, ui_theme.readable(col) + (pulse,),
                                 glow.get_rect(), width=3, border_radius=5)
                self.screen.blit(glow, (rect.x - 5, rect.y - 5))

            # Şarj göstergesi (taret gibi biriken yetenekler): slotun üstünde
            # kapasite kadar nokta, dolu olanlar aksan renginde yanar.
            if ab.get("max_charges"):
                mx = int(ab["max_charges"])
                cur = int(ab.get("charges", 0))
                pip_r, pip_gap = 4, 5
                total_pw = mx * (pip_r * 2) + (mx - 1) * pip_gap
                px = rect.centerx - total_pw // 2 + pip_r
                py = rect.top - pip_r - 4
                for c in range(mx):
                    filled = c < cur
                    pc = ui_theme.readable(col) if filled else (78, 74, 70)
                    pygame.draw.circle(self.screen, pc, (px + c * (pip_r * 2 + pip_gap), py), pip_r)
                    if filled:
                        pygame.draw.circle(self.screen, ui_theme.DARK_OUT,
                                           (px + c * (pip_r * 2 + pip_gap), py), pip_r, 1)

            name_txt = render_fit(ab["name"], 15,
                                  (206, 199, 184) if ready else (136, 130, 120),
                                  slot + gap)
            self.screen.blit(name_txt, name_txt.get_rect(
                midtop=(rect.centerx, rect.bottom + 4)))

    def _cast_fx(self, p, kind):
        """Yetenek kullanıldığında açıklamasına uygun görsel efekt üretir."""
        g = self.logic
        if kind == "dash":
            # Atılma: bakış yönünde hız çizgileri + arkada halka
            g.add_event("shockwave", p.x, p.y, radius=70, color=(120, 190, 255), timer=0.22)
            for _ in range(14):
                a = p.facing_angle + math.pi + random.uniform(-0.5, 0.5)
                v = random.uniform(6, 15)
                g.particles.append({
                    'x': p.x, 'y': p.y,
                    'vx': math.cos(a) * v, 'vy': math.sin(a) * v,
                    'timer': 0.28, 'color': (150, 205, 255), 'size': random.randint(2, 5)})
            if getattr(p, "class_id", "") == "ninja":
                # Ninja pasifi: atılma sonrası ilk vuruş 2 kat -> gölge patlaması
                g.add_event("shockwave", p.x, p.y, radius=52, color=(60, 40, 90), timer=0.3)
                g.add_event("damage_text", p.x, p.y - 42, value="GÖLGE!",
                            color=(180, 150, 255), timer=0.5)

        elif kind == "artifact":
            # Eser: büyü halkası, dışa doğru mor kıvılcım
            g.add_event("shockwave", p.x, p.y, radius=110, color=(170, 110, 240), timer=0.35)
            for _ in range(18):
                a = random.uniform(0, math.pi * 2)
                v = random.uniform(4, 11)
                g.particles.append({
                    'x': p.x, 'y': p.y,
                    'vx': math.cos(a) * v, 'vy': math.sin(a) * v,
                    'timer': 0.4, 'color': (190, 130, 255), 'size': random.randint(2, 6)})

        elif kind == "blood_absorb":
            # Kan Emme: mermileri EMER -> parçacıklar İÇERİ doğru akar
            g.add_event("shockwave", p.x, p.y, radius=130, color=(200, 30, 40), timer=0.4)
            for _ in range(22):
                a = random.uniform(0, math.pi * 2)
                dist = random.uniform(70, 130)
                sx, sy = p.x + math.cos(a) * dist, p.y + math.sin(a) * dist
                g.particles.append({
                    'x': sx, 'y': sy,
                    'vx': -math.cos(a) * dist * 0.14, 'vy': -math.sin(a) * dist * 0.14,
                    'timer': 0.45, 'color': (225, 45, 55), 'size': random.randint(2, 6)})

    @staticmethod
    def _format_stat_bonus(value, percent=False):
        if abs(value) < 0.0001:
            return ""
        if percent:
            amount = value * 100
            shown = f"{amount:.0f}" if abs(amount - round(amount)) < 0.01 else f"{amount:.1f}"
            return f"{value:+.0%}" if abs(amount) < 1000 else f"{shown}%"
        shown = f"{value:.1f}".rstrip("0").rstrip(".")
        return f"{value:+.0f}" if float(value).is_integer() else f"{value:+.1f}"

    def draw_live_stats_panel(self, p):
        """Tüm kaynaklardan gelen son statları ve kartların ham katkısını gösterir."""
        import ui_theme
        panel_w = 460
        outer = pygame.Rect(self.width - panel_w - 16, 100, panel_w,
                            min(840, self.height - 120))
        # Gotik çerçeve rect'in İÇİNE çizilir (draw_inset_frame): dış ölçü sabit
        # kalır, ekran kenarına yaslı panelde draw_panel gibi dışa taşmaz.
        panel = ui_theme.draw_inset_frame(
            self.screen, outer, "panel_frame_small.png",
            fill=(20, 17, 24), alpha=248, pad=26)
        gold = ui_theme.readable(ui_theme.COLORS["gold"])

        card_system = self.logic.card_system
        card_bonus = card_system.get_stat_contributions()
        card_count = len(card_system.active_cards)
        active = set(card_system.active_cards)
        synergy_count = sum(
            1 for synergy in card_system.synergy_system.SYNERGIES
            if all(card_id in active for card_id in synergy["required_cards"])
        )

        title = self.font_sub.render("ANLIK İSTATİSTİKLER", True, gold)
        self.screen.blit(title, (panel.x + 16, panel.y + 12))
        count_txt = self.font_desc.render(f"{card_count} kart • {synergy_count} sinerji", True, (176, 168, 155))
        self.screen.blit(count_txt, (panel.right - count_txt.get_width() - 16, panel.y + 17))

        info = self.font_desc.render("Toplam: tüm kaynaklar  |  Kart: ham kart+sinerji katkısı", True, (150, 144, 132))
        if info.get_width() > panel.width - 32:
            ratio = (panel.width - 32) / info.get_width()
            info = pygame.transform.smoothscale(info, (panel.width - 32, max(12, int(info.get_height() * ratio))))
        self.screen.blit(info, (panel.x + 16, panel.y + 43))

        y = panel.y + 72
        row_h = 24

        def section(label):
            nonlocal y
            pygame.draw.line(self.screen, (78, 68, 58), (panel.x + 14, y + 9), (panel.right - 14, y + 9), 1)
            text_surf = self.font_desc.render(label, True, gold)
            bg = pygame.Rect(panel.x + 14, y, text_surf.get_width() + 12, text_surf.get_height())
            pygame.draw.rect(self.screen, (20, 17, 24), bg)
            self.screen.blit(text_surf, (panel.x + 20, y))
            y += 25

        def row(label, value, bonus_value=0, percent_bonus=False):
            nonlocal y
            label_surf = self.font_desc.render(label, True, (176, 170, 158))
            value_surf = self.font_desc.render(str(value), True, ui_theme.TEXT_COL)
            self.screen.blit(label_surf, (panel.x + 20, y))
            self.screen.blit(value_surf, (panel.x + 270 - value_surf.get_width(), y))
            bonus_text = self._format_stat_bonus(bonus_value, percent_bonus)
            if bonus_text:
                bonus_color = (90, 220, 140) if bonus_value > 0 else (245, 115, 110)
                bonus_surf = self.font_desc.render(bonus_text, True, bonus_color)
                self.screen.blit(bonus_surf, (panel.right - bonus_surf.get_width() - 18, y))
            y += row_h

        stats = p.stats
        dmg_mult = stats.get("dmgMult", 1.0)
        dot_mult = 1.0 + stats.get("dotDmgMult", 0.0)
        phys_base = stats.get("physDmg", 20) + stats.get("physDmgFlat", 0)
        fire_base = stats.get("fireDamage", 0) + stats.get("fireDmgFlat", 0)
        frost_base = stats.get("frostDamage", 0) + stats.get("frostDmgFlat", 0)
        poison_base = stats.get("poisonDps", 0)
        attacks_per_second = 1000.0 / max(1.0, stats.get("attack_cooldown", 350))

        section("SALDIRI")
        row("Hasar çarpanı", f"x{dmg_mult:.2f}", card_bonus.get("dmgMult", 0), True)
        row("DoT çarpanı", f"x{dot_mult:.2f}", card_bonus.get("dotDmgMult", 0), True)
        row("Fiziksel vuruş", f"{phys_base * dmg_mult:.1f}", card_bonus.get("physDmg", 0) + card_bonus.get("physDmgFlat", 0))
        row("Ateş hasarı", f"{fire_base * dmg_mult * dot_mult:.1f}", card_bonus.get("fireDamage", 0) + card_bonus.get("fireDmgFlat", 0))
        row("Buz hasarı", f"{frost_base * dmg_mult * dot_mult:.1f}", card_bonus.get("frostDamage", 0) + card_bonus.get("frostDmgFlat", 0))
        row("Zehir DPS", f"{poison_base * dmg_mult * dot_mult:.1f}", card_bonus.get("poisonDps", 0))
        row("Saldırı / saniye", f"{attacks_per_second:.2f}", card_bonus.get("fireRate", 0), True)
        row("Kritik şansı", f"%{stats.get('critChance', 0.05) * 100:.0f}", card_bonus.get("critChance", 0), True)
        row("Kritik çarpanı", f"x{2.0 + stats.get('critDmg', 0):.2f}", card_bonus.get("critDmg", 0), True)

        section("HASAR TAKİBİ")
        row("Son vuruş", f"{getattr(self.logic, 'last_hit_damage', 0):.0f}")
        current_dps = self.logic.get_current_dps() if hasattr(self.logic, 'get_current_dps') else 0
        row("Anlık DPS", f"{current_dps:.0f}")
        row("Maks DPS", f"{getattr(self.logic, 'max_dps', 0):.0f}")

        section("SAVUNMA")
        row("Can", f"{int(p.hp)} / {int(p.max_hp)}", card_bonus.get("max_hp", 0))
        # Kart can bedelleri artık yüzdesel (max_hp_pct). "Can" satırındaki düz
        # katkıyla karışmaması için ayrı satırda çarpan olarak gösterilir;
        # aksi halde HUD "-20 Can" derken gerçek etki -%20 oluyordu.
        hp_pct_bonus = card_bonus.get("max_hp_pct", 0)
        if hp_pct_bonus:
            row("Kart can çarpanı", f"x{max(0.05, 1.0 + hp_pct_bonus / 100.0):.2f}",
                hp_pct_bonus / 100.0, True)
        row("Zırh", f"{stats.get('armor', 0):.0f}", card_bonus.get("armor", 0))
        row("Kaçınma", f"%{stats.get('dodgeChance', 0) * 100:.0f}", card_bonus.get("dodgeChance", 0), True)
        row("Alınan hasar", f"x{getattr(p, 'damage_taken_mult', 1.0):.2f}")

        section("YARDIMCI / MİNYON")
        row("Hareket hızı", f"{stats.get('speed', 0):.1f}", card_bonus.get("speed", 0))
        row("Can çalma", f"%{stats.get('lifesteal', 0) * 100:.0f}", card_bonus.get("lifesteal", 0), True)
        row("Minyon hasarı", f"x{stats.get('minionDamage', 1):.2f}", card_bonus.get("minionDamage", 0), True)
        row("Minyon limiti", f"{max(1, int(stats.get('minionCount', 1)))}", card_bonus.get("minionCount", 0))

    def draw_inventory(self):
        # Full Screen Overlay
        self._overlay_surface.fill((20, 20, 30, 240)) # Daha koyu premium hava
        self.screen.blit(self._overlay_surface, (0, 0))

        # İçerik alanının gotik panel zemini (sekme çubuğunun altında kalır).
        # İçerik ekran ortasına göre sağa kaymış durumda (kuşanılanlar ~510'da
        # başlar, filtre satırı ~1660'a kadar gider), panel de ona göre.
        import ui_nineslice as n9
        n9.draw(self.screen, "panel_frame.png", self._inventory_panel_rect())

        p = self.logic.players[self.logic.local_player_id]
        
        # 1. TAB BAR & HUD
        for btn in self.tab_buttons:
            btn.update()  # hover durumu hiç güncellenmiyordu
            btn.draw(self.screen, self.font_sub, self.active_tab)
            
        import ui_theme
        # Altın: sekme çubuğunun bittiği yer ile ÇIKIŞ butonu arasına sığdırılır
        # (sabit width-400 konumu son sekmenin üstüne biniyordu).
        tabs_right = self.tab_buttons[-1].rect.right
        gold_max_w = max(80, self.exit_btn_rect.left - tabs_right - 40)
        gold_txt = render_fit(f"ALTIN: {p.gold}", 26,
                              ui_theme.readable(ui_theme.COLORS["gold"]),
                              gold_max_w, bold=True)
        self.screen.blit(gold_txt, (self.exit_btn_rect.left - gold_txt.get_width() - 20,
                                    self.exit_btn_rect.centery - gold_txt.get_height() // 2))

        exit_state = "hover" if self.exit_btn_rect.collidepoint(pygame.mouse.get_pos()) else "normal"
        surf, over = ui_theme.render_banner_button(
            self.exit_btn_rect.width, self.exit_btn_rect.height, "SAVAŞA DÖN",
            ui_theme.COLORS["blood"], state=exit_state, skull=False)
        self.screen.blit(surf, (self.exit_btn_rect.centerx - surf.get_width() // 2,
                                self.exit_btn_rect.y - over))
        
        # 2. SEKME İÇERİĞİ
        if self.active_tab == "inventory":
            self.draw_inventory_tab(p)
        elif self.active_tab == "hero":
            self.draw_hero_tab(p)
        elif self.active_tab == "skills":
            self.draw_skills_tab(p)
        elif self.active_tab == "ascendancy":
            self.draw_ascendancy_tab(p)
        elif self.active_tab == "market":
            self.draw_market_tab(p)
        elif self.active_tab == "aura":
            self.draw_aura_tab(p)
        elif self.active_tab == "synergy":
            self.draw_synergy_tab(p)
        else:
            msg = self.font_main.render("YAKINDA...", True, (100, 100, 100))
            self.screen.blit(msg, (self.width // 2 - msg.get_width() // 2, self.height // 2))

    def draw_boss_healthbar(self):
        boss = getattr(self, "_hud_boss", None)
        if not boss: return

        # Ekran Üst Orta (konum _layout_top_hud'dan)
        bar_w, bar_h = 700, 25
        x = self.width // 2 - bar_w // 2
        y = self._hud_boss_bar_y

        ratio = max(0, boss.hp / boss.max_hp)
        import ui_nineslice as n9
        if not n9.draw_bar(self.screen, "bar_frame.png",
                           pygame.Rect(x, y, bar_w, bar_h), "bar_fill_hp.png", ratio):
            pygame.draw.rect(self.screen, (20, 20, 30), (x, y, bar_w, bar_h), border_radius=5)
            pygame.draw.rect(self.screen, (192, 57, 43), (x, y, int(bar_w * ratio), bar_h), border_radius=5)
            pygame.draw.rect(self.screen, (241, 196, 15), (x, y, bar_w, bar_h), width=2, border_radius=5)
        
        # İsim boss'tan okunur (sabit metin iki yerde ayrı gömülüydü)
        import ui_theme
        name = getattr(boss, "name", "BOSS").upper()
        name_t = render_fit(name, 28, ui_theme.readable(ui_theme.COLORS["gold"]),
                            bar_w, bold=True)
        self.screen.blit(name_t, (self.width // 2 - name_t.get_width() // 2,
                                  self._hud_boss_name_y))

        # HP Text (Numerical)
        hp_str = f"{int(boss.hp):,} / {int(boss.max_hp):,}"
        hp_txt = render_fit(hp_str, 17, ui_theme.TEXT_COL, bar_w - 40, bold=True)
        self.screen.blit(hp_txt, hp_txt.get_rect(center=(self.width // 2, y + bar_h // 2)))

    ORB_ROWS_PER_PAGE = 8
    MARKET_ROWS_PER_PAGE = 5

    def _craft_layout(self):
        """Craft penceresinin TÜM rect'leri — çizim, tıklama ve tooltip tek kaynak.

        Eskiden panel, kapat butonu ve orb satırları hem çizimde hem tıklama
        handler'ında ayrı ayrı literal olarak yazılıydı; "AL" butonu iki farklı
        formülle (rect.right-70 / panel.right-100) hesaplanıyordu.
        """
        # panel = içerik alanı; gotik çerçeve draw_panel ile DIŞINA çizilir
        panel = pygame.Rect(self.width // 2 - 450, self.height // 2 - 300, 900, 600)
        inner = panel.inflate(-36, -36)

        # Sol sütun geniş: kısa orb satırlarında "SEÇ" butonu plakanın uç
        # kapaklarına binmesin diye 270px.
        left_w, right_w = 270, 250
        left_x = inner.x
        right_x = inner.right - right_w
        pager_y = inner.bottom - 36

        orb_rows, orb_use = [], []
        for i in range(self.ORB_ROWS_PER_PAGE):
            r = pygame.Rect(left_x, inner.y + 46 + i * 52, left_w, 44)
            orb_rows.append(r)
            orb_use.append(pygame.Rect(r.right - 90, r.y + 5, 60, 34))

        # Market satırları sayfalama şeridinin ÜSTÜNDE bitmeli
        mkt_rows, mkt_buy = [], []
        for i in range(self.MARKET_ROWS_PER_PAGE):
            r = pygame.Rect(right_x, inner.y + 76 + i * 80, right_w, 72)
            mkt_rows.append(r)
            mkt_buy.append(pygame.Rect(r.right - 62, r.centery - 19, 56, 38))

        item_rect = pygame.Rect(panel.centerx - 140, inner.y + 46, 280, 360)
        pager_y = inner.bottom - 36
        return {
            "panel": panel,
            "inner": inner,
            "close": pygame.Rect(inner.right - 40, inner.y, 40, 40),
            "orb_rows": orb_rows, "orb_use": orb_use,
            "mkt_rows": mkt_rows, "mkt_buy": mkt_buy,
            "item": item_rect,
            "take_back": pygame.Rect(panel.centerx - 75, item_rect.bottom + 12, 150, 40),
            "orb_prev": pygame.Rect(left_x, pager_y, 110, 34),
            "orb_next": pygame.Rect(left_x + left_w - 110, pager_y, 110, 34),
            "mkt_prev": pygame.Rect(right_x, pager_y, 110, 34),
            "mkt_next": pygame.Rect(right_x + right_w - 110, pager_y, 110, 34),
        }

    def draw_craft_window(self):
        import ui_theme
        self._overlay_surface.fill((0, 0, 0, 220))
        self.screen.blit(self._overlay_surface, (0, 0))

        L = self._craft_layout()
        panel = L["panel"]
        ui_theme.draw_panel(self.screen, panel)

        item = self.crafting_target
        if not item: return

        p = self.logic.players[self.logic.local_player_id]
        mouse_pos = pygame.mouse.get_pos()
        night = ui_theme.readable(ui_theme.COLORS["night"])
        gold = ui_theme.readable(ui_theme.COLORS["gold"])
        blood = ui_theme.readable(ui_theme.COLORS["blood"])

        def plate_btn(rect, label, key, enabled=True):
            hovered = enabled and rect.collidepoint(mouse_pos)
            ui_theme.draw_plate(self.screen, rect,
                                "hover" if hovered else ("normal" if enabled else "disabled"),
                                ui_theme.COLORS[key] if enabled else None)
            col = ui_theme.TEXT_COL if hovered else (176, 170, 158)
            txt = render_fit(label, 17, col, rect.width - 30, bold=hovered)
            self.screen.blit(txt, txt.get_rect(center=rect.center))

        # 1. SOL: ENVANTERDEKİ ORBLAR
        orbs_in_inv = [x for x in p.inventory if x.get('type') == 'orb']
        title_l = render_fit(f"ORBLARIN ({self.orb_inv_page + 1})", 22, night, 250, bold=True)
        self.screen.blit(title_l, (L["inner"].x, L["inner"].y + 6))

        offset_i = self.orb_inv_page * self.ORB_ROWS_PER_PAGE
        self.craft_orb_use_rects = []
        for i in range(min(self.ORB_ROWS_PER_PAGE, len(orbs_in_inv) - offset_i)):
            orb = orbs_in_inv[offset_i + i]
            rect, use_btn = L["orb_rows"][i], L["orb_use"][i]
            self.craft_orb_use_rects.append((offset_i + i, use_btn))

            # Kısa satırda buton plakası: panel_frame_small'ın 40px köşe
            # süsleri 44px'lik satırı boğuyordu.
            ui_theme.draw_plate(self.screen, rect, "normal")
            name = orb['name'].split(" (")[0]
            txt = render_fit(f"{name} x{orb.get('stack', 1)}", 17, ui_theme.TEXT_COL,
                             use_btn.left - rect.x - 42)
            self.screen.blit(txt, (rect.x + 30, rect.centery - txt.get_height() // 2))
            plate_btn(use_btn, "SEÇ", "moss")

        plate_btn(L["orb_prev"], "<< GERİ", "night", self.orb_inv_page > 0)
        plate_btn(L["orb_next"], "İLERİ >>", "night",
                  (self.orb_inv_page + 1) * self.ORB_ROWS_PER_PAGE < len(orbs_in_inv))
        self.craft_orb_prev_rect, self.craft_orb_next_rect = L["orb_prev"], L["orb_next"]

        # 2. ORTA: HEDEF EŞYA
        title_c = render_fit("HEDEF EŞYA", 22, gold, 280, bold=True)
        self.screen.blit(title_c, (panel.centerx - title_c.get_width() // 2, L["inner"].y + 6))

        item_rect = L["item"]
        color = ui_theme.rarity_color(item.get('rarity', 'Normal'))
        # pad=32: çerçevenin köşe taşları 40px, metin onların hizasından uzak dursun
        ic = ui_theme.draw_inset_frame(
            self.screen, item_rect, "panel_frame_small.png", fill=(20, 17, 24), alpha=248,
            tint=tuple(int(c * 0.30) for c in color), pad=32)

        name_t = render_fit(item['name'], 21, color, ic.width, bold=True)
        self.screen.blit(name_t, (ic.x, ic.y))
        type_t = render_fit(f"{item['rarity']} {item['type'].upper()}", 17,
                            (172, 166, 154), ic.width)
        self.screen.blit(type_t, (ic.x, ic.y + name_t.get_height() + 2))

        line_y = ic.y + name_t.get_height() + type_t.get_height() + 8
        pygame.draw.line(self.screen, ui_theme.METAL_LO, (ic.x, line_y), (ic.right, line_y))

        y_s = line_y + 8
        for stat, val in item.get('itemBase', {}).items():
            st_t = render_fit(f"[*] {stat}: {val}", 17, (176, 122, 82), ic.width)
            self.screen.blit(st_t, (ic.x, y_s))
            y_s += 23

        # Affix seviye renkleri paletten (T1 altın, T2 yeşil, T3 mavi)
        tier_keys = {1: "gold", 2: "moss", 3: "night"}
        for aff in item.get('prefixes', []) + item.get('suffixes', []):
            tier = aff.get('tier', 3)
            a_col = ui_theme.readable(ui_theme.COLORS[tier_keys.get(tier, "night")])
            label = f"[{aff.get('label', '?')} (T{tier})] +{aff['val']} {aff['stat']}"
            af_t = render_fit(label, 17, a_col, ic.width)
            self.screen.blit(af_t, (ic.x, y_s))
            y_s += 23

        self.craft_take_back_rect = L["take_back"]
        plate_btn(L["take_back"], "GERİ AL", "night")

        # 3. SAĞ: ORB MARKET (DÜKKAN)
        title_r = render_fit(f"ORB MARKET ({self.orb_market_page + 1})", 22, blood, 250, bold=True)
        self.screen.blit(title_r, (L["mkt_rows"][0].x, L["inner"].y + 6))
        gold_t = render_fit(f"GOLD: {p.gold}", 20, gold, 250, bold=True)
        self.screen.blit(gold_t, (L["mkt_rows"][0].x, L["inner"].y + 34))

        market_list = self.logic.orb_market
        offset_m = self.orb_market_page * self.MARKET_ROWS_PER_PAGE
        for i in range(min(self.MARKET_ROWS_PER_PAGE, len(market_list) - offset_m)):
            orb = market_list[offset_m + i]
            rect, buy_btn = L["mkt_rows"][i], L["mkt_buy"][i]
            ui_theme.draw_inset_frame(self.screen, rect, "panel_frame_small.png",
                                      fill=(30, 26, 36), alpha=244, pad=10)
            text_w = buy_btn.left - rect.x - 20
            name = orb['name'].split(" (")[0]
            self.screen.blit(render_fit(name, 17, ui_theme.TEXT_COL, text_w), (rect.x + 10, rect.y + 8))
            self.screen.blit(render_fit(f"{orb['price']} GOLD", 16, gold, text_w), (rect.x + 10, rect.y + 30))
            owned = sum(x.get('stack', 1) for x in p.inventory
                        if x.get('type') == 'orb' and x.get('orb_id') == orb['orb_id'])
            self.screen.blit(render_fit(f"Sende: {owned}", 15, (176, 170, 158), text_w),
                             (rect.x + 10, rect.y + 50))
            plate_btn(buy_btn, "AL", "moss", p.gold >= orb['price'])

        plate_btn(L["mkt_prev"], "<< GERİ", "night", self.orb_market_page > 0)
        plate_btn(L["mkt_next"], "İLERİ >>", "night",
                  (self.orb_market_page + 1) * self.MARKET_ROWS_PER_PAGE < len(market_list))
        self.craft_mkt_prev_rect, self.craft_mkt_next_rect = L["mkt_prev"], L["mkt_next"]

        # Çıkış Butonu
        plate_btn(L["close"], "X", "ember")

        # Hata Mesajı
        if self.craft_error_msg:
            err_t = render_fit(self.craft_error_msg, 21, blood, panel.width - 120, bold=True)
            self.screen.blit(err_t, (panel.centerx - err_t.get_width() // 2, panel.bottom - 52))

    def handle_tooltips(self, p):
        m_pos = pygame.mouse.get_pos()
        hovered_item = None
        
        if self.show_craft_window:
            # Satır rect'leri çizimle aynı kaynaktan (paneli yeniden türetmiyoruz)
            L = self._craft_layout()
            orbs_in_inv = [x for x in p.inventory if x.get('type') == 'orb']
            offset_i = self.orb_inv_page * self.ORB_ROWS_PER_PAGE
            for i in range(min(self.ORB_ROWS_PER_PAGE, len(orbs_in_inv) - offset_i)):
                if L["orb_rows"][i].collidepoint(m_pos):
                    hovered_item = orbs_in_inv[offset_i + i]
                    break
            
            if hovered_item:
                self.draw_item_tooltip(hovered_item, m_pos, p)
            return
        
        # 1. Envanter Tabında: Kuşanılanlar ve Çanta
        if self.active_tab == "inventory":
            # Kuşanılanlar
            for row in self.equip_rows:
                if row.rect.collidepoint(m_pos) and row.item:
                    hovered_item = row.item
            
            # Çanta - çizimle AYNI filtre (tek kaynak); eskiden burada yalnız
            # orb gizleme uygulanıyor, filtre açıkken yanlış eşya gösteriliyordu
            filtered_inv = self._filtered_inventory(p)
            offset = self.inventory_page * 12
            for card in self.bp_cards:
                actual_idx = offset + card.idx
                if card.rect.collidepoint(m_pos) and actual_idx < len(filtered_inv):
                    hovered_item = filtered_inv[actual_idx]
        
        # 2. Market Tabında (Sayfa Ofsetli)
        elif self.active_tab == "market":
            market_list = self.logic.market_inventory if self.market_tab == "items" else self.logic.orb_market
            offset = self.market_page * 12
            for i, card in enumerate(self.market_cards):
                actual_idx = offset + i
                if card.rect.collidepoint(m_pos) and actual_idx < len(market_list):
                    hovered_item = market_list[actual_idx]
        
        if hovered_item:
            self.draw_item_tooltip(hovered_item, m_pos, p)

    def draw_market_tab(self, p):
        import ui_theme
        mouse_pos = pygame.mouse.get_pos()

        def plate_btn(rect, label, key):
            hovered = rect.collidepoint(mouse_pos)
            ui_theme.draw_plate(self.screen, rect, "hover" if hovered else "normal",
                                ui_theme.COLORS[key])
            col = ui_theme.TEXT_COL if hovered else (176, 170, 158)
            txt = render_fit(label, 17, col, rect.width - 30, bold=hovered)
            self.screen.blit(txt, txt.get_rect(center=rect.center))

        # Sekme Butonları
        for btn in self.market_tab_btns:
            btn.update()  # hover durumu hiç güncellenmiyordu
            btn.draw(self.screen, self.font_sub, self.market_tab)

        # Yenile Butonu (Sadece Eşyalar sekmesinde) — sekme plakalarının
        # altına hizalanır (eskiden reset_btn_rect ile aynı bölgeye düşüyordu)
        if self.market_tab == "items":
            wave_level = self.logic.wave.get("level", 1)
            cost = 500 + max(0, (wave_level - 1) * 400)
            self.refresh_btn_rect.update(self.market_tab_btns[-1].rect.right + 30,
                                         self.market_tab_btns[-1].rect.y, 190, 40)
            plate_btn(self.refresh_btn_rect, f"YENİLE ({cost} G)", "moss")

        # Eşyaları/Orbları Listele
        market_list = self.logic.market_inventory if self.market_tab == "items" else self.logic.orb_market
        
        max_m_pages = max(0, (len(market_list) - 1) // 12)
        self.market_page = min(self.market_page, max_m_pages)
        
        # Market Sayfalama (Dinamik render)
        offset = self.market_page * 12
        for i, card in enumerate(self.market_cards):
            actual_idx = offset + i
            if actual_idx < len(market_list):
                item = market_list[actual_idx]
                card.item = item
                
                # Sahiplik miktarını hesapla
                owned = 0
                if self.market_tab == "orbs":
                    owned = sum([x.get('stack', 1) for x in p.inventory if x.get('type') == 'orb' and x.get('orb_id') == item.get('orb_id')])
                else:
                    owned = sum([1 for x in p.inventory if x.get('name') == item['name']])
                
                card.draw(self.screen, self.font_sub, self.font_desc, owned_count=owned)
            else:
                card.item = None
                ui_theme.draw_inset_frame(self.screen, card.rect, "panel_frame_small.png",
                                          fill=(24, 21, 28), alpha=170, pad=10)

        # Market Sayfalama Butonları Çizimi
        if self.market_page > 0:
            plate_btn(self.mkt_prev_rect, "<< GERİ", "night")
        if (self.market_page + 1) * 12 < len(market_list):
            plate_btn(self.mkt_next_rect, "İLERİ >>", "night")

        # Sayfa No — sayfalama butonlarıyla aynı hizada (sabit y yerine)
        page_t = render_fit(f"Sayfa {self.market_page + 1}", 18, (186, 180, 168), 200)
        self.screen.blit(page_t, page_t.get_rect(
            center=(self.width // 2, self.mkt_prev_rect.centery)))


    def _item_total_stats(self, item):
        """Eşyanın toplam statları: itemBase + prefix/suffix affixleri."""
        if not item:
            return {}
        tot = dict(item.get("itemBase", {}))
        for aff in item.get("prefixes", []) + item.get("suffixes", []):
            s = aff.get("stat")
            if s is not None:
                tot[s] = tot.get(s, 0) + aff.get("val", 0)
        return tot

    def _tooltip_lines(self, item, p, text_w):
        """Tooltip içeriğini önce ÜRETİR (çizmeden).

        Yükseklik eskiden satır sayısından tahmin ediliyordu; sarılan açıklama
        ve set bonusları hesaba girmediği için uzun eşyalarda metin panelin
        altından taşıyordu. Artık gerçek yüzeylerden ölçülüyor.
        Dönen liste: (surface, x_offset, kind) — kind: 'text' | 'rule' | 'bullet'
        """
        import ui_theme
        from ui_elements import wrap_text
        lines = []
        i_rarity = item.get('rarity', 'Normal')
        color = ui_theme.rarity_color(i_rarity)

        lines.append((render_fit(item['name'], 21, color, text_w, bold=True), 0, 'text'))
        lines.append((render_fit(f"{i_rarity} {item['type'].upper()}", 17,
                                 (172, 166, 154), text_w), 0, 'text'))
        lines.append((None, 0, 'rule'))

        for stat, val in item.get("itemBase", {}).items():
            label = f"{ITEM_STAT_LABEL.get(stat, stat)}: {_fmt_stat_val(stat, val)}"
            lines.append((render_fit(label, 18, (206, 182, 140), text_w), 0, 'text'))

        # T1 altın, T2 yeşil, T3 mavi — renkler paletten
        tier_keys = {1: "gold", 2: "moss", 3: "night"}
        for aff in item.get("prefixes", []) + item.get("suffixes", []):
            tier = aff.get('tier', 3)
            a_col = ui_theme.readable(ui_theme.COLORS[tier_keys.get(tier, "night")])
            label = f"+{_fmt_stat_val(aff['stat'], aff['val'])} {ITEM_STAT_LABEL.get(aff['stat'], aff['stat'])}  (T{tier})"
            lines.append((render_fit(label, 17, a_col, text_w), 0, 'text'))

        # --- KUŞANILANLA KIYAS (bag'daki eşyayı slottaki eşyayla karşılaştır) ---
        slot = item.get("type")
        equipped = p.inv_manager.equipped.get(slot)
        if slot in _EQUIP_SLOTS and equipped is not item:
            gold = ui_theme.readable(ui_theme.COLORS["gold"])
            green = (96, 214, 130)
            red = (222, 104, 98)
            lines.append((None, 0, 'rule'))
            head = "KUŞANILANLA KIYAS" if equipped else "KUŞANILAN YOK — bu slot boş"
            lines.append((render_fit(head, 16, gold, text_w, bold=True), 0, 'text'))
            cur = self._item_total_stats(item)
            old = self._item_total_stats(equipped) if equipped else {}
            any_diff = False
            for stat in sorted(set(cur) | set(old)):
                d = cur.get(stat, 0) - old.get(stat, 0)
                if abs(d) < 1e-9:
                    continue
                any_diff = True
                better = (d < 0) if stat in _LOWER_BETTER else (d > 0)
                col = green if better else red
                sign = "+" if d > 0 else "-"
                shown = f"{sign}{_fmt_stat_val(stat, abs(d))}"
                lbl = f"{ITEM_STAT_LABEL.get(stat, stat)}: {shown}"
                lines.append((render_fit(lbl, 16, col, text_w), 0, 'text'))
            if not any_diff and equipped:
                lines.append((render_fit("(fark yok)", 15, (150, 144, 132), text_w), 0, 'text'))

        if item.get('desc'):
            lines.append((None, 0, 'rule'))
            for ln in wrap_text(self.font_desc, item['desc'], text_w):
                lines.append((self.font_desc.render(ln, True, (196, 196, 222)), 0, 'text'))

        if item.get("setTag"):
            from logic.item_system import ItemSystem
            set_key = item['setTag']
            set_data = ItemSystem.set_types.get(set_key)
            if set_data:
                gold = ui_theme.readable(ui_theme.COLORS["gold"])
                moss = ui_theme.readable(ui_theme.COLORS["moss"])
                lines.append((None, 0, 'rule'))
                lines.append((render_fit(f"SET: {set_data['name']}", 17, gold, text_w, bold=True),
                              0, 'text'))
                equipped_sets = [it.get('setTag') for it in p.inv_manager.equipped.values() if it]
                count = equipped_sets.count(set_key)
                for piece_count, bonuses in set_data['bonuses'].items():
                    is_active = count >= piece_count
                    bonus_str = f"({piece_count}) " + ", ".join(f"{k}: {v}" for k, v in bonuses.items())
                    surf = render_fit(bonus_str, 16, moss if is_active else (128, 123, 114),
                                      text_w - 12)
                    lines.append((surf, 12, 'bullet' if is_active else 'text'))
        return lines

    def draw_item_tooltip(self, item, pos, p):
        import ui_theme
        PAD, W = 16, 290
        text_w = W - PAD * 2
        lines = self._tooltip_lines(item, p, text_w)

        # Gerçek yükseklik: ölçülen satırlardan
        h = PAD * 2
        for surf, _, kind in lines:
            h += 10 if kind == 'rule' else surf.get_height() + 3

        # Ekran sınır kontrolü
        tx, ty = pos[0] + 20, pos[1] + 20
        if tx + W > self.width: tx = pos[0] - W - 20
        if ty + h > self.height: ty = pos[1] - h
        tx = max(10, min(tx, self.width - W - 10))
        ty = max(10, min(ty, self.height - h - 10))

        panel_rect = pygame.Rect(tx, ty, W, h)
        ui_theme.draw_panel(self.screen, panel_rect, fill=(20, 17, 24), alpha=245,
                            nineslice=False)

        y = ty + PAD
        for surf, x_off, kind in lines:
            if kind == 'rule':
                pygame.draw.line(self.screen, ui_theme.METAL_LO,
                                 (tx + PAD, y + 4), (tx + W - PAD, y + 4))
                y += 10
                continue
            if kind == 'bullet':
                pygame.draw.circle(self.screen, ui_theme.readable(ui_theme.COLORS["moss"]),
                                   (tx + PAD + 4, y + surf.get_height() // 2), 3)
            self.screen.blit(surf, (tx + PAD + x_off, y))
            y += surf.get_height() + 3

    def _filtered_inventory(self, p):
        """Aktif filtrelere göre çantayı süzer — TEK kaynak.

        Bu mantık çizim, tıklama ve tooltip'te üç ayrı kopya halindeydi;
        tooltip kopyası yalnız orb gizlemeyi uyguladığı için nadirlik/tip
        filtresi açıkken YANLIŞ eşyanın tooltip'ini gösteriyordu.
        """
        out = []
        for it in p.inventory:
            if self.hide_orbs and it.get('type') == 'orb':
                continue
            if self.inv_filter_rarity != "TÜMÜ":
                if self.inv_filter_rarity == "SET" and not it.get("setTag"): continue
                if self.inv_filter_rarity != "SET" and it.get("rarity") != self.inv_filter_rarity: continue
            if self.inv_filter_type != "TÜMÜ":
                it_type = it.get("type", "")
                if self.inv_filter_type == "armor" and it_type not in ["helmet", "chest"]: continue
                if self.inv_filter_type == "accessory" and it_type not in ["amulet", "ring"]: continue
                if self.inv_filter_type == "special" and it_type not in ["artifact", "orb"]: continue
                if self.inv_filter_type not in ["armor", "accessory", "special"] and it_type != self.inv_filter_type: continue
            out.append(it)
        return out

    def _inventory_panel_rect(self):
        """Tab menüsünün gotik zemin paneli."""
        return pygame.Rect(self.width // 2 - 520, 92, 1260, self.height - 150)

    def _apply_inventory_layout(self):
        """Envanter sekmesinin TÜM rect'lerini panelden türetip yazar.

        Çizim ve tıklama bu metodu çağırır. Eskiden filtreler/kartlar/sayfalama
        init'te sabit y'lerle kuruluyor, çizimde başka y'lere eziliyordu; ekran
        yüksekliği değişince ızgara toplu-satış şeridinin altına taşıyor ve
        filtre şeridi panelin üst çerçevesinin üstüne biniyordu.
        """
        panel = self._inventory_panel_rect()
        inner_top = panel.y + 52       # gotik çerçevenin iç kenarı
        inner_bottom = panel.bottom - 52

        # Filtre şeritleri (2 satır) -> başlıklar -> ızgara
        filt_y = inner_top + 10
        filt_h = 34
        self._inv_title_y = filt_y + 2 * (filt_h + 6) + 10
        grid_y = self._inv_title_y + 36

        pager_h, mass_h = 34, 38
        pager_y = inner_bottom - pager_h
        mass_y = pager_y - mass_h - 8
        grid_h = max(120, mass_y - 10 - grid_y)
        row_h = max(64, min(86, grid_h // 6))

        self._inv_grid_y = grid_y
        self._inv_row_h = row_h

        # Filtre butonları
        start_x = self.width // 2 + 20
        gap = 4
        available = self.width - start_x - 20
        fw = min(110, (available - gap * 5) // 6)
        rarity_count = len(self.rarity_filters)
        for i, r in enumerate(self.filter_rects):
            row = 0 if i < rarity_count else 1
            col = i if i < rarity_count else i - rarity_count
            r.update(start_x + col * (fw + gap), filt_y + row * (filt_h + 6),
                     fw, filt_h)
        self.orb_toggle_rect.update(start_x + 5 * (fw + gap), filt_y + filt_h + 6,
                                    fw, filt_h)

        # Kuşanılanlar (sol) ve çanta kartları (sağ)
        eq_h = min(68, row_h - 6)
        for i, row in enumerate(self.equip_rows):
            row.rect.y = grid_y + i * row_h
            row.rect.height = eq_h

        for i, card in enumerate(self.bp_cards):
            card.reposition(y=grid_y + (i // 2) * row_h, h=row_h - 6)

        # Toplu satış + sayfalama
        mass_gap = 6
        mass_w = min(140, (available - mass_gap * 3) // 4)
        for i, r in enumerate(self.mass_sell_rects):
            r.update(start_x + i * (mass_w + mass_gap), mass_y, mass_w, mass_h)

        self.inv_prev_rect.update(start_x, pager_y, 120, pager_h)
        self.inv_next_rect.update(self.width - 160, pager_y, 120, pager_h)

    def draw_inventory_tab(self, p):
        import ui_theme
        self._apply_inventory_layout()
        acc = ui_theme.readable(ui_theme.COLORS["gold"])

        # Sol Taraf: Kuşanılanlar
        title_l = render_fit("KUŞANILANLAR (SAĞ TIKLA ÇIKAR)", 24, acc, 420, bold=True)
        self.screen.blit(title_l, (self.width // 2 - 450, self._inv_title_y))

        for row in self.equip_rows:
            row.item = p.inv_manager.equipped.get(row.slot_type)
            row.update(row.item)
            row.draw(self.screen, self.font_sub)

        # Sağ Taraf: Çanta (Filtreleme, Grid & Sayfalama)
        filtered_inv = self._filtered_inventory(p)

        # FİLTRE BUTONLARI (tema plakası; aktif = hover durumu)
        mouse_pos = pygame.mouse.get_pos()

        def filter_btn(rect, label, is_active, color_key):
            hovered = rect.collidepoint(mouse_pos)
            ui_theme.draw_plate(self.screen, rect,
                                "hover" if (is_active or hovered) else "normal",
                                ui_theme.COLORS[color_key])
            col = ui_theme.TEXT_COL if (is_active or hovered) else (170, 164, 152)
            txt = render_fit(label, 17, col, rect.width - 30, bold=is_active)
            self.screen.blit(txt, txt.get_rect(center=rect.center))

        for i, rarity in enumerate(self.rarity_filters):
            filter_btn(self.filter_rects[i], rarity,
                       self.inv_filter_rarity == rarity, "gold")

        for i, t_filter in enumerate(self.type_filters):
            filter_btn(self.filter_rects[i + len(self.rarity_filters)], t_filter.upper(),
                       self.inv_filter_type == t_filter, "night")

        # ORB TOGGLE
        filter_btn(self.orb_toggle_rect,
                   "ORB GÖSTER" if self.hide_orbs else "ORB GİZLE",
                   not self.hide_orbs, "arcane")

        max_pages = max(0, (len(filtered_inv) - 1) // 12)
        self.inventory_page = min(self.inventory_page, max_pages)

        page_t = render_fit(f"ÇANTA ({len(filtered_inv)}) - Sayfa {self.inventory_page + 1}",
                            24, acc, 400, bold=True)
        self.screen.blit(page_t, (self.width // 2 + 20, self._inv_title_y))

        offset = self.inventory_page * 12
        for i, card in enumerate(self.bp_cards):
            actual_idx = offset + i
            item = filtered_inv[actual_idx] if actual_idx < len(filtered_inv) else None
            card.draw(self.screen, self.font_sub, item)

        # TOPLU SATIŞ BUTONLARI
        for i, btn in enumerate(self.mass_sell_btns):
            rect = self.mass_sell_rects[i]
            hovered = rect.collidepoint(mouse_pos)
            ui_theme.draw_plate(self.screen, rect,
                                "hover" if hovered else "normal",
                                ui_theme.COLORS[btn.get('color_key', 'steel')])
            col = ui_theme.TEXT_COL if hovered else (176, 170, 158)
            st = render_fit(btn['label'], 17, col, rect.width - 30, bold=hovered)
            self.screen.blit(st, st.get_rect(center=rect.center))

        # Sayfalama Butonları (konumları _apply_inventory_layout'tan)
        can_prev = self.inventory_page > 0
        can_next = (self.inventory_page + 1) * 12 < len(filtered_inv)

        for rect, label, enabled in ((self.inv_prev_rect, "<< GERİ", can_prev),
                                     (self.inv_next_rect, "İLERİ >>", can_next)):
            if not enabled:
                continue
            hovered = rect.collidepoint(mouse_pos)
            ui_theme.draw_plate(self.screen, rect,
                                "hover" if hovered else "normal",
                                ui_theme.COLORS["night"])
            col = ui_theme.TEXT_COL if hovered else (176, 170, 158)
            txt = render_fit(label, 17, col, rect.width - 30)
            self.screen.blit(txt, txt.get_rect(center=rect.center))

    # Kahraman sekmesi geometrisi (çizim ve tıklama tek kaynak)
    def _hero_panel_rect(self):
        # Kahraman sekmesi artık BÜYÜK envanter panelini doldurur (eskiden
        # 640x545 küçük kutuydu, geniş gotik çerçevenin içinde boş görünüyordu).
        return self._inventory_panel_rect()

    def _diff_button_rects(self):
        """Zorluk butonları panelin ALTINA sabitlenir. -104: büyük çerçevenin
        52px köşe süslerinin üstünde kalsınlar."""
        panel = self._hero_panel_rect()
        w, gap = 168, 12
        total = 4 * w + 3 * gap
        x0 = panel.centerx - total // 2
        y = panel.bottom - 104
        return [pygame.Rect(x0 + i * (w + gap), y, w, 44) for i in range(4)]

    def draw_hero_tab(self, p):
        import ui_theme
        panel = self._hero_panel_rect()
        gold = ui_theme.readable(ui_theme.COLORS["gold"])
        mouse_pos = pygame.mouse.get_pos()

        # İçerik alanı: büyük gotik çerçevenin (panel_frame.png, 52px inset) içi
        padx, padtop = 74, 62
        cx0 = panel.x + padx
        cw = panel.width - 2 * padx
        top = panel.y + padtop

        # Başlık: sınıf adı — tema serifi, ortalı
        c_name = getattr(p, 'class_name', 'Bilinmiyor')
        title = ui_theme.render_title(c_name, 46, ui_theme.COLORS["gold"])
        self.screen.blit(title, (panel.centerx - title.get_width() // 2, top))
        y = top + title.get_height() + 12

        passives = {
            "warrior": "Geniş Savuruş — Önündeki konide bulunan tüm düşmanlara aynı saldırıyla vurur.",
            "beastmaster": "Av Emri — Kamçıyla işaretlenen hedefe bütün minyonlar anında odaklanır.",
            "sniper": "Keskin Nişan — +%20 temel kritik şansı, +1 sekme ve +1 delme ile başlar.",
            "engineer": "Taret Ustası — Taret kiti kullanırken 5 saniyede bir savaş alanına taret kurar.",
            "ninja": "Arkadan Vuruş — Atılmadan sonraki ilk yakın saldırı 2 kat hasar verir.",
            "alchemist": "Uçucu Karışım — Bomba alanı %40 büyür; yakın saldırılar %30 ihtimalle zehirler.",
            "sorcerer": "Element Döngüsü — Ateş, buz ve zehir arasında döner; her 4. atış kritik ve 2 kat alanlıdır.",
            "bloodwalker": "Kan Öfkesi — Can %30'un altındayken hasar ve hız %40 artar; R ile mermi emilir.",
            "bomber": "Mayın Tarlası — Bombalar patlamaz; yere tetiklemeli mayın bırakır, düşman üstüne basınca patlar.",
        }
        passive_desc = passives.get(getattr(p, 'class_id', 'warrior'), "")
        if passive_desc:
            y = self.draw_text_wrapped(f"Pasif: {passive_desc}", cx0, y, cw,
                                       (176, 192, 226), self.font_sub) + 18

        # Zorluk butonları önce yerini alır; stat gridi kalan alanı doldurur
        diff_rects = self._diff_button_rects()
        diff_label_y = diff_rects[0].y - 34

        # ANLIK statlar (p.stats canlı okunur) — İKİ SÜTUN, kalan alanı doldurur
        st = p.stats
        aps = 1000.0 / max(1.0, st.get('attack_cooldown', 350))
        phys = (st.get('physDmg', 20) + st.get('physDmgFlat', 0)) * st.get('dmgMult', 1)
        stats = [
            ("MAKSİMUM CAN", f"{int(p.hp)} / {int(p.max_hp)}"),
            ("HASAR ÇARPANI", f"x{round(st.get('dmgMult', 1), 2)}"),
            ("FİZİKSEL VURUŞ", f"{phys:.0f}"),
            ("SALDIRI / SANİYE", f"{aps:.2f}"),
            ("KRİTİK ŞANS", f"%{int(st.get('critChance', 0.05) * 100)}"),
            ("KRİTİK ÇARPANI", f"x{2.0 + st.get('critDmg', 0):.2f}"),
            ("ALAN ETKİSİ", f"x{round(st.get('aoe', 1), 2)}"),
            ("DoT ÇARPANI", f"x{round(1.0 + st.get('dotDmgMult', 0), 2)}"),
            ("HAREKET HIZI", round(st.get('speed', 0), 1)),
            ("ZIRH", int(st.get('armor', 0))),
            ("KAÇINMA", f"%{int(st.get('dodgeChance', 0) * 100)}"),
            ("CAN ÇALMA", f"%{int(st.get('lifesteal', 0) * 100)}"),
            ("CAN YENİLENME", f"{round(st.get('regen', 0) + st.get('combatRegen', 0), 1)}/sn"),
            ("EŞYA BULMA (MF)", f"%{int(st.get('magicFind', 1) * 100)}"),
            ("MİNYON HASARI", f"x{round(st.get('minionDamage', 1), 2)}"),
            ("MİNYON LİMİTİ", max(1, int(st.get('minionCount', 1)))),
        ]
        grid_top = y
        grid_bottom = diff_label_y - 14
        col_gap = 54
        col_w = (cw - col_gap) // 2
        half = (len(stats) + 1) // 2
        row_h = min(60, max(38, (grid_bottom - grid_top) // half))
        block_h = row_h * half
        gy0 = grid_top + max(0, (grid_bottom - grid_top - block_h) // 2)
        for i, (label_t, val) in enumerate(stats):
            col = 0 if i < half else 1
            row = i - col * half
            rx = cx0 + col * (col_w + col_gap)
            ry = gy0 + row * row_h
            l_surf = render_fit(label_t, 22, (176, 170, 158), col_w - 120)
            v_surf = render_fit(str(val), 22, ui_theme.TEXT_COL, 120, bold=True)
            self.screen.blit(l_surf, (rx, ry))
            self.screen.blit(v_surf, (rx + col_w - v_surf.get_width(), ry))
            pygame.draw.line(self.screen, (52, 46, 42),
                             (rx, ry + row_h - 8), (rx + col_w, ry + row_h - 8), 1)
        # Sütun ayıracı
        midx = cx0 + col_w + col_gap // 2
        pygame.draw.line(self.screen, (62, 55, 50),
                         (midx, gy0 - 4), (midx, gy0 + block_h - 10), 1)

        # ZORLUK SEÇİMİ (panel altına sabit, ortalı)
        label = render_fit("ZORLUK SEÇİMİ (Dalga anında güncellenir)", 20, gold, cw)
        self.screen.blit(label, (panel.centerx - label.get_width() // 2, diff_label_y))

        diff_names = ["Normal", "Hard", "Very Hard", "Impossible"]
        diff_colors = {"Normal": "moss", "Hard": "gold",
                       "Very Hard": "blood", "Impossible": "ember"}
        mouse_pos = pygame.mouse.get_pos()
        for i, name in enumerate(diff_names):
            rect = diff_rects[i]
            is_active = self.logic.wave["current_diff"] == name
            hovered = rect.collidepoint(mouse_pos)
            ui_theme.draw_plate(self.screen, rect,
                                "hover" if (is_active or hovered) else "normal",
                                ui_theme.COLORS[diff_colors[name]])
            col = ui_theme.TEXT_COL if (is_active or hovered) else (170, 164, 152)
            txt = render_fit(name, 19, col, rect.width - 34, bold=is_active)
            self.screen.blit(txt, txt.get_rect(center=rect.center))

    # ======================= YETENEK AĞACI (NODE TREE) =======================
    # Eski düz 56-yetenek ızgarasının yerini alan yollu (pathing) düğüm ağacı.
    # Tasarım: SKILL_TREE.md. Veri: data/skill_tree.json, motor: logic/skill_tree.

    _TREE_TYPE_COLORS = {
        "start": "moss", "minor": "steel", "notable": "gold", "keystone": "blood",
    }

    def draw_skills_tab(self, p):
        import ui_theme
        panel = self._inventory_panel_rect()
        inner_top = panel.y + 52
        mouse_pos = pygame.mouse.get_pos()

        # Başlık: SP sayacı (solda) + SIFIRLA butonu (sağda)
        sp_txt = render_fit(f"YETENEK PUANI (SP): {p.skill_points}", 24,
                            ui_theme.readable(ui_theme.COLORS["gold"]), 520, bold=True)
        self.screen.blit(sp_txt, (panel.x + 44, inner_top + 8))

        wave_level = self.logic.wave.get("level", 1)
        cost = 2000 + max(0, (wave_level - 1) * 400)
        self.reset_btn_rect.update(panel.right - 250, inner_top + 4, 190, 36)
        reset_hover = self.reset_btn_rect.collidepoint(mouse_pos)
        ui_theme.draw_plate(self.screen, self.reset_btn_rect,
                            "hover" if reset_hover else "normal",
                            ui_theme.COLORS["ember"])
        reset_t = render_fit(f"SIFIRLA ({cost} G)", 17,
                             ui_theme.TEXT_COL if reset_hover else (176, 170, 158),
                             self.reset_btn_rect.width - 30)
        self.screen.blit(reset_t, reset_t.get_rect(center=self.reset_btn_rect.center))

        # Kullanım ipucu (ortada, başlık satırında)
        hint = render_fit("Sürükle: kaydır   •   Tekerlek: yakınlaştır", 16,
                          (150, 144, 132), 520)
        self.screen.blit(hint, (panel.centerx - hint.get_width() // 2, inner_top + 14))

        # Ağaç çizim alanı (başlığın altı). Çizim buraya kırpılır.
        area = pygame.Rect(panel.x + 28, inner_top + 50,
                           panel.width - 56, panel.height - 108)
        self._tree_area = area
        tf = self._skill_tree_transform(area)
        allocated = SkillTree._ensure_set(p)
        allocatable = set(SkillTree.allocatable_nodes(allocated))

        prev_clip = self.screen.get_clip()
        self.screen.set_clip(area)

        # 1) KENARLAR — her kenar bir kez; sahip olunan iki uç parlar
        drawn = set()
        for nid, neighbors in SkillTree.ADJ.items():
            for m in neighbors:
                key = (nid, m) if nid < m else (m, nid)
                if key in drawn:
                    continue
                drawn.add(key)
                p1 = tf(SkillTree.BY_ID[nid]["pos"])
                p2 = tf(SkillTree.BY_ID[m]["pos"])
                both = nid in allocated and m in allocated
                col = ui_theme.readable(ui_theme.COLORS["gold"]) if both else (68, 60, 56)
                pygame.draw.line(self.screen, col, p1, p2, 4 if both else 2)

        # 2) DÜĞÜMLER — kilitli önce, açık/alınmış en son (tema kuralı: seçili üstte)
        self.tree_node_hit = []
        hover_node = None
        order = sorted(
            SkillTree.NODES,
            key=lambda n: (n["id"] in allocated, n["id"] in allocatable))
        for node in order:
            nid = node["id"]
            cx, cy = tf(node["pos"])
            r = self._tree_node_radius(node["type"])
            rect = pygame.Rect(cx - r, cy - r, 2 * r, 2 * r)
            self.tree_node_hit.append((nid, rect))
            if nid in allocated:
                state = "allocated"
            elif nid in allocatable:
                state = "open"
            else:
                state = "locked"
            self._draw_tree_node(node, (cx, cy), r, state)
            if rect.collidepoint(mouse_pos):
                hover_node = node

        self.screen.set_clip(prev_clip)

        if hover_node:
            self._draw_tree_tooltip(hover_node, mouse_pos, allocated, allocatable)

    def _skill_tree_transform(self, area):
        """Ağaç düğümlerini ekrana çeviren dönüşüm. İlk açılışta ağaç panele
        sığar (fit); sonra kullanıcı sürükleyerek kaydırır, tekerlekle
        yakınlaştırır (bkz. _tree_zoom_at / event döngüsü)."""
        if not hasattr(self, "_tree_bbox"):
            xs = [n["pos"][0] for n in SkillTree.NODES]
            ys = [n["pos"][1] for n in SkillTree.NODES]
            self._tree_bbox = (min(xs), min(ys), max(xs), max(ys))
        minx, miny, maxx, maxy = self._tree_bbox
        bw = max(1, maxx - minx)
        bh = max(1, maxy - miny)
        pad = 48
        fit = min((area.width - 2 * pad) / bw, (area.height - 2 * pad) / bh)
        self._tree_fit_scale = fit
        if not self._tree_view:
            self._tree_view = {
                "scale": fit,
                "ox": area.x + (area.width - bw * fit) / 2 - minx * fit,
                "oy": area.y + (area.height - bh * fit) / 2 - miny * fit,
            }
        v = self._tree_view
        v["scale"] = max(fit * 0.7, min(fit * 4.0, v["scale"]))

        def tf(pos):
            return (int(pos[0] * v["scale"] + v["ox"]), int(pos[1] * v["scale"] + v["oy"]))
        return tf

    def _tree_zoom_at(self, pos, wheel_y):
        """Tekerlekle imlecin ÜSTÜNDEKİ noktayı sabit tutarak yakınlaştırır."""
        v = self._tree_view
        if not v:
            return
        new = max(self._tree_fit_scale * 0.7,
                  min(self._tree_fit_scale * 4.0, v["scale"] * (1.18 ** wheel_y)))
        factor = new / v["scale"] if v["scale"] else 1.0
        cx, cy = pos
        v["ox"] = cx - (cx - v["ox"]) * factor
        v["oy"] = cy - (cy - v["oy"]) * factor
        v["scale"] = new
        self._tree_clamp_view()

    def _tree_clamp_view(self):
        """Ağacın tamamen ekrandan kaybolmasını önler (kenarda pay bırakır)."""
        area, v = self._tree_area, self._tree_view
        if not area or not v or not hasattr(self, "_tree_bbox"):
            return
        minx, miny, maxx, maxy = self._tree_bbox
        s, m = v["scale"], 120
        lo, hi = sorted((area.left + m - maxx * s, area.right - m - minx * s))
        v["ox"] = max(lo, min(hi, v["ox"]))
        lo, hi = sorted((area.top + m - maxy * s, area.bottom - m - miny * s))
        v["oy"] = max(lo, min(hi, v["oy"]))

    def _tree_click_node(self, pos, p):
        """Sürükleme değil de gerçek tık ise imlecin altındaki düğümü tahsis et."""
        for nid, rect in getattr(self, 'tree_node_hit', []):
            if rect.collidepoint(pos):
                ok, msg = SkillTree.allocate(p, nid)
                color = (241, 196, 15) if ok else (231, 76, 60)
                self.logic.add_event("damage_text", p.x, p.y - 60, value=msg, color=color)
                return

    @staticmethod
    def _tree_node_radius(ntype):
        return {"keystone": 19, "notable": 16, "start": 15}.get(ntype, 12)

    def _draw_tree_node(self, node, center, r, state):
        import ui_theme
        cx, cy = center
        base = ui_theme.COLORS[self._TREE_TYPE_COLORS.get(node["type"], "steel")]
        gold = ui_theme.readable(ui_theme.COLORS["gold"])
        if state == "allocated":
            fill = ui_theme.readable(base, 110)
            ring, ring_w = gold, 3
        elif state == "open":
            fill = tuple(c // 3 + 10 for c in base)
            ring, ring_w = gold, 3
        else:  # locked
            fill = (34, 30, 32)
            ring, ring_w = (72, 64, 60), 2

        pygame.draw.circle(self.screen, (16, 14, 16), (cx, cy), r + 3)   # yuva
        pygame.draw.circle(self.screen, fill, (cx, cy), r)
        pygame.draw.circle(self.screen, ring, (cx, cy), r, ring_w)
        # Notable/keystone: parlak iç mücevher noktası
        if node["type"] in ("notable", "keystone") and state != "locked":
            hi = tuple(min(255, c + 60) for c in fill)
            pygame.draw.circle(self.screen, hi, (cx - r // 3, cy - r // 3), max(2, r // 4))

    def _draw_tree_tooltip(self, node, mouse_pos, allocated, allocatable):
        import ui_theme
        nid = node["id"]
        if nid in allocated:
            status = "✓ Alındı"
            scol = ui_theme.readable(ui_theme.COLORS["moss"])
        elif nid in allocatable:
            status = "Başlangıç" if SkillTree.is_start(nid) else "Tıkla → 1 SP"
            scol = ui_theme.readable(ui_theme.COLORS["gold"])
        else:
            status = "🔒 Kilitli — önce bağlı bir düğüm al"
            scol = (170, 120, 120)

        name_s = render_fit(node["name"], 20, ui_theme.readable(ui_theme.COLORS["gold"]), 340, bold=True)
        desc_s = render_fit(node.get("desc", ""), 16, ui_theme.TEXT_COL, 340)
        stat_s = render_fit(status, 16, scol, 340)
        w = max(name_s.get_width(), desc_s.get_width(), stat_s.get_width()) + 32
        h = 84
        tx = min(mouse_pos[0] + 18, self.width - w - 10)
        ty = min(mouse_pos[1] + 18, self.height - h - 10)
        rect = pygame.Rect(tx, ty, w, h)
        ui_theme.draw_panel(self.screen, rect, fill=ui_theme.PANEL_BG, alpha=245)
        self.screen.blit(name_s, (rect.x + 16, rect.y + 10))
        self.screen.blit(desc_s, (rect.x + 16, rect.y + 36))
        self.screen.blit(stat_s, (rect.x + 16, rect.y + 60))

    def reset_skill_tree(self, p):
        """Altın karşılığı tüm ağacı sıfırlar (SP iade edilir). Eski
        reset_skills ile aynı altın maliyeti."""
        wave_level = self.logic.wave.get("level", 1)
        cost = 2000 + max(0, (wave_level - 1) * 400)
        if p.gold < cost:
            return False
        p.gold -= cost
        SkillTree.refund_all(p)
        return True

    # ======================= YÜKSELİŞ (ASCENDANCY) =======================
    def draw_ascendancy_tab(self, p):
        import ui_theme
        from logic.ascendancy import Ascendancy
        panel = self._inventory_panel_rect()
        inner_top = panel.y + 52
        mouse_pos = pygame.mouse.get_pos()
        gold = ui_theme.readable(ui_theme.COLORS["gold"])
        self.ascendancy_node_hit = []

        if not Ascendancy.is_unlocked(p):
            msg = render_fit(
                "Yükseliş (Alt-Sınıf) ağacı Seviye 20'de sınıf evrimini seçince açılır.",
                26, gold, panel.width - 180, bold=True)
            self.screen.blit(msg, (panel.centerx - msg.get_width() // 2, panel.centery - 20))
            hint = render_fit("Seviye 20'den itibaren her seviyede +1 Yükseliş Puanı kazanırsın.",
                              19, (176, 170, 158), panel.width - 180)
            self.screen.blit(hint, (panel.centerx - hint.get_width() // 2, panel.centery + 24))
            return

        # Başlık: alt-sınıf adı + puan + sıfırla
        sub_name = p.EVOLUTIONS.get(p.evolution, {}).get("name", p.evolution)
        title = render_fit(sub_name, 30, gold, 720, bold=True)
        self.screen.blit(title, (panel.centerx - title.get_width() // 2, inner_top + 6))
        pts = render_fit(f"YÜKSELİŞ PUANI: {p.ascendancy_points}", 22,
                         ui_theme.readable(ui_theme.COLORS["arcane"]), 440, bold=True)
        self.screen.blit(pts, (panel.x + 44, inner_top + 12))

        wave_level = self.logic.wave.get("level", 1)
        cost = 1500 + max(0, (wave_level - 1) * 300)
        self.asc_reset_rect = pygame.Rect(panel.right - 250, inner_top + 8, 190, 36)
        rh = self.asc_reset_rect.collidepoint(mouse_pos)
        ui_theme.draw_plate(self.screen, self.asc_reset_rect, "hover" if rh else "normal",
                            ui_theme.COLORS["ember"])
        rt = render_fit(f"SIFIRLA ({cost} G)", 17,
                        ui_theme.TEXT_COL if rh else (176, 170, 158), self.asc_reset_rect.width - 30)
        self.screen.blit(rt, rt.get_rect(center=self.asc_reset_rect.center))

        # Mini ağaç: alt-sınıfın düğümlerini panele sığdır (pan/zoom yok)
        area = pygame.Rect(panel.x + 40, inner_top + 64, panel.width - 80, panel.height - 140)
        nodes = Ascendancy.nodes_for(p.evolution)
        xs = [n["pos"][0] for n in nodes]
        ys = [n["pos"][1] for n in nodes]
        minx, miny, maxx, maxy = min(xs), min(ys), max(xs), max(ys)
        bw, bh = max(1, maxx - minx), max(1, maxy - miny)
        pad = 90
        scale = min((area.width - 2 * pad) / bw, (area.height - 2 * pad) / bh)
        ox = area.x + (area.width - bw * scale) / 2 - minx * scale
        oy = area.y + (area.height - bh * scale) / 2 - miny * scale

        def tf(pos):
            return (int(pos[0] * scale + ox), int(pos[1] * scale + oy))

        allocated = Ascendancy._ensure_set(p)
        allocatable = set(Ascendancy.allocatable_nodes(allocated))

        # Kenarlar
        drawn = set()
        for n in nodes:
            for m in n.get("connects", []):
                if m not in Ascendancy.BY_ID:
                    continue
                key = (n["id"], m) if n["id"] < m else (m, n["id"])
                if key in drawn:
                    continue
                drawn.add(key)
                p1, p2 = tf(n["pos"]), tf(Ascendancy.BY_ID[m]["pos"])
                both = n["id"] in allocated and m in allocated
                pygame.draw.line(self.screen, gold if both else (70, 62, 58), p1, p2, 5 if both else 3)

        # Düğümler (az sayıda -> büyük) + altına isim
        hover = None
        order = sorted(nodes, key=lambda n: (n["id"] in allocated, n["id"] in allocatable))
        for node in order:
            cx, cy = tf(node["pos"])
            r = self._tree_node_radius(node["type"]) + 9
            rect = pygame.Rect(cx - r, cy - r, 2 * r, 2 * r)
            self.ascendancy_node_hit.append((node["id"], rect))
            if node["id"] in allocated:
                state = "allocated"
            elif node["id"] in allocatable:
                state = "open"
            else:
                state = "locked"
            self._draw_tree_node(node, (cx, cy), r, state)
            nm = render_fit(node["name"], 17, ui_theme.TEXT_COL, 200, bold=(node["type"] != "minor"))
            self.screen.blit(nm, (cx - nm.get_width() // 2, cy + r + 5))
            if rect.collidepoint(mouse_pos):
                hover = node

        if hover:
            self._draw_tree_tooltip(hover, mouse_pos, allocated, allocatable)

    def buy_skill(self, p, skill_idx):
        if p.skill_points <= 0: return
        
        sk = p.skills[skill_idx]
        if sk['lvl'] < sk['max']:
            sk['lvl'] += 1
            p.skill_points -= 1
            
            # HP ise anlık canı da artır
            if sk['stat'] == 'max_hp':
                p.hp += sk['val']
            
            p.inv_manager.recalculate_stats()
            print(f"Skill Purchased: {sk['name']}")


    def draw_card_select_screen(self):
        self._overlay_surface.fill((0, 0, 0, 200))
        self.screen.blit(self._overlay_surface, (0, 0))
        
        import ui_theme
        title = ui_theme.render_title("KADERİNİ SEÇ", 52,
                                      ui_theme.readable(ui_theme.COLORS["gold"]))
        tx = self.width // 2 - title.get_width() // 2
        self.screen.blit(title, (tx, 90))
        crest = get_skull_crest(44)
        if crest is not None:
            cy = 90 + title.get_height() // 2 - crest.get_height() // 2
            self.screen.blit(crest, (tx - crest.get_width() - 22, cy))
            self.screen.blit(crest, (tx + title.get_width() + 22, cy))
        
        # 3 Kartı Yan Yana Çiz
        cards = self.logic.pending_cards
        gap = 20 if len(cards) > 3 else 40
        card_w = min(300, (self.width - 80 - gap * (len(cards) - 1)) // max(1, len(cards)))
        card_top = 170
        controls_top = self.height - 230
        card_h = max(280, min(400, controls_top - card_top - 20))
        start_x = self.width // 2 - (len(cards) * card_w + (len(cards)-1) * gap) // 2
        
        m_pos = pygame.mouse.get_pos()
        self.card_rects = []
        for i, card in enumerate(cards):
            cx = start_x + i * (card_w + gap)
            cy = card_top
            rect = pygame.Rect(cx, cy, card_w, card_h)
            self.card_rects.append(rect)
            hovered = rect.collidepoint(m_pos)

            # Kart gövdesi: gotik çerçeve (sınıf kartlarıyla aynı dil)
            gold = ui_theme.COLORS["gold"]
            c = ui_theme.draw_inset_frame(
                self.screen, rect, "panel_frame_small.png",
                fill=(32, 27, 24) if hovered else (24, 21, 28), alpha=246,
                tint=tuple(int(v * (0.42 if hovered else 0.26)) for v in gold),
                glow=(ui_theme.readable(gold), 120) if hovered else None, pad=22)

            c_name = render_fit(card["name"], 24,
                                ui_theme.TEXT_COL if hovered else (206, 199, 184),
                                c.width, bold=True)
            self.screen.blit(c_name, (c.centerx - c_name.get_width() // 2, c.y))

            category, category_color = CARD_CATEGORY_LABELS.get(
                card.get('category'), ('KART', (160, 160, 170))
            )
            category_txt = render_fit(category, 18, ui_theme.readable(category_color), c.width)
            y_cat = c.y + c_name.get_height() + 6
            self.screen.blit(category_txt, category_txt.get_rect(midtop=(c.centerx, y_cat)))

            # Açıklama
            self.draw_text_wrapped(card["desc"], c.x, y_cat + category_txt.get_height() + 12,
                                   c.width, (208, 202, 190), self.font_desc)

            # Sinerji İpucu
            if hasattr(self.logic.card_system, 'synergy_system'):
                test_cards = self.logic.card_system.active_cards + [card["id"]]
                active_syns = getattr(self.logic.card_system.synergy_system, 'active_synergies', [])
                for syn in getattr(self.logic.card_system.synergy_system, 'SYNERGIES', []):
                    if syn['id'] not in active_syns and all(k in test_cards for k in syn['required_cards']):
                        hint_txt = render_fit(f"Sinerji Sağlar: {syn['name']}", 18,
                                              ui_theme.readable(ui_theme.COLORS["moss"]), c.width)
                        self.screen.blit(hint_txt, (c.x, c.bottom - hint_txt.get_height()))
                        break

        # Yenile (Reroll) ve Kart Alma butonları (tema: banner)
        rerolls = getattr(self.logic, 'card_rerolls', 0)
        self.card_reroll_rect = pygame.Rect(self.width // 2 - 150, self.height - 230, 300, 60)
        rr_state = "disabled" if rerolls <= 0 else (
            "hover" if self.card_reroll_rect.collidepoint(m_pos) else "normal")
        surf, over = ui_theme.render_banner_button(
            300, 60, f"YENİLE (Kalan: {rerolls})", ui_theme.COLORS["night"], state=rr_state, skull=False)
        self.screen.blit(surf, (self.card_reroll_rect.centerx - surf.get_width() // 2,
                                self.card_reroll_rect.y - over))

        self.card_skip_rect = pygame.Rect(self.width // 2 - 150, self.height - 150, 300, 60)
        sk_state = "hover" if self.card_skip_rect.collidepoint(m_pos) else "normal"
        surf, over = ui_theme.render_banner_button(
            300, 60, "KART ALMA (+1 SEVİYE)", ui_theme.COLORS["ember"], state=sk_state, skull=False)
        self.screen.blit(surf, (self.card_skip_rect.centerx - surf.get_width() // 2,
                                self.card_skip_rect.y - over))

    def draw_evolution_select_screen(self):
        p = self.logic.players[self.logic.local_player_id]
        class_id = getattr(p, 'class_id', 'warrior')

        # Bu sınıfa ait 2 evrimi bul
        from entities.player import Player
        evos = [(eid, edata) for eid, edata in Player.EVOLUTIONS.items()
                if edata.get("class_base") == class_id]

        self._overlay_surface.fill((0, 0, 0, 220))
        self.screen.blit(self._overlay_surface, (0, 0))

        import ui_theme
        title = ui_theme.render_title("SINIF EVRİMİ — YOLUNU SEÇ", 48,
                                      ui_theme.readable(ui_theme.COLORS["gold"]))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 56))

        sub = render_fit(f"Mevcut Sınıf: {p.class_name} → Level 20", 24,
                         (196, 190, 178), self.width - 200)
        self.screen.blit(sub, (self.width // 2 - sub.get_width() // 2, 118))

        # 2 yolu yan yana göster
        card_w, card_h = 500, 380
        total_w = len(evos) * card_w + (len(evos) - 1) * 60
        start_x = self.width // 2 - total_w // 2
        card_y = 170

        self.evo_rects = []
        self.evo_btn_rects = []   # SEÇ butonları da tıklanabilir olsun
        mouse_pos = pygame.mouse.get_pos()

        for i, (evo_id, evo_data) in enumerate(evos):
            cx = start_x + i * (card_w + 60)
            rect = pygame.Rect(cx, card_y, card_w, card_h)
            self.evo_rects.append((rect, evo_id))

            hovered = rect.collidepoint(mouse_pos)
            gold = ui_theme.COLORS["gold"]
            moss = ui_theme.readable(ui_theme.COLORS["moss"])
            blood = ui_theme.readable(ui_theme.COLORS["blood"])
            c = ui_theme.draw_inset_frame(
                self.screen, rect, "panel_frame_small.png",
                fill=(34, 28, 22) if hovered else (24, 21, 28), alpha=246,
                tint=tuple(int(v * (0.46 if hovered else 0.26)) for v in gold),
                glow=(ui_theme.readable(gold), 130) if hovered else None, pad=26)

            # İsim
            ntxt = render_fit(evo_data["name"], 26, ui_theme.readable(gold), c.width, bold=True)
            self.screen.blit(ntxt, (c.centerx - ntxt.get_width() // 2, c.y))

            # Açıklama (dönen alt y ile statlar üstüne binmiyor)
            y_stat = self.draw_text_wrapped(evo_data["desc"], c.x, c.y + ntxt.get_height() + 10,
                                            c.width, (208, 202, 190), self.font_desc) + 12

            # Stat bonusları
            for stat, val in list(evo_data["stats"].items())[:6]:
                sign = "+" if val >= 0 else ""
                s_txt = render_fit(f"{sign}{val:.1f} {stat}", 18, moss, c.width)
                self.screen.blit(s_txt, (c.x, y_stat))
                y_stat += 26

            # Max HP delta
            delta = evo_data.get("max_hp_delta", 0)
            if delta != 0:
                col = moss if delta > 0 else blood
                dtxt = render_fit(f"{'+' if delta > 0 else ''}{delta} Max HP", 18, col, c.width)
                self.screen.blit(dtxt, (c.x, y_stat))
                y_stat += 26

            # SEÇ butonu önce konumlanır, pasif satırı onun ÜSTÜNE yazılır
            # (eskiden buton kartın 15px altına taşıyordu)
            btn = pygame.Rect(c.centerx - 85, c.bottom - 42, 170, 40)
            self.evo_btn_rects.append((btn, evo_id))
            pasif_txt = render_fit(f"Pasif: {evo_data.get('passive', '')}", 18,
                                   ui_theme.readable(ui_theme.COLORS["arcane"]), c.width)
            self.screen.blit(pasif_txt, (c.x, btn.y - pasif_txt.get_height() - 8))

            btn_hover = btn.collidepoint(mouse_pos)
            ui_theme.draw_plate(self.screen, btn, "hover" if (hovered or btn_hover) else "normal",
                                ui_theme.COLORS["gold"])
            btxt = render_fit("SEÇ", 19,
                              ui_theme.TEXT_COL if (hovered or btn_hover) else (176, 170, 158),
                              btn.width - 34, bold=hovered)
            self.screen.blit(btxt, btxt.get_rect(center=btn.center))

    def draw_game_over_screen(self):
        # Overlay
        self._overlay_surface.fill((50, 0, 0, 200))
        self.screen.blit(self._overlay_surface, (0, 0))
        
        # Title
        import ui_theme
        title = ui_theme.render_title("ÖLDÜN", 64,
                                      ui_theme.readable(ui_theme.COLORS["blood"]))
        t_rect = title.get_rect(center=(self.width // 2, self.height // 2 - 215))
        self.screen.blit(title, t_rect)
        crest = get_skull_crest(52)
        if crest is not None:
            self.screen.blit(crest, (t_rect.left - crest.get_width() - 24,
                                     t_rect.centery - crest.get_height() // 2))
            self.screen.blit(crest, (t_rect.right + 24,
                                     t_rect.centery - crest.get_height() // 2))
        
        # --- MAÇ SONU TELEMETRİSİ ---
        # Değerler GameLogic.get_run_summary()'den gelir (tek kaynak); ekran
        # kendi hesabını yapmaz, yoksa gösterilen sayı ile gerçek ayrışabilir.
        summary = self.logic.get_run_summary()
        panel_w, row_h = 620, 30
        rows = (len(summary) + 1) // 2          # iki sütun
        panel_h = rows * row_h + 34
        # y: başlığın ALTINDA başlar. draw_panel çerçeveyi rect'in DIŞINA
        # çizdiği için (DESIGN.md) rect'i başlığa yaslamak çerçeveyi başlığın
        # üstüne bindiriyordu.
        panel = pygame.Rect(self.width // 2 - panel_w // 2,
                            self.height // 2 - 120, panel_w, panel_h)
        ui_theme.draw_panel(self.screen, panel, alpha=215)

        col_w = (panel_w - 60) // 2
        for i, (label, value, strong) in enumerate(summary):
            col, row = i % 2, i // 2
            x = panel.x + 30 + col * col_w
            y = panel.y + 18 + row * row_h
            lbl = render_fit(label, 19, (150, 143, 130), col_w - 110)
            self.screen.blit(lbl, (x, y))
            val_col = ui_theme.readable(ui_theme.COLORS["gold"]) if strong else (222, 216, 202)
            val = render_fit(str(value), 20, val_col, col_w - 14, bold=strong)
            self.screen.blit(val, (x + col_w - 14 - val.get_width(), y - 1))


        # Buttons - hitbox tek kaynak: rect saklanır
        # Buton panelin ALTINDAN konumlanır: özet satır sayısı değişince
        # sabit y ile üst üste biniyordu.
        # +70: draw_panel çerçevesi rect'in dışına ~52px taşıyor, +26 boşluk
        # butonu alt çerçevenin üstüne bindiriyordu.
        restart_rect = pygame.Rect(self.width // 2 - 200, panel.bottom + 70, 400, 60)
        self.game_over_restart_rect = restart_rect
        
        # Hover Kontrolü
        m_pos = pygame.mouse.get_pos()

        # Yeniden Başla (tema: banner buton + kurukafa)
        r_state = "hover" if restart_rect.collidepoint(m_pos) else "normal"
        surf, over = ui_theme.render_banner_button(
            400, 60, "ANA MENÜYE DÖN", ui_theme.COLORS["ember"], state=r_state, skull=True)
        self.screen.blit(surf, (restart_rect.centerx - surf.get_width() // 2, restart_rect.y - over))
        
        # Bilgi
        info = render_fit("Sıradaki Dalga Seni Bekliyor!", 20, (176, 170, 158), 520)
        self.screen.blit(info, (self.width // 2 - info.get_width() // 2, self.height // 2 + 160))

    def _aura_layout(self):
        """Aura sekmesinin panel/kart/sayfalama geometrisi (tek kaynak)."""
        panel = self._inventory_panel_rect()
        inner = pygame.Rect(panel.x + 60, panel.y + 58,
                            panel.width - 120, panel.height - 116)
        essence = pygame.Rect(inner.x, inner.y, inner.width, 170)
        shrine = pygame.Rect(inner.x, essence.bottom + 16,
                             inner.width, inner.bottom - essence.bottom - 16)
        card_w = (shrine.width - 60) // 2
        return essence, shrine, card_w

    def draw_aura_tab(self, p):
        import ui_theme
        essence_panel, aura_panel, card_w = self._aura_layout()
        mouse_pos = pygame.mouse.get_pos()
        arcane = ui_theme.readable(ui_theme.COLORS["arcane"])
        gold = ui_theme.readable(ui_theme.COLORS["gold"])

        # 1. ESSENCE (ÖZ) PANELİ
        # Çerçeve tonunda HAM palet rengi kullanılır; readable() metin içindir
        # ve panel çerçevesine uygulanınca taş dokuyu pembeye boyuyor.
        e_content = ui_theme.draw_inset_frame(
            self.screen, essence_panel, "panel_frame_small.png",
            fill=(26, 21, 32), alpha=244,
            tint=tuple(int(c * 0.30) for c in ui_theme.COLORS["arcane"]), pad=22)

        title_e = render_fit("Kalıcı Öz İstatistikleri (Ascension)", 24, arcane,
                             e_content.width, bold=True)
        self.screen.blit(title_e, (e_content.x, e_content.y))

        if not p.is_essence_system_unlocked:
            lock_t = render_fit("KİLİTLİ: Bu sistem 10. Wave Boss'u kesildiğinde aktifleşir.",
                                19, (154, 148, 138), e_content.width)
            self.screen.blit(lock_t, (e_content.x, e_content.y + 38))
        else:
            stats = [
                f"Max HP: +{p.essence_stats['max_hp']}",
                f"Fiziksel Hasar: +{p.essence_stats['phys_dmg']}",
                f"Büyü Hasarı: +{int(p.essence_stats['element_dmg']*100)}%",
                f"Zırh: +{p.essence_stats['armor']}",
                f"Hız: +{round(p.essence_stats['speed'], 1)}"
            ]
            col_w = e_content.width // 3
            for i, st in enumerate(stats):
                txt = render_fit(st, 19, ui_theme.TEXT_COL, col_w - 16)
                self.screen.blit(txt, (e_content.x + (i % 3) * col_w,
                                       e_content.y + 38 + (i // 3) * 34))

        # 2. AURA SHRINE
        a_content = ui_theme.draw_inset_frame(
            self.screen, aura_panel, "panel_frame_small.png",
            fill=(22, 19, 26), alpha=244,
            tint=tuple(int(c * 0.30) for c in ui_theme.COLORS["gold"]), pad=22)

        limit_t = render_fit(f"Mistik Aura Tapınağı (Aktif: {len(p.active_auras)}/{p.aura_limit})",
                             24, gold, a_content.width, bold=True)
        self.screen.blit(limit_t, (a_content.x, a_content.y))

        from logic.aura_system import AuraManager
        aura_mgr = AuraManager()
        all_auras = aura_mgr.get_all_auras()

        # Sayfalama alanı önce ayrılır, kartlar kalan yüksekliği paylaşır
        pager_h = 34
        grid_top = a_content.y + 38
        grid_bottom = a_content.bottom - pager_h - 10
        card_h = max(70, (grid_bottom - grid_top) // 4 - 10)

        self.aura_btn_rects = []
        offset = self.aura_page * 8
        for i in range(8):
            idx = offset + i
            if idx >= len(all_auras): break

            aura = all_auras[idx]
            ax = a_content.x + (i % 2) * (card_w + 20)
            ay = grid_top + (i // 2) * (card_h + 10)
            card_rect = pygame.Rect(ax, ay, card_w, card_h)
            is_active = aura.id in p.active_auras
            owned = aura.id in p.purchased_auras

            tint_col = ui_theme.COLORS["moss"] if is_active else (
                ui_theme.COLORS["night"] if owned else ui_theme.COLORS["steel"])
            c = ui_theme.draw_inset_frame(
                self.screen, card_rect, "panel_frame_small.png",
                fill=(32, 28, 38) if is_active else (26, 23, 31), alpha=244,
                tint=tuple(int(v * 0.30) for v in tint_col), pad=14)

            # Buton önce konumlanır, metin genişliği ondan türetilir
            btn_w = 104
            btn_rect = pygame.Rect(c.right - btn_w, c.centery - 19, btn_w, 38)
            self.aura_btn_rects.append((idx, btn_rect))
            text_w = max(80, btn_rect.left - c.x - 16)

            name_t = render_fit(aura.name, 21, gold, text_w, bold=True)
            self.screen.blit(name_t, (c.x, c.y))
            self.draw_text_wrapped(aura.description, c.x, c.y + name_t.get_height() + 4,
                                   text_w, (188, 182, 170), self.font_desc)

            hovered = btn_rect.collidepoint(mouse_pos)
            if owned:
                key = "moss" if is_active else "night"
                label = "AKTİF" if is_active else "KUŞAN"
            else:
                key = "gold"
                label = f"{aura.cost // 1000}K G"
            ui_theme.draw_plate(self.screen, btn_rect,
                                "hover" if (hovered or is_active) else "normal",
                                ui_theme.COLORS[key])
            txt = render_fit(label, 17,
                             ui_theme.TEXT_COL if (hovered or is_active) else (176, 170, 158),
                             btn_rect.width - 30, bold=is_active)
            self.screen.blit(txt, txt.get_rect(center=btn_rect.center))

        # Aura Kilitli Overlay
        if not p.is_essence_system_unlocked:
            if not hasattr(self, '_lock_overlay') or self._lock_overlay.get_size() != aura_panel.size:
                self._lock_overlay = pygame.Surface(aura_panel.size, pygame.SRCALPHA)
            self._lock_overlay.fill((0, 0, 0, 185))
            self.screen.blit(self._lock_overlay, aura_panel)
            lock_msg = render_fit("TAPINAK KİLİTLİ: Önce Wave 10 Boss'unu Yenmelisin!", 24,
                                  ui_theme.readable(ui_theme.COLORS["blood"]),
                                  aura_panel.width - 60, bold=True)
            self.screen.blit(lock_msg, lock_msg.get_rect(center=aura_panel.center))

        # Sayfalama Butonları - hitbox tek kaynak: rect'ler saklanır
        pager_y = a_content.bottom - pager_h
        self.aura_prev_rect = pygame.Rect(a_content.centerx - 96, pager_y, 88, pager_h)
        self.aura_next_rect = pygame.Rect(a_content.centerx + 8, pager_y, 88, pager_h)
        for rect, label, enabled in (
                (self.aura_prev_rect, "<< GERİ", self.aura_page > 0),
                (self.aura_next_rect, "İLERİ >>", (self.aura_page + 1) * 8 < len(all_auras))):
            if not enabled:
                continue
            hovered = rect.collidepoint(mouse_pos)
            ui_theme.draw_plate(self.screen, rect, "hover" if hovered else "normal",
                                ui_theme.COLORS["night"])
            # Metin rect'in MERKEZİNE (eskiden gözle hizalanmış sabit x'teydi)
            txt = render_fit(label, 16,
                             ui_theme.TEXT_COL if hovered else (176, 170, 158),
                             rect.width - 30)
            self.screen.blit(txt, txt.get_rect(center=rect.center))

    def draw_synergy_tab(self, p):
        import ui_theme
        panel = self._inventory_panel_rect()
        inner = pygame.Rect(panel.x + 60, panel.y + 58,
                            panel.width - 120, panel.height - 116)
        gold = ui_theme.readable(ui_theme.COLORS["gold"])
        moss = ui_theme.readable(ui_theme.COLORS["moss"])

        title = ui_theme.render_title("SİNERJİ REHBERİ", 34, gold)
        self.screen.blit(title, (inner.centerx - title.get_width() // 2, inner.y))
        y = inner.y + title.get_height() + 10

        synergies = getattr(self.logic.card_system.synergy_system, 'SYNERGIES', [])
        active_synergies = getattr(self.logic.card_system.synergy_system, 'active_synergies', [])
        active_names = self.logic.card_system.get_active_card_names()

        cards_title = render_fit(f"Sahip Olduğun Kartlar ({len(active_names)} Adet):",
                                 21, (196, 190, 178), inner.width, bold=True)
        self.screen.blit(cards_title, (inner.x, y))
        y += cards_title.get_height() + 4

        cards_text = " • ".join(active_names) if active_names else "Henüz kart alınmadı."
        y = self.draw_text_wrapped(cards_text, inner.x, y, inner.width, moss, self.font_desc) + 12

        # Liste ekrana sığmıyor: kaydırılabilir alan (eskiden ızgara sınırsız
        # büyüyüp panelin altından taşıyordu).
        view = pygame.Rect(inner.x, y, inner.width, inner.bottom - y - 24)
        col_w = (inner.width - 20) // 2
        card_h = 115
        rows = (len(synergies) + 1) // 2
        self._synergy_max_scroll = max(0, rows * (card_h + 10) - view.height)

        card_names = {card['id']: card['name'] for card in self.logic.card_system.CARDS}
        prev_clip = self.screen.get_clip()
        self.screen.set_clip(view)

        for i, syn in enumerate(synergies):
            is_active = syn['id'] in active_synergies
            x = inner.x + (i % 2) * (col_w + 20)
            cy = view.y + (i // 2) * (card_h + 10) + self.synergy_scroll
            if cy > view.bottom or cy + card_h < view.y:
                continue  # görünmeyeni çizme

            rect = pygame.Rect(x, cy, col_w, card_h)
            tint_col = ui_theme.COLORS["moss"] if is_active else ui_theme.COLORS["steel"]
            c = ui_theme.draw_inset_frame(
                self.screen, rect, "panel_frame_small.png",
                fill=(28, 34, 29) if is_active else (26, 23, 30), alpha=244,
                tint=tuple(int(v * (0.34 if is_active else 0.18)) for v in tint_col),
                pad=14)

            # Kartın ÜST ve ALT satırları çerçevenin köşe taşları hizasında;
            # bu iki satır yatayda ek pay alır, ortadaki açıklama tam genişlik.
            edge = 18
            ex, ew = c.x + edge, c.width - edge * 2

            status_str = "AKTİF!" if is_active else "KEŞFEDİLMEDİ"
            status_txt = render_fit(status_str, 19, moss if is_active else (140, 134, 124),
                                    ew // 2, bold=is_active)
            self.screen.blit(status_txt, (ex + ew - status_txt.get_width(), c.y))

            name_txt = render_fit(syn['name'], 20, gold if is_active else (156, 150, 140),
                                  ew - status_txt.get_width() - 12, bold=True)
            self.screen.blit(name_txt, (ex, c.y))

            dy = self.draw_text_wrapped(
                syn['desc'], c.x, c.y + name_txt.get_height() + 4, c.width,
                (208, 202, 190) if is_active else (132, 127, 118), self.font_desc)

            req_str = "Gereken: " + " + ".join(card_names.get(k, k) for k in syn['required_cards'])
            self.draw_text_wrapped(
                req_str, ex, min(dy + 2, c.bottom - self.font_desc.get_height()),
                ew, (172, 166, 154) if is_active else (110, 106, 98),
                self.font_desc)

        self.screen.set_clip(prev_clip)

        if self._synergy_max_scroll > 0:
            hint = render_fit("Tekerlek: Kaydır", 16, (150, 144, 132), 240)
            self.screen.blit(hint, (inner.right - hint.get_width(), inner.bottom - 20))

    def draw_text_wrapped(self, text, x, y, max_width, color, font):
        """Metni max_width'e bölerek çizer ve bloğun ALT y'sini döndürür.

        Dönen değer olmadan çağıranlar sonraki içeriği sabit bir y'ye koyuyor,
        metin iki satıra çıkınca üstüne biniyordu.
        """
        text = strip_unsupported(text)   # fontta olmayan emoji -> □ olmasın
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        line_h = font.get_height() + 2
        for i, line in enumerate(lines):
            l_surf = font.render(line, True, color)
            self.screen.blit(l_surf, (x, y + i * line_h))
        return y + len(lines) * line_h


    def update_aura_clicks(self, pos, p):
        if not p.is_essence_system_unlocked: return False

        from logic.aura_system import AuraManager
        aura_mgr = AuraManager()
        all_auras = aura_mgr.get_all_auras()

        # Çizimde saklanan rect'ler kullanılır (tek kaynak)
        for idx, btn_rect in getattr(self, 'aura_btn_rects', []):
            aura = all_auras[idx]
            if btn_rect.collidepoint(pos):
                if aura.id in p.purchased_auras:
                    # KUŞAN / ÇIKAR
                    p.toggle_aura(aura.id)
                else:
                    # SATIN AL
                    if p.gold >= aura.cost:
                        p.gold -= aura.cost
                        p.purchased_auras.append(aura.id)
                        self.logic.add_event("damage_text", p.x, p.y-40, value="Aura Açıldı!", color=(241, 196, 15))
                    else:
                        self.logic.add_event("damage_text", p.x, p.y-40, value="Altın Yetersiz!", color=(231, 76, 60))
                return True
        
        # Sayfalama (çizimde saklanan rect'ler)
        prev_r = getattr(self, 'aura_prev_rect', None)
        next_r = getattr(self, 'aura_next_rect', None)
        if prev_r and prev_r.collidepoint(pos) and self.aura_page > 0:
            self.aura_page -= 1; return True
        if next_r and next_r.collidepoint(pos) and (self.aura_page + 1) * 8 < len(all_auras):
            self.aura_page += 1; return True
        return False
