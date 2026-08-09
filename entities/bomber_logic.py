import math
import pygame
import random
import vfx


class Bomber:
    """
    Bombacı (Bomber) - Tuzakçı / patlayıcı uzmanı.

    KİMLİK (Simyacı'dan ayrım):
      Bombacı fırlattığı bombayı PATLATMAZ; yere tetiklemeli bir MAYIN bırakır.
      Mayın düşman yaklaşana kadar bekler, sonra tek seferlik büyük fiziksel
      patlama verir ve komşu mayınları zincirleme tetikler. Zehir/DoT yoktur.
      Oyun hissi: pozisyon kur, düşmanı tuzağa çek, zinciri patlat.

      Simyacı ise şişeyi anında patlatıp geride KALICI ZEHİR BULUTU bırakır —
      birikimli, sürekli hasar. İkisi aynı bomba yolunu kullanır ama patlama
      sonrası davranışları Projectile.becomes_mine / cloud_duration_mult ile
      ayrışır.
    """

    AOE_MULT = 1.5          # Mayın yarıçapı çarpanı
    MINE_DMG_MULT = 1.9     # Mayın beklediği için vuruş başına hasarı yüksektir
    MAX_MINES = 8           # Aynı anda yerde durabilecek mayın sayısı

    def __init__(self):
        self.attack_cooldown = 1500

    def execute_attack(self, player, game):
        weapon = player.inv_manager.equipped.get("weapon")

        # Yakın dövüş silahı veya silahsız: temel savurma/yumruk
        if not weapon or weapon.get("isMelee"):
            self.execute_melee(player, game, is_punch=(weapon is None))
            return

        # Menzilli (arbalet/asa) silahlar bomba mantığına girmez
        is_bomb = (weapon.get("isBomb", False)
                   or "şişe" in weapon.get("name", "").lower()
                   or "bomba" in weapon.get("name", "").lower())
        if not is_bomb:
            player.shoot(game)
            return

        # Yerdeki mayın sayısı tavandaysa en eskisini patlat: oyuncu mayın
        # döşemeye devam edebilsin ama harita sınırsız dolmasın.
        self._enforce_mine_cap(player, game)

        # Bombacı: normal atıştan daha büyük alan, ama patlama yerine mayın.
        orig_aoe = player.stats.get("aoe", 1.0)
        player.stats["aoe"] = orig_aoe * self.AOE_MULT
        before = len(game.projectiles)
        try:
            player.shoot(game, is_bomb=True)
        finally:
            player.stats["aoe"] = orig_aoe

        # shoot() mermileri kendi içinde üretip listeye ekler; yeni eklenenleri
        # mayına çeviriyoruz (çoklu atış varsa hepsi mayın olur).
        mine_dmg_mult = self.MINE_DMG_MULT
        radius_mult = 1.0
        if (getattr(player, "evolution_passive", "") == "mine_master"):
            # 🧨 Mayın Uzmanı evrimi: daha geniş ve daha sert mayınlar
            mine_dmg_mult *= 1.35
            radius_mult = 1.4
        for p in game.projectiles[before:]:
            p.becomes_mine = True
            p.mine_dmg_mult = mine_dmg_mult
            p.mine_radius_mult = radius_mult
            # Mayın anlık fiziksel patlama verir; zehir DoT'u Simyacı'ya ait.
            p.poison_dps = 0

    def _enforce_mine_cap(self, player, game):
        mines = [c for c in getattr(game, 'clouds', [])
                 if getattr(c, 'is_mine', False) and not c.dead]
        cap = self.MAX_MINES + (4 if (getattr(player, "evolution_passive", "") == "mine_master") else 0)
        if len(mines) >= cap:
            mines[0].detonate(game)

    def execute_melee(self, player, game, is_punch=False):
        """Silah yoksa/melee silahtayken kısa menzilli patlayıcı savurma."""
        angle = player.facing_angle
        dmg_base = 22 if not is_punch else 5
        phys_flat = player.stats.get("physDmgFlat", 0)
        dmg = ((dmg_base + phys_flat)
               * player.stats.get("dmgMult", 1.0)
               * player.get_conditional_dmg_mult())

        range_val = 110 * player.stats.get("aoe", 1.0)
        game.add_event("explosion", player.x + math.cos(angle) * 40,
                       player.y + math.sin(angle) * 40,
                       radius=int(range_val * 0.6), color=(255, 140, 40), timer=0.15)

        for e in game.iter_enemies_near(player.x, player.y, range_val):
            dx, dy = e.x - player.x, e.y - player.y
            if not e.dead and not getattr(e, 'is_trap', False) and dx * dx + dy * dy < range_val * range_val:
                e.take_damage(dmg, game, from_player=True)
                vfx.hit(game, e.x, e.y, 'fire')
                if random.random() < 0.25:
                    e.apply_dot('fire', 8 * player.stats.get("dmgMult", 1.0), 2.0)

    def update(self, dt, player, game):
        pass

    def draw_visuals(self, screen, camera_x, camera_y):
        pass
