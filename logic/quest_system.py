import random
from datetime import date

from logic.data_loader import load_data

class QuestSystem:
    # Kaynak: data/quests.json
    QUEST_POOL = load_data('quests')

    # Gunluk gorev sayisi
    DAILY_COUNT = 3

    # Ilerlemesi "en yuksek deger" mantigiyla islenen tipler (artimli degil).
    # Orn. Wave 12'ye ulasmak progress'i 12 yapar, 12 kez +1 eklemez.
    MAX_VALUE_TYPES = frozenset({"max_combo", "reach_wave", "reach_level"})

    # --- GOREV TIPI KAYIT DEFTERI (G1) ---
    # Bir tip YALNIZCA gercekten tetiklendigi zaman bu kumeye girer; havuz
    # secimi bu kumeye gore filtrelenir. Boylece oyuncuya tamamlanmasi imkansiz
    # gorev verilmez.
    #
    # YENI TETIKLEME EKLERKEN: ilgili dosyaya track_quest(...) cagrisini ekle
    # ve tipi asagidaki kumeye tasi. Aksi halde gorev havuza girmez.
    SUPPORTED_TYPES = frozenset({
        "kill",               # logic/game_logic.py -> kill_enemy()
        "kill_elite",         # logic/game_logic.py -> kill_enemy()
        "kill_boss",          # logic/game_logic.py -> kill_enemy()
        "kill_while_low",     # logic/game_logic.py -> kill_enemy()
        "earn_gold",          # entities/ground_item.py -> pickup()
        "reach_level",        # entities/player.py -> level_up()        [MAX]
        "collect_rarity",     # entities/ground_item.py -> pickup()
        "collect_unique",     # entities/ground_item.py -> pickup()
        "reach_wave",         # logic/game_logic.py -> next_wave()      [MAX]
        "max_combo",          # logic/game_logic.py -> kill_enemy()     [MAX]
        "spend_gold",         # logic/game_logic.py -> buy_item() /
                              #   manual_reroll_market(), scenes/game_scene.py
                              #   (market yenileme + orb satin alma)
        "pick_cards",         # scenes/game_scene.py -> kart secimi
        "use_artifact",       # entities/player.py -> use_artifact()
        "blood_moon_survive", # logic/game_logic.py -> update()
        "minion_kills",       # logic/game_logic.py -> kill_enemy()
                              #   (enemy.last_hit_by_minion bayragi)
        "dodge_hits",         # entities/player.py -> take_damage()
        "sell_items",         # logic/inventory_manager.py -> sell_item()/mass_sell()
        "evolve",             # entities/player.py -> apply_evolution()
    })

    # Henuz tetiklenmeyen tipler (havuza girmez, DEVIR listesi): yok.

    # Olay tipi -> session_stats anahtari. session_stats yalnizca istatistik
    # amacli tutulur (gorev ilerlemesi active_quests uzerinde islenir).
    EVENT_TO_STAT = {
        "kill": "kills", "kill_elite": "elite_kills", "kill_boss": "boss_kills",
        "reach_wave": "max_wave", "earn_gold": "gold_earned",
        "spend_gold": "gold_spent", "max_combo": "max_combo",
        "use_artifact": "artifacts_used", "pick_cards": "cards_picked",
        "minion_kills": "minion_kills", "reach_level": "max_level",
        "kill_while_low": "low_hp_kills", "dodge_hits": "dodges",
        "sell_items": "items_sold", "blood_moon_survive": "blood_moon_survived",
        "evolve": "evolved", "collect_rarity": "rare_items",
        "collect_unique": "unique_items",
    }

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

    # ------------------------------------------------------------------
    # HAVUZ
    # ------------------------------------------------------------------
    @classmethod
    def get_available_pool(cls):
        """Yalnizca gercekten takip edilen tiplerden olusan gorev havuzu."""
        pool = [q for q in cls.QUEST_POOL if q.get("type") in cls.SUPPORTED_TYPES]
        # Guvenlik agi: filtre havuzu 3'un altina dusurduyse ham havuza don
        # (oyuncu gorevsiz kalmasin).
        return pool if len(pool) >= cls.DAILY_COUNT else list(cls.QUEST_POOL)

    def _pick_daily(self, exclude_ids=()):
        pool = [q for q in self.get_available_pool() if q.get("id") not in exclude_ids]
        return pool

    def load_or_reset(self, meta):
        """Günlük görevleri yükle veya sıfırla."""
        today = date.today().isoformat()
        if meta.get("last_quest_date") != today:
            # Yeni gün: takip edilen tiplerden 3 rastgele görev seç
            pool = self.get_available_pool()
            chosen = random.sample(pool, min(self.DAILY_COUNT, len(pool)))
            self.active_quests = [
                {**q, "progress": 0, "completed": False} for q in chosen
            ]
            meta["last_quest_date"] = today
            meta["daily_quests"] = self.active_quests
        else:
            loaded = meta.get("daily_quests", []) or []
            # Eski kayitlardan gelen (artik) desteklenmeyen gorevleri at:
            # oyuncunun gunu imkansiz gorevle dolmasin (G1)
            self.active_quests = [
                q for q in loaded if q.get("type") in self.SUPPORTED_TYPES
            ]
            for q in self.active_quests:
                q.setdefault("progress", 0)
                q.setdefault("completed", False)

            # Eksik kalan slotlari ayni gun icinde tamamla
            if len(self.active_quests) < self.DAILY_COUNT:
                have = {q.get("id") for q in self.active_quests}
                extra_pool = self._pick_daily(exclude_ids=have)
                need = self.DAILY_COUNT - len(self.active_quests)
                for q in random.sample(extra_pool, min(need, len(extra_pool))):
                    self.active_quests.append({**q, "progress": 0, "completed": False})
            meta["daily_quests"] = self.active_quests
        return meta

    # ------------------------------------------------------------------
    # TAKIP
    # ------------------------------------------------------------------
    def track(self, event_type, value=1, meta=None):
        """Olay tetiklendiğinde görev ilerlemesini güncelle.

        Donen deger: bu cagri ile kazanilan kristal miktari.
        """
        # Oturum istatistigi (HUD/ozet icin)
        stat_key = self.EVENT_TO_STAT.get(event_type)
        if stat_key:
            if event_type in self.MAX_VALUE_TYPES:
                self.session_stats[stat_key] = max(self.session_stats.get(stat_key, 0), value)
            else:
                self.session_stats[stat_key] = self.session_stats.get(stat_key, 0) + value

        earned = 0
        for q in self.active_quests:
            if q.get("completed"):
                continue
            if q.get("type") != event_type:
                continue
            progress = q.get("progress", 0)
            if event_type in self.MAX_VALUE_TYPES:
                q["progress"] = max(progress, value)
            else:
                q["progress"] = progress + value
            if q["progress"] >= q.get("target", 1):
                q["progress"] = q.get("target", 1)
                q["completed"] = True
                earned += q.get("reward", 0)
        return earned  # Kazanılan kristal miktarı

    def get_display_quests(self):
        return self.active_quests

    def save_to_meta(self, meta):
        meta["daily_quests"] = self.active_quests
        return meta


# --- Veri dogrulamasi (acilista bir kez) ---
_unknown = sorted({q.get("type") for q in QuestSystem.QUEST_POOL} - QuestSystem.SUPPORTED_TYPES)
if _unknown:
    # Hata degil bilgi: bu tipler henuz tetiklenmedigi icin havuza girmiyor.
    print(f"[quest_system] Takip edilmeyen gorev tipleri havuz disi: {', '.join(_unknown)}")
