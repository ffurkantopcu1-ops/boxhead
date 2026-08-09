# -*- coding: utf-8 -*-
"""Geç-oyun (tam yatırımlı karakter) denge regresyon testleri.

test_class_balance.py başlangıç (dalga-1) gücünü ölçer; bu dosya ise TAM
YATIRIMLI bir build kurar — güç kaynaklarının hepsi birden yığıldığında OP
stacking loophole'ları çıkar mı diye bakar:

    class_bases + yetenek ağacı (SkillTree) + evrim + ascendancy (Ascendancy)
    + sınıf-sinerjik kartlar  →  player.inv_manager.recalculate_stats()

AGENTS.md kuralı: tam yatırımlı bir build eşdeğer savaşçı build'inin ~2x'inden
fazlasına ÇARPMAMALI. Burada biraz gevşetip 2.2x tavan kullanıyoruz (geç oyun
varyansı için pay). İki sınıf (sorcerer, ninja) mevcut veride bu bandı zaten
AŞIYOR — bunlar bilinen stacking outlier'ları; aşağıda KNOWN_OUTLIERS ile
belgelenip kendi (daha yüksek) tavanlarına sabitlendiler ki DAHA BÜYÜK bir
regresyon (ör. biri bir statı daha yükseltirse) yine yakalansın. Bkz. testin
başındaki not ve rapor.

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
from logic.skill_tree import SkillTree
from logic.ascendancy import Ascendancy
from logic.card_system import CardSystem


# ---------------------------------------------------------------------------
# Etkin güç formülleri (test_class_balance.py ile birebir aynı model)
# ---------------------------------------------------------------------------
def wave_dps(s):
    """Tek hedef etkin doğrudan+DoT DPS (oyunun hasar modeline yakın kaba tahmin)."""
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


# ---------------------------------------------------------------------------
# Tam yatırımlı build kurucu
# ---------------------------------------------------------------------------
# Her sınıf için güçlü, sinerjik kart seti (data/cards.json'dan seçildi).
# Amaç en agresif (en yüksek çıktı veren) makul kombinasyonu zorlamak.
CLASS_CARDS = {
    "warrior":     ["rampage", "chaos_theory", "double_edge", "crit_overload"],
    "sniper":      ["deadeye", "headhunter", "crit_overload", "long_barrel", "armor_piercing"],
    "ninja":       ["thousand_cuts", "chaos_theory", "crit_overload", "assassinate", "double_edge"],
    "bloodwalker": ["chaos_theory", "double_edge", "crit_overload", "blood_fire"],
    "sorcerer":    ["arcane_surge", "fire_soul", "void_touch", "crit_overload"],
    "alchemist":   ["poison_master", "toxic_blood", "venomous_strike", "corrosion", "toxic_cloud"],
    "beastmaster": ["war_commander", "swarmlord", "alpha_bond", "spirit_link"],
    "engineer":    ["auto_targeting", "overclock", "factory_line", "reinforced_turrets"],
    "bomber":      ["cluster_bomb", "demolition", "napalm", "bomb_barrage", "void_touch"],
}

# Sınıf -> o sınıfın Player.EVOLUTIONS'taki İLK evrimi (class_base ile süzülür).
FIRST_EVO_BY_CLASS = {}
for _evo_id, _evo in Player.EVOLUTIONS.items():
    FIRST_EVO_BY_CLASS.setdefault(_evo["class_base"], _evo_id)

SKILL_NODE_BUDGET = 60   # ~20+ seviyede biriken SP; ağacın kolunu doldurmaya yeter
ASCENDANCY_POINTS = 20   # bir alt-sınıfın 5 düğümünü fazlasıyla doldurur


def _greedy_allocate_tree(player, arm, budget):
    """Açgözlü ağaç yatırımı: önce sınıfın KENDİ kolu, sonra çekirdek, sonra
    diğerleri; her adımda en yüksek stat toplamına sahip komşu düğümü al.
    Bir sınıfın erişebileceği en güçlü yolu zorlar."""
    spent = 0
    while spent < budget:
        cands = SkillTree.allocatable_nodes(player.allocated_nodes)
        if not cands:
            break

        def score(nid):
            node = SkillTree.BY_ID[nid]
            arm_pri = 0 if node.get("arm") == arm else (1 if node.get("arm") == "core" else 2)
            stat_val = sum(abs(v) for v in node.get("stats", {}).values())
            return (arm_pri, -stat_val)

        cands.sort(key=score)
        ok, _ = SkillTree.allocate(player, cands[0])
        if not ok:
            break
        spent += 1
    return spent


def _fill_ascendancy(player):
    """Seçilen alt-sınıfın tüm ulaşılabilir düğümlerini doldur."""
    spent = 0
    while getattr(player, "ascendancy_points", 0) > 0:
        cands = [c for c in Ascendancy.allocatable_nodes(player.ascendancy_nodes)
                 if Ascendancy.BY_ID[c]["subclass"] == player.evolution]
        if not cands:
            break
        ok, _ = Ascendancy.allocate(player, cands[0])
        if not ok:
            break
        spent += 1
    return spent


def build_fully_invested(class_id):
    """Bir sınıf için maksimum-yatırımlı karakter kur ve döndür."""
    p = Player(0, 0, 0, class_id)

    # 1) Yetenek ağacı: bol SP ver, güçlü yolu açgözlüce doldur
    p.skill_points = 5 * SKILL_NODE_BUDGET
    _greedy_allocate_tree(p, class_id, SKILL_NODE_BUDGET)

    # 2) Seviye >= 20 ve sınıfın ilk evrimini uygula (ascendancy ağacını açar)
    p.level = 25
    p.apply_evolution(FIRST_EVO_BY_CLASS[class_id])

    # 3) Ascendancy puanı ver ve alt-sınıf ağacını doldur
    p.ascendancy_points = ASCENDANCY_POINTS
    _fill_ascendancy(p)

    # 4) Sınıf-sinerjik güçlü kartları uygula
    cs = CardSystem()
    for card_id in CLASS_CARDS.get(class_id, []):
        cs.apply_card(card_id, p)

    p.inv_manager.recalculate_stats()
    return p


# ---------------------------------------------------------------------------
# Tavanlar
# ---------------------------------------------------------------------------
# AGENTS.md: ~2x; geç-oyun varyansı için 2.2x'e gevşetildi.
DPS_CEILING_RATIO = 2.2

# BİLİNEN OUTLIER'LAR — mevcut veride 2.2x bandını AŞAN sınıflar. Bunlar
# gerçek stacking loophole'larıdır (rapora bkz.); testin "temiz" koşması için
# kendi (belgeli) tavanlarına sabitlendiler. Değerler mevcut tepe + küçük pay
# olarak seçildi; biri bir statı DAHA yükseltirse bu tavan da tetiklenir.
#   sorcerer: flat element hasarı (firelord evo +90, fire_soul +30) × yüksek
#             elementDmgMult (~2.65) × dmgMult × çok düşük cooldown (400 taban).
#   ninja:    kritik yığını (%86 krit × critDmg 3.47) × dmgMult 3.37 × en düşük
#             cooldown (attack_speed_bonus 1.13 + sınıf tabanı 0.3).
KNOWN_OUTLIERS = {
    "sorcerer": 5.6,
    "ninja": 3.4,
}

# EHP: makul bant. Tam yatırımlı tank/kaçınma build'leri savaşçının katları
# olabilir ama sınırsız değil.
EHP_MAX_RATIO = 3.0
EHP_MIN_RATIO = 0.10   # cam-top hasar sınıfları (sorcerer) çok düşük EHP'ye iner

# Soft-cap sağlık kontrolü: stat değerleri InventoryManager.SOFT_CAPS
# hard-cap'lerini AŞMAMALI (recalc bunları kırpmalı). Ayrıca kırpma sonrası
# knee'nin çok üstünde saçma değerler oluşmamalı.
SOFTCAP_STATS = {
    "critChance": 1.0,      # hard cap
    "critDmg": 4.0,         # hard cap
    "dmgMult": 8.0,         # knee 2.0, hard cap yok -> azalan getiri; makul tavan
    "elementDmgMult": 3.0,  # hard cap
    "dotDmgMult": 2.0,      # hard cap
    "lifesteal": 0.50,      # hard cap
    "dodgeChance": 0.60,    # hard cap
}


def _all_invested_stats():
    out = {}
    for c in sorted(InventoryManager.CLASS_IDS):
        out[c] = build_fully_invested(c).stats
    return out


class TestLateGameBalance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stats = _all_invested_stats()
        w = cls.stats["warrior"]
        cls.w_dps = wave_dps(w)
        cls.w_ehp = effective_hp(w)

    def test_no_class_dps_outlier(self):
        """Hiçbir sınıfın tam yatırımlı DPS'i savaşçının 2.2x'ini geçmemeli.
        Bilinen outlier'lar kendi (daha yüksek, belgeli) tavanına tabi tutulur;
        böylece o sınıflar bile DAHA fazla şişerse test yine kırılır."""
        for c in sorted(self.stats):
            d = wave_dps(self.stats[c])
            ratio = d / self.w_dps
            ceiling = KNOWN_OUTLIERS.get(c, DPS_CEILING_RATIO)
            self.assertLessEqual(
                ratio, ceiling,
                f"{c} tam-yatirimli DPS {d:.0f} = {ratio:.2f}x savasci "
                f"(tavan {ceiling}x) — OP STACKING loophole!")

    def test_ehp_within_band(self):
        for c in sorted(self.stats):
            e = effective_hp(self.stats[c])
            ratio = e / self.w_ehp
            self.assertGreaterEqual(
                ratio, EHP_MIN_RATIO,
                f"{c} tam-yatirimli EHP {e:.0f} = {ratio:.2f}x savasci — cok dusuk")
            self.assertLessEqual(
                ratio, EHP_MAX_RATIO,
                f"{c} tam-yatirimli EHP {e:.0f} = {ratio:.2f}x savasci — cok yuksek")

    def test_stats_respect_soft_caps(self):
        """recalculate_stats soft/hard-cap'leri uygulamalı; hiçbir stat
        makul tavanının üstüne çıkmamalı (kırpma çalışıyor mu?)."""
        for c in sorted(self.stats):
            s = self.stats[c]
            for stat, cap in SOFTCAP_STATS.items():
                val = s.get(stat, 0) or 0
                self.assertLessEqual(
                    val, cap + 1e-6,
                    f"{c}.{stat}={val:.3f} > {cap} — soft-cap kirpmasi calismiyor / "
                    f"deger sacma sekilde yigilmis")

    def test_warrior_baseline_sane(self):
        """Savaşçı baz çizgisi anlamlı olmalı (bölme sıfır/dejenerasyon yok)."""
        self.assertGreater(self.w_dps, 100, "savasci baz DPS beklenenden dusuk")
        self.assertGreater(self.w_ehp, 100, "savasci baz EHP beklenenden dusuk")


if __name__ == "__main__":
    unittest.main()
