import pygame
import math
import time
import random

import vfx

# Bombacı mayınının yerde bekleme süresi (saniye). Tetiklenmezse söner —
# aksi halde oyuncu haritayı sınırsız mayınla doldurup performansı düşürür.
MINE_LIFETIME = 12.0


class Projectile:
    def __init__(self, id, x, y, vx, vy, dmg, bounce=0, pierce=0, p_type='normal', aoe=0, lifetime=180, is_hostile=False, is_crit=False, is_returning=False, bounce_dmg_mult=1.0, throw_range=0):
        self.id = id
        self.x = x
        self.y = y
        # Fırlatılan şişe: mermi gibi düşmana çarpınca değil, belirlenen
        # menzilin sonunda yere değince patlar. Havada olduğu sürece
        # düşmanlarla çarpışmaz (üzerlerinden geçer).
        self.throw_range = throw_range
        self.start_x = x
        self.start_y = y
        self.airborne = throw_range > 0
        self.vx = vx
        self.vy = vy
        self.dmg = dmg
        self.radius = 6
        self.lifetime = lifetime
        self.initial_lifetime = lifetime
        self.dead = False
        self.type = p_type # 'normal', 'bomb', 'fire', 'frost', 'poison'
        self.aoe = aoe
        self.is_hostile = is_hostile
        self.is_crit = is_crit
        self.is_returning = is_returning
        self.has_returned = False
        
        # New: Elemental Components
        self.poison_dps = 0
        self.fire_dmg = 0
        self.frost_dmg = 0

        # --- SINIF KİMLİĞİ: MAYIN vs BULUT ---
        # Bombacı ile Simyacı aynı bomba yolunu kullanıyor ama patlama sonrası
        # davranışları burada ayrışır. Varsayılanlar hiçbir şeyi değiştirmez.
        #   becomes_mine        : patlamak yerine yere tetiklemeli mayın bırakır (Bombacı)
        #   cloud_duration_mult : geride kalan bulutun süresi (Simyacı uzatır)
        #   mine_dmg_mult       : mayın patlama hasarı çarpanı
        #   mine_radius_mult    : mayın tetikleme/patlama yarıçapı çarpanı
        self.becomes_mine = False
        self.cloud_duration_mult = 1.0
        self.mine_dmg_mult = 1.0
        self.mine_radius_mult = 1.0
        
        # Renk Belirleme
        if p_type == 'bomb':
            self.color = (46, 204, 113) # Yeşil
        elif p_type == 'fire':
            self.color = (231, 76, 60) # Kırmızı
        elif p_type == 'frost':
            self.color = (52, 152, 219) # Mavi
        elif p_type == 'katana':
            self.color = (255, 255, 255) # Beyaz Parlama
            self.radius = 12 # Biraz daha geniş vuruş alanı
        else:
            self.color = (255, 255, 100) # Standart Sarı
            
        self.bounce = bounce
        self.pierce = pierce
        self.bounce_dmg_mult = bounce_dmg_mult
        self.hit_history = []
        self.is_katana = (p_type == 'katana')
        # Çılgın Simyacı (mad_bomber) ikinci patlama bayrağı. Projectile
        # havuzlanmıyor (projectile_pool.py yalnızca BossProjectile'ı havuzlar),
        # yine de her mermide açıkça sıfırlanır.
        self._second_blast = False
        
    def update(self, dt, game):
        # Bumerang Geri Dönme Mantığı
        if self.is_returning and not self.has_returned and self.lifetime <= self.initial_lifetime / 2:
            self.has_returned = True
            if not self.is_hostile:
                p = game.players[game.local_player_id]
                angle = math.atan2(p.y - self.y, p.x - self.x)
                speed = math.hypot(self.vx, self.vy)
                self.vx = math.cos(angle) * speed
                self.vy = math.sin(angle) * speed
            else:
                self.vx *= -1
                self.vy *= -1
            self.hit_history.clear() # Dönerken aynı hedeflere tekrar vurabilmesi için sıfırla

        if self.is_returning and self.has_returned and not self.is_hostile:
            p = game.players[game.local_player_id]
            dist = math.hypot(p.x - self.x, p.y - self.y)
            if dist < getattr(p, "radius", 15) + 15:
                self.dead = True
                return

        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.lifetime -= dt * 60
        
        # Sınır Kontrolü (Memory Leak Önlemi)
        if self.x < -100 or self.x > 5100 or self.y < -100 or self.y > 5100:
            self.dead = True
            return
        
        # Menzil sonunda yere iniş: bulut tam düştüğü yerde oluşur
        if self.airborne:
            dx = self.x - self.start_x
            dy = self.y - self.start_y
            if dx * dx + dy * dy >= self.throw_range * self.throw_range:
                self.land(game)
                return

        if self.lifetime <= 0:
            if self.type == 'bomb':
                self.explode(game)
            self.dead = True
            
        # --- BLACK HOLE LOGIC ---
        if self.type == 'black_hole':
            for e in game.iter_enemies_near(self.x, self.y, self.aoe):
                if not e.dead and not e.is_trap:
                    dx = e.x - self.x
                    dy = e.y - self.y
                    dist_sq = dx * dx + dy * dy
                    if dist_sq < self.aoe * self.aoe:
                        dist = math.sqrt(dist_sq)
                        # Çekim kuvveti (Merkeze doğru)
                        angle = math.atan2(self.y - e.y, self.x - e.x)
                        pull = (1.0 - (dist / self.aoe)) * 5 # Merkeze yaklaştıkça çekim artar
                        e.x += math.cos(angle) * dt * 60 * pull
                        e.y += math.sin(angle) * dt * 60 * pull
                        # Zamanla Hasar (Text spamini engellemek için %5 şansla görsel göster)
                        e.take_damage(self.dmg * dt * 3, game, is_dot=True, from_player=not self.is_hostile)
                        if random.random() < 0.05:
                            game.add_event("damage_text", e.x, e.y - 10, value=int(self.dmg), color=(142, 68, 173), timer=0.3, scale=0.7)
            
            # Görsel Pulsasyon
            if int(time.time() * 10) % 5 == 0:
                game.add_event("explosion", self.x, self.y, radius=self.aoe/2, color=(142, 68, 173), timer=0.1)

        # Havada olan dost şişe hiçbir şeyle çarpışmaz: hedefi düşman değil,
        # yere ineceği nokta. Bu dal ayrı tutulmalı — sadece koşula
        # "not self.airborne" eklemek şişeyi aşağıdaki `else` dalına düşürüyor
        # ve o dal DÜŞMAN mermisi dalı, yani oyuncuya hasar veriyordu (şişe
        # namludan 20px'te doğduğu için her atışta kendini vuruyordu).
        if self.airborne and not self.is_hostile:
            pass
        elif not self.is_hostile:
            # --- MANYETİK ALAN SAPTIRMASI (Magnetar) ---
            for e in game.iter_enemies_near(self.x, self.y, 400):
                if not e.dead and e.type == "magnetar":
                    dx = e.x - self.x
                    dy = e.y - self.y
                    if dx * dx + dy * dy < e.magnet_radius * e.magnet_radius:
                        if random.random() < 0.30 * dt * 60:  # dt normalize
                            self.vx += random.uniform(-4, 4)
                            self.vy += random.uniform(-4, 4)
                            break

            for e in game.iter_enemies_near(self.x, self.y, 160):
                if not e.dead and e.id not in self.hit_history:
                    dx = e.x - self.x
                    dy = e.y - self.y
                    hit_radius = self.radius + e.radius
                    if dx * dx + dy * dy < hit_radius * hit_radius:
                        self.on_hit(e, game)
                        break
        else:
            # Düşman Mermisi (Archer, Venom Spider vb.) Oyuncuya Çarptı mı?
            p = game.players[game.local_player_id]
            
            # MANYETİK AURA: Mermileri yavaşlat veya saptır
            mag_aura = p.stats.get("magneticAura", 0)
            if mag_aura > 0:
                dist = math.hypot(p.x - self.x, p.y - self.y)
                if dist < 300:
                    self.vx *= 0.95
                    self.vy *= 0.95
                    if random.random() < 0.1:
                        self.vx += random.uniform(-2, 2)
                        self.vy += random.uniform(-2, 2)
                        
            dist = math.hypot(p.x - self.x, p.y - self.y)
            if dist < (self.radius + p.radius):
                # Bloodwalker Kan Emme aktifse mermileri emerek HP'ye dönüştür
                # Kimlik kontrolü class_id ile: class_name evrimde evrim adına döner
                absorb_active = (getattr(p, 'class_id', '') == "bloodwalker" and
                                 getattr(getattr(p, 'specialization', None), 'blood_absorb_active', False))
                if not absorb_active:
                    p.last_attacker_type = getattr(self, "owner_type", "bilinmeyen"); p.take_damage(self.dmg)
                # absorb_active ise bloodwalker_logic.update() zaten emer
                self.dead = True

    def land(self, game):
        """Şişe yere değdi: kırılır ve bulutu bırakır.

        Konum tam menzil noktasına oturtulur; aksi halde son karenin adımı
        kadar (~30px) hedefi aşıp bulut biraz ileride oluşuyor.
        """
        dx = self.x - self.start_x
        dy = self.y - self.start_y
        dist = math.hypot(dx, dy)
        if dist > 0 and self.throw_range:
            k = self.throw_range / dist
            self.x = self.start_x + dx * k
            self.y = self.start_y + dy * k
        self.airborne = False
        self.explode(game)
        self.dead = True

    def throw_progress(self):
        """0 (elden çıktı) -> 1 (yere indi). Yay/gölge görseli için."""
        if not self.throw_range:
            return 1.0
        dx = self.x - self.start_x
        dy = self.y - self.start_y
        return min(1.0, math.hypot(dx, dy) / self.throw_range)

    def on_hit(self, enemy, game):
        if self.type == 'bomb':
            self.explode(game)
            self.dead = True
            return
            
        # Apply Elemental Effects (NEW Standardized)
        # dotDmgMult menzilli silahlarda tamamen etkisizdi: oyuncu çarpanı
        # mermiye p.dot_mult olarak taşıyor ama burada okunmuyordu. Çarpan
        # SADECE DoT'lara uygulanır; explode()'un anlık AoE hasarı fire_dmg'yi
        # doğrudan kullandığı için oraya sızdırılmaz (çifte sayım olurdu).
        _dm = getattr(self, 'dot_mult', 1.0)
        if self.fire_dmg > 0:
            enemy.apply_dot('fire', self.fire_dmg * 0.5 * _dm, 4.0)
            # Mini Patlama (AoE Pulse) on hit
            self.explode(game, small=True)

        if self.frost_dmg > 0:
            enemy.apply_dot('frost', self.frost_dmg * 0.5 * _dm, 4.0)

        if self.poison_dps > 0:
            enemy.apply_dot('poison', self.poison_dps * _dm, 5.0)

        # İsabet geri bildirimi: normal vuruşun eskiden hiçbir görseli yoktu,
        # sadece hasar sayısı çıkıyordu. Element mermiye göre seçilir.
        if not self.is_hostile:
            if self.fire_dmg > 0:
                _elem = 'fire'
            elif self.frost_dmg > 0:
                _elem = 'frost'
            elif self.poison_dps > 0:
                _elem = 'poison'
            else:
                _elem = 'phys'
            vfx.hit(game, self.x, self.y, _elem, is_crit=self.is_crit,
                    angle=math.atan2(self.vy, self.vx) + math.pi)

        # Hasar Uygula
        # is_crit AKTARILMALI: mermi kritik bilgisini taşıyordu ama take_damage'a
        # verilmiyordu, bu yüzden krite bağlı efektler (Tetikçi evrimi
        # crit_ignite, Kritik Aşırı Yük kartı) menzilli silahlarda hiç
        # tetiklenmiyordu.
        # minion_kills görevi: bayrak SADECE bu take_damage çağrısı boyunca
        # açıktır. Enemy.take_damage ölümde game.kill_enemy'yi senkron çağırır,
        # dolayısıyla kill_enemy bayrağı doğru okur. Çağrı sonrası hemen
        # temizlenir; bayat bayrak yüzünden oyuncunun öldürdüğü düşman
        # minyona yazılmaz (DoT/patlama ile sonradan ölüm de sayılmaz).
        _by_minion = getattr(self, "is_minion_proj", False)
        enemy.last_hit_by_minion = _by_minion
        try:
            enemy.take_damage(self.dmg, game, is_crit=self.is_crit, from_player=not self.is_hostile)
        finally:
            enemy.last_hit_by_minion = False
        self.hit_history.append(enemy.id)

        # Ayaz (frostbite) aurası: frost_slow statı tanımlıydı ama okunmuyordu.
        # Sahibi (oyuncu) üzerinden okunur; düşman mermileri etkilenmez.
        if not self.is_hostile and game and hasattr(game, "players"):
            _owner = game.players[game.local_player_id]
            fs = _owner.stats.get("frost_slow", 0)
            if fs > 0:
                from logic.status_effects import apply_slow
                apply_slow(enemy.effect_manager, duration=2.0,
                           mult=max(0.0, 1.0 - fs), name="Frostbite")

        # Vampir İmparatorluğu (Minion Lifesteal)
        if getattr(self, "is_minion_proj", False) and game and hasattr(game, "players"):
            p = game.players[game.local_player_id]
            ls = p.stats.get("minionLifesteal", 0)
            if ls > 0:
                p.heal(self.dmg * ls)
        
        # Görsel Efekt (Renge göre Damage Text)
        txt_color = self.color
        if self.is_crit: txt_color = (255, 255, 0) # Krit hep sarı kalsın ya da elemental krit?
        game.add_event("damage_text", enemy.x, enemy.y - 20, value=self.dmg, color=txt_color, timer=0.5, is_crit=self.is_crit)
        
        # Bounce / Pierce Mantığı
        if self.bounce > 0:
            next_target = self.find_next_target(game, enemy.id)
            if next_target:
                self.reorient(next_target)
                self.bounce -= 1
                self.lifetime = max(self.lifetime, 40)
                # Sekme Ustası kartı sekerken hasarı artırır. bounce_dmg_mult
                # daha önce yalnızca saklanıyordu, hiçbir yerde uygulanmıyordu.
                if self.bounce_dmg_mult != 1.0:
                    self.dmg *= self.bounce_dmg_mult
            elif self.pierce <= 0:
                self.dead = True
        elif self.pierce > 0:
            self.pierce -= 1
        else:
            self.dead = True

    def explode(self, game, small=False):
        # AOE Yerine BULUT (Cloud) Oluştur
        radius = self.aoe if not small else self.aoe * 0.4

        from entities.cloud import Cloud

        # --- BOMBACI: patlama yerine tetiklemeli MAYIN ---
        # Anlık hasar vermez; düşman yaklaşana kadar yerde bekler. Hasarı
        # mermide taşınan toplam hasardan türetilir (bomba hasarı poisonDps
        # üzerinden aktığı için burada tek seferlik fiziksel patlamaya çevrilir
        # — Bombacı'da zehir DoT'u kalmaz, kimlik Simyacı'dan ayrışır).
        if self.becomes_mine and not small:
            mine_radius = radius * self.mine_radius_mult
            burst = (self.dmg + self.fire_dmg + self.poison_dps) * self.mine_dmg_mult
            game.entity_id_counter += 1
            game.clouds.append(Cloud(game.entity_id_counter, self.x, self.y,
                                     radius=mine_radius,
                                     duration=MINE_LIFETIME,
                                     is_mine=True, mine_dmg=burst))
            game.add_event("explosion", self.x, self.y, radius=int(mine_radius * 0.3),
                           color=(255, 140, 40), timer=0.12)
            return

        new_cloud = Cloud(game.entity_id_counter, self.x, self.y,
                         radius=radius,
                         duration=1.3 * self.cloud_duration_mult,  # Simyacı bunu uzatır
                         poison_dps=self.poison_dps,
                         fire_dmg=self.fire_dmg,
                         frost_dmg=self.frost_dmg)
        # --- AOE HASAR (Özellikle Ateş Patlaması için) ---
        if self.fire_dmg > 0:
            for e in game.iter_enemies_near(self.x, self.y, radius):
                if not e.dead and not e.is_trap:
                    dx = e.x - self.x
                    dy = e.y - self.y
                    if dx * dx + dy * dy < radius * radius:
                        # Patlama anlık hasarı (Ateş Hasarı * 1.5 gibi bir çarpan veya direkt fire_dmg)
                        # Ejder minyonunun alan hasarı da minion_kills sayılır
                        e.last_hit_by_minion = getattr(self, "is_minion_proj", False)
                        try:
                            e.take_damage(self.fire_dmg, game, from_player=not self.is_hostile)
                        finally:
                            e.last_hit_by_minion = False
                        # DoT da ekleyelim (Patlamadan etkilenen yanar).
                        # Anlık hasar (yukarıdaki take_damage) çarpansız kalır,
                        # yalnızca yanma dotDmgMult'tan faydalanır.
                        e.apply_dot('fire', self.fire_dmg * 0.4 * getattr(self, 'dot_mult', 1.0), 3.0)

        game.clouds.append(new_cloud)
        game.entity_id_counter += 1
        
        # Ekran Sarsıntısı. Cam şişe patlayıcı değil; her atışta 15'lik sarsıntı
        # sürekli ateş ederken kamerayı titretiyordu.
        game.trigger_shake(5 if self.type == 'bomb' else 15)
        
        if self.type == 'bomb':
            # Şişede halka çizilmiyor: "explosion" event'i iki daire konturu
            # basıyor (renkli + beyaz iç halka) ve bulutun üstünde donuk bir
            # nişan işareti gibi duruyordu. Yerine sıçrayan damlalar; geri
            # bildirimi bulutun kendisi veriyor.
            for _ in range(12):
                a = random.uniform(0, math.tau)
                v = random.uniform(2.5, 7.0)
                game.particles.append({
                    'x': self.x, 'y': self.y,
                    'vx': math.cos(a) * v, 'vy': math.sin(a) * v,
                    'timer': random.uniform(0.12, 0.28),
                    'color': random.choice([(120, 170, 70), (70, 110, 50),
                                            (170, 200, 130)]),
                    'size': random.randint(2, 4),
                })
        else:
            game.add_event("explosion", self.x, self.y, radius=self.aoe,
                           color=self.color, timer=0.2)

        # --- Çılgın Simyacı (mad_bomber): bombalar %50 şansla ikinci kez patlar ---
        # Not: taslak `self.p_type` diyordu, gerçek alan adı `self.type`.
        if (self.type == 'bomb' and not small and not self.is_hostile
                and not getattr(self, 'is_minion_proj', False)
                and not self._second_blast):
            self._second_blast = True   # zincirleme ikinci patlamayı engeller
            owner = game.players.get(game.local_player_id) if hasattr(game, 'players') else None
            if getattr(owner, 'evolution_passive', '') == 'mad_bomber' and random.random() < 0.5:
                r = self.aoe * 0.7
                game.add_event("explosion", self.x, self.y, radius=int(r),
                               color=(255, 200, 60), timer=0.25)
                for e in list(game.iter_enemies_near(self.x, self.y, r)):
                    if e.dead or getattr(e, 'is_trap', False):
                        continue
                    dx, dy = e.x - self.x, e.y - self.y
                    if dx * dx + dy * dy <= r * r:
                        e.take_damage(self.dmg * 0.5, game, from_player=True)

    def find_next_target(self, game, current_id):
        next_target = None
        min_d = 400
        for other in game.iter_enemies_near(self.x, self.y, min_d):
            if other.id != current_id and not other.dead and not other.is_trap and other.id not in self.hit_history:
                dx = other.x - self.x
                dy = other.y - self.y
                d_sq = dx * dx + dy * dy
                if d_sq < min_d * min_d:
                    min_d = math.sqrt(d_sq)
                    next_target = other
        return next_target

    def reorient(self, target):
        angle = math.atan2(target.y - self.y, target.x - self.x)
        speed = math.hypot(self.vx, self.vy)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def draw(self, screen, camera_x, camera_y):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        if self.type == 'bomb':
            if self.airborne:
                # Fırlatılan şişe: yerden yükselip inen bir yay izlenimi.
                # Tepe noktasında büyür, gölge küçülüp uzaklaşır (top-down'da
                # yükseklik ancak böyle okunuyor).
                t = self.throw_progress()
                lift = math.sin(math.pi * t)          # 0 -> 1 -> 0
                height = 26 * lift
                shadow_r = max(2, int(4 - 2 * lift))
                shadow = pygame.Surface((shadow_r * 4, shadow_r * 4), pygame.SRCALPHA)
                pygame.draw.circle(shadow, (0, 0, 0, 90),
                                   (shadow_r * 2, shadow_r * 2), shadow_r * 2)
                screen.blit(shadow, (int(draw_x) - shadow_r * 2,
                                     int(draw_y) - shadow_r * 2))

                bx, by = int(draw_x), int(draw_y - height)
                size = int(self.radius + 3 + 3 * lift)
                # Cam gövde + mantar + takla atan parlama
                pygame.draw.circle(screen, (33, 120, 68), (bx, by), size)
                pygame.draw.circle(screen, (120, 230, 150), (bx, by), size, 1)
                spin = (self.throw_progress() * 12.0)
                ox = int(math.cos(spin) * size * 0.5)
                oy = int(math.sin(spin) * size * 0.5)
                pygame.draw.line(screen, (215, 200, 160),
                                 (bx - ox, by - oy), (bx + ox, by + oy), 2)
                pygame.draw.circle(screen, (190, 255, 210), (bx - ox, by - oy), 2)
            else:
                pygame.draw.circle(screen, (39, 174, 96), (int(draw_x), int(draw_y)), self.radius + 2)
                pygame.draw.circle(screen, (255, 255, 255), (int(draw_x), int(draw_y)), self.radius + 2, 1)
        elif self.type == 'black_hole':
            # Kara Delik Görseli (Büyük ve Karanlık)
            r = int(self.radius * 3)
            # Dış Halo
            h_r = r + random.randint(2, 6)
            pygame.draw.circle(screen, (142, 68, 173), (int(draw_x), int(draw_y)), h_r)
            # İç Karanlık
            pygame.draw.circle(screen, (20, 20, 30), (int(draw_x), int(draw_y)), r)
            # Parlama/Simge
            pygame.draw.circle(screen, (255, 255, 255), (int(draw_x), int(draw_y)), 2)
        elif self.is_katana:
            # Katana Görseli (X şeklinde hızlı bir effekt)
            import random
            offset = random.randint(-5, 5)
            pygame.draw.line(screen, (255, 255, 255), (draw_x - 15 + offset, draw_y - 15), (draw_x + 15 + offset, draw_y + 15), 3)
            pygame.draw.line(screen, (255, 255, 255), (draw_x + 15, draw_y - 15 + offset), (draw_x - 15, draw_y + 15 + offset), 3)
        else:
            p_color = self.color if not self.is_crit else (255, 255, 0)
            if self.is_hostile:
                # Düşman Mermisi: Elmas/Baklava Şekli (Kırmızı-Turuncu Tonları)
                p_color = (231, 76, 60) # Radikal Kırmızı
                points = [
                    (draw_x, draw_y - self.radius - 2),
                    (draw_x + self.radius + 2, draw_y),
                    (draw_x, draw_y + self.radius + 2),
                    (draw_x - self.radius - 2, draw_y)
                ]
                pygame.draw.polygon(screen, p_color, points)
                pygame.draw.polygon(screen, (255, 255, 255), points, 1) # Beyaz kenarlık
            else:
                # Oyuncu Mermisi: Standart Yuvarlak
                pygame.draw.circle(screen, p_color, (int(draw_x), int(draw_y)), self.radius)
                pygame.draw.circle(screen, (255, 255, 255), (int(draw_x), int(draw_y)), self.radius + 1, 1)
