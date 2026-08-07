class CrystalShop:
    # Upgrades: each has id, name, desc, max_rank, costs (list per rank), effect_key, effect_per_rank
    UPGRADES = [
        # --- SURVIVAL ---
        {"id": "start_hp",      "name": "❤️ Başlangıç Canı",      "category": "survival",  "max_rank": 10,
         "costs": [500, 500, 800, 800, 1200, 1200, 2000, 2000, 3000, 3000],
         "desc": "Her seviye, yeni oyuna başladığında maksimum canını 15 artırır.",
         "effect_key": "start_hp", "effect_per_rank": 15},

        {"id": "start_armor",   "name": "🛡️ Başlangıç Zırhı",     "category": "survival",  "max_rank": 5,
         "costs": [600, 1000, 1500, 2200, 3500],
         "desc": "Her seviye, yeni oyuna başladığında zırhını 10 artırır.",
         "effect_key": "start_armor", "effect_per_rank": 10},

        {"id": "passive_regen", "name": "💉 Pasif Can Yenileme",   "category": "survival",  "max_rank": 5,
         "costs": [800, 1400, 2200, 3500, 5500],
         "desc": "Her seviye, savaş sırasında saniyede 0,5 can yenilenmesi sağlar.",
         "effect_key": "start_regen", "effect_per_rank": 0.5},

        {"id": "revive_charm",  "name": "🔄 Dirilme Tılsımı",      "category": "survival",  "max_rank": 1,
         "costs": [3000],
         "desc": "Her oyunda ilk ölümcül darbeyi engeller ve bir kez hayata döndürür.",
         "effect_key": "start_revive", "effect_per_rank": 1},

        {"id": "start_es",      "name": "🛡️ Enerji Kalkanı",         "category": "survival",  "max_rank": 10,
         "costs": [1000, 1500, 2500, 4000, 6000, 9000, 13000, 18000, 25000, 35000],
         "desc": "Her seviye, oyun başındaki enerji kalkanı kapasitesini 4 artırır.",
         "effect_key": "start_es", "effect_per_rank": 4},

        # --- ECONOMY ---
        {"id": "start_gold",    "name": "💛 Başlangıç Altını",     "category": "economy",   "max_rank": 10,
         "costs": [400, 400, 700, 700, 1200, 1200, 1800, 1800, 2800, 2800],
         "desc": "Her seviye, yeni oyuna 75 ek altınla başlamanı sağlar.",
         "effect_key": "start_gold", "effect_per_rank": 75},

        {"id": "shop_discount", "name": "🏪 Market İndirimi",      "category": "economy",   "max_rank": 5,
         "costs": [800, 1400, 2400, 3800, 6000],
         "desc": "Her seviye, marketteki eşya fiyatlarını %5 düşürür.",
         "effect_key": "shop_discount", "effect_per_rank": 0.05},

        {"id": "shop_slot",     "name": "📦 Ekstra Market Slotu",  "category": "economy",   "max_rank": 3,
         "costs": [1500, 2500, 4000],
         "desc": "Her seviye, markette aynı anda gösterilen eşya sayısını 1 artırır.",
         "effect_key": "shop_slots", "effect_per_rank": 1},

        {"id": "magic_find",    "name": "✨ Sihirli Bulma+",        "category": "economy",   "max_rank": 5,
         "costs": [600, 1000, 1800, 3000, 5000],
         "desc": "Her seviye, nadir eşya bulma değerini 0,15 artırır.",
         "effect_key": "start_magic_find", "effect_per_rank": 0.15},

        # --- COMBAT ---
        {"id": "start_dmg",     "name": "🗡️ Başlangıç Hasarı",     "category": "combat",    "max_rank": 8,
         "costs": [600, 600, 1000, 1000, 1800, 1800, 3000, 3000],
         "desc": "Her seviye, verdiğin tüm hasarı %5 artırır.",
         "effect_key": "start_dmg", "effect_per_rank": 0.05},

        {"id": "start_speed",   "name": "⚡ Başlangıç Hızı",       "category": "combat",    "max_rank": 5,
         "costs": [800, 1400, 2400, 3800, 6000],
         "desc": "Her seviye, başlangıç hareket hızına 0,3 ekler.",
         "effect_key": "start_speed", "effect_per_rank": 0.3},

        {"id": "crit_base",     "name": "🎯 Kritik Temel",         "category": "combat",    "max_rank": 3,
         "costs": [1200, 2000, 3500],
         "desc": "Her seviye, kritik vuruş şansını 3 yüzde puan artırır.",
         "effect_key": "start_crit", "effect_per_rank": 0.03},

        {"id": "xp_bonus",      "name": "🔥 XP Bonusu",            "category": "combat",    "max_rank": 5,
         "costs": [500, 800, 1400, 2200, 3500],
         "desc": "Her seviye, tüm deneyim kazanımını %10 artırır.",
         "effect_key": "start_xp", "effect_per_rank": 0.10},

        {"id": "turret_range",  "name": "🔭 Taret Menzili",        "category": "combat",    "max_rank": 5,
         "costs": [1000, 1800, 3000, 5000, 8000],
         "desc": "Her seviye, kurduğun taretlerin menzilini %10 artırır.",
         "effect_key": "start_turret_range", "effect_per_rank": 0.10},

        {"id": "turret_rate",   "name": "⚙️ Taret Ateş Hızı",       "category": "combat",    "max_rank": 5,
         "costs": [1500, 2500, 4000, 6500, 10000],
         "desc": "Her seviye, kurduğun taretlerin saldırı hızını %10 artırır.",
         "effect_key": "start_turret_rate", "effect_per_rank": 0.10},

        # --- CARD SYSTEM ---
        {"id": "card_visibility","name": "➕ Kart Görünürlüğü",    "category": "cards",     "max_rank": 2,
         "costs": [2000, 4000],
         "desc": "Her kart seçiminde 1 kart daha gösterilir (3→4→5).",
         "effect_key": "card_count", "effect_per_rank": 1},

        {"id": "card_reroll",   "name": "🔁 Kart Yenileme",        "category": "cards",     "max_rank": 1,
         "costs": [2500],
         "desc": "Her kart seçiminde 1 kez yenileme hakkın olur.",
         "effect_key": "card_reroll", "effect_per_rank": 1},

        {"id": "legendary_card","name": "🌟 Efsane Kart Şansı",   "category": "cards",     "max_rank": 3,
         "costs": [1500, 2500, 4500],
         "desc": "Her seviye, lanetli veya nadir kartların sunulma şansını %10 artırır.",
         "effect_key": "legendary_card_chance", "effect_per_rank": 0.10},

        # --- SPECIAL ---
        {"id": "blood_moon_mem","name": "🌙 Kan Ayı Hafızası",     "category": "special",   "max_rank": 1,
         "costs": [4000],
         "desc": "Kan Ayı bittiğinde marketi 1 dalga daha erişilebilir tutar.",
         "effect_key": "blood_moon_memory", "effect_per_rank": 1},

        {"id": "early_evo",     "name": "🦋 Erken Evrim",          "category": "special",   "max_rank": 1,
         "costs": [5000],
         "desc": "Karakter evrimini seviye 20 yerine seviye 15'te tetikler.",
         "effect_key": "early_evolution", "effect_per_rank": 1},

        {"id": "start_card",    "name": "🃏 Başlangıç Kartı",      "category": "special",   "max_rank": 1,
         "costs": [3500],
         "desc": "Her yeni oyunun başında koleksiyonuna 1 rastgele kart ekler.",
         "effect_key": "start_with_card", "effect_per_rank": 1},

        {"id": "biome_choice",  "name": "🌍 Biyom Seçimi",         "category": "special",   "max_rank": 1,
         "costs": [3000],
         "desc": "Yeni oyuna başlarken ilk biyomu kendin seçebilmeni sağlar.",
         "effect_key": "biome_choice", "effect_per_rank": 1},
    ]

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
