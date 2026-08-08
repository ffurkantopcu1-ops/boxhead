# -*- coding: utf-8 -*-
"""Sağ uçları kapalı olmayan varlıkları sol kapı aynalayarak onarır.

Üretilen bazı yatay varlıklarda (bar çerçevesi, buton plakaları) model sol uca
süslü bir kap çizip sağ ucu tuvalin kenarından taşırmış: sağ kenarda dikey
kapatma çizgisi yok, üst/alt köşeler şeffaf kalıyor. 9-slice bunu sadakatle
kopyaladığı için butonların ve barın sağ köşeleri kesik görünüyordu.

Bu script sol `inset` kadar şeridi yatay aynalayıp sağa yazar. Sol taraf hiç
değişmediği için tekrar tekrar çalıştırmak güvenlidir (idempotent).

Çalıştırma: python tools/fix_asset_right_caps.py
Sonra: python tools/generate_nineslice_meta.py
       python tools/generate_launcher_chrome.py
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI = os.path.join(ROOT, "assets", "ui", "gothic")

# dosya -> aynalanacak sol şerit genişliği (9-slice sol inset'i ile aynı)
TARGETS = {
    "bar_frame.png": 40,
    "button_normal.png": 26,
    "button_hover.png": 26,
    "button_pressed.png": 26,
    "button_disabled.png": 26,
}


def opaque_bounds(surf):
    w, h = surf.get_size()
    xs, ys, xe, ye = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            if surf.get_at((x, y))[3]:
                xs, ys = min(xs, x), min(ys, y)
                xe, ye = max(xe, x), max(ye, y)
    return pygame.Rect(xs, ys, xe - xs + 1, ye - ys + 1)


def fix(name, cap):
    path = os.path.join(UI, name)
    surf = pygame.image.load(path).convert_alpha()
    tr = opaque_bounds(surf)
    if tr.width < cap * 2 + 4:
        print(f"  {name}: çok dar, atlandı")
        return

    left = surf.subsurface(pygame.Rect(tr.x, tr.y, cap, tr.height)).copy()
    mirrored = pygame.transform.flip(left, True, False)

    # Sağ şeridi tamamen değiştir: eski açık kenar kalıntısı kalmasın
    dst = pygame.Rect(tr.right - cap, tr.y, cap, tr.height)
    surf.fill((0, 0, 0, 0), dst)
    surf.blit(mirrored, dst.topleft)

    pygame.image.save(surf, path)
    print(f"  {name:26s} trim={tr.width}x{tr.height} cap={cap} -> sağ uç kapatıldı")


def main():
    print("sağ uç onarımı:", UI)
    for name, cap in TARGETS.items():
        if os.path.exists(os.path.join(UI, name)):
            fix(name, cap)
        else:
            print(f"  {name}: yok")
    print("bitti")


if __name__ == "__main__":
    main()
