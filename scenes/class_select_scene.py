import pygame
from scenes.base_scene import BaseScene
from ui_elements import ClassCard

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
        card_w, card_h = 260, 400
        spacing_x, spacing_y = 30, 25
        num_cols = 4
        
        self.cards = []
        for i, data in enumerate(self.class_list):
            row = i // num_cols
            col = i % num_cols
            total_w = (card_w * num_cols) + (spacing_x * (num_cols - 1))
            start_x = (self.width - total_w) // 2 + card_w // 2
            x = start_x + col * (card_w + spacing_x)
            y = 120 + row * (card_h + spacing_y)
            # Re-filling detailed descriptions for the cards
            detailed_desc = {
                "warrior": ["Yakın dövüş uzmanı.", "Eski Kılıç ile başlar.", "+%20 Hasar ve +%20 Can."],
                "beastmaster": ["Pet odaklı uzman.", "Küçük Kurt ile başlar.", "Minyon Hasarı: +%30"],
                "sniper": ["Uzak mesafe uzmanı.", "Basit Arbalet ile başlar.", "+1 Sekme ve +1 Delme."],
                "engineer": ["Savunma ustası.", "Taret Kiti ile başlar.", "+10 Zırh ve Taretler."],
                "ninja": ["Suikastçı hızı.", "Paslı Katana ile başlar.", "+%30 Hız, %25 Kaçınma."],
                "alchemist": ["Zehir ve patlayıcılar.", "Zehir Şişesi ile başlar.", "+%40 Alan, +%30 DoT."],
                "sorcerer": ["3 Elementli Döngü.", "Sihir Asası ile başlar.", "Garantili Kritik+AoE."],
                "bloodwalker": ["Can çalan savaşçı.", "Kan Kılıcı ile başlar.", "Can çekme ve Rage modu."]
            }
            data["desc"] = detailed_desc.get(data["id"], data["desc"])
            self.cards.append(ClassCard(x, y, card_w, card_h, data, self.font_main, self.font_sub))

        # Boss Test Button
        self.boss_test_rect = pygame.Rect(self.width - 250, self.height - 80, 220, 50)
        self.selected_idx = 0 # Warrior by default
        self.preview_idx = 0

    def update(self, dt, events):
        mouse_clicked = False
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.manager.change_scene("MainMenu")

        for i, card in enumerate(self.cards):
            if card.update(events):
                self.selected_idx = i
                # Normal start on card click
                self.manager.start_new_game(self.class_list[i]['id'])
            
            # Hover detection
            if card.rect.collidepoint(mouse_pos):
                self.preview_idx = i

        if mouse_clicked and self.boss_test_rect.collidepoint(mouse_pos):
            # Use the hovered class if any, else use the last clicked one
            final_idx = self.preview_idx
            selected_class_id = self.class_list[final_idx]['id']
            self.manager.start_boss_test(selected_class_id)

    def draw(self):
        self.screen.fill(self.bg_color)
        title = self.font_main.render("SINIFINI SEÇ", True, (255, 255, 255))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 80))
        
        for i, card in enumerate(self.cards):
            card.draw(self.screen)
            # Draw a border around the previewed (hovered) class
            if i == self.preview_idx:
                pygame.draw.rect(self.screen, (255, 255, 255), card.rect, width=3, border_radius=12)
            
        info = self.font_sub.render("ESC ile geri dönebilirsin | Sınıfa tıkla veya Boss odasına git", True, (100, 100, 100))
        self.screen.blit(info, (self.width // 2 - info.get_width() // 2, self.height - 80))
        
        # Draw Boss Test Button
        mouse_pos = pygame.mouse.get_pos()
        color = (192, 57, 43) if self.boss_test_rect.collidepoint(mouse_pos) else (150, 40, 40)
        pygame.draw.rect(self.screen, color, self.boss_test_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), self.boss_test_rect, width=2, border_radius=8)
        bt_text = self.font_sub.render("BOSS DENEME ODASI", True, (255, 255, 255))
        self.screen.blit(bt_text, (self.boss_test_rect.centerx - bt_text.get_width()//2, self.boss_test_rect.centery - bt_text.get_height()//2))
