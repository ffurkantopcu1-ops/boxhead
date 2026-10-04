"""Offscreen QA for every inventory tab, temporary saves only."""
import os,sys,tempfile,copy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from scenes.game_scene import GameScene
from logic.save_manager import SaveManager
from logic.item_system import ItemSystem

def render(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);pygame.init()
 for w,h in ((1280,720),(1600,1000)):
  screen=pygame.display.set_mode((w,h))
  with tempfile.TemporaryDirectory() as tmp,patch.object(SaveManager,'SAVE_DIR',tmp):
   m=SimpleNamespace(global_settings={})
   sc=GameScene(m,screen,w,h);sc.selected_class='sniper';sc.on_enter()
   p=sc.logic.players['p1'];p.gold=10000
   for base in ItemSystem.bases[:12]:
    it=copy.deepcopy(base);it.update(rarity='Rare',prefixes=[],suffixes=[],price=2000)
    sc.logic.item_system.apply_affixes(it);p.inventory.append(it)
   for orb in ItemSystem.orbs:
    it=orb.copy();it['stack']=3;p.inventory.append(it)
   sc.show_inventory=True
   for tab in ('inventory','hero','skills','ascendancy','market','aura','synergy'):
    sc.active_tab=tab;screen.fill((0,0,0));sc.draw_inventory()
    pygame.image.save(screen,str(out/f'{tab}_{w}.png'))
   sc.active_tab='inventory';sc._filter_open=0;sc.draw_inventory();pygame.image.save(screen,str(out/f'filter_open_{w}.png'));sc._filter_open=None
   p.is_essence_system_unlocked=True
   sc.active_tab='aura';sc.draw_inventory();pygame.image.save(screen,str(out/f'aura_unlocked_{w}.png'))
   from logic.ascendancy import Ascendancy
   p.evolution=next(iter(Ascendancy.START_BY_SUBCLASS));p.level=25;p.ascendancy_points=5
   sc.active_tab='ascendancy';sc.draw_inventory();pygame.image.save(screen,str(out/f'ascendancy_unlocked_{w}.png'))
   sc.logic.card_system.active_cards=sc.logic.card_system.synergy_system.SYNERGIES[0]['required_cards'][:1]
   sc.active_tab='synergy';sc.draw_inventory();pygame.image.save(screen,str(out/f'synergy_progress_{w}.png'))
   sc.active_tab='inventory';sc.draw_inventory()
   item=p.inventory[0];sc.crafting_target=item;sc.show_craft_window=True
   sc._selected_craft_orb=next(x for x in p.inventory if x.get('orb_id')=='p_add')
   sc.draw_craft_window();pygame.image.save(screen,str(out/f'craft_{w}.png'))
   sc._craft_recipe_mode=True
   from logic.crafting import recipes
   sc._selected_recipe=recipes(item)[0]
   sc.draw_craft_window();pygame.image.save(screen,str(out/f'craft_recipe_{w}.png'))
   sc._craft_advanced_mode=True
   from logic.crafting import advanced_recipes
   sc._selected_recipe=advanced_recipes(item,p)[0];p.craft_dust=20
   sc.draw_craft_window();pygame.image.save(screen,str(out/f'craft_advanced_{w}.png'))
   sc.show_craft_window=False;sc.draw_inventory()
   sc._item_drag={'item':item,'source':None,'start':(0,0),'pos':sc.equip_rows[0].rect.center,'moved':True}
   from ui_workshop import draw_drag
   draw_drag(sc);pygame.image.save(screen,str(out/f'drag_{w}.png'))
 pygame.quit()
if __name__=='__main__':render(sys.argv[1])
