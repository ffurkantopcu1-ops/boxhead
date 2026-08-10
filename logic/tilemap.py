# -*- coding: utf-8 -*-
"""Prosedürel arena haritası — SAF VERİ katmanı (pygame/numpy YOK).

Harita bir dizi olarak saklanmaz; her karo `seed + (tx, ty)` üzerinden ANINDA
türetilir. Sonuç:
  * bellek maliyeti sıfır (5000x5000 dünya = 39x39 karo değil, 1521 karo; ama
    ileride dünya büyürse de maliyet değişmez),
  * aynı seed her zaman aynı haritayı verir — kayıt/yükleme sonrası arena
    birebir aynı görünür (seed `SaveManager` tarafından taşınır),
  * çizim katmanı (tile_renderer.py) yalnızca EKRANDA görünen karoları sorar.

Tasarım notu: burada hiçbir şey çarpışmaz. Üretilen her şey YERE YATIK
dekordur (çatlak, yosun, kemik, is lekesi). Duvar/kaya gibi engeller eklemek
hareket ve düşman yönelimini değiştirirdi; o ayrı bir karar.
"""

# Karo boyutu: çarpışma grid'i (GameLogic.grid_size) ile aynı tutuldu.
TILE_SIZE = 128

# Zemin varyantı sayısı. 0-3 "sade" taban (yalnızca gürültü tohumu farklı),
# 4-7 belirgin varyantlar (çatlak, yama, aşınma, çakıl). Ağırlıklar
# variant_at() içinde; sade olanlar baskın ki zemin gürültülü görünmesin.
VARIANT_COUNT = 8

# Dekor türleri biome'a göre seçilir (bkz. BIOME_DECOR). Çizim karşılıkları
# tile_renderer._draw_decor içinde; buradaki isimler PAYLAŞILAN SÖZLEŞMEdir.
BIOME_DECOR = {
    "forest": ("tuft", "pebble", "root", "leaf", "mushroom"),
    "lava":   ("crack_hot", "pebble", "ash", "obsidian", "fissure"),
    "ice":    ("snow", "pebble", "shard", "crack_ice", "frost"),
    "void":   ("rune", "pebble", "shard_void", "rift", "spark"),
}
DEFAULT_DECOR = BIOME_DECOR["forest"]

_MASK = 0xFFFFFFFF


def _hash01(x, y, salt, seed):
    """(x, y, salt, seed) -> [0, 1) deterministik. Tam sayı aritmetiği; aynı
    girdiler her platformda aynı çıktıyı verir (random modülüne bağlı değil)."""
    h = (x * 374761393 + y * 668265263 + salt * 2147483647 + seed * 1013904223) & _MASK
    h = ((h ^ (h >> 13)) * 1274126177) & _MASK
    h ^= h >> 16
    return h / 4294967296.0


def _smoothstep(t):
    return t * t * (3.0 - 2.0 * t)


def _value_noise(x, y, salt, seed):
    """Bilineer + smoothstep değer gürültüsü -> [0, 1). Yumuşak, büyük ölçekli
    lekeler için (yosun bölgeleri, is bölgeleri). Perlin değil ama karo
    ölçeğinde farkı görünmez ve bağımlılık gerektirmez."""
    x0, y0 = int(x // 1), int(y // 1)
    fx, fy = x - x0, y - y0
    sx, sy = _smoothstep(fx), _smoothstep(fy)

    n00 = _hash01(x0, y0, salt, seed)
    n10 = _hash01(x0 + 1, y0, salt, seed)
    n01 = _hash01(x0, y0 + 1, salt, seed)
    n11 = _hash01(x0 + 1, y0 + 1, salt, seed)

    top = n00 + (n10 - n00) * sx
    bot = n01 + (n11 - n01) * sx
    return top + (bot - top) * sy


class TileMap:
    """Tek bir arena örneği. `seed` dışında durum tutmaz — thread-safe ve
    kopyalanabilir; kaydedilen tek şey seed'dir."""

    def __init__(self, seed=0, world_size=5000, tile_size=TILE_SIZE):
        self.seed = int(seed) & _MASK
        self.world_size = world_size
        self.tile_size = tile_size
        self.tiles_across = int(world_size // tile_size) + 1

    # --- ZEMİN ---------------------------------------------------------

    def variant_at(self, tx, ty):
        """Karonun zemin varyantı (0..VARIANT_COUNT-1).

        İki ölçek birleşir: düşük frekanslı gürültü BÖLGE karakterini
        (yosunlu/aşınmış alanlar kümelensin diye), karo-başı hash ise tekil
        varyasyonu verir. Yalnızca hash kullanılsaydı zemin tuz-biber
        görünürdü; yalnızca gürültü kullanılsaydı geniş düz alanlar oluşurdu.
        """
        region = _value_noise(tx * 0.09, ty * 0.09, 11, self.seed)
        local = _hash01(tx, ty, 23, self.seed)

        # Bölge eşiği geçilmediyse sade tabanlardan biri (0-3)
        if region < 0.62:
            return int(local * 4) & 3

        # Bölge içinde: %55 sade kalsın ki yama bölgesi de tekdüze olmasın
        if local < 0.55:
            return int(local * 7.27) & 3
        # Bölge karakterini gürültünün kendisi seçer -> komşu karolar uyumlu
        return 4 + int(region * 997) % 4

    # --- DEKOR ---------------------------------------------------------

    def decor_at(self, tx, ty, biome_id):
        """Karodaki yere yatık dekorlar: ((kind, ox, oy, size, rot), ...).

        ox/oy karo İÇİNDE piksel ofsetidir. Boş tuple çoğunluktadır — dekor
        yoğunluğu ~%38; daha fazlası zemini okunmaz yapıyor, daha azı 'lean'
        hissini geri getiriyor.
        """
        d0 = _hash01(tx, ty, 101, self.seed)
        if d0 > 0.38:
            return ()

        kinds = BIOME_DECOR.get(biome_id, DEFAULT_DECOR)
        # %28 ihtimalle iki parça (kümelenme hissi)
        count = 2 if d0 < 0.11 else 1

        out = []
        ts = self.tile_size
        for i in range(count):
            k = _hash01(tx, ty, 211 + i * 7, self.seed)
            ox = _hash01(tx, ty, 307 + i * 7, self.seed)
            oy = _hash01(tx, ty, 401 + i * 7, self.seed)
            sz = _hash01(tx, ty, 503 + i * 7, self.seed)
            rt = _hash01(tx, ty, 601 + i * 7, self.seed)
            out.append((
                kinds[int(k * len(kinds)) % len(kinds)],
                int(14 + ox * (ts - 28)),
                int(14 + oy * (ts - 28)),
                0.55 + sz * 0.75,          # ölçek çarpanı
                rt,                         # 0..1, çizimde açıya çevrilir
            ))
        return tuple(out)

    # --- BÜYÜK ÖLÇEKLİ İZLER -------------------------------------------

    def landmark_at(self, tx, ty, biome_id):
        """Seyrek, karodan büyük yer izi (rün çemberi, krater izi, donmuş
        göl...). ~1/70 karo. Dönüş: (kind, cx, cy, radius) veya None.

        Bunlar da yere yatıktır — oyuncu üzerinden geçer. Amaç: boş düzlükte
        göz için sabit nokta ve 'burayı daha önce gördüm' hissi."""
        if _hash01(tx, ty, 809, self.seed) > 0.0143:   # ~1/70
            return None
        kind = {
            "forest": "moss_ring",
            "lava":   "scorch",
            "ice":    "frozen_pool",
            "void":   "rune_circle",
        }.get(biome_id, "moss_ring")
        r = 90 + _hash01(tx, ty, 907, self.seed) * 130
        return (kind, tx * self.tile_size + self.tile_size // 2,
                ty * self.tile_size + self.tile_size // 2, r)

    # --- SINIR ---------------------------------------------------------

    def is_border(self, tx, ty):
        """Arena kenarındaki moloz bandı. Oyuncu 50..4950 arasına
        kilitleniyor (entities/player.py) ama bunun görsel karşılığı yoktu —
        harita sonsuz boşluk gibi duruyordu."""
        n = self.tiles_across - 1
        return tx <= 0 or ty <= 0 or tx >= n or ty >= n
