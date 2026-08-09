from logic.item_system import ItemSystem

class InventoryManager:
    # Eşya/set/aura verilerindeki eski anahtarları stat sistemine bağlar
    # (veri dosyaları değişmez -> save uyumluluğu korunur)
    STAT_ALIASES = {"maxHp": "max_hp", "attack_speed_mult": "attack_speed_bonus"}

    # Yetenek ağacı (skills) girdilerinde kullanılan eski stat adlarının yeni
    # karşılıkları. Eşya/aura tarafını bozmamak için SADECE skill döngüsünde
    # uygulanır: eski kayıtlardaki "Fedai" skili düz değer verdiği halde
    # çarpan statını besliyordu (F3).
    SKILL_STAT_MIGRATION = {"minionMaxHp": "minionMaxHpFlat"}

    # Oynanabilir sınıflar. Bir silahın weaponClass'ı yalnızca bu kümedeyse
    # sınıfı değiştirir; "general"/"none" gibi değerler sınıfsızdır.
    CLASS_IDS = frozenset({
        "warrior", "sniper", "engineer", "beastmaster",
        "ninja", "alchemist", "sorcerer", "bloodwalker", "bomber",
    })

    # Silahın "savaş ailesi". Aynı ailedeki bir silah sınıfı karakterin
    # SINIFINI DEĞİŞTİRMEZ (kimlik korunur): ninja bir vampir/kan kılıcı
    # (bloodwalker = melee) takınca ninja kalır, bloodwalker'a dönüşmez.
    # Yalnızca FARKLI aileden bir silah (ör. arbalet=ranged, taret kiti=turret)
    # sınıfı o silahın sınıfına çevirir; çünkü o saldırı tipini ancak o sınıfın
    # uzmanlığı (specialization) doğru çalıştırır.
    WEAPON_FAMILIES = {
        "warrior": "melee", "ninja": "melee", "bloodwalker": "melee",
        "sniper": "ranged", "sorcerer": "ranged",
        "alchemist": "bomb", "bomber": "bomb",
        "engineer": "turret", "beastmaster": "minion",
    }

    # Azalan getiri + mutlak tavan tablosu: stat -> (knee, k, hard_cap)
    # knee üstü: knee + excess / (1 + excess * k); hard_cap None değilse min() ile kırpılır
    SOFT_CAPS = {
        "dmgMult":        (2.0,  0.3, None),
        "critChance":     (0.75, 2.0, 1.0),
        "lifesteal":      (0.30, 3.0, 0.50),
        "dodgeChance":    (0.40, 2.0, 0.60),
        "critDmg":        (2.0,  0.5, 4.0),
        "dotDmgMult":     (1.0,  0.5, 2.0),
        "elementDmgMult": (1.5,  0.5, 3.0),
        "minionDamage":   (2.0,  0.5, 4.0),
        "fireDmgMult":    (1.0,  0.5, 2.0),
        "frostDmgMult":   (1.0,  0.5, 2.0),
        # Pet çarpanları toplanabiliyor; eski kayıtlardaki hatalı "Küçük Kurt"
        # (minionMaxHp: 50) gibi değerleri de sınırlar (F3)
        "minionMaxHp":    (13.0, 0.5, 20.0),
    }

    def __init__(self, player):
        self.player = player
        self.equipped = {
            "weapon": None,
            "helmet": None,
            "chest": None,
            "amulet": None,
            "pet": None,
            "artifact": None
        }
        
    def equip(self, item):
        slot = item.get("type", "weapon")
        if slot in self.equipped:
            old_item = self.equipped[slot]
            if old_item:
                self.player.inventory.append(old_item)
            self.equipped[slot] = item
            self.recalculate_stats()
            return True
        return False

    def unequip(self, slot):
        if slot in self.equipped and self.equipped[slot]:
            item = self.equipped[slot]
            self.player.inventory.append(item)
            self.equipped[slot] = None
            self.recalculate_stats()
            return True
        return False

    def unequip_all(self):
        for slot in self.equipped:
            self.unequip(slot)

    def _track_sold(self, count):
        """Satış görevini besler. game referansı Player.update() içinde
        atanır (player.game); henüz oyun döngüsü başlamadıysa sessizce geçer."""
        if count <= 0:
            return
        game = getattr(self.player, 'game', None)
        if game is not None and hasattr(game, 'track_quest'):
            game.track_quest("sell_items", count)

    def sell_item(self, item_index):
        if 0 <= item_index < len(self.player.inventory):
            item = self.player.inventory.pop(item_index)
            sell_price = item.get("price", 100) // 2
            self.player.gold += sell_price
            self._track_sold(1)
            return True
        return False

    def mass_sell(self, rarity=None):
        """Belirli bir nadirlikteki tüm eşyaları sat (Set, Orb ve Artifact hariç)."""
        new_inv = []
        sold_count = 0
        total_gold = 0
        
        for item in self.player.inventory:
            # KORUMALI EŞYALAR: Setler, Orblar, Artifactler
            is_protected = (
                item.get('setTag') is not None or 
                item.get('type') == 'orb' or 
                item.get('type') == 'artifact'
            )
            
            if is_protected:
                new_inv.append(item)
                continue
                
            # Rarity Filtresi (None ise hepsini sat)
            if rarity and item.get('rarity') != rarity:
                new_inv.append(item)
                continue
            
            # Satış İşlemi
            price = item.get("price", 100) // 2
            self.player.gold += price
            total_gold += price
            sold_count += 1
            
        self.player.inventory = new_inv
        self._track_sold(sold_count)
        return sold_count, total_gold

    # 🟢 SINIF TABAN STATLARI — TEK DOĞRULUK KAYNAĞI
    # Sınıf seçim ekranı da bunu okur (bkz. get_class_preview). Eskiden bu
    # sözlük recalculate_stats'ın İÇİNDE yerel değişkendi ve seçim ekranı
    # değerleri ELLE kopyalıyordu; sınıf hızlarına global %20 zam yapılınca
    # ekran güncellenmedi ve 9 sınıfın 8'inde gösterilen hız yanlış kaldı
    # (hepsi tam 1.2 kat). Artık gösterilen değer türetiliyor, yazılmıyor.
    CLASS_BASES = {
        "warrior":     {"dmgMult": 0.2,  "max_hp_mult": 0.2,  "speed": 6.0, "regen": 0.5},
        "sniper":      {"dmgMult": 0.5,  "critChance": 0.2,   "speed": 4.8, "bounce": 1, "pierce": 1, "attack_cooldown": 500},
        "engineer":    {"turretLimit": 1, "armor": 10,         "speed": 5.0},
        "beastmaster": {"minionDamage": 0.3, "max_hp_mult": 0.1, "speed": 5.5},
        "ninja":       {"attack_speed_mult": 0.3, "dodgeChance": 0.25, "speed": 7.2, "regen": 0.5},
        "alchemist":   {"aoe": 0.4,      "dotDmgMult": 0.3,   "speed": 5.0, "attack_cooldown": 900},
        # Bombacı: TUZAKÇI. Simyacı'nın uç versiyonu DEĞİL — bombası
        # patlamaz, yere tetiklemeli mayın bırakır (bkz. bomber_logic).
        # Anlık hasar yok, hasar mayın tetiklenince tek seferde gelir.
        # Erken oyun hasarı çok düşük hissettiriyordu: dmgMult 0.2->0.35
        # (dmgMult bomba/poisonDps'i çarpar) ve vuruş aralığı 1500->1300ms
        # (daha hızlı mayın döşeme). Yine de oyunun en yavaş sınıfı.
        "bomber":      {"aoe": 0.6,      "dmgMult": 0.35,     "speed": 4.4, "attack_cooldown": 1300},
        # --- YENİ SINIFLAR ---
        "sorcerer":    {"elementDmgMult": 0.6, "max_hp_mult": -0.30, "speed": 4.8, "attack_cooldown": 400},
        "bloodwalker": {"dmgMult": 0.4,  "lifesteal": 0.20,   "speed": 5.5, "regen": 0.5},
    }

    # Sınıf kartında gösterilecek statlar: (anahtar, etiket, biçim).
    # Sıra önemli — kartta bu sırayla çıkar. "pct" yüzdeye çevirir,
    # "flat" tam sayı olarak +N yazar, "raw" ham sayıyı basar.
    CLASS_PREVIEW_STATS = [
        ("max_hp_mult",       "HP",     "pct"),
        ("dmgMult",           "Hasar",  "pct"),
        ("speed",             "Hız",    "raw"),
        ("armor",             "Zırh",   "flat"),
        ("critChance",        "Kritik", "pct"),
        ("attack_speed_mult", "S.Hızı", "pct"),
        ("dodgeChance",       "Dodge",  "pct"),
        ("aoe",               "Alan",   "pct"),
        ("dotDmgMult",        "DoT",    "pct"),
        ("elementDmgMult",    "Elem",   "pct"),
        ("lifesteal",         "Emme",   "pct"),
        ("minionDamage",      "Minyon", "pct"),
        ("turretLimit",       "Taret",  "flat"),
        ("bounce",            "Sekme",  "flat"),
        ("pierce",            "Delme",  "flat"),
    ]

    @classmethod
    def get_class_preview(cls, class_id, limit=3):
        """Sınıf kartında gösterilecek stat sözlüğü — TABANDAN TÜRETİLİR.

        Elle yazılmış bir kopya değil; `CLASS_BASES` neyse onu gösterir.
        Böylece taban değiştiğinde ekran otomatik doğru kalır.
        """
        base = cls.CLASS_BASES.get(class_id, {})
        out = {}
        for key, label, fmt in cls.CLASS_PREVIEW_STATS:
            if key not in base:
                continue
            val = base[key]
            if fmt == "pct":
                out[label] = f"{val * 100:+.0f}%"
            elif fmt == "flat":
                out[label] = f"{val:+.0f}"
            else:
                out[label] = round(val, 1)
            if len(out) >= limit:
                break
        return out

    def recalculate_stats(self):
        # 🟢 STEP 1: CLASS-SPECIFIC BASE STATS (tek kaynak: CLASS_BASES)
        class_bases = self.CLASS_BASES

        # Genel Varsayılanlar
        base_stats = {
            "speed": 4.8, "max_hp": 100, "dmgMult": 1.0, "armor": 0, "regen": 0.5,
            "magicFind": 1.0, "attack_cooldown": 350, "dodgeChance": 0.05,
            "lifesteal": 0, "combatRegen": 0, "critChance": 0.05, "pierce": 0,
            "bounce": 0, "aoe": 1.0, "projectileCount": 1,
            # meleeRange PİKSEL cinsindendir (silah tabanı + skill), meleeRangeMult
            # ise yüzde çarpanı. İkisi tek anahtarda karışıyordu (F4).
            "meleeRange": 0, "meleeRangeFlat": 0, "meleeRangeMult": 0.0,
            # Kartların "Max can %X azalır" bedelleri için yüzdesel havuz (F8)
            "max_hp_pct": 0,
            # xpGain/goldGain tüketim noktaları (1.0 + stat) şeklinde okuyor;
            # taban 1.0 bonussuz oyuncuya 2x veriyordu (H7). magicFind gerçek
            # çarpan olarak kullanıldığı için 1.0 kalır.
            "xpGain": 0.0, "goldGain": 0.0, "magnetRadius": 50,
            "turretMaxHp": 150, "turretDmg": 1.0, "turretRate": 1.0, "turretLimit": 1,
            # R yeteneğinin şarj kapasitesine EKLENEN bonus (taban 2, bkz.
            # Player.TURRET_BASE_CHARGES). Taret kartlarıyla artar.
            "turretCharges": 0,
            "cooldownReduction": 0, "attack_speed_bonus": 0, "aoe_bonus": 0,
            "minionProjectileCount": 1,
            # ELEMENTAL & SPECIALS
            "physDmgFlat": 0, "physDmgMult": 0,
            "fireDmgFlat": 0, "fireDmgMult": 0,
            "frostDmgFlat": 0, "frostDmgMult": 0,
            "elementDmgMult": 0,
            # minionCount/minionDamage tabanı 0: tüketim noktaları (player.py 1+,
            # minion.py 1.0+) tabanı zaten ekliyor; 1/1.0 çift sayım yaratıyordu (F5)
            # minionMaxHp ÇARPAN (taban 1.0), minionMaxHpFlat DÜZ can (taban 0);
            # ikisi tek anahtarda toplanınca 85.000 canlı minyon çıkıyordu (F3)
            "minionCount": 0, "minionDamage": 0.0, "minionRate": 1.0,
            "minionMaxHp": 1.0, "minionMaxHpFlat": 0, "minionArmor": 0,
            "minionRange": 1.0, 
            "minionPhysDmgFlat": 0, "minionPhysDmgMult": 0,
            "minionFireDmgFlat": 0, "minionFireDmgMult": 0,
            "minionFrostDmgFlat": 0, "minionFrostDmgMult": 0,
            "bossDmgMult": 0, "armorPen": 0, "lowHpExec": 0, "dashCooldownReduc": 0, "killComboDmg": 0
        }
        
        current_class = self.player.class_id
        class_mods = class_bases.get(current_class, {})
        
        # 🟡 STEP 2: SUM ITEM BASE AND AFFIXES
        totals = base_stats.copy()
        
        # 🧪 ESSENCE BONUSES (Kalıcı Base Stat Artışları) - tavanlı (S9)
        essence_caps = getattr(self.player, 'ESSENCE_CAPS', {})
        for stat, val in self.player.essence_stats.items():
            cap = essence_caps.get(stat)
            if cap is not None:
                val = min(val, cap)
            if stat == "phys_dmg":
                totals["physDmgFlat"] += val
            elif stat == "element_dmg":
                totals["elementDmgMult"] += val
            elif stat in totals:
                totals[stat] += val
            else:
                totals[stat] = val
        
        # Ekipman Toplamı (Bases + Affixes)
        for slot, item in self.equipped.items():
            if item:
                # Base Stats (Kahverengi)
                i_base = item.get("itemBase", {})
                is_commander = item.get("isCommander", False) and slot == "weapon"
                
                def add_stat(s_name, s_val):
                    s_name = self.STAT_ALIASES.get(s_name, s_name)
                    # Commander Weapon ise mermi/hasar statlarını minyona aktar
                    target_stat = s_name
                    if is_commander:
                        mapping = {
                            "physDmg": "minionPhysDmgFlat", "physDmgMult": "minionPhysDmgMult",
                            "fireDmgFlat": "minionFireDmgFlat", "fireDmgMult": "minionFireDmgMult",
                            "frostDmgFlat": "minionFrostDmgFlat", "frostDmgMult": "minionFrostDmgMult",
                            "poisonDps": "minionPoisonDpsFlat", "attack_speed_bonus": "minionRate",
                            "projectileCount": "minionProjectileCount", "bounce": "minionBounce",
                            "pierce": "minionPierce"
                        }
                        target_stat = mapping.get(s_name, s_name)
                    
                    if target_stat in totals: totals[target_stat] += s_val
                    else: totals[target_stat] = s_val

                for stat, val in i_base.items():
                    add_stat(stat, val)
                
                # Affixes (Mavi)
                for affix in (item.get("prefixes", []) + item.get("suffixes", [])):
                    add_stat(affix["stat"], affix["val"])

        # 🔵 STEP 3: APPLY CLASS AND SKILL MULTIPLIERS
        for sk in getattr(self.player, 'skills', []):
            if sk.get('lvl', 0) > 0:
                stat = self.SKILL_STAT_MIGRATION.get(sk.get('stat'), sk.get('stat'))
                val = sk.get('val', 0) * sk['lvl']
                if stat in totals:
                    totals[stat] += val
                else:
                    totals[stat] = val
                    
        # 🟣 KARTLARDAN GELEN KALICI STATLAR (skills_permanent)
        for stat, val in getattr(self.player, 'skills_permanent', {}).items():
            if stat in totals:
                totals[stat] += val
            else:
                totals[stat] = val

        # 🌳 YETENEK AĞACI (allocated_nodes) — düğüm statları kart havuzuyla
        # aynı biçimde toplanır. Bedeller (max_hp_pct vb.) aşağıdaki final
        # matematikte kart bedelleriyle birlikte işlenir.
        from logic.skill_tree import SkillTree
        for stat, val in SkillTree.resolve_stats(getattr(self.player, 'allocated_nodes', ())).items():
            if stat in totals:
                totals[stat] += val
            else:
                totals[stat] = val

        # 🔺 ASCENDANCY (alt-sınıf) düğümleri — aynı şekilde toplanır
        from logic.ascendancy import Ascendancy
        for stat, val in Ascendancy.resolve_stats(getattr(self.player, 'ascendancy_nodes', ())).items():
            if stat in totals:
                totals[stat] += val
            else:
                totals[stat] = val

        # Final multipliers
        new_stats = totals.copy()
        
        # Apply Class % Bonuses
        # dmgMult additive: çarpımsal olması kart/skill toplamını sınıf çarpanıyla
        # katlayıp yüksek çarpanlı sınıflarda stacking loophole yaratıyordu (S2)
        if "dmgMult" in class_mods:
            new_stats["dmgMult"] += class_mods["dmgMult"]
        if "max_hp_mult" in class_mods:
            new_stats["max_hp"] *= (1.0 + class_mods["max_hp_mult"])
        if "attack_speed_mult" in class_mods:
            new_stats["attack_speed_bonus"] += class_mods["attack_speed_mult"]

        # 🏰 SET BONUSES
        active_sets = {}
        for slot in self.equipped:
            item = self.equipped[slot]
            if item and item.get("setTag"):
                tag = item["setTag"]
                active_sets[tag] = active_sets.get(tag, 0) + 1
        
        for tag, count in active_sets.items():
            set_data = ItemSystem.set_types.get(tag)
            if set_data:
                for threshold, bonus in set_data["bonuses"].items():
                    if count >= threshold:
                        for stat, val in bonus.items():
                            stat = self.STAT_ALIASES.get(stat, stat)
                            if stat in new_stats: new_stats[stat] += val
                            else: new_stats[stat] = val

        # 🟣 AURA BONUSES (Late Game Scaling)
        from logic.aura_system import AuraManager
        aura_mgr = AuraManager()
        # Aura Sovereign Seti (2 parça: %25 aura etkisi, 4 parça: +1 aura limit)
        # aura_effectiveness set anahtarı new_stats'a toplanıyordu ama burada
        # sabit 1.25 kullanıldığı için ölüydü. Artık gerçek stat okunur;
        # 2pc yoksa 0 -> 1.0 (davranış geriye dönük aynı).
        aura_mult = 1.0 + new_stats.get("aura_effectiveness", 0)
        
        for aura_id in self.player.active_auras:
            aura = aura_mgr.get_aura(aura_id)
            if aura:
                for stat, val in aura.stats.items():
                    stat = self.STAT_ALIASES.get(stat, stat)
                    actual_val = val * aura_mult
                    if stat in new_stats: new_stats[stat] += actual_val
                    else: new_stats[stat] = actual_val

        # 🟠 AURA LIMIT CALCULATION (Base 1 + Items)
        total_limit = 1
        if active_sets.get("SET_AURA", 0) >= 4: total_limit += 1
        for slot in self.equipped:
            item = self.equipped[slot]
            if item:
                # Affixlerden gelen aura limit artışı (Sadece Orb veya Corrupted itemlar)
                for affix in (item.get("prefixes", []) + item.get("suffixes", [])):
                    if affix["stat"] == "aura_limit":
                        total_limit += affix["val"]
        self.player.aura_limit = total_limit

        # Overlay other class mods
        for k, v in class_mods.items():
            if k not in ["dmgMult", "max_hp_mult", "attack_speed_mult"]:
                if k == "speed":
                    # Sınıf hızı 4.0 tabanının YERİNE geçer (üstüne eklenmez);
                    # eşya/skill hız bonusları korunur.
                    new_stats["speed"] += v - base_stats["speed"]
                elif k == "attack_cooldown":
                    # Sınıf taban vuruş süresi 350ms varsayılanının yerine geçer
                    new_stats["attack_cooldown"] = v
                elif k in new_stats:
                    new_stats[k] += v
                else:
                    new_stats[k] = v

        # 🟢 FINAL MATH (Diminishing returns for speed and aoe)
        # Cooldown: base / (1 + bonuses)
        # AoE: base * (1 + bonuses)
        # Silahın kendi vuruş süresi (attackCooldown) sınıf tabanını ezer
        base_cooldown = new_stats.get("attackCooldown", 0) or new_stats.get("attack_cooldown", 350)
        speed_bonus = new_stats.get("attack_speed_bonus", 0)
        # Eşyalardaki fireRate bonuslarını da hıza ekle
        speed_bonus += new_stats.get("fireRate", 0)
        # Saldırı hızı azalan getiri (+%100 üzeri yumuşak tavan)
        if speed_bonus > 1.0:
            excess = speed_bonus - 1.0
            speed_bonus = 1.0 + excess / (1.0 + excess)
        new_stats["attack_cooldown"] = base_cooldown / (1.0 + max(-0.9, speed_bonus))

        aoe_bonus = new_stats.get("aoe_bonus", 0)
        # Eşyalardaki aoe statını da bonusa ekle
        aoe_bonus += (new_stats.get("aoe", 1.0) - 1.0)
        new_stats["aoe"] = 1.0 + aoe_bonus # Bu çarpan Projectile'da 100 ile çarpılacak

        # Melee Range Hesabı (F4)
        # meleeRange/meleeRangeFlat = PİKSEL, meleeRangeMult = ÇARPAN.
        # Eski kod ikisini "1.0 + bonus" diye normalize edip piksel değerini
        # yüzde gibi ele alıyordu; sonuç 50 piksellik kılıcın 0.5 piksele
        # dönmesiydi. Artık iki birim ayrı tutulur, tüketim noktaları
        # (100 + meleeRangeFlat) * meleeRangeMult şeklinde okur.
        melee_flat = new_stats.get("meleeRange", 0) + new_stats.get("meleeRangeFlat", 0)
        new_stats["meleeRangeFlat"] = melee_flat
        new_stats["meleeRange"] = melee_flat  # geriye dönük tüketiciler (piksel)
        new_stats["meleeRangeMult"] = max(0.1, 1.0 + new_stats.get("meleeRangeMult", 0.0))

        if getattr(self.player, '_bloodwalker_rage_active', False):
            new_stats["dmgMult"] = new_stats.get("dmgMult", 1.0) * 1.25
            new_stats["speed"]   = new_stats.get("speed", 5.0)  * 1.25

        # Diminishing Returns + mutlak tavanlar (SOFT_CAPS tablosu)
        for dr_stat, (knee, k, hard) in self.SOFT_CAPS.items():
            if dr_stat in new_stats:
                raw = new_stats[dr_stat]
                if raw > knee:
                    excess = raw - knee
                    raw = knee + excess / (1.0 + excess * k)
                if hard is not None:
                    raw = min(hard, raw)
                new_stats[dr_stat] = raw

        # 💀 Ölüm Anlaşması: max_hp bedeli çarpımsal; additive havuzda Canlılık
        # skiliyle sulandırılamaz (S5). Kart durumu save'den de otomatik gelir.
        game_ref = getattr(self.player, 'game', None)
        card_sys = getattr(game_ref, 'card_system', None) if game_ref else None
        if card_sys and 'death_pact' in getattr(card_sys, 'active_cards', []):
            new_stats["max_hp"] = max(1, new_stats["max_hp"] * 0.10)

        # 💔 Yüzdesel max_hp bedelleri/bonusları (F8)
        # Kart açıklamaları "Max can %20 azalır" diyor ama bedeller düz değer
        # olarak işleniyordu; 1000 can barındaki oyuncuya -20 hiçbir şey ifade
        # etmiyordu. Bu havuz YÜZDE puanı taşır (-20 => %20 azalma).
        # Havuz boşsa (eski kayıtlar/kartlar) hesap aynen eskisi gibi kalır.
        hp_pct = new_stats.get("max_hp_pct", 0)
        if hp_pct:
            new_stats["max_hp"] *= max(0.05, 1.0 + hp_pct / 100.0)

        # Fiziksel hasar negatife düşmemeli: Başbüyücü aurası (physDmg -999) ve
        # Zehirli Kalp kartı toplamı eksiye çekince düşmanlar iyileşiyordu (H8)
        for _phys_stat in ("physDmg", "physDmgFlat"):
            if _phys_stat in new_stats:
                new_stats[_phys_stat] = max(0, new_stats[_phys_stat])

        # Negatif zırh sıfıra bölme ve "hasar iyileştiriyor" durumu yaratıyordu (C3):
        # -75 tabanı alınan hasarı en fazla 4x'e çıkarır.
        new_stats["armor"] = max(-75, new_stats.get("armor", 0))

        # Max HP düşüren kartların toplamı taban 100'ü negatife çekip anında
        # ölüm yaratıyordu (C4)
        new_stats["max_hp"] = max(1, new_stats.get("max_hp", 100))

        # Ölüm Kumarı (Death Gamble): max_hp 1'e sabitlenir
        if new_stats.get("maxHpLock", 0) > 0:
            new_stats["max_hp"] = 1

        # ⏳ GEÇİCİ BUFF'LAR (Kan Ritüeli vb.) — F7
        # Doğrudan player.stats'a yazılan süreli buff'lar araya giren herhangi
        # bir recalculate_stats (eşya takma, seviye atlama, Kan Öfkesi eşiği,
        # kart seçimi) tarafından siliniyordu. Artık kalıcı statlar
        # hesaplandıktan SONRA, en üste uygulanır.
        for _tb_stat, _tb_mult in getattr(self.player, 'temp_buffs', {}).items():
            new_stats[_tb_stat] = new_stats.get(_tb_stat, 1.0) * _tb_mult

        # Sonuçları Player Statlarına Yaz
        self.player.stats.clear()
        self.player.stats.update(new_stats)
        self.player.max_hp = new_stats.get("max_hp", 100)
        self.player.max_energy_shield = new_stats.get("maxEnergyShield", 0)
        
        # Current HP and ES adjustment
        if hasattr(self.player, 'hp'):
            self.player.hp = min(self.player.hp, self.player.max_hp)
        else:
            self.player.hp = self.player.max_hp
            
        if hasattr(self.player, 'energy_shield'):
            self.player.energy_shield = min(self.player.energy_shield, self.player.max_energy_shield)
        else:
            self.player.energy_shield = 0
        
        # Weapon check (Dinamik sınıf değişimi) — AİLE KURALI (bkz. WEAPON_FAMILIES)
        # Silah yoksa / sınıfsızsa ("none", "general") ya da silah karakterle
        # AYNI savaş ailesindeyse: karakterin KENDİ sınıfı korunur. Yalnızca
        # farklı aileden bir sınıf silahı sınıfı o silaha çevirir (o saldırı
        # tipini doğru çalıştırmak için). Böylece ninja bir kan/vampir kılıcı
        # takınca ninja kalır; sadece bir arbalet/taret gibi farklı tip silah
        # sınıfı değiştirir.
        base_class = getattr(self.player, "base_class_id", None) or self.player.class_id
        weapon = self.equipped.get("weapon")
        w_class = weapon.get("weaponClass") if weapon else None
        if w_class not in self.CLASS_IDS:
            target_class = base_class
        elif self.WEAPON_FAMILIES.get(w_class) == self.WEAPON_FAMILIES.get(base_class):
            target_class = base_class
        else:
            target_class = w_class
        if target_class != self.player.class_id:
            self.player.class_id = target_class
            self.player.reinit_specialization()
            self.recalculate_stats()

    def get_item_local_stats(self, slot):
        if slot not in self.equipped or not self.equipped[slot]:
            return {}
            
        item = self.equipped[slot]
        # Base Stats Kopyala
        stats = item.get("itemBase", {}).copy()
        
        # Affixes (Prefix & Suffix)
        for affix in (item.get("prefixes", []) + item.get("suffixes", [])):
            stat = affix["stat"]
            val = affix["val"]
            if stat in stats:
                # Toplanabilir statlar (Mermi sayısı, bounce vb. hep additive olsun localde)
                stats[stat] += val
            else:
                stats[stat] = val
                
        return stats
