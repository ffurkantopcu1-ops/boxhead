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
            "desc": "Hasar alınca 3sn kalkan (1dk CD). +50 Max HP. Hız -%10.",
            "category": "survival",
            "apply": "_apply_iron_will",
        },
        {
            "id": "zombie_skin",
            "name": "🧟 Zombi Derisi",
            "desc": "Bir kez ölümden dönersin. Max HP -%20.",
            "category": "survival",
            "apply": "_apply_zombie_skin",
        },
        {
            "id": "blood_pact",
            "name": "🩸 Kan Paktı",
            "desc": "Her hasar alışta +5 XP kazanırsın. Max HP -%15.",
            "category": "survival",
            "apply": "_apply_blood_pact",
        },
        {
            "id": "iron_skin",
            "name": "🪨 Taş Deri",
            "desc": "Zırh +80 artar. Hareket hızı -%30.",
            "category": "survival",
            "apply": "_apply_iron_skin",
        },
        {
            "id": "berserker_rage",
            "name": "😡 Berserker Öfkesi",
            "desc": "%40 HP altındayken hasar +%80 artar. HP Yenileme durur.",
            "category": "survival",
            "apply": "_apply_berserker_rage",
        },
        {
            "id": "phoenix_blood",
            "name": "🔆 Anka Kanı",
            "desc": "Ölünce tüm düşmanlara 200 hasar verir. Max HP -%10.",
            "category": "survival",
            "apply": "_apply_phoenix_blood",
        },
        {
            "id": "adrenaline",
            "name": "💉 Adrenalin",
            "desc": "Her 20sn 5sn +%30 hız ve +%20 hasar. Zırh -30.",
            "category": "survival",
            "apply": "_apply_adrenaline",
        },
        # ── OFFENSE ───────────────────────────────────────────────────
        {
            "id": "blood_fire",
            "name": "🔥 Kan Ateşi",
            "desc": "Hasar verince +5 HP kazanırsın. Max HP -%30.",
            "category": "offense",
            "apply": "_apply_blood_fire",
        },
        {
            "id": "chaos_theory",
            "name": "🌀 Kaos Teorisi",
            "desc": "Taban hasar x2 artar. Ateş Hızı -%40.",
            "category": "offense",
            "apply": "_apply_chaos_theory",
        },
        {
            "id": "glass_cannon",
            "name": "🧨 Cam Top",
            "desc": "Saldırı hızı +%50 artar. Alınan hasar x2 olur.",
            "category": "offense",
            "apply": "_apply_glass_cannon",
        },
        {
            "id": "death_pact",
            "name": "💀 Ölüm Anlaşması",
            "desc": "Kritik Şans +%100. Maksimum Can 1e iner.",
            "category": "offense",
            "apply": "_apply_death_pact",
        },
        {
            "id": "double_edge",
            "name": "⚔️ Çift Ağız",
            "desc": "Hasar +%120 artar. Her vuruşta max HP'nin %2'si kadar kendini yaralar.",
            "category": "offense",
            "apply": "_apply_double_edge",
        },
        {
            "id": "poison_heart",
            "name": "💚 Zehirli Kalp",
            "desc": "Tüm hasarın zehire dönüşür. Anlık hasar sıfırlanır.",
            "category": "offense",
            "apply": "_apply_poison_heart",
        },
        {
            "id": "crit_overload",
            "name": "⚡ Kritik Aşırı Yük",
            "desc": "Kritik hasar +%200, sersemletir. Zırh -40.",
            "category": "offense",
            "apply": "_apply_crit_overload",
        },
        {
            "id": "executioner",
            "name": "🪓 Cellat",
            "desc": "%30 HP altındaki düşmanları anında öldürür. Ateş hızı -%30.",
            "category": "offense",
            "apply": "_apply_executioner",
        },
        # ── SUPPORT ───────────────────────────────────────────────────
        {
            "id": "ice_shirt",
            "name": "🧊 Buz Gömleği",
            "desc": "Zırh +50 artar. Hareket hızı -%20.",
            "category": "support",
            "apply": "_apply_ice_shirt",
        },
        {
            "id": "vampire_touch",
            "name": "🦷 Vampir Dokunuşu",
            "desc": "Can çalma +%15, Can yenileme +2. Max HP -%20.",
            "category": "support",
            "apply": "_apply_vampire_touch",
        },
        {
            "id": "gold_fever",
            "name": "💰 Altın Humması",
            "desc": "Altın dropu +%60 artar. XP kazanımı -%30 azalır.",
            "category": "support",
            "apply": "_apply_gold_fever",
        },
        {
            "id": "lucky_charm",
            "name": "🍀 Şans Tılsımı",
            "desc": "Nadir eşya şansı +%40 artar. Hasar -%15 azalır.",
            "category": "support",
            "apply": "_apply_lucky_charm",
        },
        {
            "id": "accelerator",
            "name": "🚀 İvmeleyici",
            "desc": "Hareket hızı +%50 artar. Zırh -%30 azalır.",
            "category": "support",
            "apply": "_apply_accelerator",
        },
        {
            "id": "merchant_soul",
            "name": "🪙 Tüccar Ruhu",
            "desc": "Market yenileme -%50 ucuzlar. Hasar -%20 azalır.",
            "category": "support",
            "apply": "_apply_merchant_soul",
        },
        # ── MINION ────────────────────────────────────────────────────
        {
            "id": "undead_army",
            "name": "💀 Ölümsüz Ordu",
            "desc": "%15 minyon dönüşüm şansı. Hasarın -%15 azalır.",
            "category": "minion",
            "apply": "_apply_undead_army",
        },
        {
            "id": "war_commander",
            "name": "🎖️ Savaş Komutanı",
            "desc": "Minyon hasarı +%80 artar. Kendi hasarın -%30 azalır.",
            "category": "minion",
            "apply": "_apply_war_commander",
        },
        {
            "id": "swarmlord",
            "name": "🐜 Sürü Lordu",
            "desc": "Minyon sayısı +3. Minyon saldırı hızı +%20.",
            "category": "minion",
            "apply": "_apply_swarmlord",
        },
        {
            "id": "alpha_bond",
            "name": "🐺 Alfa Bağı",
            "desc": "Pet hasarı x2 olur. Yalnızca 1 aktif pet olabilir.",
            "category": "minion",
            "apply": "_apply_alpha_bond",
        },
        {
            "id": "spirit_link",
            "name": "🔗 Vahşi Bağı",
            "desc": "Minyon kritik şansı +%30. Zırh -20.",
            "category": "minion",
            "apply": "_apply_spirit_link",
        },
        # ── ELEMENTAL ─────────────────────────────────────────────────
        {
            "id": "fire_soul",
            "name": "🔥 Ateş Ruhu",
            "desc": "Tüm hasara +%40 ateş hasarı eklenir. Hız -%15.",
            "category": "elemental",
            "apply": "_apply_fire_soul",
        },
        {
            "id": "frozen_time",
            "name": "❄️ Donmuş Zaman",
            "desc": "15 saniyede bir düşmanları dondurur. Hasar -%15.",
            "category": "elemental",
            "apply": "_apply_frozen_time",
        },
        {
            "id": "storm_caller",
            "name": "⚡ Fırtına Çağırıcı",
            "desc": "Her 8 vuruşta yıldırım düşer. Max HP -%15.",
            "category": "elemental",
            "apply": "_apply_storm_caller",
        },
        {
            "id": "void_touch",
            "name": "🔮 Karanlık Dokunuş",
            "desc": "Hasar +%50, zırh delme %100. Alınan hasar +%30.",
            "category": "elemental",
            "apply": "_apply_void_touch",
        },
        {
            "id": "poison_master",
            "name": "🧪 Zehir Ustası",
            "desc": "Zehir/DoT Hasarı +%25 artar.",
            "category": "elemental",
            "apply": "_apply_poison_master",
        },
        {
            "id": "toxic_blood",
            "name": "🩸 Toksik Kan",
            "desc": "Sabit Zehir Hasarı +20. HP Yenilenmesi saniyede -1 azalır.",
            "category": "elemental",
            "apply": "_apply_toxic_blood",
        },
        {
            "id": "venomous_strike",
            "name": "🐍 Zehirli Vuruş",
            "desc": "Zehir/DoT Hasarı +%40. Direkt hasar -%20 azalır.",
            "category": "elemental",
            "apply": "_apply_venomous_strike",
        },
        {
            "id": "mana_overload",
            "name": "🔮 Büyü Taşması",
            "desc": "Artifact bekleme süresi -%50. Her kullanımda -10 HP.",
            "category": "elemental",
            "apply": "_apply_mana_overload",
        },
        # ── CURSE ─────────────────────────────────────────────────────
        {
            "id": "death_wish",
            "name": "☠️ Ölüm Dileği",
            "desc": "Her saniye -1 HP kaybedersin. Ama hasar x3 olur.",
            "category": "curse",
            "apply": "_apply_death_wish",
        },
        {
            "id": "cursed_blood",
            "name": "🩸 Lanetli Kan",
            "desc": "Her öldürmede +2 HP kazanırsın. Can yenileme durur.",
            "category": "curse",
            "apply": "_apply_cursed_blood",
        },
        {
            "id": "glass_bones",
            "name": "💔 Cam Kemikler",
            "desc": "Krit şans +%50. Alınan hasar x2 olur.",
            "category": "curse",
            "apply": "_apply_glass_bones",
        },
        {
            "id": "pact_devil",
            "name": "😈 Şeytan Paktı",
            "desc": "İlk 5 dalgada ölümsüzsün. Sonrasında hasar -%40 kalıcı azalır.",
            "category": "curse",
            "apply": "_apply_pact_devil",
        },
    ]


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
