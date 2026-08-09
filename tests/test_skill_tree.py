import unittest

from logic.skill_tree import SkillTree
from logic.inventory_manager import InventoryManager


class _StubPlayer:
    """recalculate_stats'i tetiklemeden motoru test etmek icin minik oyuncu.

    inv_manager yok -> SkillTree._sync_player sessizce gecer; boylece bu testler
    Pygame/display'e ihtiyac duymaz.
    """

    def __init__(self, class_id="warrior", skill_points=0):
        self.class_id = class_id
        self.skill_points = skill_points
        self.allocated_nodes = set(SkillTree.start_nodes_for(class_id))


class TestData(unittest.TestCase):
    def test_every_playable_class_has_a_start_or_fallback(self):
        for class_id in InventoryManager.CLASS_IDS:
            starts = SkillTree.start_nodes_for(class_id)
            self.assertTrue(starts, f"{class_id} icin baslangic dugumu yok")
            for nid in starts:
                self.assertIn(nid, SkillTree.BY_ID)

    def test_all_playable_classes_have_a_dedicated_arm(self):
        # Artik bomber dahil tum oynanabilir siniflarin kendi baslangici var.
        for class_id in InventoryManager.CLASS_IDS:
            self.assertIn(class_id, SkillTree.START_BY_CLASS,
                          f"{class_id} icin kendi baslangic dugumu yok")

    def test_unknown_class_uses_fallback(self):
        # Tanimsiz bir sinif cekirdek fallback'ine dusmeli (kilitlenmesin).
        self.assertEqual(SkillTree.start_nodes_for("nonexistent_class"),
                         [SkillTree.ARMLESS_FALLBACK])

    def test_connections_are_symmetric(self):
        for nid, neighbors in SkillTree.ADJ.items():
            for neigh in neighbors:
                self.assertIn(nid, SkillTree.ADJ[neigh],
                              f"{nid}<->{neigh} kenari simetrik degil")

    def test_keystones_carry_a_downside(self):
        # Her keystone bir bedel tasimali (AGENTS.md guc butcesi kurali).
        for n in SkillTree.NODES:
            if n.get("type") != "keystone":
                continue
            stats = n.get("stats", {})
            has_downside = stats.get("max_hp_pct", 0) < 0 or any(
                v < 0 for v in stats.values())
            self.assertTrue(has_downside, f"{n['id']} keystone bedelsiz")


class TestPathing(unittest.TestCase):
    def test_start_is_not_a_free_root(self):
        # Baslangic dugumu tiklamayla alinamaz; kosu basinda tohumlanir.
        self.assertFalse(SkillTree.is_allocatable("start_warrior", set()))

    def test_foreign_class_start_locked_until_core_walk(self):
        # Savasci baslangiciyla ninja baslangici HEMEN acilmamali.
        self.assertFalse(SkillTree.is_allocatable("start_ninja", {"start_warrior"}))

    def test_non_start_needs_a_neighbor(self):
        self.assertFalse(SkillTree.is_allocatable("w_hide", set()))
        self.assertTrue(SkillTree.is_allocatable("w_hide", {"start_warrior"}))

    def test_already_allocated_is_not_allocatable(self):
        self.assertFalse(SkillTree.is_allocatable("start_warrior", {"start_warrior"}))

    def test_core_reachable_from_arm_via_gate(self):
        # start_warrior -> core_gate_armor -> core_heart yolu var mi
        alloc = {"start_warrior"}
        self.assertTrue(SkillTree.is_allocatable("core_gate_armor", alloc))
        alloc.add("core_gate_armor")
        self.assertTrue(SkillTree.is_allocatable("core_heart", alloc))


class TestAllocation(unittest.TestCase):
    def test_allocate_spends_one_point(self):
        p = _StubPlayer("warrior", skill_points=2)
        ok, _ = SkillTree.allocate(p, "w_hide")
        self.assertTrue(ok)
        self.assertEqual(p.skill_points, 1)
        self.assertIn("w_hide", p.allocated_nodes)

    def test_allocate_blocked_without_points(self):
        p = _StubPlayer("warrior", skill_points=0)
        ok, msg = SkillTree.allocate(p, "w_hide")
        self.assertFalse(ok)
        self.assertEqual(p.skill_points, 0)

    def test_allocate_blocked_without_path(self):
        p = _StubPlayer("warrior", skill_points=5)
        ok, _ = SkillTree.allocate(p, "w_berserk")  # derin dugum, komsu yok
        self.assertFalse(ok)

    def test_refund_returns_points_and_reseeds_start(self):
        p = _StubPlayer("warrior", skill_points=3)
        SkillTree.allocate(p, "w_hide")
        SkillTree.allocate(p, "w_vigor")
        self.assertEqual(p.skill_points, 1)
        refunded = SkillTree.refund_all(p)
        self.assertEqual(refunded, 2)
        self.assertEqual(p.skill_points, 3)
        self.assertEqual(p.allocated_nodes, {"start_warrior"})


class TestStatResolution(unittest.TestCase):
    def test_resolve_sums_stats(self):
        alloc = {"start_warrior", "w_hide", "w_vigor", "core_gate_armor"}
        stats = SkillTree.resolve_stats(alloc)
        # w_hide armor 10 + core_gate_armor armor 8 = 18; w_vigor max_hp 50
        self.assertEqual(stats["armor"], 18)
        self.assertEqual(stats["max_hp"], 50)

    def test_start_contributes_nothing(self):
        self.assertEqual(SkillTree.resolve_stats({"start_warrior"}), {})


if __name__ == "__main__":
    unittest.main()
