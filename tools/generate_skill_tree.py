# -*- coding: utf-8 -*-
"""data/skill_tree.json (ANA pasif ağaç) üretir — Path of Exile'vari ÇARK AĞACI.

Çalıştır (repo kökünden):
    python tools/generate_skill_tree.py

================================ TASARIM ================================
Eski ağaç kusursuz bir daireydi: 9 sınıf × 3 ray × 6 halka ve HER halkada
teğetsel bağ. Dört somut sorunu vardı; bu üretici hepsini hedefler:

(A) Güçlü düğümlerin hepsi dış kenardaydı ve kenar halkası teğetsel bağlıydı
    -> kenara ulaşan biri tek puan harcayıp hepsini sırayla topluyordu.
    ÇÖZÜM: notable'lar ÇARKLARIN İÇİNDE. Bir çarka tek giriş vardır ve
    notable girişin karşısındadır; almak için çarkın yarısını yürümek
    gerekir. Keystone'lar ise çarktan sonra, TEĞETSEL BAĞI OLMAYAN uzun bir
    mahmuzun ucundadır.

(B) Her yer her yere bağlıydı -> yol seçimi diye bir şey yoktu.
    ÇÖZÜM: sınıflar arası geçiş yalnız İKİ noktada: paylaşılan iç çember
    (ucuz ama sadece komşunun BAŞLANGICINA götürür) ve orta bantdaki köprü
    çarkları (pahalı, gerçek bir sapma).

(C) Kusursuz daire sıkıcı görünüyordu.
    ÇÖZÜM: çarklar farklı boyutlarda (4/6/9 düğüm), sınıf başına deterministik
    açı/yarıçap sapması (JITTER_A/JITTER_R) ve merkezde büyük bir boşluk.

(D) Sınıf başlangıçları jenerikti.
    ÇÖZÜM: her başlangıcın çevresinde İKİ küçük çark — biri sınıf kimliği,
    biri hayatta kalma. Aradaki bağlantı düğümleri de sınıf temalıdır.

Katmanlar (merkez CX,CY):
    r<R_RING   ÇEKİRDEK BOŞLUK — ortada 5 büyük SAVUNMA keystone'u, her birine
               iç çemberden ayrı mahmuz. Birbirlerine BAĞLI DEĞİLLER.
    R_RING     İÇ ÇEMBER — 9 sınıf başlangıcı + 9 geçit (arm=core).
    R_SMALL    Başlangıç çevresi — sınıf başına 2 küçük çark (kimlik + survival).
    R_MID      ORTA çark (6 düğüm, 1 notable) + komşular arası KÖPRÜ çarkı.
    R_SPEC     UZMANLIK çarkı — sekme/delme/can çalma/ganimet/minyon/taret...
    R_BIG      BÜYÜK çark (9 düğüm, 2 notable) — sınıfın imza çarkı.
    R_SPUR+    KEYSTONE MAHMUZU — 3 yolculuk düğümü, sonra keystone.

Her düğüm bir `cat` (kategori) taşır: renklendirme ve ileride ikon için tek
kaynak (bkz. scenes/game_scene.py -> TREE_CAT_COLORS).
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'skill_tree.json')

# Tuval merkezi. Aralıklar bilerek GENİŞ: ağaç tam ekranda nefes alsın,
# çarklar birbirine girmesin (UI kaydırma + yakınlaştırma yapıyor).
CX, CY = 3000, 3000

R_CORE_KEY = 260      # çekirdek savunma keystone'ları
R_CORE_MID = 500      # çekirdek mahmuzunun ara düğümü
R_RING = 740          # iç çember (sınıf başlangıçları)
R_LEAD0 = 920
R_SMALL = 1140        # başlangıç çevresi küçük çarklar
R_LEAD1 = 1360
R_MID = 1570          # orta çark + köprü çarkı
R_LEAD2 = 1790
R_SPEC = 1840         # uzmanlık çarkı (yandan dallanır)
R_BIG = 2030          # büyük çark
R_SPUR = [2320, 2490, 2660]
R_KEYSTONE = 2830

WHEEL_R_SMALL = 126
WHEEL_R_MID = 182
WHEEL_R_BIG = 252
WHEEL_R_BRIDGE = 140
WHEEL_R_SPEC = 132

CLASSES = ["warrior", "sniper", "engineer", "beastmaster", "bomber",
           "alchemist", "sorcerer", "bloodwalker", "ninja"]

# Deterministik düzensizlik — kusursuz daire görüntüsünü kırar (tasarım notu C)
JITTER_A = [-6, 4, -3, 7, 0, -5, 6, -2, 3]          # derece
JITTER_R = [0, 60, -45, 35, -22, 55, -60, 24, -34]  # piksel

# ----------------------------------------------------------------------
# KATEGORİLER — düğüm rengi ve ileride ikon buradan türetilir.
# Bir düğümün kategorisi, statlarının en yüksek öncelikli kategorisidir.
# ----------------------------------------------------------------------
CAT_PRIORITY = ["turret", "minion", "utility", "element", "dot", "defense", "damage"]

STAT_CAT = {
    # --- saldırı ---
    "dmgMult": "damage", "physDmgFlat": "damage", "physDmgMult": "damage",
    "critChance": "damage", "critDmg": "damage", "attack_speed_bonus": "damage",
    "armorPen": "damage", "bossDmgMult": "damage", "bullet_speed": "damage",
    "pierce": "damage", "bounce": "damage", "projectileCount": "damage",
    "meleeRangeFlat": "damage",
    # --- element ---
    "fireDmgFlat": "element", "fireDmgMult": "element",
    "frostDmgFlat": "element", "frostDmgMult": "element",
    "elementDmgMult": "element",
    # --- süreli hasar / alan ---
    "dotDmgMult": "dot", "poisonDps": "dot", "aoe_bonus": "dot",
    # --- hayatta kalma ---
    "max_hp": "defense", "max_hp_pct": "defense", "armor": "defense",
    "regen": "defense", "combatRegen": "defense", "lifesteal": "defense",
    "dodgeChance": "defense", "maxEnergyShield": "defense", "esRegen": "defense",
    "speed": "defense",
    # --- minyon ---
    "minionDamage": "minion", "minionRate": "minion", "minionMaxHpFlat": "minion",
    "minionCount": "minion", "minionArmor": "minion", "minionRange": "minion",
    "minionPierce": "minion", "minionBounce": "minion",
    # --- taret ---
    "turretDmg": "turret", "turretRate": "turret", "turretMaxHp": "turret",
    "turretLimit": "turret", "turretCharges": "turret", "turretRange": "turret",
    # --- yardımcı ---
    "magicFind": "utility", "goldGain": "utility", "xpGain": "utility",
    "shopRarity": "utility", "magnetRadius": "utility",
}


def cat_of(stats):
    """Düğümün kategorisi: statları arasında en yüksek öncelikli olan."""
    if not stats:
        return "core"
    cats = {STAT_CAT.get(k, "damage") for k in stats}
    for c in CAT_PRIORITY:
        if c in cats:
            return c
    return "damage"


# ----------------------------------------------------------------------
# STAT ETİKETLERİ — işaret duyarlı (negatif bedeller de okunabilir yazılır)
# ----------------------------------------------------------------------
def _pct(v):
    return f"%{abs(v) * 100:.0f}"


def _flat(v, dec=0):
    return f"{abs(v):.{dec}f}"


def _sg(v):
    return "+" if v >= 0 else "-"


STAT_LABEL = {
    "max_hp":             lambda v: f"{_sg(v)}{_flat(v)} Can",
    "max_hp_pct":         lambda v: (f"Max Can %{-v:.0f} azalır" if v < 0
                                     else f"+%{v:.0f} Max Can"),
    "maxEnergyShield":    lambda v: f"{_sg(v)}{_flat(v)} Enerji Kalkanı",
    "esRegen":            lambda v: f"{_sg(v)}{_flat(v)} ES Yenilenme",
    "armor":              lambda v: f"{_sg(v)}{_flat(v)} Zırh",
    "regen":              lambda v: f"{_sg(v)}{_flat(v, 1)} Can Yenilenme",
    "combatRegen":        lambda v: f"{_sg(v)}{_flat(v, 1)} Savaş Yenilenme",
    "lifesteal":          lambda v: f"{_sg(v)}{_pct(v)} Can Çalma",
    "dodgeChance":        lambda v: f"{_sg(v)}{_pct(v)} Kaçınma",
    "speed":              lambda v: f"{_sg(v)}{_flat(v, 1)} Hareket Hızı",
    "dmgMult":            lambda v: f"{_sg(v)}{_pct(v)} Hasar",
    "attack_speed_bonus": lambda v: f"{_sg(v)}{_pct(v)} Saldırı Hızı",
    "critChance":         lambda v: f"{_sg(v)}{_pct(v)} Kritik Şans",
    "critDmg":            lambda v: f"{_sg(v)}{_pct(v)} Kritik Hasar",
    "physDmgFlat":        lambda v: f"{_sg(v)}{_flat(v)} Fiziksel Hasar",
    "physDmgMult":        lambda v: f"{_sg(v)}{_pct(v)} Fiziksel Hasar",
    "fireDmgFlat":        lambda v: f"{_sg(v)}{_flat(v)} Ateş Hasarı",
    "fireDmgMult":        lambda v: f"{_sg(v)}{_pct(v)} Ateş Hasarı",
    "frostDmgFlat":       lambda v: f"{_sg(v)}{_flat(v)} Buz Hasarı",
    "frostDmgMult":       lambda v: f"{_sg(v)}{_pct(v)} Buz Hasarı",
    "elementDmgMult":     lambda v: f"{_sg(v)}{_pct(v)} Element Hasarı",
    "dotDmgMult":         lambda v: f"{_sg(v)}{_pct(v)} DoT Hasarı",
    "poisonDps":          lambda v: f"{_sg(v)}{_flat(v)} Zehir DPS",
    "aoe_bonus":          lambda v: f"{_sg(v)}{_pct(v)} Alan (AoE)",
    "pierce":             lambda v: f"{_sg(v)}{_flat(v)} Delme",
    "bounce":             lambda v: f"{_sg(v)}{_flat(v)} Sekme",
    "projectileCount":    lambda v: f"{_sg(v)}{_flat(v)} Mermi",
    "bullet_speed":       lambda v: f"{_sg(v)}{_flat(v)} Mermi Hızı",
    "meleeRangeFlat":     lambda v: f"{_sg(v)}{_flat(v)} Menzil",
    "armorPen":           lambda v: f"{_sg(v)}{_flat(v, 1)} Zırh Delme",
    "bossDmgMult":        lambda v: f"{_sg(v)}{_pct(v)} Boss Hasarı",
    "turretDmg":          lambda v: f"{_sg(v)}{_pct(v)} Taret Hasarı",
    "turretRate":         lambda v: f"{_sg(v)}{_pct(v)} Taret Saldırı Hızı",
    "turretMaxHp":        lambda v: f"{_sg(v)}{_flat(v)} Taret Canı",
    "turretLimit":        lambda v: f"{_sg(v)}{_flat(v)} Taret Limiti",
    "turretCharges":      lambda v: f"{_sg(v)}{_flat(v)} Taret Şarjı",
    "turretRange":        lambda v: f"{_sg(v)}{_flat(v)} Taret Menzili",
    "minionDamage":       lambda v: f"{_sg(v)}{_pct(v)} Minyon Hasarı",
    "minionRate":         lambda v: f"{_sg(v)}{_pct(v)} Minyon Saldırı Hızı",
    "minionRange":        lambda v: f"{_sg(v)}{_pct(v)} Minyon Menzili",
    "minionMaxHpFlat":    lambda v: f"{_sg(v)}{_flat(v)} Minyon Canı",
    "minionCount":        lambda v: f"{_sg(v)}{_flat(v)} Minyon",
    "minionArmor":        lambda v: f"{_sg(v)}{_flat(v)} Minyon Zırhı",
    "minionPierce":       lambda v: f"{_sg(v)}{_flat(v)} Minyon Delmesi",
    "minionBounce":       lambda v: f"{_sg(v)}{_flat(v)} Minyon Sekmesi",
    "magicFind":          lambda v: f"{_sg(v)}{_pct(v)} Eşya Düşme Şansı",
    "goldGain":           lambda v: f"{_sg(v)}{_pct(v)} Altın Kazanımı",
    "xpGain":             lambda v: f"{_sg(v)}{_pct(v)} XP Kazanımı",
    "shopRarity":         lambda v: f"{_sg(v)}{_flat(v)} Kervan Nadirliği",
    "magnetRadius":       lambda v: f"{_sg(v)}{_flat(v)} Toplama Alanı",
}


def desc_of(stats):
    return ", ".join(STAT_LABEL.get(k, lambda v: f"{k} {v}")(v) for k, v in stats.items())


def label_of(stat, val):
    return STAT_LABEL.get(stat, lambda v: f"{stat} {v}")(val)


# ----------------------------------------------------------------------
# ÇEKİRDEK SAVUNMA KEYSTONE'LARI (ortadaki boşluğun çevresi)
# Büyük savunma + gerçek bedel. Birbirlerine bağlı değiller.
# ----------------------------------------------------------------------
CORE_KEYSTONES = [
    ("❤️ Yaşam Çekirdeği", {"max_hp": 260, "regen": 2.0, "dmgMult": -0.18}),
    ("🔷 Kalkan Çekirdeği", {"maxEnergyShield": 200, "esRegen": 45, "speed": -0.6}),
    ("🪨 Granit Kalp", {"armor": 40, "max_hp": 120, "attack_speed_bonus": -0.20}),
    ("♻️ Yeniden Doğuş", {"regen": 5.0, "combatRegen": 3.0, "max_hp_pct": -10}),
    ("👁️ Kaçış Ustası", {"dodgeChance": 0.14, "speed": 0.8, "armor": -20}),
]
CORE_SPUR_STATS = [
    {"max_hp": 60}, {"maxEnergyShield": 50}, {"armor": 11},
    {"regen": 1.4}, {"dodgeChance": 0.04},
]

# ----------------------------------------------------------------------
# UZMANLIK ÇARKLARI (#7) — belirli bir özelliğe adanmış küçük çarklar.
# Her sınıfın yanına tematik olarak biri düşer; diğerlerine yürüyerek gidilir.
# ----------------------------------------------------------------------
SPEC_WHEELS = {
    "warrior":     ("🫀 Can Çarkı",
                    [("max_hp", 60), ("regen", 1.4), ("max_hp", 55)],
                    ("🫀 Yaşam Gücü", {"max_hp": 130, "max_hp_pct": 8})),
    "sniper":      ("🏹 Delme Çarkı",
                    [("pierce", 1), ("bullet_speed", 2), ("projectileCount", 1)],
                    ("🏹 Zırh Delici", {"pierce": 2, "armorPen": 0.4})),
    "engineer":    ("🔧 Taret Çarkı",
                    [("turretRange", 40), ("turretRate", 0.12), ("turretDmg", 0.14)],
                    ("📡 Uzak Menzil", {"turretRange": 90, "turretRate": 0.15})),
    "beastmaster": ("🐾 Minyon Çarkı",
                    [("minionPierce", 1), ("minionBounce", 1), ("minionRange", 0.14)],
                    ("🐾 Sürü Taktiği", {"minionRate": 0.20, "minionDamage": 0.18})),
    "bomber":      ("💥 Alan Çarkı",
                    [("aoe_bonus", 0.12), ("fireDmgFlat", 7), ("aoe_bonus", 0.11)],
                    ("💥 Geniş Yıkım", {"aoe_bonus": 0.26, "dmgMult": 0.10})),
    "alchemist":   ("💰 Ganimet Çarkı",
                    [("magicFind", 0.10), ("goldGain", 0.12), ("shopRarity", 1)],
                    ("🛝 Kervan Ustası", {"shopRarity": 2, "magicFind": 0.18})),
    "sorcerer":    ("🔷 Kalkan Çarkı",
                    [("maxEnergyShield", 55), ("esRegen", 20), ("maxEnergyShield", 50)],
                    ("🔋 Şarj Örtüsü", {"maxEnergyShield": 100, "esRegen": 35})),
    "bloodwalker": ("🩸 Can Çalma Çarkı",
                    [("lifesteal", 0.03), ("combatRegen", 1.2), ("lifesteal", 0.03)],
                    ("🩸 Kan Emici", {"lifesteal": 0.07, "max_hp": 70})),
    "ninja":       ("☄️ Sekme Çarkı",
                    [("bounce", 1), ("bullet_speed", 2), ("bounce", 1)],
                    ("☄️ Seken Bıçaklar", {"bounce": 2, "dmgMult": 0.10})),
}

# ----------------------------------------------------------------------
# SINIF TEMALARI
# ----------------------------------------------------------------------
THEMES = {
    "warrior": {
        "lead": [("physDmgFlat", 9), ("max_hp", 55), ("armor", 10)],
        "ident": ([("physDmgFlat", 9), ("dmgMult", 0.07), ("meleeRangeFlat", 22)],
                  ("🪓 Ağır Darbe", {"physDmgFlat": 15, "dmgMult": 0.09})),
        "surv": ([("max_hp", 55), ("armor", 10), ("regen", 1.2)],
                 ("🛡️ Demir İrade", {"max_hp": 95, "armor": 15})),
        "mid": ("⚔️ Savaş Ustalığı",
                [("physDmgFlat", 10), ("armor", 11), ("dmgMult", 0.07),
                 ("meleeRangeFlat", 22), ("lifesteal", 0.03)],
                ("🏰 Siper Duvarı", {"max_hp": 115, "armor": 20, "speed": -0.3})),
        "big": ("🩸 Cellat Çarkı",
                [("dmgMult", 0.08), ("physDmgFlat", 11), ("critDmg", 0.22),
                 ("armor", 11), ("max_hp", 60), ("physDmgMult", 0.08),
                 ("meleeRangeFlat", 24)],
                [("🪓 Cellat Gücü", {"dmgMult": 0.24, "physDmgFlat": 18, "attack_speed_bonus": -0.10}),
                 ("💀 Kan Davası", {"critDmg": 0.40, "physDmgMult": 0.14, "armor": -22})]),
        "keystone": ("🩸 Berserker Kalbi",
                     {"dmgMult": 0.45, "attack_speed_bonus": 0.12, "max_hp_pct": -25, "armor": -15}),
    },
    "sniper": {
        "lead": [("critChance", 0.04), ("bullet_speed", 2), ("dmgMult", 0.07)],
        "ident": ([("critChance", 0.04), ("critDmg", 0.20), ("pierce", 1)],
                  ("🦅 Kartal Gözü", {"critChance": 0.07, "critDmg": 0.45})),
        "surv": ([("max_hp", 50), ("speed", 0.3), ("dodgeChance", 0.03)],
                 ("🍃 Tetikte", {"speed": 0.5, "dodgeChance": 0.05})),
        "mid": ("🎯 Nişan Çarkı",
                [("critChance", 0.05), ("pierce", 1), ("bullet_speed", 2),
                 ("dmgMult", 0.07), ("critDmg", 0.20)],
                ("🏹 Delici Atış", {"pierce": 2, "dmgMult": 0.12})),
        "big": ("☄️ Balistik Çark",
                [("bounce", 1), ("pierce", 1), ("critDmg", 0.22), ("dmgMult", 0.08),
                 ("bullet_speed", 2), ("physDmgFlat", 10), ("critChance", 0.04)],
                [("☄️ Sekme Ustası", {"bounce": 2, "dmgMult": 0.10, "attack_speed_bonus": -0.15}),
                 ("🔭 Uzun Namlu", {"critDmg": 0.60, "bullet_speed": 3, "speed": -0.4})]),
        "keystone": ("☠️ Kafadan Vuruş",
                     {"critChance": 0.14, "critDmg": 0.80, "dmgMult": 0.20, "max_hp_pct": -20}),
    },
    "engineer": {
        "lead": [("turretDmg", 0.12), ("armor", 10), ("turretRate", 0.10)],
        "ident": ([("turretDmg", 0.14), ("turretRate", 0.11), ("turretMaxHp", 70)],
                  ("📡 Kapasite", {"turretLimit": 1, "turretDmg": 0.15})),
        "surv": ([("max_hp", 50), ("armor", 11), ("maxEnergyShield", 45)],
                 ("🧱 Sığınak", {"armor": 18, "maxEnergyShield": 70})),
        "mid": ("🔩 Atölye Çarkı",
                [("turretDmg", 0.14), ("turretMaxHp", 75), ("turretRate", 0.11),
                 ("turretRange", 35), ("armor", 10)],
                ("⚙️ Seri Üretim", {"turretCharges": 1, "turretRate": 0.15})),
        "big": ("🏭 Fabrika Çarkı",
                [("turretDmg", 0.15), ("turretRate", 0.12), ("turretMaxHp", 80),
                 ("turretRange", 40), ("fireDmgFlat", 6), ("armor", 11), ("turretCharges", 1)],
                [("🔧 Aşırı Yükleme", {"turretDmg": 0.40, "turretRate": 0.22, "turretMaxHp": -80}),
                 ("🛰️ Komuta Ağı", {"turretLimit": 1, "turretDmg": 0.20, "speed": -0.4})]),
        "keystone": ("☢️ Reaktör Taşması",
                     {"turretDmg": 0.70, "turretRate": 0.30, "turretLimit": 1, "max_hp_pct": -25}),
    },
    "beastmaster": {
        "lead": [("minionDamage", 0.12), ("minionMaxHpFlat", 70), ("regen", 1.2)],
        "ident": ([("minionDamage", 0.14), ("minionRate", 0.13), ("minionRange", 0.12)],
                  ("🐺 Alfa Sürüsü", {"minionDamage": 0.24, "minionCount": 1})),
        "surv": ([("max_hp", 55), ("regen", 1.4), ("armor", 10)],
                 ("🦴 Kalın Post", {"minionMaxHpFlat": 120, "minionArmor": 12})),
        "mid": ("🐾 Sürü Çarkı",
                [("minionDamage", 0.14), ("minionRate", 0.13), ("minionMaxHpFlat", 80),
                 ("minionArmor", 10), ("minionRange", 0.12)],
                ("🔗 Kan Bağı", {"minionDamage": 0.22, "minionRate": 0.15})),
        "big": ("🦁 Vahşi Çark",
                [("minionDamage", 0.15), ("minionRate", 0.14), ("minionMaxHpFlat", 85),
                 ("minionArmor", 11), ("minionPierce", 1), ("minionBounce", 1),
                 ("max_hp", 60)],
                [("👑 Sürü Lideri", {"minionCount": 1, "minionDamage": 0.25, "dmgMult": -0.15}),
                 ("🩸 Kan Sözleşmesi", {"minionDamage": 0.35, "minionRate": 0.18, "max_hp_pct": -15})]),
        "keystone": ("🐗 Vahşi Bağ",
                     {"minionDamage": 0.70, "minionCount": 1, "minionRate": 0.25, "dmgMult": -0.35}),
    },
    "bomber": {
        "lead": [("aoe_bonus", 0.10), ("fireDmgFlat", 5), ("max_hp", 50)],
        "ident": ([("aoe_bonus", 0.11), ("fireDmgFlat", 6), ("dmgMult", 0.07)],
                  ("🧷 Küme Mayın", {"aoe_bonus": 0.20, "dmgMult": 0.10})),
        "surv": ([("max_hp", 55), ("armor", 10), ("regen", 1.2)],
                 ("🥾 Sağlam Duruş", {"max_hp": 95, "armor": 14})),
        "mid": ("💣 Mayın Çarkı",
                [("aoe_bonus", 0.12), ("fireDmgFlat", 6), ("physDmgFlat", 9),
                 ("dmgMult", 0.07), ("poisonDps", 8)],
                ("🔥 Napalm", {"fireDmgFlat": 14, "aoe_bonus": 0.14})),
        "big": ("☢️ Yıkım Çarkı",
                [("aoe_bonus", 0.13), ("fireDmgFlat", 7), ("dmgMult", 0.08),
                 ("physDmgFlat", 10), ("fireDmgMult", 0.08), ("bossDmgMult", 0.06),
                 ("armorPen", 0.2)],
                [("💥 Termobarik", {"aoe_bonus": 0.28, "dmgMult": 0.15, "attack_speed_bonus": -0.18}),
                 ("🧨 Şarapnel", {"physDmgFlat": 20, "armorPen": 0.5, "aoe_bonus": -0.10})]),
        "keystone": ("☢️ Zincirleme Patlama",
                     {"aoe_bonus": 0.45, "dmgMult": 0.30, "fireDmgMult": 0.20, "max_hp_pct": -25}),
    },
    "alchemist": {
        "lead": [("dotDmgMult", 0.10), ("poisonDps", 8), ("aoe_bonus", 0.09)],
        "ident": ([("dotDmgMult", 0.11), ("poisonDps", 9), ("aoe_bonus", 0.10)],
                  ("🧪 Kaynayan Şişe", {"dotDmgMult": 0.20, "aoe_bonus": 0.15})),
        "surv": ([("max_hp", 50), ("regen", 1.3), ("maxEnergyShield", 45)],
                 ("🧫 Bağışıklık", {"max_hp": 85, "regen": 2.0})),
        "mid": ("☣️ Zehir Şişesi Çarkı",
                [("poisonDps", 10), ("dotDmgMult", 0.11), ("aoe_bonus", 0.10),
                 ("elementDmgMult", 0.08), ("magicFind", 0.08)],
                ("🌫️ Miyazma", {"poisonDps": 22, "aoe_bonus": 0.18})),
        "big": ("💀 Veba Çarkı",
                [("dotDmgMult", 0.12), ("poisonDps", 11), ("aoe_bonus", 0.11),
                 ("elementDmgMult", 0.09), ("goldGain", 0.10), ("max_hp", 55),
                 ("armorPen", 0.2)],
                [("☣️ Toksin Ustası", {"dotDmgMult": 0.30, "aoe_bonus": 0.18, "dmgMult": -0.12}),
                 ("🦠 Salgın", {"poisonDps": 30, "aoe_bonus": 0.22, "attack_speed_bonus": -0.15})]),
        "keystone": ("💀 Veba Bulutu",
                     {"dotDmgMult": 0.60, "poisonDps": 35, "aoe_bonus": 0.30, "dmgMult": -0.30}),
    },
    "sorcerer": {
        "lead": [("elementDmgMult", 0.09), ("maxEnergyShield", 45), ("fireDmgFlat", 4)],
        "ident": ([("elementDmgMult", 0.10), ("fireDmgFlat", 5), ("frostDmgFlat", 5)],
                  ("🌀 Gizemli Odak", {"elementDmgMult": 0.20, "dmgMult": 0.08})),
        "surv": ([("maxEnergyShield", 50), ("esRegen", 18), ("max_hp", 45)],
                 ("🧿 Büyü Kalkanı", {"maxEnergyShield": 85, "esRegen": 30})),
        "mid": ("🔮 Kadim Çark",
                [("elementDmgMult", 0.10), ("fireDmgFlat", 6), ("frostDmgFlat", 6),
                 ("maxEnergyShield", 45), ("esRegen", 16)],
                ("❄️ Kırağı Örtüsü", {"frostDmgMult": 0.18, "frostDmgFlat": 12})),
        "big": ("💥 Element Çarkı",
                [("elementDmgMult", 0.11), ("fireDmgFlat", 7), ("frostDmgFlat", 7),
                 ("fireDmgMult", 0.08), ("frostDmgMult", 0.08), ("maxEnergyShield", 50),
                 ("esRegen", 18)],
                [("🌋 Ateş Ustası", {"fireDmgMult": 0.25, "fireDmgFlat": 16, "frostDmgMult": -0.15}),
                 ("🧊 Buz Ustası", {"frostDmgMult": 0.25, "frostDmgFlat": 16, "fireDmgMult": -0.15})]),
        "keystone": ("💥 Element Taşması",
                     {"elementDmgMult": 0.55, "fireDmgMult": 0.20, "frostDmgMult": 0.20, "max_hp_pct": -30}),
    },
    "bloodwalker": {
        "lead": [("lifesteal", 0.03), ("dmgMult", 0.07), ("max_hp", 55)],
        "ident": ([("lifesteal", 0.03), ("dmgMult", 0.07), ("physDmgFlat", 9)],
                  ("🩸 Kızıl Zafer", {"lifesteal": 0.05, "dmgMult": 0.12})),
        "surv": ([("max_hp", 55), ("regen", 1.3), ("combatRegen", 1.0)],
                 ("🫀 Koyu Kan", {"max_hp": 95, "regen": 2.0})),
        "mid": ("🧛 Kan Çarkı",
                [("lifesteal", 0.03), ("max_hp", 55), ("dmgMult", 0.07),
                 ("physDmgFlat", 10), ("combatRegen", 1.0)],
                ("🍷 Kan Ziyafeti", {"lifesteal": 0.06, "max_hp": 80})),
        "big": ("🦇 Gece Çarkı",
                [("lifesteal", 0.03), ("dmgMult", 0.08), ("physDmgFlat", 11),
                 ("critDmg", 0.20), ("max_hp", 60), ("speed", 0.3), ("armorPen", 0.2)],
                [("🧛 Kan Susuzluğu", {"lifesteal": 0.08, "dmgMult": 0.20, "max_hp_pct": -15}),
                 ("🌑 Gece Avcısı", {"speed": 0.7, "critDmg": 0.35, "armor": -18})]),
        "keystone": ("🩸 Kızıl Ay",
                     {"lifesteal": 0.12, "dmgMult": 0.35, "attack_speed_bonus": 0.15, "max_hp_pct": -30}),
    },
    "ninja": {
        "lead": [("attack_speed_bonus", 0.06), ("speed", 0.3), ("critChance", 0.04)],
        "ident": ([("attack_speed_bonus", 0.06), ("speed", 0.3), ("critChance", 0.04)],
                  ("🌀 Bıçak Fırtınası", {"attack_speed_bonus": 0.12, "speed": 0.3})),
        "surv": ([("dodgeChance", 0.04), ("max_hp", 50), ("regen", 1.2)],
                 ("🌫️ Sis Adımı", {"dodgeChance": 0.07, "speed": 0.4})),
        "mid": ("🗡️ Suikast Çarkı",
                [("critChance", 0.05), ("attack_speed_bonus", 0.06), ("physDmgFlat", 9),
                 ("dodgeChance", 0.04), ("meleeRangeFlat", 20)],
                ("🌑 Gölge Vuruşu", {"critChance": 0.07, "critDmg": 0.35})),
        "big": ("🌪️ Fırtına Çarkı",
                [("attack_speed_bonus", 0.07), ("critChance", 0.04), ("speed", 0.3),
                 ("physDmgFlat", 10), ("critDmg", 0.22), ("bounce", 1),
                 ("meleeRangeFlat", 20)],
                [("⚡ Bin Kesik", {"attack_speed_bonus": 0.22, "dmgMult": 0.10, "physDmgFlat": -12}),
                 ("👻 Hayalet Dans", {"dodgeChance": 0.12, "speed": 0.6, "armor": -20})]),
        "keystone": ("🌘 Gölge Efendisi",
                     {"attack_speed_bonus": 0.30, "critChance": 0.12, "dodgeChance": 0.10,
                      "max_hp_pct": -30}),
    },
}

# İç çember geçitleri (arm=core)
GATE_STATS = [
    {"max_hp": 45}, {"armor": 8}, {"speed": 0.3}, {"regen": 1.0}, {"magnetRadius": 40},
    {"maxEnergyShield": 40}, {"dmgMult": 0.06}, {"lifesteal": 0.02}, {"attack_speed_bonus": 0.05},
]

# Köprü çarkları (komşu sınıflar arası) — jenerik güç, gerçek sapma
BRIDGE_WHEELS = [
    ("💪 Kudret", [("dmgMult", 0.07), ("physDmgFlat", 9), ("critChance", 0.04)],
     {"dmgMult": 0.16, "physDmgFlat": 12}),
    ("🛡️ Sur", [("armor", 11), ("max_hp", 55), ("regen", 1.2)],
     {"max_hp": 100, "armor": 16}),
    ("💨 Çeviklik", [("speed", 0.3), ("attack_speed_bonus", 0.06), ("dodgeChance", 0.04)],
     {"speed": 0.6, "attack_speed_bonus": 0.10}),
    ("🎯 Öldürücü", [("critChance", 0.05), ("critDmg", 0.22), ("armorPen", 0.2)],
     {"critChance": 0.07, "critDmg": 0.40}),
    ("🔷 Örtü", [("maxEnergyShield", 50), ("esRegen", 18), ("armor", 9)],
     {"maxEnergyShield": 90, "esRegen": 30}),
    ("🌟 Zenginlik", [("magicFind", 0.10), ("goldGain", 0.12), ("shopRarity", 1)],
     {"magicFind": 0.20, "goldGain": 0.20}),
    ("🔥 Öz", [("fireDmgFlat", 6), ("elementDmgMult", 0.09), ("aoe_bonus", 0.10)],
     {"elementDmgMult": 0.18, "aoe_bonus": 0.14}),
    ("🩸 Sülük", [("lifesteal", 0.03), ("max_hp", 55), ("combatRegen", 1.0)],
     {"lifesteal": 0.06, "regen": 2.0}),
    ("⚙️ Donanım", [("turretDmg", 0.12), ("minionDamage", 0.12), ("minionRange", 0.10)],
     {"turretDmg": 0.20, "minionDamage": 0.20}),
]

SPUR_FILLER = [{"max_hp": 50}, {"dmgMult": 0.06}, {"armor": 9}]


# ======================================================================
# İNŞA
# ======================================================================
nodes = {}
edges = set()


# Ağaç dairesel değil ELİPS yerleştirilir: ekran 16:9 ve UI ölçeği en dar
# kenara göre hesapladığı için kare bir ağaç tam ekranda solda/sağda kocaman
# boşluk bırakıyordu. Yalnızca MAKRO yerleşim (bant/sektör merkezleri) gerilir;
# çark içi ofsetler gerilmez, yoksa çarklar elips olur ve ezilmiş görünür.
X_STRETCH = 1.95


def macro(angle_deg, r):
    """Sektör/bant merkezi — yatayda gerilmiş (elips) konum."""
    a = math.radians(angle_deg)
    return [round(CX + r * math.cos(a) * X_STRETCH), round(CY + r * math.sin(a))]


def local(angle_deg, r, cx, cy):
    """Çark içi konum — DAİRESEL kalır (gerilme uygulanmaz)."""
    a = math.radians(angle_deg)
    return [round(cx + r * math.cos(a)), round(cy + r * math.sin(a))]


def add(nid, name, arm, ntype, stats, position):
    if nid in nodes:
        raise ValueError(f"yinelenen id: {nid}")
    nodes[nid] = {
        "id": nid, "name": name, "desc": desc_of(stats) if stats else "",
        "arm": arm, "type": ntype, "cat": cat_of(stats),
        "stats": stats, "pos": position,
    }
    if ntype == "start":
        nodes[nid]["start"] = True
    return nid


def link(a, b):
    if a != b:
        edges.add(tuple(sorted((a, b))))


def make_wheel(prefix, arm, center, wheel_r, minors, notables, start_angle=0.0):
    """Bir ÇARK üretir: düğümler bir çember üzerinde, halka şeklinde bağlı.

    Dönüş: (ids, entry_id, opposite_id)
      entry_id    : dış dünyanın bağlandığı düğüm (indeks 0)
      opposite_id : girişin tam karşısı — mahmuz/çıkış buradan devam eder,
                    yani çarkın yarısını yürümeden çıkış yok.

    notable'lar girişten uzağa yerleştirilir; güçlü düğüm "sırayla toplanan"
    bir şey değil, çarkı dolaşmanın ödülü olur (tasarım notu A).
    """
    n = len(minors) + len(notables)
    if n < 3:
        raise ValueError(f"{prefix}: çark en az 3 düğüm olmalı")

    if len(notables) == 1:
        notable_idx = {n // 2}
    else:
        notable_idx = {n // 3, (2 * n) // 3}

    ids = []
    mi = ni = 0
    for i in range(n):
        ang = start_angle + i * (360.0 / n)
        p = local(ang, wheel_r, center[0], center[1])
        nid = f"{prefix}_{i}"
        if i in notable_idx and ni < len(notables):
            nm, st = notables[ni]
            ni += 1
            add(nid, nm, arm, "notable", dict(st), p)
        else:
            stat, val = minors[mi % len(minors)]
            mi += 1
            add(nid, label_of(stat, val), arm, "minor", {stat: val}, p)
        ids.append(nid)

    for i in range(n):
        link(ids[i], ids[(i + 1) % n])
    return ids, ids[0], ids[n // 2]


# --- 1) ÇEKİRDEK: ortadaki boşluğun çevresinde savunma keystone'ları --------
core_spurs = []
for k, (nm, st) in enumerate(CORE_KEYSTONES):
    ang = -70 + k * 72
    kid = add(f"core_key_{k}", nm, "core", "keystone", dict(st), macro(ang, R_CORE_KEY))
    sstat = dict(CORE_SPUR_STATS[k])
    mid = add(f"core_spur_{k}", label_of(*next(iter(sstat.items()))),
              "core", "minor", sstat, macro(ang, R_CORE_MID))
    link(mid, kid)
    core_spurs.append((ang, mid))

# --- 2) İÇ ÇEMBER ---------------------------------------------------------
start_ids = {}
gates = []
for i, cls in enumerate(CLASSES):
    start_ids[cls] = add(f"start_{cls}", f"{cls.title()} Başlangıcı", cls, "start", {},
                         macro(-90 + i * 40, R_RING))

for i, cls in enumerate(CLASSES):
    nxt = CLASSES[(i + 1) % len(CLASSES)]
    ang = -90 + i * 40 + 20
    gid = add(f"junc_{cls}_{nxt}", "Geçit", "core", "minor", dict(GATE_STATS[i]),
              macro(ang, R_RING))
    link(start_ids[cls], gid)
    link(gid, start_ids[nxt])
    gates.append((ang, gid))

for ang, spur_mid in core_spurs:
    nearest = min(gates, key=lambda g: abs(((g[0] - ang + 180) % 360) - 180))
    link(nearest[1], spur_mid)

# --- 3) SINIF SEKTÖRLERİ --------------------------------------------------
mid_entry_of = {}
for i, cls in enumerate(CLASSES):
    a_i = -90 + i * 40
    ja, jr = JITTER_A[i], JITTER_R[i]
    th = THEMES[cls]

    s0, v0 = th["lead"][0]
    lead0 = add(f"{cls}_lead0", label_of(s0, v0), cls, "minor", {s0: v0},
                macro(a_i + ja * 0.2, R_LEAD0))
    link(start_ids[cls], lead0)

    # Başlangıç çevresi: KİMLİK + HAYATTA KALMA küçük çarkları (#9/#10)
    # Yan sapma 11°: sınıflar 40° arayla, ±15° kullanılınca KOMŞU sınıfın
    # çarkıyla arada 10° (≈199 px) kalıyor ve iki çark (2×126 px yarıçap)
    # üst üste biniyordu. 11° -> komşuyla 18° (≈358 px). Ayrıca iki çark
    # farklı yarıçapa kaydırıldı, böylece kendi aralarında da rahatlıyorlar.
    for side, key in ((-1, "ident"), (+1, "surv")):
        minors, notable = th[key]
        center = macro(a_i + side * 11 + ja * 0.25,
                       R_SMALL + side * 55 + jr * 0.25)
        _, entry, _ = make_wheel(f"{cls}_{key}", cls, center, WHEEL_R_SMALL,
                                 minors, [notable], start_angle=a_i + 180)
        link(lead0, entry)

    s1, v1 = th["lead"][1]
    lead1 = add(f"{cls}_lead1", label_of(s1, v1), cls, "minor", {s1: v1},
                macro(a_i + ja * 0.4, R_LEAD1 + jr * 0.3))
    link(lead0, lead1)

    # ORTA ÇARK — ana yol buradan geçer
    _, mid_minors, mid_notable = th["mid"]
    mid_ids, mid_entry, mid_exit = make_wheel(
        f"{cls}_mid", cls, macro(a_i + ja, R_MID + jr), WHEEL_R_MID,
        mid_minors, [mid_notable], start_angle=a_i + 180)
    link(lead1, mid_entry)
    mid_entry_of[cls] = mid_entry

    s2, v2 = th["lead"][2]
    lead2 = add(f"{cls}_lead2", label_of(s2, v2), cls, "minor", {s2: v2},
                macro(a_i + ja * 0.5, R_LEAD2 + jr * 0.5))
    link(mid_exit, lead2)

    # UZMANLIK ÇARKI (#7) — lead2'den yana dallanır
    sp_name, sp_minors, sp_notable = SPEC_WHEELS[cls]
    _, sp_entry, _ = make_wheel(
        f"{cls}_spec", cls, macro(a_i + 17 + ja * 0.3, R_SPEC + jr * 0.4),
        WHEEL_R_SPEC, sp_minors, [sp_notable], start_angle=a_i + 180)
    link(lead2, sp_entry)

    # BÜYÜK ÇARK — sınıfın imza çarkı
    _, big_minors, big_notables = th["big"]
    _, big_entry, big_exit = make_wheel(
        f"{cls}_big", cls, macro(a_i - ja * 0.5, R_BIG + jr), WHEEL_R_BIG,
        big_minors, big_notables, start_angle=a_i + 180)
    link(lead2, big_entry)

    # KEYSTONE MAHMUZU — büyük çarkın giriş KARŞISINDAN, teğetsel bağ yok
    prev = big_exit
    for k, r in enumerate(R_SPUR):
        st = dict(SPUR_FILLER[k])
        sid = add(f"{cls}_spur{k}", label_of(*next(iter(st.items()))), cls, "minor", st,
                  macro(a_i - ja * 0.3, r + jr * 0.4))
        link(prev, sid)
        prev = sid
    kname, kstats = th["keystone"]
    link(prev, add(f"{cls}_keystone", kname, cls, "keystone", dict(kstats),
                   macro(a_i - ja * 0.3, R_KEYSTONE + jr * 0.4)))

# --- 4) KÖPRÜ ÇARKLARI: sınıflar arası TEK pahalı geçiş --------------------
for i, cls in enumerate(CLASSES):
    nxt = CLASSES[(i + 1) % len(CLASSES)]
    a_b = -90 + i * 40 + 20
    bname, bminors, bnotable = BRIDGE_WHEELS[i]
    _, entry, opposite = make_wheel(
        f"bridge_{cls}_{nxt}", "core", macro(a_b, R_MID + JITTER_R[i] * 0.3),
        WHEEL_R_BRIDGE, bminors, [(bname, bnotable)], start_angle=a_b + 180)
    link(mid_entry_of[cls], entry)
    link(opposite, mid_entry_of[nxt])

# --- ÇIKTI ----------------------------------------------------------------
for nid in nodes:
    nodes[nid]["connects"] = []
for a, b in sorted(edges):
    nodes[a]["connects"].append(b)

out = list(nodes.values())
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
    f.write("\n")

by_type, by_cat = {}, {}
for n in out:
    by_type[n["type"]] = by_type.get(n["type"], 0) + 1
    by_cat[n["cat"]] = by_cat.get(n["cat"], 0) + 1
print(f"{OUT}: {len(out)} düğüm, {len(edges)} kenar")
print("  tipler:     ", ", ".join(f"{k}={v}" for k, v in sorted(by_type.items())))
print("  kategoriler:", ", ".join(f"{k}={v}" for k, v in sorted(by_cat.items())))
