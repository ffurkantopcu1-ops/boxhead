import random
import time

class ItemSystem:
    # ItemRNG.js'den port edildi (31+ Base)
    bases = [
        # --- SİLAHLAR (Melee) ---
        { 'type': 'weapon', 'name': 'Eski Kılıç (T4)', 'tier': 4, 'isMelee': True, 'weaponClass': 'warrior', 'icon_id': 'weapon_old_sword', 'itemBase': { 'physDmg': 12, 'meleeRange': 50 } },
        { 'type': 'weapon', 'name': 'Çelik Kılıç (T3)', 'tier': 3, 'isMelee': True, 'weaponClass': 'warrior', 'icon_id': 'weapon_steel_sword', 'itemBase': { 'physDmg': 28, 'meleeRange': 55 } },
        { 'type': 'weapon', 'name': 'Mithril Kılıç (T2)', 'tier': 2, 'isMelee': True, 'weaponClass': 'warrior', 'icon_id': 'weapon_mithril_sword', 'itemBase': { 'physDmg': 55, 'meleeRange': 60 } },
        { 'type': 'weapon', 'name': 'Güneş Kılıcı (T1)', 'tier': 1, 'isMelee': True, 'weaponClass': 'warrior', 'icon_id': 'weapon_sun_sword', 'itemBase': { 'physDmg': 110, 'meleeRange': 65, 'fireDamage': 30 } },
        
        # Katana hattı 'meleeRange' taşımıyordu; ninjanın başlangıç katanası ise
        # (entities/player.py'de elle tanımlıydı) meleeRange 20 taşıyordu. Sonuç:
        # T4 katanayı yerden alan ninja ELİNDEKİNDEN menzilsizini takıyordu.
        # Menzil hatta taşındı ve tier'a göre artıyor (kılıç hattı gibi), böylece
        # yükseltmek asla menzil kaybettirmez. Ninja vuruş yarıçapı
        # (entities/ninja_logic.py): 180 + meleeRangeFlat.
        { 'type': 'weapon', 'name': 'Paslı Katana (T4)', 'tier': 4, 'isMelee': True, 'weaponClass': 'ninja', 'icon_id': 'weapon_katana_rusty', 'itemBase': { 'physDmg': 15, 'attackCooldown': 450, 'meleeRange': 20 } },
        { 'type': 'weapon', 'name': 'Keskin Katana (T3)', 'tier': 3, 'isMelee': True, 'weaponClass': 'ninja', 'icon_id': 'weapon_katana_sharp', 'itemBase': { 'physDmg': 35, 'attackCooldown': 420, 'meleeRange': 25 } },
        { 'type': 'weapon', 'name': 'Usta İşi Katana (T2)', 'tier': 2, 'isMelee': True, 'weaponClass': 'ninja', 'icon_id': 'weapon_katana_master', 'itemBase': { 'physDmg': 70, 'attackCooldown': 380, 'meleeRange': 30 } },
        { 'type': 'weapon', 'name': 'Muramasa (T1)', 'tier': 1, 'isMelee': True, 'weaponClass': 'ninja', 'icon_id': 'weapon_muramasa', 'itemBase': { 'physDmg': 130, 'attackCooldown': 340, 'lifesteal': 0.1, 'meleeRange': 35 } },

        # --- SİLAHLAR (Ranged/Bomb) ---
        { 'type': 'weapon', 'name': 'Basit Arbalet (T4)', 'tier': 4, 'isRanged': True, 'weaponClass': 'sniper', 'icon_id': 'weapon_crossbow_simple', 'itemBase': { 'physDmg': 18 } },
        { 'type': 'weapon', 'name': 'Ağır Arbalet (T3)', 'tier': 3, 'isRanged': True, 'weaponClass': 'sniper', 'icon_id': 'weapon_crossbow_heavy', 'itemBase': { 'physDmg': 45 } },
        { 'type': 'weapon', 'name': 'Gölge Arbaleti (T2)', 'tier': 2, 'isRanged': True, 'weaponClass': 'sniper', 'icon_id': 'weapon_crossbow_shadow', 'itemBase': { 'physDmg': 85 } },
        { 'type': 'weapon', 'name': 'Balista (T1)', 'tier': 1, 'isRanged': True, 'weaponClass': 'sniper', 'icon_id': 'weapon_ballista', 'itemBase': { 'physDmg': 160, 'pierce': 3 } },
        
        { 'type': 'weapon', 'name': 'Zehir Şişesi (T4)', 'tier': 4, 'isBomb': True, 'weaponClass': 'alchemist', 'icon_id': 'weapon_poison_bottle', 'itemBase': { 'poisonDps': 4 } },
        { 'type': 'weapon', 'name': 'Simyacı Karışımı (T3)', 'tier': 3, 'isBomb': True, 'weaponClass': 'alchemist', 'icon_id': 'weapon_alchemist_mixture', 'itemBase': { 'poisonDps': 12, 'aoe': 1.8 } },
        { 'type': 'weapon', 'name': 'Büyük Kimyasal Şişe (T2)', 'tier': 2, 'isBomb': True, 'weaponClass': 'alchemist', 'icon_id': 'weapon_chemical_bottle_large', 'itemBase': { 'poisonDps': 25, 'aoe': 2.5 } },
        { 'type': 'weapon', 'name': 'Nükleer Atık (T1)', 'tier': 1, 'isBomb': True, 'weaponClass': 'alchemist', 'icon_id': 'weapon_nuclear_waste', 'itemBase': { 'poisonDps': 60, 'aoe': 3.5, 'dotDmgMult': 0.5 } },

        # Bombacı: patlayıcı fırlatma. Bomba hasarı poisonDps üzerinden okunur
        # (entities/player.py -> shoot(), is_bomb dalı); patlama yarıçapı
        # itemBase['aoe'] + sınıf tabanı + Bomber.AOE_MULT ile büyür.
        # Simyacı'ya göre vuruş başına daha sert ama daha yavaş (attackCooldown).
        { 'type': 'weapon', 'name': 'El Bombası Çantası (T4)', 'tier': 4, 'isBomb': True, 'weaponClass': 'bomber', 'icon_id': 'weapon_grenade_pouch', 'itemBase': { 'poisonDps': 8 } },
        { 'type': 'weapon', 'name': 'Molotof Kokteyli (T3)', 'tier': 3, 'isBomb': True, 'weaponClass': 'bomber', 'icon_id': 'weapon_molotov', 'itemBase': { 'poisonDps': 22, 'aoe': 1.0, 'attackCooldown': 1400 } },
        { 'type': 'weapon', 'name': 'Dinamit Demeti (T2)', 'tier': 2, 'isBomb': True, 'weaponClass': 'bomber', 'icon_id': 'weapon_dynamite_bundle', 'itemBase': { 'poisonDps': 48, 'aoe': 1.6, 'attackCooldown': 1250 } },
        { 'type': 'weapon', 'name': 'Termobarik Bomba (T1)', 'tier': 1, 'isBomb': True, 'weaponClass': 'bomber', 'icon_id': 'weapon_thermobaric_bomb', 'itemBase': { 'poisonDps': 110, 'aoe': 2.4, 'attackCooldown': 1100, 'dotDmgMult': 0.4 } },

        # --- YENİ SINIF SİLAHLARI ---
        # physDmg 8->12: büyücünün başlangıç asası (elle tanımlıyken) zaten 12'ydi;
        # T4 dropu 8'de kalınca yerden alınan asa elde olandan zayıf çıkıyordu.
        # Gerekçe (eski yorum): elementDmgMult sınıf kimliği düz element hasarı
        # olmadan uykuda kaldığı için büyücü erken oyunda yalnızca fizikselle vurur.
        { 'type': 'weapon', 'name': 'Sihir Asası (T4)', 'tier': 4, 'isRanged': True, 'weaponClass': 'sorcerer', 'icon_id': 'weapon_wand_magic', 'itemBase': { 'physDmg': 12, 'elementDmgMult': 0.2 } },
        { 'type': 'weapon', 'name': 'Kristal Asa (T3)', 'tier': 3, 'isRanged': True, 'weaponClass': 'sorcerer', 'icon_id': 'weapon_wand_crystal', 'itemBase': { 'physDmg': 22, 'elementDmgMult': 0.5 } },
        { 'type': 'weapon', 'name': 'Ejder Asası (T2)', 'tier': 2, 'isRanged': True, 'weaponClass': 'sorcerer', 'icon_id': 'weapon_wand_dragon', 'itemBase': { 'physDmg': 44, 'elementDmgMult': 0.9, 'fireDamage': 20, 'frostDamage': 20 } },
        { 'type': 'weapon', 'name': 'Kadim Ruh Asası (T1)', 'tier': 1, 'isRanged': True, 'weaponClass': 'sorcerer', 'icon_id': 'weapon_wand_ancient', 'itemBase': { 'physDmg': 80, 'elementDmgMult': 1.5, 'fireDamage': 50, 'frostDamage': 50 } },

        { 'type': 'weapon', 'name': 'Kan Kılıcı (T4)', 'tier': 4, 'isMelee': True, 'weaponClass': 'bloodwalker', 'icon_id': 'weapon_blood_sword', 'itemBase': { 'physDmg': 14, 'lifesteal': 0.15, 'meleeRange': 50 } },
        { 'type': 'weapon', 'name': 'Lanetli Kan Bıçağı (T3)', 'tier': 3, 'isMelee': True, 'weaponClass': 'bloodwalker', 'icon_id': 'weapon_blood_blade_cursed', 'itemBase': { 'physDmg': 45, 'lifesteal': 0.25, 'meleeRange': 58 } },
        { 'type': 'weapon', 'name': 'Ölüm Sickle (T2)', 'tier': 2, 'isMelee': True, 'weaponClass': 'bloodwalker', 'icon_id': 'weapon_death_sickle', 'itemBase': { 'physDmg': 90, 'lifesteal': 0.40, 'meleeRange': 65, 'critChance': 0.15 } },
        { 'type': 'weapon', 'name': 'Ruh Biçen (T1)', 'tier': 1, 'isMelee': True, 'weaponClass': 'bloodwalker', 'icon_id': 'weapon_soul_reaper', 'itemBase': { 'physDmg': 160, 'lifesteal': 0.60, 'meleeRange': 75, 'critChance': 0.25 } },

        { 'type': 'weapon', 'name': 'Eski Taret Kiti (T4)', 'tier': 4, 'isTurret': True, 'weaponClass': 'engineer', 'icon_id': 'weapon_turret_kit_old', 'itemBase': { 'turretDmg': 1.1, 'projectileCount': 1 } },
        { 'type': 'weapon', 'name': 'Gelişmiş Taret Kiti (T3)', 'tier': 3, 'isTurret': True, 'weaponClass': 'engineer', 'icon_id': 'weapon_turret_kit_adv', 'itemBase': { 'turretDmg': 1.3, 'projectileCount': 1, 'turretRate': 0.1 } },
        { 'type': 'weapon', 'name': 'Lazer Taret Kiti (T2)', 'tier': 2, 'isTurret': True, 'weaponClass': 'engineer', 'icon_id': 'weapon_turret_kit_laser', 'itemBase': { 'turretDmg': 1.6, 'projectileCount': 2, 'turretRate': 0.2, 'pierce': 1 } },
        { 'type': 'weapon', 'name': 'Kıyamet Tareti Kiti (T1)', 'tier': 1, 'isTurret': True, 'weaponClass': 'engineer', 'icon_id': 'weapon_turret_kit_doom', 'itemBase': { 'turretDmg': 2.2, 'projectileCount': 3, 'turretRate': 0.4, 'pierce': 2, 'bounce': 1 } },

        # Mühendis — ALEV SİLAHLARI. Taret kiti bir "ekipman" (elde vurmaz);
        # alev silahı Mühendis'in doğrudan hasar veren kolu. Mermi üretmez,
        # önündeki koniyi tarar (engineer_logic.execute_flamethrower).
        # Hasar 'fireDamage' üzerinden okunur; asıl hasar yığılan yanmadan
        # gelir. 'range' koniyi uzatır. attackCooldown çok kısa: akış hissi.
        # Menzil ve tek vuruş hasarı düşük tutuldu çünkü saniyede ~10 tick
        # vuruyor ve her tick yanma tazeliyor.
        { 'type': 'weapon', 'name': 'Sızdıran Alev Tabancası (T4)', 'tier': 4, 'isFlamethrower': True, 'weaponClass': 'engineer', 'icon_id': 'weapon_flamethrower_leaky', 'itemBase': { 'fireDamage': 4, 'attackCooldown': 115 } },
        { 'type': 'weapon', 'name': 'Basınçlı Alev Silahı (T3)', 'tier': 3, 'isFlamethrower': True, 'weaponClass': 'engineer', 'icon_id': 'weapon_flamethrower_pressure', 'itemBase': { 'fireDamage': 9, 'attackCooldown': 105, 'range': 45 } },
        { 'type': 'weapon', 'name': 'Ağır Alev Püskürtücü (T2)', 'tier': 2, 'isFlamethrower': True, 'weaponClass': 'engineer', 'icon_id': 'weapon_flamethrower_heavy', 'itemBase': { 'fireDamage': 17, 'attackCooldown': 95, 'range': 90, 'fireDmgMult': 0.2 } },
        { 'type': 'weapon', 'name': 'Ejderha Nefesi (T1)', 'tier': 1, 'isFlamethrower': True, 'weaponClass': 'engineer', 'icon_id': 'weapon_flamethrower_dragon', 'itemBase': { 'fireDamage': 31, 'attackCooldown': 85, 'range': 150, 'fireDmgMult': 0.45, 'statusDuration': 0.3 } },

        { 'type': 'weapon', 'name': 'Kırık Terbiyeci Sopası (T4)', 'tier': 4, 'isMinion': True, 'weaponClass': 'beastmaster', 'icon_id': 'weapon_tamer_staff_broken', 'itemBase': { 'minionDamage': 0.2 } },
        { 'type': 'weapon', 'name': 'Çırak Terbiyeci Sopası (T3)', 'tier': 3, 'isMinion': True, 'weaponClass': 'beastmaster', 'icon_id': 'weapon_tamer_staff_apprentice', 'itemBase': { 'minionDamage': 0.4, 'minionCount': 1 } },
        { 'type': 'weapon', 'name': 'Usta Terbiyeci Sopası (T2)', 'tier': 2, 'isMinion': True, 'weaponClass': 'beastmaster', 'icon_id': 'weapon_tamer_staff_master', 'itemBase': { 'minionDamage': 0.8, 'minionCount': 2, 'projectileCount': 1 } },
        { 'type': 'weapon', 'name': 'Sürü Liderinin Sopası (T1)', 'tier': 1, 'isMinion': True, 'weaponClass': 'beastmaster', 'icon_id': 'weapon_tamer_staff_lord', 'itemBase': { 'minionDamage': 1.5, 'minionCount': 3, 'projectileCount': 2, 'minionCrit': 0.2 } },

        # --- YENİ SİLAHLAR (TÜM SINIFLAR İÇİN ORTAK 'general') ---
        { 'type': 'weapon', 'name': 'Tahta Bumerang (T4)', 'tier': 4, 'isRanged': True, 'isBoomerang': True, 'weaponClass': 'general', 'icon_id': 'weapon_boomerang_wood', 'itemBase': { 'physDmg': 10 } },
        { 'type': 'weapon', 'name': 'Keskin Çakram (T3)', 'tier': 3, 'isRanged': True, 'isBoomerang': True, 'weaponClass': 'general', 'icon_id': 'weapon_chakram_sharp', 'itemBase': { 'physDmg': 25, 'pierce': 1 } },
        { 'type': 'weapon', 'name': 'Gölge Çakram (T2)', 'tier': 2, 'isRanged': True, 'isBoomerang': True, 'weaponClass': 'general', 'icon_id': 'weapon_chakram_shadow', 'itemBase': { 'physDmg': 50, 'pierce': 2, 'attackCooldown': 300 } },
        { 'type': 'weapon', 'name': 'Güneş Fırtınası (T1)', 'tier': 1, 'isRanged': True, 'isBoomerang': True, 'weaponClass': 'general', 'icon_id': 'weapon_chakram_sun', 'itemBase': { 'physDmg': 100, 'pierce': 3, 'attackCooldown': 250, 'fireDamage': 40 } },

        { 'type': 'weapon', 'name': 'Yırtık Boks Eldiveni (T4)', 'tier': 4, 'isMelee': True, 'weaponClass': 'general', 'icon_id': 'weapon_gauntlet_torn', 'itemBase': { 'physDmg': 8, 'attackCooldown': 200, 'meleeRange': -15, 'knockbackMult': 2.0 } },
        { 'type': 'weapon', 'name': 'Deri Boks Eldiveni (T3)', 'tier': 3, 'isMelee': True, 'weaponClass': 'general', 'icon_id': 'weapon_gauntlet_leather', 'itemBase': { 'physDmg': 18, 'attackCooldown': 150, 'meleeRange': -15, 'knockbackMult': 2.5 } },
        { 'type': 'weapon', 'name': 'Çelik Yumruk (T2)', 'tier': 2, 'isMelee': True, 'weaponClass': 'general', 'icon_id': 'weapon_gauntlet_steel', 'itemBase': { 'physDmg': 35, 'attackCooldown': 100, 'meleeRange': -10, 'knockbackMult': 3.5 } },
        { 'type': 'weapon', 'name': 'Titanium Yumruk (T1)', 'tier': 1, 'isMelee': True, 'weaponClass': 'general', 'icon_id': 'weapon_gauntlet_titanium', 'itemBase': { 'physDmg': 75, 'attackCooldown': 75, 'meleeRange': -10, 'knockbackMult': 5.0, 'critChance': 0.15 } },

        { 'type': 'weapon', 'name': 'Paslı Mayın (T4)', 'tier': 4, 'isTrapItem': True, 'weaponClass': 'general', 'icon_id': 'weapon_trap_rusty', 'itemBase': { 'trapDmg': 50, 'trapRadius': 80, 'attackCooldown': 1000 } },
        { 'type': 'weapon', 'name': 'Patlayıcı Tuzak (T3)', 'tier': 3, 'isTrapItem': True, 'weaponClass': 'general', 'icon_id': 'weapon_trap_explosive', 'itemBase': { 'trapDmg': 120, 'trapRadius': 100, 'attackCooldown': 800 } },
        { 'type': 'weapon', 'name': 'Gelişmiş Mayın (T2)', 'tier': 2, 'isTrapItem': True, 'weaponClass': 'general', 'icon_id': 'weapon_trap_advanced', 'itemBase': { 'trapDmg': 250, 'trapRadius': 120, 'attackCooldown': 600 } },
        { 'type': 'weapon', 'name': 'Nükleer Tuzak (T1)', 'tier': 1, 'isTrapItem': True, 'weaponClass': 'general', 'icon_id': 'weapon_trap_nuke', 'itemBase': { 'trapDmg': 600, 'trapRadius': 180, 'attackCooldown': 400 } },

        { 'type': 'weapon', 'name': 'Ağır Zincir (T4)', 'tier': 4, 'isMelee': True, 'isFlail': True, 'weaponClass': 'general', 'icon_id': 'weapon_flail_chain', 'itemBase': { 'physDmg': 6, 'meleeRange': 20 } },
        { 'type': 'weapon', 'name': 'Demir Gürz (T3)', 'tier': 3, 'isMelee': True, 'isFlail': True, 'weaponClass': 'general', 'icon_id': 'weapon_flail_iron', 'itemBase': { 'physDmg': 14, 'meleeRange': 30 } },
        { 'type': 'weapon', 'name': 'Gölge Tırpanı (T2)', 'tier': 2, 'isMelee': True, 'isFlail': True, 'weaponClass': 'general', 'icon_id': 'weapon_flail_shadow', 'itemBase': { 'physDmg': 30, 'meleeRange': 40, 'lifesteal': 0.1 } },
        { 'type': 'weapon', 'name': 'Kaos Gürzü (T1)', 'tier': 1, 'isMelee': True, 'isFlail': True, 'weaponClass': 'general', 'icon_id': 'weapon_flail_chaos', 'itemBase': { 'physDmg': 60, 'meleeRange': 50, 'critChance': 0.2, 'lifesteal': 0.2 } },

        # --- ZIRHLAR ---
        { 'type': 'helmet', 'name': 'Deri Başlık (T4)', 'tier': 4, 'icon_id': 'armor_helmet_leather', 'itemBase': { 'armor': 4, 'maxHp': 10 } },
        { 'type': 'helmet', 'name': 'Demir Miğfer (T3)', 'tier': 3, 'icon_id': 'armor_helmet_iron', 'itemBase': { 'armor': 12, 'maxHp': 25 } },
        { 'type': 'helmet', 'name': 'Yüce Şövalye Miğferi (T2)', 'tier': 2, 'icon_id': 'armor_helmet_knight', 'itemBase': { 'armor': 35, 'maxHp': 60 } },
        { 'type': 'helmet', 'name': 'İlahi Taç (T1)', 'tier': 1, 'icon_id': 'armor_helmet_divine', 'itemBase': { 'armor': 80, 'maxHp': 150, 'cooldownReduction': 0.1 } },

        { 'type': 'chest', 'name': 'Deri Zırh (T4)', 'tier': 4, 'icon_id': 'armor_chest_leather', 'itemBase': { 'armor': 10, 'maxHp': 20 } },
        { 'type': 'chest', 'name': 'Çelik Göğüslük (T3)', 'tier': 3, 'icon_id': 'armor_chest_steel', 'itemBase': { 'armor': 30, 'maxHp': 50 } },
        { 'type': 'chest', 'name': 'Kristal Kaftan (T2)', 'tier': 2, 'icon_id': 'armor_chest_crystal', 'itemBase': { 'armor': 75, 'maxHp': 120 } },
        { 'type': 'chest', 'name': 'Güneş Zırhı (T1)', 'tier': 1, 'icon_id': 'armor_chest_sun', 'itemBase': { 'armor': 160, 'maxHp': 300, 'hpRegen': 10 } },

        # --- TAKILAR ---
        { 'type': 'amulet', 'name': 'Gümüş Muska (T4)', 'tier': 4, 'icon_id': 'amulet_silver', 'itemBase': { 'magicFind': 0.1, 'dodgeChance': 0.05 } },
        { 'type': 'amulet', 'name': 'Altın Tılsım (T3)', 'tier': 3, 'icon_id': 'amulet_gold', 'itemBase': { 'magicFind': 0.25, 'goldGain': 0.2 } },
        { 'type': 'amulet', 'name': 'Vampir Dişi (T2)', 'tier': 2, 'icon_id': 'amulet_vampire', 'itemBase': { 'lifesteal': 0.03 } },
        { 'type': 'amulet', 'name': 'Tanrısal Kolye (T1)', 'tier': 1, 'icon_id': 'amulet_divine', 'itemBase': { 'magicFind': 0.6, 'dodgeChance': 0.15, 'critChance': 0.1 } },

        # --- PETLER (Tiered) ---
        { 'type': 'pet', 'name': '🐾 Yavru Kurt (T4)', 'tier': 4, 'icon_id': 'pet_wolf_small', 'itemBase': { 'minionDamage': 0.08, 'minionAttackSpeed': 0.10, 'minionRange': 0.10 } },
        { 'type': 'pet', 'name': '🐾 Savaş Kurdu (T3)', 'tier': 3, 'icon_id': 'pet_wolf_war', 'itemBase': { 'minionDamage': 0.25, 'minionAttackSpeed': 0.20, 'minionRange': 0.25 } },
        { 'type': 'pet', 'name': '🐾 Alfa Kurt (T2)', 'tier': 2, 'icon_id': 'pet_wolf_alpha', 'itemBase': { 'minionDamage': 0.60, 'minionAttackSpeed': 0.40, 'minionRange': 0.45, 'minionCrit': 0.1 } },
        { 'type': 'pet', 'name': '🐾 Efsanevi Kurt (T1)', 'tier': 1, 'icon_id': 'pet_wolf_legendary', 'itemBase': { 'minionDamage': 1.20, 'minionMaxHp': 7.00, 'minionRange': 0.60, 'minionCrit': 0.2 } },

        { 'type': 'pet', 'name': '🐲 Ejder Yavrusu (T4)', 'tier': 4, 'icon_id': 'pet_dragon_baby', 'itemBase': { 'minionDamage': 0.12, 'fireDamage': 10, 'minionMaxHp': 0.60 } },
        { 'type': 'pet', 'name': '🐲 Kanatlı Ejder (T3)', 'tier': 3, 'icon_id': 'pet_dragon_winged', 'itemBase': { 'minionDamage': 0.35, 'fireDamage': 30, 'minionMaxHp': 1.50, 'aoe': 0.25 } },
        { 'type': 'pet', 'name': '🐲 Kadim Ejder (T2)', 'tier': 2, 'icon_id': 'pet_dragon_ancient', 'itemBase': { 'minionDamage': 0.80, 'fireDamage': 70, 'minionMaxHp': 4.50, 'aoe': 0.50, 'pierce': 2 } },
        { 'type': 'pet', 'name': '🐲 Ejderhalar Kralı (T1)', 'tier': 1, 'icon_id': 'pet_dragon_king', 'itemBase': { 'minionDamage': 1.80, 'fireDamage': 150, 'minionMaxHp': 12.0, 'aoe': 0.80, 'pierce': 4 } },

        # --- COMMANDER WEAPONS (Minyon Odaklı, Hasarsız) ---
        { 'type': 'weapon', 'name': 'Eski Terbiye Sopası (T4)', 'tier': 4, 'icon_id': 'weapon_stick', 'isCommander': True, 'price': 800, 'itemBase': { 'minionDamage': 0.1, 'minionRange': 0.1 } },
        { 'type': 'weapon', 'name': 'Gümüş Komuta Asası (T3)', 'tier': 3, 'icon_id': 'weapon_baton', 'isCommander': True, 'price': 2500, 'itemBase': { 'minionDamage': 0.25, 'minionRate': 0.2, 'minionRange': 0.2 } },
        { 'type': 'weapon', 'name': 'Efsanevi Savaş Sinyali (T2)', 'tier': 2, 'icon_id': 'weapon_signal', 'isCommander': True, 'price': 8000, 'itemBase': { 'minionDamage': 0.5, 'minionRate': 0.4, 'minionCount': 1, 'minionRange': 0.3 } },
        
        # --- ESSENCES (Kalıcı Özler) ---
        { 'type': 'essence', 'essence_type': 'max_hp', 'name': 'Hayat Özü', 'tier': 4, 'icon_id': 'essence_vitality', 'val': 2, 'price': 2000, 'rarity': 'Normal', 'desc': 'Kullanıldığında +2 Kalıcı HP verir.' },
        { 'type': 'essence', 'essence_type': 'phys_dmg', 'name': 'Kuvvet Özü', 'tier': 4, 'icon_id': 'essence_might', 'val': 1, 'price': 2000, 'rarity': 'Normal', 'desc': 'Kullanıldığında +1 Kalıcı Fiziksel Hasar verir.' },
        { 'type': 'essence', 'essence_type': 'element_dmg', 'name': 'Büyü Özü', 'tier': 4, 'icon_id': 'essence_magic', 'val': 0.02, 'price': 2000, 'rarity': 'Normal', 'desc': 'Kullanıldığında +%2 Kalıcı Element Hasarı verir.' },
        { 'type': 'essence', 'essence_type': 'armor', 'name': 'Metanet Özü', 'tier': 4, 'icon_id': 'essence_fortitude', 'val': 1, 'price': 2000, 'rarity': 'Normal', 'desc': 'Kullanıldığında +1 Kalıcı Zırh verir.' },
        { 'type': 'essence', 'essence_type': 'speed', 'name': 'Çeviklik Özü', 'tier': 4, 'icon_id': 'essence_swiftness', 'val': 0.1, 'price': 2000, 'rarity': 'Normal', 'desc': 'Kullanıldığında +0.1 Kalıcı Hız verir.' },
        { 'type': 'essence', 'essence_type': 'xp', 'name': 'Bilgelik Özü', 'tier': 4, 'icon_id': 'essence_xp', 'val': 300, 'price': 2000, 'rarity': 'Normal', 'desc': 'Kullanıldığında 300 XP verir.' }
    ]

    set_types = {
        'SET_FIRE': { 'name': 'Alev Lordu', 'bonuses': { 2: { 'maxHp': 50 }, 3: { 'elementDmgMult': 0.5 }, 4: { 'fireDamage': 50 } } },
        'SET_FROST': { 'name': 'Buz Devi', 'bonuses': { 2: { 'armor': 10 }, 3: { 'frostDamage': 30 }, 4: { 'maxHp': 150 } } },
        'SET_NINJA': { 'name': 'Gölge Ninja', 'bonuses': { 2: { 'speed': 3 }, 3: { 'dodgeChance': 0.2 }, 4: { 'critChance': 0.3 } } },
        'SET_VENOM': { 'name': 'Zehir Ustası', 'bonuses': { 2: { 'poisonDps': 10 }, 3: { 'statusDuration': 1.0 }, 4: { 'dotDmgMult': 1.0 } } },
        'SET_TANK': { 'name': 'Kalın Zırhlı', 'bonuses': { 2: { 'maxHp': 100 }, 3: { 'armor': 20 }, 4: { 'thorns': 100 } } },
        'SET_SHOTGUN': { 'name': 'Pompalı Usta', 'bonuses': { 2: { 'projectileCount': 1 }, 3: { 'spreadAngle': 8 }, 4: { 'fireRate': 0.5, 'dmgMult': 0.3 } } },
        'SET_LIGHTNING': { 'name': 'Fırtına Efendisi', 'bonuses': { 2: { 'bounce': 2 }, 3: { 'rangedSpeed': 0.5 }, 4: { 'critChance': 0.2, 'critDmg': 1.0 } } },
        'SET_NECROMANCER': { 'name': 'Ölüm Çağıran', 'bonuses': { 2: { 'minionCount': 3 }, 3: { 'minionDamage': 0.5 }, 4: { 'dmgMult': 0.4 } } },
        'SET_BERSERKER': { 'name': 'Berserker', 'bonuses': { 2: { 'dmgMult': 0.3 }, 3: { 'lifesteal': 0.05 }, 4: { 'speed': 2 } } },
        'SET_PALADIN': { 'name': 'Kutsal Şövalye', 'bonuses': { 2: { 'armor': 20 }, 3: { 'hpRegen': 10 }, 4: { 'combatRegen': 5 } } },
        'SET_ALCHEMIST': { 'name': 'Simyacı Lordu', 'bonuses': { 2: { 'elementDmgMult': 0.3 }, 3: { 'dotDmgMult': 0.4 }, 4: { 'statusDuration': 1.0 } } },
        'SET_VOID': { 'name': 'Hiçlik Gezgini', 'bonuses': { 2: { 'dodgeChance': 0.15 }, 3: { 'speed': 2 }, 4: { 'magicFind': 1.5 } } },
        'SET_SUMMONER': { 'name': 'Ordu Komutanı', 'bonuses': { 2: { 'minionCount': 2 }, 3: { 'minionDamage': 0.4 }, 4: { 'maxHp': 200 } } },
        'SET_SPEED': { 'name': 'Rüzgar Koşucusu', 'bonuses': { 2: { 'speed': 4 }, 3: { 'dodgeChance': 0.1 }, 4: { 'fireRate': 0.3 } } },
        'SET_AURA': { 'name': 'Aura Sovereign', 'bonuses': { 2: { 'aura_effectiveness': 0.25 }, 4: { 'aura_limit': 1 } } }
    }

    affixes = {
        'weapon_prefixes': [
            {'stat': 'dmgMult', 'name': 'Hasar', 'tiers': {1: [0.3, 0.4], 2: [0.2, 0.29], 3: [0.1, 0.19]}},
            {'stat': 'armorPen', 'name': 'Zırh Delme', 'tiers': {1: [0.2, 0.3], 2: [0.1, 0.19], 3: [0.05, 0.09]}},
            {'stat': 'bossDmgMult', 'name': 'Patron Hasarı', 'tiers': {1: [0.4, 0.5], 2: [0.2, 0.39], 3: [0.1, 0.19]}},
            {'stat': 'fireDamage', 'name': 'Ateş Hasarı', 'tiers': {1: [30, 40], 2: [15, 29], 3: [5, 14]}},
            {'stat': 'frostDamage', 'name': 'Buz Hasarı', 'tiers': {1: [30, 40], 2: [15, 29], 3: [5, 14]}},
            {'stat': 'minionCount', 'name': 'Minyon Kapasitesi', 'tiers': {1: [1, 1], 2: [1, 1], 3: [1, 1]}},
            {'stat': 'projectileCount', 'name': 'Ekstra Mermi', 'tiers': {1: [2, 2], 2: [1, 1], 3: [1, 1]}},
            {'stat': 'aoe', 'name': 'Alan Etkisi', 'tiers': {1: [0.3, 0.4], 2: [0.15, 0.29], 3: [0.05, 0.14]}},
            # F4: eskiden 'meleeRange' PİKSEL veriyordu -> T1 affix +3 piksel
            # gibi anlamsız bir bonustu. Artık çarpan havuzuna yazar (0.30 = +%30).
            {'stat': 'meleeRangeMult', 'name': 'Menzil', 'tiers': {1: [0.30, 0.30], 2: [0.20, 0.20], 3: [0.10, 0.10]}},
            {'stat': 'brutal', 'name': 'Acımasız', 'tiers': {1: [0.4, 0.5], 2: [0.2, 0.39], 3: [0.1, 0.19]}},
            {'stat': 'elementDmgMult', 'name': 'Element Hasarı', 'tiers': {1: [0.4, 0.5], 2: [0.2, 0.39], 3: [0.1, 0.19]}},
            {'stat': 'dotDmgMult', 'name': 'Zehir Etkisi', 'tiers': {1: [0.4, 0.5], 2: [0.2, 0.39], 3: [0.1, 0.19]}}
        ],
        'weapon_suffixes': [
            {'stat': 'critChance', 'name': 'Kritik Şans', 'tiers': {1: [0.1, 0.15], 2: [0.05, 0.09], 3: [0.02, 0.04]}},
            {'stat': 'critDmg', 'name': 'Kritik Hasar', 'tiers': {1: [0.4, 0.6], 2: [0.2, 0.39], 3: [0.1, 0.19]}},
            {'stat': 'fireRate', 'name': 'Ateş Hızı', 'tiers': {1: [0.2, 0.3], 2: [0.1, 0.19], 3: [0.05, 0.09]}},
            {'stat': 'lifesteal', 'name': 'Can Çalma', 'tiers': {1: [0.06, 0.08], 2: [0.03, 0.05], 3: [0.01, 0.02]}},
            {'stat': 'bounce', 'name': 'Mermi Sekmesi', 'tiers': {1: [3, 3], 2: [2, 2], 3: [1, 1]}},
            {'stat': 'spreadAngle', 'name': 'Yayılım Açısı', 'tiers': {1: [12, 15], 2: [8, 11], 3: [4, 7]}},
            {'stat': 'shockwave', 'name': 'Şok Dalgası', 'tiers': {1: [200, 250], 2: [150, 199], 3: [100, 149]}},
            {'stat': 'poisonDps', 'name': 'Zehir (DPS)', 'tiers': {1: [10, 15], 2: [6, 9], 3: [2, 5]}},
        ],
        'armor_prefixes': [
            {'stat': 'maxHp', 'name': 'Maksimum Can', 'tiers': {1: [25, 35], 2: [15, 24], 3: [5, 14]}},
            {'stat': 'armor', 'name': 'Zırh', 'tiers': {1: [15, 20], 2: [8, 14], 3: [3, 7]}},
            {'stat': 'thorns', 'name': 'Dikenler', 'tiers': {1: [40, 60], 2: [25, 39], 3: [10, 24]}},
            {'stat': 'statusDuration', 'name': 'Etki Süresi', 'tiers': {1: [0.4, 0.6], 2: [0.2, 0.39], 3: [0.1, 0.19]}},
        ],
        'armor_suffixes': [
            {'stat': 'dodgeChance', 'name': 'Kaçınma', 'tiers': {1: [0.1, 0.15], 2: [0.06, 0.09], 3: [0.02, 0.05]}},
            {'stat': 'hpRegen', 'name': 'Can Yenileme', 'tiers': {1: [6, 8], 2: [3, 5], 3: [1, 2]}},
            {'stat': 'combatRegen', 'name': 'Savaş İçi Yenilenme', 'tiers': {1: [4, 5], 2: [2, 3], 3: [1, 1]}},
            {'stat': 'orbHealMult', 'name': 'Küre Şifası', 'tiers': {1: [0.8, 1.0], 2: [0.4, 0.79], 3: [0.15, 0.39]}},
        ],
        'utility_prefixes': [
            {'stat': 'goldGain', 'name': 'Altın Kazancı', 'tiers': {1: [0.3, 0.4], 2: [0.15, 0.29], 3: [0.05, 0.14]}},
            {'stat': 'magicFind', 'name': 'Eşya Bulma', 'tiers': {1: [0.4, 0.5], 2: [0.2, 0.39], 3: [0.1, 0.19]}},
            {'stat': 'orbitDrones', 'name': 'Yörünge Dronu', 'tiers': {1: [1.0, 1.2], 2: [0.6, 0.9], 3: [0.2, 0.5]}},
            {'stat': 'thiefChance', 'name': 'Çalma Şansı', 'tiers': {1: [0.1, 0.15], 2: [0.05, 0.09], 3: [0.02, 0.04]}},
        ],
        'utility_suffixes': [
            {'stat': 'speed', 'name': 'Hareket Hızı', 'tiers': {1: [2, 3], 2: [1, 1.9], 3: [0.5, 0.9]}},
            {'stat': 'cooldownReduction', 'name': 'Bekleme Süresi', 'tiers': {1: [0.3, 0.4], 2: [0.15, 0.29], 3: [0.05, 0.14]}},
            {'stat': 'xpGain', 'name': 'XP Kazancı', 'tiers': {1: [0.2, 0.3], 2: [0.1, 0.19], 3: [0.05, 0.09]}},
            {'stat': 'magnetRadius', 'name': 'Mıknatıs', 'tiers': {1: [300, 400], 2: [200, 299], 3: [100, 199]}},
            {'stat': 'killSpeedBoost', 'name': 'Öldürme Hızı', 'tiers': {1: [0.8, 1.0], 2: [0.4, 0.79], 3: [0.2, 0.39]}},
        ],
        'pet_prefixes': [
            {'stat': 'minionDamage', 'name': 'Minyon Hasarı', 'tiers': {1: [0.6, 0.8], 2: [0.3, 0.59], 3: [0.1, 0.29]}},
            {'stat': 'minionCount', 'name': 'Minyon Sayısı', 'tiers': {1: [1, 1], 2: [1, 1], 3: [1, 1]}},
            {'stat': 'minionRate', 'name': 'Minyon Hızı', 'tiers': {1: [0.4, 0.5], 2: [0.2, 0.39], 3: [0.1, 0.19]}},
            {'stat': 'minionProjectileCount', 'name': 'Minyon Mermisi', 'tiers': {1: [2, 2], 2: [1, 1], 3: [1, 1]}},
            {'stat': 'minionPierce', 'name': 'Minyon Delme', 'tiers': {1: [2, 2], 2: [1, 1], 3: [1, 1]}},
        ],
        'pet_suffixes': [
            {'stat': 'minionMaxHp', 'name': 'Minyon Canı', 'tiers': {1: [0.4, 0.5], 2: [0.2, 0.39], 3: [0.1, 0.19]}},
            {'stat': 'minionArmor', 'name': 'Minyon Zırhı', 'tiers': {1: [20, 30], 2: [10, 19], 3: [5, 9]}},
            {'stat': 'toxicAura', 'name': 'Zehir Aurası', 'tiers': {1: [40, 50], 2: [20, 39], 3: [10, 19]}},
            {'stat': 'minionRange', 'name': 'Minyon Menzili', 'tiers': {1: [0.4, 0.5], 2: [0.2, 0.39], 3: [0.1, 0.19]}},
            {'stat': 'minionBounce', 'name': 'Minyon Sekme', 'tiers': {1: [2, 2], 2: [1, 1], 3: [1, 1]}},
        ],
        'broken': [
            {'stat': 'bossDmgMult', 'name': 'Void Hunter', 'val': [1.5, 3.0]},
            {'stat': 'dashCooldownReduc', 'name': 'Quantum Leap', 'val': [0.5, 0.8]},
            {'stat': 'lifesteal', 'name': 'Soul Drinker', 'val': [0.1, 0.2]},
            {'stat': 'armorPen', 'name': 'Armor Shredder', 'val': [0.5, 1.0]},
            {'stat': 'blackHoleChance', 'name': 'Singularity', 'val': [0.05, 0.1]}
        ],
        'negative': [
            {'stat': 'maxHp', 'name': 'Kırılgan', 'val': [-10, -30]},
            {'stat': 'speed', 'name': 'Ağır', 'val': [-1, -3]},
            {'stat': 'critChance', 'name': 'Kör', 'val': [-0.05, -0.15]},
            {'stat': 'dmgMult', 'name': 'Zayıf', 'val': [-0.1, -0.3]},
            {'stat': 'fireRate', 'name': 'Yavaş', 'val': [-0.1, -0.3]}
        ]
    }

    orbs = [
        { 'name': "🟣 Özel Küre (Special)", 'type': 'orb', 'orb_id': 'special_orb', 'icon_id': 'orb_special', 'rarity': 'Unique', 'price': 5000, 
          'desc': 'Rastgele bir özelliği siler ve yerine ultra-nadir BİR KIRIK ÖZELLİK ekler.' },
        { 'name': "🔴 Lanetli Küre (Corrupted)", 'type': 'orb', 'orb_id': 'corrupted_orb', 'icon_id': 'orb_corrupted', 'rarity': 'Unique', 'price': 3000, 
          'desc': 'Eşyayı mühürler. Ya +1 affix sınırı ile güçlendirir ya da bir özelliği negatife çevirir.' },
        { 'name': "⚪ Çıkartma Orbu (Scour)", 'type': 'orb', 'orb_id': 'scour', 'icon_id': 'orb_chaos', 'rarity': 'Rare', 'price': 200, 
          'desc': 'Eşyadan rastgele bir özelliği siler.' },
        { 'name': "🟦 Prefix Silme Orbu", 'type': 'orb', 'orb_id': 'p_scour', 'icon_id': 'orb_chaos', 'rarity': 'Rare', 'price': 400, 
          'desc': 'Eşyadan rastgele bir Prefix siler.' },
        { 'name': "🟧 Suffix Silme Orbu", 'type': 'orb', 'orb_id': 's_scour', 'icon_id': 'orb_chaos', 'rarity': 'Rare', 'price': 400, 
          'desc': 'Eşyadan rastgele bir Suffix siler.' },
        { 'name': "🟩 Prefix Ekleme Orbu", 'type': 'orb', 'orb_id': 'p_add', 'icon_id': 'orb_chaos', 'rarity': 'Rare', 'price': 1000, 
          'desc': 'Boş slot varsa rastgele bir Prefix ekler.' },
        { 'name': "🟨 Suffix Ekleme Orbu", 'type': 'orb', 'orb_id': 's_add', 'icon_id': 'orb_chaos', 'rarity': 'Rare', 'price': 1000, 
          'desc': 'Boş slot varsa rastgele bir Suffix ekler.' },
        { 'name': "💎 Ekleme Orbu (Aug)", 'type': 'orb', 'orb_id': 'aug', 'icon_id': 'orb_chaos', 'rarity': 'Rare', 'price': 2000, 
          'desc': 'Eksik bir Prefix veya Suffix ekler.' },
        { 'name': "💠 Yüce Küre (Exalted)", 'type': 'orb', 'orb_id': 'exalted', 'icon_id': 'orb_chaos', 'rarity': 'Rare', 'price': 3000, 
          'desc': 'Eşyaya rastgele yüksek seviye (T1-T2) bir özellik ekler.' },
        { 'name': "🌟 İlahi Küre (Divine)", 'type': 'orb', 'orb_id': 'divine', 'icon_id': 'orb_chaos', 'rarity': 'Rare', 'price': 2500, 
          'desc': 'Özelliklerin değerlerini mevcut seviyesi (Tier) içinde yeniden belirler.' },
        { 'name': "🌀 Kaos Küresi (Chaos)", 'type': 'orb', 'orb_id': 'chaos', 'icon_id': 'orb_chaos', 'rarity': 'Rare', 'price': 2000, 
          'desc': 'Tüm özellikleri rastgele yeniler.' },
        { 'name': "💫 Tier Orbu (Upgrade)", 'type': 'orb', 'orb_id': 'tier', 'icon_id': 'orb_chaos', 'rarity': 'Rare', 'price': 1500, 
          'desc': 'Eşyanın nadirliğini arttırır (Normal -> Magic -> Rare).' },
        { 'name': "✨ Kutsanmış Küre (Blessed)", 'type': 'orb', 'orb_id': 'blessed', 'icon_id': 'orb_chaos', 'rarity': 'Unique', 'price': 2500, 
          'desc': 'Eşyadaki özelliklerin değerlerini bulundukları Tier\'ın maksimum değerine çeker.' }
    ]

    def generate(self, mf_value=1.0, is_shop=False, shop_rarity=1, difficulty="Normal", wave_level=1, is_boss=False):
        weights = [100, 30 * mf_value, 10 * mf_value, 2 * mf_value]
        
        if is_shop:
            weights = [
                max(5, 60 - shop_rarity * 4), 
                max(10, 30 + shop_rarity * 3), 
                max(5, 12 + shop_rarity * 4),  
                0 
            ]
        elif difficulty == "Normal" and not is_boss:
            weights[3] = 0
        
        rarities = ["Normal", "Magic", "Rare", "Unique"]
        
        if is_boss:
            rarity = "Unique"
        else:
            rarity = random.choices(rarities, weights=weights)[0]
        
        if random.random() < 0.1 and not is_shop:
            available_orbs = self.orbs
            if difficulty == "Normal":
                available_orbs = [o for o in self.orbs if o['orb_id'] not in ['special_orb', 'corrupted_orb']]
            return random.choice(available_orbs).copy()

        valid_bases = self.bases
        if wave_level < 10:
            valid_bases = [b for b in self.bases if b.get('type') != 'essence']
            
        unlocked_tier = 4
        if wave_level >= 30: unlocked_tier = 1
        elif wave_level >= 20: unlocked_tier = 2
        elif wave_level >= 10: unlocked_tier = 3
        
        valid_bases = [b for b in valid_bases if b.get('tier', 4) >= unlocked_tier]
        
        if not valid_bases: valid_bases = [self.bases[0]]
        base = random.choice(valid_bases)
        
        if base.get('type') == 'essence': rarity = "Normal"
        
        price_map = {"Normal": 50, "Magic": 250, "Rare": 2000, "Unique": 5000}
        
        item = {
            "id": int(time.time() * 1000) + random.randint(0, 1000),
            "name": base["name"],
            "base_name": base["name"],
            "type": base["type"],
            "rarity": rarity,
            "price": 2000 if base.get('type') == 'essence' else price_map.get(rarity, 100),
            "itemBase": base.get("itemBase", {}).copy(),
            "baseStats": {}, 
            "prefixes": [],
            "suffixes": [],
            "setTag": None
        }
        
        for key, value in base.items():
            if key not in item:
                item[key] = value
                
        if 'price' in base:
            item['price'] = base['price']
        
        if rarity != "Normal" and item['type'] not in ['artifact', 'pet'] and random.random() < 0.15:
            item['setTag'] = random.choice(list(self.set_types.keys()))
            
        self.apply_affixes(item)
        self.update_item_name(item)
        return item

    def apply_affixes(self, item):
        if item.get('type') == 'essence': return
        rarity_limits = {"Normal": 0, "Magic": 1, "Rare": 2, "Unique": 3}
        limit = rarity_limits.get(item["rarity"], 0)
        if limit == 0: return

        num_prefix = random.randint(max(0, limit-1), limit)
        num_suffix = random.randint(max(0, limit-1), limit)
        
        group_key = 'utility'
        if item['type'] == 'weapon': group_key = 'weapon'
        elif item['type'] in ['chest', 'helmet']: group_key = 'armor'
        elif item['type'] == 'pet': group_key = 'pet'
        elif item['type'] == 'amulet': group_key = 'utility'
        
        av_prefixes = self.affixes.get(f'{group_key}_prefixes', []).copy()
        av_suffixes = self.affixes.get(f'{group_key}_suffixes', []).copy()

        for _ in range(num_prefix):
            if av_prefixes:
                p = random.choice(av_prefixes)
                tier = self.roll_tier(item['rarity'])
                val = random.uniform(p['tiers'][tier][0], p['tiers'][tier][1])
                item['prefixes'].append({
                    "name": f"{p['name']} (T{tier})", "stat": p['stat'], 
                    "val": round(val, 2), "tier": tier, "label": "P", "base_name": p['name']
                })
                av_prefixes.remove(p)
        
        for _ in range(num_suffix):
            if av_suffixes:
                s = random.choice(av_suffixes)
                tier = self.roll_tier(item['rarity'])
                val = random.uniform(s['tiers'][tier][0], s['tiers'][tier][1])
                item['suffixes'].append({
                    "name": f"{s['name']} (T{tier})", "stat": s['stat'], 
                    "val": round(val, 2), "tier": tier, "label": "S", "base_name": s['name']
                })
                av_suffixes.remove(s)

    def roll_tier(self, rarity):
        if rarity == "Magic": return 3
        elif rarity == "Rare": return 2 if random.random() < 0.4 else 3
        elif rarity == "Unique":
            r = random.random()
            if r < 0.25: return 1
            if r < 0.70: return 2
            return 3
        return 3

    def apply_orb(self, item, orb_id):
        if item.get('type') == 'orb': return "Bir orbu başka orba basamazsın!"
        if item.get('type') == 'essence': return "Özlere (Essence) orb basılamaz!"
        if item.get('is_corrupted'): return "Eşya lanetlenmiş (Corrupted), üzerinde değişiklik yapılamaz!"
        
        rarities = ["Normal", "Magic", "Rare", "Unique"]
        r_limit = {"Normal": 0, "Magic": 1, "Rare": 2, "Unique": 3}
        
        group_key = 'utility'
        if item['type'] == 'weapon': group_key = 'weapon'
        elif item['type'] in ['chest', 'helmet']: group_key = 'armor'
        elif item['type'] == 'pet': group_key = 'pet'
        elif item['type'] == 'amulet': group_key = 'utility'

        if orb_id == 'scour':
            all_affixes = item['prefixes'] + item['suffixes']
            if not all_affixes: return "Eşyada silinecek özellik yok!"
            target = random.choice(all_affixes)
            if target in item['prefixes']: item['prefixes'].remove(target)
            else: item['suffixes'].remove(target)

        elif orb_id == 'p_scour':
            if not item['prefixes']: return "Eşyada prefix yok!"
            item['prefixes'].pop(random.randint(0, len(item['prefixes'])-1))

        elif orb_id == 's_scour':
            if not item['suffixes']: return "Eşyada suffix yok!"
            item['suffixes'].pop(random.randint(0, len(item['suffixes'])-1))

        elif orb_id in ['p_add', 's_add', 'aug', 'exalted']:
            limit = r_limit.get(item['rarity'], 0)
            
            can_p = len(item['prefixes']) < limit
            can_s = len(item['suffixes']) < limit
            
            if orb_id == 'p_add' and not can_p: return f"{item['rarity']} için prefix sınırı doldu!"
            if orb_id == 's_add' and not can_s: return f"{item['rarity']} için suffix sınırı doldu!"
            if not can_p and not can_s: return "Eşya zaten maksimum kapasitede!"
            
            if orb_id == 'p_add': choice = 'p'
            elif orb_id == 's_add': choice = 's'
            else: choice = random.choice([x for x, b in [('p', can_p), ('s', can_s)] if b])
            
            existing = [x['stat'] for x in item['prefixes'] + item['suffixes']]
            if choice == 'p':
                av = [x for x in self.affixes.get(f'{group_key}_prefixes', []) if x['stat'] not in existing]
                if not av: return "Eklenecek uygun özellik kalmadı!"
                p = random.choice(av)
                tier = 1 if orb_id == 'exalted' else self.roll_tier(item['rarity'])
                val = random.uniform(p['tiers'][tier][0], p['tiers'][tier][1])
                item['prefixes'].append({"name": f"{p['name']} (T{tier})", "stat": p['stat'], "val": round(val, 2), "tier": tier, "label": "P", "base_name": p['name']})
            else:
                av = [x for x in self.affixes.get(f'{group_key}_suffixes', []) if x['stat'] not in existing]
                if not av: return "Eklenecek uygun özellik kalmadı!"
                s = random.choice(av)
                tier = 1 if orb_id == 'exalted' else self.roll_tier(item['rarity'])
                val = random.uniform(s['tiers'][tier][0], s['tiers'][tier][1])
                item['suffixes'].append({"name": f"{s['name']} (T{tier})", "stat": s['stat'], "val": round(val, 2), "tier": tier, "label": "S", "base_name": s['name']})

        elif orb_id == 'divine':
            for aff in item['prefixes'] + item['suffixes']:
                pool = self.affixes.get(f'{group_key}_prefixes', []) + self.affixes.get(f'{group_key}_suffixes', [])
                match = next((x for x in pool if x['stat'] == aff['stat']), None)
                # "Kırık" affixler tier 0 ile geliyor ve tiers sözlüğünde yok;
                # doğrudan indekslemek KeyError: 0 yaratıyordu (C6)
                if match and aff.get('tier') in match['tiers']:
                    tier = aff['tier']
                    aff['val'] = round(random.uniform(match['tiers'][tier][0], match['tiers'][tier][1]), 2)

        elif orb_id == 'chaos':
            if item['rarity'] == 'Normal': return "Normal eşyaya Kaos basılamaz!"
            item['prefixes'] = []
            item['suffixes'] = []
            self.apply_affixes(item)

        elif orb_id == 'tier':
            idx = rarities.index(item['rarity'])
            if idx >= 2: return "Sadece Rare seviyesine kadar yükseltilebilir!"
            item['rarity'] = rarities[idx + 1]
            self.apply_orb(item, 'aug')
            self.apply_orb(item, 'aug')

        elif orb_id == 'blessed':
            for aff in item['prefixes'] + item['suffixes']:
                pool = self.affixes.get(f'{group_key}_prefixes', []) + self.affixes.get(f'{group_key}_suffixes', [])
                match = next((x for x in pool if x['stat'] == aff['stat']), None)
                # tier 0 ("kırık" affix) tiers sözlüğünde yok -> KeyError (C6)
                if match and aff.get('tier') in match['tiers']:
                    tier = aff['tier']
                    aff['val'] = round(match['tiers'][tier][1], 2)

        elif orb_id == 'special_orb':
            all_affixes = item['prefixes'] + item['suffixes']
            if all_affixes:
                target = random.choice(all_affixes)
                if target in item['prefixes']: item['prefixes'].remove(target)
                else: item['suffixes'].remove(target)
            
            b = random.choice(self.affixes['broken'])
            item['prefixes'].append({"name": b['name'], "stat": b['stat'], "val": round(random.uniform(b['val'][0], b['val'][1]), 2), "tier": 0, "label": "P", "base_name": b['name']})

        elif orb_id == 'corrupted_orb':
            item['is_corrupted'] = True
            if random.random() < 0.5:
                b = random.choice(self.affixes['broken'])
                item['suffixes'].append({"name": f"Lanetli {b['name']}", "stat": b['stat'], "val": round(random.uniform(b['val'][0], b['val'][1]), 2), "tier": 0, "label": "S", "base_name": b['name']})
            else:
                all_affixes = item['prefixes'] + item['suffixes']
                if all_affixes:
                    target = random.choice(all_affixes)
                    if target in item['prefixes']: item['prefixes'].remove(target)
                    else: item['suffixes'].remove(target)
                neg = random.choice(self.affixes['negative'])
                item['suffixes'].append({"name": f"Lanetli {neg['name']}", "stat": neg['stat'], "val": round(random.uniform(neg['val'][0], neg['val'][1]), 2), "tier": 0, "label": "S", "base_name": neg['name']})

        self.update_item_name(item)
        return None

    def update_item_name(self, item):
        base_name = item.get('base_name', 'Bilinmeyen')
        set_name = ""
        if item.get('setTag'):
            # Eski kayıtlarda artık tanımsız olan setTag'ler KeyError atıyordu
            set_info = self.set_types.get(item['setTag'])
            if set_info:
                set_name = f"[{set_info.get('name', '')}]"
            
        item['name'] = f"{set_name} {base_name}".strip()

