import json
import os
import time
from datetime import datetime

class SaveManager:
    SAVE_DIR = "saves"
    
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
                "class_name": p.class_name,
                "skills": p.skills,
                "skills_permanent": getattr(p, 'skills_permanent', {}),
                "x": p.x,
                "y": p.y,
                "auto_sell": getattr(p, 'auto_sell', False),
                "active_auras": getattr(p, 'active_auras', []),
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
                "difficulty": getattr(logic, 'difficulty', 'normal')
            },
            "card_system": {
                "active_cards": getattr(logic.card_system, 'active_cards', []),
                "passive_stats": getattr(logic.card_system, 'passive_stats', {})
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
        p.hp = pd.get("hp", 100)
        p.energy_shield = pd.get("energy_shield", 0)
        p.class_id = pd.get("class_id", "warrior")
        p.class_name = pd.get("class_name", "Savaşçı")
        p.skills = pd.get("skills", {"str": 1, "dex": 1, "int": 1, "vit": 1})
        p.skills_permanent = pd.get("skills_permanent", {})
        p.x = pd.get("x", p.x)
        p.y = pd.get("y", p.y)
        p.auto_sell = pd.get("auto_sell", False)
        p.active_auras = pd.get("active_auras", [])
        p.evolutions = pd.get("evolutions", [])
        p.is_evolved = pd.get("is_evolved", False)
        if "color" in pd:
            p.color = tuple(pd["color"])
        p.passive_shield_cd = pd.get("passive_shield_cd", 0)
        p.speed_mod = pd.get("speed_mod", 1.0)
        
        if hasattr(p, 'reinit_specialization'):
            p.reinit_specialization()

        # Inventory
        inv = save_data.get("inventory", {})
        p.inv_manager.equipped = inv.get("equipped", {})
        p.inventory = inv.get("bag", [])
        
        # Wave (To prevent empty spawn queue triggering next wave immediately)
        wave_data = save_data.get("wave", {})
        logic.wave["level"] = max(1, wave_data.get("level", 1) - 1)
        logic.difficulty = wave_data.get("difficulty", "normal")
        
        # Card System
        card_data = save_data.get("card_system", {})
        logic.card_system.active_cards = card_data.get("active_cards", [])
        logic.card_system.passive_stats = card_data.get("passive_stats", {})

        logic.next_wave()
        
        # Recalculate
        p.inv_manager.recalculate_stats()
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
