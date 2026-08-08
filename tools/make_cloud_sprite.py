# -*- coding: utf-8 -*-
"""Zehir bulutu sprite'ını oyunun koyu gotik paletine derecelendirir.

Üretilen ham sprite dolu ve kabarcıklıydı ama neon yeşil ve airbrush
parlamalıydı; oyunun koyu/donuk paletine hiç uymuyordu. Modelden "gotik"
istemek iki denemede de mimari üretti (taş duvarlı kuyu), o yüzden şekil
modelden, RENK buradan geliyor:

  - hue bataklık yeşiline doğru sıkıştırılır
  - doygunluk ve parlaklık düşürülür (neon gider)
  - parlaklık basamaklandırılır -> pixel-art hissi, airbrush degrade gider
  - kenara doğru koyulaştırma -> setin koyu kenarlı görünümü
  - kenar alfası yumuşak kalır ki zemine karışsın

Çalıştırma: python tools/make_cloud_sprite.py
"""
import colorsys
import math
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "vfx", "cloud_poison_raw.png")
DST = os.path.join(ROOT, "assets", "vfx", "cloud_poison.png")

TARGET_HUE = 0.245      # bataklık yeşili
HUE_PULL = 0.30         # kaynak hue'nun ne kadarı korunur
SAT_MAX = 0.78          # daha düşük tutulunca zeytin grisine kaçıp zehir
                        # kimliğini kaybediyordu
VAL_BASE = 0.10         # en koyu ton
VAL_RANGE = 0.62        # parlaklık aralığı (0.10 -> 0.72)
LEVELS = 5              # parlaklık basamağı (degrade yerine kademe)
RIM_DARKEN = 0.50       # kenardaki parlaklık çarpanı

# Kenar: kaynaktaki uzun yumuşak sönüm (0.58R -> 0.71R) airbrush gibi
# duruyordu. Eşikleyip tek adımda kesiyoruz; sınırı 1px koyu kontur veriyor,
# setin geri kalanındaki dil bu.
ALPHA_CUTOFF = 40
OUTLINE = (14, 20, 15)  # dış kontur (setin koyu kontur diline uyar)
DOWNSCALE = 96          # sprite bu boyutta saklanır; oyun nearest ile büyütür


def grade(surf):
    w, h = surf.get_size()
    cx, cy = w / 2.0, h / 2.0
    R = min(w, h) / 2.0
    out = pygame.Surface((w, h), pygame.SRCALPHA)

    for y in range(h):
        for x in range(w):
            r, g, b, a = surf.get_at((x, y))
            if a == 0:
                continue
            hh, ss, vv = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

            hh = TARGET_HUE + (hh - TARGET_HUE) * HUE_PULL
            ss = min(SAT_MAX, ss * SAT_MAX)
            vv = VAL_BASE + vv * VAL_RANGE

            # merkezden kenara doğru koyulaştır
            d = min(1.0, math.hypot(x - cx, y - cy) / R)
            vv *= 1.0 - (1.0 - RIM_DARKEN) * (d ** 2)

            # basamaklandır: degrade yerine pixel-art tonlama
            vv = round(vv * LEVELS) / LEVELS

            nr, ng, nb = colorsys.hsv_to_rgb(hh, ss, max(0.0, min(1.0, vv)))
            # Alfa eşiği: yumuşak sönüm yerine net kenar
            if a < ALPHA_CUTOFF:
                continue
            out.set_at((x, y), (int(nr * 255), int(ng * 255), int(nb * 255), 255))
    return out


def add_outline(surf):
    """Opak bölgenin dış sınırına 1px koyu kontur ekler."""
    w, h = surf.get_size()
    edge = []
    for y in range(h):
        for x in range(w):
            if surf.get_at((x, y))[3] < 120:
                continue
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if not (0 <= nx < w and 0 <= ny < h) or surf.get_at((nx, ny))[3] < 40:
                    edge.append((x, y))
                    break
    for x, y in edge:
        surf.set_at((x, y), (*OUTLINE, 235))
    return surf


def main():
    if not os.path.exists(SRC):
        raise SystemExit(
            f"kaynak yok: {SRC}\n"
            "Ham sprite'i (kirpilmis, kenari yumusatilmis hali) buraya koyun."
        )
    src = pygame.image.load(SRC).convert_alpha()
    out = grade(src)
    # Nearest ile kucult: pikselleri iri tutar, oyun da nearest ile buyutur
    out = pygame.transform.scale(out, (DOWNSCALE, DOWNSCALE))
    out = add_outline(out)
    pygame.image.save(out, DST)
    print("yazildi:", DST, out.get_size())
    print("merkez :", out.get_at((out.get_width() // 2, out.get_height() // 2)))


if __name__ == "__main__":
    main()
