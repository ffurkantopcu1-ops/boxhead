from logic.item_system import ItemSystem

class InventoryManager:
    # Eşya/set/aura verilerindeki eski anahtarları stat sistemine bağlar
    # (veri dosyaları değişmez -> save uyumluluğu korunur)
    STAT_ALIASES = {"maxHp": "max_hp", "attack_speed_mult": "attack_speed_bonus"}

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

    def sell_item(self, item_index):
        if 0 <= item_index < len(self.player.inventory):
            item = self.player.inventory.pop(item_index)
            sell_price = item.get("price", 100) // 2
            self.player.gold += sell_price
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
        return sold_count, total_gold

    def recalculate_stats(self):
        # 🟢 STEP 1: CLASS-SPECIFIC BASE STATS (Source of Truth)
        class_bases = {
            "warrior":     {"dmgMult": 0.2,  "max_hp_mult": 0.2,  "speed": 6.0, "regen": 0.5},
            "sniper":      {"dmgMult": 0.5,  "critChance": 0.2,   "speed": 4.8, "bounce": 1, "pierce": 1, "attack_cooldown": 500},
            "engineer":    {"turretLimit": 1, "armor": 10,         "speed": 5.0},
            "beastmaster": {"minionDamage": 0.3, "max_hp_mult": 0.1, "speed": 5.5},
            "ninja":       {"attack_speed_mult": 0.3, "dodgeChance": 0.25, "speed": 7.2, "regen": 0.5},
            "alchemist":   {"aoe": 0.4,      "dotDmgMult": 0.3,   "speed": 5.0, "attack_cooldown": 900},
            # --- YENİ SINIFLAR ---
            "sorcerer":    {"elementDmgMult": 0.6, "max_hp_mult": -0.30, "speed": 4.8, "attack_cooldown": 400},
            "bloodwalker": {"dmgMult": 0.4,  "lifesteal": 0.20,   "speed": 5.5, "regen": 0.5},
        }
        
        # Genel Varsayılanlar
        base_stats = {
            "speed": 4.8, "max_hp": 100, "dmgMult": 1.0, "armor": 0, "regen": 0.5,
            "magicFind": 1.0, "attack_cooldown": 350, "dodgeChance": 0.05,
            "lifesteal": 0, "combatRegen": 0, "critChance": 0.05, "pierce": 0,
            "bounce": 0, "aoe": 1.0, "projectileCount": 1, "meleeRange": 0,
            "xpGain": 1.0, "goldGain": 1.0, "magnetRadius": 50,
            "turretMaxHp": 150, "turretDmg": 1.0, "turretRate": 1.0, "turretLimit": 1,
            "cooldownReduction": 0, "attack_speed_bonus": 0, "aoe_bonus": 0,
            "minionProjectileCount": 1,
            # ELEMENTAL & SPECIALS
            "physDmgFlat": 0, "physDmgMult": 0,
            "fireDmgFlat": 0, "fireDmgMult": 0,
            "frostDmgFlat": 0, "frostDmgMult": 0,
            "elementDmgMult": 0,
            # minionCount/minionDamage tabanı 0: tüketim noktaları (player.py 1+,
            # minion.py 1.0+) tabanı zaten ekliyor; 1/1.0 çift sayım yaratıyordu (F5)
            "minionCount": 0, "minionDamage": 0.0, "minionRate": 1.0, "minionMaxHp": 1.0, "minionArmor": 0,
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
                stat = sk.get('stat')
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
        aura_mult = 1.0
        # Aura Sovereign Seti Check (2 parça: %25 aura etkisi, 4 parça: +1 aura limit)
        if active_sets.get("SET_AURA", 0) >= 2: aura_mult = 1.25
        
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

        # Melee Range Hesabı
        melee_bonus = (new_stats.get("meleeRange", 1.0) - 1.0)
        melee_bonus += (new_stats.get("meleeRangeFlat", 0) / 100.0)
        new_stats["meleeRange"] = 1.0 + melee_bonus

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

        # Sonuçları Player Statlarına Yaz
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
        
        # Weapon check (Dinamik sınıf değişimi)
        weapon = self.equipped.get("weapon")
        if weapon:
            w_class = weapon.get("weaponClass")
            if w_class and w_class != "none" and w_class != self.player.class_id:
                self.player.class_id = w_class 
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
