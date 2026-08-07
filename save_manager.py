import json
import os
import datetime

class SaveManager:
    def __init__(self, base_dir="saves"):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            
    def get_save_slots(self):
        """Mevcut kayıt dosyalarını listeler."""
        saves = []
        if not os.path.exists(self.base_dir): return []
        
        for f in os.listdir(self.base_dir):
            if f.endswith(".json"):
                path = os.path.join(self.base_dir, f)
                try:
                    with open(path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        saves.append({
                            "filename": f,
                            "level": data.get("level", 1),
                            "wave": data.get("wave", 1),
                            "class": data.get("class_id", "Unknown"),
                            "date": data.get("save_date", "Unknown")
                        })
                except:
                    continue
        return saves

    def save_game(self, logic, slot_name="last_save"):
        """Oyun durumunu JSON olarak kaydeder."""
        p = logic.players[logic.local_player_id]
        
        data = {
            "class_id": p.class_id,
            "level": p.level,
            "xp": p.xp,
            "gold": p.gold,
            "skill_points": p.skill_points,
            "wave": logic.wave["level"],
            "save_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "skills": p.skills,
            "inventory": p.inventory,
            "equipped": p.inv_manager.equipped,
            "is_essence_system_unlocked": getattr(p, "is_essence_system_unlocked", False),
            "purchased_auras": getattr(p, "purchased_auras", []),
            "active_auras": getattr(p, "active_auras", []),
            "essence_stats": getattr(p, "essence_stats", {})
        }
        
        filename = f"{slot_name}.json" if not slot_name.endswith(".json") else slot_name
        path = os.path.join(self.base_dir, filename)
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"Oyun Kaydedildi: {path}")
            return True
        except Exception as e:
            print(f"Kayıt Hatası: {e}")
            return False

    def load_game(self, logic, slot_name="last_save"):
        """Kayıtlı oyunu yükler ve logic state'i günceller."""
        filename = f"{slot_name}.json" if not slot_name.endswith(".json") else slot_name
        path = os.path.join(self.base_dir, filename)
        
        if not os.path.exists(path):
            print(f"Kayıt bulunamadı: {path}")
            return False
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            p = logic.players[logic.local_player_id]
            p.class_id = data.get("class_id", "warrior")
            p.level = data.get("level", 1)
            p.xp = data.get("xp", 0)
            p.gold = data.get("gold", 0)
            p.skill_points = data.get("skill_points", 0)
            p.skills = data.get("skills", p.skills)
            p.inventory = data.get("inventory", [])
            p.inv_manager.equipped = data.get("equipped", p.inv_manager.equipped)
            p.is_essence_system_unlocked = data.get("is_essence_system_unlocked", False)
            p.purchased_auras = data.get("purchased_auras", [])
            p.active_auras = data.get("active_auras", [])
            p.essence_stats = data.get("essence_stats", getattr(p, "essence_stats", {}))
            
            logic.wave["level"] = data.get("wave", 1)
            
            # Statları yeniden hesapla!
            p.inv_manager.recalculate_stats()
            # Canı doldur
            p.hp = p.max_hp
            
            # Temizlik
            logic.enemies = []
            logic.projectiles = []
            logic.particles = []
            logic.clouds = []
            
            print(f"Oyun Yüklendi: {path}")
            return True
        except Exception as e:
            print(f"Yükleme Hatası: {e}")
            return False

    def delete_save(self, slot_name):
        """Belirli bir kayıt dosyasını siler."""
        filename = f"{slot_name}.json" if not slot_name.endswith(".json") else slot_name
        path = os.path.join(self.base_dir, filename)
        if os.path.exists(path):
            os.remove(path)
            print(f"Kayıt Silindi: {path}")
            return True
        return False

    def delete_all_saves(self):
        """Tüm kayıt dosyalarını temizler."""
        if not os.path.exists(self.base_dir): return
        for f in os.listdir(self.base_dir):
            if f.endswith(".json"):
                os.remove(os.path.join(self.base_dir, f))
        print("Tüm Kayıtlar Temizlendi!")
