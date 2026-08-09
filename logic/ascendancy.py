"""Ascendancy (alt-sınıf) mini ağaç motoru — PoE ascendancy'sine benzer.

Seviye 20'de seçilen evrim (bkz. Player.EVOLUTIONS) o alt-sınıfın küçük
ağacını AÇAR. Ana ağaçtan AYRI bir para birimiyle işlenir:
`player.ascendancy_points` (seviye 20'den itibaren seviye başına +1).

Motor durumsuzdur (SkillTree gibi); oyuncuya ait tek durum
`player.ascendancy_nodes` kümesidir. Yalnızca oyuncunun SEÇTİĞİ alt-sınıfın
(player.evolution) düğümleri alınabilir.
"""

from logic.data_loader import load_data

_VALID_TYPES = {"minor", "notable", "keystone", "start"}


def _build_index(nodes):
    by_id = {}
    for n in nodes:
        nid = n["id"]
        if nid in by_id:
            raise ValueError(f"ascendancy.json: yinelenen id: {nid}")
        by_id[nid] = n
    adj = {nid: set() for nid in by_id}
    for n in nodes:
        for target in n.get("connects", []):
            if target not in by_id:
                raise ValueError(f"ascendancy.json: '{n['id']}' tanimsiz dugume baglaniyor: {target}")
            adj[n["id"]].add(target)
            adj[target].add(n["id"])
    return by_id, adj


class Ascendancy:
    NODES = load_data('ascendancy')
    BY_ID, ADJ = _build_index(NODES)

    # evrim_id (alt-sınıf) -> başlangıç düğüm id'si
    START_BY_SUBCLASS = {
        n["subclass"]: n["id"]
        for n in NODES
        if n.get("type") == "start" or n.get("start")
    }

    # ------------------------------------------------------------------
    @classmethod
    def start_for(cls, evo_id):
        return cls.START_BY_SUBCLASS.get(evo_id)

    @classmethod
    def nodes_for(cls, evo_id):
        """Bir alt-sınıfın TÜM düğümleri (UI için)."""
        return [n for n in cls.NODES if n["subclass"] == evo_id]

    @classmethod
    def is_start(cls, node_id):
        node = cls.BY_ID.get(node_id)
        return bool(node and (node.get("type") == "start" or node.get("start")))

    @classmethod
    def is_unlocked(cls, player):
        """Alt-sınıf ağacı açık mı? (Seviye 20'de evrim seçilmişse.)"""
        return bool(getattr(player, "evolution", "")) and \
            getattr(player, "evolution", "") in cls.START_BY_SUBCLASS

    # ------------------------------------------------------------------
    @classmethod
    def is_allocatable(cls, node_id, allocated):
        """Yollama kuralı: alınmamış + alınmış bir komşuya bitişik.
        Başlangıç düğümü bedava kök DEĞİLDİR (evrimle tohumlanır)."""
        if node_id not in cls.BY_ID or node_id in allocated:
            return False
        return any(neigh in allocated for neigh in cls.ADJ.get(node_id, ()))

    @classmethod
    def allocatable_nodes(cls, allocated):
        return [nid for nid in cls.BY_ID if cls.is_allocatable(nid, allocated)]

    # ------------------------------------------------------------------
    @classmethod
    def allocate(cls, player, node_id):
        node = cls.BY_ID.get(node_id)
        if not node:
            return False, "Düğüm bulunamadı."
        if node["subclass"] != getattr(player, "evolution", ""):
            return False, "Bu alt-sınıf düğümü değil."
        allocated = cls._ensure_set(player)
        if node_id in allocated:
            return False, "Zaten alınmış."
        if not cls.is_allocatable(node_id, allocated):
            return False, "Önce bağlı bir düğüm al."
        if getattr(player, "ascendancy_points", 0) < 1:
            return False, "Yükseliş Puanı yok! (Seviye 20+ ile kazanılır)"
        allocated.add(node_id)
        player.ascendancy_points -= 1
        cls._sync_player(player)
        return True, node["name"]

    @classmethod
    def seed_start(cls, player):
        """Evrim seçilince alt-sınıf başlangıcını tohumla (ağacı açar)."""
        evo = getattr(player, "evolution", "")
        start = cls.start_for(evo)
        if start:
            cls._ensure_set(player).add(start)
            cls._sync_player(player)

    @classmethod
    def refund_all(cls, player):
        """Başlangıç dışı düğümleri iade eder; puan geri verir."""
        allocated = cls._ensure_set(player)
        refunded = sum(1 for nid in allocated if not cls.is_start(nid))
        start = cls.start_for(getattr(player, "evolution", ""))
        player.ascendancy_nodes = {start} if start else set()
        player.ascendancy_points = getattr(player, "ascendancy_points", 0) + refunded
        cls._sync_player(player)
        return refunded

    # ------------------------------------------------------------------
    @classmethod
    def resolve_stats(cls, allocated):
        totals = {}
        for nid in allocated:
            node = cls.BY_ID.get(nid)
            if not node:
                continue
            for stat, val in node.get("stats", {}).items():
                totals[stat] = totals.get(stat, 0) + val
        return totals

    @classmethod
    def apply_flags(cls, player, allocated):
        for nid in allocated:
            node = cls.BY_ID.get(nid)
            if not node:
                continue
            for attr, val in node.get("flags", {}).items():
                setattr(player, attr, val)

    # ------------------------------------------------------------------
    @staticmethod
    def _ensure_set(player):
        alloc = getattr(player, "ascendancy_nodes", None)
        if not isinstance(alloc, set):
            alloc = set(alloc) if alloc else set()
            player.ascendancy_nodes = alloc
        return alloc

    @classmethod
    def _sync_player(cls, player):
        inv = getattr(player, "inv_manager", None)
        if inv is not None:
            cls.apply_flags(player, player.ascendancy_nodes)
            inv.recalculate_stats()
            if hasattr(player, "hp") and hasattr(player, "max_hp"):
                player.hp = min(player.hp, player.max_hp)


# --- Veri dogrulamasi (acilista bir kez) ---
def _validate():
    starts = {}
    for n in Ascendancy.NODES:
        if n.get("type") not in _VALID_TYPES:
            raise ValueError(f"ascendancy.json: '{n['id']}' gecersiz type: {n.get('type')}")
        if "subclass" not in n:
            raise ValueError(f"ascendancy.json: '{n['id']}' subclass eksik")
        if n.get("type") == "start" or n.get("start"):
            starts.setdefault(n["subclass"], []).append(n["id"])
    for sub, ids in starts.items():
        if len(ids) != 1:
            raise ValueError(f"ascendancy.json: '{sub}' alt-sınıfında tam 1 baslangic olmali: {ids}")


_validate()
