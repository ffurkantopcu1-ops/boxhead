import random


from logic.synergy_system import SynergySystem
from logic.data_loader import load_data

_CARDS = load_data('cards')

class CardSystem:
    def __init__(self):
        self.active_cards = []
        self.synergy_system = SynergySystem()

    # ------------------------------------------------------------------
    # CARDS LIST
    # ------------------------------------------------------------------
    # Kaynak: data/cards.json (stat katkilari her kartin 'stats' alaninda)
    CARDS = _CARDS

    # HUD'da kaynak ayrimi icin kartlarin dogrudan stat katkilari;
    # kosullu/pasif etkiler _apply_* metodlarinda kalir.
    CARD_STAT_BONUSES = {c['id']: c['stats'] for c in _CARDS if 'stats' in c}

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
        """💀 Ölüm Anlaşması — Krit şans +%100, Max HP %90 azalır (çarpımsal).
        Bedel recalculate_stats'ta aktif kart kontrolüyle uygulanır; additive
        havuzda Canlılık skiliyle sulandırılamaz (S5)."""
        sp = getattr(player, "skills_permanent", {})
        sp["critChance"] = sp.get("critChance", 0) + 1.0
        player.skills_permanent = sp
        # Recalc'ın kartı görmesi için aktif listeye şimdi ekle (apply_card idempotent)
        if "death_pact" not in self.active_cards:
            self.active_cards.append("death_pact")
        player.inv_manager.recalculate_stats()
        player.hp = min(player.hp, player.max_hp)

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
        """🐜 Sürü Lordu — Minyon sayısı +2, minyon saldırı hızı +%20, kendi hasarı -%20."""
        sp = getattr(player, "skills_permanent", {})
        sp["minionCount"] = sp.get("minionCount", 0) + 2
        sp["minionAttackSpeed"] = sp.get("minionAttackSpeed", 0) + 0.20
        sp["dmgMult"] = sp.get("dmgMult", 0) - 0.20
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


    def _apply_shadow_clone(self, player):
        setattr(player, "has_shadow_clone", True)
        
    def _apply_midas_touch(self, player):
        setattr(player, "has_midas_touch", True)

    def _apply_mutation(self, player):
        setattr(player, "has_mutation", True)

    def _apply_static_armor(self, player):
        setattr(player, "has_static_armor", True)

    def _apply_ricochet_master(self, player):
        setattr(player, "has_ricochet_master", True)

    def _apply_blood_bank(self, player):
        setattr(player, "has_blood_bank", True)
        setattr(player, "blood_bank_amount", 0)

    def _apply_chaos_field(self, player):
        setattr(player, "has_chaos_field", True)

    def _apply_doppelganger(self, player):
        setattr(player, "has_doppelganger", True)
        
    def _apply_furnace(self, player):
        setattr(player, "has_furnace", True)


# --- Veri dogrulamasi (acilista bir kez) ---
_card_ids = {c['id'] for c in CardSystem.CARDS}
for _card in CardSystem.CARDS:
    if not hasattr(CardSystem, _card['apply']):
        raise ValueError(f"cards.json: '{_card['id']}' kartinin apply metodu tanimsiz: {_card['apply']}")
for _syn in SynergySystem.SYNERGIES:
    _missing = [cid for cid in _syn['required_cards'] if cid not in _card_ids]
    if _missing:
        raise ValueError(f"synergies.json: '{_syn['id']}' sinerjisi olmayan kartlara referans veriyor: {_missing}")
