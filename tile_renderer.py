# -*- coding: utf-8 -*-
"""Prosedürel zemin çizimi — `logic/tilemap.py` verisini ekrana basar.

Kök dizindeki diğer çizim yardımcılarıyla (vfx.py, ui_theme.py, ui_nineslice.py)
aynı desende: modül düzeyinde önbellek, sahne katmanı sadece çağırır.

MALİYET MODELİ (önemli — eski kod buradaki asıl problemdi):
  Eskiden `draw_floor_to_surf` her kare, görünen HER karo için 2 adet
  `pygame.draw.rect` çağırıyordu (min zoom'da ~644 çağrı/kare, cache yok).
  Şimdi:
    * karo görselleri biome başına BİR KEZ üretilir (_tiles_for),
    * karo ızgarası (varyant + dekor + yer izi) biome başına BİR KEZ
      hesaplanır (_map_for) — kare başına gürültü matematiği YOK,
    * kare başına iş = iki adet toplu `Surface.blits()` (C tarafında döner).

Üretilen her şey YERE YATIKtır; çarpışma yoktur (bkz. logic/tilemap.py).
"""

import math
import random

import pygame

from logic.biome_system import BiomeSystem
from logic.tilemap import VARIANT_COUNT

# (biome_id) -> [Surface] * VARIANT_COUNT
_tile_cache = {}
# (biome_id) -> Surface (arena kenarı moloz bandı)
_border_cache = {}
# (biome_id, kind) -> [Surface] * _DECOR_VARIANTS
_decor_cache = {}
# (biome_id, kind, radius_bucket) -> Surface
_landmark_cache = {}
# (seed, biome_id) -> {"variant": [...], "decor": {...}, "landmarks": [...]}
_map_cache = {}

_DECOR_VARIANTS = 6
_LANDMARK_BUCKETS = (110, 165, 220)


def clear_cache():
    """Yeni oyun/biome paleti değişimi sonrası önbelleği boşaltır."""
    _tile_cache.clear()
    _border_cache.clear()
    _decor_cache.clear()
    _landmark_cache.clear()
    _map_cache.clear()


# --- PALET -------------------------------------------------------------

def _clamp(v):
    return max(0, min(255, int(v)))


def _shift(color, amount):
    return tuple(_clamp(c + amount) for c in color[:3])


def _mix(a, b, t):
    return tuple(_clamp(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _palette(biome_id):
    """Biome'un çizim paleti. Kaynak `BiomeSystem.BIOMES` — floor_color_1/2,
    grid_line_color ve accent_color alanları eskiden ÖLÜ veriydi (hiçbir yer
    okumuyordu); artık gerçekten zemini belirliyorlar."""
    b = BiomeSystem.BIOMES.get(biome_id) or BiomeSystem.BIOMES["forest"]
    return {
        "base": b["floor_color_1"],
        "base2": b["floor_color_2"],
        "seam": b["grid_line_color"],
        "accent": b.get("accent_color", _shift(b["floor_color_2"], 40)),
    }


# --- KARO GÖRSELLERİ ---------------------------------------------------

def _make_tile(pal, variant, size, rng):
    """Tek bir zemin karosu. Varyantlar:
      0-3 sade taban (yalnızca gürültü tohumu farklı)
      4   çatlaklı
      5   accent yaması (yosun/köz/kırağı)
      6   aşınmış koyu leke
      7   çakıllı
    """
    surf = pygame.Surface((size, size)).convert()
    # Taban tonu varyanttan varyanta NEREDEYSE aynı (0.25-0.46 aralığı, iki
    # zemin rengi arası ~3 RGB birimi). Rastgele geniş bir aralık kullanılınca
    # her karo farklı parlaklıkta düz bir kare oluyor ve zemin yamalı bir
    # dama tahtasına dönüyordu — çeşitlilik dokudan ve dekordan gelmeli,
    # karo parlaklığından değil.
    base = _mix(pal["base"], pal["base2"], 0.25 + (variant % 4) * 0.07)
    surf.fill(base)

    # Taban gürültüsü: 1-3 px benekler. Düz dolgu top-down'da plastik gibi
    # duruyordu; benek zemine doku hissi veriyor.
    for _ in range(210):
        x, y = rng.randrange(size), rng.randrange(size)
        d = rng.randint(-13, 13)
        pygame.draw.rect(surf, _shift(base, d), (x, y, rng.randint(1, 3), rng.randint(1, 3)))

    if variant == 4:      # çatlaklar
        for _ in range(rng.randint(2, 3)):
            x, y = rng.randrange(size), rng.randrange(size)
            pts = [(x, y)]
            ang = rng.random() * math.tau
            for _ in range(rng.randint(4, 7)):
                ang += rng.uniform(-0.8, 0.8)
                x += math.cos(ang) * rng.randint(6, 16)
                y += math.sin(ang) * rng.randint(6, 16)
                pts.append((x, y))
            pygame.draw.lines(surf, _shift(base, -26), False, pts, 2)

    # NOT (varyant 5 ve 6): lekeler karo kenarında KESİLMEMELİ — kesilirse
    # karo sınırında dümdüz bir kenar oluşuyor ve tam da kaçınmaya çalıştığımız
    # ızgara geri geliyor. Bu yüzden merkez, yarıçap kadar içeri alınıyor.
    elif variant == 5:    # accent yaması
        for _ in range(rng.randint(3, 5)):
            r = rng.randint(10, 24)
            cx = rng.randint(r, size - r)
            cy = rng.randint(r, size - r)
            col = _mix(base, pal["accent"], rng.uniform(0.35, 0.7))
            pygame.draw.circle(surf, col, (cx, cy), r)
            pygame.draw.circle(surf, _mix(col, base, 0.5), (cx, cy), r, 2)

    elif variant == 6:    # aşınmış koyu leke
        for _ in range(rng.randint(2, 4)):
            r = rng.randint(16, 30)
            cx = rng.randint(r, size - r)
            cy = rng.randint(r, size - r)
            pygame.draw.circle(surf, _shift(base, -16), (cx, cy), r)

    elif variant == 7:    # çakıl
        for _ in range(rng.randint(14, 22)):
            x, y = rng.randrange(size), rng.randrange(size)
            r = rng.randint(2, 5)
            pygame.draw.circle(surf, _shift(base, 16), (x, y), r)
            pygame.draw.circle(surf, _shift(base, -20), (x, y), r, 1)

    # Kenar gölgesi — SADECE sağ ve alt kenara. Dört kenara çizilirse komşu
    # karonun kendi kenarıyla üst üste binip iki kat kalın, kusursuz düz bir
    # çizgi oluşuyor ve zemin milimetrik kağıda dönüyordu (eski sabit grid
    # çizgisinin da sorunu buydu). Çizgi ayrıca KESİNTİLİ: doğal zeminde
    # kusursuz düz çizgi yapay duruyor, kesik gölge toprak/kaya sınırı gibi
    # okunuyor.
    seam = pal["seam"]
    edge = pygame.Surface((size, size), pygame.SRCALPHA)
    a = 34 + variant * 3
    for axis in (0, 1):
        pos = 0
        while pos < size:
            seg = rng.randint(12, 30)
            if rng.random() < 0.72:
                end = min(size, pos + seg)
                if axis == 0:
                    pygame.draw.line(edge, (*seam, a), (pos, size - 1), (end, size - 1), 2)
                else:
                    pygame.draw.line(edge, (*seam, a), (size - 1, pos), (size - 1, end), 2)
            pos += seg + rng.randint(2, 10)
    surf.blit(edge, (0, 0))
    return surf


def _tiles_for(biome_id):
    tiles = _tile_cache.get(biome_id)
    if tiles is None:
        pal = _palette(biome_id)
        size = 128
        tiles = [_make_tile(pal, v, size, random.Random(hash((biome_id, v)) & 0xFFFF))
                 for v in range(VARIANT_COUNT)]
        _tile_cache[biome_id] = tiles
    return tiles


def _border_for(biome_id):
    surf = _border_cache.get(biome_id)
    if surf is None:
        pal = _palette(biome_id)
        rng = random.Random(hash((biome_id, "border")) & 0xFFFF)
        size = 128
        surf = pygame.Surface((size, size)).convert()
        base = _shift(pal["base"], -22)
        surf.fill(base)
        # Moloz: arena sınırı görünür olsun (oyuncu 50..4950'ye kilitli ama
        # bunun görsel karşılığı yoktu, harita sonsuz boşluk gibiydi).
        for _ in range(46):
            x, y = rng.randrange(size), rng.randrange(size)
            r = rng.randint(3, 9)
            pygame.draw.circle(surf, _shift(base, rng.randint(-14, 22)), (x, y), r)
            pygame.draw.circle(surf, _shift(base, -24), (x, y), r, 1)
        _border_cache[biome_id] = surf
    return surf


# --- DEKOR -------------------------------------------------------------

def _make_decor(pal, kind, rng):
    """Yere yatık küçük dekor. Boyut ~48px; konum/ölçek çeşitliliği
    tilemap.decor_at'ten gelir, burada yalnızca görsel varyasyon üretilir."""
    s = 48
    surf = pygame.Surface((s, s), pygame.SRCALPHA)
    c = s // 2
    acc = pal["accent"]
    base = pal["base"]

    if kind == "tuft":                      # ot tutamı
        for _ in range(rng.randint(5, 8)):
            x = c + rng.randint(-9, 9)
            h = rng.randint(9, 18)
            col = _mix(acc, (40, 90, 30), rng.random() * 0.5)
            pygame.draw.line(surf, col, (x, c + 8), (x + rng.randint(-5, 5), c + 8 - h), 2)

    elif kind == "pebble":                  # çakıl öbeği
        for _ in range(rng.randint(2, 4)):
            x, y = c + rng.randint(-11, 11), c + rng.randint(-8, 8)
            r = rng.randint(3, 6)
            pygame.draw.circle(surf, _shift(base, 26), (x, y), r)
            pygame.draw.circle(surf, _shift(base, -22), (x, y), r, 1)

    elif kind == "root":                    # kök / dal
        pts, x, y, ang = [], c - 14, c, rng.uniform(-0.5, 0.5)
        for _ in range(5):
            pts.append((x, y))
            ang += rng.uniform(-0.5, 0.5)
            x += math.cos(ang) * 7
            y += math.sin(ang) * 7
        pygame.draw.lines(surf, _shift(base, -26), False, pts, 3)

    elif kind == "leaf":                    # yaprak döküntüsü
        for _ in range(rng.randint(3, 6)):
            x, y = c + rng.randint(-13, 13), c + rng.randint(-13, 13)
            pygame.draw.ellipse(surf, _mix(acc, (120, 90, 40), rng.random()),
                                (x, y, rng.randint(4, 8), rng.randint(3, 5)))

    elif kind == "mushroom":
        x, y = c, c
        pygame.draw.rect(surf, _shift(base, 34), (x - 1, y, 3, 6))
        pygame.draw.ellipse(surf, (150, 60, 55), (x - 6, y - 5, 13, 8))

    elif kind == "crack_hot":               # kızıl çatlak
        pts, x, y, ang = [], c - 15, c, rng.uniform(-0.6, 0.6)
        for _ in range(6):
            pts.append((x, y))
            ang += rng.uniform(-0.6, 0.6)
            x += math.cos(ang) * 6
            y += math.sin(ang) * 6
        pygame.draw.lines(surf, (150, 55, 20), False, pts, 3)
        pygame.draw.lines(surf, (235, 140, 45), False, pts, 1)

    elif kind == "ash":
        for _ in range(rng.randint(4, 7)):
            x, y = c + rng.randint(-13, 13), c + rng.randint(-13, 13)
            pygame.draw.circle(surf, (86, 80, 76), (x, y), rng.randint(2, 5))

    elif kind == "obsidian":
        pts = [(c + rng.randint(-11, 11), c + rng.randint(-11, 11)) for _ in range(rng.randint(4, 6))]
        pygame.draw.polygon(surf, (34, 28, 34), pts)
        pygame.draw.polygon(surf, (96, 74, 88), pts, 1)

    elif kind == "fissure":
        pygame.draw.ellipse(surf, (120, 45, 18), (c - 15, c - 5, 30, 11))
        pygame.draw.ellipse(surf, (225, 120, 40), (c - 10, c - 3, 20, 6))

    elif kind == "snow":
        for _ in range(rng.randint(3, 5)):
            x, y = c + rng.randint(-12, 12), c + rng.randint(-10, 10)
            pygame.draw.circle(surf, (218, 228, 240), (x, y), rng.randint(5, 10))

    elif kind == "shard":
        pts = [(c, c - 13), (c + rng.randint(5, 9), c + 6), (c - rng.randint(5, 9), c + 6)]
        pygame.draw.polygon(surf, (150, 190, 220), pts)
        pygame.draw.polygon(surf, (210, 235, 255), pts, 1)

    elif kind == "crack_ice":
        for _ in range(rng.randint(2, 3)):
            a = rng.random() * math.tau
            pygame.draw.line(surf, (176, 208, 232),
                             (c, c), (c + math.cos(a) * 15, c + math.sin(a) * 15), 2)

    elif kind == "frost":
        pygame.draw.circle(surf, (188, 214, 236, 130), (c, c), rng.randint(9, 15))

    elif kind == "rune":
        col = (150, 96, 200)
        pygame.draw.circle(surf, col, (c, c), 11, 2)
        for _ in range(3):
            a = rng.random() * math.tau
            pygame.draw.line(surf, col, (c, c), (c + math.cos(a) * 9, c + math.sin(a) * 9), 2)

    elif kind == "shard_void":
        pts = [(c, c - 12), (c + 7, c), (c, c + 12), (c - 7, c)]
        pygame.draw.polygon(surf, (58, 34, 84), pts)
        pygame.draw.polygon(surf, (156, 104, 210), pts, 1)

    elif kind == "rift":
        pygame.draw.ellipse(surf, (24, 10, 34), (c - 16, c - 5, 32, 11))
        pygame.draw.ellipse(surf, (140, 70, 190), (c - 16, c - 5, 32, 11), 1)

    elif kind == "spark":
        for _ in range(rng.randint(3, 5)):
            x, y = c + rng.randint(-12, 12), c + rng.randint(-12, 12)
            pygame.draw.circle(surf, (180, 130, 230), (x, y), rng.randint(1, 3))

    return surf


def _decor_for(biome_id, kind):
    key = (biome_id, kind)
    variants = _decor_cache.get(key)
    if variants is None:
        pal = _palette(biome_id)
        # convert_alpha(): SRCALPHA yüzeyler ekran biçimine çevrilmezse pygame
        # her blit'te yavaş yolu kullanır. Kare başına ~120 dekor blit'i var,
        # dönüşüm bir kez yapılıp önbelleğe alınıyor.
        variants = [_make_decor(pal, kind, random.Random(hash((biome_id, kind, i)) & 0xFFFF)).convert_alpha()
                    for i in range(_DECOR_VARIANTS)]
        _decor_cache[key] = variants
    return variants


# --- YER İZLERİ (landmark) ---------------------------------------------

def _landmark_for(biome_id, kind, radius):
    bucket = min(_LANDMARK_BUCKETS, key=lambda b: abs(b - radius))
    key = (biome_id, kind, bucket)
    surf = _landmark_cache.get(key)
    if surf is not None:
        return surf, bucket

    pal = _palette(biome_id)
    rng = random.Random(hash(key) & 0xFFFF)
    d = bucket * 2
    surf = pygame.Surface((d, d), pygame.SRCALPHA)
    c = bucket

    if kind == "moss_ring":
        for _ in range(26):
            a = rng.random() * math.tau
            rr = bucket * rng.uniform(0.45, 0.98)
            pygame.draw.circle(surf, (*_mix(pal["base"], pal["accent"], 0.75), 150),
                               (int(c + math.cos(a) * rr), int(c + math.sin(a) * rr)),
                               rng.randint(12, 30))
    elif kind == "scorch":
        pygame.draw.circle(surf, (18, 12, 10, 170), (c, c), bucket)
        pygame.draw.circle(surf, (40, 24, 18, 120), (c, c), int(bucket * 0.7))
        for _ in range(8):
            a = rng.random() * math.tau
            pygame.draw.line(surf, (150, 60, 24, 130), (c, c),
                             (c + math.cos(a) * bucket, c + math.sin(a) * bucket), 3)
    elif kind == "frozen_pool":
        pygame.draw.circle(surf, (120, 156, 190, 150), (c, c), bucket)
        pygame.draw.circle(surf, (188, 216, 238, 170), (c, c), bucket, 4)
        for _ in range(7):
            a = rng.random() * math.tau
            pygame.draw.line(surf, (206, 230, 248, 130), (c, c),
                             (c + math.cos(a) * bucket * 0.85, c + math.sin(a) * bucket * 0.85), 2)
    else:  # rune_circle
        pygame.draw.circle(surf, (108, 60, 160, 90), (c, c), bucket)
        pygame.draw.circle(surf, (168, 110, 220, 170), (c, c), bucket, 3)
        pygame.draw.circle(surf, (168, 110, 220, 130), (c, c), int(bucket * 0.62), 2)
        for i in range(8):
            a = i * math.tau / 8
            x, y = c + math.cos(a) * bucket * 0.8, c + math.sin(a) * bucket * 0.8
            pygame.draw.line(surf, (196, 150, 240, 160), (x - 5, y - 5), (x + 5, y + 5), 2)

    surf = surf.convert_alpha()     # bkz. _decor_for: yavaş blit yolundan kaçın
    _landmark_cache[key] = surf
    return surf, bucket


# --- KARO IZGARASI ÖN HESABI -------------------------------------------

def _map_for(tmap, biome_id):
    """Tüm arenanın karo verisini bir kez hesaplar (5000/128 -> ~40x40 = 1600
    karo). Kare başına gürültü matematiği yapmamak için; biome ya da seed
    değişince yeniden üretilir."""
    key = (tmap.seed, biome_id)
    data = _map_cache.get(key)
    if data is not None:
        return data

    n = tmap.tiles_across
    variant = {}
    decor = {}
    landmarks = []
    for tx in range(-1, n + 2):
        for ty in range(-1, n + 2):
            if tmap.is_border(tx, ty):
                continue
            variant[(tx, ty)] = tmap.variant_at(tx, ty)
            items = tmap.decor_at(tx, ty, biome_id)
            if items:
                cell = []
                for kind, ox, oy, sz, rot in items:
                    variants = _decor_for(biome_id, kind)
                    src = variants[int(rot * _DECOR_VARIANTS) % _DECOR_VARIANTS]
                    if abs(sz - 1.0) > 0.08:
                        w = max(6, int(src.get_width() * sz))
                        src = pygame.transform.smoothscale(src, (w, w))
                    cell.append((src, ox - src.get_width() // 2, oy - src.get_height() // 2))
                decor[(tx, ty)] = cell
            lm = tmap.landmark_at(tx, ty, biome_id)
            if lm:
                kind, wx, wy, r = lm
                surf, bucket = _landmark_for(biome_id, kind, r)
                landmarks.append((surf, wx - bucket, wy - bucket, bucket * 2))

    data = {"variant": variant, "decor": decor, "landmarks": landmarks}
    _map_cache[key] = data
    return data


# --- ÇİZİM -------------------------------------------------------------

def draw_floor(surf, camera_x, camera_y, width, height, biome_id, tmap):
    """Görünen zemini `surf` üzerine basar. Yüzeyi ayrıca temizlemeye gerek
    yok — karolar opak ve görüş alanının tamamını kaplıyor."""
    ts = tmap.tile_size
    tiles = _tiles_for(biome_id)
    border = _border_for(biome_id)
    data = _map_for(tmap, biome_id)
    variant, decor = data["variant"], data["decor"]

    tx0 = int(camera_x // ts)
    ty0 = int(camera_y // ts)
    tx1 = int((camera_x + width) // ts) + 1
    ty1 = int((camera_y + height) // ts) + 1

    floor_blits = []
    decor_blits = []
    for tx in range(tx0, tx1 + 1):
        px = tx * ts - camera_x
        for ty in range(ty0, ty1 + 1):
            py = ty * ts - camera_y
            v = variant.get((tx, ty))
            if v is None:                      # sınır bandı / dünya dışı
                floor_blits.append((border, (px, py)))
                continue
            floor_blits.append((tiles[v], (px, py)))
            cell = decor.get((tx, ty))
            if cell:
                for src, ox, oy in cell:
                    decor_blits.append((src, (px + ox, py + oy)))

    surf.blits(floor_blits, doreturn=False)

    # Yer izleri dekorun ALTINDA: dekor izin üstünde kalsın, iz zeminin.
    for lsurf, wx, wy, size in data["landmarks"]:
        sx, sy = wx - camera_x, wy - camera_y
        if -size <= sx <= width and -size <= sy <= height:
            surf.blit(lsurf, (sx, sy))

    if decor_blits:
        surf.blits(decor_blits, doreturn=False)
