"""
VFX katmanı — görsel efektlerin ortak çizim/doku altyapısı.

NEDEN: Efektler eskiden doğrudan `pygame.draw` ile çiziliyordu; ömre bağlı
sönme yoktu (efekt aniden belirip aniden kayboluyordu), `explosion` ile
`shockwave` aynı daireyi çiziyordu, parçacıklar içi dolu opak dairelerdi ve
doku desteği hiç yoktu.

Bu modül `entities/cloud.py`'daki "tek doku üret, hue kaydırarak çoğalt,
cache'le" desenini genelleştirir: assets/vfx/ altındaki bir gri/nötr doku
istenen renge boyanır, istenen boya ölçeklenir ve iki seviyede cache'lenir.
Doku yoksa her fonksiyon eski prosedürel çizime düşer — yani assets/vfx/
tamamen boş olsa bile oyun çalışmaya devam eder.
"""

import math
import os
import sys

import pygame


def _base_path():
    """Kaynak kök dizini. PyInstaller paketinde assets _MEIPASS altına açılır
    (bkz. Boxhead.spec datas ve logic/version.py aynı deseni kullanır)."""
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.dirname(os.path.abspath(__file__))


_VFX_DIR = os.path.join(_base_path(), "assets", "vfx")

# --- CACHE'LER ---
_RAW = {}        # dosya adı -> ham yüzey (veya None: dosya yok)
_TINTED = {}     # (ad, hue, sat) -> boyanmış yüzey
_SCALED = {}     # (ad, hue, sat, boy) -> ölçeklenmiş yüzey

# Ölçek cache'i sınırsız büyümesin: efekt yarıçapları sürekli değiştiği için
# her piksel değeri ayrı girdi olur. Boyutları 4'ün katına yuvarlıyoruz.
_SIZE_QUANT = 4
_MAX_SCALED = 512
_MAX_TINTED = 256


def _quant(size):
    return max(_SIZE_QUANT, int(size / _SIZE_QUANT + 0.5) * _SIZE_QUANT)


def get_raw(name):
    """assets/vfx/<name>.png yüzeyi (bir kez yüklenir). Yoksa None.

    DİKKAT: Başarısızlık YALNIZCA dosya gerçekten yoksa cache'lenir. Dosya var
    ama yükleme patlıyorsa (en tipik sebep: ekran modu henüz kurulmadığı için
    convert_alpha() çalışamaz) cache'lenmez — aksi halde erken bir çağrı None'ı
    kalıcı hale getirip dokuyu oturum boyunca devre dışı bırakırdı.
    """
    if name in _RAW:
        return _RAW[name]
    path = os.path.join(_VFX_DIR, name + ".png")
    if not os.path.exists(path):
        _RAW[name] = None       # gerçekten yok: kalıcı olarak yedek çizime düş
        return None
    try:
        surf = pygame.image.load(path).convert_alpha()
    except Exception:
        return None             # geçici hata: cache'leme, sonra tekrar dene
    _RAW[name] = surf
    return surf


def _qcolor(color):
    """Rengi 16'lık adımlara yuvarla — cache patlamasını önler.

    Sönme, renk karartılarak yapıldığı (bkz. _blit_sprite) için renk her karede
    değişir; yuvarlamazsak her ton ayrı cache girdisi olur.
    """
    return (color[0] & 0xF0, color[1] & 0xF0, color[2] & 0xF0)


def get_tinted(name, color):
    """Dokuyu istenen renge boyar. Yoksa None.

    Kaynak dokular BEYAZ/GRİ TONLUDUR (Kenney Particle Pack, CC0). Gri tonlu
    bir kaynağı renklendirmek = kanal kanal çarpmak; BLEND_RGBA_MULT bunu C
    seviyesinde anında yapar.

    DİKKAT: Burada önce piksel piksel HSV dönüşümü yazılmıştı — 512x512 doku
    için 262 bin colorsys çağrısı demekti ve her yeni renk ilk kullanıldığında
    oyunu saniyelerce donduruyordu. Çarpma hem doğru hem anlık.
    """
    base = get_raw(name)
    if base is None:
        return None
    c = _qcolor(color)
    cached = _TINTED.get((name, c))
    if cached is not None:
        return cached
    tinted = base.copy()
    tinted.fill((c[0], c[1], c[2], 255), special_flags=pygame.BLEND_RGBA_MULT)
    if len(_TINTED) > _MAX_TINTED:
        _TINTED.clear()
    _TINTED[(name, c)] = tinted
    return tinted


def get_sprite(name, color, size):
    """İstenen renk ve boyutta doku (iki seviye cache'li). Yoksa None."""
    q = _quant(size)
    key = (name, _qcolor(color), q)
    cached = _SCALED.get(key)
    if cached is not None:
        return cached
    tinted = get_tinted(name, color)
    if tinted is None:
        return None
    if len(_SCALED) > _MAX_SCALED:
        _SCALED.clear()
    # Pixel-art netliği için nearest (DESIGN.md kuralı 4)
    scaled = pygame.transform.scale(tinted, (q, q))
    _SCALED[key] = scaled
    return scaled


# --- ÖMÜR EĞRİLERİ ---

def life_progress(obj):
    """0.0 (yeni doğdu) -> 1.0 (ömrü bitti). t0 yoksa güvenli varsayılan."""
    t0 = obj.get('t0') or obj.get('timer') or 1.0
    if t0 <= 0:
        return 1.0
    return max(0.0, min(1.0, 1.0 - (obj.get('timer', 0) / t0)))


def fade_alpha(progress, curve="out"):
    """Sönme eğrisi -> 0..255."""
    if curve == "flash":
        # Patlama: doğar doğmaz parlak (taban 0.65), ilk %12'de tepeye çıkar,
        # sonra hızlanarak söner. Taban şart: sıfırdan başlayan eğri efekti
        # ilk karede görünmez yapıyordu.
        if progress < 0.12:
            a = 0.65 + 0.35 * (progress / 0.12)
        else:
            k = (progress - 0.12) / 0.88
            a = (1.0 - k) ** 1.6
    elif curve == "in_out":
        a = math.sin(math.pi * progress)
    elif curve == "flat":
        a = 1.0 if progress < 0.75 else (1.0 - progress) * 4.0
    else:
        a = 1.0 - progress
    return max(0, min(255, int(a * 255)))


# --- VFX KATMANI ---
# MİMARİ: Efektler tek tek toplamalı (additive) harmanlanırsa her efekt için
# geçici yüzey + ayrı blit gerekir; tavan yükünde bu 18 ms/kare ediyordu.
# Doğrudan çizmek ise YANLIŞ: pygame.draw piksel eklemez, DEĞİŞTİRİR — sönük
# bir efekt arka plandan koyu kalıp kara leke bırakır.
# Çözüm: tüm efektler ortak bir şeffaf katmana UCUZ (normal) çizilir, katman
# kare başına BİR KEZ toplamalı basılır. N pahalı blit yerine 1 tane.
_LAYER = None
_USED = False       # bu karede katmana bir şey çizildi mi
_PREV_USED = False  # geçen kare kirli miydi (temizlik gerekir mi)


def _mark():
    """Katmanın kirlendiğini işaretle.

    NOT: Burada sınırlayıcı-dikdörtgen birleşimi (Rect.union) denendi ve
    ÖLÇÜMDE KÖTÜLEŞTİ (9.6 -> 12.6 ms): efektler ekrana yayıldığında birleşim
    zaten tam ekrana çıkıyor, üstüne çizim başına union maliyeti biniyor.
    Basit bir bayrak, hiç efekt olmayan karelerde maliyeti sıfırlamak için
    yeterli — asıl kazanç orada.
    """
    global _USED
    _USED = True


def begin_frame(size):
    """Kare başında VFX katmanını hazırla ve döndür. Efektler buna çizilir."""
    global _LAYER, _USED, _PREV_USED
    if _LAYER is None or _LAYER.get_size() != size:
        _LAYER = pygame.Surface(size, pygame.SRCALPHA)
    elif _PREV_USED:
        _LAYER.fill((0, 0, 0, 0))
    _USED = False
    return _LAYER


def end_frame(target):
    """Katmanı hedefe toplamalı harmanla bas (kare başına tek pahalı işlem)."""
    global _PREV_USED
    _PREV_USED = _USED
    if _LAYER is not None and _USED:
        target.blit(_LAYER, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)


def _dim(color, alpha):
    """Toplamalı harman için rengi karart.

    DİKKAT: BLEND_RGBA_ADD alpha kanalını parlaklık için KULLANMAZ — kaynak
    RGB'si olduğu gibi eklenir. Bu yüzden sönmeyi alpha ile değil, RGB'yi
    ölçekleyerek yapmak zorundayız (ilk sürümde efektler bu yüzden sönmek
    yerine parlıyordu).
    """
    f = max(0.0, min(1.0, alpha / 255.0))
    return (int(color[0] * f), int(color[1] * f), int(color[2] * f), 255)


def _blit_sprite(surf, sprite, x, y):
    """Dokuyu VFX katmanına bas.

    DİKKAT: Burada `sprite.set_alpha(alpha)` KULLANILMAZ. Katman sonunda
    BLEND_RGBA_ADD ile basılıyor ve toplamalı harman alpha kanalını yok sayar —
    set_alpha ile sönme denendi, efekt hiç sönmedi. Sönme, dokunun tint
    rengi karartılarak (bkz. _dim + get_sprite çağrıları) yapılır.
    """
    surf.blit(sprite, (x, y))
    _mark()


# --- EFEKT ÇİZİCİLERİ ---

def draw_explosion(surf, ev, dx, dy):
    """Patlama: içi dolu çekirdek + genişleyen halka. Doku varsa onu kullanır."""
    prog = life_progress(ev)
    rad = ev.get('radius', 100)
    clr = ev.get('color', (255, 200, 80))
    alpha = fade_alpha(prog, "flash")

    # Çekirdek hızla açılır (ilk üçte bir), sonra sönerken hafifçe küçülür
    core_r = rad * (0.45 + 0.55 * min(1.0, prog * 3.0)) * (1.0 - 0.25 * prog)
    sprite = get_sprite("burst", _dim(clr, alpha), core_r * 2)
    if sprite is not None:
        _blit_sprite(surf, sprite, int(dx - core_r), int(dy - core_r))
    else:
        _fallback_disc(surf, dx, dy, core_r, clr, alpha)

    # Dışa doğru açılan ince şok halkası
    ring_r = rad * (0.3 + 0.9 * prog)
    ring_a = int(alpha * (1.0 - prog) * 0.9)
    if ring_r > 2 and ring_a > 4:
        _ring(surf, dx, dy, ring_r, clr, ring_a, width=max(1, int(3 * (1.0 - prog)) + 1))


def draw_shockwave(surf, ev, dx, dy):
    """Şok dalgası: yalnızca hızla genişleyen halka — patlamayla karışmaz."""
    prog = life_progress(ev)
    rad = ev.get('radius', 100)
    clr = ev.get('color', (255, 255, 255))
    ring_r = rad * (0.15 + 1.0 * prog)
    alpha = int(fade_alpha(prog, "out") * 0.95)
    if ring_r > 2 and alpha > 4:
        _ring(surf, dx, dy, ring_r, clr, alpha, width=max(1, int(4 * (1.0 - prog)) + 1))
        # İçeride sönen ikinci, ince halka (derinlik hissi)
        inner = ring_r * 0.72
        if inner > 2:
            _ring(surf, dx, dy, inner, clr, int(alpha * 0.5), width=1)


def draw_slash(surf, ev, dx, dy):
    """Savurma: verilen açıya dik, ortası kalın bir yay.

    Eskiden yönden bağımsız sabit bir X çiziliyordu; artık `angle` kullanılır.
    """
    prog = life_progress(ev)
    r = ev.get('range', 80) * 0.5
    clr = ev.get('color', (255, 255, 255))
    alpha = fade_alpha(prog, "out")
    if alpha <= 4:
        return
    angle = ev.get('angle')
    if angle is None:
        angle = 0.0
    # Yay, saldırı yönüne DİK uzanır ve ilerledikçe biraz açılır
    perp = angle + math.pi / 2
    span = r * (0.9 + 0.35 * prog)
    bow = r * 0.35 * (1.0 - prog)
    pts = []
    for i in range(9):
        t = i / 8.0
        off = (t - 0.5) * 2.0
        px = dx + math.cos(perp) * off * span + math.cos(angle) * bow * (1 - off * off)
        py = dy + math.sin(perp) * off * span + math.sin(angle) * bow * (1 - off * off)
        pts.append((px, py))
    width = max(1, int(5 * (1.0 - prog)) + 1)
    _lines(surf, pts, clr, alpha, width)


def draw_sweep(surf, ev, dx, dy, surface_provider):
    """Geniş süpürme konisi. Ömür ilerledikçe sönerek genişler."""
    prog = life_progress(ev)
    angle = ev.get('angle', 0.0)
    r_v = ev.get('range', 100) * (0.85 + 0.25 * prog)
    a_v = ev.get('arc', 1.0)
    clr = ev.get('color', (255, 255, 255))
    # Koni dolgusu: toplamalı harmanda düşük alfa soluk gri okunuyordu,
    # savurma parlak bir kesik gibi görünmeli.
    alpha = int(fade_alpha(prog, "out") * 0.85)
    if alpha <= 4:
        return

    pts = [(dx, dy)]
    steps = 10
    sa = angle - a_v / 2
    for i in range(steps + 1):
        a = sa + (a_v / steps) * i
        pts.append((dx + math.cos(a) * r_v, dy + math.sin(a) * r_v))
    if len(pts) <= 2:
        return

    # Doğrudan VFX katmanına çiziliyor; ayrı geçici yüzeye gerek yok.
    # (surface_provider imza uyumu için korunuyor, artık kullanılmıyor.)
    _mark()
    pygame.draw.polygon(surf, _dim(clr, alpha), [(int(px), int(py)) for px, py in pts])
    _lines(surf, pts[1:], clr, min(255, alpha * 2), max(1, int(3 * (1.0 - prog)) + 1))


def draw_fx(surf, ev, dx, dy):
    """Genel dokulu efekt — `tex` ile hangi doku olduğu belirlenir.

    Yeni bir efekt eklemek için çizim döngüsüne dal eklemeye gerek yok:
        game.add_event("fx", x, y, tex="crit", size=40, color=(255,220,90))

    Parametreler: tex, size, color, timer, grow (büyüme oranı), spin (dönüş),
    curve (sönme eğrisi), rise (yukarı süzülme hızı, px/sn).
    """
    prog = life_progress(ev)
    alpha = fade_alpha(prog, ev.get('curve', 'out'))
    if alpha <= 3:
        return
    size = ev.get('size', 32) * (1.0 + ev.get('grow', 0.6) * prog)
    if size < 1:
        return
    clr = ev.get('color', (255, 255, 255))
    dy -= ev.get('rise', 0.0) * prog

    sprite = get_sprite(ev.get('tex', 'spark'), _dim(clr, alpha), size)
    if sprite is None:
        _fallback_disc(surf, dx, dy, size * 0.4, clr, alpha)
        return
    spin = ev.get('spin', 0.0)
    if spin:
        sprite = pygame.transform.rotate(sprite, spin * prog * 360.0)
    w, h = sprite.get_size()
    _blit_sprite(surf, sprite, int(dx - w / 2), int(dy - h / 2))


def draw_particle(surf, part, px, py):
    """Parçacık: ömre bağlı sönme + küçülme. Doku varsa toplamalı harman."""
    prog = life_progress(part)
    color = part.get('color', (255, 255, 255))
    base_alpha = color[3] if len(color) > 3 else 255
    alpha = int(base_alpha * (1.0 - prog))
    if alpha <= 3:
        return
    size = max(1.0, part.get('size', 3) * (1.0 - 0.55 * prog))

    tex = part.get('tex')
    if tex:
        sprite = get_sprite(tex, _dim(color, alpha), size * 2)
        if sprite is not None:
            _blit_sprite(surf, sprite, int(px - size), int(py - size))
            return
    _fallback_disc(surf, px, py, size, color, alpha)


# --- YEDEK PROSEDÜREL ÇİZİM (doku yokken) ---

def _fallback_disc(surf, cx, cy, r, color, alpha):
    """Katmana çizilen leke: sönük dış hale + parlak çekirdek.

    `surf` VFX katmanıdır (şeffaf), bu yüzden normal çizim yeterli — parlama
    katman bir kez toplamalı basılırken oluşur.
    """
    if alpha <= 2:
        return
    r = int(max(1, r))
    cx, cy = int(cx), int(cy)
    _mark()
    if r <= 3:
        pygame.draw.circle(surf, _dim(color, alpha), (cx, cy), r)
        return
    # DİKKAT: pygame.draw.circle piksel EKLEMEZ, değiştirir — çekirdek haleden
    # KOYU olursa ortada kara delik oluşur. Çekirdek her zaman daha parlak.
    pygame.draw.circle(surf, _dim(color, int(alpha * 0.55)), (cx, cy), r)
    hot = (min(255, color[0] + 90), min(255, color[1] + 90), min(255, color[2] + 90))
    pygame.draw.circle(surf, _dim(hot, alpha), (cx, cy), int(r * 0.5))


def _ring(surf, cx, cy, r, color, alpha, width=2):
    """Halka — VFX katmanına çizilir."""
    if alpha <= 2:
        return
    r = int(max(1, r))
    if r > 3000:
        return
    _mark()
    pygame.draw.circle(surf, _dim(color, alpha), (int(cx), int(cy)), r, width)


def _lines(surf, pts, color, alpha, width):
    """Polyline — VFX katmanına çizilir."""
    if len(pts) < 2 or alpha <= 2:
        return
    _mark()
    pygame.draw.lines(surf, _dim(color, alpha), False,
                      [(int(p[0]), int(p[1])) for p in pts], width)


# --- ELEMENT GÖRSEL DİLİ ---
# Her elementin tek bir rengi ve dokusu var; oyuncu efektin tipini renginden
# tanısın diye tüm sistemler (mermi, DoT, bulut, patlama) bunu kullanır.
ELEMENTS = {
    'phys':      {'color': (255, 236, 180), 'tex': 'spark'},
    'fire':      {'color': (255, 130, 40),  'tex': 'flame'},
    'frost':     {'color': (110, 200, 255), 'tex': 'spark'},
    'poison':    {'color': (120, 230, 90),  'tex': 'smoke'},
    'lightning': {'color': (150, 200, 255), 'tex': 'lightning'},
    'arcane':    {'color': (190, 120, 255), 'tex': 'magic'},
    'heal':      {'color': (110, 240, 150), 'tex': 'glow'},
    'gold':      {'color': (255, 205, 70),  'tex': 'crit'},
}


def element(name):
    return ELEMENTS.get(name, ELEMENTS['phys'])


# --- ÜST SEVİYE GERİ BİLDİRİM YARDIMCILARI ---
# Oyun kodu bunları çağırır; efekt tipi/parametre seçimi burada merkezî kalır.

def hit(game, x, y, elem='phys', is_crit=False, angle=None):
    """İsabet geri bildirimi. Eskiden normal vuruşun HİÇBİR görseli yoktu."""
    if not hasattr(game, 'add_event'):
        return
    e = element(elem)
    if is_crit:
        game.add_event("fx", x, y, tex="crit", size=54, grow=0.9,
                       color=(255, 225, 120), timer=0.28, curve="flash")
        emit(game, x, y, count=7, color=(255, 220, 130), speed=(2.0, 5.0),
             size=(2, 4), life=(0.18, 0.34), tex="spark", drag=0.08)
    else:
        game.add_event("fx", x, y, tex=e['tex'], size=22, grow=0.7,
                       color=e['color'], timer=0.16)
        emit(game, x, y, count=3, color=e['color'], speed=(1.2, 3.0),
             size=(1.5, 3), life=(0.12, 0.24), spread=1.6,
             angle=angle if angle is not None else 0.0, drag=0.1)


def dodge(game, x, y):
    game.add_event("fx", x, y, tex="ring", size=46, grow=1.4,
                   color=(190, 220, 255), timer=0.3)


def heal(game, x, y, amount=0):
    game.add_event("fx", x, y, tex="glow", size=48, grow=0.5,
                   color=(110, 240, 150), timer=0.4, rise=30)
    emit(game, x, y, count=5, color=(140, 255, 180), speed=(0.4, 1.2),
         size=(2, 4), life=(0.4, 0.7), tex="spark", gravity=-0.04)


def level_up(game, x, y):
    game.add_event("fx", x, y, tex="magic", size=110, grow=0.8,
                   color=(255, 225, 130), timer=0.7, spin=0.25, curve="flash")
    emit(game, x, y, count=22, color=(255, 220, 140), speed=(1.5, 4.0),
         size=(2, 5), life=(0.5, 0.9), tex="spark", gravity=-0.03, drag=0.04)


def pickup(game, x, y, kind='gold'):
    e = element(kind)
    game.add_event("fx", x, y, tex="crit", size=30, grow=1.0,
                   color=e['color'], timer=0.3, rise=40)


def muzzle(game, x, y, angle, color=(255, 220, 150)):
    game.add_event("fx", x, y, tex="muzzle", size=26, grow=0.3,
                   color=color, timer=0.09)


# --- PARÇACIK YAYICI ---

def emit(game, x, y, count=8, color=(255, 200, 80), speed=(1.0, 3.5),
         size=(2, 5), life=(0.2, 0.5), tex=None, spread=None, angle=0.0,
         gravity=0.0, drag=0.0):
    """Bir noktadan parçacık demeti fırlatır.

    `spread` verilmezse tam daire (360°) saçılır; verilirse `angle` yönünde
    o genişlikte koni oluşur. Üretim MAX_PARTICLES tavanına saygılıdır.
    """
    import random
    parts = getattr(game, 'particles', None)
    if parts is None:
        return
    budget = getattr(game, 'MAX_PARTICLES', 500) - len(parts)
    if budget <= 0:
        return
    count = min(count, budget)
    for _ in range(count):
        if spread is None:
            a = random.uniform(0, math.tau)
        else:
            a = angle + random.uniform(-spread / 2, spread / 2)
        sp = random.uniform(*speed)
        lt = random.uniform(*life)
        parts.append({
            'x': x, 'y': y,
            'vx': math.cos(a) * sp, 'vy': math.sin(a) * sp,
            'timer': lt, 't0': lt,
            'color': color,
            'size': random.uniform(*size),
            'tex': tex,
            'gravity': gravity, 'drag': drag,
        })
