"""Exercise the real startup and scene rendering without a fullscreen window."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch


def run(native=False):
    import pygame
    from scene_manager import SceneManager
    from logic.save_manager import SaveManager
    import scene_manager
    import audio
    pygame.init()
    screen = scene_manager.create_display("windowed" if native else "borderless",1920,1080)
    with tempfile.TemporaryDirectory(prefix='boxhead-smoke-') as directory, \
            patch.object(SaveManager,'SAVE_DIR',directory), \
            patch.object(scene_manager,'SETTINGS_PATH',str(Path(directory)/'settings.json')):
        audio.init(0)
        manager = SceneManager(screen,1920,1080)
        import gc
        for _ in range(240):
            pygame.event.pump()
            manager.update(1/60,[])
            manager.draw()
            gc.collect()
            pygame.display.flip()
        manager.change_scene('ClassSelect')
        manager.draw()
        manager.start_new_game('sniper')
        for _ in range(5):
            manager.update(1/60,[])
            manager.draw()
        scene=manager.current_scene
        scene.show_inventory=True
        for tab in ('inventory','hero','skills','ascendancy','market','aura','synergy'):
            scene.active_tab=tab
            scene.draw_inventory()
        scene.crafting_target=scene.logic.players['p1'].inv_manager.equipped['weapon']
        scene.show_craft_window=True
        scene.draw_craft_window()
    pygame.quit()
    result={'ok':True,'startup':'menu, class selection, game, seven tabs, workshop'}
    Path('smoke_result.json').write_text(json.dumps(result),encoding='utf-8')
    return result
