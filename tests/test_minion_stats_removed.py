"""Live replacement stats and repeat-safe migration of obsolete pet defenses."""
import copy
from types import SimpleNamespace
import pytest
from logic.minion_stats import OBSOLETE, migrate_item, migrate_player
from logic.item_system import ItemSystem
from logic.skill_tree import SkillTree
from logic.ascendancy import Ascendancy
from tests.test_combat_regressions import combat

def test_new_content_never_grants_obsolete_minion_stats():
    for node in list(SkillTree.NODES) + list(Ascendancy.NODES):
        assert not OBSOLETE.intersection(node.get('stats', {}))
    for item in ItemSystem.bases:
        assert not OBSOLETE.intersection(item.get('itemBase', {}))
    for affix in ItemSystem.affixes['pet_suffixes']:
        assert affix['stat'] not in OBSOLETE

def test_legacy_affixes_preserve_slots_tiers_and_are_idempotent():
    item = {'itemBase': {'minionMaxHp': 7, 'minionRange': .6},
            'prefixes': [], 'suffixes': [
                {'stat':'minionMaxHp', 'val':.4, 'tier':1, 'name':'Minyon Canı'},
                {'stat':'minionArmor', 'val':30, 'tier':1, 'name':'Minyon Zırhı'}]}
    migrate_item(item)
    assert item['itemBase']['minionRange'] == pytest.approx(.9)
    assert [a['stat'] for a in item['suffixes']] == ['minionRange','minionCrit']
    assert item['suffixes'][1]['val'] == pytest.approx(.06)
    assert all(a['tier']==1 for a in item['suffixes'])
    before = copy.deepcopy(item)
    migrate_item(item)
    assert item == before

def test_old_fedai_keeps_spent_levels(combat):
    p, _, _ = combat('beastmaster')
    p.skills = [{'stat':'minionMaxHp', 'val':80, 'lvl':3, 'max':10, 'name':'Fedai'}]
    p.inv_manager.recalculate_stats()
    assert p.skills[0]['lvl'] == 3
    assert p.skills[0]['stat'] == 'minionRange'
    assert p.stats['minionRange'] >= 1.24
    assert not OBSOLETE.intersection(p.stats)
    before = dict(p.stats)
    p.inv_manager.recalculate_stats()
    assert p.stats == before

def test_immortal_minions_ignore_legacy_life_and_armor(combat):
    from entities.minion import Minion
    p, _, g = combat('beastmaster')
    p.stats.update(minionMaxHp=999, minionMaxHpFlat=999, minionArmor=999)
    pet = Minion(9, p.x, p.y, owner=p)
    pet.take_damage(99999, g)
    assert pet.hp == pet.max_hp == 1
    assert not pet.dead and not pet.is_recharging

def test_shadow_clone_expires_instead_of_recharging_forever(combat):
    from entities.minion import Minion
    p, _, g = combat()
    pet = Minion(9, p.x, p.y, m_type='shadow_clone', owner=p)
    pet.update(10.1, g)
    assert pet.dead
