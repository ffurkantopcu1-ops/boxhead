# DESIGN.md — Boxhead 2.0 UI Teması

Koyu-fantastik **pixel-art** UI teması. Referans: metal çerçeveli, sivri uçlu
kırmızı banner + boynuzlu kurukafa süsü. Tüm UI bileşenleri bu temadan türetilir.

## Tek kaynak

- **`ui_theme.py`** (repo kökü): palet, kurukafa piksel haritası, banner buton
  ve panel üreticileri. Tüm çizimler burada; başka yerde el ile tema çizme.
- **`tools/generate_ui_assets.py`**: `assets/ui/` altına şablon PNG'leri üretir
  (`skull.png`, `button_<durum>.png`, `panel_template.png`, `theme_sheet.png`).
  Tema değişince yeniden çalıştır: `python tools/generate_ui_assets.py`
- Oyun çalışırken butonlar/paneller boyuta göre **prosedürel** üretilir ve
  cache'lenir; PNG'ler şablon/referans içindir.

## Palet (`ui_theme.COLORS`)

| Anahtar | RGB | Kullanım |
|---|---|---|
| `blood` | (146, 24, 16) | Ana aksiyon (YENİ OYUN, OYNA) |
| `night` | (30, 78, 110) | İkincil aksiyon (OYUN YÜKLE) |
| `arcane` | (88, 40, 120) | Büyü/kristal içerik |
| `steel` | (95, 98, 104) | Nötr (AYARLAR) |
| `gold` | (150, 100, 22) | Vurgu/bilgi (YENİLİKLER) |
| `ember` | (70, 18, 14) | Tehlike/çıkış |
| `moss` | (44, 96, 58) | Onay/başarı (satın al, craft) |

Yapısal renkler: `METAL` (122,126,134), `METAL_HI`, `METAL_LO`, `DARK_OUT`
(24,20,22 kontur), `BONE`/`HORN` (kurukafa), `TEXT_COL` (240,234,220),
`PANEL_BG` (26,24,34), `GLOW_WARM` (255,120,50 hover halesi).

## Bileşenler

### Banner buton — `ui_theme.render_banner_button(w, h, text, color, state, skull)`

- Uçları sivri altıgen banner + 2px metal çerçeve + dış koyu kontur + iç gölge.
- Detaylar: uçlarda çift sivri metal elmas, dört eğim köşesinde metal plaka,
  alt ortada madalyon sarkıt (yükseklik >= ~48px'te görünür).
- Dolgu: dikey gradyan (üst %115 açık → alt %55 koyu).
- Metin: Georgia serif bold, koyu gölgeli, native ölçekte render edilip
  bütünle birlikte nearest-neighbor ölçeklenir (piksel görünümü).
- Durumlar: `normal` / `hover` (çerçeve parlar, sıcak hale, kurukafa gözleri
  yanar) / `pressed` (1 native px çöker) / `disabled` (gri tonlama).
- **Kurukafa sadece hover/seçili durumda** gösterilir (dar dikey menülerde
  üst üste binmeyi önler); banner üstüne ~9 native px taşar — `draw` çağrısı
  dönen `overhang` kadar yukarı blit eder.
- Kullanım: `ui_elements.Button` bu fonksiyonu sarar; eski
  `Button(x, y, w, h, text, font, color, hover_color)` API'si korunur
  (`hover_color` yok sayılır). Ek bayraklar: `.selected`, `.disabled`.

### Panel — `ui_theme.draw_panel(screen, rect, fill, alpha, skull)`

Menü panelleri, kart arkaları, tooltip zeminleri için: koyu yarı saydam zemin +
3px metal çerçeve + köşe plakaları + kenar ortası perçinleri; `skull=True` ile
üst ortaya 3x kurukafa oturur (18px yukarı taşar).

### Kurukafa — `ui_theme.render_skull(scale, glow)`

25x14 piksel harita (`ui_theme.SKULL`); `glow=True` gözleri turuncu yakar.
Asset kopyası: `assets/ui/skull.png`, `assets/ui/skull_glow.png`.

## Kurallar

1. Yeni buton eklerken `ui_elements.Button` kullan; renkleri `ui_theme.COLORS`
   üzerinden seç (ham RGB gömme).
2. Yeni panel/tooltip eklerken `ui_theme.draw_panel` kullan; el ile
   `pygame.draw.rect` + kenar çizme.
3. Seçili durum için sarı çerçeve çizme; `button.selected = True` yeter.
4. Pixel-art netliği için tema yüzeylerini `smoothscale` ile ÖLÇEKLEME —
   nearest (`pygame.transform.scale`) kullan.
5. Tema değişikliği yaptıysan: `python tools/generate_ui_assets.py` çalıştırıp
   `assets/ui/` şablonlarını güncelle ve bu dosyayı senkron tut.
6. Launcher (Tkinter) aynı paleti kullanır (`launcher/main.py` içindeki
   renk sözlüğü) — pygame teması birebir kopyalanamaz, palet ve sivri banner
   silueti Canvas ile yaklaşıklanır.

## Durum örnekleri

Bkz. `assets/ui/theme_sheet.png` (4 durum + 7 renk varyantı tek sayfada).
