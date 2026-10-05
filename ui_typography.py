"""Shared, cached Turkish-capable fonts for readable interface text."""
import pygame
import os
from pathlib import Path

BODY_FONT = 'Segoe UI, DejaVu Sans, Arial'
TITLE_FONT = 'Georgia, Times New Roman, DejaVu Serif'
_CACHE = {}

def get_font(size, bold=False, title=False):
    key=(int(size),bool(bold),bool(title))
    if key not in _CACHE:
        # SysFont can resolve Segoe UI to its Light face on Windows.
        # Select the actual regular/bold files so small text has solid strokes.
        path=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/('segoeuib.ttf' if bold else 'segoeui.ttf')
        if not title and path.is_file():
            _CACHE[key]=pygame.font.Font(str(path),key[0])
        else:
            _CACHE[key]=pygame.font.SysFont(TITLE_FONT if title else BODY_FONT,key[0],bold=key[1])
    return _CACHE[key]

def fit_font(text,size,width,bold=False,min_size=14,max_height=None):
    """Fit by rasterizing at a native size, never scaling rendered letters."""
    floor=min(size,min_size)
    for point in range(int(size),int(floor)-1,-1):
        font=get_font(point,bold)
        if font.size(text)[0]<=width and (max_height is None or font.get_height()<=max_height):
            return font,text
    font=get_font(floor,bold)
    clipped=text
    while clipped and font.size(clipped+'…')[0]>width:
        clipped=clipped[:-1]
    return font,clipped+'…'
