import os
import unittest
from types import SimpleNamespace

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')

try:
    import pygame
    from logic.game_logic import GameLogic
    from entities.projectile_pool import ProjectilePool
    from scene_manager import SceneManager
except ModuleNotFoundError:
    pygame = None
    GameLogic = None
    ProjectilePool = None
    SceneManager = None


@unittest.skipIf(pygame is None, 'pygame is not installed')
class TestSceneUi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1366, 768))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.manager = SceneManager(self.screen, 1366, 768)

    def test_startup_only_enters_main_menu(self):
        self.assertEqual(self.manager.current_scene_name, 'MainMenu')
        self.assertFalse(hasattr(self.manager.scenes['Game'], 'logic'))

    def test_main_menu_supports_keyboard_navigation(self):
        menu = self.manager.current_scene
        menu.update(0.016, [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)])
        self.assertEqual(menu.selected_idx, 1)

    def test_load_selection_keeps_visible_window_in_sync(self):
        menu = self.manager.current_scene
        menu.save_slots = [{'filename': f'save_{i}'} for i in range(8)]
        menu.selected_idx = 6
        menu._keep_selected_save_visible()
        self.assertEqual(menu.load_offset, 2)

    def test_class_cards_fit_768p_viewport(self):
        self.manager.change_scene('ClassSelect')
        scene = self.manager.current_scene
        for card in scene.cards:
            self.assertGreaterEqual(card.rect.left, 0)
            self.assertLessEqual(card.rect.right, scene.width)
            self.assertGreaterEqual(card.rect.top, 0)
            self.assertLessEqual(card.rect.bottom, scene.height - 75)

    def test_inventory_controls_fit_768p_viewport(self):
        scene = self.manager.scenes['Game']
        scene.init_ui_components()
        controls = [
            scene.orb_toggle_rect,
            scene.inv_prev_rect,
            scene.inv_next_rect,
            *scene.mass_sell_rects,
        ]
        for rect in controls:
            self.assertGreaterEqual(rect.left, 0)
            self.assertLessEqual(rect.right, scene.width)
            self.assertLessEqual(rect.bottom, scene.height)

    def test_market_orbs_have_unlimited_stock(self):
        class FakePlayer:
            def __init__(self):
                self.gold = 1000
                self.x = 0
                self.y = 0
                self.items = []

            def add_item(self, item):
                self.items.append(item)
                return True

        logic = GameLogic.__new__(GameLogic)
        player = FakePlayer()
        logic.players = {0: player}
        logic.local_player_id = 0
        logic.market_inventory = []
        logic.orb_market = [{"name": "Test Orbu", "type": "orb", "orb_id": "test", "price": 100}]
        logic.events = []
        # buy_item -> track_quest zinciri; sahte görev/kayıt bağımlılıkları
        # olmadan "Quest tracking error" basıyordu. Disk okuma/yazma yok:
        # meta bellekte tutulur, oyuncunun gerçek meta.json'ı bozulmaz.
        logic.width, logic.height = 1366, 768
        logic._meta_cache = {}
        logic._meta_dirty = False
        logic.save_manager = SimpleNamespace(load_meta=lambda: {},
                                             save_meta=lambda meta: None)
        logic.quest_system = SimpleNamespace(track=lambda event_type, value, meta: 0,
                                             save_to_meta=lambda meta: meta)

        self.assertTrue(logic.buy_item(0, "orbs"))
        self.assertTrue(logic.buy_item(0, "orbs"))
        self.assertEqual(len(logic.orb_market), 1)
        self.assertEqual(len(player.items), 2)
        self.assertEqual(player.gold, 800)

    def test_live_stats_panel_toggles_with_c(self):
        self.manager.change_scene('ClassSelect')
        self.manager.current_scene.selected_class = 'warrior'
        self.manager.change_scene('Game')
        scene = self.manager.current_scene

        scene.update(0, [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c)])

        self.assertTrue(scene.show_stats_panel)

    def test_zoom_render_surface_is_reused(self):
        self.manager.change_scene('ClassSelect')
        self.manager.current_scene.selected_class = 'warrior'
        self.manager.change_scene('Game')
        scene = self.manager.current_scene
        scene.zoom_level = scene.target_zoom = scene.min_zoom

        scene.draw()
        first_surface = scene._world_surface
        scene.draw()

        self.assertIs(scene._world_surface, first_surface)
        self.assertGreaterEqual(scene.min_zoom, 0.70)

    def test_spatial_grid_only_returns_nearby_enemies(self):
        logic = GameLogic.__new__(GameLogic)
        logic.grid_size = 128
        near = SimpleNamespace(id=1, x=100, y=100, dead=False)
        far = SimpleNamespace(id=2, x=1000, y=1000, dead=False)
        logic.enemies = [near, far]
        logic.update_grid()

        found = list(logic.iter_enemies_near(100, 100, 100))

        self.assertIn(near, found)
        self.assertNotIn(far, found)

    def test_projectile_pool_tracks_only_active_objects(self):
        pool = ProjectilePool(size=10)
        projectile = pool.spawn(0, 0, 1, 0, damage=1)
        self.assertEqual(len(pool.active_objects), 1)

        projectile.active = False
        pool.update(0, None)

        self.assertEqual(pool.active_objects, [])


if __name__ == '__main__':
    unittest.main()
