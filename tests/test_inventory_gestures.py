"""Inventory ownership and deliberate workshop actions survive UI gestures."""
import copy
from types import SimpleNamespace
from unittest.mock import patch
import pygame
import pytest
from logic.save_manager import SaveManager
from scenes.game_scene import GameScene
import ui_workshop
from logic.crafting import apply_recipe, recipes, recipe_cost


@pytest.fixture
def scene(tmp_path):
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    with patch.object(SaveManager, 'SAVE_DIR', str(tmp_path)):
        sc = GameScene(SimpleNamespace(global_settings={}), screen, 1280, 720)
        sc.selected_class = 'sniper'
        sc.on_enter()
    sc.show_inventory = True
    sc.active_tab = 'inventory'
    sc.hide_orbs = False
    sc._apply_inventory_layout()
    return sc


def move(scene, item, source, pos):
    scene._item_drag = dict(item=item, source=source, start=(0, 0), pos=pos, moved=True)
    ui_workshop.finish_drag(scene, scene.logic.players['p1'], pos)


def test_equip_equal_items_uses_identity_and_keeps_old_weapon(scene):
    p = scene.logic.players['p1']
    old = p.inv_manager.equipped['weapon']
    first = copy.deepcopy(old)
    second = copy.deepcopy(first)
    p.inventory[:] = [first, second]
    move(scene, second, None, scene.equip_rows[0].rect.center)
    assert p.inv_manager.equipped['weapon'] is second
    assert any(it is first for it in p.inventory)
    assert any(it is old for it in p.inventory)
    assert not any(it is second for it in p.inventory)


def test_wrong_slot_and_outside_drop_do_not_change_ownership(scene):
    p = scene.logic.players['p1']
    item = copy.deepcopy(p.inv_manager.equipped['weapon'])
    p.inventory[:] = [item]
    move(scene, item, None, scene.equip_rows[1].rect.center)
    move(scene, item, None, (0, 0))
    assert p.inventory == [item]
    assert p.inv_manager.equipped['helmet'] is None


def test_equipped_item_can_be_crafted_without_copy_or_removal(scene):
    p = scene.logic.players['p1']
    item = p.inv_manager.equipped['weapon']
    move(scene, item, 'weapon', scene.craft_drop_rect.center)
    assert scene.crafting_target is item
    assert scene.show_craft_window
    assert p.inv_manager.equipped['weapon'] is item
    assert not any(it is item for it in p.inventory)


def test_drag_equipment_to_bag_unequips_once(scene):
    p = scene.logic.players['p1']
    item = p.inv_manager.equipped['weapon']
    move(scene, item, 'weapon', scene.bag_drop_rect.center)
    assert p.inv_manager.equipped['weapon'] is None
    assert sum(it is item for it in p.inventory) == 1


def test_selecting_orb_does_not_spend_it_apply_does(scene):
    p = scene.logic.players['p1']
    orb = next(x.copy() for x in scene.logic.item_system.orbs if x['orb_id'] == 'tier')
    orb['stack'] = 2
    p.inventory.append(orb)
    item = p.inv_manager.equipped['weapon']
    scene.crafting_target = item
    scene.show_craft_window = True
    scene.draw_craft_window()
    scene._handle_inventory_mouse(p, scene.craft_orb_use_rects[0][1].center)
    assert orb['stack'] == 2
    assert item['rarity'] == 'Normal'
    scene._handle_inventory_mouse(p, scene._craft_layout()['apply'].center)
    assert orb['stack'] == 1
    assert item['rarity'] == 'Magic'


def test_failed_craft_does_not_consume_orb(scene):
    p = scene.logic.players['p1']
    orb = next(x.copy() for x in scene.logic.item_system.orbs if x['orb_id'] == 'scour')
    p.inventory.append(orb)
    scene.show_craft_window = True
    scene.crafting_target = p.inv_manager.equipped['weapon']
    scene._selected_craft_orb = orb
    scene._handle_inventory_mouse(p, scene._craft_layout()['apply'].center)
    assert any(it is orb for it in p.inventory)
    assert scene.craft_error_msg


def test_inventory_geometry_keeps_cards_above_footer(scene):
    for w, h in ((1280, 720), (1600, 1000)):
        scene.width, scene.height = w, h
        scene._apply_inventory_layout()
        panel = scene._inventory_panel_rect()
        for card in scene.bp_cards:
            assert panel.contains(card.rect)
            assert card.rect.bottom < scene.mass_sell_rects[0].top
            assert card.rect.contains(card.craft_rect)
        for row in scene.equip_rows:
            assert row.rect.bottom < scene.craft_drop_rect.top - 22


def test_mouse_events_drag_instead_of_activating_card_buttons(scene):
    p = scene.logic.players['p1']
    item = copy.deepcopy(p.inv_manager.equipped['weapon'])
    p.inventory[:] = [item]
    start = scene.bp_cards[0].slot_rect.center
    end = scene.equip_rows[0].rect.center
    scene.update(0, [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=start),
                     pygame.event.Event(pygame.MOUSEMOTION, pos=end, rel=(0,0), buttons=(1,0,0)),
                     pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=end)])
    assert p.inv_manager.equipped['weapon'] is item
    assert getattr(scene, '_item_drag', None) is None


def test_directed_recipe_promotes_normal_and_preserves_natural_rolls(scene):
    p = scene.logic.players['p1']
    p.gold = 100
    item = p.inv_manager.equipped['weapon']
    assert apply_recipe(p, item, 'prefixes:dmgMult', 1) is None
    assert p.gold == 50
    assert item['rarity'] == 'Magic'
    natural = dict(stat='critChance', val=.03, tier=3, name='Kritik', label='S')
    item['suffixes'].append(natural)
    assert apply_recipe(p, item, 'prefixes:fireDamage', 1) is None
    assert item['suffixes'] == [natural]
    assert len(item['prefixes']) == 1
    assert item['prefixes'][0]['stat'] == 'fireDamage'
    assert item['prefixes'][0]['crafted']


def test_failed_recipe_has_no_cost_or_partial_mutation(scene):
    p = scene.logic.players['p1']
    p.gold = 49
    item = p.inv_manager.equipped['weapon']
    before = copy.deepcopy(item)
    assert apply_recipe(p,item,'prefixes:dmgMult',1)
    assert item == before and p.gold == 49
    p.gold = 100
    item['is_corrupted'] = True
    before = copy.deepcopy(item)
    assert apply_recipe(p,item,'prefixes:dmgMult',1)
    assert item == before and p.gold == 100


def test_recipe_cannot_overwrite_natural_modifier_or_use_detached_item(scene):
    p = scene.logic.players['p1']
    p.gold = 1000
    item = p.inv_manager.equipped['weapon']
    item['rarity'] = 'Rare'
    item['prefixes'] = [dict(stat='dmgMult',val=.35,tier=1,name='Hasar')]
    before = copy.deepcopy(item)
    assert apply_recipe(p,item,'prefixes:dmgMult',1)
    assert apply_recipe(p,copy.deepcopy(item),'prefixes:fireDamage',1)
    assert item == before and p.gold == 1000


@pytest.mark.parametrize('wave,tier,cost',[(1,3,50),(10,2,300),(20,1,1200)])
def test_recipe_progression_has_explicit_tiers_and_prices(scene,wave,tier,cost):
    p = scene.logic.players['p1']
    p.gold = 2000
    item = p.inv_manager.equipped['weapon']
    assert recipe_cost(wave) == cost
    assert apply_recipe(p,item,'prefixes:dmgMult',wave) is None
    assert item['prefixes'][0]['tier'] == tier
    assert p.gold == 2000-cost


def test_crafted_marker_survives_real_save_load(scene,tmp_path):
    p=scene.logic.players['p1']
    p.gold=100
    item=p.inv_manager.equipped['weapon']
    assert apply_recipe(p,item,'prefixes:dmgMult',1) is None
    with patch.object(SaveManager,'SAVE_DIR',str(tmp_path)):
        SaveManager.save_game(scene.logic,'recipe_roundtrip')
        assert SaveManager.load_game(scene.logic,'recipe_roundtrip')
    restored=p.inv_manager.equipped['weapon']
    assert restored['prefixes'][0]['crafted']
    assert p.gold==50
    assert apply_recipe(p,restored,'prefixes:fireDamage',1) is None
    assert len(restored['prefixes'])==1


def test_keyboard_navigation_and_view_sort_leave_inventory_unchanged(scene):
    p=scene.logic.players['p1']
    items=[dict(name='Z',type='weapon',rarity='Normal'),dict(name='A',type='weapon',rarity='Rare')]
    p.inventory[:]=items
    scene.inv_sort_mode='rarity'
    assert scene._filtered_inventory(p)[0] is items[1]
    assert p.inventory[0] is items[0]
    scene.update(0,[pygame.event.Event(pygame.KEYDOWN,key=pygame.K_5,unicode='5')])
    assert scene.active_tab=='market'


def test_unlocked_ascendancy_and_aura_draw_with_shared_art(scene):
    from logic.ascendancy import Ascendancy
    p=scene.logic.players['p1']
    p.evolution=next(iter(Ascendancy.START_BY_SUBCLASS))
    p.ascendancy_points=4
    scene.draw_ascendancy_tab(p)
    assert scene.ascendancy_node_hit
    p.is_essence_system_unlocked=True
    scene.draw_aura_tab(p)
    assert len(scene.aura_btn_rects)==4
    assert all(rect.bottom < scene.aura_next_rect.top for _,rect in scene.aura_btn_rects)


def test_dropdown_filters_search_and_clear_share_the_visible_inventory(scene):
    import ui_gothic_tabs
    p=scene.logic.players['p1']
    sword=dict(name='Alev Kılıcı',type='weapon',rarity='Rare')
    helm=dict(name='Miğfer',type='helmet',rarity='Normal')
    p.inventory[:]=[sword,helm]
    scene.draw_inventory_tab(p)
    assert ui_gothic_tabs.filter_click(scene,scene.inv_combo_rects[0].center)
    ui_gothic_tabs.filters(scene,popup=True)
    value,rect=next((v,r) for v,r in scene._filter_options if v=='Rare')
    assert not ui_workshop.start_drag(scene,p,rect.center)
    assert ui_gothic_tabs.filter_click(scene,rect.center)
    assert scene._filtered_inventory(p)==[sword]
    scene._inv_query='alev'
    assert scene._filtered_inventory(p)==[sword]
    scene._inv_query='bulunmayan'
    assert scene._filtered_inventory(p)==[]
    assert ui_gothic_tabs.filter_click(scene,scene.inv_clear_rect.center)
    assert scene._filtered_inventory(p)==[sword,helm]
