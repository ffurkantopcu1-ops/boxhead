import random
from datetime import date

from logic.data_loader import load_data

class QuestSystem:
    # Kaynak: data/quests.json
    QUEST_POOL = load_data('quests')

    def __init__(self):
        self.active_quests = []  # [{...quest_pool_entry..., progress, completed}]
        self.session_stats = {
            "kills": 0, "elite_kills": 0, "boss_kills": 0,
            "max_wave": 0, "gold_earned": 0, "gold_spent": 0,
            "max_combo": 0, "artifacts_used": 0, "cards_picked": 0,
            "minion_kills": 0, "max_level": 0, "low_hp_kills": 0,
            "dodges": 0, "items_sold": 0, "blood_moon_survived": 0,
            "evolved": 0, "rare_items": 0, "unique_items": 0
        }

    def load_or_reset(self, meta):
        """Günlük görevleri yükle veya sıfırla."""
        today = date.today().isoformat()
        if meta.get("last_quest_date") != today:
            # Yeni gün: 3 rastgele görev seç
            chosen = random.sample(self.QUEST_POOL, 3)
            self.active_quests = [
                {**q, "progress": 0, "completed": False} for q in chosen
            ]
            meta["last_quest_date"] = today
            meta["daily_quests"] = self.active_quests
        else:
            self.active_quests = meta.get("daily_quests", [])
            # Ensure progress/completed keys exist
            for q in self.active_quests:
                q.setdefault("progress", 0)
                q.setdefault("completed", False)
        return meta

    def track(self, event_type, value=1, meta=None):
        """Olay tetiklendiğinde görev ilerlemesini güncelle."""
        earned = 0
        for q in self.active_quests:
            if q["completed"]:
                continue
            if q["type"] == event_type:
                if event_type in ("max_combo", "reach_wave", "reach_level"):
                    q["progress"] = max(q["progress"], value)
                else:
                    q["progress"] += value
                if q["progress"] >= q["target"]:
                    q["completed"] = True
                    earned += q["reward"]
        return earned  # Kazanılan kristal miktarı

    def get_display_quests(self):
        return self.active_quests

    def save_to_meta(self, meta):
        meta["daily_quests"] = self.active_quests
        return meta
