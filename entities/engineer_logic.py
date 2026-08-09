import math
import pygame
import vfx
import audio

class Engineer:
    """
    Mühendis (Engineer) - Taret odaklı savunma sınıfı.
    - +1 taret limiti (toplam 2) ve +10 zırh ile başlar.
    - 5 saniyede bir taret kurabilir; taret hasarı sahibinin silah gücüyle
      (physDmg) ve turretDmg/turretRate statlarıyla ölçeklenir.
    - Taretler düşman saldırısını üstüne çeker (aggro emer).
    """
    # --- ALEV SİLAHI (Flamethrower) ---
    # Diğer arketiplerden farkı: mermi üretmez, her saldırıda ÖNÜNDEKİ KONİYİ
    # tarar. Atış aralığı çok kısa olduğu için sürekli bir akış hissi verir;
    # tek vuruş hasarı düşük, asıl hasar yanma (burn) yığılmasından gelir.
    FLAME_ARC = 0.62            # ~35 derece koni
    FLAME_BASE_RANGE = 210      # taban menzil (silah 'range' ile artırır)

    def execute_flamethrower(self, player, game, weapon):
        angle = player.facing_angle
        local = player.inv_manager.get_item_local_stats("weapon") or {}

        rng = (self.FLAME_BASE_RANGE + local.get("range", 0)) * \
              player.stats.get("meleeRangeMult", 1.0)
        arc = self.FLAME_ARC

        fire_mult, _frost_mult, elem_mult = player.get_elemental_mults()
        dmg_mult = player.stats.get("dmgMult", 1.0) * player.get_conditional_dmg_mult()
        # Alev hasarı ateş statlarından okunur; fiziksel taban yok.
        base_fire = (player.stats.get("fireDamage", 0)
                     + player.stats.get("fireDmgFlat", 0))
        tick_dmg = base_fire * dmg_mult * fire_mult
        burn_dps = tick_dmg * 0.9

        audio.play('flame')
        vfx.flamethrower(game, player.x, player.y, angle, rng, arc)

        hit_any = False
        for e in game.iter_enemies_near(player.x, player.y, rng + 80):
            if e.dead or getattr(e, 'is_trap', False):
                continue
            dx, dy = e.x - player.x, e.y - player.y
            hit_range = rng + e.radius
            if dx * dx + dy * dy > hit_range * hit_range:
                continue
            angle_to_e = math.atan2(dy, dx)
            diff = abs(((angle_to_e - angle) + math.pi) % (2 * math.pi) - math.pi)
            # Yakında koni genişler: dipte dar olması silahı kullanılmaz yapıyor
            dist = math.hypot(dx, dy)
            eff_arc = arc + (0.9 if dist < 70 else 0.0)
            if diff > eff_arc / 2:
                continue
            if tick_dmg > 0:
                e.take_damage(tick_dmg, game, from_player=True)
            # Yanma yığılır: alevin içinde kalmak cezalandırır
            e.apply_dot('fire', burn_dps, 2.0)
            hit_any = True

        return hit_any

    def execute_attack(self, player, game):
        weapon = player.inv_manager.equipped.get("weapon")

        # Alev silahı: koni taraması (mermi üretmez)
        if weapon and weapon.get("isFlamethrower"):
            self.execute_flamethrower(player, game, weapon)
            return

        # Menzilli / Bomba Kontrolü
        if weapon and (weapon.get("isRanged") or weapon.get("isBomb")):
            player.shoot(game)
            return

        # Taret artık saldırıya bağlı DEĞİL: R tuşuyla kullanılan bir yetenek
        # (bkz. player.try_place_turret / game_scene R tuşu). Eskiden taret kiti
        # takılıyken execute_attack koşulsuz return ediyordu, yani Mühendis
        # bekleme süresi boyunca hiçbir hasar veremiyordu.
        # Taret kiti bir EKİPMAN: taretleri güçlendirir, silah gibi vurmaz.
        # Ama saldırıyı ÖLDÜRMEMELİ — koşulsuz return ediyordu ve kiti
        # kuşanan oyuncu hiç hasar veremiyordu, yani kit bir TUZAK eşyaydı.
        # Artık zayıf yumrukla dövüşür: güçlü taret / zayıf şahsi hasar
        # dengesi kurulur.
        is_turret_kit = bool(weapon and weapon.get("isTurret"))

        # Yakın Dövüş Modu (Silah varsa Keser, yoksa Yumruk)
        angle = player.facing_angle
        is_punch = (weapon is None) or is_turret_kit
        dmg = 25 * player.stats["dmgMult"] * player.get_conditional_dmg_mult() if not is_punch else 5
        
        audio.play('melee')
        
        game.add_event("slash", player.x, player.y, angle=angle, range=90, arc=1.0, timer=0.1)
        
        for e in game.iter_enemies_near(player.x, player.y, 110):
            dx, dy = e.x - player.x, e.y - player.y
            if not e.dead and dx * dx + dy * dy < 110 * 110:
                e.take_damage(dmg, game, from_player=True)
                vfx.hit(game, e.x, e.y, 'phys')
        
    def update(self, dt, player, game):
        pass
        
    def draw_visuals(self, screen, camera_x, camera_y):
        pass
        
