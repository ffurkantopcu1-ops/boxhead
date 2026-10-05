import copy
import pytest
from tests.test_inventory_gestures import scene
from logic import orb_crafting as oc
from logic.crafting import apply_advanced
from logic.save_manager import SaveManager
import ui_workshop

def setup(scene, orb_id):
    p=scene.logic.players['p1']
    item=p.inv_manager.equipped['weapon']
    item.update(rarity='Rare',ilvl=1,prefixes=[],suffixes=[])
    orb=next(copy.deepcopy(o) for o in scene.logic.item_system.orbs if o['orb_id']==orb_id)
    orb['stack']=2;p.inventory.append(orb)
    p.craft_essences={k:2 for k in oc.FAMILIES}
    return p,item,orb

def aff(stat,**flags):
    return dict(stat=stat,val=.1,tier=3,name=stat,**flags)

@pytest.mark.parametrize('family',['fire','frost','poison','weapon'])
def test_focus_spends_once_and_respects_family_level(scene,family):
    p,item,orb=setup(scene,'p_add')
    item['suffixes']=[aff('critChance')];old=copy.deepcopy(item['suffixes'])
    assert oc.apply(p,item,orb,'prefixes',family) is None
    assert item['prefixes'][0]['stat'] in oc.FAMILIES[family][1]
    assert item['prefixes'][0]['tier']==3
    assert item['suffixes']==old and orb['stack']==1 and p.craft_essences[family]==1

def test_random_add_has_no_essence_cost(scene):
    p,item,orb=setup(scene,'aug');stock=copy.deepcopy(p.craft_essences)
    assert oc.apply(p,item,orb,'prefixes') is None
    assert p.craft_essences==stock

def test_transform_only_selected_modifier(scene):
    p,item,orb=setup(scene,'transmute')
    item['prefixes']=[aff('dmgMult'),aff('armorPen')];item['suffixes']=[aff('critChance')]
    old=copy.deepcopy(item)
    assert oc.apply(p,item,orb,'prefixes','poison','dmgMult') is None
    assert item['prefixes'][0]['stat']=='dotDmgMult'
    assert item['prefixes'][1]==old['prefixes'][1] and item['suffixes']==old['suffixes']
    assert orb['stack']==1 and p.craft_essences['poison']==1

@pytest.mark.parametrize('flag',['crafted','fractured','special','no_essence','corrupt','detached','wrong_family'])
def test_invalid_transform_is_atomic(scene,flag):
    p,item,orb=setup(scene,'transmute');item['prefixes']=[aff('dmgMult')]
    family='poison'
    if flag in ('crafted','fractured'):item['prefixes'][0][flag]=True
    if flag=='special':item['prefixes'][0]['tier']=0
    if flag=='no_essence':p.craft_essences['poison']=0
    if flag=='corrupt':item['is_corrupted']=True
    if flag=='detached':item=copy.deepcopy(item)
    if flag=='wrong_family':family='invalid'
    before=copy.deepcopy(item);stock=copy.deepcopy(p.craft_essences)
    assert oc.apply(p,item,orb,'prefixes',family,'dmgMult')
    assert item==before and p.craft_essences==stock and orb['stack']==2

@pytest.mark.parametrize('protected',['crafted','fractured'])
def test_side_chaos_preserves_opposite_and_protected(scene,protected):
    p,item,orb=setup(scene,'side_chaos')
    item['prefixes']=[aff('dmgMult',**{protected:True}),aff('armorPen')]
    item['suffixes']=[aff('critChance')];old=copy.deepcopy(item);stock=copy.deepcopy(p.craft_essences)
    assert oc.apply(p,item,orb,'prefixes') is None
    assert item['prefixes'][0]==old['prefixes'][0] and item['suffixes']==old['suffixes']
    assert len(item['prefixes'])==2 and item['prefixes'][1]['tier']==3
    stats=[a['stat'] for side in oc.SIDES for a in item[side]]
    assert len(stats)==len(set(stats)) and p.craft_essences==stock and orb['stack']==1

def test_salvage_yields_one_chosen_family_and_excludes_crafted(scene):
    p,item,orb=setup(scene,'aug')
    item['prefixes']=[aff('fireDamage'),aff('elementDmgMult')]
    item['suffixes']=[aff('poisonDps',crafted=True)]
    assert 'poison' not in oc.salvage_families(item)
    assert apply_advanced(p,item,'salvage:fire')
    p.inv_manager.equipped['weapon']=None;p.inventory.append(item)
    assert apply_advanced(p,item,'salvage:fire') is None
    assert p.craft_essences['fire']==3 and p.craft_essences['frost']==2

def test_essences_survive_save(scene,tmp_path,monkeypatch):
    p,item,orb=setup(scene,'aug')
    p.craft_essences={'poison':7,'fire':1}
    monkeypatch.setattr(SaveManager,'SAVE_DIR',str(tmp_path))
    SaveManager.save_game(scene.logic,'essence')
    p.craft_essences={};SaveManager.load_game(scene.logic,'essence')
    assert scene.logic.players['p1'].craft_essences=={'poison':7,'fire':1}

def test_visible_family_selection_and_apply_spends_once(scene):
    p,item,orb=setup(scene,'p_add')
    scene.crafting_target=item;scene.show_craft_window=True;scene._selected_craft_orb=orb
    scene.draw_craft_window()
    rect=next(r for action,value,r in scene.craft_config_rects if action=='family' and value=='fire')
    scene._handle_inventory_mouse(p,rect.center);scene.draw_craft_window()
    scene._handle_inventory_mouse(p,scene._craft_layout()['apply'].center)
    assert orb['stack']==1 and p.craft_essences['fire']==1
    assert item['prefixes'][0]['stat'] in oc.FAMILIES['fire'][1]

def test_legacy_orb_names_and_icons_refresh_without_changing_stack(scene,tmp_path,monkeypatch):
    p,item,orb=setup(scene,'p_scour')
    orb.update(name='Prefix Silme Orbu',icon_id='orb_chaos',stack=19)
    monkeypatch.setattr(SaveManager,'SAVE_DIR',str(tmp_path))
    SaveManager.save_game(scene.logic,'old-orbs')
    SaveManager.load_game(scene.logic,'old-orbs')
    loaded=next(x for x in scene.logic.players['p1'].inventory if x.get('orb_id')=='p_scour')
    assert loaded['name']=='Unutuş Küresi' and loaded['icon_id']=='orb_p_scour'
    assert loaded['stack']==19

def test_every_orb_has_a_distinct_loadable_icon(scene):
    from ui_elements import ImageLoader
    orbs=scene.logic.item_system.orbs
    assert len({o['icon_id'] for o in orbs})==len(orbs)
    for orb in orbs:
        icon=ImageLoader.get_item_icon(orb['icon_id'],(40,40))
        assert icon is not None,orb['orb_id']
        assert icon.get_size()==(40,40)
