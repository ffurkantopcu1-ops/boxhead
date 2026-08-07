import pygame
import math
import time
import os

class ImageLoader:
    _cache = {}
    
    @staticmethod
    def get_item_icon(icon_id, size=(40, 40)):
        if not icon_id: return None
        
        cache_key = f"{icon_id}_{size[0]}x{size[1]}"
        if cache_key in ImageLoader._cache:
            return ImageLoader._cache[cache_key]
        
        # Farklı uzantıları dene
        for ext in ['.png', '.jpg', '.jpeg']:
            path = f"assets/items/{icon_id}{ext}"
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.smoothscale(img, size)
                    ImageLoader._cache[cache_key] = img
                    return img
                except:
                    continue
        return None

class Button:
    def __init__(self, x, y, width, height, text, font, color=(52, 152, 219), hover_color=(41, 128, 185)):
        self.rect = pygame.Rect(x - width // 2, y, width, height)
        self.text = text
        self.font = font
        self.base_color = color
        self.hover_color = hover_color
        self.current_color = color
        self.is_hovered = False
        
        # Premium Efektler için: Kenarlıkları yumuşatma ve parlatma
        self.glow_alpha = 0
        self.target_glow = 0

    def update(self, events):
        mouse_pos = pygame.mouse.get_pos()
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        if self.is_hovered:
            self.current_color = self.hover_color
            self.target_glow = 100 # Hover etkisindeki parlama
        else:
            self.current_color = self.base_color
            self.target_glow = 0

        # Glow yumuşatma (Lerp)
        self.glow_alpha += (self.target_glow - self.glow_alpha) * 0.1

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.is_hovered:
                    return True # Tıklandı!
        return False

    def draw(self, screen):
        # 1. Glow Efekti (Alt katman)
        if self.glow_alpha > 5:
            glow_surface = pygame.Surface((self.rect.width + 20, self.rect.height + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (self.current_color[0], self.current_color[1], self.current_color[2], int(self.glow_alpha)), (0, 0, self.rect.width + 20, self.rect.height + 20), border_radius=15)
            screen.blit(glow_surface, (self.rect.x - 10, self.rect.y - 10))

        # 2. Ana Gövde
        pygame.draw.rect(screen, self.current_color, self.rect, border_radius=10)
        
        # 3. Kenar Çizgisi (Vurgu)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, border_radius=10, width=2)

        # 4. Metin
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

class ClassCard:
    def __init__(self, x, y, width, height, class_data, font_main, font_sub):
        self.rect = pygame.Rect(x - width // 2, y, width, height)
        self.base_y = y
        self.current_y = y
        self.data = class_data # {id, name, desc, color, stats: {}}
        self.font_main = font_main
        self.font_sub = font_sub
        self.font_desc = pygame.font.SysFont("Segoe UI, Arial", 18) # Daha modern font
        
        self.is_hovered = False
        self.glow_alpha = 0
        
        # --- İkon Yükleme (Multi-extension support) ---
        self.icon = None
        # İkon boyutu: Kart genişliği - 80 (Overlap önleme için küçültüldü)
        icon_size = width - 80 
        for ext in ['.png', '.jpeg', '.jpg']:
            try:
                icon_path = f"assets/classes/{self.data['id']}{ext}"
                loaded = pygame.image.load(icon_path).convert_alpha()
                self.icon = pygame.transform.smoothscale(loaded, (icon_size, icon_size))
                break # Dosya bulunduysa döngüden çık
            except:
                continue # Diğer uzantıyı dene

    def update(self, events):
        mouse_pos = pygame.mouse.get_pos()
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        # Hover Efektleri: Parlama ve Yükselme (Lift)
        target_glow = 180 if self.is_hovered else 0
        target_y = self.base_y - 12 if self.is_hovered else self.base_y
        
        self.glow_alpha += (target_glow - self.glow_alpha) * 0.1
        self.current_y += (target_y - self.current_y) * 0.15
        self.rect.y = int(self.current_y)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.is_hovered:
                    return True
        return False

    def draw(self, screen):
        # 1. Glow & Shadow (Alt parıltı)
        if self.glow_alpha > 5:
            s = pygame.Surface((self.rect.width + 16, self.rect.height + 16), pygame.SRCALPHA)
            pygame.draw.rect(s, (*self.data['color'], int(self.glow_alpha * 0.4)), (0, 0, self.rect.width + 16, self.rect.height + 16), border_radius=18)
            screen.blit(s, (self.rect.x - 8, self.rect.y - 8))

        # 2. Ana Kart Gövdesi (Glassmorphism)
        bg_alpha = 230 if not self.is_hovered else 255
        main_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(main_surface, (25, 25, 35, bg_alpha), (0, 0, *self.rect.size), border_radius=14)
        pygame.draw.rect(main_surface, (255, 255, 255, 20), (2, 2, self.rect.width - 4, 80), border_radius=14) # Üst glossy
        screen.blit(main_surface, self.rect.topleft)

        border_color = self.data['color']
        if self.is_hovered:
            border_color = (min(255, border_color[0] + 50), min(255, border_color[1] + 50), min(255, border_color[2] + 50))
        pygame.draw.rect(screen, border_color, self.rect, border_radius=14, width=3)

        # 3. İKON Bölümü (Ortalı)
        icon_size = self.rect.width - 80
        icon_x = self.rect.x + 40
        icon_y_start = self.rect.y + 15
        if self.icon:
            screen.blit(self.icon, (icon_x, icon_y_start))
        else:
            center = (self.rect.centerx, icon_y_start + icon_size // 2)
            pygame.draw.circle(screen, (*self.data['color'], 40), center, 48)
            pygame.draw.circle(screen, self.data['color'], center, 50, width=2)
            char = self.font_main.render(self.data['name'][0], True, self.data['color'])
            screen.blit(char, char.get_rect(center=center))

        # 4. Metin Bölümü
        text_y_start = icon_y_start + icon_size + 15
        
        name_surf = self.font_sub.render(self.data['name'].upper(), True, (255, 255, 255))
        if name_surf.get_width() > self.rect.width - 20:
            scale = (self.rect.width - 20) / name_surf.get_width()
            name_surf = pygame.transform.smoothscale(
                name_surf,
                (int(name_surf.get_width() * scale), int(name_surf.get_height() * scale)),
            )
        name_rect = name_surf.get_rect(center=(self.rect.centerx, text_y_start))
        screen.blit(name_surf, name_rect)
        
        pygame.draw.line(screen, (*self.data['color'], 80), (self.rect.x + 40, text_y_start + 18), (self.rect.x + self.rect.width - 40, text_y_start + 18), 1)

        y_off = text_y_start + 35
        max_txt_w = self.rect.width - 20
        for line in self.data['desc']:
            d_surf = self.font_desc.render(line, True, (200, 200, 210))
            if d_surf.get_width() > max_txt_w:
                scale = max_txt_w / d_surf.get_width()
                d_surf = pygame.transform.smoothscale(d_surf, (int(d_surf.get_width() * scale), int(d_surf.get_height() * scale)))
            d_rect = d_surf.get_rect(center=(self.rect.centerx, y_off))
            screen.blit(d_surf, d_rect)
            y_off += 21

        y_off = self.rect.bottom - 25
        stat_items = list(self.data['stats'].items())
        combined_stats = " | ".join([f"{k}: {v}" for k, v in stat_items])
        s_surf = self.font_desc.render(combined_stats, True, self.data['color'])
        if s_surf.get_width() > max_txt_w:
            scale = max_txt_w / s_surf.get_width()
            s_surf = pygame.transform.smoothscale(s_surf, (int(s_surf.get_width() * scale), int(s_surf.get_height() * scale)))
        s_rect = s_surf.get_rect(center=(self.rect.centerx, y_off))
        screen.blit(s_surf, s_rect)

class InventorySlot:
    def __init__(self, x, y, size, slot_type):
        self.rect = pygame.Rect(x, y, size, size)
        self.slot_type = slot_type 
        self.item = None
        self.is_hovered = False

    def update(self):
        self.is_hovered = self.rect.collidepoint(pygame.mouse.get_pos())

    def draw(self, screen, font):
        color = (45, 45, 60) if not self.is_hovered else (60, 60, 80)
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        
        border_color = (100, 100, 120)
        if self.item:
            rarity_colors = {"Normal": (255,255,255), "Magic": (52,152,219), "Rare": (241,196,15), "Unique": (231,76,60)}
            border_color = rarity_colors.get(self.item['rarity'], (255,255,255))
            
        pygame.draw.rect(screen, border_color, self.rect, width=2, border_radius=8)
        
        # --- İkon Çizimi ---
        icon_drawn = False
        if self.item and self.item.get('icon_id'):
            icon_img = ImageLoader.get_item_icon(self.item['icon_id'], (self.rect.width-10, self.rect.height-10))
            if icon_img:
                screen.blit(icon_img, (self.rect.x + 5, self.rect.y + 5))
                icon_drawn = True
        
        if not icon_drawn:
            label = self.slot_type[0:2].upper() if not self.item else self.item['name'][0:1]
            txt_color = (150, 150, 150) if not self.item else border_color
            txt = font.render(label, True, txt_color)
            screen.blit(txt, txt.get_rect(center=self.rect.center))

        # --- Set İşaretçisi (S) ---
        if self.item and self.item.get('setTag'):
            s_font = pygame.font.SysFont("Arial", 16, bold=True)
            s_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(s_surf, (241, 196, 15), (10, 10), 10) # Altın Yuvarlak
            st_txt = s_font.render("S", True, (30, 30, 40))
            s_surf.blit(st_txt, st_txt.get_rect(center=(10, 10)))
            screen.blit(s_surf, (self.rect.right - 18, self.rect.top - 2))
            
        # --- Corrupted Aura ---
        if self.item and self.item.get('is_corrupted'):
            pulse = (math.sin(time.time() * 8) + 1) * 60 + 50
            aura = pygame.Surface((self.rect.width + 10, self.rect.height + 10), pygame.SRCALPHA)
            pygame.draw.rect(aura, (155, 89, 182, int(pulse)), (0, 0, self.rect.width + 10, self.rect.height + 10), border_radius=12, width=3)
            screen.blit(aura, (self.rect.x - 5, self.rect.y - 5))

class SkillButton:
    def __init__(self, x, y, w, h, text, skill_id):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.skill_id = skill_id
        self.is_hovered = False
        self.detail_font = pygame.font.SysFont("Segoe UI, Arial", 14)

    def update(self):
        self.is_hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        return self.is_hovered and pygame.mouse.get_pressed()[0]

    def draw(self, screen, font, can_afford, description=None):
        bg = (39, 174, 96) if self.is_hovered and can_afford else (46, 204, 113)
        if not can_afford: bg = (127, 140, 141)
        
        pygame.draw.rect(screen, bg, self.rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, width=2, border_radius=10)
        
        txt = font.render(self.text, True, (255, 255, 255))
        max_width = self.rect.width - 16
        if txt.get_width() > max_width:
            ratio = max_width / txt.get_width()
            txt = pygame.transform.smoothscale(txt, (max_width, int(txt.get_height() * ratio)))
        text_y = self.rect.centery - 10 if description else self.rect.centery
        screen.blit(txt, txt.get_rect(center=(self.rect.centerx, text_y)))

        if description:
            words = description.split()
            lines = []
            current = []
            for word in words:
                candidate = ' '.join(current + [word])
                if self.detail_font.size(candidate)[0] <= max_width:
                    current.append(word)
                else:
                    if current:
                        lines.append(' '.join(current))
                    current = [word]
            if current:
                lines.append(' '.join(current))
            for i, line in enumerate(lines[:2]):
                detail = self.detail_font.render(line, True, (225, 230, 235))
                y = self.rect.centery + 10 + i * 15
                screen.blit(detail, detail.get_rect(center=(self.rect.centerx, y)))

class TabButton:
    def __init__(self, x, y, w, h, text, tab_id):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.tab_id = tab_id
        self.is_hovered = False

    def update(self):
        self.is_hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        return self.is_hovered and pygame.mouse.get_pressed()[0]

    def draw(self, screen, font, active_tab):
        is_active = (active_tab == self.tab_id)
        bg = (52, 73, 94) if is_active else (44, 62, 80)
        border = (241, 196, 15) if is_active else (100, 100, 100)
        
        pygame.draw.rect(screen, bg, self.rect, border_radius=5)
        pygame.draw.rect(screen, border, self.rect, width=2, border_radius=5)
        
        color = (255, 255, 255) if is_active else (180, 180, 180)
        txt = font.render(self.text, True, color)
        screen.blit(txt, txt.get_rect(center=self.rect.center))

class EquippedRow:
    def __init__(self, x, y, w, h, slot_type):
        self.rect = pygame.Rect(x, y, w, h)
        self.slot_type = slot_type
        self.item = None
        self.is_hovered = False

    def update(self, item):
        self.item = item
        self.is_hovered = self.rect.collidepoint(pygame.mouse.get_pos())

    def draw(self, screen, font_sub):
        bg = (40, 40, 55) if not self.is_hovered else (50, 50, 70)
        
        border_width = 1
        glow_color = (80, 80, 100)
        if self.item and self.item.get("setTag"):
            bg = (20, 45, 20) if not self.is_hovered else (30, 60, 30)
            border_width = 2
            glow_color = (46, 204, 113)
            
        pygame.draw.rect(screen, bg, self.rect, border_radius=8)
        pygame.draw.rect(screen, glow_color, self.rect, width=border_width, border_radius=8)
        
        slot_map = {
            "weapon": "Silah",
            "helmet": "Miğfer",
            "chest": "Zırh",
            "amulet": "Muska",
            "pet": "Pet",
            "artifact": "Eser",
            "orb": "Orb (Küre)"
        }
        
        label = self.slot_type.upper()
        if self.item:
            i_rarity = self.item.get('rarity', 'Normal')
            label = f"[{i_rarity.upper()}] {self.item['name']}"
            rarity_colors = {"Normal": (255,255,255), "Magic": (52,152,219), "Rare": (241,196,15), "Unique": (231,76,60)}
            color = rarity_colors.get(i_rarity, (255,255,255))
            
            # Slot box
            slot_rect = pygame.Rect(self.rect.x + 5, self.rect.y + 5, 40, 40)
            pygame.draw.rect(screen, (30, 30, 40), slot_rect, border_radius=4)
            
            # İkon
            if self.item.get('icon_id'):
                icon_img = ImageLoader.get_item_icon(self.item['icon_id'], (36, 36))
                if icon_img:
                    screen.blit(icon_img, (self.rect.x + 7, self.rect.y + 7))
            
            # --- Set/Corrupted Labels ---
            if self.item.get('setTag'):
                s_font = pygame.font.SysFont("Arial", 14, bold=True)
                pygame.draw.circle(screen, (241, 196, 15), (self.rect.x + 50, self.rect.y + 10), 8)
                st = s_font.render("S", True, (0, 0, 0))
                screen.blit(st, st.get_rect(center=(self.rect.x + 50, self.rect.y + 10)))
            
            if self.item.get('is_corrupted'):
                pulse = (math.sin(time.time() * 10) + 1) * 0.5
                c_color = (155 + pulse*40, 89, 182)
                pygame.draw.rect(screen, c_color, self.rect, width=2, border_radius=8)
        else:
            color = (100, 100, 100)
            pygame.draw.rect(screen, (30, 30, 40), (self.rect.x + 5, self.rect.y + 5, 40, 40), border_radius=4)
            label = f"Boş {slot_map.get(self.slot_type, self.slot_type)}"

        txt = font_sub.render(label, True, color)
        # İsmi sığdır (Scale)
        max_w = self.rect.width - 70
        if txt.get_width() > max_w:
            scale = max_w / txt.get_width()
            txt = pygame.transform.smoothscale(txt, (int(txt.get_width() * scale), int(txt.get_height() * scale)))
        screen.blit(txt, (self.rect.x + 60, self.rect.y + 15))

class BackpackItemCard:
    def __init__(self, x, y, w, h, idx):
        self.rect = pygame.Rect(x, y, w, h)
        # Kartın kendi içindeki göreceli indexi (0-11)
        self.idx = idx
        
        # Butonlar (İkonun sağına yerleştirildi)
        icon_w = 60
        btn_w = (w - icon_w - 15) // 3
        btn_y = y + 35
        self.use_rect = pygame.Rect(x + icon_w, btn_y, btn_w, 30)
        self.sell_rect = pygame.Rect(x + icon_w + btn_w + 5, btn_y, btn_w, 30)
        self.craft_rect = pygame.Rect(x + icon_w + (btn_w + 5) * 2, btn_y, btn_w, 30)
        self.is_hovered = False

    def draw(self, screen, font_sub, item):
        if not item: 
            # Boş Slot Çizimi (Görsel tutarlılık için)
            pygame.draw.rect(screen, (30, 30, 40), self.rect, border_radius=8, width=1)
            return
        
        rarity_colors = {"Normal": (255,255,255), "Magic": (52,152,219), "Rare": (241,196,15), "Unique": (231,76,60)}
        color = rarity_colors.get(item['rarity'], (255, 255, 255))
        
        # Card BG
        bg = (35, 35, 50)
        if item.get("setTag"): bg = (20, 40, 20)
            
        pygame.draw.rect(screen, bg, self.rect, border_radius=8)
        pygame.draw.rect(screen, color, self.rect, width=1, border_radius=8)
        
        # --- İkon / Slot ---
        # Sol orta kısma yerleştirildi
        slot_rect = pygame.Rect(self.rect.x + 8, self.rect.y + 26, 48, 48)
        pygame.draw.rect(screen, (25, 25, 35), slot_rect, border_radius=6)
        pygame.draw.rect(screen, color, slot_rect, width=1, border_radius=6)
        
        if item.get('icon_id'):
            icon_img = ImageLoader.get_item_icon(item['icon_id'], (44, 44))
            if icon_img:
                screen.blit(icon_img, (slot_rect.x + 2, slot_rect.y + 2))
        
        # Name (Kırpılmış veya punto küçültülmüş)
        name_t = font_sub.render(item['name'], True, color)
        if name_t.get_width() > self.rect.width - 15:
            name_t = pygame.transform.scale(name_t, (self.rect.width - 15, int(name_t.get_height() * 0.9)))
        screen.blit(name_t, (self.rect.x + 8, self.rect.y + 6))
        
        # Buttons
        # KULLAN (Sadece ekipmanlar için)
        if item.get('type') == 'essence':
            pygame.draw.rect(screen, (155, 89, 182), self.use_rect, border_radius=4)
            u_txt = font_sub.render("TÜKET", True, (255, 255, 255))
            u_scale = pygame.transform.scale(u_txt, (int(u_txt.get_width()*0.6), int(u_txt.get_height()*0.6)))
            screen.blit(u_scale, u_scale.get_rect(center=self.use_rect.center))
        elif item.get('type') != 'orb':
            pygame.draw.rect(screen, (46, 204, 113), self.use_rect, border_radius=4)
            u_txt = font_sub.render("GİY", True, (255, 255, 255))
            u_scale = pygame.transform.scale(u_txt, (int(u_txt.get_width()*0.6), int(u_txt.get_height()*0.6)))
            screen.blit(u_scale, u_scale.get_rect(center=self.use_rect.center))
        else:
            pygame.draw.rect(screen, (50, 50, 70), self.use_rect, border_radius=4)
            u_txt = font_sub.render("ORB", True, (150, 150, 150))
            u_scale = pygame.transform.scale(u_txt, (int(u_txt.get_width()*0.6), int(u_txt.get_height()*0.6)))
            screen.blit(u_scale, u_scale.get_rect(center=self.use_rect.center))
        
        # SAT
        pygame.draw.rect(screen, (231, 76, 60), self.sell_rect, border_radius=4)
        s_price = item.get('price', 100) // 2
        s_txt = font_sub.render(f"SAT({s_price})", True, (255, 255, 255))
        s_scale = pygame.transform.scale(s_txt, (int(s_txt.get_width()*0.6), int(s_txt.get_height()*0.6)))
        screen.blit(s_scale, s_scale.get_rect(center=self.sell_rect.center))
 
        # CRAFT
        is_equip = item.get('type') in ['weapon', 'helmet', 'chest', 'amulet', 'pet']
        c_color = (52, 152, 219) if is_equip else (100, 100, 100)
        pygame.draw.rect(screen, c_color, self.craft_rect, border_radius=4)
        c_txt = font_sub.render("UP", True, (255, 255, 255))
        c_scale = pygame.transform.scale(c_txt, (int(c_txt.get_width()*0.6), int(c_txt.get_height()*0.6)))
        screen.blit(c_scale, c_scale.get_rect(center=self.craft_rect.center))

        # --- Set/Corrupted Overlay (S) ---
        if item.get('setTag'):
            pygame.draw.circle(screen, (241, 196, 15), (self.rect.right - 10, self.rect.y + 10), 8)
            s_font = pygame.font.SysFont("Arial", 12, bold=True)
            st = s_font.render("S", True, (0,0,0))
            screen.blit(st, st.get_rect(center=(self.rect.right - 10, self.rect.y + 10)))
        
        if item.get('is_corrupted'):
            s = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(s, (155, 89, 182, 40), (0, 0, *self.rect.size), border_radius=8)
            screen.blit(s, self.rect.topleft)

class MarketCard:
    def __init__(self, x, y, width, height, idx):
        self.rect = pygame.Rect(x, y, width, height)
        self.idx = idx
        self.item = None
        # Buton sağ alta, ikon sola
        self.buy_rect = pygame.Rect(x + width - 100, y + 25, 80, 40)
        self.is_hovered = False
        self.buy_hovered = False

    def update(self, item):
        self.item = item
        m_pos = pygame.mouse.get_pos()
        self.is_hovered = self.rect.collidepoint(m_pos)
        self.buy_hovered = self.buy_rect.collidepoint(m_pos)
        
        if self.buy_hovered and pygame.mouse.get_pressed()[0]:
            return True # Buy clicked
        return False

    def draw(self, screen, font_sub, font_desc, owned_count=0):
        if not self.item: return
        
        rarity_colors = {"Normal": (255,255,255), "Magic": (52,152,219), "Rare": (241,196,15), "Unique": (231,76,60)}
        color = rarity_colors.get(self.item['rarity'], (255,255,255))
        
        # Card BG
        bg = (35, 35, 50) if not self.is_hovered else (45, 45, 65)
        if self.item.get("setTag"):
            bg = (20, 40, 20) if not self.is_hovered else (30, 50, 30)
            
        pygame.draw.rect(screen, bg, self.rect, border_radius=10)
        pygame.draw.rect(screen, color, self.rect, width=1, border_radius=10)
        
        if self.item.get("setTag"):
            s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, (46, 204, 113, 30), (0, 0, self.rect.width, self.rect.height), border_radius=10)
            screen.blit(s, self.rect.topleft)
        
        # İkon Slotu (SOLA ALINDI)
        slot_rect = pygame.Rect(self.rect.x + 10, self.rect.y + 12, 55, 55)
        pygame.draw.rect(screen, (25, 25, 40), slot_rect, border_radius=8)
        pygame.draw.rect(screen, color, slot_rect, width=1, border_radius=8)
        
        if self.item.get('icon_id'):
            icon_img = ImageLoader.get_item_icon(self.item['icon_id'], (50, 50))
            if icon_img:
                screen.blit(icon_img, (slot_rect.x + 2, slot_rect.y + 2))

        # Name & Price (SAĞA KAYDIRILDI)
        name_txt = font_desc.render(self.item['name'], True, color)
        # İsmi sığdır (Scale)
        if name_txt.get_width() > self.rect.width - 185:
            name_txt = pygame.transform.scale(name_txt, (self.rect.width - 185, int(name_txt.get_height() * 0.9)))
        screen.blit(name_txt, (self.rect.x + 75, self.rect.y + 15))
        
        # Price
        price_txt = font_desc.render(f"{self.item.get('price', 0)} GOLD", True, (241, 196, 15))
        screen.blit(price_txt, (self.rect.x + 75, self.rect.y + 40))
        
        # Owned Count
        if owned_count > 0:
            o_txt = font_desc.render(f"Sende: {owned_count}", True, (200, 200, 200))
            screen.blit(o_txt, (self.rect.x + 75, self.rect.y + 58))

        # Buy Button
        btn_color = (46, 204, 113) if not self.buy_hovered else (39, 174, 96)
        pygame.draw.rect(screen, btn_color, self.buy_rect, border_radius=5)
        buy_txt = font_desc.render("AL", True, (255, 255, 255))
        screen.blit(buy_txt, buy_txt.get_rect(center=self.buy_rect.center))
