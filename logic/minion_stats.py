"""Migrate obsolete pet defenses while preserving invested slots and points."""
OBSOLETE = frozenset(("minionMaxHp", "minionMaxHpFlat", "minionArmor"))

def convert(stat, value):
    if stat == "minionMaxHp":
        return "minionRange", max(-.5, min(.3, value))
    if stat == "minionMaxHpFlat":
        return "minionRange", value * .001
    if stat == "minionArmor":
        return "minionCrit", value * .002
    return stat, value

def migrate_stats(stats):
    for stat in list(stats):
        if stat in OBSOLETE:
            key, value = convert(stat, stats.pop(stat))
            stats[key] = stats.get(key, 0) + value
    return stats

def migrate_item(item):
    if not isinstance(item, dict):
        return
    migrate_stats(item.get("itemBase", {}))
    for affix in item.get("prefixes", []) + item.get("suffixes", []):
        if affix.get("stat") in OBSOLETE:
            affix["stat"], affix["val"] = convert(affix["stat"], affix["val"])
            affix["name"] = "Minyon Menzili" if affix["stat"] == "minionRange" else "Minyon Kritik Şansı"

def migrate_player(player, equipped):
    for item in list(equipped.values()) + list(getattr(player, "inventory", [])):
        migrate_item(item)
    for field in ("skills_permanent", "essence_stats"):
        migrate_stats(getattr(player, field, {}))
    for skill in getattr(player, "skills", []):
        stat = skill.get("stat")
        if stat in OBSOLETE:
            # Old Fedai entries used either HP key for the same flat bonus.
            key = "minionMaxHpFlat" if stat == "minionMaxHp" else stat
            skill["stat"], skill["val"] = convert(key, skill.get("val", 0))
            skill["name"] = "Keskin Duyular (+%8 Minyon Menzili)" if skill["stat"] == "minionRange" else "Minyon Kritik Şansı"
