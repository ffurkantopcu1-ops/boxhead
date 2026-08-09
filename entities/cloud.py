import colorsys
import math
import os
import random

import pygame

import vfx
import audio

# --- BULUT GÖRSELİ ---
# Tek bir yeşil zehir sprite'ı üretildi; diğer tipler (ateş/buz/ağ/kara delik/
# mayın) ondan hue kaydırılarak türetiliyor. Böylece bütün bulutlar aynı doku
# ve kenar yumuşaklığını paylaşıyor.
_SPRITE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "vfx", "cloud_poison.png",
)
_BASE_SPRITE = None
_BASE_MISSING = False
_TINTED = {}    # hedef hue -> renklendirilmiş kaynak
_SCALED = {}    # (hue, çap) -> ölçeklenmiş yüzey


def _base_sprite():
    """Kaynak sprite (bir kez yüklenir). Dosya yoksa None -> daire çizimine düşülür."""
    global _BASE_SPRITE, _BASE_MISSING
    if _BASE_SPRITE is None and not _BASE_MISSING:
        try:
            _BASE_SPRITE = pygame.image.load(_SPRITE_PATH).convert_alpha()
        except Exception:
            _BASE_MISSING = True
    return _BASE_SPRITE


_BASE_SAT = 0.85    # kaynak sprite'ın (yeşil) yaklaşık doygunluğu


def _hue_sat_of(color):
    r, g, b = [c / 255.0 for c in color[:3]]
    h, s, _ = colorsys.rgb_to_hsv(r, g, b)
    return h, s


def _cloud_surface(color, diameter):
    """İstenen renkte ve çapta bulut yüzeyi (cache'li). Yoksa None."""
    base = _base_sprite()
    if base is None:
        return None
    hue, sat = _hue_sat_of(color)
    # Doygunluğu da taşımak şart: ağ bulutunun rengi gri (180,180,180), yani
    # doygunluğu 0. Sadece hue kaydırılsaydı gri bir hedef kırmızıya dönerdi.
    sat_scale = min(1.2, sat / _BASE_SAT)
    key = (round(hue, 3), round(sat_scale, 2), diameter)
    cached = _SCALED.get(key)
    if cached is not None:
        return cached

    tint_key = (round(hue, 3), round(sat_scale, 2))
    tinted = _TINTED.get(tint_key)
    if tinted is None:
        tinted = base.copy()
        w, h = tinted.get_size()
        for y in range(h):
            for x in range(w):
                r, g, b, a = tinted.get_at((x, y))
                if a == 0:
                    continue
                _, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
                nr, ng, nb = colorsys.hsv_to_rgb(hue, min(1.0, s * sat_scale), v)
                tinted.set_at((x, y), (int(nr * 255), int(ng * 255), int(nb * 255), a))
        _TINTED[tint_key] = tinted

    # smoothscale DEĞİL: bulut sprite'ı oyun boyutuna büyütülürken bilinear
    # filtre pikselleri eritip airbrush görünümü veriyordu. Nearest, setin
    # geri kalanıyla aynı keskin pixel-art dilini korur.
    scaled = pygame.transform.scale(tinted, (diameter, diameter))
    if len(_SCALED) > 240:      # sınırsız büyümesin
        _SCALED.clear()
    _SCALED[key] = scaled
    return scaled


class Cloud:
    def __init__(self, id, x, y, radius, duration, poison_dps=0, fire_dmg=0, frost_dmg=0, is_black_hole=False, is_web=False, is_mine=False, mine_dmg=0):
        self.id = id
        self.x = x
        self.y = y
        self.radius = radius
        self.duration = duration
        self.poison_dps = poison_dps
        self.fire_dmg = fire_dmg
        self.frost_dmg = frost_dmg
        self.dead = False
        
        self.is_black_hole = is_black_hole
        self.is_web = is_web
        self.is_mine = is_mine
        self.mine_dmg = mine_dmg
        # Mayın yerleştirildikten sonra kısa bir kurma süresi bekler.
        self.arm_timer = 0.35 if is_mine else 0.0

        # DoT uygulama sayacı: bulut her KAREDE apply_dot çağırdığı için zehir
        # yığını 0.067 sn'de tavana ulaşıyor, süre de sürekli yenileniyordu.
        # Artık saniyede iki kez tick atar (F5).
        self.dot_interval = 0.5
        self.dot_timer = 0.0
        
        # Mixed color based on strength
        # Zehir (Yeşil), Ateş (Kırmızı), Buz (Mavi), Kara Delik (Koyu Mor), Ağ (Gri), Mayın (Kırmızı/Turuncu)
        if self.is_mine: self.color = (255, 80, 0)
        elif self.is_web: self.color = (180, 180, 180)
        elif self.is_black_hole: self.color = (44, 62, 80)
        elif fire_dmg > poison_dps and fire_dmg > frost_dmg: self.color = (231, 76, 60)
        elif frost_dmg > fire_dmg and frost_dmg > poison_dps: self.color = (52, 152, 219)
        else: self.color = (46, 204, 113)

        diameter = max(2, int(self.radius * 2))
        self._visual = None
        if not self.is_mine:
            # Üretilen bulut sprite'ı (yoksa aşağıdaki daire çizimine düşer)
            self._visual = _cloud_surface(self.color, diameter)
        if self._visual is not None:
            return

        self._visual = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        if self.is_mine:
            # Mayın için ortasında belirgin bir çekirdek
            pygame.draw.circle(self._visual, (*self.color, 150), (diameter // 2, diameter // 2), 10)
            pygame.draw.circle(self._visual, (*self.color, 50), (diameter // 2, diameter // 2), int(self.radius), 2)
        else:
            pygame.draw.circle(
                self._visual, (*self.color, 100),
                (diameter // 2, diameter // 2), int(self.radius),
            )
            pygame.draw.circle(
                self._visual, (*self.color, 50),
                (diameter // 2, diameter // 2), int(self.radius), 10,
            )
            
    def detonate(self, game, _chain_depth=0):
        """Mayını patlat. Yakındaki diğer mayınları da zincirleme tetikler."""
        if self.dead:
            return
        self.dead = True
        audio.play('explosion')
        game.add_event("explosion", self.x, self.y, radius=self.radius,
                       color=(255, 80, 0), timer=0.3)
        for me in game.iter_enemies_near(self.x, self.y, self.radius):
            if not me.dead and not getattr(me, 'is_trap', False):
                mdx, mdy = me.x - self.x, me.y - self.y
                if mdx * mdx + mdy * mdy < self.radius * self.radius:
                    me.take_damage(self.mine_dmg, game, from_player=True)

        # Zincirleme: komşu mayınlar da patlar. Derinlik sınırı, uzun mayın
        # zincirlerinde özyinelemenin yığını taşırmasını engeller.
        if _chain_depth >= 4:
            return
        chain_r = self.radius * 1.5
        for c in list(getattr(game, 'clouds', [])):
            if c is self or c.dead or not getattr(c, 'is_mine', False):
                continue
            cdx, cdy = c.x - self.x, c.y - self.y
            if cdx * cdx + cdy * cdy < chain_r * chain_r:
                c.detonate(game, _chain_depth + 1)

    def update(self, dt, game):
        self.duration -= dt
        if self.duration <= 0:
            self.dead = True
            return

        if self.arm_timer > 0:
            self.arm_timer -= dt
            
        # DoT tick'i (F5): yığın eklemesi ve süre yenilemesi her karede değil,
        # dot_interval'da bir yapılır. Mayın tetiklemesi her karede kontrol
        # edilmeye devam eder.
        self.dot_timer -= dt
        apply_dot_now = self.dot_timer <= 0
        if apply_dot_now:
            self.dot_timer = self.dot_interval

        # Düşmanlara DOT veya Mayın patlaması uygula
        for e in game.iter_enemies_near(self.x, self.y, self.radius):
            if not e.dead and getattr(e, 'is_trap', False) == False:
                dx = e.x - self.x
                dy = e.y - self.y
                if dx * dx + dy * dy < self.radius * self.radius:
                    if self.is_mine:
                        # Mayın Patlaması. Kurma gecikmesi dolmadan tetiklenmez;
                        # yoksa oyuncunun ayağının dibindeki düşman mayını
                        # yerleştirildiği karede patlatırdı.
                        if self.arm_timer > 0:
                            continue
                        self.detonate(game)
                        return
                    
                    if not apply_dot_now:
                        continue

                    # 1. Zehir Etkisi
                    if self.poison_dps > 0:
                        e.apply_dot('poison', self.poison_dps, 1.5)

                    # 2. Ateş Etkisi
                    if self.fire_dmg > 0:
                        e.apply_dot('fire', self.fire_dmg, 1.5)
                        # Tick başına şans (eskiden kare başınaydı: saniyede ~3
                        # patlama; artık ~0.5)
                        if random.random() < 0.25:
                            game.add_event("explosion", e.x, e.y, radius=40, color=(255, 100, 0), timer=0.15)
                            for other in game.iter_enemies_near(e.x, e.y, 40):
                                if not other.dead and not other.is_trap and other != e:
                                    odx = other.x - e.x
                                    ody = other.y - e.y
                                    if odx * odx + ody * ody < 40 * 40:
                                        other.take_damage(self.fire_dmg * 0.5, game)
                    
                    # 3. Buz Etkisi
                    if self.frost_dmg > 0:
                        e.apply_dot('frost', self.frost_dmg * 0.5, 1.5)

        # Kara Delik Etkisi
        if self.is_black_hole:
            p = game.players[game.local_player_id]
            dist_to_p = math.hypot(p.x - self.x, p.y - self.y)
            if dist_to_p < self.radius:
                # Oyuncuyu merkeze çek
                angle_to_center = math.atan2(self.y - p.y, self.x - p.x)
                pull_strength = 60 * dt
                p.x += math.cos(angle_to_center) * pull_strength
                p.y += math.sin(angle_to_center) * pull_strength
                # Hasar ver
                dmg = getattr(self, 'dmg', 10)
                p.take_damage(dmg * dt, force=True)

        # Ağ Etkisi (Oyuncuyu yavaşlatır ve susturur)
        if getattr(self, 'is_web', False):
            p = game.players[game.local_player_id]
            dist_to_p = math.hypot(p.x - self.x, p.y - self.y)
            if dist_to_p < self.radius:
                # speed_mod'a dogrudan yazmak etkisizdi: StatusEffectManager her
                # karede sifirliyor. Etki artik status sistemi uzerinden (H3)
                from logic.status_effects import apply_slow, apply_silence
                apply_slow(p.effect_manager, duration=0.4, mult=0.3, name="Web")  # %70 yavaşlama
                apply_silence(p.effect_manager, duration=0.4)
                p.silence_timer = 0.5 # Ağa bastığı sürece sürekli yenilenir

        # Oyuncuya Hasar Uygula - DEVRE DIŞI BIRAKILDI (GDD 62)
        # p = game.players[game.local_player_id]
        # if math.hypot(p.x - self.x, p.y - self.y) < self.radius:
        #     if self.fire_dmg > 0:
        #         p.take_damage(self.fire_dmg * dt, force=True)
        #     if self.poison_dps > 0:
        #         p.take_damage(self.poison_dps * dt, force=True)
        #     if self.frost_dmg > 0:
        #         p.take_damage(self.frost_dmg * 0.1 * dt, force=True) # Hafif dondurucu hasar
        #         p.speed_mod = min(p.speed_mod, 0.5) # Yavaşlat

    def draw(self, screen, camera_x, camera_y):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y

        if self.is_mine:
            # Mayın yerde beklerken görünür olmalı: kararan bir is lekesi +
            # nabız gibi atan tetikleme halkası. Kurma süresince halka soluk.
            armed = self.arm_timer <= 0
            scorch = vfx.get_sprite("scorch", (150, 70, 30), self.radius * 2)
            if scorch is not None:
                screen.blit(scorch, (draw_x - self.radius, draw_y - self.radius))
            pulse = 0.55 + 0.45 * math.sin(self.duration * 6.0)
            base = (255, 90, 20) if armed else (140, 120, 90)
            col = tuple(int(c * (0.45 + 0.55 * pulse)) for c in base)
            pygame.draw.circle(screen, col, (int(draw_x), int(draw_y)),
                               int(self.radius), 2)
            pygame.draw.circle(screen, base, (int(draw_x), int(draw_y)),
                               max(2, int(4 * pulse) + 2))
            return

        # Geometri init'te önbelleğe alınır; burada yalnızca solma alfası değişir.
        # NOT: sprite yüzeyi aynı renk/çaptaki bulutlar arasında PAYLAŞILIR.
        # set_alpha hemen ardından blit geldiği ve çizim sıralı olduğu için her
        # bulut kendi alfasıyla basılır; değer kalıcı olarak saklanmaz.
        alpha = min(255, int(255 * (self.duration / 2.0)))
        self._visual.set_alpha(alpha)
        screen.blit(self._visual, (draw_x - self.radius, draw_y - self.radius))
