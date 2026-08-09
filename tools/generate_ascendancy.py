# -*- coding: utf-8 -*-
"""data/ascendancy.json üretir — 18 alt-sınıf (ascendancy) mini ağacı.

Her evrim (EVOLUTIONS) için küçük bir ağaç: start (evrimin kendisi, bedava)
+ 2 minör + 1 notable + 1 keystone (capstone). Aynı anda yalnız oyuncunun
seçtiği alt-sınıf gösterildiği için hepsi AYNI koordinat alanını kullanır.

Çalıştır (repo kökünden):
    python tools/generate_ascendancy.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'ascendancy.json')

STAT_LABEL = {
    "max_hp": lambda v: f"+{v:.0f} Can", "dmgMult": lambda v: f"+%{v*100:.0f} Hasar",
    "armor": lambda v: f"+{v:.0f} Zırh", "speed": lambda v: f"+{v:.1f} Hız",
    "critChance": lambda v: f"+%{v*100:.0f} Kritik", "critDmg": lambda v: f"+%{v*100:.0f} Krit Hasar",
    "dodgeChance": lambda v: f"+%{v*100:.0f} Kaçınma", "attack_speed_bonus": lambda v: f"+%{v*100:.0f} Saldırı Hızı",
    "lifesteal": lambda v: f"+%{v*100:.0f} Can Çalma", "regen": lambda v: f"+{v:.1f} Rejen",
    "physDmgFlat": lambda v: f"+{v:.0f} Fiziksel", "fireDmgFlat": lambda v: f"+{v:.0f} Ateş",
    "frostDmgFlat": lambda v: f"+{v:.0f} Buz", "elementDmgMult": lambda v: f"+%{v*100:.0f} Element",
    "dotDmgMult": lambda v: f"+%{v*100:.0f} DoT", "poisonDps": lambda v: f"+{v:.0f} Zehir DPS",
    "aoe_bonus": lambda v: f"+%{v*100:.0f} Alan", "pierce": lambda v: f"+{v:.0f} Delme",
    "projectileCount": lambda v: f"+{v:.0f} Mermi", "turretDmg": lambda v: f"+%{v*100:.0f} Taret Hasarı",
    "turretRate": lambda v: f"+%{v*100:.0f} Taret Hızı", "turretMaxHp": lambda v: f"+{v:.0f} Taret Canı",
    "turretLimit": lambda v: f"+{v:.0f} Taret Limiti", "minionDamage": lambda v: f"+%{v*100:.0f} Minyon Hasarı",
    "minionCount": lambda v: f"+{v:.0f} Minyon", "minionMaxHpFlat": lambda v: f"+{v:.0f} Minyon Canı",
    "minionRate": lambda v: f"+%{v*100:.0f} Minyon Hızı", "lowHpExec": lambda v: f"Düşük canı infaz",
    "max_hp_pct": lambda v: f"Max Can %{-v:.0f} azalır",
}


def desc(stats):
    return ", ".join(STAT_LABEL.get(k, lambda v: f"{k} {v}")(v) for k, v in stats.items())


# evo_id -> (Görünen Ad, minor1, minor2, notable(ad,stat), capstone(ad,stat))
# minor: (ad, stats)  |  notable/capstone: (ad, stats)
S = {
    "warrior_gladiator": ("🏟️ Gladyatör",
        ("Kan Sarhoşu", {"dmgMult": 0.15}), ("Keskin Refleks", {"critChance": 0.08}),
        ("🩸 Arena Ustası", {"dmgMult": 0.20, "physDmgFlat": 12}),
        ("⚔️ Kan Meydanı", {"dmgMult": 0.30, "max_hp_pct": -10})),
    "warrior_paladin": ("🛡️ Paladin",
        ("Kutsal Zırh", {"armor": 20}), ("Dayanıklılık", {"max_hp": 80}),
        ("✨ Aziz Koruması", {"armor": 25, "regen": 2.0}),
        ("🛡️ Kutsal Kalkan", {"max_hp": 150, "armor": 20})),
    "beastmaster_emperor": ("👑 Pet İmparatoru",
        ("Sürü Emri", {"minionDamage": 0.20}), ("Çoğalma", {"minionCount": 1}),
        ("🐺 Sürü Efendisi", {"minionDamage": 0.30, "minionRate": 0.20}),
        ("👑 Sürü İmparatorluğu", {"minionCount": 2, "minionDamage": 0.30})),
    "beastmaster_hunter": ("🦅 Avcı",
        ("Vahşi Güç", {"minionDamage": 0.30}), ("Kalın Post", {"minionMaxHpFlat": 100}),
        ("🐾 Dev Yoldaş", {"minionDamage": 0.40, "minionMaxHpFlat": 100}),
        ("🐺 Alfa Canavar", {"minionDamage": 0.60, "dmgMult": -0.10})),
    "sniper_marksman": ("💥 Tetikçi",
        ("Nişan", {"critChance": 0.10}), ("Sertlik", {"critDmg": 0.4}),
        ("🎯 Keskin Göz", {"critChance": 0.10, "critDmg": 0.5}),
        ("💥 İnfaz Atışı", {"critDmg": 1.0, "max_hp_pct": -10})),
    "sniper_phantom": ("🌑 Hayalet Nişancı",
        ("Ölümcül", {"critDmg": 0.5}), ("Sıyrılma", {"dodgeChance": 0.08}),
        ("🌫️ Gölge Atış", {"critDmg": 0.6, "pierce": 1}),
        ("🌑 Hayalet Kurşun", {"critChance": 0.15, "critDmg": 0.8, "max_hp_pct": -10})),
    "engineer_architect": ("🏰 Kale Mimarı",
        ("Ek Slot", {"turretLimit": 1}), ("Takviye", {"turretMaxHp": 100}),
        ("🏭 Fabrika", {"turretLimit": 1, "turretDmg": 0.20}),
        ("🏰 Kale Ağı", {"turretLimit": 2, "turretDmg": 0.25})),
    "engineer_electrician": ("⚡ Elektrikçi",
        ("Voltaj", {"turretDmg": 0.25}), ("Hızlı Ateş", {"turretRate": 0.20}),
        ("⚙️ Aşırı Gerilim", {"turretDmg": 0.35, "turretRate": 0.20}),
        ("⚡ Aşırı Şarj", {"turretDmg": 0.60, "max_hp_pct": -10})),
    "bomber_nuclear": ("☢️ Nükleer Bombacı",
        ("Geniş Patlama", {"aoe_bonus": 0.20}), ("Ağır Dolgu", {"dmgMult": 0.15}),
        ("💥 Serpinti", {"aoe_bonus": 0.25, "dmgMult": 0.15}),
        ("☢️ Nükleer Kış", {"aoe_bonus": 0.40, "dmgMult": 0.20, "max_hp_pct": -10})),
    "bomber_chemist": ("🧨 Mayın Uzmanı",
        ("Fazla Mayın", {"aoe_bonus": 0.15}), ("Güçlü Dolgu", {"dmgMult": 0.15}),
        ("🧷 Küme Mayın", {"aoe_bonus": 0.20, "physDmgFlat": 12}),
        ("🧨 Mayın Tarlası", {"dmgMult": 0.30, "aoe_bonus": 0.20})),
    "ninja_shadow": ("🗡️ Ölüm Gölgesi",
        ("Sessiz Adım", {"critChance": 0.10}), ("Ölümcül", {"critDmg": 0.6}),
        ("🌑 Suikast", {"critChance": 0.10, "dodgeChance": 0.08}),
        ("🗡️ Ölüm Fısıltısı", {"critDmg": 1.0, "lowHpExec": 0.20})),
    "ninja_storm": ("🌀 Fırtına Bıçağı",
        ("Hız", {"attack_speed_bonus": 0.15}), ("Çeviklik", {"speed": 0.5}),
        ("🌀 Kasırga", {"attack_speed_bonus": 0.15, "dodgeChance": 0.08}),
        ("⚔️ Bin Bıçak", {"attack_speed_bonus": 0.25, "dmgMult": -0.10})),
    "alchemist_grandmaster": ("🧪 Çılgın Simyacı",
        ("Yayılım", {"aoe_bonus": 0.15}), ("Hızlı Karışım", {"attack_speed_bonus": 0.10}),
        ("🍶 Ek Şişe", {"projectileCount": 1, "aoe_bonus": 0.15}),
        ("🧪 Çılgın Karışım", {"projectileCount": 1, "dmgMult": 0.15})),
    "alchemist_poison_god": ("🍄 Zehir Tanrısı",
        ("Zehir", {"dotDmgMult": 0.20}), ("Toksin", {"poisonDps": 15}),
        ("☣️ Salgın", {"dotDmgMult": 0.30, "aoe_bonus": 0.15}),
        ("🍄 Veba Tanrısı", {"dotDmgMult": 0.50, "dmgMult": -0.15})),
    "sorcerer_firelord": ("🌋 Ateş Başbüyücüsü",
        ("Kor", {"fireDmgFlat": 10}), ("Alev Gücü", {"elementDmgMult": 0.15}),
        ("🔥 Yangın", {"fireDmgFlat": 15, "elementDmgMult": 0.15}),
        ("🌋 Cehennem", {"elementDmgMult": 0.50, "max_hp_pct": -15})),
    "sorcerer_icemage": ("❄️ Buz Büyücüsü",
        ("Ayaz", {"frostDmgFlat": 10}), ("Buz Gücü", {"elementDmgMult": 0.15}),
        ("🧊 Buzul", {"frostDmgFlat": 15, "elementDmgMult": 0.15}),
        ("❄️ Sonsuz Kış", {"elementDmgMult": 0.40, "armor": 20})),
    "bloodwalker_noble": ("🧛 Asil Vampir",
        ("Kan İçici", {"lifesteal": 0.05}), ("Dayanıklılık", {"max_hp": 80}),
        ("🩸 Soylu Kan", {"lifesteal": 0.06, "regen": 2.0}),
        ("🧛 Ölümsüz Asalet", {"lifesteal": 0.10, "max_hp": 100})),
    "bloodwalker_martyr": ("💔 Şehit",
        ("Öfke", {"dmgMult": 0.15}), ("Kan İçici", {"lifesteal": 0.05}),
        ("🔥 Kızıl Gazap", {"dmgMult": 0.20, "lifesteal": 0.05}),
        ("💔 Kan Şehidi", {"dmgMult": 0.40, "max_hp_pct": -20})),
}

# Sabit yerleşim (hepsi aynı alanı kullanır — aynı anda tek alt-sınıf gösterilir)
POS = {"a0": [300, 80], "a1": [190, 210], "a2": [410, 210], "a3": [300, 330], "a4": [300, 470]}

nodes = []
for evo_id, (start_name, m1, m2, notable, capstone) in S.items():
    def node(suffix, name, ntype, stats, connects):
        nodes.append({
            "id": f"{evo_id}_{suffix}", "name": name, "desc": desc(stats) if stats else "",
            "subclass": evo_id, "type": ntype, "stats": stats,
            "connects": [f"{evo_id}_{c}" for c in connects], "pos": POS[suffix],
        })
    node("a0", start_name, "start", {}, ["a1", "a2"])
    node("a1", m1[0], "minor", m1[1], [])
    node("a2", m2[0], "minor", m2[1], [])
    node("a3", notable[0], "notable", notable[1], ["a1", "a2", "a4"])
    node("a4", capstone[0], "keystone", capstone[1], [])
    nodes[-1]["start"] = False  # capstone
    # a0'a start bayrağı
    for n in nodes:
        if n["id"] == f"{evo_id}_a0":
            n["start"] = True

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(nodes, f, ensure_ascii=False, indent=2)
    f.write("\n")

print(f"{OUT}: {len(nodes)} düğüm ({len(S)} alt-sınıf)")
