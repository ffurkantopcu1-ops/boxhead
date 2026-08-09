import pygame

class BaseScene:
    def __init__(self, manager, screen, width, height):
        self.manager = manager
        self.screen = screen
        self.width = width
        self.height = height
        # Gotik temayla uyumlu serif (bkz. ui_elements.UI_FONT_NAME)
        _THEME_FONT = "Georgia, Times New Roman, serif"
        self.font_main = pygame.font.SysFont(_THEME_FONT, 72, bold=True)
        self.font_sub = pygame.font.SysFont(_THEME_FONT, 32)
        self.font_desc = pygame.font.SysFont(_THEME_FONT, 20)

    def on_enter(self):
        # Sahneler arası geçişte yapılacak işlemler
        pass

    def update(self, dt, events):
        pass

    def draw(self):
        pass
