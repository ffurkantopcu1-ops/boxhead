import pygame
from scenes.base_scene import BaseScene
from ui_elements import Button, get_font, render_fit, wrap_text
from logic.crystal_shop import CrystalShop
from logic.save_manager import SaveManager

class MenuScene(BaseScene):
    def on_enter(self):
        # Arka plan rengini ve başlığı belirle
        self.bg_color = (15, 15, 25)
        self.title_text = "BOXHEAD 2.0"
        self.subtitle_text = "NATIVE EVOLUTION"
        
        self.menu_state = "MAIN" # MAIN, LOAD, SETTINGS
        self.selected_idx = 0
        self.save_slots = []
        self.load_offset = 0
        self.shop_message = ""
        self.shop_message_timer = 0
        self.shop_message_success = False
        
        # Butonları oluştur
        button_width = 300
        button_height = 60
        self.start_y = self.height // 2 - 100 # Biraz daha yukarıdan başlatalım ki alta taşmasın
        
        # Buton Metinleri ve Renkleri (koyu fantastik tema paleti, bkz. DESIGN.md)
        import ui_theme
        C = ui_theme.COLORS
        self.main_buttons = [
            Button(self.width // 2, self.start_y, button_width, button_height, "YENİ OYUN", self.font_sub, C["blood"]),
            Button(self.width // 2, self.start_y + 70, button_width, button_height, "OYUN YÜKLE", self.font_sub, C["night"]),
            Button(self.width // 2, self.start_y + 140, button_width, button_height, "KALICI YETENEKLER (KRİSTAL)", self.font_sub, C["arcane"]),
            Button(self.width // 2, self.start_y + 210, button_width, button_height, "AYARLAR", self.font_sub, C["steel"]),
            Button(self.width // 2, self.start_y + 280, button_width, button_height, "YENİLİKLER", self.font_sub, C["gold"]),
            Button(self.width // 2, self.start_y + 350, button_width, button_height, "ÇIKIŞ", self.font_sub, C["ember"])
        ]
        self.notes_scroll = 0
        self.patch_notes = None  # PATCH_NOTES ekranına girince yüklenir

        self.shop = CrystalShop()
        self.meta_data = SaveManager.load_meta()
        self.shop_scroll = 0
        self._bg_cache = None

    def update(self, dt, events):
        if self.shop_message_timer > 0:
            self.shop_message_timer = max(0, self.shop_message_timer - dt)

        if self.menu_state == "MAIN":
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.selected_idx = (self.selected_idx - 1) % len(self.main_buttons)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.selected_idx = (self.selected_idx + 1) % len(self.main_buttons)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._trigger_main_action(self.selected_idx)

            # Buton durumlarını ve tıklamaları kontrol et
            for i, button in enumerate(self.main_buttons):
                if button.update(events):
                    self._trigger_main_action(i)

            for event in events:
                if event.type == pygame.MOUSEMOTION:
                    for i, button in enumerate(self.main_buttons):
                        if button.rect.collidepoint(event.pos):
                            self.selected_idx = i
                            break
                
        elif self.menu_state == "LOAD":
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = any(e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 for e in events)
            
            # Çizimde saklanan rect'ler kullanılır (tek kaynak)
            for i, slot_rect in enumerate(getattr(self, 'load_slot_rects', [])):
                if slot_rect.collidepoint(mouse_pos):
                    idx = self.load_offset + i
                    if idx >= len(self.save_slots):
                        continue
                    self.selected_idx = idx
                    if mouse_clicked:
                        slot = self.save_slots[self.selected_idx]
                        self.manager.load_game_from_menu(slot['filename'])
            
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.menu_state = "MAIN"
                    elif len(self.save_slots) > 0:
                        if event.key == pygame.K_UP:
                            self.selected_idx = (self.selected_idx - 1) % len(self.save_slots)
                        elif event.key == pygame.K_DOWN:
                            self.selected_idx = (self.selected_idx + 1) % len(self.save_slots)
                        elif event.key == pygame.K_RETURN:
                            slot = self.save_slots[self.selected_idx]
                            self.manager.load_game_from_menu(slot['filename'])
                        self._keep_selected_save_visible()

        elif self.menu_state == "SETTINGS":
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = any(e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 for e in events)
            
            # Çizimde saklanan rect'ler kullanılır (tek kaynak)
            for i, opt_rect in enumerate(getattr(self, 'settings_row_rects', [])):
                if opt_rect.collidepoint(mouse_pos):
                    self.selected_idx = i
                    if mouse_clicked:
                        self._trigger_setting_action(i)

            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.menu_state = "MAIN"
                    elif event.key == pygame.K_UP:
                        self.selected_idx = (self.selected_idx - 1) % 3
                    elif event.key == pygame.K_DOWN:
                        self.selected_idx = (self.selected_idx + 1) % 3
                    elif event.key == pygame.K_RETURN:
                        self._trigger_setting_action(self.selected_idx)

        elif self.menu_state == "PATCH_NOTES":
            for event in events:
                if event.type == pygame.MOUSEWHEEL:
                    self.notes_scroll += event.y * 40
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.menu_state = "MAIN"
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        self.notes_scroll += 40
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.notes_scroll -= 40
            # Sınırlar draw sırasında hesaplanan toplam yüksekliğe göre uygulanır
            max_up = getattr(self, '_notes_max_scroll', 0)
            self.notes_scroll = max(-max_up, min(0, self.notes_scroll))

        elif self.menu_state == "SHOP":
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = any(e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 for e in events)
            
            # Kaydırma
            for event in events:
                if event.type == pygame.MOUSEWHEEL:
                    self.shop_scroll += event.y * 30
                    
                    cols = 3
                    box_h = 124  # draw_crystal_shop ile ayni olmali, yoksa son satir kirpilir
                    padding = 20
                    num_items = len(self.shop.UPGRADES)
                    rows = (num_items + cols - 1) // cols
                    total_h = rows * (box_h + padding)
                    
                    min_scroll = min(0, self.height - 150 - total_h - 50)
                    self.shop_scroll = max(min_scroll, min(0, self.shop_scroll))
                    
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.menu_state = "MAIN"

            # Tıklama kontrolü: çizimde saklanan görünür rect'ler (tek kaynak)
            if mouse_clicked:
                for i, rect in getattr(self, 'shop_box_rects', {}).items():
                    if rect.collidepoint(mouse_pos):
                        upg = self.shop.UPGRADES[i]
                        meta_updated, success, msg = self.shop.purchase(self.meta_data, upg["id"])
                        if success:
                            SaveManager.save_meta(meta_updated)
                            self.meta_data = meta_updated
                        self.shop_message = msg
                        self.shop_message_timer = 2.5
                        self.shop_message_success = success
                        break

    def _trigger_setting_action(self, idx):
        if idx == 0:  # Shake
            self.manager.global_settings['shake'] = not self.manager.global_settings['shake']
            self.manager.save_settings()
        elif idx == 1:  # Ekran Modu (fullscreen -> borderless -> windowed)
            self.manager.cycle_display_mode()
        elif idx == 2:  # Back
            self.menu_state = "MAIN"

    def _trigger_main_action(self, idx):
        if idx == 0:
            self.manager.change_scene("ClassSelect")
        elif idx == 1:
            self.save_slots = SaveManager().get_save_slots()
            self.menu_state = "LOAD"
            self.selected_idx = 0
            self.load_offset = 0
        elif idx == 2:
            self.meta_data = SaveManager.load_meta()
            self.menu_state = "SHOP"
            self.shop_scroll = 0
        elif idx == 3:
            self.menu_state = "SETTINGS"
            self.selected_idx = 0
        elif idx == 4:
            self._load_patch_notes()
            self.menu_state = "PATCH_NOTES"
            self.notes_scroll = 0
        elif idx == 5:
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _load_patch_notes(self):
        if self.patch_notes is not None:
            return
        try:
            from logic.data_loader import load_data
            self.patch_notes = load_data('patch_notes').get('versions', [])
        except (OSError, ValueError, KeyError):
            self.patch_notes = []

    def _keep_selected_save_visible(self):
        if self.selected_idx < self.load_offset:
            self.load_offset = self.selected_idx
        elif self.selected_idx >= self.load_offset + 5:
            self.load_offset = self.selected_idx - 4

    def _draw_background(self):
        """Koyu taş zemin + vinyet (sınıf seçim ekranıyla aynı dil)."""
        import ui_theme
        if self._bg_cache is None or self._bg_cache.get_size() != (self.width, self.height):
            bg = pygame.Surface((self.width, self.height))
            top, bottom = (34, 29, 38), (16, 13, 18)
            for y in range(self.height):
                t = y / max(1, self.height - 1)
                pygame.draw.line(bg, tuple(int(top[i] + (bottom[i] - top[i]) * t)
                                           for i in range(3)), (0, y), (self.width, y))
            vig = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            steps = 60
            for i in range(steps):
                a = int(90 * (i / steps) ** 2)
                inset = int(min(self.width, self.height) * 0.5 * (1 - i / steps))
                pygame.draw.rect(vig, (0, 0, 0, a),
                                 pygame.Rect(inset, inset, self.width - inset * 2,
                                             self.height - inset * 2), width=6)
            bg.blit(vig, (0, 0))
            self._bg_cache = bg
        self.screen.fill(ui_theme.DARK_OUT)
        self.screen.blit(self._bg_cache, (0, 0))

    def draw(self):
        import ui_theme
        from ui_elements import get_skull_crest
        self._draw_background()

        # Başlıklar (tema serif + kurukafa arması)
        title_surf = ui_theme.render_title(self.title_text, 72)
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 2 - 250))
        self.screen.blit(title_surf, title_rect)
        crest = get_skull_crest(60)
        if crest is not None:
            cy = title_rect.centery - crest.get_height() // 2
            self.screen.blit(crest, (title_rect.left - crest.get_width() - 28, cy))
            self.screen.blit(crest, (title_rect.right + 28, cy))

        # Alt başlık sönük metal tonu: readable(night) parlak camgöbeğine
        # çıkıyor ve gotik palette yabancı duruyordu.
        sub_surf = render_fit(self.subtitle_text, 28, ui_theme.METAL_HI, self.width - 200)
        sub_rect = sub_surf.get_rect(center=(self.width // 2, self.height // 2 - 180))
        self.screen.blit(sub_surf, sub_rect)

        if self.menu_state == "MAIN":
            for i, button in enumerate(self.main_buttons):
                button.selected = (i == self.selected_idx)
                button.draw(self.screen)
        elif self.menu_state == "SETTINGS":
            self.draw_settings_menu()
        elif self.menu_state == "LOAD":
            self.draw_load_menu()
        elif self.menu_state == "SHOP":
            self.draw_shop_menu()
        elif self.menu_state == "PATCH_NOTES":
            self.draw_patch_notes_menu()

        # Sürüm ve Telif Hakkı (Alt Köşe)
        from logic.version import get_version
        version_surf = self.font_sub.render(f"v{get_version()}  •  ERKEN ERİŞİM", True, (80, 80, 80))
        self.screen.blit(version_surf, (20, self.height - 40))

    def draw_patch_notes_menu(self):
        import ui_theme
        panel = pygame.Rect(self.width // 2 - 400, 120, 800, self.height - 220)
        ui_theme.draw_panel(self.screen, panel, skull=True)

        title = render_fit("YENİLİKLER (PATCH NOTES)", 30, (230, 126, 34), panel.width - 40, bold=True)
        self.screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 16))

        content = pygame.Rect(panel.x + 30, panel.y + 65, panel.width - 60, panel.height - 105)
        self.screen.set_clip(content)

        font_ver = get_font(26, bold=True)
        font_cat = get_font(20, bold=True)
        font_note = get_font(18)

        y = content.y + self.notes_scroll
        notes = self.patch_notes or []
        if not notes:
            empty = font_note.render("Patch notes bulunamadı.", True, (150, 150, 160))
            self.screen.blit(empty, (content.x, y))
            y += 30
        for entry in notes:
            ver_txt = font_ver.render(f"v{entry['version']}  •  {entry.get('date', '')}", True, (241, 196, 15))
            self.screen.blit(ver_txt, (content.x, y))
            y += ver_txt.get_height() + 8
            for cat, items in entry.get('categories', {}).items():
                cat_txt = font_cat.render(cat, True, (52, 152, 219))
                self.screen.blit(cat_txt, (content.x + 15, y))
                y += cat_txt.get_height() + 4
                for note in items:
                    note_txt = render_fit(f"• {note}", 18, (210, 210, 220), content.width - 50)
                    self.screen.blit(note_txt, (content.x + 35, y))
                    y += note_txt.get_height() + 3
                y += 6
            pygame.draw.line(self.screen, (60, 65, 90), (content.x, y + 6), (content.right, y + 6))
            y += 24

        total_height = (y - self.notes_scroll) - content.y
        self._notes_max_scroll = max(0, total_height - content.height)
        self.screen.set_clip(None)

        hint = render_fit("ESC: Geri  •  Tekerlek/Ok Tuşları: Kaydır", 18, (110, 110, 125), panel.width - 40)
        self.screen.blit(hint, (panel.centerx - hint.get_width() // 2, panel.bottom - 32))

    def draw_settings_menu(self):
        import ui_theme
        panel = pygame.Rect(self.width // 2 - 250, self.height // 2 - 50, 500, 300)
        ui_theme.draw_panel(self.screen, panel)

        title = render_fit("AYARLAR", 30, (149, 165, 166), panel.width - 40, bold=True)
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, panel.y + 18))

        opts = [
            f"EKRAN SARSINTISI: {'[AÇIK]' if self.manager.global_settings['shake'] else '[KAPALI]'}",
            f"EKRAN MODU: [{self.manager.get_display_mode_label()}]",
            "ANA MENÜYE DÖN"
        ]

        self.settings_row_rects = []
        for i, opt in enumerate(opts):
            # +84: 30 punto başlık panel.y+18'de başlayıp ~y+56'ya kadar iniyor;
            # satırlar y+40'tan başlayınca opak dolgusu başlığın altını kesiyordu.
            row_rect = pygame.Rect(self.width // 2 - 200, panel.y + 84 + i * 70 - 20, 400, 50)
            self.settings_row_rects.append(row_rect)
            active = i == self.selected_idx
            ui_theme.draw_plate(self.screen, row_rect, "hover" if active else "normal",
                                ui_theme.COLORS["steel"])
            color = ui_theme.TEXT_COL if active else (176, 170, 158)
            txt = render_fit(opt, 24, color, row_rect.width - 60, bold=active)
            self.screen.blit(txt, txt.get_rect(center=row_rect.center))

        hint = render_fit("ESC: Geri  •  ENTER: Seç", 18, (110, 110, 125), panel.width - 40)
        self.screen.blit(hint, (self.width // 2 - hint.get_width() // 2, panel.bottom - 40))

    def draw_load_menu(self):
        import ui_theme
        panel = pygame.Rect(self.width // 2 - 300, self.height // 2 - 100, 600, 400)
        ui_theme.draw_panel(self.screen, panel)
        
        title = ui_theme.render_title("KAYIT SEÇ", 32,
                                      ui_theme.readable(ui_theme.COLORS["night"]))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, panel.y + 24))

        if not self.save_slots:
            # Bayat rect'ler: kayıt silindikten sonra eski satırlar hâlâ
            # tıklanabilir kalıyor ve IndexError yaratıyordu (P4)
            self.load_slot_rects = []
            msg = render_fit("KAYIT BULUNAMADI", 26, (150, 145, 135), panel.width - 40)
            self.screen.blit(msg, (self.width // 2 - msg.get_width() // 2, panel.y + 150))
        else:
            self.load_slot_rects = []
            for i, slot in enumerate(self.save_slots[self.load_offset:self.load_offset + 5]):
                actual_idx = self.load_offset + i
                row_rect = pygame.Rect(self.width // 2 - 250, panel.y + 100 + i * 54 - 20, 500, 44)
                self.load_slot_rects.append(row_rect)
                is_selected = actual_idx == self.selected_idx
                ui_theme.draw_plate(self.screen, row_rect,
                                    "hover" if is_selected else "normal",
                                    ui_theme.COLORS["night"])
                color = ui_theme.TEXT_COL if is_selected else (176, 170, 158)
                slot_txt = f"SEVİYE {slot['level']}  •  DALGA {slot['wave']}  •  {slot['class'].upper()}"
                txt = render_fit(slot_txt, 22, color, row_rect.width - 60, bold=is_selected)
                self.screen.blit(txt, txt.get_rect(center=row_rect.center))

        footer = "ESC: Geri"
        if len(self.save_slots) > 5:
            footer += f"  •  {self.selected_idx + 1}/{len(self.save_slots)}"
        back_msg = render_fit(footer, 20, (110, 110, 125), panel.width - 40)
        self.screen.blit(back_msg, (self.width // 2 - back_msg.get_width() // 2, panel.bottom - 40))

    def draw_shop_menu(self):
        import ui_theme
        arcane = ui_theme.readable(ui_theme.COLORS["arcane"])

        # Dükkan tam ekran: draw() ana menü başlığını koşulsuz çiziyor,
        # ızgaranın arasından "BOXHEAD 2.0" sızıyordu.
        self._draw_background()

        # Üst Panel
        pygame.draw.rect(self.screen, (22, 19, 28), (0, 0, self.width, 100))
        pygame.draw.line(self.screen, ui_theme.METAL, (0, 100), (self.width, 100), 2)
        pygame.draw.line(self.screen, ui_theme.DARK_OUT, (0, 102), (self.width, 102), 1)

        # Başlık ve kristal sayacı üst bara dikey olarak ortalanır (eski 72pt font bardan taşıyordu)
        title = ui_theme.render_title("KALICI YETENEKLER", 38, arcane)
        self.screen.blit(title, (40, 50 - title.get_height() // 2))

        crystals = self.meta_data.get("crystals", 0)
        c_text = render_fit(f"{crystals} Kristal", 30,
                            ui_theme.readable(ui_theme.COLORS["night"], 200),
                            self.width // 2 - 60, bold=True)
        self.screen.blit(c_text, (self.width - c_text.get_width() - 40, 50 - c_text.get_height() // 2))

        # Grid Alanı — kutu yüksekliği 124: çerçevenin köşe süsleri 40px,
        # 100px'lik kutuda üç metin satırına yer kalmıyordu.
        cols = 3
        box_w, box_h = 300, 124
        padding = 20
        start_x = self.width // 2 - ((cols * box_w + (cols - 1) * padding) // 2)
        start_y = 150 + self.shop_scroll

        mouse_pos = pygame.mouse.get_pos()

        # Hitbox tek kaynak: görünen kutu rect'leri saklanır
        self.shop_box_rects = {}
        for i, upg in enumerate(self.shop.UPGRADES):
            col = i % cols
            row = i // cols
            rect = pygame.Rect(start_x + col * (box_w + padding), start_y + row * (box_h + padding), box_w, box_h)

            # Sadece ekrandakileri çiz
            if rect.bottom < 100 or rect.top > self.height:
                continue
            self.shop_box_rects[i] = rect

            hover = rect.collidepoint(mouse_pos)
            rank = self.shop.get_rank(self.meta_data, upg["id"])
            is_max = rank >= upg["max_rank"]
            cost = self.shop.get_cost(upg["id"], rank)

            accent = ui_theme.COLORS["moss"] if is_max else ui_theme.COLORS["arcane"]
            c = ui_theme.draw_inset_frame(
                self.screen, rect, "panel_frame_small.png",
                fill=(30, 24, 38) if hover else (24, 20, 30), alpha=246,
                tint=tuple(int(v * (0.46 if hover else 0.28)) for v in accent),
                glow=(ui_theme.readable(accent), 110) if hover else None, pad=16)

            # Üst/alt satır köşe süslerinin hizasında: yatayda ek pay bırakılır
            # (çerçeve köşeleri 40px, pad 16 -> her yanda 24px kalıyor)
            edge = 22
            ex, ew = c.x + edge, c.width - edge * 2

            # Rank (Seviye) — önce ölç ki isim ona göre daralsın
            r_txt = render_fit(f"{rank}/{upg['max_rank']}", 18, (186, 180, 168), 70)
            self.screen.blit(r_txt, (ex + ew - r_txt.get_width(), c.y))

            # İsim (rank etiketiyle çakışmadan sığdırılır)
            n_txt = render_fit(upg["name"], 21, ui_theme.TEXT_COL,
                               ew - r_txt.get_width() - 12, bold=True)
            self.screen.blit(n_txt, (ex, c.y))

            # Seviye ilerleme çubuğu: ismin ÖLÇÜLEN altına (sabit ofset değil)
            bar_rect = pygame.Rect(c.x, c.y + n_txt.get_height() + 8, c.width, 6)
            pygame.draw.rect(self.screen, ui_theme.METAL_LO, bar_rect, border_radius=3)
            if upg['max_rank'] > 0 and rank > 0:
                fill_w = int(bar_rect.width * min(1, rank / upg['max_rank']))
                fill_color = ui_theme.readable(accent)
                pygame.draw.rect(self.screen, fill_color, (bar_rect.x, bar_rect.y, fill_w, 6), border_radius=3)

            # Fiyat
            if not is_max:
                cost_color = (ui_theme.readable(ui_theme.COLORS["night"], 200)
                              if crystals >= cost else ui_theme.readable(ui_theme.COLORS["blood"]))
                c_lbl = render_fit(f"Maliyet: {cost}", 20, cost_color, ew)
            else:
                c_lbl = render_fit("MAKSİMUM", 20, ui_theme.readable(ui_theme.COLORS["moss"]),
                                   ew, bold=True)
            self.screen.blit(c_lbl, (ex, c.bottom - c_lbl.get_height()))

            # Hover edilen yeteneği kaydet ki tooltipi en üste (diğer rect'lerin üzerine) çizelim
            if hover:
                hovered_upg = upg

        # ESC ile çıkış uyarısı — sol altta sürüm etiketi var, ortaya alınır
        esc_txt = render_fit("Ana Menü için ESC", 22, (150, 144, 132), 400)
        self.screen.blit(esc_txt, (self.width // 2 - esc_txt.get_width() // 2,
                                   self.height - 40))

        if self.shop_message_timer > 0 and self.shop_message:
            msg_color = (ui_theme.readable(ui_theme.COLORS["moss"]) if self.shop_message_success
                         else ui_theme.readable(ui_theme.COLORS["blood"]))
            msg = render_fit(self.shop_message, 24, msg_color, self.width - 120, bold=True)
            msg_bg = msg.get_rect(center=(self.width // 2, 128)).inflate(40, 18)
            ui_theme.draw_plate(self.screen, msg_bg, "normal")
            self.screen.blit(msg, msg.get_rect(center=msg_bg.center))

        # Tooltip Çizimi (En Üst Katman)
        if 'hovered_upg' in locals() and hovered_upg:
            rank = self.meta_data.get("upgrades", {}).get(hovered_upg["id"], 0)
            is_max = rank >= hovered_upg["max_rank"]
            category_names = {
                "survival": "Hayatta Kalma", "economy": "Ekonomi",
                "combat": "Savaş", "cards": "Kartlar", "special": "Özel",
            }
            max_text_width = 370
            desc_font = get_font(20)
            # Ortak wrap_text (burada elle yazılmış bir kopyası vardı)
            desc_lines = wrap_text(desc_font, hovered_upg["desc"], max_text_width)

            meta_line = f"{category_names.get(hovered_upg['category'], 'Yükseltme')}  •  Seviye {rank}/{hovered_upg['max_rank']}"
            cost = self.shop.get_cost(hovered_upg["id"], rank)
            cost_line = "Tamamen geliştirildi" if is_max else f"Sonraki seviye: {cost} kristal"
            tw = max(
                300,
                self.font_desc.size(meta_line)[0] + 24,
                self.font_desc.size(cost_line)[0] + 24,
                *(desc_font.size(line)[0] + 24 for line in desc_lines),
            )
            line_height = desc_font.get_height() + 3
            th = 58 + len(desc_lines) * line_height
            mx, my = pygame.mouse.get_pos()
            
            # Ekrana sığdır
            tx = mx + 15
            ty = my + 15
            if tx + tw > self.width: tx = self.width - tw - 10
            if ty + th > self.height: ty = self.height - th - 10
            
            t_rect = pygame.Rect(tx, ty, tw, th)
            ui_theme.draw_panel(self.screen, t_rect, fill=(20, 17, 24), alpha=245,
                                nineslice=False)
            meta_txt = self.font_desc.render(meta_line, True, (178, 172, 160))
            self.screen.blit(meta_txt, (tx + 12, ty + 9))
            for i, line in enumerate(desc_lines):
                desc_txt = desc_font.render(line, True, ui_theme.TEXT_COL)
                self.screen.blit(desc_txt, (tx + 12, ty + 28 + i * line_height))
            cost_color = (ui_theme.readable(ui_theme.COLORS["moss"])
                          if is_max or crystals >= (cost or 0)
                          else ui_theme.readable(ui_theme.COLORS["blood"]))
            cost_txt = self.font_desc.render(cost_line, True, cost_color)
            self.screen.blit(cost_txt, (tx + 12, t_rect.bottom - cost_txt.get_height() - 8))
