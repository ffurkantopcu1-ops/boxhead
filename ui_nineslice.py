# -*- coding: utf-8 -*-
"""assets/ui/gothic/ altındaki sabit boyutlu PNG'leri her ölçüde çizer.

Oyun arayüzü her şeyi serbest ölçülerde çiziyor (sekmeler 150x50, kartlar
280x80, boss barı 700x25...), üretilen PNG'ler ise tek boyutlu. Bu modül
9-slice yaklaşımıyla araya girer: köşeler bozulmadan blitlenir, kenarlar tek
eksende, orta bölge iki eksende gerilir. Böylece tek panel PNG'si her panel
boyutunu karşılar.

Dilim sınırları assets/ui/gothic/nineslice.json içinde tutulur; şeffaf kenar
boşlukları (trim) orada hazır ölçülmüştür.

Kullanım:
    import ui_nineslice as n9
    n9.draw(screen, "panel_frame.png", rect)
    n9.draw_bar(screen, "bar_frame.png", rect, "bar_fill_hp.png", 0.62)

Varlık yoksa fonksiyonlar sessizce False döner; çağıran taraf eski
ui_theme çizimine düşebilir.
"""
import json
import os

import pygame

_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "ui", "gothic")
_META_FILE = os.path.join(_DIR, "nineslice.json")

_meta = None
_src_cache = {}      # name -> trim'lenmiş kaynak Surface
_compose_cache = {}  # (name, w, h) -> hazır Surface
_MAX_CACHE = 256     # ölçü başına bir yüzey; sınırsız büyümesin


def _load_meta():
    global _meta
    if _meta is None:
        try:
            with open(_META_FILE, encoding="utf-8") as fh:
                _meta = json.load(fh)
        except (OSError, ValueError):
            _meta = {}
    return _meta


def has(name):
    """Varlık ve dilim bilgisi mevcut mu?"""
    return name in _load_meta() and os.path.exists(os.path.join(_DIR, name))


def min_size(name):
    """Bozulmadan çizilebilen en küçük (genişlik, yükseklik)."""
    info = _load_meta().get(name)
    if not info:
        return (0, 0)
    return tuple(info["min_size"])


def _source(name):
    """Şeffaf kenarları kırpılmış kaynak yüzeyi (cache'li)."""
    surf = _src_cache.get(name)
    if surf is None:
        info = _load_meta()[name]
        full = pygame.image.load(os.path.join(_DIR, name)).convert_alpha()
        tx, ty, tw, th = info["trim"]
        surf = full.subsurface(pygame.Rect(tx, ty, tw, th)).copy()
        _src_cache[name] = surf
    return surf


def get(name, width, height):
    """İstenen ölçüde 9-slice yüzey üretir (cache'li). Yoksa None."""
    return _compose(name, width, height, include_center=True)


def get_border(name, width, height, tint=None):
    """Sadece kenar ve köşe dilimleri; orta boş kalır.

    Mevcut bir içeriği (ör. sınıf kartındaki eser) çerçevelemek için: normal
    `get` ortadaki dolguyu da gerdiği için altındaki görseli kapatıyor.
    tint verilirse çerçeve o renkle harmanlanır (sınıf rengi gibi).
    """
    return _compose(name, width, height, include_center=False, tint=tint)


def _compose(name, width, height, include_center=True, tint=None):
    if not has(name):
        return None
    mw, mh = min_size(name)
    width, height = max(int(width), mw), max(int(height), mh)

    key = (name, width, height, include_center, tint)
    cached = _compose_cache.get(key)
    if cached is not None:
        return cached

    src = _source(name)
    sw, sh = src.get_size()
    l, t, r, b = _load_meta()[name]["insets"]

    # kaynak ve hedefteki orta şeritler
    src_mid_w, src_mid_h = sw - l - r, sh - t - b
    dst_mid_w, dst_mid_h = width - l - r, height - t - b

    out = pygame.Surface((width, height), pygame.SRCALPHA)

    def piece(sx, sy, pw, ph):
        return src.subsurface(pygame.Rect(sx, sy, pw, ph))

    # scale() bilinçli olarak smoothscale değil: pixel-art'ta yumuşatma
    # kenarları bulanıklaştırır.
    def stretch(surf, w, h):
        return pygame.transform.scale(surf, (max(1, w), max(1, h)))

    # köşeler -- hiç gerilmez
    out.blit(piece(0, 0, l, t), (0, 0))
    out.blit(piece(sw - r, 0, r, t), (width - r, 0))
    out.blit(piece(0, sh - b, l, b), (0, height - b))
    out.blit(piece(sw - r, sh - b, r, b), (width - r, height - b))

    # kenarlar -- tek eksende
    if dst_mid_w > 0 and src_mid_w > 0:
        out.blit(stretch(piece(l, 0, src_mid_w, t), dst_mid_w, t), (l, 0))
        out.blit(stretch(piece(l, sh - b, src_mid_w, b), dst_mid_w, b), (l, height - b))
    if dst_mid_h > 0 and src_mid_h > 0:
        out.blit(stretch(piece(0, t, l, src_mid_h), l, dst_mid_h), (0, t))
        out.blit(stretch(piece(sw - r, t, r, src_mid_h), r, dst_mid_h), (width - r, t))

    # orta -- iki eksende (çerçeve modunda atlanır, içerik görünsün)
    if (include_center and dst_mid_w > 0 and dst_mid_h > 0
            and src_mid_w > 0 and src_mid_h > 0):
        out.blit(stretch(piece(l, t, src_mid_w, src_mid_h), dst_mid_w, dst_mid_h), (l, t))

    if tint is not None:
        # Toplamalı harman şeffaf pikselleri atlar, çerçeve dışına taşmaz
        layer = pygame.Surface((width, height))
        layer.fill(tint)
        out.blit(layer, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    if len(_compose_cache) >= _MAX_CACHE:
        _compose_cache.clear()
    _compose_cache[key] = out
    return out


def content_rect(name, rect):
    """rect içindeki kenarlıktan arta kalan alan (metin/dolgu buraya)."""
    info = _load_meta().get(name)
    if not info:
        return pygame.Rect(rect)
    l, t, r, b = info["insets"]
    return pygame.Rect(rect.x + l, rect.y + t,
                       max(0, rect.width - l - r), max(0, rect.height - t - b))


def outer_rect(name, content):
    """content_rect'in tersi: verilen içerik alanını saracak dış rect.

    Çağıran taraf rect'i içerik alanı olarak hesaplamışsa (eski ince
    çerçeveye göre yazılmış kod), çerçeve rect'in dışına çizilmeli; aksi
    halde 52px'lik kenar başlığı/metni örter.
    """
    info = _load_meta().get(name)
    if not info:
        return pygame.Rect(content)
    l, t, r, b = info["insets"]
    return pygame.Rect(content.x - l, content.y - t,
                       content.width + l + r, content.height + t + b)


def draw(screen, name, rect):
    """Çerçeveyi rect ölçüsünde çizer. Varlık yoksa False."""
    surf = get(name, rect.width, rect.height)
    if surf is None:
        return False
    screen.blit(surf, (rect.x, rect.y))
    return True


def draw_bar(screen, frame_name, rect, fill_name, ratio):
    """Çerçeveli durum çubuğu: oluk içine dolguyu oran kadar çizer.

    Dolgu yatay olarak kırpılır (gerilmez), böylece doku uzayıp incelmez.
    """
    if not draw(screen, frame_name, rect):
        return False
    inner = content_rect(frame_name, rect)
    ratio = max(0.0, min(1.0, ratio))
    fill_w = int(inner.width * ratio)
    if fill_w <= 0 or inner.height <= 0:
        return True

    path = os.path.join(_DIR, fill_name)
    if not os.path.exists(path):
        return True
    key = ("__fill__", fill_name, inner.width, inner.height)
    scaled = _compose_cache.get(key)
    if scaled is None:
        fill = pygame.image.load(path).convert_alpha()
        scaled = pygame.transform.scale(fill, (inner.width, inner.height))
        if len(_compose_cache) >= _MAX_CACHE:
            _compose_cache.clear()
        _compose_cache[key] = scaled
    screen.blit(scaled, (inner.x, inner.y), pygame.Rect(0, 0, fill_w, inner.height))
    return True


def clear_caches():
    _src_cache.clear()
    _compose_cache.clear()
