# -*- coding: utf-8 -*-
"""Koyu-fantastik pixel-art UI teması (bkz. DESIGN.md).

Tek kaynak: banner butonlar, metal çerçeveli paneller ve kurukafa süsü
burada üretilir. tools/generate_ui_assets.py bu modülü kullanarak
assets/ui/ altına şablon PNG'lerini yazar; oyun çalışırken de aynı
fonksiyonlar boyuta göre üretir ve cache'ler.
"""
import os
import pygame

# --- PALET ---
DARK_OUT = (24, 20, 22)      # dış kontur
METAL = (122, 126, 134)      # metal çerçeve
METAL_HI = (176, 180, 188)   # metal parlama
METAL_LO = (64, 66, 72)      # metal gölge / devre dışı
BONE = (198, 189, 168)       # kurukafa kemik
BONE_LO = (140, 132, 112)
HORN = (108, 96, 78)         # boynuz
HORN_HI = (156, 142, 116)
EYE_RED = (255, 60, 40)
EYE_GLOW = (255, 170, 80)
TEXT_COL = (240, 234, 220)
PANEL_BG = (26, 24, 34)      # panel zemini
GLOW_WARM = (255, 120, 50)   # hover halesi

# Koyu fantastik buton paleti (onaylanan B paleti)
COLORS = {
    "blood":    (146, 24, 16),    # ana aksiyon (kan kırmızısı)
    "night":    (30, 78, 110),    # ikincil (gece mavisi)
    "arcane":   (88, 40, 120),    # büyü/kristal (koyu mor)
    "steel":    (95, 98, 104),    # nötr (çelik grisi)
    "gold":     (150, 100, 22),   # vurgu (eski altın)
    "ember":    (70, 18, 14),     # tehlike/çıkış (kararmış bordo)
    "moss":     (44, 96, 58),     # onay/başarı (koyu yosun yeşili)
}

_FONT_NAME = "Georgia, Times New Roman, serif"

# --- KURUKAFA (25x14 piksel haritası) ---
SKULL = [
    "....hHH...........HHh....",
    "...hHHh..........hHHh....",
    "..hHh...sssssssss...hHh..",
    "..hH..sssssssssssss..Hh..",
    "..hh.sssssssssssssss.hh..",
    "...h.sssssssssssssss.h...",
    ".....sssssssssssssss.....",
    ".....ss.ddd.s.ddd.ss.....",
    ".....ss.dRd.s.dRd.ss.....",
    "......sssssssssssss......",
    ".......ssss.d.ssss.......",
    "........sssssssss........",
    "........s.s.s.s.s........",
    "........d.d.d.d.d........",
]
SKULL_W, SKULL_H = len(SKULL[0]), len(SKULL)

_skull_cache = {}
_button_cache = {}
_panel_cache = {}


def render_skull(scale=1, glow=False):
    """Kurukafayı native çizip nearest-neighbor ölçekler."""
    key = (scale, glow)
    if key in _skull_cache:
        return _skull_cache[key]
    surf = pygame.Surface((SKULL_W, SKULL_H), pygame.SRCALPHA)
    for ry, row in enumerate(SKULL):
        for rx, ch in enumerate(row):
            if ch == 's':
                surf.set_at((rx, ry), BONE)
            elif ch == 'd':
                surf.set_at((rx, ry), BONE_LO)
            elif ch == 'h':
                surf.set_at((rx, ry), HORN)
            elif ch == 'H':
                surf.set_at((rx, ry), HORN_HI if not glow else METAL_HI)
            elif ch == 'R':
                surf.set_at((rx, ry), EYE_RED if not glow else EYE_GLOW)
    if scale != 1:
        surf = pygame.transform.scale(surf, (SKULL_W * scale, SKULL_H * scale))
    _skull_cache[key] = surf
    return surf


def _banner_points(x0, y0, w, h, inset):
    cy = y0 + h // 2
    return [
        (x0, cy), (x0 + inset, y0), (x0 + w - inset, y0),
        (x0 + w, cy), (x0 + w - inset, y0 + h), (x0 + inset, y0 + h),
    ]


def render_banner_button(width, height, text, color, state="normal", skull=False):
    """Sivri uçlu banner buton döndürür: (surface, overhang_px).

    surface, buton rect'inden overhang_px kadar yukarı taşar (kurukafa);
    blit ederken (rect.x, rect.y - overhang_px) kullanın.
    state: normal | hover | pressed | disabled
    """
    key = (width, height, text, color, state, skull)
    if key in _button_cache:
        return _button_cache[key]

    hover = state == "hover"
    pressed = state == "pressed"
    disabled = state == "disabled"

    s = max(2, height // 16)
    nw = max(24, width // s)
    nh = max(12, height // s)
    over_n = (SKULL_H - 5) if skull else 0  # kurukafanın banner üstüne taşan kısmı

    surf = pygame.Surface((nw, nh + over_n), pygame.SRCALPHA)
    bx, by = 1, over_n + (1 if pressed else 0)
    bw, bh = nw - 2, nh - 2
    inset = max(4, min(7, bh // 2))

    # Hover halesi
    if hover and not disabled:
        glow_pts = _banner_points(bx - 1, by - 1, bw + 2, bh + 2, inset)
        glow_s = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(glow_s, GLOW_WARM + (70,), glow_pts)
        surf.blit(glow_s, (0, 0))

    pts = _banner_points(bx, by, bw, bh, inset)

    # Dolgu + dikey gradyan
    base = color
    if disabled:
        g = sum(base) // 3
        base = (g, g, g)
    top_c = tuple(min(255, int(c * (1.35 if hover else 1.15))) for c in base)
    bot_c = tuple(int(c * 0.55) for c in base)
    pygame.draw.polygon(surf, base, pts)
    for yy in range(by + 1, by + bh):
        t = (yy - by) / bh
        row_c = tuple(int(top_c[i] + (bot_c[i] - top_c[i]) * t) for i in range(3))
        for xx in range(bx, bx + bw + 1):
            if surf.get_at((xx, yy))[3] > 0:
                surf.set_at((xx, yy), row_c)

    # Çerçeve: metal + dış kontur + iç gölge
    metal = METAL_HI if hover else (METAL_LO if disabled else METAL)
    pygame.draw.polygon(surf, metal, pts, 2)
    pygame.draw.polygon(surf, DARK_OUT, _banner_points(bx - 1, by - 1, bw + 2, bh + 2, inset), 1)
    pygame.draw.polygon(surf, tuple(int(c * 0.5) for c in base),
                        _banner_points(bx + 2, by + 2, bw - 4, bh - 4, max(2, inset - 2)), 1)

    cy = by + bh // 2
    m_hi = METAL_LO if disabled else METAL_HI

    # Uç elmasları (çift sivri uç)
    for tx, dr in [(bx, -1), (bx + bw, 1)]:
        tip = [(tx + dr * 3, cy), (tx + dr, cy - 3), (tx - dr, cy), (tx + dr, cy + 3)]
        pygame.draw.polygon(surf, metal, tip)
        pygame.draw.polygon(surf, DARK_OUT, tip, 1)
        surf.set_at((tx + dr, cy - 1), m_hi)

    # Köşe plakaları
    if bh >= 12:
        corners = [
            ((bx + inset, by), (1, 1)), ((bx + bw - inset, by), (-1, 1)),
            ((bx + inset, by + bh), (1, -1)), ((bx + bw - inset, by + bh), (-1, -1)),
        ]
        for (cx_, cy_), (dx, dy) in corners:
            plate = [(cx_ - dx * 2, cy_), (cx_ + dx * 3, cy_), (cx_ + dx * 3, cy_ + dy * 2)]
            pygame.draw.polygon(surf, metal, plate)
            pygame.draw.polygon(surf, DARK_OUT, plate, 1)
            surf.set_at((cx_ + dx, cy_), m_hi)

        # Alt madalyon
        mx, my = nw // 2, by + bh
        pend = [(mx - 2, my), (mx, my - 1), (mx + 2, my), (mx, my + 3)]
        pygame.draw.polygon(surf, metal, pend)
        pygame.draw.polygon(surf, DARK_OUT, pend, 1)

    # Kurukafa (banner üst ortasına oturur)
    if skull:
        sk = render_skull(1, glow=hover)
        surf.blit(sk, (nw // 2 - SKULL_W // 2, (1 if pressed else 0)))

    # Banner yüzeyini önce ölçeklendir
    out = pygame.transform.scale(surf, (nw * s, (nh + over_n) * s))

    # Metni direkt olarak ölçeklenmiş yüzeye (out) kendi net font boyutuyla çiz
    f_size_scaled = max(7 * s, int(bh * 0.62 * s))
    font = pygame.font.SysFont(_FONT_NAME, f_size_scaled, bold=True)
    t_col = (150, 148, 142) if disabled else TEXT_COL
    txt = font.render(text, True, t_col)
    
    max_tw_scaled = (bw - 2 * inset - 6) * s
    if txt.get_width() > max_tw_scaled and max_tw_scaled > 0:
        ratio = max_tw_scaled / txt.get_width()
        txt = pygame.transform.smoothscale(txt, (max_tw_scaled, max(1, int(txt.get_height() * ratio))))
        
    tx_scaled = (nw * s) // 2 - txt.get_width() // 2
    ty_scaled = (by * s) + (bh * s) // 2 - txt.get_height() // 2 + s
    
    # Gölge
    sh = font.render(text, True, (20, 10, 8))
    if sh.get_size() != txt.get_size():
        sh = pygame.transform.smoothscale(sh, txt.get_size())
    out.blit(sh, (tx_scaled + max(1, s // 2), ty_scaled + max(1, s // 2)))
    out.blit(txt, (tx_scaled, ty_scaled))
    result = (out, over_n * s)
    _button_cache[key] = result
    return result


def draw_panel(screen, rect, fill=PANEL_BG, alpha=235, skull=False):
    """Metal çerçeveli koyu panel çizer (menü panelleri, kartlar, tooltipler)."""
    key = (rect.width, rect.height, fill, alpha, skull)
    surf = _panel_cache.get(key)
    if surf is None:
        surf = pygame.Surface((rect.width, rect.height + (18 if skull else 0)), pygame.SRCALPHA)
        oy = 18 if skull else 0
        body = pygame.Rect(0, oy, rect.width, rect.height)
        pygame.draw.rect(surf, fill + (alpha,), body, border_radius=4)
        pygame.draw.rect(surf, METAL, body, width=3, border_radius=4)
        pygame.draw.rect(surf, DARK_OUT, body.inflate(2, 2), width=1, border_radius=5)
        pygame.draw.rect(surf, METAL_LO, body.inflate(-6, -6), width=1, border_radius=3)
        # Köşe plakaları
        cs = 9
        for cx_, cy_, dx, dy in [
            (body.left, body.top, 1, 1), (body.right, body.top, -1, 1),
            (body.left, body.bottom, 1, -1), (body.right, body.bottom, -1, -1),
        ]:
            plate = [(cx_, cy_), (cx_ + dx * cs, cy_), (cx_, cy_ + dy * cs)]
            pygame.draw.polygon(surf, METAL, plate)
            pygame.draw.polygon(surf, DARK_OUT, plate, 1)
        # Kenar ortası perçinleri
        for px_, py_ in [(body.centerx, body.top + 1), (body.centerx, body.bottom - 2),
                         (body.left + 1, body.centery), (body.right - 2, body.centery)]:
            pygame.draw.rect(surf, METAL_HI, (px_ - 1, py_ - 1, 3, 3))
        if skull:
            sk = render_skull(3)
            surf.blit(sk, (rect.width // 2 - sk.get_width() // 2, 0))
        _panel_cache[key] = surf
    screen.blit(surf, (rect.x, rect.y - (18 if skull else 0)))


def clear_caches():
    _skull_cache.clear()
    _button_cache.clear()
    _panel_cache.clear()
