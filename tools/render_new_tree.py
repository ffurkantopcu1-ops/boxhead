"""Actual scene renderer, temporary saves, overview/focus/long tooltip QA."""
import os, sys, tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from scenes.game_scene import GameScene
from logic.save_manager import SaveManager
from logic.skill_tree import SkillTree
from tools.inspect_new_tree import path_to


def render(out):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    pygame.init()
    for w,h in ((1600,1000),(1280,720)):
        screen=pygame.display.set_mode((w,h))
        manager=SimpleNamespace(global_settings={})
        with tempfile.TemporaryDirectory() as tmp, patch.object(SaveManager,'SAVE_DIR',tmp):
            scene=GameScene(manager,screen,w,h)
            manager.current_scene=scene
            scene.selected_class='sniper'; scene.on_enter()
            p=scene.logic.players['p1']; p.skill_points=30
            start='start_sniper'
            for n in path_to(start,'sniper_chain_notable')[1:]:
                assert SkillTree.allocate(p,n)[0]
            scene._tree_fullscreen=True
            scene.draw_skills_tab(p)
            pygame.image.save(screen,str(out/f'agac_genel_{w}.png'))
            scene._tree_handle_key(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_HOME,unicode=''))
            scene.draw_skills_tab(p)
            pygame.image.save(screen,str(out/f'agac_sniper_{w}.png'))
            scene._draw_tree_tooltip(SkillTree.BY_ID['central_flame'],(w-50,h-40),p.allocated_nodes,set())
            pygame.image.save(screen,str(out/f'agac_tooltip_{w}.png'))
    pygame.quit()


if __name__=='__main__': render(sys.argv[1])
