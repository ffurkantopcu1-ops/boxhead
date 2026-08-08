import pygame
from scenes.base_scene import BaseScene
from ui_elements import Button, get_font, render_fit
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
                    self.selected_idx = self.load_offset + i
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
                        if i == 0: self.manager.global_settings['shake'] = not self.manager.global_settings['shake']
                        elif i == 1: self.menu_state = "MAIN"
            
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.menu_state = "MAIN"
                    elif event.key == pygame.K_UP:
                        self.selected_idx = (self.selected_idx - 1) % 2
                    elif event.key == pygame.K_DOWN:
                        self.selected_idx = (self.selected_idx + 1) % 2
                    elif event.key == pygame.K_RETURN:
                        if self.selected_idx == 0: # Shake
                            self.manager.global_settings['shake'] = not self.manager.global_settings['shake']
                        elif self.selected_idx == 1: # Back
                            self.menu_state = "MAIN"

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
                    box_h = 100
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

    def draw(self):
        # Arka Plan
        self.screen.fill(self.bg_color)
        
        # Başlıklar
        title_surf = self.font_main.render(self.title_text, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 2 - 250))
        self.screen.blit(title_surf, title_rect)
        
        sub_surf = self.font_sub.render(self.subtitle_text, True, (52, 152, 219))
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
        version_surf = self.font_sub.render(f"v{get_version()}", True, (80, 80, 80))
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
            "ANA MENÜYE DÖN"
        ]

        self.settings_row_rects = []
        for i, opt in enumerate(opts):
            row_rect = pygame.Rect(self.width // 2 - 200, panel.y + 60 + i * 70 - 20, 400, 50)
            self.settings_row_rects.append(row_rect)
            if i == self.selected_idx:
                pygame.draw.rect(self.screen, (45, 45, 65), row_rect, border_radius=8)
                pygame.draw.rect(self.screen, (241, 196, 15), row_rect, width=2, border_radius=8)
            color = (255, 255, 255) if i == self.selected_idx else (150, 150, 160)
            txt = render_fit(opt, 26, color, row_rect.width - 24)
            self.screen.blit(txt, txt.get_rect(center=row_rect.center))

        hint = render_fit("ESC: Geri  •  ENTER: Seç", 18, (110, 110, 125), panel.width - 40)
        self.screen.blit(hint, (self.width // 2 - hint.get_width() // 2, panel.bottom - 40))

    def draw_load_menu(self):
        import ui_theme
        panel = pygame.Rect(self.width // 2 - 300, self.height // 2 - 100, 600, 400)
        ui_theme.draw_panel(self.screen, panel)
        
        title = self.font_sub.render("KAYIT SEÇ", True, (52, 152, 219))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, panel.y + 30))
        
        if not self.save_slots:
            msg = render_fit("KAYIT BULUNAMADI", 26, (150, 150, 150), panel.width - 40)
            self.screen.blit(msg, (self.width // 2 - msg.get_width() // 2, panel.y + 150))
        else:
            self.load_slot_rects = []
            for i, slot in enumerate(self.save_slots[self.load_offset:self.load_offset + 5]):
                actual_idx = self.load_offset + i
                row_rect = pygame.Rect(self.width // 2 - 250, panel.y + 100 + i * 50 - 20, 500, 40)
                self.load_slot_rects.append(row_rect)
                is_selected = actual_idx == self.selected_idx
                if is_selected:
                    pygame.draw.rect(self.screen, (45, 45, 65), row_rect, border_radius=8)
                    pygame.draw.rect(self.screen, (52, 152, 219), row_rect, width=2, border_radius=8)
                color = (255, 255, 255) if is_selected else (150, 150, 160)
                slot_txt = f"SEVİYE {slot['level']}  •  DALGA {slot['wave']}  •  {slot['class'].upper()}"
                txt = render_fit(slot_txt, 24, color, row_rect.width - 24)
                self.screen.blit(txt, txt.get_rect(center=row_rect.center))

        footer = "ESC: Geri"
        if len(self.save_slots) > 5:
            footer += f"  •  {self.selected_idx + 1}/{len(self.save_slots)}"
        back_msg = render_fit(footer, 20, (110, 110, 125), panel.width - 40)
        self.screen.blit(back_msg, (self.width // 2 - back_msg.get_width() // 2, panel.bottom - 40))

    def draw_shop_menu(self):
        # Üst Panel
        pygame.draw.rect(self.screen, (20, 20, 30), (0, 0, self.width, 100))
        pygame.draw.line(self.screen, (155, 89, 182), (0, 100), (self.width, 100), 2)

        # Başlık ve kristal sayacı üst bara dikey olarak ortalanır (eski 72pt font bardan taşıyordu)
        title = render_fit("KALICI YETENEKLER", 40, (155, 89, 182), self.width // 2 - 60, bold=True)
        self.screen.blit(title, (40, 50 - title.get_height() // 2))

        crystals = self.meta_data.get("crystals", 0)
        c_text = render_fit(f"💎 {crystals} Kristal", 32, (100, 220, 255), self.width // 2 - 60, bold=True)
        self.screen.blit(c_text, (self.width - c_text.get_width() - 40, 50 - c_text.get_height() // 2))

        # Grid Alanı
        cols = 3
        box_w, box_h = 300, 100
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

            bg_color = (40, 30, 50) if hover else (30, 20, 40)
            if is_max: bg_color = (20, 40, 20)
            
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=10)
            pygame.draw.rect(self.screen, (155, 89, 182) if hover else (100, 50, 120), rect, width=2, border_radius=10)

            # Rank (Seviye) — önce ölç ki isim ona göre daralsın
            r_txt = render_fit(f"{rank}/{upg['max_rank']}", 18, (200, 200, 200), 70)
            self.screen.blit(r_txt, (rect.right - r_txt.get_width() - 12, rect.y + 12))

            # İsim (rank etiketiyle çakışmadan sığdırılır)
            n_txt = render_fit(upg["name"], 22, (255, 255, 255), rect.width - r_txt.get_width() - 34, bold=True)
            self.screen.blit(n_txt, (rect.x + 12, rect.y + 10))

            # Seviye ilerleme çubuğu
            bar_rect = pygame.Rect(rect.x + 12, rect.y + 44, rect.width - 24, 6)
            pygame.draw.rect(self.screen, (50, 40, 65), bar_rect, border_radius=3)
            if upg['max_rank'] > 0 and rank > 0:
                fill_w = int(bar_rect.width * min(1, rank / upg['max_rank']))
                fill_color = (100, 255, 100) if is_max else (155, 89, 182)
                pygame.draw.rect(self.screen, fill_color, (bar_rect.x, bar_rect.y, fill_w, 6), border_radius=3)

            # Fiyat
            if not is_max:
                cost_color = (100, 220, 255) if crystals >= cost else (255, 100, 100)
                c_lbl = render_fit(f"Maliyet: {cost} 💎", 20, cost_color, rect.width - 24)
            else:
                c_lbl = render_fit("MAKSİMUM", 20, (100, 255, 100), rect.width - 24, bold=True)
            self.screen.blit(c_lbl, (rect.x + 12, rect.bottom - c_lbl.get_height() - 10))

            # Hover edilen yeteneği kaydet ki tooltipi en üste (diğer rect'lerin üzerine) çizelim
            if hover:
                hovered_upg = upg

        # ESC ile çıkış uyarısı
        esc_txt = self.font_sub.render("Ana Menü için ESC", True, (150, 150, 150))
        self.screen.blit(esc_txt, (20, self.height - 40))

        if self.shop_message_timer > 0 and self.shop_message:
            msg_color = (120, 255, 160) if self.shop_message_success else (255, 130, 130)
            msg = self.font_sub.render(self.shop_message, True, msg_color)
            msg_bg = msg.get_rect(center=(self.width // 2, 125)).inflate(24, 14)
            pygame.draw.rect(self.screen, (20, 20, 30), msg_bg, border_radius=8)
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
            words = hovered_upg["desc"].split()
            desc_lines, current = [], []
            for word in words:
                candidate = " ".join(current + [word])
                if desc_font.size(candidate)[0] <= max_text_width:
                    current.append(word)
                else:
                    if current:
                        desc_lines.append(" ".join(current))
                    current = [word]
            if current:
                desc_lines.append(" ".join(current))

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
            pygame.draw.rect(self.screen, (20, 20, 30), t_rect, border_radius=8)
            pygame.draw.rect(self.screen, (241, 196, 15), t_rect, width=2, border_radius=8)
            meta_txt = self.font_desc.render(meta_line, True, (180, 180, 195))
            self.screen.blit(meta_txt, (tx + 12, ty + 9))
            for i, line in enumerate(desc_lines):
                desc_txt = desc_font.render(line, True, (255, 255, 220))
                self.screen.blit(desc_txt, (tx + 12, ty + 28 + i * line_height))
            cost_color = (120, 255, 160) if is_max or crystals >= (cost or 0) else (255, 130, 130)
            cost_txt = self.font_desc.render(cost_line, True, cost_color)
            self.screen.blit(cost_txt, (tx + 12, t_rect.bottom - cost_txt.get_height() - 8))
