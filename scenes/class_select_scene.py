import pygame
from scenes.base_scene import BaseScene
from ui_elements import ClassCard, render_fit

class ClassSelectScene(BaseScene):
    def on_enter(self):
        self.bg_color = (20, 20, 30)
        
        # Sınıf Verileri
        self.class_list = [
            {"id": "warrior", "name": "Warrior", "color": (46, 204, 113), "desc": ["Yakın dövüş uzmanı."], "stats": {"HP": "+20%", "Hız": 5.0, "Hasar": "+20%"}},
            {"id": "beastmaster", "name": "Ruh Terbiyecisi", "color": (155, 89, 182), "desc": ["Pet odaklı uzman."], "stats": {"HP": "+10%", "Hız": 4.6, "Minyon": "+30%"}},
            {"id": "sniper", "name": "Keskin Nişancı", "color": (230, 126, 34), "desc": ["Uzak mesafe uzmanı."], "stats": {"Hız": 4.0, "Hasar": "+50%", "Sekme": "+1", "Delme": "+1"}},
            {"id": "engineer", "name": "Mühendis", "color": (52, 152, 219), "desc": ["Savunma ustası."], "stats": {"Zırh": "+10", "Hız": 4.2, "Taret": "+1"}},
            {"id": "ninja", "name": "Gölge Ninja", "color": (44, 62, 80), "desc": ["Suikastçı hızı."], "stats": {"Hız": 6.0, "S.Hızı": "+30%", "Dodge": "25%"}},
            {"id": "alchemist", "name": "Simyacı", "color": (241, 196, 15), "desc": ["Zehir ve patlayıcılar."], "stats": {"Hız": 4.2, "Alan": "+40%", "DoT": "+30%"}},
            {"id": "sorcerer", "name": "Kadim Büyücü", "color": (148, 88, 230), "desc": ["3 Elementli Döngü."], "stats": {"HP": "-30%", "Elem": "+60%", "Hız": 4.0}},
            {"id": "bloodwalker", "name": "Vampir", "color": (192, 40, 40), "desc": ["Can çalan savaşçı."], "stats": {"Hız": 4.6, "Emme": "+20%", "Hasar": "+40%"}}
        ]

        # Kartları Oluştur
        side_margin = max(32, self.width // 24)
        spacing_x, spacing_y = 18, 18
        num_cols = 4
        card_w = min(260, (self.width - side_margin * 2 - spacing_x * (num_cols - 1)) // num_cols)
        footer_h = 75
        grid_top = 135
        card_h = min(400, (self.height - grid_top - footer_h - spacing_y) // 2)
        card_h = max(260, card_h)
        
        self.cards = []
        for i, data in enumerate(self.class_list):
            row = i // num_cols
            col = i % num_cols
            total_w = (card_w * num_cols) + (spacing_x * (num_cols - 1))
            start_x = (self.width - total_w) // 2 + card_w // 2
            x = start_x + col * (card_w + spacing_x)
            y = grid_top + row * (card_h + spacing_y)
            # Re-filling detailed descriptions for the cards
            detailed_desc = {
                "warrior": ["Dayanıklı yakın dövüşçü.", "Kılıcı öndeki düşmanları biçer.", "+%20 hasar ve +%20 can."],
                "beastmaster": ["Minyonlarını hedefe yönlendirir.", "Küçük Kurt ile başlar.", "Minyon hasarı +%30."],
                "sniper": ["Güvenli mesafeden tek hedef avlar.", "Basit Arbalet ile başlar.", "+1 sekme, +1 delme, +%20 kritik."],
                "engineer": ["Alanı otomatik taretlerle tutar.", "Taret Kiti ile başlar.", "+10 zırh; 5 sn'de bir taret."],
                "ninja": ["Hızlı ve kaçınmaya dayalı suikastçı.", "Paslı Katana ile başlar.", "Atılma sonrası ilk vuruş 2 kat."],
                "alchemist": ["Zehir ve alan hasarı uzmanı.", "Zehir Şişesi ile başlar.", "+%40 patlama alanı, +%30 DoT."],
                "sorcerer": ["Ateş, buz ve zehir arasında döner.", "Sihir Asası ile başlar.", "Her 4. saldırı kritik ve 2 kat alanlı."],
                "bloodwalker": ["Can çalarak riskli oynar.", "Kan Kılıcı ile başlar.", "%30 can altında hasar ve hız +%40."]
            }
            data["desc"] = detailed_desc.get(data["id"], data["desc"])
            self.cards.append(ClassCard(x, y, card_w, card_h, data, self.font_main, self.font_sub))

        # Boss Test Button
        self.boss_test_rect = pygame.Rect(self.width - 250, self.height - 65, 220, 50)
        self.selected_idx = 0 # Warrior by default
        self.preview_idx = 0

    def update(self, dt, events):
        mouse_clicked = False
        mouse_pos = pygame.mouse.get_pos()
        mouse_moved = False
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True
            elif event.type == pygame.MOUSEMOTION:
                mouse_moved = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.manager.change_scene("MainMenu")
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self.preview_idx = (self.preview_idx - 1) % len(self.cards)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.preview_idx = (self.preview_idx + 1) % len(self.cards)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.preview_idx = (self.preview_idx - 4) % len(self.cards)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.preview_idx = (self.preview_idx + 4) % len(self.cards)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.manager.start_new_game(self.class_list[self.preview_idx]['id'])
                elif event.key == pygame.K_b:
                    self.manager.start_boss_test(self.class_list[self.preview_idx]['id'])

        for i, card in enumerate(self.cards):
            if card.update(events):
                self.selected_idx = i
                # Normal start on card click
                self.manager.start_new_game(self.class_list[i]['id'])
            
            # Hover detection
            if mouse_moved and card.rect.collidepoint(mouse_pos):
                self.preview_idx = i

        if mouse_clicked and self.boss_test_rect.collidepoint(mouse_pos):
            # Use the hovered class if any, else use the last clicked one
            final_idx = self.preview_idx
            selected_class_id = self.class_list[final_idx]['id']
            self.manager.start_boss_test(selected_class_id)

    def draw(self):
        self.screen.fill(self.bg_color)
        title = self.font_main.render("SINIFINI SEÇ", True, (255, 255, 255))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 30))
        
        for i, card in enumerate(self.cards):
            card.draw(self.screen)
            # Draw a border around the previewed (hovered) class
            if i == self.preview_idx:
                pygame.draw.rect(self.screen, (255, 255, 255), card.rect, width=3, border_radius=12)
            
        # Alt bilgi, boss butonuyla çakışmayacak genişliğe sığdırılır
        info_max_w = self.boss_test_rect.left - 60
        info = render_fit("Tıkla veya ENTER: Başla  •  Oklar/WASD: Seç  •  B: Boss testi  •  ESC: Geri", 20, (150, 150, 165), info_max_w)
        self.screen.blit(info, (30, self.height - 42))

        # Draw Boss Test Button
        mouse_pos = pygame.mouse.get_pos()
        color = (192, 57, 43) if self.boss_test_rect.collidepoint(mouse_pos) else (150, 40, 40)
        pygame.draw.rect(self.screen, color, self.boss_test_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), self.boss_test_rect, width=2, border_radius=8)
        bt_text = render_fit("BOSS DENEME ODASI", 24, (255, 255, 255), self.boss_test_rect.width - 20, bold=True)
        self.screen.blit(bt_text, bt_text.get_rect(center=self.boss_test_rect.center))
