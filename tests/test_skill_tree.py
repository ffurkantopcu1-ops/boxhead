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


class TestTreeShape(unittest.TestCase):
    """Yeniden tasarlanan çark ağacının sözleşmesi (bkz. SKILL_TREE.md).

    Eski ağacın somut kusurlarını regresyon olarak kilitler: güçlü düğümlerin
    ucuza sıralanması, sınıflar arası bedava geçiş, kategorisiz düğümler.
    """

    CLASSES = ["warrior", "sniper", "engineer", "beastmaster", "bomber",
               "alchemist", "sorcerer", "bloodwalker", "ninja"]

    @staticmethod
    def _cost_map(start_id):
        """Başlangıçtan her düğüme en ucuz yol (SP = düğüm sayısı)."""
        import collections
        dist = {start_id: 0}
        q = collections.deque([start_id])
        while q:
            cur = q.popleft()
            for nb in SkillTree.ADJ[cur]:
                if nb not in dist:
                    dist[nb] = dist[cur] + 1
                    q.append(nb)
        return dist

    def test_all_nodes_reachable_from_every_class(self):
        total = len(SkillTree.BY_ID)
        for c in self.CLASSES:
            self.assertEqual(len(self._cost_map(f"start_{c}")), total,
                             f"{c} başlangıcından erişilemeyen düğüm var")

    def test_keystone_is_a_real_commitment(self):
        # Eskiden dış halkaya varan biri keystone'ları sırayla alıyordu.
        for c in self.CLASSES:
            cost = self._cost_map(f"start_{c}")[f"{c}_keystone"]
            self.assertGreaterEqual(cost, 12, f"{c} keystone'u çok ucuz ({cost} SP)")

    def test_notables_are_not_chainable(self):
        # Aynı sınıfın iki notable'ı arasında en az 2 SP olmalı; 1 SP olsaydı
        # hepsi tek tek sıralanabilirdi (eski ağacın asıl sorunu).
        for c in self.CLASSES:
            nots = [n["id"] for n in SkillTree.NODES
                    if n["type"] == "notable" and n["arm"] == c]
            self.assertGreater(len(nots), 1)
            for a in nots:
                d = self._cost_map(a)
                nearest = min(d[b] for b in nots if b != a)
                self.assertGreaterEqual(
                    nearest, 2, f"{c}: {a} -> komşu notable yalnızca {nearest} SP")

    def test_foreign_keystone_costs_more_than_own(self):
        for c in self.CLASSES:
            d = self._cost_map(f"start_{c}")
            own = d[f"{c}_keystone"]
            for o in self.CLASSES:
                if o != c:
                    self.assertGreater(d[f"{o}_keystone"], own,
                                       f"{c} için {o} keystone'u kendi keystone'undan ucuz")

    # Renk tablosunun anahtarları (scenes/game_scene.py -> TREE_CAT_COLORS).
    # Burada elle yazılı: testin pygame ekranı açmasına gerek kalmasın.
    VALID_CATS = {"damage", "element", "dot", "minion", "turret", "defense",
                  "utility", "core"}

    def test_every_node_has_a_category(self):
        # Kategori = düğüm rengi (ve ileride ikon). Eksikse düğüm nötr çizilir.
        for n in SkillTree.NODES:
            self.assertIn(n.get("cat"), self.VALID_CATS,
                          f"{n['id']} kategorisi geçersiz: {n.get('cat')}")

    def test_category_table_matches_renderer(self):
        """Üreticinin ürettiği kategoriler ile çizicinin renk tablosu aynı
        kümeyi kullanmalı; biri değişip diğeri unutulursa düğümler nötr çizilir."""
        import re, io, os
        src = io.open(os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "scenes", "game_scene.py"),
            encoding="utf-8").read()
        block = src.split("TREE_CAT_COLORS = {", 1)[1].split("}", 1)[0]
        renderer_cats = set(re.findall(r'"(\w+)"\s*:', block))
        self.assertEqual(renderer_cats, self.VALID_CATS)

    def test_keystones_have_a_downside(self):
        for n in SkillTree.NODES:
            if n["type"] == "keystone":
                self.assertTrue(any(v < 0 for v in n["stats"].values()),
                                f"{n['name']} bedelsiz keystone")

    def test_stale_saved_nodes_are_refunded(self):
        """Ağaç yeniden üretilince eski kayıttaki id'ler kaybolur. Sessizce
        atılırlarsa oyuncu yatırdığı tüm SP'yi kaybeder — iade edilmeli."""
        import json, os, tempfile
        from logic.save_manager import SaveManager

        class _P:
            def __init__(self):
                self.base_class_id = "warrior"
                self.class_id = "warrior"
                self.skill_points = 0
                self.skills = []
                self.allocated_nodes = set()

        p = _P()
        # Eski ray düzeninden kalma id'ler (yeni ağaçta çark var, ray yok).
        # Bilerek YALNIZCA artık var olmayanlar seçildi.
        pd = {"allocated_nodes": ["start_warrior", "warrior_C4",
                                  "warrior_L5", "warrior_R2"]}
        for stale_id in ("warrior_C4", "warrior_L5", "warrior_R2"):
            self.assertNotIn(stale_id, SkillTree.BY_ID,
                             "test verisi güncel değil: bu id hâlâ mevcut")
        # load_game'in ilgili bloğunu birebir taklit et
        saved = set(pd["allocated_nodes"])
        stale = {n for n in saved if n not in SkillTree.BY_ID}
        refund = sum(1 for n in stale if not SkillTree.is_start(n))
        p.skill_points += refund
        p.allocated_nodes = (saved - stale) | set(
            SkillTree.start_nodes_for(p.base_class_id))

        self.assertEqual(refund, 3, "geçersiz düğümler iade edilmedi")
        self.assertEqual(p.allocated_nodes, {"start_warrior"})
        for nid in p.allocated_nodes:
            self.assertIn(nid, SkillTree.BY_ID)

    def test_requested_stats_present(self):
        want = ["shopRarity", "goldGain", "magicFind", "bounce", "pierce",
                "lifesteal", "max_hp", "regen", "maxEnergyShield", "esRegen",
                "meleeRangeFlat", "aoe_bonus", "speed", "minionPierce",
                "minionBounce", "minionRate", "minionRange", "minionDamage",
                "turretRange", "turretRate", "turretDmg"]
        used = {s for n in SkillTree.NODES for s in n.get("stats", {})}
        for w in want:
            self.assertIn(w, used, f"ağaçta '{w}' veren düğüm yok")


if __name__ == "__main__":
    unittest.main()
