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


if __name__ == "__main__":
    unittest.main()
