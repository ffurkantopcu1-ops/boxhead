import unittest

from logic.card_system import CardSystem


class TestCardStatContributions(unittest.TestCase):
    def test_sums_card_damage_and_dot_bonuses(self):
        cards = CardSystem()
        cards.active_cards = ["chaos_theory", "poison_master", "venomous_strike"]

        contribution = cards.get_stat_contributions()

        self.assertAlmostEqual(contribution["dmgMult"], 0.8)
        self.assertAlmostEqual(contribution["dotDmgMult"], 0.65)
        self.assertAlmostEqual(contribution["fireRate"], -0.4)

    def test_includes_unlocked_synergy_bonus(self):
        cards = CardSystem()
        cards.active_cards = ["chaos_theory", "crit_overload"]

        contribution = cards.get_stat_contributions()

        self.assertAlmostEqual(contribution["critDmg"], 3.0)


class TestAffinityOffering(unittest.TestCase):
    def _offer_all(self, player_class):
        cards = CardSystem()
        cards.active_cards = []
        cards.legendary_chance = 0.0
        # count'u havuzdan buyuk verince izin verilen TUM kartlar doner
        return {c["id"] for c in cards.offer_cards(count=999, player_class=player_class)}

    def test_turret_cards_only_for_engineer(self):
        eng = self._offer_all("engineer")
        war = self._offer_all("warrior")
        self.assertIn("factory_line", eng)
        self.assertNotIn("factory_line", war)

    def test_minion_cards_only_for_beastmaster(self):
        bm = self._offer_all("beastmaster")
        sniper = self._offer_all("sniper")
        self.assertIn("war_commander", bm)
        self.assertNotIn("war_commander", sniper)

    def test_new_class_cards_gated_by_affinity(self):
        bomber = self._offer_all("bomber")
        warrior = self._offer_all("warrior")
        self.assertIn("bomb_barrage", bomber)
        self.assertNotIn("bomb_barrage", warrior)
        self.assertIn("rampage", warrior)
        self.assertNotIn("rampage", bomber)

    def test_universal_cards_offered_to_everyone(self):
        for cls in ("warrior", "engineer", "bomber", "sorcerer"):
            self.assertIn("chaos_theory", self._offer_all(cls))

    def test_no_player_class_disables_filter(self):
        # Geriye donuk: sinif verilmezse affinity kartlari da gelebilir
        cards = CardSystem()
        cards.active_cards = []
        cards.legendary_chance = 0.0
        ids = {c["id"] for c in cards.offer_cards(count=999, player_class=None)}
        self.assertIn("factory_line", ids)


class TestCardDataIntegrity(unittest.TestCase):
    def test_every_affinity_targets_a_real_class(self):
        from logic.inventory_manager import InventoryManager
        for card in CardSystem.CARDS:
            for cid in card.get("affinity", []):
                self.assertIn(cid, InventoryManager.CLASS_IDS,
                              f"{card['id']} gecersiz sinifa affinity veriyor: {cid}")

    def test_new_cards_carry_a_downside(self):
        # v1.16 kimlik kartlari bedelsiz olmamali (AGENTS.md guc butcesi).
        new_ids = {
            "bomb_barrage", "cluster_bomb", "napalm", "shrapnel", "demolition",
            "armor_piercing", "headhunter", "deadeye", "long_barrel",
            "shadow_step", "thousand_cuts", "assassinate", "swift_reflexes",
            "rampage", "juggernaut", "auto_targeting", "reinforced_turrets",
            "toxic_cloud", "corrosion", "arcane_surge",
        }
        by_id = {c["id"]: c for c in CardSystem.CARDS}
        for cid in new_ids:
            self.assertIn(cid, by_id, f"{cid} cards.json'da yok")
            stats = by_id[cid].get("stats", {})
            has_downside = any(v < 0 for v in stats.values()) or \
                by_id[cid]["id"] == "demolition"  # demolition bedeli flag (damage_taken)
            self.assertTrue(has_downside, f"{cid} bedelsiz görünüyor")


if __name__ == "__main__":
    unittest.main()
