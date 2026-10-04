"""Feedback represents actual item changes, never an anticipated result."""
import copy
from logic.craft_feedback import changes


def test_added_removed_and_changed_values_are_separate():
    before={'prefixes':[{'stat':'armor','val':5,'tier':3},{'stat':'speed','val':1,'tier':3}]}
    after={'prefixes':[{'stat':'armor','val':10,'tier':2},{'stat':'max_hp','val':20,'tier':3}]}
    snapshot=copy.deepcopy((before,after))
    result={c['stat']:c for c in changes(before,after)}
    assert result['armor']['kind']=='changed'
    assert result['armor']['before']['val']==5 and result['armor']['after']['val']==10
    assert result['speed']['kind']=='removed'
    assert result['max_hp']['kind']=='added'
    assert (before,after)==snapshot


def test_side_tier_and_sealing_changes_are_reported():
    before={'rarity':'Normal','prefixes':[{'stat':'armor','val':10,'tier':3}]}
    after={'rarity':'Magic','is_corrupted':True,'prefixes':[{'stat':'armor','val':10,'tier':2}]}
    assert {c['stat'] for c in changes(before,after)}=={'armor','rarity','is_corrupted'}


def test_no_change_does_not_invent_a_successful_roll():
    item={'prefixes':[{'stat':'armor','val':10,'tier':3}],'suffixes':[]}
    assert changes(item,copy.deepcopy(item))==[]


def test_fixed_modifier_and_base_roll_changes_are_visible():
    before={'itemBase':{'physDmg':10},'suffixes':[{'stat':'armor','val':10,'tier':3}]}
    after={'itemBase':{'physDmg':15},'suffixes':[{'stat':'armor','val':10,'tier':3,'fractured':True}]}
    result=changes(before,after)
    assert {(c['side'],c['stat']) for c in result}=={('base','physDmg'),('suffixes','armor')}


def test_cosmetic_name_changes_are_not_reported_as_stat_changes():
    before={'prefixes':[{'stat':'armor','val':10,'tier':3,'name':'Eski'}]}
    after={'prefixes':[{'stat':'armor','val':10,'tier':3,'name':'Yeni'}]}
    assert changes(before,after)==[]
