# -*- coding: utf-8 -*-
"""Denge sistemleri testleri: SOFT_CAPS, poison yığın tavanı, DoT yönlendirme,
essence tavanları, stat alias'ları ve additive sınıf dmgMult.

Pygame penceresi açmadan çalışır (SDL_VIDEODRIVER=dummy).
"""
import os
import sys
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.inventory_manager import InventoryManager
from logic.status_effects import StatusEffect, StatusEffectManager


class FakePlayer:
    """recalculate_stats'ın dokunduğu alanları taşıyan hafif oyuncu."""

    def __init__(self, class_id="warrior"):
        self.class_id = class_id
        self.essence_stats = {}
        self.skills = []
        self.skills_permanent = {}
        self.active_auras = []
        self.inventory = []
        self.stats = {}
        self.game = None
        self.hp = 100
        self.max_hp = 100
        self.energy_shield = 0
        self.max_energy_shield = 0

    # Player.ESSENCE_CAPS ile aynı sözleşme
    ESSENCE_CAPS = {"max_hp": 200, "phys_dmg": 60, "element_dmg": 0.60, "armor": 60, "speed": 1.5}


def make_manager(player):
    mgr = InventoryManager(player)
    player.inv_manager = mgr
    return mgr


class TestSoftCaps(unittest.TestCase):
    def test_dodge_hard_capped_below_100_percent(self):
        p = FakePlayer("ninja")
        mgr = make_manager(p)
        p.skills_permanent = {"dodgeChance": 1.50}  # eski broken build toplamı
        mgr.recalculate_stats()
        self.assertLessEqual(p.stats["dodgeChance"], 0.60)

    def test_critdmg_hard_capped(self):
        p = FakePlayer("sniper")
        mgr = make_manager(p)
        p.skills_permanent = {"critDmg": 8.1}
        mgr.recalculate_stats()
        self.assertLessEqual(p.stats["critDmg"], 4.0)

    def test_lifesteal_hard_capped(self):
        p = FakePlayer("bloodwalker")
        mgr = make_manager(p)
        p.skills_permanent = {"lifesteal": 1.60}  # + sınıf 0.20 = 1.80 ham
        mgr.recalculate_stats()
        self.assertLessEqual(p.stats["lifesteal"], 0.50)

    def test_dot_mult_capped(self):
        p = FakePlayer("alchemist")
        mgr = make_manager(p)
        p.skills_permanent = {"dotDmgMult": 4.55}  # + sınıf 0.3 = 4.85 ham
        mgr.recalculate_stats()
        self.assertLessEqual(p.stats["dotDmgMult"], 2.0)

    def test_class_dmg_mult_is_additive(self):
        p = FakePlayer("sniper")  # sınıf dmgMult 0.5
        mgr = make_manager(p)
        p.skills_permanent = {"dmgMult": 0.5}
        mgr.recalculate_stats()
        # additive: 1.0 + 0.5 + 0.5 = 2.0 (DR knee'de); çarpımsal olsaydı 2.25 olurdu
        self.assertAlmostEqual(p.stats["dmgMult"], 2.0, places=5)

    def test_essence_capped_in_recalc(self):
        p = FakePlayer("warrior")
        mgr = make_manager(p)
        p.essence_stats = {"armor": 999}
        mgr.recalculate_stats()
        self.assertLessEqual(p.stats["armor"], 60)

    def test_maxhp_alias_from_item(self):
        p = FakePlayer("engineer")
        mgr = make_manager(p)
        mgr.equipped["chest"] = {
            "name": "Test Zırhı", "type": "chest",
            "itemBase": {"maxHp": 300}, "prefixes": [], "suffixes": [],
        }
        mgr.recalculate_stats()
        self.assertGreaterEqual(p.max_hp, 300)  # 100 taban + 300 eşya

    def test_minion_bases_are_zero(self):
        p = FakePlayer("warrior")
        mgr = make_manager(p)
        mgr.recalculate_stats()
        self.assertEqual(p.stats["minionCount"], 0)
        self.assertEqual(p.stats["minionDamage"], 0.0)


class FakeEnemy:
    type = "barrel"

    def __init__(self):
        self.hp = 1000
        self.x = 0
        self.y = 0
        self.dot_calls = []

    def take_damage(self, amount, game, is_crit=False, is_dot=False, from_player=False):
        self.dot_calls.append((amount, is_dot))
        self.hp -= amount


class FakeGame:
    def add_event(self, *a, **k):
        pass


class TestStatusEffects(unittest.TestCase):
    def test_poison_stack_capped_at_4x(self):
        mgr = StatusEffectManager()
        for _ in range(8):
            mgr.add_effect(StatusEffect("Poison", 5.0, dps=100))
        poison = next(e for e in mgr.effects if e.name == "Poison")
        self.assertLessEqual(poison.dps, 400)

    def test_dot_routed_through_take_damage(self):
        enemy = FakeEnemy()
        eff = StatusEffect("Poison", 5.0, dps=100)
        eff.update(0.1, enemy, FakeGame())
        self.assertTrue(enemy.dot_calls, "DoT take_damage üzerinden akmalı")
        self.assertTrue(all(is_dot for _, is_dot in enemy.dot_calls))


if __name__ == "__main__":
    unittest.main()
