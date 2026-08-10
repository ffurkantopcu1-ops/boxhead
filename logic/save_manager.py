import copy
import json
import os
import time
from datetime import datetime

# tilemap saf veri modülü (pygame/logic bağımlılığı yok) — döngüsel import riski
# taşımaz; game_logic zaten save_manager'ı import ediyor.
from logic.tilemap import TileMap

class SaveManager:
    SAVE_DIR = "saves"

    # Kartların oyuncuya yazdığı DAVRANIŞ bayrakları. Kayıtta yalnızca
    # active_cards tutulduğu için yükleme sırasında bunlar yeniden kurulur;
    # önce buradaki varsayılanlara sıfırlanır ki (oyun içi yükleme) mevcut
    # koşunun kartları üst üste binmesin. Değerler entities/player.py'deki
    # __init__ varsayılanlarıyla birebir aynıdır.
    CARD_FLAG_DEFAULTS = {
        "damage_taken_mult": 1.0,
        "self_dmg_on_hit": 0.0,
        "poison_convert": False,
        "stun_on_crit": 0.0,
        "execute_threshold": 0.0,
        "revive_count": 0,
        "death_explosion": False,
        "passive_hp_drain": 0.0,
        "passive_shield_cd": 0.0,
        "adrenaline_active": False,
        "lifesteal_bonus": 0.0,
        "xp_on_hit_bonus": 0.0,
        "kill_hp_bonus": 0.0,
        "periodic_freeze_cd": 0.0,
        "lightning_proc_hits": 0,
        "artifact_hp_cost": 0,
        "alpha_mode": False,
        "minion_respawn_chance": 0.0,
        "shop_discount": 0.0,
        "pact_devil_waves": 0,
        "berserker_rage": False,
        "has_shadow_clone": False,
        "has_midas_touch": False,
        "has_mutation": False,
        "has_static_armor": False,
        "has_ricochet_master": False,
        "has_blood_bank": False,
        "blood_bank_amount": 0,
        "has_chaos_field": False,
        "has_doppelganger": False,
        "has_furnace": False,
    }

    # Başlangıç silahlarında (Player.init_class_specialization) eskiden
    # weaponClass alanı yoktu; o silah geri takıldığında sınıf eski silahın
    # sınıfında takılı kalıyordu. Eski kayıtlar yüklenirken geri doldurulur.
    LEGACY_STARTING_WEAPON_CLASSES = {
        "Eski Kılıç": "warrior",
        "Basit Arbalet": "sniper",
        "Paslı Katana": "ninja",
        "Zehir Şişesi": "alchemist",
        "Sihir Asası": "sorcerer",
        "Kan Kılıcı": "bloodwalker",
        "Taret Kiti": "engineer",
    }

    @staticmethod
    def _find_evolution_id(player, class_name):
        """Gösterim adından evrim kimliğini çözer (eski kayıtlar için)."""
        for evo_id, evo in getattr(player, "EVOLUTIONS", {}).items():
            if evo.get("name") == class_name:
                return evo_id
        return ""

    @staticmethod
    def backfill_weapon_classes(equipped, bag):
        """Eski kayıtlardaki weaponClass'sız başlangıç silahlarını onarır."""
        items = list(equipped.values()) + list(bag)
        for item in items:
            if not isinstance(item, dict) or item.get("type") != "weapon":
                continue
            if item.get("weaponClass"):
                continue
            w_class = SaveManager.LEGACY_STARTING_WEAPON_CLASSES.get(item.get("name"))
            if w_class:
                item["weaponClass"] = w_class

    @staticmethod
    def _reset_card_flags(player):
        """Kart bayraklarını varsayılana çeker, kristal dükkânı payını korur."""
        for attr, default in SaveManager.CARD_FLAG_DEFAULTS.items():
            setattr(player, attr, default)

        # revive_count ve shop_discount kristal yükseltmelerinden de gelebilir;
        # sıfırlama bunları silmesin diye meta'dan yeniden hesaplanır.
        try:
            from logic.crystal_shop import CrystalShop
            meta = SaveManager.load_meta()
            shop = CrystalShop()
            player.revive_count = int(shop.get_effective(meta, "start_revive"))
            player.shop_discount = min(0.9, shop.get_effective(meta, "shop_discount"))
        except Exception as e:
            print("Kristal bonusu geri yuklenemedi:", e)

    @staticmethod
    def restore_card_effects(logic, player, saved_cards, saved_synergies):
        """active_cards listesinden kart DAVRANIŞ bayraklarını yeniden kurar.

        Kayıtta yalnızca kart kimlikleri var; `damage_taken_mult`, `revive_count`
        gibi bayraklar kayıp oluyordu (Cam Top'un x2 hasar bedeli yüklemede
        siliniyor, kart saf buff'a dönüyordu). apply_card stat katkılarını da
        tekrar eklediği için skills_permanent snapshot'ı geri konur; böylece
        statlar çift sayılmaz.
        """
        card_system = logic.card_system
        # Sinerjiler önce kurulur: check_synergies zaten aktif olanları atlar,
        # böylece sinerji bonusları da tekrar eklenmez.
        card_system.synergy_system.active_synergies = list(saved_synergies)

        snapshot = copy.deepcopy(getattr(player, "skills_permanent", {}))
        SaveManager._reset_card_flags(player)

        card_system.active_cards = []
        for card_id in saved_cards:
            try:
                card_system.apply_card(card_id, player)
            except Exception as e:
                print(f"Kart geri yuklenemedi ({card_id}):", e)

        # Kayıttaki sıra/liste korunur (apply_card bulamadığı kartı eklemez)
        card_system.active_cards = list(saved_cards)
        # Stat çift sayımını geri al
        player.skills_permanent = snapshot

        # Evrimden gelen tek-pet modu kart sıfırlamasında kaybolmasın
        if getattr(player, "evolution_passive", "") == "alpha_pet":
            player.alpha_mode = True

    @staticmethod
    def delete_save(slot_name):
        """Kayıt dosyasını siler. Dönüş: silindiyse True, dosya yoksa False."""
        file_path = os.path.join(SaveManager.SAVE_DIR, f"{slot_name}.json")
        try:
            os.remove(file_path)
            return True
        except FileNotFoundError:
            print(f"Silinecek kayit bulunamadi: {file_path}")
            return False
        except OSError as e:
            print(f"Kayit silinemedi ({file_path}): {e}")
            return False

    @staticmethod
    def ensure_dir():
        if not os.path.exists(SaveManager.SAVE_DIR):
            os.makedirs(SaveManager.SAVE_DIR)
            
    @staticmethod
    def load_meta():
        path = os.path.join(SaveManager.SAVE_DIR, "meta.json")
        if not os.path.exists(path):
            return {"crystals": 0, "upgrades": {}}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"crystals": 0, "upgrades": {}}

    @staticmethod
    def save_meta(meta_data):
        SaveManager.ensure_dir()
        path = os.path.join(SaveManager.SAVE_DIR, "meta.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, indent=4)

            
    @staticmethod
    def save_game(logic, slot_name):
        SaveManager.ensure_dir()
        p = logic.players[logic.local_player_id]
        
        save_data = {
            "metadata": {
                "level": p.level,
                "wave": logic.wave["level"],
                "class": p.class_id,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "timestamp": time.time()
            },
            "player": {
                "level": p.level,
                "xp": getattr(p, 'xp', 0),
                "xp_to_next_level": getattr(p, 'xp_to_next_level', 100),
                "gold": p.gold,
                "skill_points": p.skill_points,
                "hp": getattr(p, 'hp', 100),
                "energy_shield": getattr(p, 'energy_shield', 0),
                "class_id": p.class_id,
                "base_class_id": getattr(p, 'base_class_id', p.class_id),
                "class_name": p.class_name,
                "evolution": getattr(p, 'evolution', ""),
                "evolution_passive": getattr(p, 'evolution_passive', ""),
                "skills": p.skills,
                # Yetenek ağacı: koşu-kapsamlı tahsis (meta.json'a DEĞİL buraya).
                "allocated_nodes": sorted(getattr(p, 'allocated_nodes', [])),
                # Ascendancy (alt-sınıf) tahsisi + puanı
                "ascendancy_points": getattr(p, 'ascendancy_points', 0),
                "ascendancy_nodes": sorted(getattr(p, 'ascendancy_nodes', [])),
                "skills_permanent": getattr(p, 'skills_permanent', {}),
                "x": p.x,
                "y": p.y,
                "auto_sell": getattr(p, 'auto_sell', False),
                "active_auras": getattr(p, 'active_auras', []),
                # Öz yatırımı ve satın alınan auralar eskiden kaydedilmiyordu:
                # oyuncu harcadığı özleri/aura parasını yüklemede kaybediyordu.
                "essence_stats": getattr(p, 'essence_stats', {}),
                "is_essence_system_unlocked": getattr(p, 'is_essence_system_unlocked', False),
                "purchased_auras": getattr(p, 'purchased_auras', []),
                # aura_limit KAYDEDİLMEZ: recalculate_stats her çağrıda onu
                # kuşanılan eşyalardan yeniden hesaplıyor (türetilmiş stat).
                "evolutions": getattr(p, 'evolutions', []),
                "is_evolved": getattr(p, 'is_evolved', False),
                "color": p.color,
                "passive_shield_cd": getattr(p, 'passive_shield_cd', 0),
                "speed_mod": getattr(p, 'speed_mod', 1.0)
            },
            "inventory": {
                "equipped": p.inv_manager.equipped,
                "bag": p.inventory
            },
            "wave": {
                "level": logic.wave["level"],
                "difficulty": getattr(logic, 'difficulty', 'normal'),
                # Prosedürel arena tohumu: harita dizi olarak saklanmaz, bu tek
                # sayıdan türetilir (logic/tilemap.py). Kaydedilmezse yüklenen
                # oyun başka bir arenada açılırdı.
                "map_seed": getattr(logic, 'map_seed', 0),
            },
            "card_system": {
                "active_cards": getattr(logic.card_system, 'active_cards', []),
                "passive_stats": getattr(logic.card_system, 'passive_stats', {}),
                "active_synergies": getattr(logic.card_system.synergy_system, 'active_synergies', [])
            }
        }
        
        file_path = os.path.join(SaveManager.SAVE_DIR, f"{slot_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=4)
        print(f"Oyun kaydedildi: {file_path}")

    @staticmethod
    def load_game(logic, slot_name):
        file_path = os.path.join(SaveManager.SAVE_DIR, f"{slot_name}.json")
        if not os.path.exists(file_path):
            return False
            
        with open(file_path, "r", encoding="utf-8") as f:
            save_data = json.load(f)
            
        p = logic.players[logic.local_player_id]
        
        # Player Stats
        pd = save_data["player"]
        p.level = pd.get("level", 1)
        p.xp = pd.get("xp", 0)
        p.xp_to_next_level = pd.get("xp_to_next_level", 100)
        p.gold = pd.get("gold", 0)
        p.skill_points = pd.get("skill_points", 0)
        p.class_id = pd.get("class_id", "warrior")
        p.base_class_id = pd.get("base_class_id", p.class_id)
        p.class_name = pd.get("class_name", "Savaşçı")
        # p.skills gerçek yapısı list-of-dict; eski/bozuk kayıtta dict gelirse
        # yetenek sekmesi çöküyordu. Geçersizse sınıfın varsayılan listesi kalır.
        saved_skills = pd.get("skills")
        if isinstance(saved_skills, list) and all(isinstance(s, dict) for s in saved_skills):
            p.skills = saved_skills
        else:
            print("Kayittaki yetenek listesi gecersiz, varsayilan liste korundu.")
        p.skills_permanent = pd.get("skills_permanent", {})

        # --- YETENEK AĞACI (koşu-kapsamlı) ---
        # Eski kayıtlarda "allocated_nodes" yok: başlangıç düğümünü tohumla ve
        # eski düz "skills" seviyelerini SP olarak iade et ki oyuncu yatırdığı
        # puanları yeni ağaçta yeniden harcayabilsin (kayıp olmasın). Seviyeler
        # sıfırlanır; yoksa recalculate_stats hem ağacı hem eski skili sayar.
        from logic.skill_tree import SkillTree
        if "allocated_nodes" in pd:
            p.allocated_nodes = set(pd.get("allocated_nodes", []))
            p.allocated_nodes |= set(SkillTree.start_nodes_for(p.base_class_id))
        else:
            refund = 0
            if isinstance(p.skills, list):
                for sk in p.skills:
                    refund += int(sk.get("lvl", 0) or 0)
                    sk["lvl"] = 0
            p.skill_points = p.skill_points + refund
            p.allocated_nodes = set(SkillTree.start_nodes_for(p.base_class_id))

        p.x = pd.get("x", p.x)
        p.y = pd.get("y", p.y)
        p.auto_sell = pd.get("auto_sell", False)
        p.active_auras = pd.get("active_auras", [])
        # Öz/aura yatırımı (eski kayıtlarda yoksa mevcut değerler korunur)
        p.essence_stats = pd.get("essence_stats", getattr(p, 'essence_stats', {}))
        p.is_essence_system_unlocked = pd.get(
            "is_essence_system_unlocked", getattr(p, 'is_essence_system_unlocked', False))
        # purchased_auras kaydedilmiyordu: kuşanılmış aura "satın alınmamış"
        # görünüyor, kuşandan çıkarınca geri takılamıyordu.
        p.purchased_auras = pd.get("purchased_auras", list(p.active_auras))
        p.evolutions = pd.get("evolutions", [])
        p.is_evolved = pd.get("is_evolved", False)
        # Evrim durumu eskiden kaydedilmiyordu; eski kayıtlarda gösterim
        # adından (class_name) geriye doğru çözülür.
        p.evolution = pd.get("evolution") or SaveManager._find_evolution_id(p, p.class_name)
        p.evolution_passive = pd.get("evolution_passive") or \
            p.EVOLUTIONS.get(p.evolution, {}).get("passive", "")

        # --- ASCENDANCY (alt-sınıf) — evrim yukarıda çözüldükten SONRA ---
        from logic.ascendancy import Ascendancy
        p.ascendancy_points = pd.get("ascendancy_points", 0)
        p.ascendancy_nodes = set(pd.get("ascendancy_nodes") or [])
        if p.evolution:  # evrim seçilmişse başlangıç düğümü garanti (eski kayıt)
            start = Ascendancy.start_for(p.evolution)
            if start:
                p.ascendancy_nodes.add(start)

        if "color" in pd:
            p.color = tuple(pd["color"])

        if hasattr(p, 'reinit_specialization'):
            p.reinit_specialization()

        # Inventory
        inv = save_data.get("inventory", {})
        p.inv_manager.equipped = inv.get("equipped", {})
        p.inventory = inv.get("bag", [])
        SaveManager.backfill_weapon_classes(p.inv_manager.equipped, p.inventory)
        
        # Wave (To prevent empty spawn queue triggering next wave immediately)
        wave_data = save_data.get("wave", {})
        logic.wave["level"] = max(1, wave_data.get("level", 1) - 1)
        logic.difficulty = wave_data.get("difficulty", "normal")

        # Prosedürel arena: tohumu geri yükle (eski kayıtlarda yok -> mevcut
        # rastgele tohum korunur, sadece arena farklı görünür, oyun bozulmaz).
        seed = wave_data.get("map_seed")
        if seed is not None and hasattr(logic, 'tilemap'):
            logic.map_seed = int(seed)
            logic.tilemap = TileMap(logic.map_seed, world_size=logic.arena_size)

        # Biyomu kaydedilen dalgayla eşitle. Eskiden yüklenen oyun hangi
        # dalgada olursa olsun "forest" zemininde açılıyor, ancak bir sonraki
        # dalga geçişinde doğru biyoma atlıyordu.
        if hasattr(logic, 'biome_system'):
            biome_id, _ = logic.biome_system.get_biome_for_wave(logic.wave["level"])
            logic.biome_system.current_biome_id = biome_id
            logic.wave["biome"] = biome_id

        # Card System
        card_data = save_data.get("card_system", {})
        saved_cards = list(card_data.get("active_cards", []))
        logic.card_system.passive_stats = card_data.get("passive_stats", {})
        saved_synergies = card_data.get("active_synergies")
        if saved_synergies is None:
            # Eski kayıtlar sinerji kimliklerini saklamıyordu. Bonusları zaten
            # skills_permanent içinde olduğu için yalnızca aktif kimlikleri çıkar.
            active_cards = set(saved_cards)
            saved_synergies = [
                synergy["id"]
                for synergy in logic.card_system.synergy_system.SYNERGIES
                if all(card_id in active_cards for card_id in synergy["required_cards"])
            ]
        # Kart bayrakları (bedeller dâhil) yeniden kurulur; statlar çift sayılmaz
        SaveManager.restore_card_effects(logic, p, saved_cards, saved_synergies)

        logic.next_wave()

        # Kayıtta açıkça tutulan alanlar; Demir İrade'den gelen CD kaybolmasın
        p.passive_shield_cd = max(pd.get("passive_shield_cd", 0) or 0,
                                  getattr(p, 'passive_shield_cd', 0) or 0)
        p.speed_mod = pd.get("speed_mod", 1.0)

        # Recalculate (apply_card can/max_hp'yi değiştirdiği için hp en sona)
        p.inv_manager.recalculate_stats()
        p.hp = min(pd.get("hp", 100), p.max_hp)
        p.energy_shield = pd.get("energy_shield", 0)
        max_es = getattr(p, 'max_energy_shield', 0)
        if max_es:
            p.energy_shield = min(p.energy_shield, max_es)
        print(f"Oyun yüklendi: {file_path}")
        return True

    @staticmethod
    def get_save_slots():
        SaveManager.ensure_dir()
        slots = []
        for file in os.listdir(SaveManager.SAVE_DIR):
            if file == "meta.json":
                continue
            if file.endswith(".json"):
                slot_name = file.replace(".json", "")
                file_path = os.path.join(SaveManager.SAVE_DIR, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        meta = data.get("metadata", data)
                        slots.append({
                            "filename": slot_name,
                            "level": meta.get("level", data.get("level", 1)),
                            "wave": meta.get("wave", data.get("wave", 1)),
                            "class": meta.get("class", data.get("class_id", "warrior")),
                            "date": meta.get("date", data.get("save_date", "Unknown")),
                            "ts": meta.get("timestamp", os.path.getmtime(file_path))
                        })
                    except:
                        continue
        # En yeni tarihe göre sırala
        return sorted(slots, key=lambda x: x['ts'], reverse=True)
