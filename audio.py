"""
Ses katmanı — oyunun ses efektlerini yükler, karıştırır ve çalar.

NEDEN: Oyunda hiç ses yoktu. `pygame.mixer` kod tabanında bir kez bile
çağrılmıyordu; `sounds/` altında tek bir öksüz dosya vardı ve ayarlardaki
`"sound"` anahtarı hiçbir şeye bağlı değildi (ölü ayar). Aksiyon oyununda
düğme→sonuç bağını yalnız görsele bırakmak vuruşun ağırlığını yok ediyordu.

TASARIM
-------
- Ses YOKSA oyun çalışmaya devam eder. Mixer açılamazsa (ses kartı yok,
  headless test, sürücü sorunu) her çağrı sessizce no-op olur. Ses, oynanışı
  bloke edecek bir bağımlılık değildir.
- Sık tekrarlanan olayların (isabet, ölüm) birden çok varyasyonu vardır ve
  her çalışta rastgele seçilir; aynı örneğin üst üste binmesi kulak tırmalar.
- SPAM KORUMASI: aynı olay milisaniyeler içinde onlarca kez tetiklenebilir
  (saniyede 10 tick vuran alev silahı, 40 düşmanın aynı anda ölmesi).
  Olay başına minimum aralık ve eşzamanlı kanal sınırı uygulanır — yoksa
  ses çamura döner ve mixer kanalları tükenir.
- Ses seviyesi 0-100 arası YÜZDE olarak tutulur (ayarlar ekranı böyle
  gösteriyor); pygame 0.0-1.0 beklediği için burada çevrilir.
"""

import os
import random
import sys

import pygame


def _base_path():
    """Kaynak kökü. PyInstaller paketinde sesler _MEIPASS altına açılır."""
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.dirname(os.path.abspath(__file__))


SOUND_DIR = os.path.join(_base_path(), "sounds")

# olay -> (dosya kökü, göreli ses, minimum tekrar aralığı sn)
# Göreli ses: her efektin doğal yüksekliği farklı; burada dengelenir.
# Aralık: 0 = sınırsız. Sık olaylarda kısa bir aralık şart.
EVENTS = {
    "shoot":       ("shoot",       0.35, 0.05),
    "shoot_heavy": ("shoot_heavy", 0.45, 0.08),
    "melee":       ("melee",       0.45, 0.06),
    "flame":       ("flame",       0.30, 0.18),   # saniyede ~10 tick vuruyor
    "hit":         ("hit",         0.30, 0.04),
    "crit":        ("crit",        0.55, 0.06),
    "enemy_death": ("enemy_death", 0.35, 0.05),
    "player_hurt": ("player_hurt", 0.70, 0.15),
    "explosion":   ("explosion",   0.55, 0.06),
    "boss":        ("boss",        0.80, 0.50),
    "pickup_gold": ("pickup_gold", 0.30, 0.05),
    "pickup_item": ("pickup_item", 0.45, 0.05),
    "heal":        ("heal",        0.45, 0.20),
    "level_up":    ("level_up",    0.75, 0.00),
    "dodge":       ("dodge",       0.50, 0.10),
    "turret":      ("turret",      0.60, 0.00),
    "mine":        ("mine",        0.45, 0.05),
    "ui_click":    ("ui_click",    0.55, 0.03),
    "ui_hover":    ("ui_hover",    0.25, 0.04),
    "ui_select":   ("ui_select",   0.60, 0.03),
    "ui_error":    ("ui_error",    0.60, 0.10),
    "game_over":   ("game_over",   0.80, 0.00),
}

# Aynı anda çalabilecek toplam efekt kanalı. Çok yüksek olursa yoğun
# dalgalarda ses duvarı oluşur; çok düşük olursa efektler yutulur.
CHANNELS = 24

_ready = False          # mixer açıldı mı
_failed = False         # açılamadıysa bir daha deneme
_sounds = {}            # olay -> [Sound, ...]
_last_played = {}       # olay -> son çalma zamanı (ms)
_volume_pct = 70        # 0-100 (0 = sessiz; ayrı bir mute bayrağı yok)


def init(volume_pct=70):
    """Mixer'ı hazırla ve sesleri yükle. Başarısız olursa sessizce devam eder."""
    global _ready, _failed, _volume_pct
    if _ready or _failed:
        return _ready
    _volume_pct = max(0, min(100, int(volume_pct)))
    try:
        # buffer=512: varsayılan 4096 aksiyon oyununda duyulur gecikme yaratır
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(CHANNELS)
    except Exception as error:
        _failed = True
        print(f"[audio] ses acilamadi, sessiz devam ediliyor: {error}")
        return False

    loaded = 0
    for event, (stem, _vol, _gap) in EVENTS.items():
        variants = []
        # tek dosya: <stem>.ogg — varyasyonlu: <stem>_1.ogg, _2.ogg ...
        for path in [os.path.join(SOUND_DIR, f"{stem}.ogg")] + \
                    [os.path.join(SOUND_DIR, f"{stem}_{i}.ogg") for i in range(1, 9)]:
            if not os.path.isfile(path):
                continue
            try:
                variants.append(pygame.mixer.Sound(path))
            except Exception as error:
                print(f"[audio] yuklenemedi {os.path.basename(path)}: {error}")
        if variants:
            _sounds[event] = variants
            loaded += len(variants)

    _ready = True
    _apply_volume()
    print(f"[audio] {loaded} ses dosyasi yuklendi ({len(_sounds)} olay)")
    return True


def _apply_volume():
    if not _ready:
        return
    factor = _volume_pct / 100.0
    for event, variants in _sounds.items():
        rel = EVENTS[event][1]
        for snd in variants:
            snd.set_volume(rel * factor)


def set_volume(pct):
    """Ses seviyesini YÜZDE olarak ayarla (0-100)."""
    global _volume_pct
    _volume_pct = max(0, min(100, int(pct)))
    _apply_volume()


def get_volume():
    return _volume_pct


def is_ready():
    return _ready


def play(event, volume_scale=1.0):
    """Bir olay sesi çal. Ses yoksa veya olay tanımsızsa sessizce geçer."""
    if not _ready or _volume_pct <= 0:
        return
    variants = _sounds.get(event)
    if not variants:
        return

    gap = EVENTS[event][2]
    now = pygame.time.get_ticks()
    if gap > 0:
        last = _last_played.get(event, -99999)
        if now - last < gap * 1000:
            return          # spam koruması
    _last_played[event] = now

    snd = random.choice(variants)
    channel = pygame.mixer.find_channel(True)   # meşgulse en eskisini al
    if channel is None:
        return
    if volume_scale != 1.0:
        # Tek seferlik ölçek: kaynak Sound'un seviyesini kalıcı bozmadan
        channel.set_volume(min(1.0, snd.get_volume() * volume_scale))
    channel.play(snd)
