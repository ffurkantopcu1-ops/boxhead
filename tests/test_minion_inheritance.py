"""Actual pet attacks: tamer-only item transfer and all inherited combat rules."""
import copy
from unittest.mock import patch
import pytest
from entities.minion import Minion
from entities.enemy import Enemy
from logic.minion_inheritance import combat_stats, EXCLUDED, WEAPON_STATS
from logic.card_system import CardSystem
from tests.test_combat_regressions import combat

def shot(player, enemy, game, kind='wolf'):
    pet = Minion(91, 0, 0, m_type=kind, owner=player)
    pet.target = enemy
    before = len(game.projectiles)
    with patch('entities.minion.random.random', return_value=1):
        pet.attack(game)
    return pet, game.projectiles[before:]

@pytest.mark.parametrize('flag', ['isMinion', 'isCommander'])
@pytest.mark.parametrize('stat', ['physDmg', 'physDmgFlat', 'fireDamage','fireDmgFlat',
                                'frostDamage','frostDmgFlat','poisonDps'])
def test_only_tamer_weapon_transfers_flat_damage(combat, flag, stat):
    p, e, g = combat('beastmaster')
    p.inv_manager.equipped['weapon'] = {'name':'Terbiyeci Sopası', flag:True,
                                      'itemBase':{}, 'prefixes':[{'stat':stat,'val':17}], 'suffixes':[]}
    p.inv_manager.recalculate_stats()
    target = WEAPON_STATS[stat]
    assert p.stats[target] >= 17
    assert p.stats.get(stat, 0) == 0
    _, shots = shot(p, e, g)
    s = shots[0]
    if stat.startswith('fire'): assert s.fire_dmg > 0
    elif stat.startswith('frost'): assert s.frost_dmg > 0
    elif stat == 'poisonDps': assert s.poison_dps > 0
    else: assert s.dmg > 17
    p.inv_manager.equipped['weapon'][flag] = False
    p.inv_manager.recalculate_stats()
    assert p.stats.get(target, 0) == 0

@pytest.mark.parametrize('flag', ['isMinion','isCommander'])
def test_tamer_projectiles_pierce_and_bounce_are_not_double_counted(combat, flag):
    p,e,g = combat('beastmaster')
    p.inv_manager.equipped['weapon'] = {'name':'Sopa',flag:True,
        'itemBase':{'projectileCount':2,'pierce':2,'bounce':3},'prefixes':[],'suffixes':[]}
    p.inv_manager.recalculate_stats()
    for card in (False,True):
        p.has_minion_inheritance = card
        _,shots=shot(p,e,g)
        assert len(shots)==3
        assert all(s.pierce==2 and s.bounce==3 for s in shots)


def test_tree_pierce_is_player_only_until_card(combat):
    p,e,g=combat('beastmaster')
    p.stats['pierce']=3
    _,shots=shot(p,e,g)
    assert shots[0].pierce==0
    p.has_minion_inheritance=True
    _,shots=shot(p,e,g)
    assert shots[0].pierce==3

@pytest.mark.parametrize('source,target', list(WEAPON_STATS.items()))
def test_every_declared_combat_stat_is_inherited_once(combat, source, target):
    p,e,g=combat('beastmaster')
    p.has_minion_inheritance=True
    before=combat_stats(p).get(target,0)
    if source=='attack_speed_mult':
        # This legacy alias is normalized before the snapshot.
        p.skills_permanent[source]=.2
        p.inv_manager.recalculate_stats()
        assert p.stats.get('attack_speed_bonus',0)>=.2
        return
    p.stats[source]=p.stats.get(source,0)+.2
    assert combat_stats(p)[target] == pytest.approx(before+.2)
    assert combat_stats(p)[target] == pytest.approx(before+.2)

@pytest.mark.parametrize('stat', sorted(EXCLUDED))
def test_defense_and_recovery_not_inherited(combat,stat):
    p,e,g=combat('beastmaster')
    p.has_minion_inheritance=True
    p.stats[stat]=99999
    inherited=combat_stats(p)
    assert stat not in inherited
    assert inherited.get('minionPhysDmgFlat',0)==0

@pytest.mark.parametrize('kind', ['wolf','dragon'])
def test_frost_bonus_deals_actual_frost_damage(combat,kind):
    p,e,g=combat('beastmaster')
    p.stats['minionFrostDmgFlat']=20
    _,shots=shot(p,e,g,kind)
    s=shots[0]
    e.armor=100000
    before=e.hp
    s.on_hit(e,g)
    assert before-e.hp >= s.frost_dmg


def test_poison_conversion_applies_to_every_pet_packet(combat):
    p,e,g=combat('beastmaster')
    p.has_minion_inheritance=True
    p.poison_convert=True
    p.stats.update(fireDamage=20, frostDmgFlat=10)
    _,shots=shot(p,e,g)
    before=e.hp
    shots[0].on_hit(e,g)
    assert e.hp == before
    assert any(effect.name=='CardConversionPoison' for effect in e.effect_manager.effects)
    assert not any(effect.name=='Burn' for effect in e.effect_manager.effects)
    e.effect_manager.update(1,e,g)
    assert e.hp < before


def test_pure_fire_rule_does_not_disable_pet_primary_attack(combat):
    p,e,g=combat('beastmaster')
    p.has_minion_inheritance=True
    p.stats.update(treeFireOnly=1,fireDmgMult=2,poisonDps=50,frostDmgFlat=50)
    _,shots=shot(p,e,g)
    s=shots[0]
    assert s.damage_type=='fire' and s.dmg>0
    assert s.poison_dps==s.frost_dmg==0
    before=e.hp
    s.on_hit(e,g)
    assert e.hp<before


def test_aoe_card_hits_nearby_target(combat):
    p,e,g=combat('beastmaster')
    p.has_minion_inheritance=True
    p.stats['aoe']=2
    nearby=Enemy(92,e.x+20,e.y,g)
    nearby.hp=nearby.max_hp=10000
    g.enemies.append(nearby)
    _,shots=shot(p,e,g)
    before=nearby.hp
    shots[0].on_hit(e,g)
    assert nearby.hp<before


def test_element_percent_does_not_boost_physical_pet_damage(combat):
    p,e,g=combat('beastmaster')
    p.has_minion_inheritance=True
    _,shots=shot(p,e,g)
    base=shots[0].dmg
    p.stats.update(fireDmgMult=2,frostDmgMult=2,elementDmgMult=2)
    _,shots=shot(p,e,g)
    assert shots[0].dmg==pytest.approx(base)


def test_conditional_and_temporary_buffs_apply_at_attack_time(combat):
    p,e,g=combat('beastmaster')
    p.has_minion_inheritance=True
    _,shots=shot(p,e,g)
    base=shots[0].dmg
    p._adrenaline_timer=5
    p._berserker_active=True
    _,shots=shot(p,e,g)
    assert shots[0].dmg==pytest.approx(base*1.2*1.8)
    p._adrenaline_timer=0
    p._berserker_active=False
    _,shots=shot(p,e,g)
    assert shots[0].dmg==pytest.approx(base)


def test_card_state_survives_reload_without_duplicate_stats(combat,tmp_path,monkeypatch):
    from logic.game_logic import GameLogic
    from logic.save_manager import SaveManager
    monkeypatch.setattr(SaveManager,'SAVE_DIR',str(tmp_path))
    g=GameLogic(None,1024,768,'beastmaster')
    p=g.players[g.local_player_id]
    assert g.card_system.apply_card('pack_soul',p)
    before=copy.deepcopy(p.skills_permanent)
    SaveManager.save_game(g,'pack')
    dst=GameLogic(None,1024,768,'beastmaster')
    SaveManager.load_game(dst,'pack')
    q=dst.players[dst.local_player_id]
    assert q.has_minion_inheritance
    assert q.skills_permanent==before
    assert dst.card_system.active_cards.count('pack_soul')==1


@pytest.mark.parametrize('stat', ['static_field','starfallAura','decayAura'])
def test_personal_damage_auras_follow_minions_with_card(combat,stat):
    from unittest.mock import Mock
    p,e,g=combat('beastmaster')
    p.has_minion_inheritance=True
    p.stats[stat]=5
    pet=Minion(91,0,0,owner=p)
    pet.offset_x=pet.offset_y=0
    pet.attack=Mock()
    before=e.hp
    pet.update(1.01,g)
    assert e.hp<before


def test_shockwave_is_emitted_once_per_minion_attack(combat):
    p,e,g=combat('beastmaster')
    p.has_minion_inheritance=True
    p.stats.update(shockwave=20,projectileCount=3)
    before=e.hp
    pet,shots=shot(p,e,g)
    assert len(shots)==3
    assert before-e.hp==pytest.approx(20)


def test_inherited_speed_attack_speed_cooldown_and_range_are_live(combat):
    p,e,g=combat('beastmaster')
    p.has_minion_inheritance=True
    before=combat_stats(p)
    p.stats.update(speed=p.stats['speed']*1.5, fireRate=.5, cooldownReduction=.25,
                   range=80,meleeRangeMult=.2)
    after=combat_stats(p)
    assert after['minionMoveMult']>before['minionMoveMult']
    assert after['minionRate']==pytest.approx(before['minionRate']+.5)
    assert after['minionCooldownMult']==.75
    assert after['minionExtraRange']==80
    assert after['minionRange']==pytest.approx(p.stats['minionRange']*1.2)
    pet=Minion(91,0,0,owner=p)
    pet.offset_x=pet.offset_y=0
    pet.update(.01,g)
    assert pet.attack_cooldown==pytest.approx(pet.base_cd/after['minionRate'])
    assert pet.range==pytest.approx(pet.base_range*after['minionRange']+80)


def test_armor_penetration_and_boss_damage_apply_to_pet_hit(combat):
    p,e,g=combat('beastmaster')
    p.has_minion_inheritance=True
    p.stats.update(armorPen=1,bossDmgMult=.5,brutal=.2)
    e.armor=10000
    e.type='boss'
    _,shots=shot(p,e,g)
    before=e.hp
    shots[0].on_hit(e,g)
    assert before-e.hp==pytest.approx(shots[0].dmg*1.5*1.2)


def test_status_duration_and_dot_damage_affect_pet_poison(combat):
    p,e,g=combat('beastmaster')
    p.has_minion_inheritance=True
    p.stats.update(poisonDps=10,dotDmgMult=.5,statusDuration=.25)
    _,shots=shot(p,e,g)
    shots[0].on_hit(e,g)
    poison=next(x for x in e.effect_manager.effects if x.name=='Poison')
    assert poison.dps==pytest.approx(shots[0].poison_dps*1.5)
    assert poison.duration==pytest.approx(5*1.25)


def test_crit_chance_and_crit_damage_affect_pet_hit(combat):
    p,e,g=combat('beastmaster')
    p.has_minion_inheritance=True
    p.stats.update(critChance=1,critDmg=1)
    pet=Minion(91,0,0,owner=p)
    pet.target=e
    with patch('entities.minion.random.random',return_value=0):
        pet.attack(g)
    s=g.projectiles[-1]
    assert s.is_crit
    assert s.hit_crit_mult==3


@pytest.mark.parametrize('source',['tree','item','skill','aura','card','temporary'])
def test_every_source_reaches_actual_pet_attack(combat,source):
    p,e,g=combat('beastmaster')
    p.has_minion_inheritance=True
    _,before=shot(p,e,g)
    base=before[0].dmg
    if source=='tree':
        from logic.skill_tree import SkillTree
        node=next(n for n in SkillTree.NODES if n['stats'].get('dmgMult',0)>0 and n['type']=='minor')
        p.allocated_nodes.add(node['id'])
    elif source=='item':
        p.inv_manager.equipped['armor']={'name':'Test','itemBase':{'dmgMult':.5},'prefixes':[],'suffixes':[]}
    elif source=='skill':
        p.skills.append({'stat':'dmgMult','val':.5,'lvl':1,'max':1})
    elif source=='aura':
        p.active_auras.append('berserker')
    elif source=='card':
        CardSystem().apply_card('chaos_theory',p)
    else:
        p.temp_buffs['dmgMult']=2
    p.inv_manager.recalculate_stats()
    _,after=shot(p,e,g)
    assert after[0].dmg>base


def test_only_card_inherits_nontamer_weapon_damage(combat):
    p,e,g=combat('beastmaster')
    p.inv_manager.equipped['weapon']={'name':'Kılıç','itemBase':{'fireDamage':20},'prefixes':[],'suffixes':[]}
    p.inv_manager.recalculate_stats()
    _,shots=shot(p,e,g)
    assert shots[0].fire_dmg==0
    p.has_minion_inheritance=True
    _,shots=shot(p,e,g)
    assert shots[0].fire_dmg>0


def test_impossible_penalty_is_applied_once_to_pet_hit(combat):
    p,e,g=combat('beastmaster')
    _,shots=shot(p,e,g)
    before=e.hp
    shots[0].on_hit(e,g)
    normal=before-e.hp
    g.wave['current_diff']='Impossible'
    _,shots=shot(p,e,g)
    before=e.hp
    shots[0].on_hit(e,g)
    assert before-e.hp==pytest.approx(normal*.5)


def test_half_poison_conversion_conserves_pet_hit(combat):
    p,e,g=combat('beastmaster')
    p.has_minion_inheritance=True
    p.stats['treePoisonConversion']=.5
    _,shots=shot(p,e,g)
    s=shots[0]
    before=e.hp
    s.on_hit(e,g)
    immediate=before-e.hp
    timed=sum(effect.dps*effect.duration for effect in e.effect_manager.effects if effect.name=='ConversionPoison')
    assert immediate==pytest.approx(s.dmg*.5)
    assert timed==pytest.approx(s.dmg*.5)


def test_sets_reach_elemental_pet_attack(combat):
    p,e,g=combat('beastmaster')
    p.has_minion_inheritance=True
    p.skills_permanent['fireDamage']=10
    p.inv_manager.recalculate_stats()
    _,shots=shot(p,e,g)
    base=shots[0].fire_dmg
    for slot in ('armor','helmet','gloves'):
        p.inv_manager.equipped[slot]={'name':'Set','setTag':'SET_FIRE','itemBase':{},'prefixes':[],'suffixes':[]}
    p.inv_manager.recalculate_stats()
    _,shots=shot(p,e,g)
    assert shots[0].fire_dmg>base


def test_ascendancy_bonus_updates_existing_pet(combat):
    from logic.ascendancy import Ascendancy
    p,e,g=combat('beastmaster')
    p.has_minion_inheritance=True
    _,shots=shot(p,e,g)
    base=shots[0].dmg
    node=next(n for n in Ascendancy.NODES if n['subclass']=='beastmaster_hunter' and n['stats'].get('minionDamage',0)>0)
    p.ascendancy_nodes.add(node['id'])
    p.inv_manager.recalculate_stats()
    _,shots=shot(p,e,g)
    assert shots[0].dmg>base
