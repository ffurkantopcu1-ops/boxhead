from scenes.base_scene import BaseScene
from logic.game_logic import GameLogic
from entities.player import Player
from ui_elements import TabButton, EquippedRow, BackpackItemCard, SkillButton, MarketCard, render_fit, shrink_to_width
import pygame
import math
import time
import random
import sys

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
    'dmgMult': 'Tüm doğrudan ve element saldırılarının hasarını artırır.',
    'meleeRange': 'Yakın dövüş saldırılarının erişim mesafesini artırır.',
    'physDmgFlat': 'Her fiziksel vuruşa sabit hasar ekler.',
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
    'speed': 'Temel hareket hızını artırır.',
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
    'minionMaxHp': 'Minyonların maksimum canını artırır.',
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
        
        # Midnight Slate: Göz yormayan, mermilerin net göründüğü modern koyu tema
        self.tile_size = 128
        # Warm Stone Theme: Daha koyu, gözü yormayan sıcak gri tonu
        self.tile_size = 128
        self.floor_color_1 = (140, 135, 125)
        self.floor_color_2 = (140, 135, 125)
        self.grid_line_color = (110, 105, 95)
        self.font_main = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_sub = pygame.font.SysFont("Arial", 24)
        self.font_desc = pygame.font.SysFont("Arial", 18)
        self.active_tab = "inventory" # inventory, hero, skills, market, aura
        
        # Aura & Essence UI State
        self.aura_page = 0
        self.aura_msg = ""
        self.aura_msg_timer = 0
        
        # Market & Crafting States
        self.market_tab = "items" # "items" or "orbs"
        self.show_craft_window = False
        self.show_inventory = False 
        self.show_stats_panel = False
        self.crafting_target = None
        
        # Blood Moon Filter
        self.blood_moon_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.blood_moon_surf.fill((200, 0, 0, 45)) 

        # --- PERF: Preallocate Surfaces & Fonts ---
        self._overlay_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._sweep_surface = pygame.Surface((3840, 2160), pygame.SRCALPHA)
        self.font_combo = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_boss_name = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_boss_hp = pygame.font.SysFont("Arial", 16, bold=True)
        
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
        self.tab_buttons = [
            TabButton(self.width // 2 - 475, 40, 150, 50, "ENVANTER", "inventory"),
            TabButton(self.width // 2 - 315, 40, 150, 50, "KAHRAMAN", "hero"),
            TabButton(self.width // 2 - 155, 40, 150, 50, "YETENEK", "skills"),
            TabButton(self.width // 2 + 5, 40, 150, 50, "KERVAN", "market"),
            TabButton(self.width // 2 + 165, 40, 150, 50, "AURA", "aura"),
            TabButton(self.width // 2 + 325, 40, 150, 50, "SİNERJİ", "synergy")
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
        self.diff_btn_rects = []
        diff_names = ["Normal", "Hard", "Very Hard", "Impossible"]
        for i, name in enumerate(diff_names):
            self.diff_btn_rects.append(pygame.Rect(self.width // 2 - 280 + i * 140, 570, 130, 40))

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
        self.filter_rects = []
        filter_start_x = self.width // 2 + 20
        filter_gap = 4
        filter_available = self.width - filter_start_x - 20
        filter_width = min(110, (filter_available - filter_gap * 5) // 6)
        for i in range(10): # 2 satır x 5 sütun
            row = i // 5
            col = i % 5
            self.filter_rects.append(pygame.Rect(
                filter_start_x + col * (filter_width + filter_gap),
                110 + row * 40,
                filter_width,
                35,
            ))
            
        # Toplu Satış Butonları (SAĞ ALT)
        self.mass_sell_btns = [
            {"label": "NORMAL SAT", "rarity": "Normal", "color": (150, 150, 150)},
            {"label": "MAGIC SAT", "rarity": "Magic", "color": (52, 152, 219)},
            {"label": "RARE SAT", "rarity": "Rare", "color": (241, 196, 15)},
            {"label": "ÖZLERİ TÜKET", "action": "consume_essences", "color": (155, 89, 182)}
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
        
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True
            
            if (
                event.type == pygame.MOUSEWHEEL
                and not self.show_inventory
                and not self.show_settings
                and self.logic.state == "PLAYING"
            ):
                # Zoom hızı ve limitleri
                self.target_zoom += event.y * 0.1
                self.target_zoom = max(self.min_zoom, min(self.max_zoom, self.target_zoom))

            if event.type == pygame.KEYDOWN:
                # ESC: Menüyü aç/kapat
                if event.key == pygame.K_ESCAPE:
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
                        if event.key == pygame.K_UP: self.selected_setting_idx = (self.selected_setting_idx - 1) % 8
                        elif event.key == pygame.K_DOWN: self.selected_setting_idx = (self.selected_setting_idx + 1) % 8
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
                                if hasattr(self.logic.save_manager, 'delete_save'):
                                    self.logic.save_manager.delete_save(slot['filename'])
                                else:
                                    import os
                                    try: os.remove(f"saves/{slot['filename']}.json")
                                    except: pass
                                self.save_slots = self.logic.save_manager.get_save_slots()
                                if self.selected_setting_idx >= len(self.save_slots): self.selected_setting_idx = max(0, len(self.save_slots)-1)
                            elif event.key == pygame.K_x:
                                for s in self.save_slots:
                                    if hasattr(self.logic.save_manager, 'delete_save'):
                                        self.logic.save_manager.delete_save(s['filename'])
                                    else:
                                        import os
                                        try: os.remove(f"saves/{s['filename']}.json")
                                        except: pass
                                self.save_slots = []
                                self.selected_setting_idx = 0
                    continue

                # --- OYUN İÇİ DİĞER KONTROLLER (Sadece menü kapalıyken) ---
                if not self.show_settings:
                    if event.key in (pygame.K_TAB, pygame.K_i) and self.logic.state == "PLAYING":
                        self.show_inventory = not self.show_inventory
                    if event.key == pygame.K_c and self.logic.state == "PLAYING" and not self.show_inventory:
                        self.show_stats_panel = not self.show_stats_panel
                    if event.key == pygame.K_f:
                        self._toggle_auto_sell(p)
                    if event.key == pygame.K_z:
                        p.auto_attack = not p.auto_attack
                    if event.key == pygame.K_q:
                        p.use_artifact(self.logic)
                    if event.key == pygame.K_r:
                        self._use_blood_absorb(p)
                    if event.key == pygame.K_SPACE and not self.show_inventory:
                        p.dash()

        # --- 2. AYARLAR MENÜSÜ FARE KONTROLÜ (MOUSE) ---
        settings_was_open = self.show_settings
        if settings_was_open:
            panel = pygame.Rect(self.width // 2 - 250, self.height // 2 - 250, 500, 500)
            if mouse_clicked and not panel.collidepoint(mouse_pos):
                self.show_settings = False
            
            if self.setting_tab == "main":
                for i in range(8):
                    opt_rect = pygame.Rect(self.width // 2 - 200, panel.y + 100 + i * 50 - 15, 400, 40)
                    if opt_rect.collidepoint(mouse_pos):
                        self.selected_setting_idx = i
                        if mouse_clicked: self._trigger_setting_action(i)
            elif self.setting_tab == "save":
                for i in range(2):
                    opt_rect = pygame.Rect(self.width // 2 - 200, panel.y + 150 + i * 80 - 20, 400, 60)
                    if opt_rect.collidepoint(mouse_pos):
                        self.selected_setting_idx = i
                        if mouse_clicked:
                            if i == 0:
                                name = f"save_{len(self.logic.save_manager.get_save_slots()) + 1}"
                                self.logic.save_manager.save_game(self.logic, name)
                            else: self.logic.save_manager.save_game(self.logic, "last_save")
                            self.setting_tab = "main"
            elif self.setting_tab == "load":
                for i, slot in enumerate(self.save_slots):
                    opt_rect = pygame.Rect(self.width // 2 - 250, panel.y + 110 + i * 55 - 20, 500, 40)
                    if opt_rect.collidepoint(mouse_pos):
                        self.selected_setting_idx = i
                        if mouse_clicked:
                            self.logic.save_manager.load_game(self.logic, slot['filename'])
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
        if self.show_inventory and mouse_clicked:
            self._handle_inventory_mouse(p, mouse_pos)
            return
            
        # --- 4. GAME OVER FARE KONTROLÜ ---
        if self.logic.state == "GAMEOVER" and mouse_clicked:
            self._handle_game_over_mouse(mouse_pos)
            
        # --- 5. KART VE EVRİM SEÇİM FARE KONTROLÜ ---
        if self.logic.state == "CARD_SELECT" and mouse_clicked:
            if hasattr(self, 'card_rects'):
                for i, rect in enumerate(self.card_rects):
                    if rect.collidepoint(mouse_pos):
                        card = self.logic.pending_cards[i]
                        self.logic.card_system.apply_card(card["id"], p)
                        self.logic.state = "PLAYING"
                        self.logic.pending_cards = []
                        break
                        
            if hasattr(self, 'card_skip_rect') and self.card_skip_rect.collidepoint(mouse_pos):
                p.level += 1
                p.skill_points += 1
                self.logic.state = "PLAYING"
                self.logic.pending_cards = []
            
            if hasattr(self, 'card_reroll_rect') and self.card_reroll_rect.collidepoint(mouse_pos):
                if getattr(self.logic, 'card_rerolls', 0) > 0:
                    self.logic.card_rerolls -= 1
                    cards = self.logic.card_system.offer_cards()
                    if cards:
                        self.logic.pending_cards = cards
                        
        if self.logic.state == "EVOLUTION_SELECT" and mouse_clicked:
            if hasattr(self, 'evo_rects'):
                for rect, evo_id in self.evo_rects:
                    if rect.collidepoint(mouse_pos):
                        p.apply_evolution(evo_id)
                        self.logic.state = "PLAYING"
                        break

    def _handle_game_over_mouse(self, pos):
        # "Yeniden Başla" butonu (çizimde saklanan rect kullanılır)
        restart_rect = getattr(self, 'game_over_restart_rect', None) or \
            pygame.Rect(self.width // 2 - 200, self.height // 2 + 80, 400, 60)

        if restart_rect.collidepoint(pos):
            self.manager.change_scene("MainMenu") # New Game için geri at


    def _trigger_setting_action(self, idx):
        if idx == 0:
            self.logic.settings['shake'] = not self.logic.settings['shake']
            self.manager.global_settings['shake'] = self.logic.settings['shake']
            self.manager.save_settings()
        elif idx == 1:
            self.manager.cycle_display_mode()
        elif idx == 2:
            self.logic.cheat_mode = not self.logic.cheat_mode
            status = "AÇIK" if self.logic.cheat_mode else "KAPALI"
            self.logic.add_event("damage_text", self.width//2, self.height//2, value=f"HİLE MODU: {status}", color=(241, 196, 15), timer=1.5)
        elif idx == 3: self.setting_tab = "save"; self.selected_setting_idx = 0
        elif idx == 4:
            self.save_slots = self.logic.save_manager.get_save_slots()[:5]
            self.setting_tab = "load"; self.selected_setting_idx = 0
        elif idx == 5:
            self.logic.save_manager.save_game(self.logic, "last_save")
            self.manager.change_scene("MainMenu")
        elif idx == 6: self.manager.change_scene("MainMenu")
        elif idx == 7: self.show_settings = False

    def _toggle_auto_sell(self, p):
        modes = ["KAPALI", "BEYAZ", "MAVİ", "SARI", "TÜMÜ"]
        p.auto_sell_mode = (getattr(p, 'auto_sell_mode', 0) + 1) % 5
        m_str = modes[p.auto_sell_mode]
        self.logic.add_event("damage_text", p.x, p.y-80, value=f"OTO-SATIŞ: {m_str}", color=(241, 196, 15), timer=1.0)

    def _use_blood_absorb(self, p):
        # class_name evrimle değişir; kalıcı kimlik class_id'dir (Bloodwalker Q evrim sonrası da çalışsın)
        if getattr(p, 'class_id', '') == "bloodwalker" and hasattr(p.specialization, 'activate_blood_absorb'):
            if p.specialization.activate_blood_absorb(p):
                self.logic.add_event("damage_text", p.x, p.y - 60, value="KAN EMME!", color=(255, 50, 50), timer=1.0)

    def _handle_inventory_mouse(self, p, pos):
        # 1. CRAFTİNG PENCERESİ AÇIKSA (Öncelikli)
        if self.show_craft_window:
            panel = pygame.Rect(self.width // 2 - 450, self.height // 2 - 300, 900, 600)
            
            # Kapatma Butonu
            close_btn = pygame.Rect(panel.right - 50, panel.y + 10, 40, 40)
            if close_btn.collidepoint(pos):
                self.show_craft_window = False
                return

            # ORB SATIN ALMA (Dükkan - Sağ)
            market_list = self.logic.orb_market
            offset_m = self.orb_market_page * 5
            for i in range(min(5, len(market_list) - offset_m)):
                actual_idx = offset_m + i
                orb = market_list[actual_idx]
                y_off = panel.y + 110 + i * 90
                # TIKLAMA ALANI (DİKKAT: draw_craft_window ile aynı (panel.right - 100) olmalı!)
                buy_btn = pygame.Rect(panel.right - 100, y_off + 20, 60, 40)
                if buy_btn.collidepoint(pos):
                    if p.gold >= orb['price']:
                        if p.add_item(orb.copy()):
                            p.gold -= orb['price']
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
            if self.craft_orb_prev_rect.collidepoint(pos) and self.orb_inv_page > 0: self.orb_inv_page -= 1; return
            if self.craft_orb_next_rect.collidepoint(pos) and (self.orb_inv_page + 1) * 8 < len(orbs_in_inv): self.orb_inv_page += 1; return
            if self.craft_mkt_prev_rect.collidepoint(pos) and self.orb_market_page > 0: self.orb_market_page -= 1; return
            if self.craft_mkt_next_rect.collidepoint(pos) and (self.orb_market_page + 1) * 5 < len(market_list): self.orb_market_page += 1; return
            
            # GERİ AL (Hedef Eşyayı Envantere Çek) - çizimde saklanan rect kullanılır
            take_back_btn = getattr(self, 'craft_take_back_rect', None)
            if take_back_btn and take_back_btn.collidepoint(pos):
                if p.add_item(self.crafting_target):
                    self.crafting_target = None
                    self.show_craft_window = False
                    self.craft_error_msg = ""
                    return
            return # Craft penceresi dışındakileri blockla

        # 2. ANA TABLAR
        for btn in self.tab_buttons:
            if btn.rect.collidepoint(pos):
                self.active_tab = btn.tab_id
                return

        # 3. SAVAŞA DÖN / ÇIKIŞ
        if self.exit_btn_rect.collidepoint(pos):
            self.show_inventory = False
            return

        # 4. SEKME İÇERİĞİ
        if self.active_tab == "inventory":
            # --- FİLTRE TIKLAMALARI ---
            for i, rect in enumerate(self.filter_rects):
                if rect.collidepoint(pos):
                    if i < 5: # Rarity
                        self.inv_filter_rarity = self.rarity_filters[i]
                    else: # Type
                        self.inv_filter_type = self.type_filters[i-5]
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
            filtered_inv = []
            for it in p.inventory:
                # ORB GİZLEME
                if self.hide_orbs and it.get('type') == 'orb': continue

                if self.inv_filter_rarity != "TÜMÜ":
                    if self.inv_filter_rarity == "SET" and not it.get("setTag"): continue
                    if self.inv_filter_rarity != "SET" and it.get("rarity") != self.inv_filter_rarity: continue
                if self.inv_filter_type != "TÜMÜ":
                    it_type = it.get("type", "")
                    if self.inv_filter_type == "armor" and it_type not in ["helmet", "chest"]: continue
                    if self.inv_filter_type == "accessory" and it_type not in ["amulet", "ring"]: continue
                    if self.inv_filter_type == "special" and it_type not in ["artifact", "orb"]: continue
                    if self.inv_filter_type not in ["armor", "accessory", "special"] and it_type != self.inv_filter_type: continue
                filtered_inv.append(it)

            # Sayfalama Kontrolü
            if self.inv_prev_rect.collidepoint(pos) and self.inventory_page > 0:
                self.inventory_page -= 1
                return
            if self.inv_next_rect.collidepoint(pos) and (self.inventory_page + 1) * 12 < len(filtered_inv):
                self.inventory_page += 1
                return

            # Kuşanılanlar
            for row in self.equip_rows:
                if row.rect.collidepoint(pos) and row.item:
                    p.inv_manager.unequip(row.slot_type)
                    return

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
                            # NORMAL EKİPMAN
                            p.inventory.pop(orig_idx)
                            p.inv_manager.equip(target_item)
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
            # Tablar (çizimde saklanan rect'ler kullanılır)
            for i, tab_rect in enumerate(getattr(self, 'skill_sub_tab_rects', [])):
                if tab_rect.collidepoint(pos):
                    self.active_skill_sub_tab = self.skill_sub_tabs[i]
                    
            if self.reset_btn_rect.collidepoint(pos):
                if p.reset_skills():
                    self.logic.add_event("damage_text", p.x, p.y-60, value="Yetenekler Sıfırlandı!", color=(46, 204, 113))
                else:
                    self.logic.add_event("damage_text", p.x, p.y-60, value="Yetersiz Altın! (10K G Gerekli)", color=(231, 76, 60))
                
            for btn in self.skill_btns:
                sk_data = p.skills[btn.skill_id]
                if sk_data['group'] == self.active_skill_sub_tab:
                    if btn.rect.collidepoint(pos):
                        self.buy_skill(p, btn.skill_id)

        elif self.active_tab == "hero":
            diff_names = ["Normal", "Hard", "Very Hard", "Impossible"]
            for i, rect in enumerate(self.diff_btn_rects):
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
        for part in getattr(self.logic, 'particles', []):
            if not (
                final_cam_x - 20 <= part['x'] <= final_cam_x + internal_w + 20
                and final_cam_y - 20 <= part['y'] <= final_cam_y + internal_h + 20
            ):
                continue
            px, py = part['x'] - final_cam_x, part['y'] - final_cam_y
            pygame.draw.circle(world_surf, part['color'], (int(px), int(py)), part['size'])
            
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
                r = ev.get('range', 80) * 0.4
                pygame.draw.line(world_surf, (255, 255, 255), (dx - r, dy - r), (dx + r, dy + r), 4)
                pygame.draw.line(world_surf, (255, 255, 255), (dx + r*0.3, dy - r*0.6), (dx - r*0.3, dy + r*0.6), 4)
            elif ev['type'] == 'sweep':
                angle, r_v, a_v = ev['angle'], ev['range'], ev['arc']
                pts = [(dx, dy)]
                steps = 10
                sa = angle - a_v / 2
                for i in range(steps + 1):
                    a = sa + (a_v / steps) * i
                    pts.append((dx + math.cos(a) * r_v, dy + math.sin(a) * r_v))
                if len(pts) > 2:
                    if internal_w > self._sweep_surface.get_width() or internal_h > self._sweep_surface.get_height():
                        self._sweep_surface = pygame.Surface((int(internal_w*1.2), int(internal_h*1.2)), pygame.SRCALPHA)
                    self._sweep_surface.fill((0,0,0,0))
                    pygame.draw.polygon(self._sweep_surface, (255, 255, 255, 120), pts)
                    world_surf.blit(self._sweep_surface, (0, 0), area=pygame.Rect(0, 0, internal_w, internal_h))
                    pygame.draw.lines(world_surf, (255, 255, 255), False, pts[1:], 3)
            elif ev['type'] == 'shockwave' or ev['type'] == 'explosion':
                rad = ev.get('radius', 100)
                clr = ev.get('color', (255, 255, 255))
                pygame.draw.circle(world_surf, clr, (int(dx), int(dy)), int(rad), 2)
                if ev['type'] == 'explosion':
                    # Patlama için iç halka
                    pygame.draw.circle(world_surf, (255, 255, 255), (int(dx), int(dy)), int(rad * 0.7), 1)

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
        
        # Artifact
        art = p.inv_manager.equipped.get("artifact")
        if art:
            art_name, max_cd = art.get("name", "Artifact").upper(), art.get("cooldown", 30)
            pygame.draw.rect(self.screen, (30, 30, 40, 200), (20, 215, 250, 45), border_radius=5)
            pygame.draw.rect(self.screen, (100, 100, 120), (20, 215, 250, 45), width=2, border_radius=5)
            if p.artifact_cooldown > 0:
                ratio = 1.0 - (p.artifact_cooldown / max_cd)
                pygame.draw.rect(self.screen, (192, 57, 43), (25, 240, 240 * ratio, 10), border_radius=3)
                txt = f"{art_name} ({int(p.artifact_cooldown)}s)"
                clr = (200, 200, 200)
            else:
                pygame.draw.rect(self.screen, (46, 204, 113), (25, 240, 240, 10), border_radius=3)
                txt = f"{art_name} (HAZIR)"
                clr = (255, 255, 255)
            art_surf = self.font_sub.render(txt, True, clr)
            self.screen.blit(art_surf, (25, 215))
        else:
            pygame.draw.rect(self.screen, (30, 30, 40, 150), (20, 215, 250, 30), border_radius=5)
            art_surf = self.font_sub.render("ARTIFACT: EKSİK", True, (100, 100, 100))
            self.screen.blit(art_surf, (25, 215))
        
        # 4. Kan Ayı Filtresi
        if self.logic.wave.get("is_blood_moon"):
            self.screen.blit(self.blood_moon_surf, (0, 0))

        # 🟢 KILL STREAK HUD
        # 4. Kill Streak (Combo) - Minimalist Tasarım
        if self.logic.kill_streak > 1:
            streak = self.logic.kill_streak
            color = (241, 196, 15) if streak < 20 else (231, 76, 60)
            
            # Daha küçük ve şık font
            txt = self.font_combo.render(f"COMBO: {streak}", True, color)
            txt_rect = txt.get_rect(center=(self.width // 2, 80))
            
            # Hafif gölge
            shadow = self.font_combo.render(f"COMBO: {streak}", True, (0, 0, 0))
            self.screen.blit(shadow, (txt_rect.x + 2, txt_rect.y + 2))
            self.screen.blit(txt, txt_rect)
            
            # Streak Zaman Çubuğu (Daha ince ve kısa)
            bar_w = 120
            ratio = max(0, min(1.0, self.logic.streak_timer / 3.5))
            bar_y = txt_rect.bottom + 5
            pygame.draw.rect(self.screen, (40, 40, 40), (self.width//2 - bar_w//2, bar_y, bar_w, 4), border_radius=2)
            pygame.draw.rect(self.screen, color, (self.width//2 - bar_w//2, bar_y, bar_w * ratio, 4), border_radius=2)

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


    def draw_settings_menu(self):
        self._overlay_surface.fill((0, 0, 0, 180))
        self.screen.blit(self._overlay_surface, (0, 0))
        
        panel = pygame.Rect(self.width // 2 - 250, self.height // 2 - 250, 500, 500)
        pygame.draw.rect(self.screen, (35, 35, 50), panel, border_radius=15)
        pygame.draw.rect(self.screen, (80, 80, 100), panel, width=2, border_radius=15)
        
        if self.setting_tab == "main":
            title = self.font_main.render("DURAKLATILDI", True, (241, 196, 15))
            self.screen.blit(title, (self.width // 2 - title.get_width() // 2, panel.y + 30))

            options = [
                f"EKRAN SARSINTISI: {'[AÇIK]' if self.logic.settings['shake'] else '[KAPALI]'}",
                f"EKRAN MODU: [{self.manager.get_display_mode_label()}]",
                f"HİLE MODU: {'[AÇIK]' if self.logic.cheat_mode else '[KAPALI]'}",
                "OYUNU KAYDET",
                "KAYITLI OYUNLAR",
                "KAYDET VE ANA MENÜYE DÖN",
                "ANA MENÜYE DÖN (Kaydetmeden)",
                "OYUNA GERİ DÖN"
            ]
            for i, label in enumerate(options):
                row_rect = pygame.Rect(self.width // 2 - 200, panel.y + 100 + i * 50 - 15, 400, 40)
                is_selected = i == self.selected_setting_idx
                if is_selected:
                    pygame.draw.rect(self.screen, (50, 50, 70), row_rect, border_radius=8)
                    pygame.draw.rect(self.screen, (241, 196, 15), row_rect, width=2, border_radius=8)
                color = (255, 255, 255) if is_selected else (150, 150, 160)
                txt = render_fit(label, 20, color, row_rect.width - 20)
                self.screen.blit(txt, txt.get_rect(center=row_rect.center))

        elif self.setting_tab == "save":
            title = self.font_main.render("KAYDET", True, (46, 204, 113))
            self.screen.blit(title, (self.width // 2 - title.get_width() // 2, panel.y + 30))
            
            options = ["YENİ KAYIT (FARKLI KAYDET)", "SON KAYDI GÜNCELLE"]
            for i, label in enumerate(options):
                row_rect = pygame.Rect(self.width // 2 - 200, panel.y + 150 + i * 80 - 20, 400, 60)
                is_selected = i == self.selected_setting_idx
                if is_selected:
                    pygame.draw.rect(self.screen, (50, 50, 70), row_rect, border_radius=8)
                    pygame.draw.rect(self.screen, (46, 204, 113), row_rect, width=2, border_radius=8)
                color = (255, 255, 255) if is_selected else (150, 150, 160)
                txt = render_fit(label, 24, color, row_rect.width - 24)
                self.screen.blit(txt, txt.get_rect(center=row_rect.center))

        elif self.setting_tab == "load":
            title = self.font_main.render("KAYITLAR", True, (52, 152, 219))
            self.screen.blit(title, (self.width // 2 - title.get_width() // 2, panel.y + 30))
            if not self.save_slots:
                info = self.font_desc.render("HENÜZ KAYIT YOK", True, (150, 150, 150))
                self.screen.blit(info, (self.width // 2 - info.get_width() // 2, panel.y + 180))
            else:
                for i, slot in enumerate(self.save_slots[:5]): # Sadece son 5
                    # Satır konumu, update()'teki tıklama alanıyla aynı (110 + i*55)
                    row_rect = pygame.Rect(self.width // 2 - 250, panel.y + 110 + i * 55 - 20, 500, 40)
                    is_selected = i == self.selected_setting_idx
                    if is_selected:
                        pygame.draw.rect(self.screen, (50, 50, 70), row_rect, border_radius=8)
                        pygame.draw.rect(self.screen, (52, 152, 219), row_rect, width=2, border_radius=8)
                    color = (255, 255, 255) if is_selected else (150, 150, 160)
                    slot_txt = f"SEVİYE {slot['level']}  •  DALGA {slot['wave']}  •  {slot['class'].upper()}"
                    date_txt = render_fit(slot['date'], 16, (120, 120, 135), 140)
                    txt = render_fit(slot_txt, 19, color, row_rect.width - date_txt.get_width() - 40)
                    self.screen.blit(txt, (row_rect.x + 14, row_rect.centery - txt.get_height() // 2))
                    self.screen.blit(date_txt, (row_rect.right - date_txt.get_width() - 14, row_rect.centery - date_txt.get_height() // 2))

                # Bilgi Notu
                info_txt = render_fit("[DEL]: SİL  |  [X]: HEPSİNİ TEMİZLE", 18, (231, 76, 60), panel.width - 40)
                self.screen.blit(info_txt, (self.width // 2 - info_txt.get_width() // 2, panel.bottom - 50))

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

    def draw_hud(self):
        p = self.logic.players[self.logic.local_player_id]
        # Wave Bilgisi
        wave_str = f"WAVE: {self.logic.wave['level']}"
        wave_surf = self.font_sub.render(wave_str, True, (241, 196, 15))
        self.screen.blit(wave_surf, (self.width // 2 - wave_surf.get_width() // 2, 20))

        # Aktif dalga olayı şeridi (dalga boyunca görünür kalır)
        evt = self.logic.wave.get("event")
        if evt:
            strip_txt = self.font_desc.render(evt["desc"], True, (255, 180, 40))
            sw, sh = strip_txt.get_width() + 24, strip_txt.get_height() + 8
            strip_bg = pygame.Surface((sw, sh), pygame.SRCALPHA)
            pygame.draw.rect(strip_bg, (25, 20, 5, 190), strip_bg.get_rect(), border_radius=6)
            pygame.draw.rect(strip_bg, (255, 165, 0, 220), strip_bg.get_rect(), width=1, border_radius=6)
            strip_bg.blit(strip_txt, (12, 4))
            self.screen.blit(strip_bg, (self.width // 2 - sw // 2, 58))

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
            pygame.draw.rect(banner, (10, 10, 22, 200), banner.get_rect(), border_radius=12)
            pygame.draw.rect(banner, (241, 196, 15, 255), banner.get_rect(), width=2, border_radius=12)
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
        
        # HP ve ES Barları (Sol Üst)
        hp_ratio = p.hp / max(1, p.max_hp)
        pygame.draw.rect(self.screen, (30, 30, 45), (20, 95, 200, 12), border_radius=6)
        pygame.draw.rect(self.screen, (231, 76, 60), (20, 95, 200 * hp_ratio, 12), border_radius=6)
        hp_txt = self.font_desc.render(f"HP: {int(p.hp)}/{int(p.max_hp)}", True, (255, 255, 255))
        self.screen.blit(hp_txt, (225, 90))
        
        y_offset = 115
        if p.max_energy_shield > 0:
            es_ratio = p.energy_shield / max(1, p.max_energy_shield)
            pygame.draw.rect(self.screen, (30, 30, 45), (20, 115, 200, 12), border_radius=6)
            pygame.draw.rect(self.screen, (52, 152, 219), (20, 115, 200 * es_ratio, 12), border_radius=6)
            es_txt = self.font_desc.render(f"ES: {int(p.energy_shield)}/{int(p.max_energy_shield)}", True, (255, 255, 255))
            self.screen.blit(es_txt, (225, 110))
            y_offset += 20
        
        # XP Barı
        xp_ratio = p.xp / p.xp_to_next_level
        pygame.draw.rect(self.screen, (30, 30, 45), (20, y_offset, 200, 12), border_radius=6)
        pygame.draw.rect(self.screen, (46, 204, 113), (20, y_offset, 200 * xp_ratio, 12), border_radius=6)
        xp_txt = self.font_desc.render(f"XP: {p.xp:.1f}/{p.xp_to_next_level}", True, (255, 255, 255))
        self.screen.blit(xp_txt, (225, y_offset - 5))
        
        # --- HUD: DASH DURUMU (Space) ---
        dash_x, dash_y = self.width - 270, 20
        pygame.draw.rect(self.screen, (30, 30, 40), (dash_x, dash_y, 250, 45), border_radius=5) # Transparency (RGBA) Surface olmadan pygame.draw.rect ile yapılamaz, Color box yeterli
        pygame.draw.rect(self.screen, (100, 100, 120), (dash_x, dash_y, 250, 45), width=2, border_radius=5)
        
        if p.dash_timer > 0:
            ratio = 1.0 - (p.dash_timer / p.dash_cooldown)
            pygame.draw.rect(self.screen, (52, 152, 219), (dash_x + 5, dash_y + 25, 240 * ratio, 10), border_radius=3)
            dash_text = f"DASH: {int(p.dash_timer)}s"
            d_color = (200, 200, 200)
        else:
            pygame.draw.rect(self.screen, (39, 174, 150), (dash_x + 5, dash_y + 25, 240, 10), border_radius=3)
            dash_text = "DASH [SPACE] HAZIR"
            d_color = (46, 204, 113)
            import time
            if int(time.time() * 4) % 2 == 0: d_color = (255, 255, 255)
            
        dash_surf = self.font_sub.render(dash_text, True, d_color)
        self.screen.blit(dash_surf, (dash_x + 5, dash_y))

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
        panel_w = 430
        panel = pygame.Rect(self.width - panel_w - 20, 120, panel_w, min(720, self.height - 135))
        surface = pygame.Surface(panel.size, pygame.SRCALPHA)
        surface.fill((18, 22, 32, 238))
        self.screen.blit(surface, panel.topleft)
        pygame.draw.rect(self.screen, (80, 135, 190), panel, width=2, border_radius=10)

        card_system = self.logic.card_system
        card_bonus = card_system.get_stat_contributions()
        card_count = len(card_system.active_cards)
        active = set(card_system.active_cards)
        synergy_count = sum(
            1 for synergy in card_system.synergy_system.SYNERGIES
            if all(card_id in active for card_id in synergy["required_cards"])
        )

        title = self.font_sub.render("ANLIK İSTATİSTİKLER", True, (130, 200, 255))
        self.screen.blit(title, (panel.x + 16, panel.y + 12))
        count_txt = self.font_desc.render(f"{card_count} kart • {synergy_count} sinerji", True, (175, 185, 200))
        self.screen.blit(count_txt, (panel.right - count_txt.get_width() - 16, panel.y + 17))

        info = self.font_desc.render("Toplam: tüm kaynaklar  |  Kart: ham kart+sinerji katkısı", True, (145, 155, 170))
        if info.get_width() > panel.width - 32:
            ratio = (panel.width - 32) / info.get_width()
            info = pygame.transform.smoothscale(info, (panel.width - 32, max(12, int(info.get_height() * ratio))))
        self.screen.blit(info, (panel.x + 16, panel.y + 43))

        y = panel.y + 72
        row_h = 24

        def section(label):
            nonlocal y
            pygame.draw.line(self.screen, (65, 80, 105), (panel.x + 14, y + 9), (panel.right - 14, y + 9), 1)
            text_surf = self.font_desc.render(label, True, (241, 196, 15))
            bg = pygame.Rect(panel.x + 14, y, text_surf.get_width() + 12, text_surf.get_height())
            pygame.draw.rect(self.screen, (18, 22, 32), bg)
            self.screen.blit(text_surf, (panel.x + 20, y))
            y += 25

        def row(label, value, bonus_value=0, percent_bonus=False):
            nonlocal y
            label_surf = self.font_desc.render(label, True, (190, 195, 205))
            value_surf = self.font_desc.render(str(value), True, (255, 255, 255))
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
        
        p = self.logic.players[self.logic.local_player_id]
        
        # 1. TAB BAR & HUD
        for btn in self.tab_buttons:
            btn.draw(self.screen, self.font_sub, self.active_tab)
            
        # Altın & Çıkış
        gold_txt = self.font_sub.render(f"ALTIN: {p.gold}", True, (241, 196, 15))
        self.screen.blit(gold_txt, (self.width - 400, 50))
        
        import ui_theme
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
        boss = next((e for e in self.logic.enemies if e.type == "boss"), None)
        if not boss: return
        
        # Ekran Üst Orta
        bar_w, bar_h = 700, 25
        x = self.width // 2 - bar_w // 2
        y = 55
        
        # Arka plan
        pygame.draw.rect(self.screen, (20, 20, 30), (x, y, bar_w, bar_h), border_radius=5)
        # Dolgu
        ratio = max(0, boss.hp / boss.max_hp)
        pygame.draw.rect(self.screen, (192, 57, 43), (x, y, int(bar_w * ratio), bar_h), border_radius=5)
        # Kenarlık
        pygame.draw.rect(self.screen, (241, 196, 15), (x, y, bar_w, bar_h), width=2, border_radius=5)
        
        # İsim (EchelionFinrod)
        name_t = self.font_boss_name.render("ECHELION FINROD", True, (241, 196, 15))
        self.screen.blit(name_t, (self.width // 2 - name_t.get_width() // 2, y - 35))
        
        # HP Text (Numerical)
        hp_str = f"{int(boss.hp):,} / {int(boss.max_hp):,}"
        hp_txt = self.font_boss_hp.render(hp_str, True, (255, 255, 255))
        self.screen.blit(hp_txt, (self.width // 2 - hp_txt.get_width() // 2, y + 2))

    def draw_craft_window(self):
        # Overlay
        self._overlay_surface.fill((0, 0, 0, 220))
        self.screen.blit(self._overlay_surface, (0, 0))
        
        panel = pygame.Rect(self.width // 2 - 450, self.height // 2 - 300, 900, 600)
        pygame.draw.rect(self.screen, (30, 30, 45), panel, border_radius=15)
        pygame.draw.rect(self.screen, (100, 100, 120), panel, width=3, border_radius=15)
        
        item = self.crafting_target
        if not item: return

        # 1. SOL: ENVANTERDEKİ ORBLAR
        p = self.logic.players[self.logic.local_player_id]
        orbs_in_inv = [x for x in p.inventory if x.get('type') == 'orb']
        
        title_l = self.font_sub.render(f"ORBLARIN ({self.orb_inv_page + 1})", True, (52, 152, 219))
        self.screen.blit(title_l, (panel.x + 30, panel.y + 30))
        
        offset_i = self.orb_inv_page * 8
        self.craft_orb_use_rects = []
        for i in range(min(8, len(orbs_in_inv) - offset_i)):
            orb = orbs_in_inv[offset_i + i]
            y_off = panel.y + 80 + i * 55
            rect = pygame.Rect(panel.x + 30, y_off, 250, 45)
            pygame.draw.rect(self.screen, (45, 45, 60), rect, border_radius=5)

            name = orb['name'].split(" (")[0]
            stack = orb.get('stack', 1)
            txt = self.font_desc.render(f"{name} x{stack}", True, (255, 255, 255))
            self.screen.blit(txt, (rect.x + 10, rect.y + 12))

            # Seç/Kullan Butonu - hitbox tek kaynak: rect saklanır
            use_btn = pygame.Rect(rect.right - 70, rect.y + 5, 60, 35)
            self.craft_orb_use_rects.append((offset_i + i, use_btn))
            pygame.draw.rect(self.screen, (39, 174, 96), use_btn, border_radius=5)
            u_txt = self.font_desc.render("SEÇ", True, (255, 255, 255))
            self.screen.blit(u_txt, u_txt.get_rect(center=use_btn.center))

        # SAYFALAMA BUTONLARI (SOL)
        if self.orb_inv_page > 0:
            pygame.draw.rect(self.screen, (52, 152, 219), self.craft_orb_prev_rect, border_radius=5)
            txt = self.font_desc.render("<<", True, (255, 255, 255))
            self.screen.blit(txt, txt.get_rect(center=self.craft_orb_prev_rect.center))
        if (self.orb_inv_page + 1) * 8 < len(orbs_in_inv):
            pygame.draw.rect(self.screen, (52, 152, 219), self.craft_orb_next_rect, border_radius=5)
            txt = self.font_desc.render(">>", True, (255, 255, 255))
            self.screen.blit(txt, txt.get_rect(center=self.craft_orb_next_rect.center))

        # 2. ORTA: HEDEF EŞYA
        title_c = self.font_sub.render("HEDEF EŞYA", True, (241, 196, 15))
        self.screen.blit(title_c, (self.width // 2 - title_c.get_width() // 2, panel.y + 30))
        
        # Kutuyu daha uzun (380) yapıyoruz ki affixler sığsın
        item_rect = pygame.Rect(self.width // 2 - 140, panel.y + 80, 280, 380)
        pygame.draw.rect(self.screen, (20, 20, 30), item_rect, border_radius=12)
        
        # Nadirlik Rengi
        rarity_colors = {"Normal": (255,255,255), "Magic": (52,152,219), "Rare": (241,196,15), "Unique": (231,76,60)}
        color = rarity_colors.get(item['rarity'], (255,255,255))
        
        # Kenarlık (Nadirlik renginde)
        pygame.draw.rect(self.screen, color, item_rect, width=2, border_radius=12)
        
        # Başlık ve Alt Başlık (Tooltip stili)
        name_t = self.font_sub.render(item['name'], True, color)
        self.screen.blit(name_t, (item_rect.x + 15, item_rect.y + 15))
        
        type_t = self.font_desc.render(f"{item['rarity']} {item['type'].upper()}", True, (180, 180, 180))
        self.screen.blit(type_t, (item_rect.x + 15, item_rect.y + 45))
        
        pygame.draw.line(self.screen, (60, 60, 80), (item_rect.x + 15, item_rect.y + 70), (item_rect.right - 15, item_rect.y + 70))
        
        # Statları Göster
        y_s = item_rect.y + 85
        base_stats = item.get('itemBase', {})
        brown = (160, 82, 45) # Base Stat Rengi
        for stat, val in base_stats.items():
            st_t = self.font_desc.render(f"[*] {stat}: {val}", True, brown)
            self.screen.blit(st_t, (item_rect.x + 15, y_s))
            y_s += 25

        affixes = item.get('prefixes', []) + item.get('suffixes', [])
        for aff in affixes:
            tier = aff.get('tier', 3)
            label = aff.get('label', '?')
            color = (46, 204, 113) # Yeşil (Standart)
            icon = ""
            if tier == 1:
                color = (241, 196, 15) # Altın/Sarı
                icon = "✨ "
            elif tier == 3:
                color = (52, 152, 219) # Cyan/Mavi
            
            tier_str = f"{icon}[{label} (T{tier})]"
            af_t = self.font_desc.render(f"{tier_str} +{aff['val']} {aff['stat']}", True, color)
            self.screen.blit(af_t, (item_rect.x + 15, y_s))
            y_s += 25

        # GERİ AL BUTONU (Kutunun biraz altına) - hitbox tek kaynak: bu rect saklanır
        take_back_btn = pygame.Rect(self.width // 2 - 70, item_rect.bottom + 10, 140, 40)
        self.craft_take_back_rect = take_back_btn
        pygame.draw.rect(self.screen, (52, 152, 219), take_back_btn, border_radius=5)
        tb_t = self.font_desc.render("GERİ AL", True, (255, 255, 255))
        self.screen.blit(tb_t, tb_t.get_rect(center=take_back_btn.center))

        # 3. SAĞ: ORB MARKET (DÜKKAN)
        title_r = self.font_sub.render(f"ORB MARKET ∞ ({self.orb_market_page + 1})", True, (231, 76, 60))
        self.screen.blit(title_r, (panel.right - 280, panel.y + 30))
        
        gold_t = self.font_sub.render(f"GOLD: {p.gold}", True, (241, 196, 15))
        self.screen.blit(gold_t, (panel.right - 280, panel.y + 60))
        
        market_list = self.logic.orb_market
        offset_m = self.orb_market_page * 5
        for i in range(min(5, len(market_list) - offset_m)):
            orb = market_list[offset_m + i]
            y_off = panel.y + 110 + i * 90
            rect = pygame.Rect(panel.right - 280, y_off, 250, 80)
            pygame.draw.rect(self.screen, (45, 45, 60), rect, border_radius=8)
            
            name = orb['name'].split(" (")[0]
            n_t = self.font_desc.render(name, True, (255, 255, 255))
            p_t = self.font_desc.render(f"{orb['price']} GOLD", True, (241, 196, 15))
            self.screen.blit(n_t, (rect.x + 10, rect.y + 10))
            self.screen.blit(p_t, (rect.x + 10, rect.y + 35))
            
            # Sahip olunan sayı
            owned = sum([x.get('stack', 1) for x in p.inventory if x.get('type') == 'orb' and x.get('orb_id') == orb['orb_id']])
            o_t = self.font_desc.render(f"Sende: {owned}", True, (200, 200, 200))
            self.screen.blit(o_t, (rect.x + 10, rect.y + 55))
            
            buy_btn = pygame.Rect(rect.right - 70, rect.y + 20, 60, 40)
            pygame.draw.rect(self.screen, (231, 76, 60), buy_btn, border_radius=5)
            b_t = self.font_desc.render("AL", True, (255, 255, 255))
            self.screen.blit(b_t, b_t.get_rect(center=buy_btn.center))

        # SAYFALAMA BUTONLARI (SAĞ)
        if self.orb_market_page > 0:
            pygame.draw.rect(self.screen, (52, 152, 219), self.craft_mkt_prev_rect, border_radius=5)
            txt = self.font_desc.render("<<", True, (255, 255, 255))
            self.screen.blit(txt, txt.get_rect(center=self.craft_mkt_prev_rect.center))
        if (self.orb_market_page + 1) * 5 < len(market_list):
            pygame.draw.rect(self.screen, (52, 152, 219), self.craft_mkt_next_rect, border_radius=5)
            txt = self.font_desc.render(">>", True, (255, 255, 255))
            self.screen.blit(txt, txt.get_rect(center=self.craft_mkt_next_rect.center))

        # Çıkış Butonu
        close_btn = pygame.Rect(panel.right - 50, panel.y + 10, 40, 40)
        pygame.draw.rect(self.screen, (192, 57, 43), close_btn, border_radius=20)
        c_t = self.font_sub.render("X", True, (255, 255, 255))
        self.screen.blit(c_t, c_t.get_rect(center=close_btn.center))
        
        # Hata Mesajı
        if self.craft_error_msg:
            err_t = self.font_sub.render(self.craft_error_msg, True, (231, 76, 60))
            self.screen.blit(err_t, (self.width // 2 - err_t.get_width() // 2, panel.bottom - 60))

    def handle_tooltips(self, p):
        m_pos = pygame.mouse.get_pos()
        hovered_item = None
        
        if self.show_craft_window:
            orbs_in_inv = [x for x in p.inventory if x.get('type') == 'orb']
            offset_i = self.orb_inv_page * 8
            for i in range(min(8, len(orbs_in_inv) - offset_i)):
                orb = orbs_in_inv[offset_i + i]
                y_off = (self.height // 2 - 300) + 80 + i * 55
                rect = pygame.Rect((self.width // 2 - 450) + 30, y_off, 250, 45)
                if rect.collidepoint(m_pos):
                    hovered_item = orb
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
            
            # Çanta - Filtreye göre senkronize (GDD 62)
            filtered_inv = [item for item in p.inventory if not (self.hide_orbs and item.get('type') == 'orb')]
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
        # Sekme Butonları
        for btn in self.market_tab_btns:
            btn.draw(self.screen, self.font_sub, self.market_tab)
            
        # Yenile Butonu (Sadece Eşyalar sekmesinde)
        if self.market_tab == "items":
            wave_level = self.logic.wave.get("level", 1)
            cost = 500 + max(0, (wave_level - 1) * 400)
            pygame.draw.rect(self.screen, (39, 174, 96), self.refresh_btn_rect, border_radius=8)
            rf_txt = self.font_desc.render(f"YENİLE ({cost} G)", True, (255, 255, 255))
            self.screen.blit(rf_txt, rf_txt.get_rect(center=self.refresh_btn_rect.center))

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
                pygame.draw.rect(self.screen, (30, 30, 40), card.rect, border_radius=10, width=1)

        # Market Sayfalama Butonları Çizimi
        can_prev = self.market_page > 0
        can_next = (self.market_page + 1) * 12 < len(market_list)
        
        if can_prev:
            pygame.draw.rect(self.screen, (52, 152, 219), self.mkt_prev_rect, border_radius=5)
            pt = self.font_desc.render("<< GERİ", True, (255, 255, 255))
            self.screen.blit(pt, pt.get_rect(center=self.mkt_prev_rect.center))
            
        if can_next:
            pygame.draw.rect(self.screen, (52, 152, 219), self.mkt_next_rect, border_radius=5)
            nt = self.font_desc.render("İLERİ >>", True, (255, 255, 255))
            self.screen.blit(nt, nt.get_rect(center=self.mkt_next_rect.center))
        
        # Sayfa No
        page_t = self.font_desc.render(f"Sayfa {self.market_page + 1}", True, (200, 200, 200))
        self.screen.blit(page_t, (self.width // 2 - page_t.get_width() // 2, 150 + 6 * 85 + 12))


    def draw_item_tooltip(self, item, pos, p):
        # Tooltip Panel (Dinamik Yükseklik)
        affixes = item.get("prefixes", []) + item.get("suffixes", [])
        base_stats = item.get("itemBase", {})
        h = 140 + (max(1, len(base_stats)) * 25) + (len(affixes) * 25)
        if item.get("setTag"): h += 60
        
        # Ekran sınır kontrolü
        tx = pos[0] + 20
        ty = pos[1] + 20
        if tx + 280 > self.width: tx = pos[0] - 300
        if ty + h > self.height: ty = pos[1] - h
        
        # Ekran Üst/Sol Sınır Koruması
        tx = max(10, tx)
        ty = max(10, ty)
        
        panel_rect = pygame.Rect(tx, ty, 280, h)
        pygame.draw.rect(self.screen, (20, 20, 30, 240), panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, (100, 100, 120), panel_rect, width=2, border_radius=10)
        
        # Nadirlik Rengi
        rarity_colors = {"Normal": (255,255,255), "Magic": (52,152,219), "Rare": (241,196,15), "Unique": (231,76,60)}
        i_rarity = item.get('rarity', 'Normal')
        color = rarity_colors.get(i_rarity, (255,255,255))
        
        # Name
        name_t = self.font_sub.render(item['name'], True, color)
        self.screen.blit(name_t, (tx + 15, ty + 15))
        
        # Type & Rarity
        type_t = self.font_desc.render(f"{i_rarity} {item['type'].upper()}", True, (180, 180, 180))
        self.screen.blit(type_t, (tx + 15, ty + 45))
        
        pygame.draw.line(self.screen, (60, 60, 80), (tx + 15, ty + 70), (tx + 265, ty + 70))
        
        y = ty + 85
        # 🟢 ITEM BASE STATS (KAHVERENGİ)
        brown = (160, 82, 45) # Sienna / Kahverengi
        for stat, val in base_stats.items():
            st_t = self.font_desc.render(f"[*] {stat}: {val}", True, brown)
            self.screen.blit(st_t, (tx + 15, y))
            y += 25
            
        # Affixes (GDD 62)
        for aff in affixes:
            tier = aff.get('tier', 3)
            label = aff.get('label', '?')
            # Renk Paleti: T1 (Sarı), T2 (Yeşil), T3 (Mavi)
            color = (46, 204, 113) # Yeşil
            icon = ""
            if tier == 1:
                color = (241, 196, 15) # Altın/Sarı
                icon = "✨ "
            elif tier == 3:
                color = (52, 152, 219) # Cyan/Mavi
            
            tier_str = f"{icon}[{label} (T{tier})]"
            af_t = self.font_desc.render(f"{tier_str} +{aff['val']} {aff['stat']}", True, color)
            self.screen.blit(af_t, (tx + 15, y))
            y += 25
            
        # 📘 ORB AÇIKLAMASI (GDD 62)
        if item.get('desc'):
            pygame.draw.line(self.screen, (60, 60, 80), (tx + 15, y + 5), (tx + 265, y + 5))
            y += 15
            # Çok satırlı açıklama yapısı (Basit wrap)
            words = item['desc'].split(' ')
            line = ""
            for word in words:
                test_line = line + word + " "
                if self.font_desc.size(test_line)[0] < 250:
                    line = test_line
                else:
                    d_t = self.font_desc.render(line, True, (200, 200, 230))
                    self.screen.blit(d_t, (tx + 15, y))
                    y += 20
                    line = word + " "
            if line:
                d_t = self.font_desc.render(line, True, (200, 200, 230))
                self.screen.blit(d_t, (tx + 15, y))
                y += 20
            
        # Set Tag & Bonuses
        if item.get("setTag"):
            from logic.item_system import ItemSystem
            set_key = item['setTag']
            set_data = ItemSystem.set_types[set_key]
            
            # Ayırıcı Çizgi
            pygame.draw.line(self.screen, (241, 196, 15, 100), (tx + 15, y + 5), (tx + 265, y + 5))
            y += 15
            
            set_title = self.font_desc.render(f"SET: {set_data['name']}", True, (241, 196, 15))
            self.screen.blit(set_title, (tx + 15, y))
            y += 22
            
            # Aktif parça sayısını hesapla
            equipped_sets = [getattr(it, 'get', lambda x: None)('setTag') for it in p.inv_manager.equipped.values() if it]
            count = equipped_sets.count(set_key)
            
            for piece_count, bonuses in set_data['bonuses'].items():
                is_active = count >= piece_count
                b_color = (46, 204, 113) if is_active else (120, 120, 120)
                
                # Bonus metnini oluştur
                bonus_str = f"({piece_count}) " + ", ".join([f"{k}: {v}" for k, v in bonuses.items()])
                b_surf = self.font_desc.render(bonus_str, True, b_color)
                
                # Aktifse yanına bir onay işareti veya yıldız ekle
                if is_active:
                    self.screen.blit(b_surf, (tx + 25, y))
                    pygame.draw.circle(self.screen, (46, 204, 113), (tx + 18, y + 10), 3)
                else:
                    self.screen.blit(b_surf, (tx + 25, y))
                
                y += 20

    def draw_inventory_tab(self, p):
        # Sol Taraf: Kuşanılanlar
        title_l = self.font_sub.render("KUŞANILANLAR (SAĞ TIKLA ÇIKAR)", True, (230, 126, 34))
        self.screen.blit(title_l, (self.width // 2 - 450, 200))
        
        for row in self.equip_rows:
            # Kuşanılanları da biraz aşağı kaydıralım
            row.rect.y = 240 + (self.equip_rows.index(row) * 75)
            row.item = p.inv_manager.equipped.get(row.slot_type)
            row.update(row.item)
            row.draw(self.screen, self.font_sub)
            
        # Sağ Taraf: Çanta (Filtreleme, Grid & Sayfalama)
        
        # --- FİLTRELEME MANTIĞI ---
        filtered_inv = []
        for it in p.inventory:
            # ORB GİZLEME (Filtrelerden Önce)
            if self.hide_orbs and it.get('type') == 'orb': continue

            if self.inv_filter_rarity != "TÜMÜ":
                if self.inv_filter_rarity == "SET" and not it.get("setTag"): continue
                if self.inv_filter_rarity != "SET" and it.get("rarity") != self.inv_filter_rarity: continue
            if self.inv_filter_type != "TÜMÜ":
                it_type = it.get("type", "")
                if self.inv_filter_type == "armor" and it_type not in ["helmet", "chest"]: continue
                if self.inv_filter_type == "accessory" and it_type not in ["amulet", "ring"]: continue
                if self.inv_filter_type == "special" and it_type not in ["artifact", "orb"]: continue
                if self.inv_filter_type not in ["armor", "accessory", "special"] and it_type != self.inv_filter_type: continue
            filtered_inv.append(it)

        # FİLTRE BUTONLARINI ÇİZ
        for i, rarity in enumerate(self.rarity_filters):
            rect = self.filter_rects[i]
            is_active = self.inv_filter_rarity == rarity
            color = (46, 204, 113) if is_active else (52, 73, 94)
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            txt = self.font_desc.render(rarity, True, (255, 255, 255))
            self.screen.blit(txt, txt.get_rect(center=rect.center))

        for i, t_filter in enumerate(self.type_filters):
            rect = self.filter_rects[i + 5]
            is_active = self.inv_filter_type == t_filter
            color = (52, 152, 219) if is_active else (52, 73, 94)
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            txt = self.font_desc.render(t_filter.upper(), True, (255, 255, 255))
            self.screen.blit(txt, txt.get_rect(center=rect.center))
            
        # ORB TOGGLE BUTONU
        color = (231, 76, 60) if self.hide_orbs else (46, 204, 113)
        label = "ORB GÖSTER" if self.hide_orbs else "ORB GİZLE"
        pygame.draw.rect(self.screen, color, self.orb_toggle_rect, border_radius=5)
        txt = self.font_desc.render(label, True, (255, 255, 255))
        self.screen.blit(txt, txt.get_rect(center=self.orb_toggle_rect.center))

        max_pages = max(0, (len(filtered_inv) - 1) // 12)
        self.inventory_page = min(self.inventory_page, max_pages)
        
        page_t = self.font_sub.render(f"ÇANTA ({len(filtered_inv)}) - Sayfa {self.inventory_page + 1}", True, (230, 126, 34))
        self.screen.blit(page_t, (self.width // 2 + 20, 200))
        
        offset = self.inventory_page * 12
        for i, card in enumerate(self.bp_cards):
            # Kartın ve içindeki butonların koordinatlarını güncelle
            card.rect.y = 240 + (i // 2 * 85)
            # Buton y'lerini de güncelle (reposition mantığını manuel uyguluyoruz)
            btn_y = card.rect.y + 35
            card.use_rect.y = btn_y
            card.sell_rect.y = btn_y
            card.craft_rect.y = btn_y
            
            actual_idx = offset + i
            item = filtered_inv[actual_idx] if actual_idx < len(filtered_inv) else None
            card.draw(self.screen, self.font_sub, item)

        # TOPLU SATIŞ BUTONLARI
        for i, btn in enumerate(self.mass_sell_btns):
            rect = self.mass_sell_rects[i]
            pygame.draw.rect(self.screen, btn['color'], rect, border_radius=8)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, width=1, border_radius=8)
            st = self.font_desc.render(btn['label'], True, (255, 255, 255))
            self.screen.blit(st, st.get_rect(center=rect.center))

        # Sayfalama Butonları Çizimi (Pozisyon Güncellendi)
        self.inv_prev_rect.y = 750 + 45
        self.inv_next_rect.y = 750 + 45
        
        can_prev = self.inventory_page > 0
        can_next = (self.inventory_page + 1) * 12 < len(filtered_inv)
        
        if can_prev:
            pygame.draw.rect(self.screen, (52, 152, 219), self.inv_prev_rect, border_radius=5)
            pt = self.font_desc.render("<< GERİ", True, (255, 255, 255))
            self.screen.blit(pt, pt.get_rect(center=self.inv_prev_rect.center))
            
        if can_next:
            pygame.draw.rect(self.screen, (52, 152, 219), self.inv_next_rect, border_radius=5)
            nt = self.font_desc.render("İLERİ >>", True, (255, 255, 255))
            self.screen.blit(nt, nt.get_rect(center=self.inv_next_rect.center))

    def draw_hero_tab(self, p):
        # Kahraman İstatistikleri
        panel = pygame.Rect(self.width // 2 - 300, 150, 600, 500)
        pygame.draw.rect(self.screen, (35, 35, 50), panel, border_radius=15)
        
        # Sınıf Bilgisi ve Pasif
        c_name = getattr(p, 'class_name', 'Bilinmiyor')
        class_name_txt = self.font_sub.render(f"Sınıf: {c_name}", True, (241, 196, 15))
        self.screen.blit(class_name_txt, (panel.x + 40, panel.y + 15))
        
        passives = {
            "warrior": "Geniş Savuruş — Önündeki konide bulunan tüm düşmanlara aynı saldırıyla vurur.",
            "beastmaster": "Av Emri — Kamçıyla işaretlenen hedefe bütün minyonlar anında odaklanır.",
            "sniper": "Keskin Nişan — +%20 temel kritik şansı, +1 sekme ve +1 delme ile başlar.",
            "engineer": "Taret Ustası — Taret kiti kullanırken 5 saniyede bir savaş alanına taret kurar.",
            "ninja": "Arkadan Vuruş — Atılmadan sonraki ilk yakın saldırı 2 kat hasar verir.",
            "alchemist": "Uçucu Karışım — Bomba alanı %40 büyür; yakın saldırılar %30 ihtimalle zehirler.",
            "sorcerer": "Element Döngüsü — Ateş, buz ve zehir arasında döner; her 4. atış kritik ve 2 kat alanlıdır.",
            "bloodwalker": "Kan Öfkesi — Can %30'un altındayken hasar ve hız %40 artar; R ile mermi emilir.",
        }
        passive_desc = passives.get(getattr(p, 'class_id', 'warrior'), "")
        self.draw_text_wrapped(f"Pasif: {passive_desc}", panel.x + 40, panel.y + 45, 520, (180, 200, 255), self.font_desc)
        
        y = panel.y + 85
        stats = [
            ("MAKSİMUM CAN", f"{int(p.hp)} / {int(p.max_hp)}"),
            ("HAREKET HIZI", round(p.stats.get('speed', 0), 1)),
            ("ZIRH (Hasar Azaltma)", p.stats.get('armor', 0)),
            ("KAÇINMA ŞANSI", f"%{int(p.stats.get('dodgeChance', 0) * 100)}"),
            ("KRİTİK ŞANS", f"%{int(p.stats.get('critChance', 0.05) * 100)}"),
            ("CAN ÇALMA", f"%{int(p.stats.get('lifesteal', 0) * 100)}"),
            ("CAN YENİLENME", f"{round(p.stats.get('hpRegen', 0) + p.stats.get('combatRegen', 0), 1)}/sn"),
            ("EŞYA BULMA (MF)", f"%{int(p.stats.get('magicFind', 0) * 100)}"),
            ("HASAR ÇARPANI", f"x{round(p.stats.get('dmgMult', 1), 2)}"),
            ("MİNYON HASARI", f"x{round(p.stats.get('minionDamage', 1), 2)}")
        ]
        for label, val in stats:
            l_surf = self.font_desc.render(label, True, (150, 150, 150))
            v_surf = self.font_desc.render(str(val), True, (255, 255, 255))
            self.screen.blit(l_surf, (panel.x + 40, y))
            self.screen.blit(v_surf, (panel.right - 180, y))
            y += 28

        # ZORLUK SEÇİMİ (Alt Kısım)
        pygame.draw.rect(self.screen, (30, 30, 45), (panel.x, 540, panel.width, 100), border_radius=10)
        label = self.font_desc.render("ZORLUK SEÇİMİ (Dalga anında güncellenir)", True, (241, 196, 15))
        self.screen.blit(label, (panel.x + 20, 545))
        
        diff_names = ["Normal", "Hard", "Very Hard", "Impossible"]
        diff_colors = {"Normal": (46, 204, 113), "Hard": (241, 196, 15), "Very Hard": (230, 126, 34), "Impossible": (231, 76, 60)}
        
        for i, name in enumerate(diff_names):
            rect = self.diff_btn_rects[i]
            is_active = self.logic.wave["current_diff"] == name
            bg = diff_colors[name] if is_active else (50, 50, 65)
            pygame.draw.rect(self.screen, bg, rect, border_radius=5)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, width=2 if is_active else 1, border_radius=5)
            
            txt = self.font_desc.render(name, True, (255, 255, 255))
            self.screen.blit(txt, txt.get_rect(center=rect.center))

    def draw_skills_tab(self, p):
        # ÜST KATEGORİ BUTONLARI (Alt Sekme) - hitbox tek kaynak: rect'ler saklanır
        self.skill_sub_tab_rects = []
        for i, tab_name in enumerate(self.skill_sub_tabs):
            tab_rect = pygame.Rect(self.width // 2 - 480 + i * 195, 140, 185, 40)
            self.skill_sub_tab_rects.append(tab_rect)
            color = (46, 204, 113) if self.active_skill_sub_tab == tab_name else (52, 73, 94)
            pygame.draw.rect(self.screen, color, tab_rect, border_radius=5)
            pygame.draw.rect(self.screen, (255, 255, 255), tab_rect, width=1, border_radius=5)
            
            txt = self.font_desc.render(tab_name, True, (255, 255, 255))
            self.screen.blit(txt, txt.get_rect(center=tab_rect.center))
            
        # SIFIRLA BUTONU
        wave_level = self.logic.wave.get("level", 1)
        cost = 2000 + max(0, (wave_level - 1) * 400)
        pygame.draw.rect(self.screen, (192, 57, 43), self.reset_btn_rect, border_radius=5)
        reset_t = self.font_desc.render(f"SIFIRLA ({cost} G)", True, (255, 255, 255))
        self.screen.blit(reset_t, reset_t.get_rect(center=self.reset_btn_rect.center))

        # YETENEK BUTONLARINI FİLTRELE VE ÇİZ
        sp_txt = self.font_sub.render(f"MEVCUT PUAN (SP): {p.skill_points}", True, (241, 196, 15))
        self.screen.blit(sp_txt, (self.width // 2 - sp_txt.get_width() // 2, 90))
        
        shown_count = 0
        for btn in self.skill_btns:
            sk_data = p.skills[btn.skill_id]
            if sk_data['group'] == self.active_skill_sub_tab:
                # Pozisyonu dinamik ata (Grup içinde 2 sütun)
                col = shown_count % 2
                row = shown_count // 2
                btn.rect.x = self.width // 2 - 350 + (col * 360)
                btn.rect.y = 210 + (row * 85)
                
                btn.text = f"{sk_data['name']} ({sk_data['lvl']}/{sk_data['max']})"
                btn.draw(
                    self.screen,
                    self.font_desc,
                    p.skill_points > 0 and sk_data['lvl'] < sk_data['max'],
                    SKILL_HELP.get(sk_data['stat'], 'Bu özellik karakter istatistiklerini kalıcı olarak güçlendirir.'),
                )
                shown_count += 1

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
        
        title = self.font_main.render("KADERİNİ SEÇ", True, (241, 196, 15))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 100))
        
        # 3 Kartı Yan Yana Çiz
        cards = self.logic.pending_cards
        gap = 20 if len(cards) > 3 else 40
        card_w = min(300, (self.width - 80 - gap * (len(cards) - 1)) // max(1, len(cards)))
        card_top = 170
        controls_top = self.height - 230
        card_h = max(280, min(400, controls_top - card_top - 20))
        start_x = self.width // 2 - (len(cards) * card_w + (len(cards)-1) * gap) // 2
        
        self.card_rects = []
        for i, card in enumerate(cards):
            cx = start_x + i * (card_w + gap)
            cy = card_top
            rect = pygame.Rect(cx, cy, card_w, card_h)
            self.card_rects.append(rect)
            
            # Kart Arka Planı
            pygame.draw.rect(self.screen, (35, 35, 50), rect, border_radius=15)
            pygame.draw.rect(self.screen, (241, 196, 15), rect, width=2, border_radius=15)
            
            # Kart İsmi (keskin sığdırma)
            c_name = render_fit(card["name"], 24, (255, 255, 255), card_w - 30, bold=True)
            self.screen.blit(c_name, (cx + card_w//2 - c_name.get_width()//2, cy + 30))

            category, category_color = CARD_CATEGORY_LABELS.get(
                card.get('category'), ('KART', (160, 160, 170))
            )
            category_txt = self.font_desc.render(category, True, category_color)
            self.screen.blit(category_txt, category_txt.get_rect(center=(rect.centerx, cy + 78)))
            
            # Açıklama
            self.draw_text_wrapped(card["desc"], cx + 20, cy + 110, card_w - 40, (215, 215, 225), self.font_desc)
            
            # Sinerji İpucu
            if hasattr(self.logic.card_system, 'synergy_system'):
                p = self.logic.players[self.logic.local_player_id]
                test_cards = self.logic.card_system.active_cards + [card["id"]]
                active_syns = getattr(self.logic.card_system.synergy_system, 'active_synergies', [])
                for syn in getattr(self.logic.card_system.synergy_system, 'SYNERGIES', []):
                    if syn['id'] not in active_syns and all(c in test_cards for c in syn['required_cards']):
                        hint_txt = render_fit(f"✨ Sinerji Sağlar: {syn['name']}", 18, (46, 204, 113), card_w - 40)
                        self.screen.blit(hint_txt, (cx + 20, cy + card_h - 40))
                        break
        # Yenile (Reroll) ve Kart Alma butonları (tema: banner)
        import ui_theme
        m_pos = pygame.mouse.get_pos()
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

        title = self.font_main.render("⚡ SINIF EVRİMİ — YOLUNU SEÇ!", True, (230, 126, 34))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 60))

        sub = self.font_sub.render(f"Mevcut Sınıf: {p.class_name} → Level 20", True, (200, 200, 200))
        self.screen.blit(sub, (self.width // 2 - sub.get_width() // 2, 120))

        # 2 yolu yan yana göster
        card_w, card_h = 500, 380
        total_w = len(evos) * card_w + (len(evos) - 1) * 60
        start_x = self.width // 2 - total_w // 2
        card_y = 170

        self.evo_rects = []
        mouse_pos = pygame.mouse.get_pos()

        for i, (evo_id, evo_data) in enumerate(evos):
            cx = start_x + i * (card_w + 60)
            rect = pygame.Rect(cx, card_y, card_w, card_h)
            self.evo_rects.append((rect, evo_id))

            hovered = rect.collidepoint(mouse_pos)
            bg_color = (50, 40, 20) if hovered else (25, 25, 35)
            border_color = (255, 160, 40) if hovered else (150, 80, 20)

            pygame.draw.rect(self.screen, bg_color, rect, border_radius=16)
            pygame.draw.rect(self.screen, border_color, rect, width=3, border_radius=16)

            # İsim
            ntxt = render_fit(evo_data["name"], 26, (255, 220, 120), card_w - 40, bold=True)
            self.screen.blit(ntxt, (cx + card_w//2 - ntxt.get_width()//2, card_y + 20))

            # Açıklama
            self.draw_text_wrapped(evo_data["desc"], cx + 20, card_y + 80, card_w - 40,
                                   (210, 210, 210), self.font_desc)

            # Stat bonusları
            y_stat = card_y + 160
            for stat, val in list(evo_data["stats"].items())[:6]:
                sign = "+" if val >= 0 else ""
                s_txt = self.font_desc.render(f"{sign}{val:.1f} {stat}", True, (120, 255, 120))
                self.screen.blit(s_txt, (cx + 20, y_stat))
                y_stat += 26

            # Max HP delta
            delta = evo_data.get("max_hp_delta", 0)
            if delta != 0:
                col = (120, 255, 120) if delta > 0 else (255, 100, 100)
                dtxt = self.font_desc.render(f"{'+'if delta>0 else ''}{delta} Max HP", True, col)
                self.screen.blit(dtxt, (cx + 20, y_stat))
                y_stat += 26

            # Pasif bilgisi
            pasif_txt = render_fit(f"Pasif: {evo_data.get('passive','')}", 18, (180, 140, 255), card_w - 40)
            self.screen.blit(pasif_txt, (cx + 20, card_y + card_h - 50))

            # Seç butonu
            btn = pygame.Rect(cx + card_w//2 - 80, card_y + card_h - 25, 160, 40)
            pygame.draw.rect(self.screen, (200, 100, 20) if hovered else (100, 60, 10), btn, border_radius=8)
            btxt = self.font_desc.render("SEÇ →", True, (255, 255, 255))
            self.screen.blit(btxt, btxt.get_rect(center=btn.center))

    def draw_game_over_screen(self):
        # Overlay
        self._overlay_surface.fill((50, 0, 0, 200))
        self.screen.blit(self._overlay_surface, (0, 0))
        
        # Title
        title = self.font_main.render("ÖLDÜN", True, (231, 76, 60))
        t_rect = title.get_rect(center=(self.width // 2, self.height // 2 - 150))
        self.screen.blit(title, t_rect)
        
        # Stats Display
        if hasattr(self, 'stats_tracker'):
            # Sync with logic stats if available
            if hasattr(self.logic, 'stats'):
                self.stats_tracker['total_damage_dealt'] = int(self.logic.stats.get('total_damage_dealt', 0))
                self.stats_tracker['total_damage_taken'] = int(self.logic.stats.get('total_damage_taken', 0))
                self.stats_tracker['gold_earned'] = int(self.logic.stats.get('gold_earned', 0))
                
            stats = [
                f"Hasar Verilen: {self.stats_tracker['total_damage_dealt']}",
                f"Hasar Alınan: {self.stats_tracker['total_damage_taken']}",
                f"Kazanılan Altın: {self.stats_tracker['gold_earned']}",
                f"Geçilen Dalga: {self.stats_tracker['waves_survived']}"
            ]
            sy = self.height // 2 - 80
            for st_str in stats:
                st_txt = self.font_sub.render(st_str, True, (200, 200, 200))
                self.screen.blit(st_txt, (self.width // 2 - st_txt.get_width() // 2, sy))
                sy += 30
        
        # Buttons - hitbox tek kaynak: rect saklanır
        restart_rect = pygame.Rect(self.width // 2 - 200, self.height // 2 + 80, 400, 60)
        self.game_over_restart_rect = restart_rect
        
        # Hover Kontrolü
        m_pos = pygame.mouse.get_pos()
        
        # Yeniden Başla (tema: banner buton + kurukafa)
        import ui_theme
        r_state = "hover" if restart_rect.collidepoint(m_pos) else "normal"
        surf, over = ui_theme.render_banner_button(
            400, 60, "ANA MENÜYE DÖN", ui_theme.COLORS["ember"], state=r_state, skull=True)
        self.screen.blit(surf, (restart_rect.centerx - surf.get_width() // 2, restart_rect.y - over))
        
        # Bilgi
        info = self.font_desc.render("Sıradaki Dalga Seni Bekliyor!", True, (200, 200, 200))
        self.screen.blit(info, (self.width // 2 - info.get_width() // 2, self.height // 2 + 160))
    def draw_aura_tab(self, p):
        # 1. ESSENCE (ÖZ) PANELİ (Üst Yarım)
        essence_panel = pygame.Rect(self.width // 2 - 480, 140, 960, 200)
        pygame.draw.rect(self.screen, (35, 35, 50), essence_panel, border_radius=15)
        pygame.draw.rect(self.screen, (155, 89, 182), essence_panel, width=2, border_radius=15)
        
        title_e = self.font_sub.render("Kalıcı Öz İstatistikleri (Ascension)", True, (155, 89, 182))
        self.screen.blit(title_e, (essence_panel.x + 20, essence_panel.y + 15))
        
        if not p.is_essence_system_unlocked:
            lock_t = self.font_desc.render("KİLİTLİ: Bu sistem 10. Wave Boss'u kesildiğinde aktifleşir.", True, (150, 150, 150))
            self.screen.blit(lock_t, (essence_panel.x + 20, essence_panel.y + 60))
        else:
            # Öz İstatistiklerini Listele
            stats = [
                f"Max HP: +{p.essence_stats['max_hp']}",
                f"Fiziksel Hasar: +{p.essence_stats['phys_dmg']}",
                f"Büyü Hasarı: +{int(p.essence_stats['element_dmg']*100)}%",
                f"Zırh: +{p.essence_stats['armor']}",
                f"Hız: +{round(p.essence_stats['speed'], 1)}"
            ]
            for i, st in enumerate(stats):
                txt = self.font_desc.render(f"✨ {st}", True, (255, 255, 255))
                self.screen.blit(txt, (essence_panel.x + 20 + (i % 3) * 300, essence_panel.y + 60 + (i // 3) * 40))

        # 2. AURA SHRINE (Alt Yarım)
        aura_panel = pygame.Rect(self.width // 2 - 480, 360, 960, 480)
        pygame.draw.rect(self.screen, (25, 25, 35), aura_panel, border_radius=15)
        pygame.draw.rect(self.screen, (241, 196, 15), aura_panel, width=2, border_radius=15)
        
        limit_t = self.font_sub.render(f"Mistik Aura Tapınağı (Aktif: {len(p.active_auras)}/{p.aura_limit})", True, (241, 196, 15))
        self.screen.blit(limit_t, (aura_panel.x + 20, aura_panel.y + 15))
        
        from logic.aura_system import AuraManager
        aura_mgr = AuraManager()
        all_auras = aura_mgr.get_all_auras()
        
        # Sayfalama
        self.aura_btn_rects = []
        offset = self.aura_page * 8
        for i in range(8):
            idx = offset + i
            if idx >= len(all_auras): break
            
            aura = all_auras[idx]
            ax = aura_panel.x + 20 + (i % 2) * 460
            ay = aura_panel.y + 60 + (i // 2) * 100
            card_rect = pygame.Rect(ax, ay, 440, 90)

            # Kart Arkaplanı
            bg_color = (45, 45, 60)
            if aura.id in p.active_auras: bg_color = (60, 60, 80)
            pygame.draw.rect(self.screen, bg_color, card_rect, border_radius=10)

            # Aura İsmi ve Açıklama
            name_t = self.font_sub.render(aura.name, True, (241, 196, 15))
            self.screen.blit(name_t, (ax + 15, ay + 10))
            # Açıklamayı sığdır (Wrap)
            self.draw_text_wrapped(aura.description, ax + 15, ay + 42, 290, (200, 200, 200), self.font_desc)

            # Buton (Satın Al veya Kuşan) - hitbox tek kaynak: rect saklanır
            btn_rect = pygame.Rect(ax + 320, ay + 15, 100, 60)
            self.aura_btn_rects.append((idx, btn_rect))
            if aura.id in p.purchased_auras:
                is_active = aura.id in p.active_auras
                btn_color = (46, 204, 113) if is_active else (52, 152, 219)
                pygame.draw.rect(self.screen, btn_color, btn_rect, border_radius=8)
                label = "AKTİF" if is_active else "KUŞAN"
                txt = self.font_desc.render(label, True, (255, 255, 255))
                self.screen.blit(txt, txt.get_rect(center=btn_rect.center))
            else:
                pygame.draw.rect(self.screen, (230, 126, 34), btn_rect, border_radius=8)
                txt = self.font_desc.render(f"{aura.cost // 1000}K G", True, (255, 255, 255))
                self.screen.blit(txt, txt.get_rect(center=btn_rect.center))
                
        # Aura Kilitli Overlay
        if not p.is_essence_system_unlocked:
            if not hasattr(self, '_lock_overlay') or self._lock_overlay.get_size() != (aura_panel.width, aura_panel.height):
                self._lock_overlay = pygame.Surface((aura_panel.width, aura_panel.height), pygame.SRCALPHA)
            self._lock_overlay.fill((0, 0, 0, 180))
            self.screen.blit(self._lock_overlay, aura_panel)
            lock_msg = self.font_sub.render("TAPINAK KİLİTLİ: Önce Wave 10 Boss'unu Yenmelisin!", True, (231, 76, 60))
            self.screen.blit(lock_msg, lock_msg.get_rect(center=aura_panel.center))
                
        # Sayfalama Butonları - hitbox tek kaynak: rect'ler saklanır
        self.aura_prev_rect = pygame.Rect(aura_panel.x + 400, aura_panel.bottom - 40, 70, 30)
        self.aura_next_rect = pygame.Rect(aura_panel.x + 490, aura_panel.bottom - 40, 70, 30)
        if self.aura_page > 0:
            pygame.draw.rect(self.screen, (52, 152, 219), self.aura_prev_rect, border_radius=5)
            self.screen.blit(self.font_desc.render("<", True, (255, 255, 255)), (aura_panel.x + 430, aura_panel.bottom - 35))
        if (self.aura_page + 1) * 8 < len(all_auras):
            pygame.draw.rect(self.screen, (52, 152, 219), self.aura_next_rect, border_radius=5)
            self.screen.blit(self.font_desc.render(">", True, (255, 255, 255)), (aura_panel.x + 520, aura_panel.bottom - 35))

    def draw_synergy_tab(self, p):
        title = self.font_main.render("SİNERJİ REHBERİ", True, (241, 196, 15))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 120))
        
        synergies = getattr(self.logic.card_system.synergy_system, 'SYNERGIES', [])
        active_synergies = getattr(self.logic.card_system.synergy_system, 'active_synergies', [])
        
        active_names = self.logic.card_system.get_active_card_names()
                
        cards_title = self.font_sub.render(f"Sahip Olduğun Kartlar ({len(active_names)} Adet):", True, (200, 200, 200))
        self.screen.blit(cards_title, (self.width // 2 - 480, 160))
        
        if not active_names:
            cards_text = "Henüz kart alınmadı."
        else:
            cards_text = " • ".join(active_names)
            
        self.draw_text_wrapped(cards_text, self.width // 2 - 480, 190, 960, (150, 255, 150), self.font_desc)
        
        # Açıklama ve gereksinim satırlarına ayrı alan bırak.
        start_y = 240
        col_w = 460
        start_x_left = self.width // 2 - 480
        start_x_right = self.width // 2 + 20
        
        for i, syn in enumerate(synergies):
            is_active = syn['id'] in active_synergies
            
            x = start_x_left if i % 2 == 0 else start_x_right
            y = start_y + (i // 2) * 125
            
            rect = pygame.Rect(x, y, col_w, 115)
            
            bg_color = (40, 50, 40) if is_active else (30, 30, 35)
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=10)
            
            border_color = (46, 204, 113) if is_active else (100, 100, 100)
            pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=10)
            
            name_txt = self.font_sub.render(syn['name'], True, (255, 215, 0) if is_active else (150, 150, 150))
            self.screen.blit(name_txt, (x + 15, y + 10))
            
            status_str = "AKTİF!" if is_active else "KEŞFEDİLMEDİ"
            status_txt = self.font_sub.render(status_str, True, (46, 204, 113) if is_active else (100, 100, 100))
            self.screen.blit(status_txt, (x + col_w - status_txt.get_width() - 15, y + 10))
            
            self.draw_text_wrapped(
                syn['desc'], x + 15, y + 40, col_w - 30,
                (220, 220, 220) if is_active else (120, 120, 120),
                self.font_desc,
            )
            
            card_names = {card['id']: card['name'] for card in self.logic.card_system.CARDS}
            req_str = "Gereken: " + " + ".join(card_names.get(c, c) for c in syn['required_cards'])
            self.draw_text_wrapped(
                req_str, x + 15, y + 84, col_w - 30,
                (180, 180, 180) if is_active else (90, 90, 90),
                self.font_desc,
            )

    def draw_text_wrapped(self, text, x, y, max_width, color, font):
        """Metni belirtilen genişliğe göre satırlara bölerek çizer."""
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
        
        for i, line in enumerate(lines):
            l_surf = font.render(line, True, color)
            self.screen.blit(l_surf, (x, y + i * (font.get_height() + 2)))
            
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
