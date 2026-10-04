"""New topology, capped progression, real oath consumers and save migration."""
import json
from types import SimpleNamespace
import pytest
from logic.skill_tree import SkillTree
from logic.progression import earned_main_points, xp_threshold
from logic.save_manager import SaveManager
from tools.inspect_new_tree import distances, path_to
from tools.generate_skill_tree import generate
from tests.test_combat_regressions import combat
from tests.test_wave_events_removed import game


def test_generator_matches_json_and_size():
    assert generate() == SkillTree.NODES
    assert 700 <= len(SkillTree.NODES) <= 900


@pytest.mark.parametrize('cls', list(SkillTree.START_BY_CLASS))
def test_early_clear_and_defense_notables_arrive_at_four_points(cls):
    costs,_=distances('start_'+cls)
    near=[n for n in SkillTree.NODES if n['arm']==cls and n['type']=='notable' and costs[n['id']]<=4]
    assert len(near)>=3
    assert any(set(n['stats']) & {'armor','max_hp','max_hp_pct','maxEnergyShield',
                                 'minionArmor','minionMaxHp','turretMaxHp','dodgeChance'} for n in near)
    assert min(costs[n['id']] for n in near)==4
    assert all(costs[n['id']]>=3 for n in SkillTree.NODES if n['type']=='notable')


@pytest.mark.parametrize('cls', list(SkillTree.START_BY_CLASS))
def test_center_is_deep_and_second_center_requires_fresh_investment(cls):
    start='start_'+cls
    costs,_=distances(start)
    centers=[n for n in SkillTree.BY_ID if n.startswith('central_')]
    assert len(centers)==12
    assert 15<=min(costs[n] for n in centers)<=20
    for first in centers:
        assert len(SkillTree.ADJ[first])==1
        paid=path_to(start,first)
        marginal,_=distances(start,paid)
        assert min(marginal[n] for n in centers if n!=first)>=15


def test_sniper_can_invest_into_every_foreign_region_within_budget():
    costs,_=distances('start_sniper')
    assert len(costs)==len(SkillTree.NODES)
    for cls in SkillTree.START_BY_CLASS:
        assert min(costs[n['id']] for n in SkillTree.NODES if n['arm']==cls and n['type']=='notable')<100


def test_level_rewards_cap_at_one_hundred_and_keep_ascendancy(game):
    p=game.players['p1']
    for _ in range(65): p.grant_free_level()
    assert p.skill_points==p.main_points_earned==100
    assert p.ascendancy_points==47
    assert p.xp_to_next_level==xp_threshold(p.level)
    assert earned_main_points(51)==100


def test_version_migration_round_trip_does_not_mint_roots_or_points(game):
    p=game.players['p1']
    p.level=6; p.skill_points=3
    SaveManager.save_game(game,'old')
    filename=__import__('pathlib').Path(SaveManager.SAVE_DIR)/'old.json'
    data=json.loads(filename.read_text())
    data['player'].pop('skill_tree_version')
    data['player'].pop('main_points_earned')
    data['player']['allocated_nodes']=['start_warrior','core_fallback','warrior_main_1','warrior_main_2']
    filename.write_text(json.dumps(data))
    SaveManager.load_game(game,'old')
    assert p.allocated_nodes=={'start_warrior'}
    assert p.skill_points==10
    SaveManager.save_game(game,'new')
    SaveManager.load_game(game,'new')
    SaveManager.save_game(game,'new')
    SaveManager.load_game(game,'new')
    assert p.skill_points==10


def test_conversion_delays_half_damage_and_never_reconverts(combat):
    p,e,g=combat()
    p.stats['treePoisonConversion']=.5
    before=e.hp
    e.take_damage(100,g,from_player=True)
    assert before-e.hp==50
    effects=[eff for eff in e.effect_manager.effects if eff.name=='ConversionPoison']
    assert len(effects)==1 and effects[0].dps==12.5
    e.effect_manager.update(4,g.enemies[0],g)
    assert before-e.hp==pytest.approx(100)
    assert not e.effect_manager.effects


def test_fire_only_removes_nonfire_and_boosts_existing_fire(combat):
    p,e,g=combat('sniper')
    p.allocated_nodes.add('central_flame')
    p.inv_manager.recalculate_stats()
    assert p.stats['fireDmgMult']>=2
    before=e.hp
    e.take_damage(100,g,from_player=True)
    e.apply_dot('poison',100,5)
    e.apply_dot('frost',100,5)
    assert e.hp==before and not e.effect_manager.effects
    e.take_damage(100,g,from_player=True,damage_type='fire')
    assert before-e.hp==100
    SkillTree.refund_all(p)
    assert not p.stats.get('treeFireOnly')
    e.take_damage(100,g,from_player=True)
    assert before-e.hp==200


@pytest.mark.parametrize('key,check',[
    ('single',lambda s:s['projectileCount']==1 and s['pierce']==s['bounce']==0),
    ('certainty',lambda s:s['critChance']==s['minionCrit']==0),
    ('giant',lambda s:s['aoe']>=2 and s['attack_cooldown']>350),
    ('horizon',lambda s:s['meleeRangeMult']>=1.8),
    ('army',lambda s:s['minionCount']>=2 and s['turretLimit']>=3),
    ('overdrive',lambda s:s['minionRate']>=1.6 and s['turretRate']>=1.6),
    ('vampire',lambda s:s['lifesteal']>=.2 and s['regen']==s['combatRegen']==0),
    ('astral',lambda s:s['maxEnergyShield']>=180 and s['max_hp']<100),
    ('wind',lambda s:s['armor']==0 and s['dodgeChance']>=.15),
    ('fortress',lambda s:s['armor']>=90 and s['dodgeChance']==0),
])
def test_oath_rules_are_recalculated_and_refundable(combat,key,check):
    p,e,g=combat()
    p.allocated_nodes.add('central_'+key)
    p.inv_manager.recalculate_stats()
    assert check(p.stats)
    SkillTree.refund_all(p)
    assert all(not k.startswith('tree') or not v for k,v in p.stats.items())


def test_single_shot_doubles_actual_direct_damage(combat):
    p,e,g=combat('sniper')
    p.stats['treeSingleShot']=1
    before=e.hp
    e.take_damage(100,g,from_player=True)
    assert before-e.hp==200


def test_kamikaze_contact_is_suppressed_during_warning(combat):
    p,e,g=combat()
    e.type='kamikaze'; e.explode_timer=.5
    before=p.hp
    e.update_contact(2,p,True)
    assert p.hp==before
