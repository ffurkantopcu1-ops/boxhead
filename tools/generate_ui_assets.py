# -*- coding: utf-8 -*-
"""ui_theme şablonlarından assets/ui/ altına PNG üretir.

Kullanım (repo kökünden):
    python tools/generate_ui_assets.py

Üretilenler:
    assets/ui/skull.png            - 25x14 native kurukafa spriteı
    assets/ui/skull_glow.png       - hover (gözler parlak) varyantı
    assets/ui/button_<durum>.png   - 300x60 örnek banner buton (4 durum)
    assets/ui/panel_template.png   - 400x300 metal çerçeveli panel örneği
    assets/ui/theme_sheet.png      - DESIGN.md'de referans verilen genel bakış

Oyun çalışırken butonlar/paneller ui_theme.py tarafından boyuta göre
prosedürel üretilir; buradaki PNG'ler şablon/referans ve dış kullanım içindir.
"""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame
pygame.init()
pygame.font.init()

import ui_theme

OUT_DIR = os.path.join(ROOT, 'assets', 'ui')


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    pygame.image.save(ui_theme.render_skull(1), os.path.join(OUT_DIR, 'skull.png'))
    pygame.image.save(ui_theme.render_skull(1, glow=True), os.path.join(OUT_DIR, 'skull_glow.png'))

    for state in ('normal', 'hover', 'pressed', 'disabled'):
        surf, _ = ui_theme.render_banner_button(
            300, 60, 'BUTTON', ui_theme.COLORS['blood'], state=state, skull=True)
        pygame.image.save(surf, os.path.join(OUT_DIR, f'button_{state}.png'))

    panel = pygame.Surface((400, 318), pygame.SRCALPHA)
    ui_theme.draw_panel(panel, pygame.Rect(0, 18, 400, 300), skull=True)
    pygame.image.save(panel, os.path.join(OUT_DIR, 'panel_template.png'))

    # Genel bakış sayfası
    sheet = pygame.Surface((760, 560))
    sheet.fill((38, 32, 30))
    font = pygame.font.SysFont('Segoe UI', 18, bold=True)
    y = 14
    for state in ('normal', 'hover', 'pressed', 'disabled'):
        surf, over = ui_theme.render_banner_button(
            300, 56, state.upper(), ui_theme.COLORS['blood'], state=state, skull=True)
        sheet.blit(surf, (20, y))
        y += surf.get_height() + 6
    x = 360
    y = 30
    for name, col in ui_theme.COLORS.items():
        surf, over = ui_theme.render_banner_button(220, 44, name.upper(), col, skull=False)
        sheet.blit(surf, (x, y))
        lbl = font.render(str(col), True, (200, 195, 185))
        sheet.blit(lbl, (x + 230, y + 12))
        y += surf.get_height() + 8
    pygame.image.save(sheet, os.path.join(OUT_DIR, 'theme_sheet.png'))

    print(f'{OUT_DIR} icine yazildi: skull, skull_glow, 4x button, panel_template, theme_sheet')
    return 0


if __name__ == '__main__':
    sys.exit(main())
