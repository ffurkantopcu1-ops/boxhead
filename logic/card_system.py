import random


from logic.synergy_system import SynergySystem

class CardSystem:
    def __init__(self):
        self.active_cards = []
        self.synergy_system = SynergySystem()

    # ------------------------------------------------------------------
    # CARDS LIST
    # ------------------------------------------------------------------
    CARDS = [
        # ── SURVIVAL ──────────────────────────────────────────────────
        {
            "id": "iron_will",
            "name": "🛡️ Demir İrade",
            "desc": "Etki: Hasar alınca 3 sn kalkan kazanır (60 sn bekleme) ve +50 maksimum can verir. Bedel: Hareket hızı %10 azalır.",
            "category": "survival",
            "apply": "_apply_iron_will",
        },
        {
            "id": "zombie_skin",
            "name": "🧟 Zombi Derisi",
            "desc": "Etki: Ölümcül hasarı bir kez engeller ve hayata döndürür. Bedel: Maksimum can %20 azalır.",
            "category": "survival",
            "apply": "_apply_zombie_skin",
        },
        {
            "id": "blood_pact",
            "name": "🩸 Kan Paktı",
            "desc": "Etki: Her hasar aldığında 5 deneyim kazanırsın. Bedel: Maksimum can %15 azalır.",
            "category": "survival",
            "apply": "_apply_blood_pact",
        },
        {
            "id": "iron_skin",
            "name": "🪨 Taş Deri",
            "desc": "Etki: +80 zırh kazanırsın. Bedel: Hareket hızın %30 azalır.",
            "category": "survival",
            "apply": "_apply_iron_skin",
        },
        {
            "id": "berserker_rage",
            "name": "😡 Berserker Öfkesi",
            "desc": "Etki: Canın %40'ın altındayken hasarın %80 artar. Bedel: Pasif can yenilenmesi tamamen durur.",
            "category": "survival",
            "apply": "_apply_berserker_rage",
        },
        {
            "id": "phoenix_blood",
            "name": "🔆 Anka Kanı",
            "desc": "Etki: Öldüğünde savaş alanındaki tüm düşmanlara 200 hasar verir. Bedel: Maksimum can %10 azalır.",
            "category": "survival",
            "apply": "_apply_phoenix_blood",
        },
        {
            "id": "adrenaline",
            "name": "💉 Adrenalin",
            "desc": "Etki: Her 20 saniyede, 5 saniye boyunca hızın %30 ve hasarın %20 artar. Bedel: 30 zırh kaybedersin.",
            "category": "survival",
            "apply": "_apply_adrenaline",
        },
        # ── OFFENSE ───────────────────────────────────────────────────
        {
            "id": "blood_fire",
            "name": "🔥 Kan Ateşi",
            "desc": "Etki: Hasar verdiğinde 5 can yenilersin. Bedel: Maksimum can %30 azalır.",
            "category": "offense",
            "apply": "_apply_blood_fire",
        },
        {
            "id": "chaos_theory",
            "name": "🌀 Kaos Teorisi",
            "desc": "Etki: Taban hasarın 2 katına çıkar. Bedel: Saldırı hızın %40 azalır.",
            "category": "offense",
            "apply": "_apply_chaos_theory",
        },
        {
            "id": "glass_cannon",
            "name": "🧨 Cam Top",
            "desc": "Etki: Saldırı hızın %50 artar. Bedel: Düşmanlardan 2 kat hasar alırsın.",
            "category": "offense",
            "apply": "_apply_glass_cannon",
        },
        {
            "id": "death_pact",
            "name": "💀 Ölüm Anlaşması",
            "desc": "Etki: Tüm saldırıların kritik vurur. Bedel: Maksimum canın 1'e düşer.",
            "category": "offense",
            "apply": "_apply_death_pact",
        },
        {
            "id": "double_edge",
            "name": "⚔️ Çift Ağız",
            "desc": "Etki: Hasarın %120 artar. Bedel: Her saldırıda maksimum canının %2'si kadar hasar alırsın.",
            "category": "offense",
            "apply": "_apply_double_edge",
        },
        {
            "id": "poison_heart",
            "name": "💚 Zehirli Kalp",
            "desc": "Etki: Verdiğin hasarın tamamı zamanla işleyen zehir hasarına dönüşür. Bedel: Doğrudan vuruş hasarın sıfırlanır.",
            "category": "offense",
            "apply": "_apply_poison_heart",
        },
        {
            "id": "crit_overload",
            "name": "⚡ Kritik Aşırı Yük",
            "desc": "Etki: Kritik hasarın %200 artar ve kritikler hedefi sersemletir. Bedel: 40 zırh kaybedersin.",
            "category": "offense",
            "apply": "_apply_crit_overload",
        },
        {
            "id": "executioner",
            "name": "🪓 Cellat",
            "desc": "Etki: Canı %30'un altındaki düşmanları anında infaz eder. Bedel: Saldırı hızın %30 azalır.",
            "category": "offense",
            "apply": "_apply_executioner",
        },
        # ── SUPPORT ───────────────────────────────────────────────────
        {
            "id": "ice_shirt",
            "name": "🧊 Buz Gömleği",
            "desc": "Etki: +50 zırh kazanırsın. Bedel: Hareket hızın %20 azalır.",
            "category": "support",
            "apply": "_apply_ice_shirt",
        },
        {
            "id": "vampire_touch",
            "name": "🦷 Vampir Dokunuşu",
            "desc": "Etki: %15 can çalma ve saniyede +2 can yenilenmesi kazanırsın. Bedel: Maksimum can %20 azalır.",
            "category": "support",
            "apply": "_apply_vampire_touch",
        },
        {
            "id": "gold_fever",
            "name": "💰 Altın Humması",
            "desc": "Etki: Kazandığın altın %60 artar. Bedel: Deneyim kazanımın %30 azalır.",
            "category": "support",
            "apply": "_apply_gold_fever",
        },
        {
            "id": "lucky_charm",
            "name": "🍀 Şans Tılsımı",
            "desc": "Etki: Nadir eşya bulma şansın %40 artar. Bedel: Verdiğin hasar %15 azalır.",
            "category": "support",
            "apply": "_apply_lucky_charm",
        },
        {
            "id": "accelerator",
            "name": "🚀 İvmeleyici",
            "desc": "Etki: Hareket hızın %50 artar. Bedel: Zırhın %30 azalır.",
            "category": "support",
            "apply": "_apply_accelerator",
        },
        {
            "id": "merchant_soul",
            "name": "🪙 Tüccar Ruhu",
            "desc": "Etki: Kervanı yenileme maliyeti %50 azalır. Bedel: Verdiğin hasar %20 azalır.",
            "category": "support",
            "apply": "_apply_merchant_soul",
        },
        # ── MINION ────────────────────────────────────────────────────
        {
            "id": "undead_army",
            "name": "💀 Ölümsüz Ordu",
            "desc": "Etki: Düşmanların minyona dönüşme şansı %15 olur. Bedel: Kendi hasarın %15 azalır.",
            "category": "minion",
            "apply": "_apply_undead_army",
        },
        {
            "id": "war_commander",
            "name": "🎖️ Savaş Komutanı",
            "desc": "Etki: Minyon hasarı %80 artar. Bedel: Kendi saldırı hasarın %30 azalır.",
            "category": "minion",
            "apply": "_apply_war_commander",
        },
        {
            "id": "swarmlord",
            "name": "🐜 Sürü Lordu",
            "desc": "Etki: Minyon limitin 3, minyon saldırı hızın %20 artar. Bedeli yoktur.",
            "category": "minion",
            "apply": "_apply_swarmlord",
        },
        {
            "id": "alpha_bond",
            "name": "🐺 Alfa Bağı",
            "desc": "Etki: Tek aktif petin 2 kat hasar verir. Bedel: Aynı anda yalnızca 1 pet kullanabilirsin.",
            "category": "minion",
            "apply": "_apply_alpha_bond",
        },
        {
            "id": "spirit_link",
            "name": "🔗 Vahşi Bağı",
            "desc": "Etki: Minyonların kritik şansı %30 artar. Bedel: 20 zırh kaybedersin.",
            "category": "minion",
            "apply": "_apply_spirit_link",
        },
        # ── ELEMENTAL ─────────────────────────────────────────────────
        {
            "id": "fire_soul",
            "name": "🔥 Ateş Ruhu",
            "desc": "Etki: Tüm saldırılarına verdiğin hasarın %40'ı kadar ateş hasarı eklenir. Bedel: Hızın %15 azalır.",
            "category": "elemental",
            "apply": "_apply_fire_soul",
        },
        {
            "id": "frozen_time",
            "name": "❄️ Donmuş Zaman",
            "desc": "Etki: Her 15 saniyede yakındaki düşmanları dondurur. Bedel: Verdiğin hasar %15 azalır.",
            "category": "elemental",
            "apply": "_apply_frozen_time",
        },
        {
            "id": "storm_caller",
            "name": "⚡ Fırtına Çağırıcı",
            "desc": "Etki: Her 8. vuruşunda hedefe yıldırım düşer. Bedel: Maksimum can %15 azalır.",
            "category": "elemental",
            "apply": "_apply_storm_caller",
        },
        {
            "id": "void_touch",
            "name": "🔮 Karanlık Dokunuş",
            "desc": "Etki: Hasarın %50 artar ve düşman zırhını tamamen yok sayarsın. Bedel: %30 daha fazla hasar alırsın.",
            "category": "elemental",
            "apply": "_apply_void_touch",
        },
        {
            "id": "poison_master",
            "name": "🧪 Zehir Ustası",
            "desc": "Etki: Zehir, yanma ve diğer zamanla işleyen hasarların %25 artar. Bedeli yoktur.",
            "category": "elemental",
            "apply": "_apply_poison_master",
        },
        {
            "id": "toxic_blood",
            "name": "🩸 Toksik Kan",
            "desc": "Etki: Zehir saldırılarına saniyede 20 sabit hasar ekler. Bedel: Can yenilenmen saniyede 1 azalır.",
            "category": "elemental",
            "apply": "_apply_toxic_blood",
        },
        {
            "id": "venomous_strike",
            "name": "🐍 Zehirli Vuruş",
            "desc": "Etki: Zamanla işleyen hasarın %40 artar. Bedel: Doğrudan vuruş hasarın %20 azalır.",
            "category": "elemental",
            "apply": "_apply_venomous_strike",
        },
        {
            "id": "mana_overload",
            "name": "🔮 Büyü Taşması",
            "desc": "Etki: Eser bekleme süreleri %50 azalır. Bedel: Her eser kullanımında 10 can kaybedersin.",
            "category": "elemental",
            "apply": "_apply_mana_overload",
        },
        # ── CURSE ─────────────────────────────────────────────────────
        {
            "id": "death_wish",
            "name": "☠️ Ölüm Dileği",
            "desc": "Etki: Verdiğin hasar 3 katına çıkar. Bedel: Canın 1'in altına inmese de her saniye 1 can kaybedersin.",
            "category": "curse",
            "apply": "_apply_death_wish",
        },
        {
            "id": "cursed_blood",
            "name": "🩸 Lanetli Kan",
            "desc": "Etki: Her düşman öldürmede 2 can yenilersin. Bedel: Diğer pasif can yenilenmeleri durur.",
            "category": "curse",
            "apply": "_apply_cursed_blood",
        },
        {
            "id": "glass_bones",
            "name": "💔 Cam Kemikler",
            "desc": "Etki: Kritik şansın %50 artar. Bedel: Düşmanlardan 2 kat hasar alırsın.",
            "category": "curse",
            "apply": "_apply_glass_bones",
        },
        {
            "id": "pact_devil",
            "name": "😈 Şeytan Paktı",
            "desc": "Etki: İlk 5 dalga boyunca ölümcül hasar alamazsın. Bedel: Sonrasında verdiğin hasar kalıcı olarak %40 azalır.",
            "category": "curse",
            "apply": "_apply_pact_devil",
        },
    ]

    # HUD'da kaynak ayrımı yapabilmek için kartların doğrudan stat katkıları.
    # Koşullu/pasif etkiler kart açıklamalarında kalır; burada yalnızca oyuncunun
    # hesaplanan stat havuzuna eklenen sayısal değerler bulunur.
    CARD_STAT_BONUSES = {
        "iron_will": {"max_hp": 50},
        "zombie_skin": {"max_hp": -20},
        "blood_pact": {"max_hp": -15},
        "iron_skin": {"armor": 80},
        "phoenix_blood": {"max_hp": -10},
        "adrenaline": {"armor": -30},
        "blood_fire": {"max_hp": -30},
        "chaos_theory": {"dmgMult": 1.0, "fireRate": -0.4},
        "glass_cannon": {"fireRate": 0.5},
        "death_pact": {"max_hp": -99, "critChance": 1.0},
        "double_edge": {"dmgMult": 1.2},
        "crit_overload": {"critDmg": 2.0, "armor": -40},
        "executioner": {"fireRate": -0.3},
        "ice_shirt": {"armor": 50},
        "vampire_touch": {"lifesteal": 0.15, "regen": 2, "max_hp": -20},
        "gold_fever": {"goldGain": 0.6, "xpGain": -0.3},
        "lucky_charm": {"magicFind": 0.4, "dmgMult": -0.15},
        "accelerator": {"speed": 1.5, "armor": -30},
        "merchant_soul": {"dmgMult": -0.2},
        "undead_army": {"dmgMult": -0.15},
        "war_commander": {"minionDamage": 0.8, "dmgMult": -0.3},
        "swarmlord": {"minionCount": 3, "minionAttackSpeed": 0.2},
        "alpha_bond": {"minionDamage": 1.0, "minionCount": -10},
        "spirit_link": {"minionCrit": 0.3, "armor": -20},
        "fire_soul": {"fireDamage": 20, "fireDmgFlat": 10},
        "frozen_time": {"dmgMult": -0.15},
        "storm_caller": {"max_hp": -15},
        "void_touch": {"dmgMult": 0.5, "armorPen": 1.0},
        "poison_master": {"dotDmgMult": 0.25},
        "toxic_blood": {"poisonDps": 20, "hpRegen": -1},
        "venomous_strike": {"dotDmgMult": 0.4, "dmgMult": -0.2},
        "mana_overload": {"cooldownReduction": 0.5},
        "death_wish": {"dmgMult": 2.0},
        "glass_bones": {"critChance": 0.5},
    }


    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def apply_card(self, card_id: str, player) -> bool:
        """Verilen kart id'sine göre ilgili _apply_ metodunu çağrır."""
        for card in self.CARDS:
            if card["id"] == card_id:
                method = getattr(self, card["apply"], None)
                if method:
                    method(player)
                    if card_id not in self.active_cards:
                        self.active_cards.append(card_id)
                    # Check for synergies
                    if hasattr(self, 'synergy_system'):
                        new_synergy = self.synergy_system.check_synergies(self.active_cards, player)
                        if new_synergy and hasattr(player, 'game') and player.game:
                            player.game.add_event("damage_text", player.x, player.y - 50, value=f"Sinerji Aktif: {new_synergy['name']}", color=(255, 215, 0), timer=3.0)
                    return True
        return False

    def offer_cards(self, count: int = 3) -> list:
        """Henüz aktif olmayan kartlardan rastgele `count` adet sunar."""
        available = [c for c in self.CARDS if c["id"] not in self.active_cards]
        return random.sample(available, min(count, len(available)))

    def get_active_card_names(self) -> list:
        return [c["name"] for c in self.CARDS if c["id"] in self.active_cards]

    def get_stat_contributions(self) -> dict:
        """Aktif kart ve onların açtığı sinerjilerin ham stat katkılarını döndürür."""
        totals = {}
        active = set(self.active_cards)

        for card_id in active:
            for stat, value in self.CARD_STAT_BONUSES.get(card_id, {}).items():
                totals[stat] = totals.get(stat, 0) + value

        for synergy in self.synergy_system.SYNERGIES:
            if all(card_id in active for card_id in synergy["required_cards"]):
                for stat, value in synergy.get("bonus", {}).items():
                    totals[stat] = totals.get(stat, 0) + value

        return totals

    # ------------------------------------------------------------------
    # SURVIVAL CARDS
    # ------------------------------------------------------------------

    def _apply_iron_will(self, player):
        """🛡️ Demir İrade — +50 Max HP, pasif kalkan (60sn CD)."""
        sp = getattr(player, "skills_permanent", {})
        sp["max_hp"] = sp.get("max_hp", 0) + 50
        player.skills_permanent = sp
        player.hp = min(getattr(player, "hp", 100), getattr(player, "max_hp", 100))
        player.passive_shield_cd = 60
        player.speed_mod = getattr(player, "speed_mod", 1.0) - 0.10

    def _apply_zombie_skin(self, player):
        """🧟 Zombi Derisi — Bir kez ölümden dönüş, Max HP -%20."""
        sp = getattr(player, "skills_permanent", {})
        sp["max_hp"] = sp.get("max_hp", 0) - 20
        player.skills_permanent = sp
        player.hp = min(getattr(player, "hp", 100), getattr(player, "max_hp", 100))
        player.revive_count = getattr(player, "revive_count", 0) + 1

    def _apply_blood_pact(self, player):
        """🩸 Kan Paktı — Her hasar alışta +5 XP. Max HP -%15."""
        sp = getattr(player, "skills_permanent", {})
        sp["max_hp"] = sp.get("max_hp", 0) - 15
        player.skills_permanent = sp
        player.hp = min(getattr(player, "hp", 100), getattr(player, "max_hp", 100))
        player.xp_on_hit_bonus = getattr(player, "xp_on_hit_bonus", 0) + 5

    def _apply_iron_skin(self, player):
        """🪨 Taş Deri — Zırh +80, hız -%30."""
        sp = getattr(player, "skills_permanent", {})
        sp["armor"] = sp.get("armor", 0) + 80
        player.skills_permanent = sp
        player.speed_mod = getattr(player, "speed_mod", 1.0) - 0.3

    def _apply_berserker_rage(self, player):
        """😡 Berserker Öfkesi — %40 HP altındayken hasar +%80 (pasif)."""
        player.berserker_rage = True
        sp = getattr(player, "skills_permanent", {}); sp["regen"] = -999; player.skills_permanent = sp

    def _apply_phoenix_blood(self, player):
        """🔆 Anka Kanı — Ölünce 200 AoE hasar (1 kez)."""
        player.death_explosion = True
        sp = getattr(player, "skills_permanent", {})
        sp["max_hp"] = sp.get("max_hp", 0) - 10
        player.skills_permanent = sp
        player.hp = min(getattr(player, "hp", 100), getattr(player, "max_hp", 100))

    def _apply_adrenaline(self, player):
        """💉 Adrenalin — Her 20sn, 5sn +%30 hız +%20 hasar."""
        player.adrenaline_active = True
        sp = getattr(player, "skills_permanent", {}); sp["armor"] = sp.get("armor", 0) - 30; player.skills_permanent = sp

    # ------------------------------------------------------------------
    # OFFENSE CARDS
    # ------------------------------------------------------------------

    def _apply_blood_fire(self, player):
        """🔥 Kan Ateşi — Lifesteal +5, Max HP -%30."""
        sp = getattr(player, "skills_permanent", {})
        sp["max_hp"] = sp.get("max_hp", 0) - 30
        player.skills_permanent = sp
        player.hp = min(getattr(player, "hp", 100), getattr(player, "max_hp", 100))
        player.lifesteal_bonus = getattr(player, "lifesteal_bonus", 0) + 5

    def _apply_chaos_theory(self, player):
        """🌀 Kaos Teorisi — Hasar çarpanı x2."""
        sp = getattr(player, "skills_permanent", {})
        sp["dmgMult"] = sp.get("dmgMult", 0) + 1.0
        sp["fireRate"] = sp.get("fireRate", 0) - 0.4
        player.skills_permanent = sp

    def _apply_glass_cannon(self, player):
        """🧨 Cam Top — Ateş hızı +%50, alınan hasar x2."""
        sp = getattr(player, "skills_permanent", {})
        sp["fireRate"] = sp.get("fireRate", 0) + 0.5
        player.skills_permanent = sp
        player.damage_taken_mult = getattr(player, "damage_taken_mult", 1.0) * 2.0

    def _apply_death_pact(self, player):
        """💀 Ölüm Anlaşması — Krit şans +%100, Max HP = 1."""
        sp = getattr(player, "skills_permanent", {})
        sp["max_hp"] = sp.get("max_hp", 0) - 99
        sp["critChance"] = sp.get("critChance", 0) + 1.0
        player.skills_permanent = sp
        player.hp = 1

    def _apply_double_edge(self, player):
        """⚔️ Çift Ağız — Hasar +%120, her vuruşta %2 Max HP kendine hasar."""
        sp = getattr(player, "skills_permanent", {})
        sp["dmgMult"] = sp.get("dmgMult", 0) + 1.2
        player.skills_permanent = sp
        player.self_dmg_on_hit = 0.02

    def _apply_poison_heart(self, player):
        """💚 Zehirli Kalp — Tüm hasar zehire dönüşür, fiziksel hasar = 0."""
        player.poison_convert = True
        sp = getattr(player, "skills_permanent", {})
        sp["physDmg"] = 0
        player.skills_permanent = sp

    def _apply_crit_overload(self, player):
        """⚡ Kritik Aşırı Yük — Krit hasar +%200, krit sersemletme 0.5sn."""
        sp = getattr(player, "skills_permanent", {})
        sp["critDmg"] = sp.get("critDmg", 0) + 2.0
        player.skills_permanent = sp
        player.stun_on_crit = 0.5
        sp["armor"] = sp.get("armor", 0) - 40

    def _apply_executioner(self, player):
        """🪓 Cellat — %30 HP altındaki düşmanları anında öldür, ateş hızı -%30."""
        player.execute_threshold = 0.30
        sp = getattr(player, "skills_permanent", {})
        sp["fireRate"] = sp.get("fireRate", 0) - 0.3
        player.skills_permanent = sp

    # ------------------------------------------------------------------
    # SUPPORT CARDS
    # ------------------------------------------------------------------

    def _apply_ice_shirt(self, player):
        """🧊 Buz Gömleği — Zırh +50, hız -%20."""
        sp = getattr(player, "skills_permanent", {})
        sp["armor"] = sp.get("armor", 0) + 50
        player.skills_permanent = sp
        player.speed_mod = getattr(player, "speed_mod", 1.0) - 0.2

    def _apply_vampire_touch(self, player):
        """🦷 Vampir Dokunuşu — Lifesteal +%15, HP rejen +2."""
        sp = getattr(player, "skills_permanent", {})
        sp["lifesteal"] = sp.get("lifesteal", 0) + 0.15
        sp["regen"] = sp.get("regen", 0) + 2
        sp["max_hp"] = sp.get("max_hp", 0) - 20
        player.skills_permanent = sp
        player.hp = min(getattr(player, "hp", 100), getattr(player, "max_hp", 100))

    def _apply_gold_fever(self, player):
        """💰 Altın Humması — Altın dropu +%60, XP -%30."""
        sp = getattr(player, "skills_permanent", {})
        sp["goldGain"] = sp.get("goldGain", 0) + 0.6
        sp["xpGain"] = sp.get("xpGain", 0) - 0.3
        player.skills_permanent = sp

    def _apply_lucky_charm(self, player):
        """🍀 Şans Tılsımı — Magic find +%40, hasar -%15."""
        sp = getattr(player, "skills_permanent", {})
        sp["magicFind"] = sp.get("magicFind", 0) + 0.4
        sp["dmgMult"] = sp.get("dmgMult", 0) - 0.15
        player.skills_permanent = sp

    def _apply_accelerator(self, player):
        """🚀 İvmeleyici — Hız +%50, zırh -%30."""
        sp = getattr(player, "skills_permanent", {})
        sp["speed"] = sp.get("speed", 0) + 1.5
        sp["armor"] = sp.get("armor", 0) - 30
        player.skills_permanent = sp

    def _apply_merchant_soul(self, player):
        """🪙 Tüccar Ruhu — Market indirimi %50, hasar -%20."""
        player.shop_discount = 0.5
        sp = getattr(player, "skills_permanent", {})
        sp["dmgMult"] = sp.get("dmgMult", 0) - 0.2
        player.skills_permanent = sp

    # ------------------------------------------------------------------
    # MINION CARDS
    # ------------------------------------------------------------------

    def _apply_undead_army(self, player):
        """💀 Ölümsüz Ordu — %15 minyon dönüş şansı."""
        player.minion_respawn_chance = 0.15
        sp = getattr(player, "skills_permanent", {}); sp["dmgMult"] = sp.get("dmgMult", 0) - 0.15; player.skills_permanent = sp

    def _apply_war_commander(self, player):
        """🎖️ Savaş Komutanı — Minyon hasarı +%80, kendi hasarı -%30."""
        sp = getattr(player, "skills_permanent", {})
        sp["minionDamage"] = sp.get("minionDamage", 0) + 0.8
        sp["dmgMult"] = sp.get("dmgMult", 0) - 0.3
        player.skills_permanent = sp

    def _apply_swarmlord(self, player):
        """🐜 Sürü Lordu — Minyon sayısı +3, minyon saldırı hızı +%20."""
        sp = getattr(player, "skills_permanent", {})
        sp["minionCount"] = sp.get("minionCount", 0) + 3
        sp["minionAttackSpeed"] = sp.get("minionAttackSpeed", 0) + 0.20
        player.skills_permanent = sp

    def _apply_alpha_bond(self, player):
        """🐺 Alfa Bağı — Pet hasarı x2, yalnızca 1 aktif pet."""
        sp = getattr(player, "skills_permanent", {})
        sp["minionDamage"] = sp.get("minionDamage", 0) + 1.0
        sp["minionCount"] = sp.get("minionCount", 0) - 10
        player.skills_permanent = sp
        player.alpha_mode = True

    def _apply_spirit_link(self, player):
        """🔗 Vahşi Bağı — Minyon kritik şansı +%30."""
        sp = getattr(player, "skills_permanent", {})
        sp["minionCrit"] = sp.get("minionCrit", 0) + 0.30
        sp["armor"] = sp.get("armor", 0) - 20
        player.skills_permanent = sp

    # ------------------------------------------------------------------
    # ELEMENTAL CARDS
    # ------------------------------------------------------------------

    def _apply_fire_soul(self, player):
        """🔥 Ateş Ruhu — Ateş hasarı bonusları eklenir."""
        sp = getattr(player, "skills_permanent", {})
        sp["fireDamage"] = sp.get("fireDamage", 0) + 20
        sp["fireDmgFlat"] = sp.get("fireDmgFlat", 0) + 10
        player.skills_permanent = sp
        player.speed_mod = getattr(player, "speed_mod", 1.0) - 0.15

    def _apply_frozen_time(self, player):
        """❄️ Donmuş Zaman — Her 15sn tüm düşmanları 3sn dondurur."""
        player.periodic_freeze_cd = 15
        sp = getattr(player, "skills_permanent", {}); sp["dmgMult"] = sp.get("dmgMult", 0) - 0.15; player.skills_permanent = sp

    def _apply_storm_caller(self, player):
        """⚡ Fırtına Çağırıcı — Her 8 vuruşta yıldırım."""
        player.lightning_proc_hits = 8
        sp = getattr(player, "skills_permanent", {})
        sp["max_hp"] = sp.get("max_hp", 0) - 15
        player.skills_permanent = sp
        player.hp = min(getattr(player, "hp", 100), getattr(player, "max_hp", 100))

    def _apply_void_touch(self, player):
        """🔮 Karanlık Dokunuş - Hasar +%50, zırh delme tam."""
        sp = getattr(player, "skills_permanent", {})
        sp["dmgMult"] = sp.get("dmgMult", 0) + 0.5
        sp["armorPen"] = sp.get("armorPen", 0) + 1.0
        player.skills_permanent = sp
        player.damage_taken_mult = getattr(player, "damage_taken_mult", 1.0) * 1.30

    def _apply_poison_master(self, player):
        """🧪 Zehir Ustası - Zehir/DoT Hasarı +%25 artar."""
        sp = getattr(player, "skills_permanent", {})
        sp["dotDmgMult"] = sp.get("dotDmgMult", 0) + 0.25
        player.skills_permanent = sp

    def _apply_toxic_blood(self, player):
        """🩸 Toksik Kan - Sabit Zehir Hasarı +20, HP Regen -1."""
        sp = getattr(player, "skills_permanent", {})
        sp["poisonDps"] = sp.get("poisonDps", 0) + 20
        sp["hpRegen"] = sp.get("hpRegen", 0) - 1
        player.skills_permanent = sp

    def _apply_venomous_strike(self, player):
        """🐍 Zehirli Vuruş - DoT +%40, Direkt Hasar -%20."""
        sp = getattr(player, "skills_permanent", {})
        sp["dotDmgMult"] = sp.get("dotDmgMult", 0) + 0.40
        sp["dmgMult"] = sp.get("dmgMult", 0) - 0.20
        player.skills_permanent = sp

    def _apply_mana_overload(self, player):
        """🔮 Büyü Taşması — CD -%50, kullanımda -10 HP."""
        sp = getattr(player, "skills_permanent", {})
        sp["cooldownReduction"] = sp.get("cooldownReduction", 0) + 0.5
        player.skills_permanent = sp
        player.artifact_hp_cost = 10

    # ------------------------------------------------------------------
    # CURSE CARDS
    # ------------------------------------------------------------------

    def _apply_death_wish(self, player):
        """☠️ Ölüm Dileği — Her sn -1 HP, hasar x3."""
        sp = getattr(player, "skills_permanent", {})
        sp["dmgMult"] = sp.get("dmgMult", 0) + 2.0
        player.skills_permanent = sp
        player.passive_hp_drain = 1.0

    def _apply_cursed_blood(self, player):
        """🩸 Lanetli Kan — Her öldürmede +2 HP, rejen durur."""
        player.kill_hp_bonus = getattr(player, "kill_hp_bonus", 0) + 2
        sp = getattr(player, "skills_permanent", {})
        sp["regen"] = -999  # Oyun mantığında 0'a sıkıştırılır
        player.skills_permanent = sp

    def _apply_glass_bones(self, player):
        """💔 Cam Kemikler — Krit şans +%50, alınan hasar x2."""
        sp = getattr(player, "skills_permanent", {})
        sp["critChance"] = sp.get("critChance", 0) + 0.5
        player.skills_permanent = sp
        player.damage_taken_mult = getattr(player, "damage_taken_mult", 1.0) * 2.0

    def _apply_pact_devil(self, player):
        """😈 Şeytan Paktı — İlk 5 dalga ölümsüz, sonra hasar -%40."""
        player.pact_devil_waves = 5
