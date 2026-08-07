import pygame
from scenes.base_scene import BaseScene
from ui_elements import Button
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
        
        # Buton Metinleri ve Renkleri
        self.main_buttons = [
            Button(self.width // 2, self.start_y, button_width, button_height, "YENİ OYUN", self.font_sub, (46, 204, 113), (39, 174, 96)),
            Button(self.width // 2, self.start_y + 70, button_width, button_height, "OYUN YÜKLE", self.font_sub, (52, 152, 219), (41, 128, 185)),
            Button(self.width // 2, self.start_y + 140, button_width, button_height, "KALICI YETENEKLER (KRİSTAL)", self.font_sub, (155, 89, 182), (142, 68, 173)),
            Button(self.width // 2, self.start_y + 210, button_width, button_height, "AYARLAR", self.font_sub, (149, 165, 166), (127, 140, 141)),
            Button(self.width // 2, self.start_y + 280, button_width, button_height, "ÇIKIŞ", self.font_sub, (231, 76, 60), (192, 57, 43))
        ]

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
            if self.main_buttons[0].update(events): # New Game
                self._trigger_main_action(0)
            if self.main_buttons[1].update(events): # Load Game
                self._trigger_main_action(1)
            if self.main_buttons[2].update(events): # Upgrades
                self._trigger_main_action(2)
            if self.main_buttons[3].update(events): # Settings
                self._trigger_main_action(3)
            if self.main_buttons[4].update(events): # Exit
                self._trigger_main_action(4)

            for event in events:
                if event.type == pygame.MOUSEMOTION:
                    for i, button in enumerate(self.main_buttons):
                        if button.rect.collidepoint(event.pos):
                            self.selected_idx = i
                            break
                
        elif self.menu_state == "LOAD":
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = any(e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 for e in events)
            
            panel_y = self.height // 2 - 100
            visible_slots = self.save_slots[self.load_offset:self.load_offset + 5]
            for i in range(len(visible_slots)):
                slot_rect = pygame.Rect(self.width // 2 - 250, panel_y + 100 + i * 50 - 20, 500, 40)
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
            
            panel_y = self.height // 2 - 50
            for i in range(2):
                opt_rect = pygame.Rect(self.width // 2 - 200, panel_y + 60 + i * 70 - 20, 400, 50)
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

            # Tıklama kontrolü grid üzerinden
            cols = 3
            box_w, box_h = 300, 100
            padding = 20
            start_x = self.width // 2 - ((cols * box_w + (cols - 1) * padding) // 2)
            start_y = 150 + self.shop_scroll
            
            for i, upg in enumerate(self.shop.UPGRADES):
                col = i % cols
                row = i // cols
                rect = pygame.Rect(start_x + col * (box_w + padding), start_y + row * (box_h + padding), box_w, box_h)
                
                # Sadece ekranda görünenlere tıklanabilir
                if rect.bottom > 100 and rect.top < self.height:
                    if rect.collidepoint(mouse_pos) and mouse_clicked:
                        meta_updated, success, msg = self.shop.purchase(self.meta_data, upg["id"])
                        if success:
                            SaveManager.save_meta(meta_updated)
                            self.meta_data = meta_updated
                        self.shop_message = msg
                        self.shop_message_timer = 2.5
                        self.shop_message_success = success

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
            pygame.event.post(pygame.event.Event(pygame.QUIT))

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
                if i == self.selected_idx:
                    pygame.draw.rect(self.screen, (241, 196, 15), button.rect.inflate(8, 8), width=2, border_radius=13)
                button.draw(self.screen)
        elif self.menu_state == "SETTINGS":
            self.draw_settings_menu()
        elif self.menu_state == "LOAD":
            self.draw_load_menu()
        elif self.menu_state == "SHOP":
            self.draw_shop_menu()

        # Sürüm ve Telif Hakkı (Alt Köşe)
        from logic.version import get_version
        version_surf = self.font_sub.render(f"v{get_version()}", True, (80, 80, 80))
        self.screen.blit(version_surf, (20, self.height - 40))

    def draw_settings_menu(self):
        panel = pygame.Rect(self.width // 2 - 250, self.height // 2 - 50, 500, 300)
        pygame.draw.rect(self.screen, (30, 30, 45), panel, border_radius=15)
        pygame.draw.rect(self.screen, (100, 100, 120), panel, width=2, border_radius=15)
        
        opts = [
            f"EKRAN SARSINTISI: {'[AÇIK]' if self.manager.global_settings['shake'] else '[KAPALI]'}",
            "ANA MENÜYE DÖN"
        ]
        
        for i, opt in enumerate(opts):
            color = (255, 255, 255) if i == self.selected_idx else (120, 120, 120)
            txt = self.font_sub.render(opt, True, color)
            self.screen.blit(txt, (self.width // 2 - txt.get_width() // 2, panel.y + 60 + i * 70))

    def draw_load_menu(self):
        panel = pygame.Rect(self.width // 2 - 300, self.height // 2 - 100, 600, 400)
        pygame.draw.rect(self.screen, (30, 30, 45), panel, border_radius=15)
        pygame.draw.rect(self.screen, (100, 100, 120), panel, width=2, border_radius=15)
        
        title = self.font_sub.render("KAYIT SEÇ", True, (52, 152, 219))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, panel.y + 30))
        
        if not self.save_slots:
            msg = self.font_sub.render("KAYIT BULUNAMADI", True, (150, 150, 150))
            self.screen.blit(msg, (self.width // 2 - msg.get_width() // 2, panel.y + 150))
        else:
            for i, slot in enumerate(self.save_slots[self.load_offset:self.load_offset + 5]):
                actual_idx = self.load_offset + i
                color = (255, 255, 255) if actual_idx == self.selected_idx else (120, 120, 120)
                slot_txt = f"{slot['level']} LVL - WAVE {slot['wave']} ({slot['class'].upper()})"
                txt = self.font_sub.render(slot_txt, True, color)
                txt_scale = pygame.transform.scale(txt, (int(txt.get_width()*0.8), int(txt.get_height()*0.8)))
                self.screen.blit(txt_scale, (self.width // 2 - txt_scale.get_width() // 2, panel.y + 100 + i * 50))
        
        footer = "ESC: Geri"
        if len(self.save_slots) > 5:
            footer += f"  •  {self.selected_idx + 1}/{len(self.save_slots)}"
        back_msg = self.font_sub.render(footer, True, (100, 100, 100))
        self.screen.blit(back_msg, (self.width // 2 - back_msg.get_width() // 2, panel.bottom - 40))

    def draw_shop_menu(self):
        # Üst Panel
        pygame.draw.rect(self.screen, (20, 20, 30), (0, 0, self.width, 100))
        pygame.draw.line(self.screen, (155, 89, 182), (0, 100), (self.width, 100), 2)
        
        title = self.font_main.render("META UPGRADES", True, (155, 89, 182))
        self.screen.blit(title, (40, 30))
        
        crystals = self.meta_data.get("crystals", 0)
        c_text = self.font_main.render(f"💎 {crystals} Kristal", True, (100, 220, 255))
        self.screen.blit(c_text, (self.width - c_text.get_width() - 40, 30))

        # Grid Alanı
        cols = 3
        box_w, box_h = 300, 100
        padding = 20
        start_x = self.width // 2 - ((cols * box_w + (cols - 1) * padding) // 2)
        start_y = 150 + self.shop_scroll

        mouse_pos = pygame.mouse.get_pos()

        for i, upg in enumerate(self.shop.UPGRADES):
            col = i % cols
            row = i // cols
            rect = pygame.Rect(start_x + col * (box_w + padding), start_y + row * (box_h + padding), box_w, box_h)
            
            # Sadece ekrandakileri çiz
            if rect.bottom < 100 or rect.top > self.height:
                continue

            hover = rect.collidepoint(mouse_pos)
            rank = self.shop.get_rank(self.meta_data, upg["id"])
            is_max = rank >= upg["max_rank"]
            cost = self.shop.get_cost(upg["id"], rank)

            bg_color = (40, 30, 50) if hover else (30, 20, 40)
            if is_max: bg_color = (20, 40, 20)
            
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=10)
            pygame.draw.rect(self.screen, (155, 89, 182) if hover else (100, 50, 120), rect, width=2, border_radius=10)

            # İsim
            n_txt = self.font_sub.render(upg["name"], True, (255, 255, 255))
            n_scale = pygame.transform.scale(n_txt, (int(n_txt.get_width()*0.8), int(n_txt.get_height()*0.8)))
            self.screen.blit(n_scale, (rect.x + 10, rect.y + 10))

            # Rank (Seviye)
            r_txt = self.font_sub.render(f"[{rank}/{upg['max_rank']}]", True, (200, 200, 200))
            r_scale = pygame.transform.scale(r_txt, (int(r_txt.get_width()*0.7), int(r_txt.get_height()*0.7)))
            self.screen.blit(r_scale, (rect.right - r_scale.get_width() - 10, rect.y + 10))

            # Fiyat
            if not is_max:
                cost_color = (100, 220, 255) if crystals >= cost else (255, 100, 100)
                c_lbl = self.font_sub.render(f"Maliyet: {cost} 💎", True, cost_color)
            else:
                c_lbl = self.font_sub.render("MAKSİMUM", True, (100, 255, 100))
            c_scale = pygame.transform.scale(c_lbl, (int(c_lbl.get_width()*0.8), int(c_lbl.get_height()*0.8)))
            self.screen.blit(c_scale, (rect.x + 10, rect.bottom - c_scale.get_height() - 10))

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
            words = hovered_upg["desc"].split()
            desc_lines, current = [], []
            for word in words:
                candidate = " ".join(current + [word])
                if self.font_sub.size(candidate)[0] <= max_text_width:
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
                *(self.font_sub.size(line)[0] + 24 for line in desc_lines),
            )
            line_height = self.font_sub.get_height() + 3
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
                desc_txt = self.font_sub.render(line, True, (255, 255, 220))
                self.screen.blit(desc_txt, (tx + 12, ty + 28 + i * line_height))
            cost_color = (120, 255, 160) if is_max or crystals >= (cost or 0) else (255, 130, 130)
            cost_txt = self.font_desc.render(cost_line, True, cost_color)
            self.screen.blit(cost_txt, (tx + 12, t_rect.bottom - cost_txt.get_height() - 8))
