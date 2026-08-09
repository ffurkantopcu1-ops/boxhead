"""Node-based (Path of Exile'vari) yetenek agaci motoru.

Tasarim ve sozlesme: SKILL_TREE.md. Ozet:
- Yollu (pathing) ve deterministik: bir dugum ancak SINIF BASLANGIC dugumuyse
  ya da sahip oldugun bir dugume komsuysa alinabilir.
- Kosu-kapsamli: tahsis oyuncunun kosu kaydinda yasar (meta.json'da DEGIL).
- Para birimi mevcut `player.skill_points` (seviye basi +1). Her dugum 1 SP;
  baslangic dugumu 0 SP ve kosu basinda otomatik tahsis edilir.

Motor durumsuzdur (CrystalShop gibi): dugum verisi sinif seviyesinde bir kez
kurulur, oyuncuya ait tek durum `player.allocated_nodes` kumesidir.
"""

from logic.data_loader import load_data

# Dugum tipleri (yalnizca dogrulama/UI icin ayrimlar)
_VALID_TYPES = {"minor", "notable", "keystone", "start"}


def _build_index(nodes):
    by_id = {}
    for n in nodes:
        nid = n["id"]
        if nid in by_id:
            raise ValueError(f"skill_tree.json: yinelenen dugum id'si: {nid}")
        by_id[nid] = n

    # Kenarlar yonsuz: connects tek yonde yazilir, simetrik komsuluk kurulur.
    adj = {nid: set() for nid in by_id}
    for n in nodes:
        for target in n.get("connects", []):
            if target not in by_id:
                raise ValueError(
                    f"skill_tree.json: '{n['id']}' tanimsiz dugume baglaniyor: {target}")
            adj[n["id"]].add(target)
            adj[target].add(n["id"])
    return by_id, adj


class SkillTree:
    NODES = load_data('skill_tree')
    BY_ID, ADJ = _build_index(NODES)

    # Sinif -> baslangic dugum id'si (arm != core ve type == start)
    START_BY_CLASS = {
        n["arm"]: n["id"]
        for n in NODES
        if n.get("type") == "start" or n.get("start")
    }

    # Bir sinifin kendi kolu yoksa (tanimsiz/gelecekteki sinif) cekirdek
    # buradan acilir: core_heart bedava tahsis edilir ki paylasilan cekirdek
    # yine de yollanabilsin. Su an tum oynanabilir siniflarin kendi kolu var.
    ARMLESS_FALLBACK = "core_heart"

    # ------------------------------------------------------------------
    # Baslangic / kosu kurulumu
    # ------------------------------------------------------------------
    @classmethod
    def start_nodes_for(cls, class_id):
        """Kosu basinda (ve sinif degisiminde) otomatik tahsis edilen dugumler."""
        start = cls.START_BY_CLASS.get(class_id)
        if start:
            return [start]
        if cls.ARMLESS_FALLBACK in cls.BY_ID:
            return [cls.ARMLESS_FALLBACK]
        return []

    @classmethod
    def is_start(cls, node_id):
        node = cls.BY_ID.get(node_id)
        return bool(node and (node.get("type") == "start" or node.get("start")))

    @classmethod
    def get_cost(cls, node_id):
        """Baslangic dugumleri bedava; digerleri 1 SP."""
        return 0 if cls.is_start(node_id) else 1

    # ------------------------------------------------------------------
    # Yollama (pathing) kurallari
    # ------------------------------------------------------------------
    @classmethod
    def is_allocatable(cls, node_id, allocated):
        """node_id su an alinabilir mi?

        - Zaten alinmissa ya da bilinmeyen id: hayir.
        - Aksi halde: alinmis herhangi bir dugume komsuysa evet.

        Baslangic dugumleri "bedava kok" DEGILDIR; yalnizca oyuncunun KENDI
        sinif baslangici kosu basinda otomatik tohumlanir (start_nodes_for).
        Baska sinifin baslangici ancak cekirdek uzerinden o kolun gecidine
        yuruyup komsu olununca acilir. Boylece bir savasci, tum arayi
        yatirmadan ninja koluna atlayamaz (sinif kimligi korunur)."""
        if node_id not in cls.BY_ID or node_id in allocated:
            return False
        return any(neigh in allocated for neigh in cls.ADJ.get(node_id, ()))

    @classmethod
    def allocatable_nodes(cls, allocated):
        """Su an alinabilir tum dugum id'leri (UI vurgusu icin)."""
        return [nid for nid in cls.BY_ID if cls.is_allocatable(nid, allocated)]

    # ------------------------------------------------------------------
    # Tahsis / iade
    # ------------------------------------------------------------------
    @classmethod
    def allocate(cls, player, node_id):
        """Bir dugum alir. Donen: (basari, mesaj). player'i gunceller."""
        if node_id not in cls.BY_ID:
            return False, "Dugum bulunamadi."
        allocated = cls._ensure_set(player)
        if node_id in allocated:
            return False, "Zaten alinmis."
        if not cls.is_allocatable(node_id, allocated):
            return False, "Once bagli bir dugum al."

        cost = cls.get_cost(node_id)
        if cost > 0 and getattr(player, "skill_points", 0) < cost:
            return False, "Yetersiz Yetenek Puani!"

        allocated.add(node_id)
        if cost:
            player.skill_points -= cost
        cls._sync_player(player)
        return True, cls.BY_ID[node_id]["name"]

    @classmethod
    def refund_all(cls, player):
        """Baslangic disi tum dugumleri iade eder; SP geri verir, kolu yeniden
        tohumlar. Donen: iade edilen dugum sayisi (harcanan SP)."""
        allocated = cls._ensure_set(player)
        refunded = sum(1 for nid in allocated if not cls.is_start(nid))
        player.allocated_nodes = set(cls.start_nodes_for(cls._class_of(player)))
        player.skill_points = getattr(player, "skill_points", 0) + refunded
        cls._sync_player(player)
        return refunded

    @classmethod
    def reseed_start(cls, player):
        """Karakterin sinifina ait baslangic dugumunu ekler, mevcut tahsisleri
        korur. Baska sinifin baslangicini SILMEZ (yol kopmasin)."""
        allocated = cls._ensure_set(player)
        for nid in cls.start_nodes_for(cls._class_of(player)):
            allocated.add(nid)
        cls._sync_player(player)

    # ------------------------------------------------------------------
    # Stat cozumleme (recalculate_stats buradan okur)
    # ------------------------------------------------------------------
    @classmethod
    def resolve_stats(cls, allocated):
        """Alinan dugumlerin `stats` katkilarini toplayip tek sozluk dondurur."""
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
        """Stat olmayan keystone etkilerini oyuncu ozniteligine yazar.

        Kartlarla ayni oznitelikleri kullanir; v1 dugumlerinde flag yok ama
        mekanizma ileri kullanim icin burada. (Cift-tanim onlemek icin bir
        anahtar hem kart hem dugum tarafindan yazilmamali.)
        """
        for nid in allocated:
            node = cls.BY_ID.get(nid)
            if not node:
                continue
            for attr, val in node.get("flags", {}).items():
                setattr(player, attr, val)

    # ------------------------------------------------------------------
    # Dahili yardimcilar
    # ------------------------------------------------------------------
    @staticmethod
    def _class_of(player):
        """Agac kolu, silahla gecici degisen class_id'yi degil karakterin
        SECTIGI sinifi (base_class_id) izler."""
        return getattr(player, "base_class_id", None) or getattr(player, "class_id", "")

    @staticmethod
    def _ensure_set(player):
        alloc = getattr(player, "allocated_nodes", None)
        if not isinstance(alloc, set):
            alloc = set(alloc) if alloc else set()
            player.allocated_nodes = alloc
        return alloc

    @classmethod
    def _sync_player(cls, player):
        """Tahsis degisince statlari yeniden hesapla (motorun tek yan etkisi)."""
        inv = getattr(player, "inv_manager", None)
        if inv is not None:
            cls.apply_flags(player, player.allocated_nodes)
            inv.recalculate_stats()
            if hasattr(player, "hp") and hasattr(player, "max_hp"):
                player.hp = min(player.hp, player.max_hp)


# --- Veri dogrulamasi (acilista bir kez) ---
def _validate():
    starts_by_arm = {}
    for n in SkillTree.NODES:
        ntype = n.get("type")
        if ntype not in _VALID_TYPES:
            raise ValueError(f"skill_tree.json: '{n['id']}' gecersiz type: {ntype}")
        if "arm" not in n:
            raise ValueError(f"skill_tree.json: '{n['id']}' arm alani eksik")
        if ntype == "start" or n.get("start"):
            arm = n["arm"]
            starts_by_arm.setdefault(arm, []).append(n["id"])
            # Baslangic bir cekirdek dugumune baglanmali (kola giris + core gecidi)
            reaches_core = any(
                SkillTree.BY_ID[t]["arm"] == "core"
                for t in SkillTree.ADJ[n["id"]]
                if t in SkillTree.BY_ID
            )
            if not reaches_core:
                raise ValueError(
                    f"skill_tree.json: baslangic '{n['id']}' hicbir cekirdek gecidine baglanmiyor")

    for arm, ids in starts_by_arm.items():
        if len(ids) != 1:
            raise ValueError(
                f"skill_tree.json: '{arm}' kolunda tam olarak 1 baslangic olmali, {len(ids)} bulundu: {ids}")


_validate()
