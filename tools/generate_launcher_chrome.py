# -*- coding: utf-8 -*-
"""Launcher için hazır (pre-render) UI parçalarını üretir.

Launcher tkinter ile yazılı; tkinter'da çalışma zamanında 9-slice yapmak yok,
ama Tk 8.6 PNG okuyabiliyor. Bu yüzden gotik parçalar burada pygame +
ui_nineslice ile launcher'ın TAM ölçülerinde bir kez çizilip PNG olarak
kaydedilir, launcher da sadece gösterir.

Çıktı: assets/ui/gothic/launcher/
Çalıştırma: python tools/generate_launcher_chrome.py

Ölçüler launcher/main.py içindeki LAYOUT ile birebir aynı olmalı.
"""
import json
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import ui_nineslice as n9  # noqa: E402

SRC = os.path.join(ROOT, "assets", "ui", "gothic")
OUT = os.path.join(SRC, "launcher")

W, H = 720, 540          # arka plan / içerik alanı (özel başlık çubuğunun altı)
TOPBAR = (720, 40)       # özel başlık çubuğu; OS çerçevesi kapalı
ICON = 26                # başlık çubuğu ikon butonları (kapat / küçült)
PANEL = (34, 132, 652, 206)
BAR = (548, 26)
BTN_HALF = (318, 54)
BTN_FULL = (652, 54)
VERSION_BOX = (196, 64)
STATES = ["normal", "hover", "pressed", "disabled"]

# Yerleşim tek kaynak burada; launcher bunu layout.json'dan okur, böylece
# ölçüler ile konumlar birbirinden kopamaz.
POS = {
    "panel": (34, 132),
    "bar": (86, 256),
    "btn_play": (34, 378) + BTN_HALF,
    "btn_update": (368, 378) + BTN_HALF,
    "btn_notes": (34, 444) + BTN_FULL,
    "version_box": (490, 38) + VERSION_BOX,
}


def save(surf, name):
    pygame.image.save(surf, os.path.join(OUT, name))
    print(f"  {name:26s} {surf.get_width()}x{surf.get_height()}")


def build_background():
    """launcher_bg_a'yı 2x büyütüp okunabilirlik için karartma bindirir."""
    bg = pygame.image.load(os.path.join(SRC, "launcher_bg_a.png")).convert_alpha()
    # tam 2x: pixel-art'ta tam sayı ölçek, bulanıklık yok (scale = nearest)
    big = pygame.transform.scale(bg, (bg.get_width() * 2, bg.get_height() * 2))
    out = pygame.Surface((W, H))
    out.blit(big, (0, 0))  # 720x544 -> alttan 4px taşar, ay/gökyüzü korunur

    # Genel karartma: metin her yerde okunabilsin
    scrim = pygame.Surface((W, H), pygame.SRCALPHA)
    scrim.fill((8, 6, 10, 90))
    out.blit(scrim, (0, 0))

    # Alt tarafa doğru güçlenen degrade: buton ve footer bölgesi sakinleşsin
    grad = pygame.Surface((1, H), pygame.SRCALPHA)
    for y in range(H):
        t = max(0.0, (y - H * 0.42) / (H * 0.58))
        grad.set_at((0, y), (6, 5, 8, int(190 * t * t)))
    out.blit(pygame.transform.scale(grad, (W, H)), (0, 0))

    # Üst şerit: marka yazıları için hafif koyulaştırma
    top = pygame.Surface((W, 130), pygame.SRCALPHA)
    for y in range(130):
        a = int(120 * (1.0 - y / 130))
        top.fill((6, 5, 8, a), pygame.Rect(0, y, W, 1))
    out.blit(top, (0, 0))

    save(out, "bg.png")


def build_plate(asset, size, state_tint, name, darken=1.0):
    """9-slice plakayı verilen ölçüde çizip renkle tonlar (oyundaki gibi).

    darken<1: plakanın açık taş çerçevesi launcher'ın koyu arka planında fazla
    parlak kalıyordu; önce karartılıyor, renk tonu sonra bindiriliyor.
    """
    w, h = size
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    plate = n9.get(asset, w, h)
    if plate is None:
        raise SystemExit(f"{asset}: 9-slice üretilemedi ({w}x{h})")
    surf.blit(plate, (0, 0))
    if darken < 1.0:
        # BLEND_RGB_MULT sadece RGB'yi çarpar, alfa korunur
        k = int(255 * darken)
        surf.fill((k, k, k, 255), special_flags=pygame.BLEND_RGB_MULT)
    if state_tint is not None:
        tint = pygame.Surface((w, h))
        tint.fill(state_tint)
        surf.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    save(surf, name)


# Oyunun buton paletiyle aynı (ui_theme.COLORS)
BTN_COLORS = {
    "play": (146, 24, 16),     # blood
    "update": (150, 100, 22),  # gold
    "notes": (30, 78, 110),    # night
}
ASSET_FOR = {
    "normal": "button_normal.png",
    "hover": "button_hover.png",
    "pressed": "button_pressed.png",
    "disabled": "button_disabled.png",
}


def tint_for(color, state):
    if state == "disabled":
        return None
    k = 0.38 if state == "hover" else 0.26
    return tuple(int(c * k) for c in color)


def main():
    os.makedirs(OUT, exist_ok=True)
    print("launcher chrome ->", OUT)

    build_background()

    # Durum kartı
    build_plate("panel_frame.png", PANEL[2:], None, "panel.png")

    # Sürüm kutusu (ince kenarlı plaka; panel_frame min 106x106 buraya sığmaz)
    build_plate("button_normal.png", VERSION_BOX, None, "version_box.png")

    # Butonlar
    for key, color in BTN_COLORS.items():
        size = BTN_FULL if key == "notes" else BTN_HALF
        for state in STATES:
            build_plate(ASSET_FOR[state], size, tint_for(color, state),
                        f"btn_{key}_{state}.png", darken=0.66)

    # Progress bar: çerçeve + tam genişlikte dolgu (launcher soldan kırpar)
    build_plate("bar_frame.png", BAR, None, "bar.png")
    inner = n9.content_rect("bar_frame.png", pygame.Rect(0, 0, *BAR))
    print(f"  bar inner: x={inner.x} y={inner.y} {inner.width}x{inner.height}")
    for role, fill in [("bar_fill.png", "bar_fill_green.png"),
                       ("bar_fill_busy.png", "bar_fill_xp.png")]:
        src = pygame.image.load(os.path.join(SRC, fill)).convert_alpha()
        save(pygame.transform.scale(src, (inner.width, inner.height)), role)

    # Özel başlık çubuğu (OS çerçevesi kapalı olduğu için kendimiz çiziyoruz)
    build_plate("button_normal.png", TOPBAR, None, "titlebar.png", darken=0.62)

    # Başlık çubuğu ikon butonları: kapat (kırmızı X) ve küçült (aşağı ok)
    for name, asset, hover_tint in [
        ("close", "icon_close.png", (120, 24, 18)),
        ("min", "icon_arrow_down.png", (70, 74, 82)),
    ]:
        base = pygame.image.load(os.path.join(SRC, asset)).convert_alpha()
        small = pygame.transform.smoothscale(base, (ICON, ICON))
        for state, tint in [("normal", None), ("hover", hover_tint)]:
            surf = small.copy()
            surf.fill((178, 178, 178, 255), special_flags=pygame.BLEND_RGB_MULT)
            if tint is not None:
                t = pygame.Surface((ICON, ICON))
                t.fill(tint)
                surf.blit(t, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
            save(surf, f"btn_{name}_{state}.png")

    # Marka süsü
    sk = pygame.image.load(os.path.join(SRC, "skull_crest.png")).convert_alpha()
    save(pygame.transform.scale2x(sk), "crest.png")
    save(pygame.transform.smoothscale(sk, (36, 24)), "crest_small.png")

    # Launcher bunu okur; ölçü/konum ikilisi tek kaynaktan gelsin
    layout = {
        "topbar_h": TOPBAR[1],
        "content": [W, H],
        "window": [W, H + TOPBAR[1]],
        "panel_inset": n9._load_meta()["panel_frame.png"]["insets"][0],
        "bar_inner": [inner.x, inner.y, inner.width, inner.height],
        "icon": ICON,
    }
    layout.update({k: list(v) for k, v in POS.items()})
    with open(os.path.join(OUT, "layout.json"), "w", encoding="utf-8") as fh:
        json.dump(layout, fh, indent=1)
    old_txt = os.path.join(OUT, "layout.txt")
    if os.path.exists(old_txt):
        os.remove(old_txt)
    print(f"  layout.json  bar_inner={layout['bar_inner']}")
    print("bitti")


if __name__ == "__main__":
    main()
