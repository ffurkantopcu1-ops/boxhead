# -*- coding: utf-8 -*-
"""data/skill_tree.json (ANA pasif ağaç) üretir — Path of Exile'vari BÜYÜK çark.

Yapı:
- Merkez ÇEMBER: 9 sınıf başlangıcı + aralarında 9 paylaşımlı "junction" (jenerik).
- Her sınıf DIŞA doğru 3 raylı (L/C/R) bir sektör açar; 6 halka derinliğinde.
- Komşu sınıflar arasında 6 halkalı "köprü" rayı (jenerik) — sınıflar arası geçiş.
- Radyal + teğetsel + sınıflar-arası bağlar => çok yollu, geniş bir web.

Çalıştır (repo kökünden):
    python tools/generate_skill_tree.py
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'skill_tree.json')

CX, CY = 1500, 1300
R0 = 240                                   # iç çember yarıçapı
RINGS = [380, 540, 700, 860, 1020, 1180]   # dış halkalar (6 derinlik)
RAIL_OFF = 13                              # L/C/R ray açı sapması (derece)
BRIDGE_OFF = 20                            # köprü açısı (iki sınıf ortası)

# Sınıf sırası = çember üzerindeki açısal sıra (40°'lik dilimler)
CLASSES = ["warrior", "sniper", "engineer", "beastmaster", "bomber",
           "alchemist", "sorcerer", "bloodwalker", "ninja"]

# Sınıf temaları: minör havuz (dönüşümlü kullanılır) + 2 notable + 1 keystone
THEMES = {
    "warrior": {
        "minors": [("armor", 8), ("max_hp", 45), ("physDmgFlat", 8), ("dmgMult", 0.08), ("meleeRangeFlat", 20)],
        "notables": [("🏰 Siper", {"max_hp": 80, "armor": 12}), ("🪓 Cellat Gücü", {"dmgMult": 0.15, "physDmgFlat": 10})],
        "keystone": ("🩸 Berserker Kalbi", {"dmgMult": 0.30, "max_hp_pct": -15}),
    },
    "ninja": {
        "minors": [("dodgeChance", 0.04), ("attack_speed_bonus", 0.06), ("speed", 0.3), ("critChance", 0.04), ("physDmgFlat", 6)],
        "notables": [("🌀 Bıçak Fırtınası", {"attack_speed_bonus": 0.10, "speed": 0.2}), ("🌑 Gölge Vuruşu", {"critChance": 0.06, "dodgeChance": 0.05})],
        "keystone": ("👻 Hayalet Dans", {"dodgeChance": 0.15, "attack_speed_bonus": 0.15, "max_hp_pct": -15}),
    },
    "bloodwalker": {
        "minors": [("lifesteal", 0.03), ("dmgMult", 0.08), ("max_hp", 45), ("regen", 1.0), ("physDmgFlat", 8)],
        "notables": [("🩸 Kızıl Zafer", {"lifesteal": 0.05, "dmgMult": 0.10}), ("🫀 Koyu Kan", {"max_hp": 80, "regen": 1.5})],
        "keystone": ("🧛 Kan Susuzluğu", {"lifesteal": 0.08, "dmgMult": 0.20, "max_hp_pct": -15}),
    },
    "sniper": {
        "minors": [("critChance", 0.05), ("pierce", 1), ("dmgMult", 0.08), ("critDmg", 0.2), ("bullet_speed", 1)],
        "notables": [("🦅 Kartal Gözü", {"critChance": 0.06, "critDmg": 0.5}), ("🏹 Delici Atış", {"pierce": 1, "dmgMult": 0.10})],
        "keystone": ("☠️ Kafadan Vuruş", {"critChance": 0.10, "dmgMult": 0.20, "max_hp_pct": -10}),
    },
    "sorcerer": {
        "minors": [("elementDmgMult", 0.10), ("fireDmgFlat", 3), ("frostDmgFlat", 3), ("dmgMult", 0.08), ("max_hp", 40)],
        "notables": [("🌀 Gizemli Odak", {"elementDmgMult": 0.20, "dmgMult": 0.10}), ("🧿 Büyü Kalkanı", {"max_hp": 60, "elementDmgMult": 0.10})],
        "keystone": ("💥 Element Taşması", {"elementDmgMult": 0.5, "max_hp_pct": -20}),
    },
    "alchemist": {
        "minors": [("dotDmgMult", 0.12), ("aoe_bonus", 0.10), ("poisonDps", 8), ("dmgMult", 0.08), ("elementDmgMult", 0.08)],
        "notables": [("☣️ Toksin Ustası", {"dotDmgMult": 0.25, "aoe_bonus": 0.15}), ("🌫️ Yayılım", {"aoe_bonus": 0.20, "dmgMult": 0.08})],
        "keystone": ("💀 Veba Bulutu", {"dotDmgMult": 0.5, "dmgMult": -0.15}),
    },
    "bomber": {
        "minors": [("aoe_bonus", 0.12), ("physDmgFlat", 8), ("dmgMult", 0.08), ("fireDmgFlat", 4), ("pierce", 1)],
        "notables": [("🧷 Küme Mayın", {"aoe_bonus": 0.20, "dmgMult": 0.10}), ("🔥 Napalm", {"fireDmgFlat": 10, "aoe_bonus": 0.10})],
        "keystone": ("☢️ Zincirleme Patlama", {"aoe_bonus": 0.30, "dmgMult": 0.25, "max_hp_pct": -15}),
    },
    "engineer": {
        "minors": [("turretDmg", 0.15), ("turretRate", 0.12), ("turretMaxHp", 60), ("armor", 8), ("dmgMult", 0.06)],
        "notables": [("📡 Kapasite", {"turretLimit": 1, "turretDmg": 0.15}), ("🧱 Sığınak", {"turretMaxHp": 100, "armor": 10})],
        "keystone": ("🔧 Aşırı Yükleme", {"turretDmg": 0.5, "turretRate": 0.25, "max_hp_pct": -15}),
    },
    "beastmaster": {
        "minors": [("minionDamage", 0.15), ("minionRate", 0.15), ("minionMaxHpFlat", 60), ("regen", 1.0), ("dmgMult", 0.06)],
        "notables": [("🐺 Alfa Sürüsü", {"minionDamage": 0.25, "minionCount": 1}), ("🦴 Kalın Post", {"minionMaxHpFlat": 100, "regen": 1.0})],
        "keystone": ("🔗 Vahşi Bağ", {"minionDamage": 0.5, "dmgMult": -0.20}),
    },
}

GENERIC = [("max_hp", 40), ("dmgMult", 0.08), ("armor", 8), ("speed", 0.3),
           ("critChance", 0.04), ("regen", 1.0), ("attack_speed_bonus", 0.06),
           ("lifesteal", 0.03), ("aoe_bonus", 0.10)]
GENERIC_NOTABLES = [("💪 Kudret", {"dmgMult": 0.15}), ("🛡️ Sur", {"max_hp": 80, "armor": 10}),
                    ("💨 Çeviklik", {"speed": 0.5, "attack_speed_bonus": 0.08}),
                    ("🎯 Öldürücü", {"critChance": 0.06, "critDmg": 0.4})]

STAT_LABEL = {
    "max_hp": lambda v: f"+{v:.0f} Can", "dmgMult": lambda v: f"+%{v*100:.0f} Hasar",
    "armor": lambda v: f"+{v:.0f} Zırh", "speed": lambda v: f"+{v:.1f} Hız",
    "critChance": lambda v: f"+%{v*100:.0f} Kritik", "critDmg": lambda v: f"+%{v*100:.0f} Krit Hasar",
    "dodgeChance": lambda v: f"+%{v*100:.0f} Kaçınma",
    "attack_speed_bonus": lambda v: f"+%{v*100:.0f} Saldırı Hızı", "lifesteal": lambda v: f"+%{v*100:.0f} Can Çalma",
    "regen": lambda v: f"+{v:.1f} Rejen", "physDmgFlat": lambda v: f"+{v:.0f} Fiziksel",
    "fireDmgFlat": lambda v: f"+{v:.0f} Ateş", "frostDmgFlat": lambda v: f"+{v:.0f} Buz",
    "elementDmgMult": lambda v: f"+%{v*100:.0f} Element", "dotDmgMult": lambda v: f"+%{v*100:.0f} DoT",
    "poisonDps": lambda v: f"+{v:.0f} Zehir DPS", "aoe_bonus": lambda v: f"+%{v*100:.0f} Alan",
    "pierce": lambda v: f"+{v:.0f} Delme", "bullet_speed": lambda v: f"+{v:.0f} Mermi Hızı",
    "meleeRangeFlat": lambda v: f"+{v:.0f} Menzil",
    "turretDmg": lambda v: f"+%{v*100:.0f} Taret Hasarı", "turretRate": lambda v: f"+%{v*100:.0f} Taret Hızı",
    "turretMaxHp": lambda v: f"+{v:.0f} Taret Canı", "turretLimit": lambda v: f"+{v:.0f} Taret Limiti",
    "minionDamage": lambda v: f"+%{v*100:.0f} Minyon Hasarı", "minionRate": lambda v: f"+%{v*100:.0f} Minyon Hızı",
    "minionMaxHpFlat": lambda v: f"+{v:.0f} Minyon Canı", "minionCount": lambda v: f"+{v:.0f} Minyon",
    "max_hp_pct": lambda v: f"Max Can %{-v:.0f} azalır",
}


def desc_of(stats):
    return ", ".join(STAT_LABEL.get(k, lambda v: f"{k} {v}")(v) for k, v in stats.items())


def pos(angle_deg, r):
    a = math.radians(angle_deg)
    return [round(CX + r * math.cos(a)), round(CY + r * math.sin(a))]


nodes = {}
edges = set()


def add_node(nid, name, arm, ntype, stats, angle, r):
    nodes[nid] = {"id": nid, "name": name, "desc": desc_of(stats) if stats else "",
                  "arm": arm, "type": ntype, "stats": stats, "pos": pos(angle, r)}
    if ntype == "start":
        nodes[nid]["start"] = True


def link(a, b):
    edges.add(tuple(sorted((a, b))))


RAILS = [("L", -RAIL_OFF), ("C", 0), ("R", RAIL_OFF)]

for i, cls in enumerate(CLASSES):
    a_i = -90 + i * 40
    theme = THEMES[cls]
    minors = theme["minors"]
    # Başlangıç düğümü (iç çember)
    start_id = f"start_{cls}"
    add_node(start_id, f"{cls.title()} Başlangıcı", cls, "start", {}, a_i, R0)

    # Junction (bu sınıf ile bir sonraki sınıf arasında, iç çember)
    nxt = CLASSES[(i + 1) % len(CLASSES)]
    jstat = dict([GENERIC[i % len(GENERIC)]])
    jid = f"junc_{cls}_{nxt}"
    add_node(jid, "Geçit", "core", "minor", jstat, a_i + BRIDGE_OFF, R0)
    link(start_id, jid)  # çember: start -> junction -> (sonraki start, aşağıda)

    # Sınıf rayları (L/C/R) dışa doğru
    for rail, off in RAILS:
        prev = None
        for k, r in enumerate(RINGS):
            nid = f"{cls}_{rail}{k}"
            # Tip ve stat ata
            if rail == "C" and k == len(RINGS) - 1:
                nm, st = theme["keystone"]; ntype = "keystone"
            elif rail == "C" and k in (2, 4):
                nm, st = theme["notables"][0 if k == 2 else 1]; ntype = "notable"
            elif rail in ("L", "R") and k == len(RINGS) - 1:
                nm, st = theme["notables"][0 if rail == "L" else 1]; ntype = "notable"
            else:
                s = minors[(k + (0 if rail == "C" else (1 if rail == "L" else 3))) % len(minors)]
                st = dict([s]); nm = STAT_LABEL[s[0]](s[1]); ntype = "minor"
            add_node(nid, nm, cls, ntype, st, a_i + off, r)
            # radyal bağ (ray boyunca)
            if prev:
                link(prev, nid)
            prev = nid
        # C rayının kökü başlangıca bağlanır; L/R ilk halkası C ilk halkasına
    # Başlangıç -> C rayı ilk halka
    link(start_id, f"{cls}_C0")
    # Her halkada teğetsel "rung": L-C-R
    for k in range(len(RINGS)):
        link(f"{cls}_L{k}", f"{cls}_C{k}")
        link(f"{cls}_C{k}", f"{cls}_R{k}")

# Çemberi kapat: junction -> sonraki başlangıç
for i, cls in enumerate(CLASSES):
    nxt = CLASSES[(i + 1) % len(CLASSES)]
    link(f"junc_{cls}_{nxt}", f"start_{nxt}")

# Köprü rayları (komşu sınıflar arası, dışa doğru jenerik) + sınıflar-arası rung
for i, cls in enumerate(CLASSES):
    nxt = CLASSES[(i + 1) % len(CLASSES)]
    a_b = -90 + i * 40 + BRIDGE_OFF
    jid = f"junc_{cls}_{nxt}"
    prev = jid
    for k, r in enumerate(RINGS):
        bid = f"bridge_{cls}_{nxt}_{k}"
        if k == len(RINGS) - 1:
            nm, st = GENERIC_NOTABLES[i % len(GENERIC_NOTABLES)]; ntype = "notable"
        else:
            s = GENERIC[(i + k) % len(GENERIC)]; st = dict([s]); nm = STAT_LABEL[s[0]](s[1]); ntype = "minor"
        add_node(bid, nm, "core", ntype, st, a_b, r)
        link(prev, bid)
        # sınıflar-arası teğetsel bağ: bu sınıfın R rayı <-> köprü <-> sonraki sınıfın L rayı
        link(f"{cls}_R{k}", bid)
        link(bid, f"{nxt}_L{k}")
        prev = bid

# connects'i tek yönde (küçük id'ye) yaz — motor simetrik kurar
for nid in nodes:
    nodes[nid]["connects"] = []
for a, b in sorted(edges):
    nodes[a]["connects"].append(b)

out = list(nodes.values())
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
    f.write("\n")

n_start = sum(1 for n in out if n["type"] == "start")
n_key = sum(1 for n in out if n["type"] == "keystone")
n_not = sum(1 for n in out if n["type"] == "notable")
print(f"{OUT}: {len(out)} düğüm ({n_start} başlangıç, {n_not} notable, {n_key} keystone, "
      f"{len(edges)} kenar)")
