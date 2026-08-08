import json
import os

import pygame

from scenes.menu_scene import MenuScene
from scenes.game_scene import GameScene
from scenes.class_select_scene import ClassSelectScene

SETTINGS_PATH = os.path.join("saves", "settings.json")

# Ekran modları: sıralama cycle sırasıdır
DISPLAY_MODES = ["fullscreen", "borderless", "windowed"]
DISPLAY_MODE_LABELS = {
    "fullscreen": "TAM EKRAN",
    "borderless": "ÇERÇEVESİZ PENCERE",
    "windowed": "PENCERE",
}


def load_global_settings():
    """saves/settings.json'dan kalıcı ayarları okur (yoksa varsayılanlar)."""
    settings = {"shake": True, "sound": True, "display_mode": "fullscreen"}
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            settings.update(json.load(f))
    except (OSError, ValueError):
        pass
    if settings.get("display_mode") not in DISPLAY_MODES:
        settings["display_mode"] = "fullscreen"
    return settings


def save_global_settings(settings):
    try:
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except OSError:
        pass


def create_display(mode, width, height):
    """İstenen ekran modunda pencereyi oluşturur.

    Mantıksal çözünürlük her modda (width, height) kalır; 'windowed' modda
    pygame.SCALED içeriği pencere boyutuna ölçekler ve fare koordinatlarını
    otomatik çevirir — sahne yerleşimleri hiçbir modda bozulmaz.
    """
    if mode == "windowed":
        return pygame.display.set_mode((width, height), pygame.SCALED | pygame.RESIZABLE)
    if mode == "borderless":
        os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
        return pygame.display.set_mode((width, height), pygame.NOFRAME)
    return pygame.display.set_mode((width, height), pygame.NOFRAME | pygame.FULLSCREEN)


class SceneManager:
    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height

        # Scene constructors may consult shared preferences. Initialize these
        # before creating scenes and only enter the active scene at startup.
        self.global_settings = load_global_settings()
        self.pending_save_slot = None

        self.scenes = {
            "MainMenu": MenuScene(self, screen, width, height),
            "Game": GameScene(self, screen, width, height),
            "ClassSelect": ClassSelectScene(self, screen, width, height)
        }
        self.current_scene_name = "MainMenu"
        self.current_scene = self.scenes[self.current_scene_name]
        self.current_scene.on_enter()

    # --- Ekran Modu ---
    def get_display_mode_label(self):
        return DISPLAY_MODE_LABELS.get(
            self.global_settings.get("display_mode", "fullscreen"), "TAM EKRAN")

    def cycle_display_mode(self):
        """Sıradaki ekran moduna geçer, uygular ve kaydeder."""
        current = self.global_settings.get("display_mode", "fullscreen")
        idx = DISPLAY_MODES.index(current) if current in DISPLAY_MODES else 0
        new_mode = DISPLAY_MODES[(idx + 1) % len(DISPLAY_MODES)]
        self.set_display_mode(new_mode)
        return new_mode

    def set_display_mode(self, mode):
        self.global_settings["display_mode"] = mode
        new_screen = create_display(mode, self.width, self.height)
        # set_mode yeni surface döndürebilir; tüm sahne referanslarını tazele
        self.screen = new_screen
        for scene in self.scenes.values():
            scene.screen = new_screen
        self.save_settings()

    def save_settings(self):
        save_global_settings(self.global_settings)

    def start_new_game(self, class_id):
        # Yeni oyun başladığında class_id'yi GameScene'e aktar
        game_scene = self.scenes["Game"]
        game_scene.selected_class = class_id
        game_scene.pending_save_slot = None # Sıfırla
        game_scene.is_boss_test = False
        self.change_scene("Game")

    def start_boss_test(self, class_id):
        game_scene = self.scenes["Game"]
        game_scene.selected_class = class_id
        game_scene.pending_save_slot = None
        game_scene.is_boss_test = True
        self.change_scene("Game")

    def load_game_from_menu(self, slot_name):
        """Ana menüden direkt kayıt yüklemesi yapar."""
        game_scene = self.scenes["Game"]
        game_scene.pending_save_slot = slot_name
        self.change_scene("Game")

    def change_scene(self, scene_name):
        if scene_name in self.scenes:
            self.current_scene_name = scene_name
            self.current_scene = self.scenes[scene_name]
            self.current_scene.on_enter()

    def update(self, dt, events):
        self.current_scene.update(dt, events)

    def draw(self):
        self.screen.fill((20, 20, 30)) # Koyu arka plan
        self.current_scene.draw()
