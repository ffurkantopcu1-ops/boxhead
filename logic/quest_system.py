import random
from datetime import date

class QuestSystem:
    QUEST_POOL = [
        {"id": "kill_100",        "desc": "100 düşman öldür",                    "target": 100,  "reward": 8,  "type": "kill"},
        {"id": "kill_elite_10",   "desc": "10 Elite öldür",                       "target": 10,   "reward": 12, "type": "kill_elite"},
        {"id": "kill_boss",       "desc": "1 Boss öldür",                         "target": 1,    "reward": 15, "type": "kill_boss"},
        {"id": "survive_wave_10", "desc": "Wave 10'a ulaş",                      "target": 10,   "reward": 10, "type": "reach_wave"},
        {"id": "survive_wave_20", "desc": "Wave 20'ye ulaş",                     "target": 20,   "reward": 15, "type": "reach_wave"},
        {"id": "earn_5000_gold",  "desc": "5000 altın kazan",                    "target": 5000, "reward": 8,  "type": "earn_gold"},
        {"id": "collect_rare",    "desc": "Rare veya üstü eşya topla",           "target": 1,    "reward": 10, "type": "collect_rarity"},
        {"id": "collect_unique",  "desc": "Unique eşya topla",                   "target": 1,    "reward": 15, "type": "collect_unique"},
        {"id": "combo_30",        "desc": "30 Combo yap",                         "target": 30,   "reward": 8,  "type": "max_combo"},
        {"id": "combo_50",        "desc": "50 Combo yap",                         "target": 50,   "reward": 12, "type": "max_combo"},
        {"id": "use_artifact_10", "desc": "Artifact'i 10 kez kullan",            "target": 10,   "reward": 8,  "type": "use_artifact"},
        {"id": "blood_moon",      "desc": "Kan Ayı'nı hayatta geç",              "target": 1,    "reward": 15, "type": "blood_moon_survive"},
        {"id": "spend_3000_gold", "desc": "Markette 3000 altın harca",           "target": 3000, "reward": 8,  "type": "spend_gold"},
        {"id": "pick_3_cards",    "desc": "3 kart al",                            "target": 3,    "reward": 10, "type": "pick_cards"},
        {"id": "minion_kills_50", "desc": "Minyonların 50 düşman öldürsün",      "target": 50,   "reward": 8,  "type": "minion_kills"},
        {"id": "reach_level_10",  "desc": "Level 10'a ulaş",                    "target": 10,   "reward": 10, "type": "reach_level"},
        {"id": "kill_low_hp",     "desc": "%20 can altında 20 düşman öldür",    "target": 20,   "reward": 12, "type": "kill_while_low"},
        {"id": "dodge_10",        "desc": "10 kez dodge ile hasar alma",         "target": 10,   "reward": 10, "type": "dodge_hits"},
        {"id": "sell_10_items",   "desc": "10 eşya sat",                         "target": 10,   "reward": 8,  "type": "sell_items"},
        {"id": "evolve_class",    "desc": "Sınıf Evrimi geçir",                  "target": 1,    "reward": 20, "type": "evolve"},
    ]

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
        TYPE_MAP = {
            "kill":              "kill_100",
            "kill_elite":        "kill_elite_10",
            "kill_boss":         "kill_boss",
            "earn_gold":         "earn_5000_gold",
            "spend_gold":        "spend_3000_gold",
            "collect_rarity":    "collect_rare",
            "collect_unique":    "collect_unique",
            "max_combo":         "combo_30",
            "use_artifact":      "use_artifact_10",
            "blood_moon_survive":"blood_moon",
            "pick_cards":        "pick_3_cards",
            "minion_kills":      "minion_kills_50",
            "reach_level":       "reach_level_10",
            "kill_while_low":    "kill_low_hp",
            "dodge_hits":        "dodge_10",
            "sell_items":        "sell_10_items",
            "evolve":            "evolve_class",
            "reach_wave":        "survive_wave_10",
        }
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
