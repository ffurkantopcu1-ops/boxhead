# -*- coding: utf-8 -*-
"""Ascendancy (alt-sınıf) motoru testleri. Pygame penceresi açmadan çalışır."""
import os
import sys
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.ascendancy import Ascendancy


class _P:
    """inv_manager'sız minik oyuncu (recalc tetiklenmez)."""

    def __init__(self, evo, points=0):
        self.evolution = evo
        self.ascendancy_points = points
        self.ascendancy_nodes = set()
        start = Ascendancy.start_for(evo)
        if start:
            self.ascendancy_nodes.add(start)


class TestData(unittest.TestCase):
    def test_18_subclasses_each_one_start(self):
        self.assertEqual(len(Ascendancy.START_BY_SUBCLASS), 18)

    def test_connections_symmetric(self):
        for nid, neighbors in Ascendancy.ADJ.items():
            for m in neighbors:
                self.assertIn(nid, Ascendancy.ADJ[m])

    def test_every_evolution_has_a_tree(self):
        import pygame
        pygame.init()
        from entities.player import Player
        for evo in Player.EVOLUTIONS:
            self.assertIn(evo, Ascendancy.START_BY_SUBCLASS,
                          f"{evo} için ascendancy ağacı yok")


class TestUnlockAndAllocation(unittest.TestCase):
    def test_unlocked_only_when_evolved(self):
        self.assertTrue(Ascendancy.is_unlocked(_P("ninja_shadow")))
        self.assertFalse(Ascendancy.is_unlocked(_P("")))

    def test_allocate_spends_ascendancy_point(self):
        p = _P("ninja_shadow", points=3)
        ok, _ = Ascendancy.allocate(p, "ninja_shadow_a1")
        self.assertTrue(ok)
        self.assertEqual(p.ascendancy_points, 2)

    def test_no_points_blocks(self):
        self.assertFalse(Ascendancy.allocate(_P("ninja_shadow", 0), "ninja_shadow_a1")[0])

    def test_foreign_subclass_blocked(self):
        p = _P("ninja_shadow", 5)
        self.assertFalse(Ascendancy.allocate(p, "warrior_gladiator_a1")[0])

    def test_capstone_needs_path(self):
        # a4 (capstone) yalnız a3'ten sonra alınabilir
        self.assertFalse(Ascendancy.allocate(_P("ninja_shadow", 5), "ninja_shadow_a4")[0])

    def test_refund_returns_points_keeps_start(self):
        p = _P("ninja_shadow", 3)
        Ascendancy.allocate(p, "ninja_shadow_a1")
        Ascendancy.allocate(p, "ninja_shadow_a2")
        self.assertEqual(p.ascendancy_points, 1)
        refunded = Ascendancy.refund_all(p)
        self.assertEqual(refunded, 2)
        self.assertEqual(p.ascendancy_points, 3)
        self.assertEqual(p.ascendancy_nodes, {"ninja_shadow_a0"})


class TestStats(unittest.TestCase):
    def test_resolve_sums(self):
        stats = Ascendancy.resolve_stats({"ninja_shadow_a1", "ninja_shadow_a2"})
        self.assertAlmostEqual(stats.get("critChance", 0), 0.10)
        self.assertAlmostEqual(stats.get("critDmg", 0), 0.6)

    def test_start_contributes_nothing(self):
        self.assertEqual(Ascendancy.resolve_stats({"ninja_shadow_a0"}), {})


if __name__ == "__main__":
    unittest.main()
