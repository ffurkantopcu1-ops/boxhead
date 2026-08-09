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
    # sound: eski sürümlerde açık/kapalı bir bayraktı ve HİÇBİR ŞEYE bağlı
    # değildi (oyunda ses yoktu). Artık 0-100 arası yüzde. Eski kayıtlarla
    # uyumluluk: True -> 70, False -> 0.
    settings = {"shake": True, "sound": 70, "display_mode": "fullscreen"}
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            settings.update(json.load(f))
    except (OSError, ValueError):
        pass
    if settings.get("display_mode") not in DISPLAY_MODES:
        settings["display_mode"] = "fullscreen"

    vol = settings.get("sound", 70)
    if isinstance(vol, bool):
        vol = 70 if vol else 0
    try:
        vol = int(vol)
    except (TypeError, ValueError):
        vol = 70
    settings["sound"] = max(0, min(100, vol))
    return settings


def save_global_settings(settings):
    try:
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except OSError:
        pass


def create_display(mode, logical_w, logical_h):
    """İstenen ekran modunda fiziksel pencereyi oluşturur.
    Mantıksal çözünürlük 1920x1080'de kalır; manuel ölçekleme yapılır.
    """
    # Münhasır tam ekranda SDL, pencere odağı kaybedince oyunu VARSAYILAN
    # OLARAK simge durumuna küçültür. Bu yüzden Win+Shift+S (ekran alıntısı),
    # bildirim tıklaması veya alt-tab oyunu alta düşürüyordu. Hint set_mode'dan
    # ÖNCE verilmeli.
    os.environ.setdefault("SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS", "0")

    desktop_sizes = pygame.display.get_desktop_sizes()
    desktop_w, desktop_h = desktop_sizes[0] if desktop_sizes else (1920, 1080)
    
    if mode == "windowed":
        os.environ["SDL_VIDEO_WINDOW_POS"] = "center"
        screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
        try:
            import pygame._sdl2 as sdl2
            win = sdl2.Window.from_display_module()
            win.position = sdl2.WINDOWPOS_CENTERED
        except Exception:
            pass
        return screen
    
    if mode == "borderless":
        os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
        screen = pygame.display.set_mode((desktop_w, desktop_h), pygame.NOFRAME)
        try:
            import pygame._sdl2 as sdl2
            win = sdl2.Window.from_display_module()
            win.position = (0, 0)
        except Exception:
            pass
        return screen

    return pygame.display.set_mode((desktop_w, desktop_h), pygame.FULLSCREEN)


class SceneManager:
    def __init__(self, screen, width, height):
        self.real_screen = screen
        self.width = width
        self.height = height
        self.logical_surface = pygame.Surface((width, height))
        self.screen = self.logical_surface

        # Scene constructors may consult shared preferences. Initialize these
        # before creating scenes and only enter the active scene at startup.
        self.global_settings = load_global_settings()
        self.pending_save_slot = None

        self.scenes = {
            "MainMenu": MenuScene(self, self.screen, width, height),
            "Game": GameScene(self, self.screen, width, height),
            "ClassSelect": ClassSelectScene(self, self.screen, width, height)
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
        self.real_screen = new_screen
        # scene'lerin screen referansı zaten self.logical_surface olarak sabit
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
        
        # Manuel ölçekleme: logical_surface'ı fiziksel ekrana çiz
        rs_size = self.real_screen.get_size()
        if rs_size != (self.width, self.height):
            scaled = pygame.transform.smoothscale(self.screen, rs_size)
            self.real_screen.blit(scaled, (0, 0))
        else:
            self.real_screen.blit(self.screen, (0, 0))
