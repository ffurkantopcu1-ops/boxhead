# -*- coding: utf-8 -*-
"""Silah 'savaş ailesi' kuralı: aynı aileden silah sınıfı DEĞİŞTİRMEZ, farklı
aileden silah değiştirir (bkz. InventoryManager.WEAPON_FAMILIES).

Pygame penceresi açmadan çalışır."""
import os
import sys
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.inventory_manager import InventoryManager


class FakePlayer:
    ESSENCE_CAPS = {}

    def __init__(self, class_id):
        self.class_id = class_id
        self.base_class_id = class_id
        self.essence_stats = {}
        self.skills = []
        self.skills_permanent = {}
        self.active_auras = []
        self.allocated_nodes = set()
        self.inventory = []
        self.stats = {}
        self.game = None
        self.hp = 100
        self.max_hp = 100
        self.energy_shield = 0
        self.max_energy_shield = 0

    def reinit_specialization(self):
        pass


def resulting_class(base, weapon_class, **flags):
    p = FakePlayer(base)
    m = InventoryManager(p)
    p.inv_manager = m
    weapon = {"type": "weapon", "weaponClass": weapon_class,
              "itemBase": {}, "prefixes": [], "suffixes": []}
    weapon.update(flags)
    m.equipped["weapon"] = weapon
    m.recalculate_stats()
    return p.class_id


class TestWeaponFamily(unittest.TestCase):
    def test_same_family_keeps_class(self):
        # Kullanıcı hatası: ninja bir vampir/kan kılıcı takınca ninja KALMALI
        self.assertEqual(resulting_class("ninja", "bloodwalker"), "ninja")
        self.assertEqual(resulting_class("warrior", "ninja"), "warrior")
        self.assertEqual(resulting_class("bloodwalker", "warrior"), "bloodwalker")
        self.assertEqual(resulting_class("sorcerer", "sniper"), "sorcerer")
        self.assertEqual(resulting_class("bomber", "alchemist"), "bomber")

    def test_cross_family_swaps_class(self):
        # Farklı savaş ailesi: o silahın mekaniği ancak kendi sınıfıyla çalışır
        self.assertEqual(resulting_class("ninja", "sniper"), "sniper")
        self.assertEqual(resulting_class("warrior", "engineer"), "engineer")
        self.assertEqual(resulting_class("beastmaster", "warrior"), "warrior")

    def test_classless_weapon_keeps_base(self):
        self.assertEqual(resulting_class("ninja", "general"), "ninja")
        self.assertEqual(resulting_class("bomber", "none"), "bomber")

    def test_lifesteal_from_offclass_weapon_applies(self):
        # Ninja, kan kılıcının can çalma statını sınıf değiştirmeden alır
        p = FakePlayer("ninja")
        m = InventoryManager(p)
        p.inv_manager = m
        m.equipped["weapon"] = {
            "type": "weapon", "weaponClass": "bloodwalker", "isMelee": True,
            "itemBase": {"physDmg": 14, "lifesteal": 0.15},
            "prefixes": [], "suffixes": [],
        }
        m.recalculate_stats()
        self.assertEqual(p.class_id, "ninja")
        self.assertAlmostEqual(p.stats.get("lifesteal", 0), 0.15, places=3)


if __name__ == "__main__":
    unittest.main()
