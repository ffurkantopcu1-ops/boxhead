# -*- coding: utf-8 -*-
"""Sınıf denge regresyon testleri (AGENTS.md 'Class And Evolution Balance').

Dalga-1 (başlangıç silahı) etkin DPS ve EHP'yi hesaplar; hiçbir sınıfın
Savaşçı temeline göre BOZUK (>2x) olmadığını, doğrudan-hasar sınıflarının
uygulanabilir kaldığını ve class_bases değerlerinin envelope içinde durduğunu
doğrular. Amaç: ileride biri bir statı yükseltip sınıfı OP yaparsa yakalamak.

Pygame penceresi açmadan çalışır (SDL dummy)."""
import os
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from entities.player import Player
from logic.inventory_manager import InventoryManager


def wave1_dps(s):
    """Dalga-1 tek hedef etkin DPS (oyunun kendi hasar modeline yakın kaba tahmin)."""
    cd = s.get("attack_cooldown", 350) / 1000.0
    dm = s.get("dmgMult", 1.0)
    phys = s.get("physDmg", 0) + s.get("physDmgFlat", 0)
    elem = (s.get("fireDamage", 0) + s.get("fireDmgFlat", 0)
            + s.get("frostDamage", 0) + s.get("frostDmgFlat", 0)) * (1 + s.get("elementDmgMult", 0))
    crit = 1 + s.get("critChance", 0.05) * (1.0 + s.get("critDmg", 0))
    direct = ((phys + elem) * dm * crit) / cd if cd > 0 else 0
    dot = s.get("poisonDps", 0) * dm * (1 + s.get("dotDmgMult", 0))
    return direct + dot


def effective_hp(s):
    hp = s.get("max_hp", 100)
    armor = max(-75, s.get("armor", 0))
    dodge = min(0.6, s.get("dodgeChance", 0.05))
    es = s.get("maxEnergyShield", 0)
    return (hp + es) * (1 + armor / 100.0) / (1 - dodge)


def _stats_for(class_id):
    p = Player(0, 0, 0, class_id)
    p.inv_manager.recalculate_stats()
    return p.stats


# Doğrudan-hasar (combat) sınıfları: alt sınır da uygulanır.
# Utility/summon/DoT (engineer, beastmaster, alchemist, bomber, sorcerer) gücü
# taret/minyon/DoT/element'te olduğu için kaba DPS formülü onları düşük gösterir.
DIRECT_CLASSES = {"warrior", "sniper", "ninja", "bloodwalker"}

# class_bases stat -> (min, max) izinli aralık (mevcut değerler bunları sağlar).
ENVELOPE = {
    "dmgMult": (0.0, 0.6), "max_hp_mult": (-0.35, 0.35), "speed": (4.0, 7.5),
    "attack_cooldown": (350, 1600), "lifesteal": (0.0, 0.25), "critChance": (0.0, 0.25),
    "dodgeChance": (0.0, 0.30), "attack_speed_mult": (0.0, 0.4), "elementDmgMult": (0.0, 0.7),
    "aoe": (0.0, 0.7), "dotDmgMult": (0.0, 0.4), "minionDamage": (0.0, 0.5),
    "turretLimit": (0, 2), "armor": (0, 30), "regen": (0.0, 3.0), "bounce": (0, 3), "pierce": (0, 3),
}


class TestClassBalance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        w = _stats_for("warrior")
        cls.w_dps = wave1_dps(w)
        cls.w_ehp = effective_hp(w)

    def test_no_class_is_broken(self):
        # AGENTS.md: hiçbir sınıf ~2x savaşçıyı geçmemeli
        for c in sorted(InventoryManager.CLASS_IDS):
            d = wave1_dps(_stats_for(c))
            self.assertLessEqual(
                d, 2.0 * self.w_dps,
                f"{c} DPS {d:.1f} > 2x savaşçı ({self.w_dps:.1f}) — BOZUK/OP")

    def test_direct_classes_are_viable(self):
        for c in DIRECT_CLASSES:
            d = wave1_dps(_stats_for(c))
            self.assertGreaterEqual(
                d, 0.5 * self.w_dps,
                f"{c} DPS {d:.1f} < 0.5x savaşçı ({self.w_dps:.1f}) — çok zayıf")

    def test_ehp_within_band(self):
        for c in sorted(InventoryManager.CLASS_IDS):
            e = effective_hp(_stats_for(c))
            self.assertGreaterEqual(e, 0.4 * self.w_ehp, f"{c} EHP {e:.0f} çok düşük")
            self.assertLessEqual(e, 2.0 * self.w_ehp, f"{c} EHP {e:.0f} çok yüksek")

    def test_class_bases_within_envelope(self):
        for c, bases in InventoryManager.CLASS_BASES.items():
            for stat, val in bases.items():
                if stat not in ENVELOPE:
                    continue
                lo, hi = ENVELOPE[stat]
                self.assertGreaterEqual(val, lo, f"{c}.{stat}={val} < {lo} (envelope)")
                self.assertLessEqual(val, hi, f"{c}.{stat}={val} > {hi} (envelope)")


if __name__ == "__main__":
    unittest.main()
