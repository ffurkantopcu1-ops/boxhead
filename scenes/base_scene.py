import pygame

class BaseScene:
    def __init__(self, manager, screen, width, height):
        self.manager = manager
        self.screen = screen
        self.width = width
        self.height = height
        self.font_main = pygame.font.SysFont("Outfit, Roboto, Inter, Segoe UI, Arial", 72, bold=True)
        self.font_sub = pygame.font.SysFont("Outfit, Roboto, Inter, Segoe UI, Arial", 32)

    def on_enter(self):
        # Sahneler arası geçişte yapılacak işlemler
        pass

    def update(self, dt, events):
        pass

    def draw(self):
        pass
