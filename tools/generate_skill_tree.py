"""Generate the connected passive tree, preserving the published branch IDs.
Shared bridges begin at mastery, never at class starts.
"""
import json
import math
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "skill_tree.json")

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
    return f"%{abs(v) * 100:g}"


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


STAT_LABEL.update({
    "aoe": lambda v: f"{_sg(v)}{_pct(v)} Alan Etkisi",
    "cooldownReduction": lambda v: f"{_sg(v)}{_pct(v)} Yetenek Bekleme Azaltma",
    "killComboDmg": lambda v: f"Kombo başına {_sg(v)}{_pct(v)} Hasar",
    "lowHpExec": lambda v: f"%{abs(v) * 100:g} canın altında İnfaz",
    "minionMaxHp": lambda v: f"{_sg(v)}{_pct(v)} Minyon Canı",
    "minionProjectileCount": lambda v: f"{_sg(v)}{_flat(v)} Minyon Mermisi",
})
STAT_CAT.update({"aoe": "dot", "cooldownReduction": "utility",
                 "killComboDmg": "damage", "lowHpExec": "damage",
                 "minionMaxHp": "minion", "minionProjectileCount": "minion"})

THEMES = {'warrior': {'minor': [('Warrior Gelişimi 1', {'armor': 5, 'physDmgFlat': 10}),
                       ('Warrior Gelişimi 2', {'physDmgFlat': 10, 'lifesteal': 0.02}),
                       ('Warrior Gelişimi 3', {'lifesteal': 0.02, 'regen': 1.5}),
                       ('Warrior Gelişimi 4', {'regen': 1.5, 'meleeRangeFlat': 15}),
                       ('Warrior Gelişimi 5', {'meleeRangeFlat': 15, 'max_hp_pct': 3})],
             'mastery': ('⚜️ Warrior Ustalığı', {'armor': 10, 'physDmgFlat': 20, 'lifesteal': 0.04}),
             'keystones': [('🛡️ Yenilmez', {'max_hp_pct': 20, 'armor': 50, 'speed': -0.5}),
                           ('⚔️ Savaş Tanrısı', {'physDmgMult': 0.2, 'lifesteal': 0.1})]},
 'sniper': {'minor': [('Sniper Gelişimi 1', {'critChance': 0.03, 'pierce': 1}),
                      ('Sniper Gelişimi 2', {'pierce': 1, 'bounce': 1}),
                      ('Sniper Gelişimi 3', {'bounce': 1, 'attack_speed_bonus': 0.04}),
                      ('Sniper Gelişimi 4', {'attack_speed_bonus': 0.04, 'speed': 0.2}),
                      ('Sniper Gelişimi 5', {'speed': 0.2, 'dmgMult': 0.05})],
            'mastery': ('⚜️ Sniper Ustalığı', {'critChance': 0.06, 'pierce': 2, 'bounce': 2}),
            'keystones': [('🎯 Keskin Nişancı', {'dmgMult': 0.3, 'critChance': 0.15, 'armor': -30}),
                          ('🦅 Avcı Kuş', {'bounce': 2, 'pierce': 2})]},
 'engineer': {'minor': [('Engineer Gelişimi 1', {'turretMaxHp': 30, 'armor': 5}),
                        ('Engineer Gelişimi 2', {'armor': 5, 'cooldownReduction': 0.04}),
                        ('Engineer Gelişimi 3', {'cooldownReduction': 0.04, 'turretLimit': 1}),
                        ('Engineer Gelişimi 4', {'turretLimit': 1, 'turretRate': 0.05}),
                        ('Engineer Gelişimi 5', {'turretRate': 0.05, 'turretDmg': 0.05})],
              'mastery': ('⚜️ Engineer Ustalığı',
                          {'turretMaxHp': 60, 'armor': 10, 'cooldownReduction': 0.08}),
              'keystones': [('⚙️ Makine Mühendisi', {'turretLimit': 2, 'turretDmg': 0.2}),
                            ('🔩 Çelik Ağ', {'turretMaxHp': 200, 'cooldownReduction': 0.2})]},
 'beastmaster': {'minor': [('Beastmaster Gelişimi 1', {'minionMaxHp': 0.1, 'minionRate': 0.05}),
                           ('Beastmaster Gelişimi 2', {'minionRate': 0.05, 'minionArmor': 5}),
                           ('Beastmaster Gelişimi 3', {'minionArmor': 5, 'speed': 0.3}),
                           ('Beastmaster Gelişimi 4', {'speed': 0.3, 'max_hp': 20}),
                           ('Beastmaster Gelişimi 5', {'max_hp': 20, 'minionDamage': 0.05})],
                 'mastery': ('⚜️ Beastmaster Ustalığı',
                             {'minionMaxHp': 0.2, 'minionRate': 0.1, 'minionArmor': 10}),
                 'keystones': [('🐺 Alfa Kurdu', {'minionDamage': 0.3, 'minionMaxHp': 0.3}),
                               ('🦅 Vahşi Sürü', {'minionProjectileCount': 2, 'minionRate': 0.15})]},
 'bomber': {'minor': [('Bomber Gelişimi 1', {'dmgMult': 0.05, 'cooldownReduction': 0.05}),
                      ('Bomber Gelişimi 2', {'cooldownReduction': 0.05, 'magnetRadius': 20}),
                      ('Bomber Gelişimi 3', {'magnetRadius': 20, 'fireDmgMult': 0.05}),
                      ('Bomber Gelişimi 4', {'fireDmgMult': 0.05, 'aoe': 0.05}),
                      ('Bomber Gelişimi 5', {'aoe': 0.05, 'dmgMult': 0.05})],
            'mastery': ('⚜️ Bomber Ustalığı', {'dmgMult': 0.1, 'cooldownReduction': 0.1, 'magnetRadius': 40}),
            'keystones': [('💣 Patlayıcı Uzmanı', {'aoe': 0.4, 'fireDmgMult': 0.2}),
                          ('🔥 Zincirleme Reaksiyon', {'dmgMult': 0.3, 'cooldownReduction': 0.2})]},
 'alchemist': {'minor': [('Alchemist Gelişimi 1', {'aoe': 0.04, 'speed': 0.3}),
                         ('Alchemist Gelişimi 2', {'speed': 0.3, 'dodgeChance': 0.02}),
                         ('Alchemist Gelişimi 3', {'dodgeChance': 0.02, 'maxEnergyShield': 20}),
                         ('Alchemist Gelişimi 4', {'maxEnergyShield': 20, 'dotDmgMult': 0.05}),
                         ('Alchemist Gelişimi 5', {'dotDmgMult': 0.05, 'aoe': 0.04})],
               'mastery': ('⚜️ Alchemist Ustalığı', {'aoe': 0.08, 'speed': 0.6, 'dodgeChance': 0.04}),
               'keystones': [('🧪 Zehir Ustası', {'dotDmgMult': 0.4, 'aoe': 0.15}),
                             ('⚗️ Kimyasal Kalkan', {'maxEnergyShield': 100, 'dodgeChance': 0.15})]},
 'sorcerer': {'minor': [('Sorcerer Gelişimi 1', {'maxEnergyShield': 30, 'esRegen': 5}),
                        ('Sorcerer Gelişimi 2', {'esRegen': 5, 'cooldownReduction': 0.04}),
                        ('Sorcerer Gelişimi 3', {'cooldownReduction': 0.04, 'pierce': 1}),
                        ('Sorcerer Gelişimi 4', {'pierce': 1, 'magicFind': 0.05}),
                        ('Sorcerer Gelişimi 5', {'magicFind': 0.05, 'elementDmgMult': 0.06})],
              'mastery': ('⚜️ Sorcerer Ustalığı',
                          {'maxEnergyShield': 60, 'esRegen': 10, 'cooldownReduction': 0.08}),
              'keystones': [('🔮 Element Efendisi', {'elementDmgMult': 0.4, 'magicFind': 1.0}),
                            ('✨ Astral Kalkan', {'maxEnergyShield': 150, 'esRegen': 50})]},
 'bloodwalker': {'minor': [('Bloodwalker Gelişimi 1', {'max_hp_pct': 4, 'meleeRangeFlat': 15}),
                           ('Bloodwalker Gelişimi 2', {'meleeRangeFlat': 15, 'physDmgMult': 0.05}),
                           ('Bloodwalker Gelişimi 3', {'physDmgMult': 0.05, 'lowHpExec': 0.05}),
                           ('Bloodwalker Gelişimi 4', {'lowHpExec': 0.05, 'lifesteal': 0.03}),
                           ('Bloodwalker Gelişimi 5', {'lifesteal': 0.03, 'max_hp_pct': 4})],
                 'mastery': ('⚜️ Bloodwalker Ustalığı',
                             {'max_hp_pct': 8, 'meleeRangeFlat': 30, 'physDmgMult': 0.1}),
                 'keystones': [('🩸 Kan Banyosu', {'lifesteal': 0.15, 'max_hp_pct': 30}),
                               ('💀 Ölümcül Hasat', {'physDmgMult': 0.3, 'lowHpExec': 0.15})]},
 'ninja': {'minor': [('Ninja Gelişimi 1', {'dodgeChance': 0.03, 'speed': 0.4}),
                     ('Ninja Gelişimi 2', {'speed': 0.4, 'critChance': 0.04}),
                     ('Ninja Gelişimi 3', {'critChance': 0.04, 'bossDmgMult': 0.05}),
                     ('Ninja Gelişimi 4', {'bossDmgMult': 0.05, 'killComboDmg': 0.02}),
                     ('Ninja Gelişimi 5', {'killComboDmg': 0.02, 'attack_speed_bonus': 0.05})],
           'mastery': ('⚜️ Ninja Ustalığı', {'dodgeChance': 0.06, 'speed': 0.8, 'critChance': 0.08}),
           'keystones': [('🥷 Gölgelerin İçinden', {'dodgeChance': 0.2, 'speed': 1.0}),
                         ('🗡️ Suikastçi', {'bossDmgMult': 0.3, 'critChance': 0.2})]}}

CLASSES = list(THEMES)
# Crossing a bridge requires four shared nodes after reaching class mastery.
BRIDGES = [
    ("Keskin Nişan", [{"physDmgMult": .04}, {"critChance": .02},
                      {"attack_speed_bonus": .04}, {"max_hp": 20}]),
    ("Mekanik Odak", [{"dmgMult": .04}, {"speed": .15},
                      {"maxEnergyShield": 15}, {"critChance": .02}]),
    ("Komuta Bağı", [{"minionDamage": .04, "turretDmg": .04},
                     {"minionRange": .10, "turretRange": 20},
                     {"minionRate": .04, "turretRate": .04},
                     {"minionPierce": 1, "minionBounce": 1, "turretMaxHp": 25}]),
    ("Saha Kontrolü", [{"aoe_bonus": .04}, {"dmgMult": .04},
                       {"max_hp": 20}, {"regen": .4}]),
    ("Yanıcı Karışım", [{"dotDmgMult": .04}, {"aoe_bonus": .04},
                        {"fireDmgMult": .04}, {"regen": .4}]),
    ("Element Akışı", [{"elementDmgMult": .04}, {"dotDmgMult": .04},
                       {"maxEnergyShield": 15}, {"esRegen": 3}]),
    ("Kan ve Mana", [{"lifesteal": .01}, {"dmgMult": .04},
                     {"regen": .4}, {"max_hp": 20}]),
    ("Kanlı Çeviklik", [{"physDmgMult": .04}, {"attack_speed_bonus": .04},
                        {"critChance": .02}, {"lifesteal": .01}]),
    ("Çelik Adımlar", [{"meleeRangeFlat": 10}, {"dodgeChance": .02},
                       {"physDmgMult": .04}, {"speed": .15}]),
]
PENALTIES = {
    "warrior_keystone_2": {"max_hp_pct": -15},
    "sniper_keystone_2": {"attack_speed_bonus": -.12},
    "engineer_keystone_1": {"turretMaxHp": -40},
    "engineer_keystone_2": {"turretDmg": -.15},
    "beastmaster_keystone_1": {"minionRate": -.12},
    "beastmaster_keystone_2": {"minionDamage": -.15},
    "bomber_keystone_1": {"attack_speed_bonus": -.12},
    "bomber_keystone_2": {"max_hp_pct": -15},
    "alchemist_keystone_1": {"max_hp_pct": -10},
    "alchemist_keystone_2": {"armor": -25, "max_hp_pct": -15},
    "sorcerer_keystone_1": {"max_hp_pct": -15},
    "sorcerer_keystone_2": {"elementDmgMult": -.15},
    "bloodwalker_keystone_1": {"dmgMult": -.15},
    "bloodwalker_keystone_2": {"max_hp_pct": -15},
    "ninja_keystone_1": {"max_hp_pct": -15},
    "ninja_keystone_2": {"armor": -20},
}


# Each class offers three distinct five-point commitments from its first point.
EARLY_ROUTES = {
 "warrior": [("Düellocu", [{"physDmgFlat":3},{"attack_speed_bonus":.05},{"critChance":.025},{"physDmgMult":.06},{"armorPen":3}]),
             ("Demir Muhafız", [{"armor":5},{"max_hp":15},{"regen":.5},{"max_hp_pct":4},{"armor":7}]),
             ("Cephe Kırıcı", [{"meleeRangeFlat":12},{"aoe_bonus":.06},{"speed":.2},{"lifesteal":.015},{"meleeRangeFlat":15}])],
 "ninja": [("Suikast", [{"critChance":.03},{"physDmgFlat":2},{"critDmg":.10},{"bossDmgMult":.06},{"attack_speed_bonus":.05}]),
           ("Gölge Adımı", [{"dodgeChance":.025},{"speed":.25},{"max_hp":12},{"dodgeChance":.025},{"regen":.4}]),
           ("Akıcı Bıçak", [{"attack_speed_bonus":.05},{"meleeRangeFlat":10},{"killComboDmg":.01},{"speed":.2},{"physDmgMult":.05}])],
 "sniper": [("Tek Atış", [{"physDmgFlat":3},{"critChance":.03},{"armorPen":3},{"bossDmgMult":.06},{"critDmg":.1}]),
            ("Gezgin Avcı", [{"speed":.25},{"dodgeChance":.025},{"max_hp":15},{"regen":.4},{"speed":.2}]),
            ("Çapraz Ateş", [{"bullet_speed":.5},{"pierce":1},{"attack_speed_bonus":.04},{"bounce":1},{"dmgMult":.04}])],
 "sorcerer": [("Element Akışı", [{"fireDmgFlat":3,"frostDmgFlat":3},{"elementDmgMult":.05},{"critChance":.025},{"elementDmgMult":.06},{"attack_speed_bonus":.04}]),
              ("Astral Siper", [{"maxEnergyShield":20},{"esRegen":3},{"max_hp":12},{"maxEnergyShield":25},{"esRegen":4}]),
              ("Büyü Dokuma", [{"dotDmgMult":.05},{"aoe_bonus":.05},{"speed":.2},{"cooldownReduction":.04},{"pierce":1}])],
 "alchemist": [("Aşındırıcı", [{"poisonDps":3},{"dotDmgMult":.06},{"poisonDps":3},{"dotDmgMult":.06},{"dmgMult":.04}]),
               ("Simyasal Siper", [{"maxEnergyShield":18},{"regen":.5},{"max_hp":15},{"dodgeChance":.025},{"maxEnergyShield":20}]),
               ("Dağıtıcı", [{"aoe_bonus":.06},{"speed":.2},{"attack_speed_bonus":.04},{"aoe_bonus":.06},{"cooldownReduction":.04}])],
 "bomber": [("Yıkım", [{"dmgMult":.05},{"fireDmgMult":.05},{"physDmgFlat":3},{"critChance":.025},{"dmgMult":.05}]),
            ("Siperci", [{"armor":5},{"max_hp":15},{"regen":.5},{"max_hp_pct":4},{"armor":7}]),
            ("Saha Kontrolü", [{"aoe_bonus":.06},{"cooldownReduction":.04},{"speed":.2},{"aoe_bonus":.06},{"attack_speed_bonus":.04}])],
 "bloodwalker": [("Kızıl Hasat", [{"physDmgFlat":3},{"physDmgMult":.05},{"critChance":.025},{"lowHpExec":.025},{"physDmgMult":.06}]),
                 ("Kan Sığınağı", [{"max_hp":15},{"lifesteal":.015},{"regen":.5},{"max_hp_pct":4},{"armor":5}]),
                 ("Kan Akışı", [{"meleeRangeFlat":12},{"attack_speed_bonus":.04},{"speed":.2},{"lifesteal":.015},{"aoe_bonus":.06}])],
 "engineer": [("Alev Ustası", [{"fireDmgFlat":3},{"dmgMult":.04},{"fireDmgMult":.05},{"attack_speed_bonus":.04},{"aoe_bonus":.05}]),
              ("Tahkimat", [{"turretMaxHp":20},{"armor":5},{"max_hp":15},{"turretMaxHp":25},{"regen":.5}]),
              ("Otomasyon", [{"turretDmg":.05},{"turretRate":.05},{"turretRange":25},{"cooldownReduction":.04},{"turretDmg":.06}])],
 "beastmaster": [("Sürü Pençesi", [{"minionDamage":.05},{"minionPhysDmgFlat":2},{"minionCrit":.03},{"minionDamage":.06},{"minionRate":.05}]),
                 ("Sürü Sığınağı", [{"minionMaxHp":.08},{"max_hp":15},{"minionArmor":5},{"regen":.5},{"minionMaxHp":.10}]),
                 ("Av Komutası", [{"minionRate":.05},{"minionRange":.08},{"speed":.2},{"minionPierce":1},{"cooldownReduction":.04}])]
}
STAT_LABEL.update({"minionPhysDmgFlat":lambda v:f"{_sg(v)}{_flat(v)} Minyon Fiziksel Hasarı",
                   "minionCrit":lambda v:f"{_sg(v)}{_pct(v)} Minyon Kritik Şansı"})
STAT_CAT.update({"minionPhysDmgFlat":"minion","minionCrit":"minion"})

def open_initial_routes(nodes):
    by_id={n["id"]:n for n in nodes}
    for i,cls in enumerate(CLASSES):
        angle=i*2*math.pi/len(CLASSES)
        ux,uy=math.cos(angle),math.sin(angle)
        vx,vy=-uy,ux
        def pos(radius,lateral=0):
            return [round(3000+ux*radius+vx*lateral),round(3000+uy*radius+vy*lateral)]
        by_id["start_"+cls]["pos"]=pos(500)
        mastery=by_id[cls+"_notable_core"]
        mastery["pos"]=pos(1500)
        for lane,(name,values) in enumerate(EARLY_ROUTES[cls]):
            previous="start_"+cls
            for j,stats in enumerate(values,1):
                nid=f"{cls}_main_{j}" if lane==0 else f"{cls}_early{lane}_{j}"
                lateral=(0 if lane==0 else (-1 if lane==1 else 1))*(75+j*25)
                node={"id":nid,"name":name+f" {j}","desc":desc_of(stats),"arm":cls,
                      "type":"minor","cat":cat_of(stats),"stats":dict(stats),
                      "pos":pos(500+j*160,lateral),"connects":[previous],"route":name}
                if lane==0:
                    by_id[nid].update(node)
                else:
                    nodes.append(node)
                    by_id[nid]=node
                previous=nid
            if lane:
                nid=f"{cls}_early{lane}_notable"
                stats=({"armor":8,"max_hp":15} if lane==1 else {"speed":.2,"cooldownReduction":.04})
                node={"id":nid,"name":name+" Ustalığı","desc":desc_of(stats),"arm":cls,
                      "type":"notable","cat":cat_of(stats),"stats":stats,
                      "pos":pos(1450,-260 if lane==1 else 260),
                      "connects":[previous,f"{cls}_path{lane}_1"],"route":name}
                nodes.append(node)
                by_id[nid]=node
        # A route can pivot after three spent points, without skipping depth.
        for lane in (1,2):
            by_id[f"{cls}_early{lane}_3"]["connects"].append(f"{cls}_main_3")
        for branch in (1,2):
            sign=-1 if branch==1 else 1
            for j in range(1,6):
                by_id[f"{cls}_path{branch}_{j}"]["pos"]=pos(1500+j*145,sign*(80+j*40))
            by_id[f"{cls}_keystone_{branch}"]["pos"]=pos(2370,sign*320)
    # Same shared-bridge investment as before, between the mastery junctions.
    for i,cls in enumerate(CLASSES):
        nxt=CLASSES[(i+1)%len(CLASSES)]
        for j in range(1,5):
            a=(i+j/5)*2*math.pi/len(CLASSES)
            by_id[f"bridge_{cls}_{nxt}_{j}"]["pos"]=[round(3000+math.cos(a)*1500),round(3000+math.sin(a)*1500)]
    return nodes

def generate():
    nodes = []
    by_id = {}
    def add(nid, name, arm, typ, stats, pos, previous=None):
        node = {"id": nid, "name": name, "desc": desc_of(stats), "arm": arm,
                "type": typ, "cat": cat_of(stats), "stats": dict(stats),
                "pos": [round(pos[0]), round(pos[1])],
                "connects": [previous] if previous else []}
        if typ == "start":
            node["start"] = True
        nodes.append(node)
        by_id[nid] = node
        return nid
    def radial(angle, radius):
        return (3000 + math.cos(angle) * radius, 3000 + math.sin(angle) * radius)
    for i, cls in enumerate(CLASSES):
        angle = i * 2 * math.pi / len(CLASSES)
        theme = THEMES[cls]
        prev = add("start_" + cls, cls.title() + " Başlangıcı", cls, "start", {},
                   radial(angle, 300))
        for j, (name, stats) in enumerate(theme["minor"], 1):
            prev = add(f"{cls}_main_{j}", name, cls, "minor", stats,
                       radial(angle, 300 + j * 150), prev)
        name, stats = theme["mastery"]
        mastery = add(cls + "_notable_core", name, cls, "notable", stats,
                      radial(angle, 1200), prev)
        for branch in (1, 2):
            prev = mastery
            branch_angle = angle + (-.4 if branch == 1 else .4)
            ox, oy = radial(angle, 1200)
            for j, (name, stats) in enumerate(theme["minor"], 1):
                # The third node on one branch is an additional notable,
                # separated from mastery by two travel nodes.
                typ = "notable" if branch == 1 and j == 3 else "minor"
                values = {k: round(v * 1.5, 3) for k, v in stats.items()} if typ == "notable" else stats
                name = cls.title() + " İleri Ustalığı" if typ == "notable" else name
                prev = add(f"{cls}_path{branch}_{j}", name, cls, typ, values,
                           (ox + math.cos(branch_angle) * j * 150,
                            oy + math.sin(branch_angle) * j * 150), prev)
            name, stats = theme["keystones"][branch - 1]
            stats = dict(stats)
            stats.update(PENALTIES.get(f"{cls}_keystone_{branch}", {}))
            add(f"{cls}_keystone_{branch}", name, cls, "keystone", stats,
                (ox + math.cos(branch_angle) * 900,
                 oy + math.sin(branch_angle) * 900), prev)
    # Shared travel nodes follow an arc between mastery points. No start shortcuts.
    for i, cls in enumerate(CLASSES):
        nxt = CLASSES[(i + 1) % len(CLASSES)]
        name, stats_list = BRIDGES[i]
        prev = cls + "_notable_core"
        for j, stats in enumerate(stats_list, 1):
            angle = (i + j / 5) * 2 * math.pi / len(CLASSES)
            prev = add(f"bridge_{cls}_{nxt}_{j}", name + f" {j}", "core", "minor",
                       stats, radial(angle, 1200), prev)
        by_id[nxt + "_notable_core"]["connects"].append(prev)
    # Economy is a side investment, available after reaching the shared bridge.
    prev = "bridge_warrior_sniper_2"
    for j, stats in enumerate(({"goldGain": .04}, {"shopRarity": .04},
                               {"magicFind": .08, "magnetRadius": 20}), 1):
        prev = add(f"shared_trade_{j}", "Gezgin Tüccar " + str(j), "core",
                   "notable" if j == 3 else "minor", stats,
                   radial(.24, 1200 - j * 140), prev)
    add("core_fallback", "Evrensel Merkez", "core", "start", {},
        (3000, 3000), "shared_trade_3")
    return open_initial_routes(nodes)

if __name__ == "__main__":
    out = generate()
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(out, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"Yetenek ağacı: {len(out)} düğüm.")
