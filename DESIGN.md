# DESIGN.md — Boxhead 2.0 UI Teması

Koyu-fantastik UI teması. **Görsel tek kaynak: `assets/ui/gothic/`** — oyulmuş
koyu taş çerçeveler, köşelerde kırmızı mühür taşları, aynı dilden buton
plakaları, portre/eşya çerçeveleri ve boynuzlu kurukafa arması.

> Bu dosyanın eski sürümü prosedürel (kodla çizilen) banner/panel temasını
> anlatıyordu. O çizim yolu hâlâ **yedek** olarak duruyor (varlık yüklenemezse
> devreye girer) ama referans değil. Gotik varlıklarla eski prosedürel anlatım
> çeliştiğinde **varlıklar kazanır**.

## Tek kaynak

- **`assets/ui/gothic/`**: görünüşün kendisi. Çerçeveler, buton durumları,
  slotlar, bar çerçevesi/dolguları, kurukafa arması.
- **`assets/ui/gothic/nineslice.json`**: her varlığın `insets`, `min_size` ve
  `trim` bilgisi. Elle ölçü tahmin etme, buradan oku.
- **`ui_nineslice.py`**: varlıkları serbest ölçüde çizen 9-slice katmanı.
- **`ui_theme.py`**: palet + üst seviye çizim API'si (panel, buton, başlık,
  aksan rengi düzeltme). UI kodu doğrudan buradan geçer.
- **`ui_elements.py`**: widget'lar (`Button`, `ClassCard`, slotlar) ve metin
  yardımcıları (`render_fit`, `wrap_text`, `get_font`).

## Varlık envanteri (`assets/ui/gothic/`)

| Varlık | insets | Kullanım |
|---|---|---|
| `panel_frame.png` | 52 | Geniş menü paneli (opak taş zemin dahil) |
| `panel_frame_small.png` | 40 | Kart/satır çerçevesi (ortası şeffaf) |
| `panel_frame_epic.png` | 56 | Mor "epic" vurgu paneli |
| `button_normal/hover/pressed/disabled.png` | 26/12 | Buton plakası, 4 durum |
| `portrait_frame.png` | 24 | Portre/eser çerçevesi |
| `item_slot.png`, `rarity_frame_*.png` | 14 | Envanter slotu ve nadirlik çerçevesi |
| `bar_frame.png` + `bar_fill_*.png` | 40/5 | HP/XP/kalkan/mana çubukları |
| `skull_crest.png` | — | Başlık ve seçili öğe arması |
| `icon_*.png`, `toggle_*.png` | — | Ok/onay/kapat ikonları, aç-kapa |

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
(24,20,22 kontur), `TEXT_COL` (240,234,220), `PANEL_BG` (26,24,34),
`GLOW_WARM` (255,120,50 hover halesi).

## Bileşenler

### Buton — `ui_elements.Button`

`ui_theme.render_banner_button` üzerinden `button_<durum>.png` plakasını çizer;
plaka tek renk taş olduğu için menüdeki renk kodlaması iç yüzeye toplamalı
(additive) harmanla uygulanır. Durumlar: `normal` / `hover` / `pressed` /
`disabled`. Kurukafa yalnız hover/seçilide görünür ve butonun üstüne taşar —
`draw`, dönen `overhang` kadar yukarı blit eder.

Eski API korunur: `Button(x, y, w, h, text, font, color, hover_color)`
(`hover_color` yok sayılır). Ek bayraklar: `.selected`, `.disabled`.

### Panel — `ui_theme.draw_panel(screen, rect, fill, alpha, skull, nineslice)`

Geniş, tek başına duran paneller için. **Çerçeve rect'in DIŞINA çizilir**
(`ui_nineslice.outer_rect`): çağıran taraf rect'i içerik alanı sayar. Izgarada
komşusu olan kutularda bu taşma bindirme yapar — orada aşağıdakini kullan.

### Izgara çerçevesi — `ui_theme.draw_inset_frame(screen, rect, ...)`

Çerçeveyi rect'in **İÇİNE** çizer, dış ölçü sabit kalır; kart/satır ızgaraları
için. `tint` ile aksan rengi harmanlanır, `glow` ile hover halesi eklenir,
`pad` ile içerik payı 9-slice insets yerine elle verilir. İçerik rect'ini
döndürür.

### Başlık — `ui_theme.render_title(text, size, color)`

Serif + koyu gölge. İki yanına `ui_elements.get_skull_crest(size)` konabilir.

### Aksan rengi — `ui_theme.readable(color, min_lum=150)`

Koyu sınıf/marka renklerini (ör. Gölge Ninja 44,62,80) koyu zeminde okunur
parlaklığa çeker; ton korunur. Metin ve ince çizgilerde ham renk kullanma.

## Kurallar

1. Buton eklerken `ui_elements.Button`; renk `ui_theme.COLORS`'tan (ham RGB yok).
2. Panel/tooltip eklerken `draw_panel`, ızgara kartı eklerken
   `draw_inset_frame`. Panel/buton/slot yerine çıplak
   `pygame.draw.rect(..., border_radius=N)` tema ihlalidir.
3. Seçili durum için sarı çerçeve çizme; `button.selected = True` yeter.
   Kartlarda seçili öğe **en son** çizilir (arma/hale komşunun altında kalmasın).
4. Pixel-art netliği için tema yüzeylerini `smoothscale` ile ÖLÇEKLEME —
   nearest (`pygame.transform.scale`) kullan.
5. Dikey yerleşimi **alttan yukarı** tahsis et: sabit yükseklikli öğeler (alt
   şerit, stat satırı, aksiyon sırası) önce yerini alır, esnek öğe (portre,
   liste gövdesi) kalanı doldurur.
6. 9-slice `insets` köşe süsünün ölçüsüdür, kenar taşının kalınlığı değil.
   İçeriği `pad` ile daha kenara yaklaştırabilirsin ama yatayda köşe
   taşlarının hizasından uzak dur.
7. Metni `render_fit` / `wrap_text` ile gerçek kullanılabilir genişliğe sığdır;
   en uzun içeriği (en uzun sınıf adı, 4 statlı satır) test et.
8. Launcher (Tkinter) aynı paleti kullanır (`launcher/main.py` renk sözlüğü) —
   pygame teması birebir kopyalanamaz, palet ve silüet Canvas ile yaklaşıklanır.

## Doğrulama

UI değişikliğini ekran görüntüsü almadan bitmiş sayma. Sahneyi offscreen kur
(`pygame.HIDDEN` veya `SDL_VIDEODRIVER=dummy`), stub bir manager ver,
`scene.draw()` çağır ve `pygame.image.save` ile PNG'ye yaz. Hem boşta hem
hover/seçili durumu, hem de en uzun metinle bak. Bu projede hizalama hataları
sürekli koddan değil render'dan yakalandı.

## Yedek çizim yolu

`ui_theme.USE_NINESLICE = False` her şeyi eski prosedürel çizime döndürür
(varlıklar bozulursa hızlı çıkış). `tools/generate_ui_assets.py` prosedürel
temanın şablon PNG'lerini üretir; gotik varlıkların yerine geçmez.
