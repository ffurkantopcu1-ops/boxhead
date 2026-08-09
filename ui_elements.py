import pygame
import math
import time
import os

# --- Ortak Metin Yardımcıları ---
_FONT_CACHE = {}
UI_FONT_NAME = "Segoe UI, Arial"

def get_font(size, bold=False):
    """Boyuta göre önbelleğe alınmış font döndürür."""
    key = (size, bold)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = pygame.font.SysFont(UI_FONT_NAME, size, bold=bold)
    return _FONT_CACHE[key]

_glyph_cache = {}

def strip_unsupported(text):
    """UI fontunun çizemediği karakterleri (emoji vb.) atar.

    Yetenek/sinerji adları emoji önekleriyle geliyor, Segoe UI'da bu glifler
    yok ve ekranda boş kutu (□) olarak çiziliyordu. pygame per-glyph fallback
    yapmadığı için karakteri metinden düşürüyoruz. Sonuç metin bazında cache'li.
    """
    cached = _glyph_cache.get(text)
    if cached is not None:
        return cached
    try:
        metrics = get_font(18).metrics(text)
    except Exception:
        metrics = None
    if not metrics or len(metrics) != len(text):
        metrics = [1] * len(text)

    kept = []
    for ch, m in zip(text, metrics):
        if ch.isspace():
            kept.append(ch)
            continue
        # Metrik yokken kesin at. Metrik olsa da emoji/dingbat aralıklarını
        # atıyoruz: Segoe UI bu kod noktaları için glif bildirip .notdef
        # (boş kutu) çiziyor, yani metrik kontrolü tek başına yetmiyor.
        if m is None or _is_emoji(ch):
            continue
        kept.append(ch)
    out = ' '.join(''.join(kept).split()) or text
    _glyph_cache[text] = out
    return out


def _is_emoji(ch):
    o = ord(ch)
    return (0x2190 <= o <= 0x2BFF        # oklar, çeşitli semboller, dingbatlar
            or 0xFE00 <= o <= 0xFE0F     # varyasyon seçiciler
            or 0x1F000 <= o <= 0x1FAFF)  # emoji blokları


def render_fit(text, size, color, max_width, bold=False, min_size=11):
    """Metni max_width'e sığana kadar font boyutunu küçülterek keskin şekilde render eder.
    Yine sığmazsa sonuna '…' koyarak kırpar. Bulanık scale yerine bunu kullanın."""
    text = strip_unsupported(text)
    s = size
    while s >= min_size:
        font = get_font(s, bold)
        if font.size(text)[0] <= max_width:
            return font.render(text, True, color)
        s -= 1
    font = get_font(min_size, bold)
    clipped = text
    while clipped and font.size(clipped + "…")[0] > max_width:
        clipped = clipped[:-1]
    return font.render(clipped + "…", True, color)

def shrink_to_width(surface, max_width):
    """Render edilmiş bir yüzeyi, oranını koruyarak max_width'e sığdırır."""
    if surface.get_width() <= max_width or max_width <= 0:
        return surface
    ratio = max_width / surface.get_width()
    return pygame.transform.smoothscale(
        surface, (max_width, max(1, int(surface.get_height() * ratio)))
    )

def wrap_text(font, text, max_width):
    """Metni kelime bazında satırlara böler."""
    text = strip_unsupported(text)
    lines, current = [], []
    for word in text.split():
        candidate = " ".join(current + [word])
        if font.size(candidate)[0] <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines

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
        # Başarısızlık da cache'lenir: ikonu olmayan eşyalar için her karede
        # 3 kez os.path.exists disk I/O'su yapılıyordu.
        ImageLoader._cache[cache_key] = None
        return None

class Button:
    """Pixel-art fantazi banner buton (tema: ui_theme.py, bkz. DESIGN.md).

    Eski API korunur: (x, y, w, h, text, font, color, hover_color).
    hover_color artık kullanılmaz (hover durumunu tema üretir); `selected`
    ve `disabled` bayraklarıyla ek durumlar açılır. Kurukafa süsü yalnızca
    hover/seçili butonda görünür (dar menülerde üst üste binmesin diye).
    """

    def __init__(self, x, y, width, height, text, font, color=(52, 152, 219), hover_color=(41, 128, 185)):
        self.rect = pygame.Rect(x - width // 2, y, width, height)
        self.text = text
        self.font = font  # API uyumu için tutulur; tema kendi fontunu kullanır
        self.base_color = color
        self.is_hovered = False
        self.selected = False
        self.disabled = False

    def update(self, events):
        if self.disabled:
            self.is_hovered = False
            return False
        mouse_pos = pygame.mouse.get_pos()
        self.is_hovered = self.rect.collidepoint(mouse_pos)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.is_hovered:
                    return True # Tıklandı!
        return False

    def draw(self, screen):
        import ui_theme
        if self.disabled:
            state = "disabled"
        elif self.is_hovered and pygame.mouse.get_pressed()[0]:
            state = "pressed"
        elif self.is_hovered or self.selected:
            state = "hover"
        else:
            state = "normal"

        show_skull = state in ("hover", "pressed") or self.selected
        surf, overhang = ui_theme.render_banner_button(
            self.rect.width, self.rect.height, self.text,
            self.base_color, state=state, skull=show_skull)
        bx = self.rect.centerx - surf.get_width() // 2
        screen.blit(surf, (bx, self.rect.y - overhang))

def draw_set_badge(screen, center, radius=10):
    """Set eşyası rozeti (altın madalyon + S).

    Slot/kart/satır sınıflarının üçü de bunu ayrı ayrı çiziyor ve her karede
    yeni SysFont açıyordu.
    """
    import ui_theme
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(surf, ui_theme.RARITY_COLORS["Rare"], (radius, radius), radius)
    pygame.draw.circle(surf, ui_theme.DARK_OUT, (radius, radius), radius, 1)
    txt = get_font(int(radius * 1.6), bold=True).render("S", True, ui_theme.DARK_OUT)
    surf.blit(txt, txt.get_rect(center=(radius, radius)))
    screen.blit(surf, (center[0] - radius, center[1] - radius))


def draw_corrupted_pulse(screen, rect, pad=5):
    """Bozulmuş (corrupted) eşya için nabız gibi atan mor hale."""
    import ui_theme
    pulse = int((math.sin(time.time() * 8) + 1) * 55 + 60)
    col = ui_theme.readable(ui_theme.COLORS["arcane"], 190)
    aura = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
    pygame.draw.rect(aura, col + (pulse,), aura.get_rect(), width=3, border_radius=4)
    screen.blit(aura, (rect.x - pad, rect.y - pad))


_crest_cache = {}

def get_skull_crest(size):
    """assets/ui/gothic/skull_crest.png'i istenen yükseklikte döndürür."""
    if size in _crest_cache:
        return _crest_cache[size]
    surf = None
    path = "assets/ui/gothic/skull_crest.png"
    if os.path.exists(path):
        try:
            src = pygame.image.load(path).convert_alpha()
            ratio = size / src.get_height()
            surf = pygame.transform.smoothscale(
                src, (max(1, int(src.get_width() * ratio)), size))
        except pygame.error:
            surf = None
    _crest_cache[size] = surf
    return surf


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
        # _icon_src ham görsel: çizimde çerçevenin içerik alanına göre yeniden
        # ölçekleniyor, tekrar tekrar küçültülen kopyadan ölçek almasın.
        self._icon_src = None
        self.icon = None
        for ext in ['.png', '.jpeg', '.jpg']:
            try:
                icon_path = f"assets/classes/{self.data['id']}{ext}"
                self._icon_src = pygame.image.load(icon_path).convert_alpha()
                self.icon = self._icon_src
                break # Dosya bulunduysa döngüden çık
            except (pygame.error, FileNotFoundError):
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

    def draw(self, screen, selected=False):
        import ui_theme
        import ui_nineslice as n9

        col = self.data['color']
        accent = ui_theme.readable(col)          # koyu sınıf renkleri okunur hale
        active = self.is_hovered or selected

        # 1. Gövde: gotik taş çerçeve kartın İÇİNE çizilir (ızgarada taşmasın).
        #    Hover'da sınıf rengi tonu güçlenir ve arkada sıcak hale belirir.
        strength = 0.34 if active else 0.16
        tint = tuple(int(c * strength) for c in accent)
        glow = (accent, self.glow_alpha * 0.6) if self.glow_alpha > 5 else None
        # pad=16: 9-slice insets (40px) köşe süslerinin ölçüsü, kenar taşı çok
        # daha ince. 40px pay dar kartta metne yer bırakmıyordu.
        content = ui_theme.draw_inset_frame(
            screen, self.rect, "panel_frame_small.png",
            fill=(22, 19, 26), alpha=248 if active else 236,
            tint=tint, glow=glow, pad=16)

        # 2. Dikey yerleşim ALTTAN yukarı tahsis edilir: stat şeridi ve
        #    açıklama sabit yer alır, portre arta kalan alanı doldurur.
        #    (Önce portre büyütülünce metin karttan taşıyordu.)
        max_txt_w = content.width
        desc_lines = self.data['desc']
        # stat_h alt kenar payını da içerir: şerit tam kenara oturunca
        # çerçevenin köşe taşlarının üstüne biniyordu.
        stat_h, desc_h, name_h = 28, len(desc_lines) * 19, 26
        divider_h = 11
        icon_size = content.height - (stat_h + desc_h + name_h + divider_h + 10)
        icon_size = max(48, min(icon_size, content.width))

        icon_x = content.centerx - icon_size // 2
        icon_y = content.y
        if self.icon:
            if self.icon.get_width() != icon_size:
                self.icon = pygame.transform.smoothscale(self._icon_src, (icon_size, icon_size))
            screen.blit(self.icon, (icon_x, icon_y))
            frame_rect = pygame.Rect(icon_x, icon_y, icon_size, icon_size).inflate(12, 12)
            border = n9.get_border("portrait_frame.png", frame_rect.width,
                                   frame_rect.height, tint=tint)
            if border is not None:
                screen.blit(border, frame_rect.topleft)
        else:
            center = (content.centerx, icon_y + icon_size // 2)
            pygame.draw.circle(screen, accent, center, icon_size // 2, width=2)
            char = self.font_main.render(self.data['name'][0], True, accent)
            screen.blit(char, char.get_rect(center=center))

        # 3. Ad + aksan ayracı
        y = icon_y + icon_size + 8
        name_col = ui_theme.TEXT_COL if active else (196, 190, 178)
        name_surf = render_fit(self.data['name'].upper(), 22, name_col, max_txt_w, bold=True)
        screen.blit(name_surf, name_surf.get_rect(midtop=(content.centerx, y)))
        y += name_h

        pygame.draw.line(screen, accent, (content.x + 8, y), (content.right - 8, y), 1)
        y += divider_h

        # 4. Açıklama
        desc_col = (206, 199, 184) if active else (168, 162, 150)
        for line in desc_lines:
            d_surf = render_fit(line, 15, desc_col, max_txt_w)
            screen.blit(d_surf, d_surf.get_rect(midtop=(content.centerx, y)))
            y += 19

        # 5. Stat şeridi (alt kenara sabit)
        combined = "  •  ".join(f"{k} {v}" for k, v in self.data['stats'].items())
        # Köşe süslerinden kaçmak için şerit daraltılır: çerçeve köşeleri 40px,
        # içerik payı 16px -> her yanda 24px köşe payı bırakılır.
        s_surf = render_fit(combined, 14, accent, max_txt_w - 48, bold=True)
        screen.blit(s_surf, s_surf.get_rect(midbottom=(content.centerx, content.bottom - 6)))

        # 5. Seçili/hover kartın tepesine kurukafa arması
        if active:
            crest = get_skull_crest(48)
            if crest is not None:
                screen.blit(crest, (self.rect.centerx - crest.get_width() // 2,
                                    self.rect.y - crest.get_height() // 2))

class InventorySlot:
    def __init__(self, x, y, size, slot_type):
        self.rect = pygame.Rect(x, y, size, size)
        self.slot_type = slot_type 
        self.item = None
        self.is_hovered = False

    def update(self):
        self.is_hovered = self.rect.collidepoint(pygame.mouse.get_pos())

    def draw(self, screen, font):
        import ui_theme
        rarity = self.item.get('rarity') if self.item else None
        ui_theme.draw_item_slot(screen, self.rect, rarity, self.is_hovered)
        border_color = ui_theme.rarity_color(rarity) if rarity else ui_theme.METAL

        # --- İkon Çizimi ---
        icon_drawn = False
        if self.item and self.item.get('icon_id'):
            icon_img = ImageLoader.get_item_icon(self.item['icon_id'], (self.rect.width-10, self.rect.height-10))
            if icon_img:
                screen.blit(icon_img, (self.rect.x + 5, self.rect.y + 5))
                icon_drawn = True

        if not icon_drawn:
            label = self.slot_type[0:2].upper() if not self.item else self.item['name'][0:1]
            txt_color = ui_theme.METAL_LO if not self.item else border_color
            txt = font.render(label, True, txt_color)
            screen.blit(txt, txt.get_rect(center=self.rect.center))

        # --- Set İşaretçisi (S) ---
        if self.item and self.item.get('setTag'):
            draw_set_badge(screen, (self.rect.right - 8, self.rect.top + 8), 10)

        # --- Corrupted Aura ---
        if self.item and self.item.get('is_corrupted'):
            draw_corrupted_pulse(screen, self.rect)

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
        # Tema: gotik taş çerçeve; alınabilirlik yeşil tonla gösterilir
        import ui_theme
        active = can_afford and self.is_hovered
        if can_afford:
            base = ui_theme.COLORS["moss"]
            tint = tuple(int(c * (0.50 if active else 0.34)) for c in base)
        else:
            tint = tuple(int(c * 0.16) for c in ui_theme.METAL_LO)
        content = ui_theme.draw_inset_frame(
            screen, self.rect, "panel_frame_small.png",
            fill=(30, 38, 32) if can_afford else (28, 25, 32),
            alpha=246, tint=tint, pad=12)

        max_width = content.width
        name_col = ui_theme.TEXT_COL if can_afford else (162, 156, 146)
        # render_fit: shrink_to_width bulanıklaştırıyordu
        txt = render_fit(self.text, 19, name_col, max_width, bold=can_afford)
        text_y = content.y + 2 if description else self.rect.centery - txt.get_height() // 2
        screen.blit(txt, txt.get_rect(midtop=(content.centerx, text_y)))

        if description:
            # Ortak wrap_text (bu sınıfın kendi kopyası vardı)
            lines = wrap_text(self.detail_font, description, max_width)
            desc_col = (204, 210, 206) if can_afford else (150, 145, 138)
            y = text_y + txt.get_height() + 4
            for line in lines[:2]:
                detail = self.detail_font.render(line, True, desc_col)
                screen.blit(detail, detail.get_rect(midtop=(content.centerx, y)))
                y += self.detail_font.get_height() + 1

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
        import ui_theme
        is_active = (active_tab == self.tab_id)
        color = ui_theme.COLORS["gold"] if is_active else ui_theme.COLORS["steel"]
        state = "hover" if (is_active or self.is_hovered) else "normal"
        surf, overhang = ui_theme.render_banner_button(
            self.rect.width, self.rect.height, self.text, color, state=state, skull=False)
        screen.blit(surf, (self.rect.centerx - surf.get_width() // 2, self.rect.y - overhang))

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
        import ui_theme
        # Satır gövdesi: gotik çerçeve içeri çizilir (ızgarada taşmasın).
        # Set eşyasında yeşil, bozulmuşta mor tonla vurgulanır.
        tint = None
        if self.item and self.item.get("setTag"):
            tint = tuple(int(c * 0.34) for c in ui_theme.RARITY_COLORS["Set"])
        elif self.item and self.item.get("is_corrupted"):
            tint = tuple(int(c * 0.34) for c in ui_theme.readable(ui_theme.COLORS["arcane"]))
        elif self.is_hovered:
            tint = tuple(int(c * 0.22) for c in ui_theme.METAL_HI)
        ui_theme.draw_inset_frame(
            screen, self.rect, "panel_frame_small.png",
            fill=(30, 26, 36) if not self.is_hovered else (42, 37, 50),
            alpha=242, tint=tint, pad=10)

        slot_map = {
            "weapon": "Silah",
            "helmet": "Miğfer",
            "chest": "Zırh",
            "amulet": "Muska",
            "pet": "Pet",
            "artifact": "Eser",
            "orb": "Orb (Küre)"
        }
        
        # İkon yuvası dikeyde ortalanır (eskiden üste sabitti, satır 68px olunca
        # metinle aynı hizada durmuyordu).
        slot_size = min(44, self.rect.height - 14)
        slot_rect = pygame.Rect(self.rect.x + 10, self.rect.centery - slot_size // 2,
                                slot_size, slot_size)
        text_x = slot_rect.right + 12

        if self.item:
            i_rarity = self.item.get('rarity', 'Normal')
            label = f"[{i_rarity.upper()}] {self.item['name']}"
            color = ui_theme.rarity_color(i_rarity)
            ui_theme.draw_item_slot(screen, slot_rect, i_rarity, self.is_hovered)

            if self.item.get('icon_id'):
                icon_img = ImageLoader.get_item_icon(self.item['icon_id'],
                                                     (slot_size - 8, slot_size - 8))
                if icon_img:
                    screen.blit(icon_img, (slot_rect.x + 4, slot_rect.y + 4))

            if self.item.get('setTag'):
                draw_set_badge(screen, (slot_rect.right - 2, slot_rect.top + 2), 8)
            if self.item.get('is_corrupted'):
                draw_corrupted_pulse(screen, self.rect, pad=2)
        else:
            color = ui_theme.METAL_LO
            ui_theme.draw_item_slot(screen, slot_rect)
            label = f"Boş {slot_map.get(self.slot_type, self.slot_type)}"

        # İsmi keskin şekilde sığdır (bulanık scale yerine font küçültme).
        # Genişlik ikonun GERÇEK sağ kenarından hesaplanır.
        txt = render_fit(label, 18, color, self.rect.right - text_x - 14)
        txt_y = self.rect.y + (self.rect.height - txt.get_height()) // 2
        screen.blit(txt, (text_x, txt_y))

class BackpackItemCard:
    def __init__(self, x, y, w, h, idx):
        self.rect = pygame.Rect(x, y, w, h)
        # Kartın kendi içindeki göreceli indexi (0-11)
        self.idx = idx
        self.is_hovered = False
        self._layout()

    def reposition(self, x=None, y=None, w=None, h=None):
        """Kartı taşır/boyutlandırır ve İÇ rect'lerini yeniden hesaplar.

        Eskiden çizim tarafı yalnız rect.y ve buton y'lerini elle set ediyordu;
        yükseklik değişince ikon/buton hizası kartla birlikte gelmiyordu.
        """
        if x is not None: self.rect.x = x
        if y is not None: self.rect.y = y
        if w is not None: self.rect.width = w
        if h is not None: self.rect.height = h
        self._layout()

    def _layout(self):
        r = self.rect
        slot = max(34, min(46, r.height - 16))
        self.slot_rect = pygame.Rect(r.x + 10, r.centery - slot // 2, slot, slot)
        bx = self.slot_rect.right + 10
        avail = max(60, r.right - 10 - bx)
        btn_w = max(54, (avail - 10) // 3)   # 54: buton plakasının min genişliği
        btn_h = max(26, min(30, r.height // 2 - 6))
        by = r.bottom - btn_h - 6
        self.use_rect = pygame.Rect(bx, by, btn_w, btn_h)
        self.sell_rect = pygame.Rect(bx + btn_w + 5, by, btn_w, btn_h)
        self.craft_rect = pygame.Rect(bx + (btn_w + 5) * 2, by, btn_w, btn_h)
        self.name_pos = (bx, r.y + 7)
        self.name_max_w = avail

    def draw(self, screen, font_sub, item):
        import ui_theme
        if not item:
            # Boş slot: dolu kartla aynı çerçeve dilinde, sadece sönük
            ui_theme.draw_inset_frame(screen, self.rect, "panel_frame_small.png",
                                      fill=(24, 21, 28), alpha=170, pad=10)
            return

        color = ui_theme.rarity_color(item.get('rarity', 'Normal'))
        tint = tuple(int(c * 0.30) for c in color)
        if item.get("setTag"):
            tint = tuple(int(c * 0.34) for c in ui_theme.RARITY_COLORS["Set"])
        ui_theme.draw_inset_frame(screen, self.rect, "panel_frame_small.png",
                                  fill=(30, 26, 36), alpha=244, tint=tint, pad=10)

        # --- İkon / Slot (dikeyde ortalı, _layout'tan) ---
        slot_rect = self.slot_rect
        ui_theme.draw_item_slot(screen, slot_rect, item.get('rarity'))

        if item.get('icon_id'):
            ic = slot_rect.width - 8
            icon_img = ImageLoader.get_item_icon(item['icon_id'], (ic, ic))
            if icon_img:
                screen.blit(icon_img, (slot_rect.x + 4, slot_rect.y + 4))

        if item.get("is_corrupted"):
            draw_corrupted_pulse(screen, self.rect, pad=2)

        # Name (sığmazsa font küçültülür, oran bozulmaz)
        name_t = render_fit(item['name'], 18, color, self.name_max_w)
        screen.blit(name_t, self.name_pos)

        # Buttons (tema: mini banner)
        def mini_btn(rect, label, color, disabled=False):
            surf, overhang = ui_theme.render_banner_button(
                rect.width, rect.height, label, color,
                state="disabled" if disabled else "normal", skull=False)
            screen.blit(surf, (rect.centerx - surf.get_width() // 2, rect.y - overhang))

        # KULLAN (Sadece ekipmanlar için)
        if item.get('type') == 'essence':
            mini_btn(self.use_rect, "TÜKET", ui_theme.COLORS["arcane"])
        elif item.get('type') != 'orb':
            mini_btn(self.use_rect, "GİY", ui_theme.COLORS["moss"])
        else:
            mini_btn(self.use_rect, "ORB", ui_theme.COLORS["steel"], disabled=True)

        # SAT
        s_price = item.get('price', 100) // 2
        mini_btn(self.sell_rect, f"SAT ({s_price})", ui_theme.COLORS["ember"])

        # CRAFT
        is_equip = item.get('type') in ['weapon', 'helmet', 'chest', 'amulet', 'pet']
        mini_btn(self.craft_rect, "UP", ui_theme.COLORS["night"], disabled=not is_equip)

        # Set rozeti kartın sağ üstünde (isim şeridiyle çakışmasın)
        if item.get('setTag'):
            draw_set_badge(screen, (self.rect.right - 12, self.rect.y + 12), 8)

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
        import ui_theme

        color = ui_theme.rarity_color(self.item.get('rarity', 'Normal'))
        tint = tuple(int(c * (0.36 if self.is_hovered else 0.26)) for c in color)
        if self.item.get("setTag"):
            tint = tuple(int(c * 0.34) for c in ui_theme.RARITY_COLORS["Set"])
        ui_theme.draw_inset_frame(
            screen, self.rect, "panel_frame_small.png",
            fill=(30, 26, 36) if not self.is_hovered else (42, 37, 50),
            alpha=244, tint=tint, pad=10)

        # İkon Slotu (SOLA ALINDI)
        slot_rect = pygame.Rect(self.rect.x + 10, self.rect.y + 12, 55, 55)
        ui_theme.draw_item_slot(screen, slot_rect, self.item.get('rarity'), self.is_hovered)

        if self.item.get('icon_id'):
            icon_img = ImageLoader.get_item_icon(self.item['icon_id'], (46, 46))
            if icon_img:
                screen.blit(icon_img, (slot_rect.x + 5, slot_rect.y + 5))

        if self.item.get("setTag"):
            draw_set_badge(screen, (slot_rect.right - 2, slot_rect.top + 2), 8)

        # Name & Price: ikonun GERÇEK sağ kenarı ile AL butonu arasına sığdırılır
        text_x = slot_rect.right + 12
        name_max_w = max(40, self.buy_rect.left - text_x - 12)
        name_txt = render_fit(self.item['name'], 18, color, name_max_w)
        screen.blit(name_txt, (text_x, self.rect.y + 15))

        price_txt = render_fit(f"{self.item.get('price', 0)} GOLD", 17,
                               ui_theme.readable(ui_theme.COLORS["gold"]), name_max_w)
        screen.blit(price_txt, (text_x, self.rect.y + 40))

        if owned_count > 0:
            o_txt = render_fit(f"Sende: {owned_count}", 16, (186, 180, 168), name_max_w)
            screen.blit(o_txt, (text_x, self.rect.y + 60))

        # Buy Button (tema: mini banner)
        surf, overhang = ui_theme.render_banner_button(
            self.buy_rect.width, self.buy_rect.height, "AL", ui_theme.COLORS["moss"],
            state="hover" if self.buy_hovered else "normal", skull=False)
        screen.blit(surf, (self.buy_rect.centerx - surf.get_width() // 2, self.buy_rect.y - overhang))
