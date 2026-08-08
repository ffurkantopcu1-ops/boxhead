from logic.data_loader import load_data


class CrystalShop:
    # Upgrades: each has id, name, desc, max_rank, costs (list per rank), effect_key, effect_per_rank
    # Kaynak: data/crystal_upgrades.json
    UPGRADES = load_data('crystal_upgrades')

    def __init__(self):
        pass

    def get_rank(self, meta, upgrade_id):
        return meta.get("upgrades", {}).get(upgrade_id, 0)

    def get_cost(self, upgrade_id, current_rank):
        upg = next((u for u in self.UPGRADES if u["id"] == upgrade_id), None)
        if not upg or current_rank >= upg["max_rank"]:
            return None  # Maksimum seviyede
        return upg["costs"][current_rank]

    def purchase(self, meta, upgrade_id):
        """Kristal harcayarak yükseltme satın al. meta dict'ini günceller."""
        upg = next((u for u in self.UPGRADES if u["id"] == upgrade_id), None)
        if not upg:
            return meta, False, "Yükseltme bulunamadı."

        current_rank = self.get_rank(meta, upgrade_id)
        if current_rank >= upg["max_rank"]:
            return meta, False, "Maksimum seviyeye ulaşıldı!"

        cost = upg["costs"][current_rank]
        if meta.get("crystals", 0) < cost:
            return meta, False, f"Yetersiz Kristal! ({cost} gerekli)"

        meta["crystals"] -= cost
        if "upgrades" not in meta:
            meta["upgrades"] = {}
        meta["upgrades"][upgrade_id] = current_rank + 1
        return meta, True, f"{upg['name']} Seviye {current_rank + 1}e yükseltildi!"

    def apply_to_player(self, meta, player):
        """meta.json'daki yükseltmeleri oyuncuya uygula."""
        upgrades = meta.get("upgrades", {})
        for upg in self.UPGRADES:
            rank = upgrades.get(upg["id"], 0)
            if rank <= 0:
                continue
            total = upg["effect_per_rank"] * rank
            key = upg["effect_key"]

            if key == "start_hp":
                player.max_hp += total
                player.hp = player.max_hp
            elif key == "start_armor":
                sp = getattr(player, 'skills_permanent', {})
                sp['armor'] = sp.get('armor', 0) + total
                player.skills_permanent = sp
            elif key == "start_regen":
                sp = getattr(player, 'skills_permanent', {})
                sp['hpRegen'] = sp.get('hpRegen', 0) + total
                player.skills_permanent = sp
            elif key == "start_revive":
                player.revive_count = getattr(player, 'revive_count', 0) + int(total)
            elif key == "start_es":
                player.max_energy_shield += total
                player.energy_shield = player.max_energy_shield
            elif key == "start_gold":
                player.gold += int(total)
            elif key == "start_dmg":
                sp = getattr(player, 'skills_permanent', {})
                sp['dmgMult'] = sp.get('dmgMult', 0) + total
                player.skills_permanent = sp
            elif key == "start_speed":
                sp = getattr(player, 'skills_permanent', {})
                sp['speed'] = sp.get('speed', 0) + total
                player.skills_permanent = sp
            elif key == "start_crit":
                sp = getattr(player, 'skills_permanent', {})
                sp['critChance'] = sp.get('critChance', 0) + total
                player.skills_permanent = sp
            elif key == "start_xp":
                sp = getattr(player, 'skills_permanent', {})
                sp['xpGain'] = sp.get('xpGain', 0) + total
                player.skills_permanent = sp
            elif key == "start_magic_find":
                sp = getattr(player, 'skills_permanent', {})
                sp['magicFind'] = sp.get('magicFind', 1.0) + total
                player.skills_permanent = sp
            elif key == "start_turret_range":
                sp = getattr(player, 'skills_permanent', {})
                sp['turretRange'] = sp.get('turretRange', 0) + total
                player.skills_permanent = sp
            elif key == "start_turret_rate":
                sp = getattr(player, 'skills_permanent', {})
                sp['turretRate'] = sp.get('turretRate', 0) + total
                player.skills_permanent = sp
            elif key == "start_with_card":
                player._meta_start_card = True
            elif key == "early_evolution":
                player._early_evolution = True
            # shop_discount, card_count, card_reroll, biome_choice etc. are read from meta directly

    def get_effective(self, meta, key):
        """meta'dan belirli bir etkinin toplam değerini hesapla."""
        upgrades = meta.get("upgrades", {})
        for upg in self.UPGRADES:
            if upg["effect_key"] == key:
                rank = upgrades.get(upg["id"], 0)
                return upg["effect_per_rank"] * rank
        return 0


# --- Veri dogrulamasi (acilista bir kez) ---
for _u in CrystalShop.UPGRADES:
    if len(_u['costs']) != _u['max_rank']:
        raise ValueError(f"crystal_upgrades.json: '{_u['id']}' icin len(costs)={len(_u['costs'])} != max_rank={_u['max_rank']}")
