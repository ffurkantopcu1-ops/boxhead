import random


from logic.synergy_system import SynergySystem
from logic.data_loader import load_data

_CARDS = load_data('cards')

class CardSystem:
    # "Efsanevi" sayılan kart kategorileri: lanetli ve minyon kartları en
    # yüksek varyanslı/güçlü kartlar; legendary_card_chance bunları öne çeker.
    LEGENDARY_CATEGORIES = ("curse",)

    def __init__(self):
        self.active_cards = []
        self.synergy_system = SynergySystem()
        # --- KRİSTAL DÜKKÂNI YÜKSELTMELERİ (G2) ---
        # card_count / legendary_card_chance hiçbir yerden okunmuyordu; kart
        # sistemi meta'yı kendisi okur (GameLogic offer_cards'ı argümansız çağırır).
        self.bonus_card_count = 0
        self.legendary_chance = 0.0
        self.pending_start_card = False
        self._load_meta_bonuses()

    def _load_meta_bonuses(self):
        """meta.json'daki kart yükseltmelerini oku (oyun başında bir kez)."""
        try:
            from logic.save_manager import SaveManager
            from logic.crystal_shop import CrystalShop
            meta = SaveManager.load_meta()
            shop = CrystalShop()
            self.bonus_card_count = max(0, int(shop.get_effective(meta, "card_count")))
            self.legendary_chance = min(0.9, max(0.0, float(shop.get_effective(meta, "legendary_card_chance"))))
            self.pending_start_card = shop.get_effective(meta, "start_with_card") > 0
        except Exception as e:
            print("Kart meta bonusu okunamadi:", e)

    def grant_start_card(self, player):
        """Başlangıç Kartı yükseltmesi: koşunun başında 1 rastgele kart verir.

        Çağrı noktası GameLogic.__init__ (oyuncu ve inv_manager hazır olduktan
        sonra) olmalıdır; Player.__init__ sırasında inv_manager henüz yok.
        """
        if not self.pending_start_card:
            return None
        self.pending_start_card = False
        offered = self.offer_cards(1, player_class=getattr(player, "base_class_id", None))
        if not offered:
            return None
        self.apply_card(offered[0]["id"], player)
        return offered[0]

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
                    # _apply_* metodlari yalnizca skills_permanent'a yaziyor;
                    # recalc cagrilmadan kartlarin cogu etkisiz kaliyordu (C1)
                    if hasattr(player, 'inv_manager'):
                        player.inv_manager.recalculate_stats()
                        player.hp = min(player.hp, player.max_hp)
                    # Check for synergies
                    if hasattr(self, 'synergy_system'):
                        new_synergy = self.synergy_system.check_synergies(self.active_cards, player)
                        if new_synergy and hasattr(player, 'game') and player.game:
                            player.game.add_event("damage_text", player.x, player.y - 50, value=f"Sinerji Aktif: {new_synergy['name']}", color=(255, 215, 0), timer=3.0)
                    return True
        return False

    @staticmethod
    def _card_allowed(card, player_class):
        """Sinif-uyumu (affinity) filtresi.

        `affinity` alani olmayan kartlar EVRENSELDIR (herkese sunulur). Alani
        olanlar yalnizca listedeki siniflara sunulur; boylece bir savasciya
        taret karti, bir nisanciya minyon karti gibi OLU secimler gelmez.
        player_class None ise (sinif bilinmiyor) filtre uygulanmaz - geriye
        donuk uyumluluk."""
        aff = card.get("affinity")
        if not aff or player_class is None:
            return True
        return player_class in aff

    def offer_cards(self, count: int = None, player_class: str = None) -> list:
        """Henüz aktif olmayan kartlardan rastgele `count` adet sunar.

        count verilmezse taban 3 + "Kart Görünürlüğü" kristal yükseltmesi
        kullanılır. "Efsane Kart Şansı" yükseltmesi her slot için lanetli
        kartların çıkma olasılığını artırır (G2). player_class verilirse
        sinif-uyumlu olmayan (affinity) kartlar elenir (bkz. _card_allowed).
        """
        if count is None:
            count = 3 + self.bonus_card_count
        available = [c for c in self.CARDS
                     if c["id"] not in self.active_cards
                     and self._card_allowed(c, player_class)]
        count = min(count, len(available))
        if count <= 0:
            return []

        chosen = []
        if self.legendary_chance > 0:
            legendary_pool = [c for c in available
                              if c.get("category") in self.LEGENDARY_CATEGORIES]
            for _ in range(count):
                if not legendary_pool:
                    break
                if random.random() >= self.legendary_chance:
                    continue
                pick = random.choice(legendary_pool)
                chosen.append(pick)
                available.remove(pick)
                legendary_pool.remove(pick)

        remaining = count - len(chosen)
        if remaining > 0:
            chosen.extend(random.sample(available, min(remaining, len(available))))
        random.shuffle(chosen)
        return chosen

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
        # speed_mod her karede StatusEffectManager tarafindan siliniyor;
        # kalici hiz cezalari skills_permanent uzerinden uygulanir (H3)
        sp["speed"] = sp.get("speed", 0) - 0.3

    def _apply_zombie_skin(self, player):
        """🧟 Zombi Derisi — Bir kez ölümden dönüş, Max HP -%20."""
        sp = getattr(player, "skills_permanent", {})
        # F8: bedel YÜZDESEL (max_hp_pct havuzu). Düz -20 geç oyunda (1000+ can)
        # hissedilmiyordu; artık açıklamadaki "%20 azalır" ile birebir örtüşür.
        sp["max_hp_pct"] = sp.get("max_hp_pct", 0) - 20
        player.skills_permanent = sp
        player.hp = min(getattr(player, "hp", 100), getattr(player, "max_hp", 100))
        player.revive_count = getattr(player, "revive_count", 0) + 1

    def _apply_blood_pact(self, player):
        """🩸 Kan Paktı — Her hasar alışta +5 XP. Max HP -%15."""
        sp = getattr(player, "skills_permanent", {})
        sp["max_hp_pct"] = sp.get("max_hp_pct", 0) - 15
        player.skills_permanent = sp
        player.hp = min(getattr(player, "hp", 100), getattr(player, "max_hp", 100))
        player.xp_on_hit_bonus = getattr(player, "xp_on_hit_bonus", 0) + 5

    def _apply_iron_skin(self, player):
        """🪨 Taş Deri — Zırh +80, hız -%30."""
        sp = getattr(player, "skills_permanent", {})
        sp["armor"] = sp.get("armor", 0) + 80
        sp["speed"] = sp.get("speed", 0) - 0.9  # H3: kalici hiz cezasi
        player.skills_permanent = sp

    def _apply_berserker_rage(self, player):
        """😡 Berserker Öfkesi — %40 HP altındayken hasar +%80 (pasif)."""
        player.berserker_rage = True
        sp = getattr(player, "skills_permanent", {}); sp["regen"] = -999; player.skills_permanent = sp

    def _apply_phoenix_blood(self, player):
        """🔆 Anka Kanı — Ölünce 200 AoE hasar (1 kez)."""
        player.death_explosion = True
        sp = getattr(player, "skills_permanent", {})
        sp["max_hp_pct"] = sp.get("max_hp_pct", 0) - 10
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
        sp["max_hp_pct"] = sp.get("max_hp_pct", 0) - 30
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
        # Tuketim noktasi enemy.take_damage'daki lowHpExec stati (P3)
        sp["lowHpExec"] = sp.get("lowHpExec", 0) + 0.30
        player.skills_permanent = sp

    # ------------------------------------------------------------------
    # SUPPORT CARDS
    # ------------------------------------------------------------------

    def _apply_ice_shirt(self, player):
        """🧊 Buz Gömleği — Zırh +50, hız -%20."""
        sp = getattr(player, "skills_permanent", {})
        sp["armor"] = sp.get("armor", 0) + 50
        sp["speed"] = sp.get("speed", 0) - 0.6  # H3: kalici hiz cezasi
        player.skills_permanent = sp

    def _apply_vampire_touch(self, player):
        """🦷 Vampir Dokunuşu — Lifesteal +%15, HP rejen +2."""
        sp = getattr(player, "skills_permanent", {})
        sp["lifesteal"] = sp.get("lifesteal", 0) + 0.15
        sp["regen"] = sp.get("regen", 0) + 2
        sp["max_hp_pct"] = sp.get("max_hp_pct", 0) - 20
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
        # "1 aktif pet" bedeli minionCount -10 ile degil alpha_mode bayragiyla
        # uygulanir; negatif sayi check_minions'ta pop() cokmesi yaratiyordu (C5)
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
        sp["speed"] = sp.get("speed", 0) - 0.45  # H3: kalici hiz cezasi
        player.skills_permanent = sp

    def _apply_frozen_time(self, player):
        """❄️ Donmuş Zaman — Her 15sn tüm düşmanları 3sn dondurur."""
        player.periodic_freeze_cd = 15
        sp = getattr(player, "skills_permanent", {}); sp["dmgMult"] = sp.get("dmgMult", 0) - 0.15; player.skills_permanent = sp

    def _apply_storm_caller(self, player):
        """⚡ Fırtına Çağırıcı — Her 8 vuruşta yıldırım."""
        player.lightning_proc_hits = 8
        sp = getattr(player, "skills_permanent", {})
        sp["max_hp_pct"] = sp.get("max_hp_pct", 0) - 15
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
        sp = getattr(player, "skills_permanent", {})
        sp["dmgMult"] = sp.get("dmgMult", 0) - 0.2  # cards.json bedeli (H11)
        player.skills_permanent = sp

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
        sp = getattr(player, "skills_permanent", {})
        sp["armor"] = sp.get("armor", 0) - 20  # cards.json bedeli (H11)
        player.skills_permanent = sp

    def _apply_doppelganger(self, player):
        setattr(player, "has_doppelganger", True)
        sp = getattr(player, "skills_permanent", {})
        sp["dmgMult"] = sp.get("dmgMult", 0) - 0.5  # cards.json bedeli (H11)
        player.skills_permanent = sp
        
    def _apply_furnace(self, player):
        setattr(player, "has_furnace", True)

    # --- TARET KARTLARI (Mühendis) ---
    # turretCharges = R yeteneğinin şarj kapasitesi (aynı anda kaç taret
    # kurabilirsin), turretLimit = yerde aynı anda durabilecek taret sayısı.
    # İkisi farklı: şarj "ne kadar hızlı kurarsın", limit "kaç tanesi yaşar".

    def _apply_mass_production(self, player):
        """⚙️ Seri Üretim — +1 taret şarjı. Bedel: -%15 hasar."""
        sp = getattr(player, "skills_permanent", {})
        sp["turretCharges"] = sp.get("turretCharges", 0) + 1
        sp["dmgMult"] = sp.get("dmgMult", 0) - 0.15
        player.skills_permanent = sp

    def _apply_factory_line(self, player):
        """🏭 Fabrika Hattı — +1 taret limiti, +%25 taret atış hızı.
        Bedel: -%20 hareket hızı."""
        sp = getattr(player, "skills_permanent", {})
        sp["turretLimit"] = sp.get("turretLimit", 0) + 1
        sp["turretRate"] = sp.get("turretRate", 0) + 0.25
        # Hız cezası skills_permanent üzerinden: speed_mod her karede siliniyor (H3)
        sp["speed"] = sp.get("speed", 0) - 0.6
        player.skills_permanent = sp

    def _apply_overclock(self, player):
        """🔧 Aşırı Yükleme — +2 limit, +1 şarj, +%40 taret hasarı.
        Bedel: taret canı yarıya iner, max can -%15."""
        sp = getattr(player, "skills_permanent", {})
        sp["turretLimit"] = sp.get("turretLimit", 0) + 2
        sp["turretCharges"] = sp.get("turretCharges", 0) + 1
        sp["turretDmg"] = sp.get("turretDmg", 0) + 0.4
        sp["max_hp_pct"] = sp.get("max_hp_pct", 0) - 15
        player.skills_permanent = sp
        setattr(player, "turret_hp_penalty", 0.5)

    # ------------------------------------------------------------------
    # SINIF KİMLİK KARTLARI (v1.16) — sinif-uyumlu (affinity) havuz.
    # Her biri bir bedel tasir (AGENTS.md guc butcesi). Cogu yalnizca
    # skills_permanent'a yazar; recalculate_stats bunlari toplar.
    # ------------------------------------------------------------------

    # --- BOMBACI: AoE / tuzak ---
    def _apply_bomb_barrage(self, player):
        """💣 Bomba Yağmuru — +%30 Alan. Bedel: -%15 saldırı hızı."""
        sp = getattr(player, "skills_permanent", {})
        sp["aoe_bonus"] = sp.get("aoe_bonus", 0) + 0.30
        sp["fireRate"] = sp.get("fireRate", 0) - 0.15
        player.skills_permanent = sp

    def _apply_cluster_bomb(self, player):
        """🧷 Küme Bombası — +%25 Hasar, +%15 Alan. Bedel: -0.4 hız."""
        sp = getattr(player, "skills_permanent", {})
        sp["dmgMult"] = sp.get("dmgMult", 0) + 0.25
        sp["aoe_bonus"] = sp.get("aoe_bonus", 0) + 0.15
        sp["speed"] = sp.get("speed", 0) - 0.4
        player.skills_permanent = sp

    def _apply_napalm(self, player):
        """🔥 Napalm — +12 Ateş Hasarı, +%15 Alan. Bedel: Max Can %15 azalır."""
        sp = getattr(player, "skills_permanent", {})
        sp["fireDmgFlat"] = sp.get("fireDmgFlat", 0) + 12
        sp["aoe_bonus"] = sp.get("aoe_bonus", 0) + 0.15
        sp["max_hp_pct"] = sp.get("max_hp_pct", 0) - 15
        player.skills_permanent = sp
        player.hp = min(getattr(player, "hp", 100), getattr(player, "max_hp", 100))

    def _apply_shrapnel(self, player):
        """🔩 Şarapnel — +10 Fiziksel Hasar, +1 Delme. Bedel: -0.3 hız."""
        sp = getattr(player, "skills_permanent", {})
        sp["physDmgFlat"] = sp.get("physDmgFlat", 0) + 10
        sp["pierce"] = sp.get("pierce", 0) + 1
        sp["speed"] = sp.get("speed", 0) - 0.3
        player.skills_permanent = sp

    def _apply_demolition(self, player):
        """☢️ Yıkım Uzmanı — +%50 Alan, +%20 Hasar. Bedel: %30 daha fazla hasar alırsın."""
        sp = getattr(player, "skills_permanent", {})
        sp["aoe_bonus"] = sp.get("aoe_bonus", 0) + 0.50
        sp["dmgMult"] = sp.get("dmgMult", 0) + 0.20
        player.skills_permanent = sp
        player.damage_taken_mult = getattr(player, "damage_taken_mult", 1.0) * 1.30

    # --- NİŞANCI: kritik / delme / menzil ---
    def _apply_armor_piercing(self, player):
        """🎯 Zırh Delici — +2 Delme, +%50 Zırh Delme. Bedel: -%15 saldırı hızı."""
        sp = getattr(player, "skills_permanent", {})
        sp["pierce"] = sp.get("pierce", 0) + 2
        sp["armorPen"] = sp.get("armorPen", 0) + 0.5
        sp["fireRate"] = sp.get("fireRate", 0) - 0.15
        player.skills_permanent = sp

    def _apply_headhunter(self, player):
        """💀 Kelle Avcısı — +%40 Kritik Hasar. Bedel: 30 zırh kaybedersin."""
        sp = getattr(player, "skills_permanent", {})
        sp["critDmg"] = sp.get("critDmg", 0) + 0.4
        sp["armor"] = sp.get("armor", 0) - 30
        player.skills_permanent = sp

    def _apply_deadeye(self, player):
        """👁️ Keskin Göz — +%15 Kritik Şans. Bedel: -%20 saldırı hızı."""
        sp = getattr(player, "skills_permanent", {})
        sp["critChance"] = sp.get("critChance", 0) + 0.15
        sp["fireRate"] = sp.get("fireRate", 0) - 0.20
        player.skills_permanent = sp

    def _apply_long_barrel(self, player):
        """🔭 Uzun Namlu — +%30 Hasar, +2 Mermi Hızı. Bedel: -0.5 hız."""
        sp = getattr(player, "skills_permanent", {})
        sp["dmgMult"] = sp.get("dmgMult", 0) + 0.30
        sp["bullet_speed"] = sp.get("bullet_speed", 0) + 2
        sp["speed"] = sp.get("speed", 0) - 0.5
        player.skills_permanent = sp

    # --- NİNJA: kaçınma / saldırı hızı / infaz ---
    def _apply_shadow_step(self, player):
        """🌑 Gölge Adımı — +%20 Kaçınma. Bedel: 20 zırh kaybedersin."""
        sp = getattr(player, "skills_permanent", {})
        sp["dodgeChance"] = sp.get("dodgeChance", 0) + 0.20
        sp["armor"] = sp.get("armor", 0) - 20
        player.skills_permanent = sp

    def _apply_thousand_cuts(self, player):
        """🗡️ Bin Kesik — +%30 Saldırı Hızı. Bedel: Vuruş başına hasar %20 azalır."""
        sp = getattr(player, "skills_permanent", {})
        sp["attack_speed_bonus"] = sp.get("attack_speed_bonus", 0) + 0.30
        sp["dmgMult"] = sp.get("dmgMult", 0) - 0.20
        player.skills_permanent = sp

    def _apply_assassinate(self, player):
        """🔪 Suikast — Canı %25 altındaki düşmanları infaz. Bedel: Max Can %15 azalır."""
        sp = getattr(player, "skills_permanent", {})
        sp["lowHpExec"] = sp.get("lowHpExec", 0) + 0.25
        sp["max_hp_pct"] = sp.get("max_hp_pct", 0) - 15
        player.skills_permanent = sp
        player.execute_threshold = max(getattr(player, "execute_threshold", 0.0), 0.25)
        player.hp = min(getattr(player, "hp", 100), getattr(player, "max_hp", 100))

    def _apply_swift_reflexes(self, player):
        """💨 Hızlı Refleks — +0.8 Hız, +%10 Kaçınma. Bedel: Max Can %15 azalır."""
        sp = getattr(player, "skills_permanent", {})
        sp["speed"] = sp.get("speed", 0) + 0.8
        sp["dodgeChance"] = sp.get("dodgeChance", 0) + 0.10
        sp["max_hp_pct"] = sp.get("max_hp_pct", 0) - 15
        player.skills_permanent = sp
        player.hp = min(getattr(player, "hp", 100), getattr(player, "max_hp", 100))

    # --- SAVAŞÇI: yakın dövüş / tank ---
    def _apply_rampage(self, player):
        """⚔️ Cinnet — +%40 Hasar, +30 Yakın Menzil. Bedel: Max Can %20 azalır."""
        sp = getattr(player, "skills_permanent", {})
        sp["dmgMult"] = sp.get("dmgMult", 0) + 0.40
        sp["meleeRangeFlat"] = sp.get("meleeRangeFlat", 0) + 30
        sp["max_hp_pct"] = sp.get("max_hp_pct", 0) - 20
        player.skills_permanent = sp
        player.hp = min(getattr(player, "hp", 100), getattr(player, "max_hp", 100))

    def _apply_juggernaut(self, player):
        """🐗 Ezici Güç — +60 Zırh, +80 Max Can. Bedel: -0.6 hız."""
        sp = getattr(player, "skills_permanent", {})
        sp["armor"] = sp.get("armor", 0) + 60
        sp["max_hp"] = sp.get("max_hp", 0) + 80
        sp["speed"] = sp.get("speed", 0) - 0.6
        player.skills_permanent = sp

    # --- MÜHENDİS: taret ---
    def _apply_auto_targeting(self, player):
        """🎯 Otomatik Nişan — +%30 Taret Hasarı. Bedel: Kendi hasarın %15 azalır."""
        sp = getattr(player, "skills_permanent", {})
        sp["turretDmg"] = sp.get("turretDmg", 0) + 0.30
        sp["dmgMult"] = sp.get("dmgMult", 0) - 0.15
        player.skills_permanent = sp

    def _apply_reinforced_turrets(self, player):
        """🛠️ Takviyeli Taret — +100 Taret Canı, +%20 Taret Hızı. Bedel: -0.4 hız."""
        sp = getattr(player, "skills_permanent", {})
        sp["turretMaxHp"] = sp.get("turretMaxHp", 0) + 100
        sp["turretRate"] = sp.get("turretRate", 0) + 0.20
        sp["speed"] = sp.get("speed", 0) - 0.4
        player.skills_permanent = sp

    # --- SİMYACI: DoT / alan ---
    def _apply_toxic_cloud(self, player):
        """☁️ Zehirli Bulut — +%30 DoT, +%20 Alan. Bedel: Doğrudan hasar %20 azalır."""
        sp = getattr(player, "skills_permanent", {})
        sp["dotDmgMult"] = sp.get("dotDmgMult", 0) + 0.30
        sp["aoe_bonus"] = sp.get("aoe_bonus", 0) + 0.20
        sp["dmgMult"] = sp.get("dmgMult", 0) - 0.20
        player.skills_permanent = sp

    def _apply_corrosion(self, player):
        """🧪 Aşındırma — Zırh delme tam, +15 Zehir DPS. Bedel: Max Can %15 azalır."""
        sp = getattr(player, "skills_permanent", {})
        sp["armorPen"] = sp.get("armorPen", 0) + 1.0
        sp["poisonDps"] = sp.get("poisonDps", 0) + 15
        sp["max_hp_pct"] = sp.get("max_hp_pct", 0) - 15
        player.skills_permanent = sp
        player.hp = min(getattr(player, "hp", 100), getattr(player, "max_hp", 100))

    # --- BÜYÜCÜ: elemental ---
    def _apply_arcane_surge(self, player):
        """🔮 Gizem Dalgası — +%40 Elemental Hasar. Bedel: Max Can %20 azalır."""
        sp = getattr(player, "skills_permanent", {})
        sp["elementDmgMult"] = sp.get("elementDmgMult", 0) + 0.40
        sp["max_hp_pct"] = sp.get("max_hp_pct", 0) - 20
        player.skills_permanent = sp
        player.hp = min(getattr(player, "hp", 100), getattr(player, "max_hp", 100))


# --- Veri dogrulamasi (acilista bir kez) ---
_card_ids = {c['id'] for c in CardSystem.CARDS}
for _card in CardSystem.CARDS:
    if not hasattr(CardSystem, _card['apply']):
        raise ValueError(f"cards.json: '{_card['id']}' kartinin apply metodu tanimsiz: {_card['apply']}")
for _syn in SynergySystem.SYNERGIES:
    _missing = [cid for cid in _syn['required_cards'] if cid not in _card_ids]
    if _missing:
        raise ValueError(f"synergies.json: '{_syn['id']}' sinerjisi olmayan kartlara referans veriyor: {_missing}")
