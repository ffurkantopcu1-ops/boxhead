from scenes.menu_scene import MenuScene
from scenes.game_scene import GameScene
from scenes.class_select_scene import ClassSelectScene

class SceneManager:
    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height

        # Scene constructors may consult shared preferences. Initialize these
        # before creating scenes and only enter the active scene at startup.
        self.global_settings = {'shake': True, 'sound': True}
        self.pending_save_slot = None

        self.scenes = {
            "MainMenu": MenuScene(self, screen, width, height),
            "Game": GameScene(self, screen, width, height),
            "ClassSelect": ClassSelectScene(self, screen, width, height)
        }
        self.current_scene_name = "MainMenu"
        self.current_scene = self.scenes[self.current_scene_name]
        self.current_scene.on_enter()

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
