import pygame
from ui_typography import get_font

class BaseScene:
    def __init__(self, manager, screen, width, height):
        self.manager = manager
        self.screen = screen
        self.width = width
        self.height = height
        self.font_main = get_font(72, bold=True, title=True)
        self.font_sub = get_font(32)
        self.font_desc = get_font(20)

    def on_enter(self):
        # Sahneler arası geçişte yapılacak işlemler
        pass

    def update(self, dt, events):
        pass

    def draw(self):
        pass
