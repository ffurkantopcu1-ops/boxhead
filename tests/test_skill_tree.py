import unittest

from logic.skill_tree import SkillTree
from logic.inventory_manager import InventoryManager


class _StubPlayer:
    """recalculate_stats'i tetiklemeden motoru test etmek icin minik oyuncu.
    inv_manager yok -> SkillTree._sync_player sessizce gecer (Pygame gerekmez)."""

    def __init__(self, class_id="warrior", skill_points=0):
        self.class_id = class_id
        self.base_class_id = class_id
        self.skill_points = skill_points
        self.allocated_nodes = set(SkillTree.start_nodes_for(class_id))


def _first_step(start="start_warrior"):
    """Baslangicin baslangic-olmayan ilk komsusu (ilk tahsis adimi)."""
    return next(t for t in SkillTree.ADJ[start] if not SkillTree.is_start(t))


class TestData(unittest.TestCase):
    def test_all_playable_classes_have_a_start(self):
        for c in InventoryManager.CLASS_IDS:
            self.assertIn(c, SkillTree.START_BY_CLASS, f"{c} icin baslangic yok")
            self.assertIn(SkillTree.START_BY_CLASS[c], SkillTree.BY_ID)

    def test_unknown_class_uses_fallback(self):
        self.assertEqual(SkillTree.start_nodes_for("nonexistent_class"),
                         [SkillTree.ARMLESS_FALLBACK])

    def test_connections_are_symmetric(self):
        for nid, neighbors in SkillTree.ADJ.items():
            for neigh in neighbors:
                self.assertIn(nid, SkillTree.ADJ[neigh],
                              f"{nid}<->{neigh} simetrik degil")

    def test_graph_is_huge(self):
        # "Büyük" ağaç: bol düğüm = varyasyon
        self.assertGreaterEqual(len(SkillTree.NODES), 150)

    def test_keystones_carry_a_downside(self):
        for n in SkillTree.NODES:
            if n.get("type") == "keystone":
                stats = n.get("stats", {})
                self.assertTrue(any(v < 0 for v in stats.values()),
                                f"{n['id']} keystone bedelsiz")

    def test_every_start_reaches_a_core_node(self):
        for cls, sid in SkillTree.START_BY_CLASS.items():
            self.assertTrue(
                any(SkillTree.BY_ID[t]["arm"] == "core" for t in SkillTree.ADJ[sid]),
                f"{sid} hicbir cekirdek dugumune baglanmiyor")


class TestPathing(unittest.TestCase):
    def test_start_is_not_a_free_root(self):
        self.assertFalse(SkillTree.is_allocatable("start_warrior", set()))

    def test_non_start_needs_a_neighbor(self):
        step = _first_step()
        self.assertFalse(SkillTree.is_allocatable(step, set()))
        self.assertTrue(SkillTree.is_allocatable(step, {"start_warrior"}))

    def test_foreign_class_start_locked(self):
        self.assertFalse(SkillTree.is_allocatable("start_ninja", {"start_warrior"}))

    def test_already_allocated_not_allocatable(self):
        self.assertFalse(SkillTree.is_allocatable("start_warrior", {"start_warrior"}))


class TestAllocation(unittest.TestCase):
    def test_allocate_spends_one_point(self):
        p = _StubPlayer("warrior", skill_points=2)
        ok, _ = SkillTree.allocate(p, _first_step())
        self.assertTrue(ok)
        self.assertEqual(p.skill_points, 1)

    def test_allocate_blocked_without_points(self):
        p = _StubPlayer("warrior", skill_points=0)
        ok, _ = SkillTree.allocate(p, _first_step())
        self.assertFalse(ok)

    def test_allocate_blocked_without_path(self):
        p = _StubPlayer("warrior", skill_points=5)
        deep = next(n["id"] for n in SkillTree.NODES
                    if n["type"] == "keystone" and n["arm"] == "warrior")
        self.assertFalse(SkillTree.allocate(p, deep)[0])

    def test_refund_returns_points_and_reseeds_start(self):
        p = _StubPlayer("warrior", skill_points=3)
        s1 = _first_step()
        SkillTree.allocate(p, s1)
        s2 = next(t for t in SkillTree.ADJ[s1]
                  if t not in p.allocated_nodes and not SkillTree.is_start(t))
        SkillTree.allocate(p, s2)
        self.assertEqual(p.skill_points, 1)
        refunded = SkillTree.refund_all(p)
        self.assertEqual(refunded, 2)
        self.assertEqual(p.skill_points, 3)
        self.assertEqual(p.allocated_nodes, {"start_warrior"})


class TestStatResolution(unittest.TestCase):
    def test_resolve_sums_stats(self):
        ids = [n["id"] for n in SkillTree.NODES
               if n["arm"] == "warrior" and n.get("stats")][:4]
        expected = {}
        for nid in ids:
            for k, v in SkillTree.BY_ID[nid]["stats"].items():
                expected[k] = expected.get(k, 0) + v
        got = SkillTree.resolve_stats(set(ids))
        for k, v in expected.items():
            self.assertAlmostEqual(got[k], v)

    def test_start_contributes_nothing(self):
        self.assertEqual(SkillTree.resolve_stats({"start_warrior"}), {})


if __name__ == "__main__":
    unittest.main()
