import pygame
from scenes.base_scene import BaseScene
from ui_elements import Button, ClassCard, render_fit, get_skull_crest

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
            {"id": "bloodwalker", "name": "Vampir", "color": (192, 40, 40), "desc": ["Can çalan savaşçı."], "stats": {"Hız": 4.6, "Emme": "+20%", "Hasar": "+40%"}},
            {"id": "bomber", "name": "Bombacı", "color": (211, 84, 0), "desc": ["Patlayıcı alan uzmanı."], "stats": {"Hız": 4.4, "Alan": "+60%", "Hasar": "+20%"}}
        ]

        detailed_desc = {
            "warrior": ["Dayanıklı yakın dövüşçü.", "Kılıcı öndeki düşmanları biçer.", "+%20 hasar ve +%20 can."],
            "beastmaster": ["Minyonlarını hedefe yönlendirir.", "Küçük Kurt ile başlar.", "Minyon hasarı +%30."],
            "sniper": ["Güvenli mesafeden tek hedef avlar.", "Basit Arbalet ile başlar.", "+1 sekme, +1 delme, +%20 kritik."],
            "engineer": ["Alanı otomatik taretlerle tutar.", "Taret Kiti ile başlar.", "+10 zırh; 5 sn'de bir taret."],
            "ninja": ["Hızlı ve kaçınmaya dayalı suikastçı.", "Paslı Katana ile başlar.", "Atılma sonrası ilk vuruş 2 kat."],
            "alchemist": ["Zehir ve alan hasarı uzmanı.", "Zehir Şişesi ile başlar.", "+%40 patlama alanı, +%30 DoT."],
            "sorcerer": ["Ateş, buz ve zehir arasında döner.", "Sihir Asası ile başlar.", "Her 4. saldırı kritik ve 2 kat alanlı."],
            "bloodwalker": ["Can çalarak riskli oynar.", "Kan Kılıcı ile başlar.", "%30 can altında hasar ve hız +%40."],
            "bomber": ["Devasa patlamalarla kalabalık siler.", "El Bombası Çantası ile başlar.", "En geniş alan; en yavaş atış."],
        }

        # Kartları Oluştur
        # Izgara sınıf sayısına göre kurulur: sütun sayısı satırı ikide tutacak
        # şekilde seçilir (9 sınıf -> 5+4), kart yüksekliği de GERÇEK satır
        # sayısından hesaplanır. Sabit "2 satır" varsayımı 9. sınıfla birlikte
        # alt satırı ekran dışına taşırıyordu.
        count = len(self.class_list)
        side_margin = max(32, self.width // 24)
        spacing_x, spacing_y = 18, 18
        num_cols = max(4, min(6, -(-count // 2)))
        num_rows = -(-count // num_cols)
        self.num_cols = num_cols
        card_w = min(260, (self.width - side_margin * 2 - spacing_x * (num_cols - 1)) // num_cols)
        footer_h = 75
        grid_top = 135
        avail_h = self.height - grid_top - footer_h - spacing_y * (num_rows - 1)
        # Alt sınır yok: satır sayısı arttığında kartlar kısalır ama asla
        # footer'ın altına taşmaz (bkz. tests/test_ui.py).
        card_h = max(120, min(400, avail_h // num_rows))

        self.cards = []
        for i, data in enumerate(self.class_list):
            row = i // num_cols
            col = i % num_cols
            # Her satır KENDİ kart sayısına göre ortalanır; eksik kartlı son
            # satır sola yapışık kalmaz.
            row_count = min(num_cols, count - row * num_cols)
            total_w = (card_w * row_count) + (spacing_x * (row_count - 1))
            start_x = (self.width - total_w) // 2 + card_w // 2
            x = start_x + col * (card_w + spacing_x)
            y = grid_top + row * (card_h + spacing_y)
            data["desc"] = detailed_desc.get(data["id"], data["desc"])
            self.cards.append(ClassCard(x, y, card_w, card_h, data, self.font_main, self.font_sub))

        # Boss Test Button (tema banner butonu; ham rect çizimi yok)
        import ui_theme
        self.boss_btn = Button(self.width - 160, self.height - 68, 260, 52,
                               "BOSS DENEME ODASI", self.font_desc,
                               ui_theme.COLORS["ember"])
        self.selected_idx = 0 # Warrior by default
        self.preview_idx = 0
        self._bg_cache = None

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
                    self.preview_idx = (self.preview_idx - self.num_cols) % len(self.cards)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.preview_idx = (self.preview_idx + self.num_cols) % len(self.cards)
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

        if self.boss_btn.update(events):
            # Use the hovered class if any, else use the last clicked one
            final_idx = self.preview_idx
            selected_class_id = self.class_list[final_idx]['id']
            self.manager.start_boss_test(selected_class_id)

    def _draw_background(self):
        """Koyu taş zemin + merkezden dışa kararan vinyet (gotik tema)."""
        import ui_theme
        self.screen.fill(ui_theme.DARK_OUT)
        if self._bg_cache is None or self._bg_cache.get_size() != (self.width, self.height):
            bg = pygame.Surface((self.width, self.height))
            top, bottom = (34, 29, 38), (16, 13, 18)
            for y in range(self.height):
                t = y / max(1, self.height - 1)
                pygame.draw.line(bg, tuple(int(top[i] + (bottom[i] - top[i]) * t)
                                           for i in range(3)), (0, y), (self.width, y))
            # Kenar kararması: ekranın ortasındaki kartlar öne çıksın
            vig = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            steps = 60
            for i in range(steps):
                a = int(90 * (i / steps) ** 2)
                inset = int(min(self.width, self.height) * 0.5 * (1 - i / steps))
                pygame.draw.rect(vig, (0, 0, 0, a),
                                 pygame.Rect(inset, inset,
                                             self.width - inset * 2,
                                             self.height - inset * 2), width=6)
            bg.blit(vig, (0, 0))
            self._bg_cache = bg
        self.screen.blit(self._bg_cache, (0, 0))

    def draw(self):
        import ui_theme
        self._draw_background()

        # --- Başlık: kurukafa arması + gotik serif başlık ---
        title = ui_theme.render_title("SINIFINI SEÇ", 62)
        tx = self.width // 2 - title.get_width() // 2
        self.screen.blit(title, (tx, 34))
        crest = get_skull_crest(56)
        if crest is not None:
            gap = 26
            cy = 34 + title.get_height() // 2 - crest.get_height() // 2
            self.screen.blit(crest, (tx - crest.get_width() - gap, cy))
            self.screen.blit(crest, (tx + title.get_width() + gap, cy))

        # Başlık altı metal ayraç
        line_y = 34 + title.get_height() + 8
        half = min(self.width // 2 - 40, 420)
        pygame.draw.line(self.screen, ui_theme.METAL_LO,
                         (self.width // 2 - half, line_y),
                         (self.width // 2 + half, line_y), 2)
        pygame.draw.line(self.screen, ui_theme.METAL,
                         (self.width // 2 - half // 2, line_y),
                         (self.width // 2 + half // 2, line_y), 2)

        # Seçili kart en son çizilir: kurukafa arması ve halesi komşuların
        # çerçevesinin altında kalmasın.
        for i, card in enumerate(self.cards):
            if i != self.preview_idx:
                card.draw(self.screen)
        self.cards[self.preview_idx].draw(self.screen, selected=True)

        # Alt bilgi, boss butonuyla çakışmayacak genişliğe sığdırılır
        info_max_w = self.boss_btn.rect.left - 60
        info = render_fit("Tıkla veya ENTER: Başla  •  Oklar/WASD: Seç  •  B: Boss testi  •  ESC: Geri",
                          20, (150, 144, 132), info_max_w)
        self.screen.blit(info, (30, self.height - 42))

        self.boss_btn.draw(self.screen)
