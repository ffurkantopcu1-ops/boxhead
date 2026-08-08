"""Write assets/ui/gothic/nineslice.json and validate every inset.

No atlas is generated: slicing happens at load time straight from the source
PNG, so there is one copy of each sprite and it stays editable.

Insets are validated rather than trusted -- a corner inset that overlaps the
opposite one, or an edge strip that is fully transparent, means the sprite
would smear when stretched. Better to fail here than in the game loop.
"""
import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

pygame.init()
pygame.display.set_mode((1, 1))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI = os.path.join(ROOT, "assets", "ui", "gothic")

# left, top, right, bottom -- measured off 4x magnified rulers
SPEC = {
    "panel_frame.png": [52, 52, 52, 52],
    "panel_frame_epic.png": [56, 56, 56, 56],
    "panel_frame_small.png": [40, 40, 40, 40],
    # rails are ~6px; 5 keeps them intact while leaving the trough as much
    # room as possible at the small heights the HUD uses.
    # right inset == left: the right cap is mirrored from the left one by
    # tools/fix_asset_right_caps.py (the generated art had an open right edge)
    "bar_frame.png": [40, 5, 40, 5],
    "item_slot.png": [14, 14, 14, 14],
    "rarity_frame_common.png": [14, 14, 14, 14],
    "rarity_frame_rare.png": [14, 14, 14, 14],
    "rarity_frame_epic.png": [14, 14, 14, 14],
    "rarity_frame_legendary.png": [14, 14, 14, 14],
    "button_normal.png": [26, 12, 26, 12],
    "button_hover.png": [26, 12, 26, 12],
    "button_pressed.png": [26, 12, 26, 12],
    "button_disabled.png": [26, 12, 26, 12],
}


def trim_bounds(surf):
    """Tightest rect containing any non-transparent pixel."""
    w, h = surf.get_size()
    xs, ys, xe, ye = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            if surf.get_at((x, y))[3]:
                xs, ys = min(xs, x), min(ys, y)
                xe, ye = max(xe, x), max(ye, y)
    if xe < 0:
        raise SystemExit("fully transparent sprite")
    return [xs, ys, xe - xs + 1, ye - ys + 1]


def opaque_frac(surf, rect):
    r = pygame.Rect(rect).clip(surf.get_rect())
    if r.w <= 0 or r.h <= 0:
        return 0.0
    n = op = 0
    for y in range(r.top, r.bottom):
        for x in range(r.left, r.right):
            n += 1
            if surf.get_at((x, y))[3] > 8:
                op += 1
    return op / max(1, n)


meta, problems = {}, []
for name, (l, t, r, b) in SPEC.items():
    path = os.path.join(UI, name)
    if not os.path.exists(path):
        problems.append(f"{name}: missing")
        continue
    surf = pygame.image.load(path).convert_alpha()
    tx, ty, tw, th = trim_bounds(surf)

    if l + r >= tw or t + b >= th:
        problems.append(f"{name}: insets {l},{t},{r},{b} exceed trimmed {tw}x{th}")
        continue

    # every edge strip must carry real pixels, or stretching it shows nothing
    strips = {
        "top": (tx + l, ty, tw - l - r, t),
        "bottom": (tx + l, ty + th - b, tw - l - r, b),
        "left": (tx, ty + t, l, th - t - b),
        "right": (tx + tw - r, ty + t, r, th - t - b),
    }
    thin = {k: round(opaque_frac(surf, v), 2) for k, v in strips.items()}
    for k, v in thin.items():
        if v < 0.15:
            problems.append(f"{name}: {k} edge only {int(v * 100)}% opaque")

    meta[name] = {
        "insets": [l, t, r, b],
        "trim": [tx, ty, tw, th],
        "min_size": [l + r + 2, t + b + 2],
        "edge_opacity": thin,
    }
    print(f"{name:30s} trim={tw}x{th} insets={l},{t},{r},{b} min={l+r+2}x{t+b+2} edges={thin}")

out = os.path.join(UI, "nineslice.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=1)
print(f"\nwrote {out}  ({len(meta)} entries)")
for p in problems:
    print("  !", p)
