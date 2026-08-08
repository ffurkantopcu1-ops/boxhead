# Gothic UI Kit

`assets/references/` altındaki referans sayfalarından yola çıkarak
[PixelLab MCP](https://api.pixellab.ai/mcp/docs) ile üretilmiş karanlık gotik
(Diablo tarzı) pixel-art UI seti. Tüm PNG'ler şeffaf arka planlıdır.

`assets/ui/` kökündeki `button_*.png` / `panel_template.png` dosyaları
`tools/generate_ui_assets.py` tarafından yeniden üretilen prosedürel
şablonlardır; üzerine yazmamak için bu set ayrı klasörde tutulur.

## İçerik

| Dosya | Boyut | Açıklama |
|---|---|---|
| `panel_frame.png` | 400x300 | Ana panel: taş çerçeve, köşe yakutları, koyu dolgu (opak) |
| `panel_frame_small.png` | 256x192 | Küçük panel çerçevesi, içi boş (şeffaf) |
| `panel_frame_epic.png` | 400x300 | Mor "epic" varyant, içi boş |
| `bar_frame.png` | 320x40 | Boş durum çubuğu yuvası, solda kurukafa madalyonu |
| `bar_fill_hp.png` | 288x22 | Kırmızı dolgu şeridi (can) |
| `bar_fill_mana.png` | 288x22 | Mor dolgu şeridi (mana) |
| `bar_fill_xp.png` | 288x22 | Altın dolgu şeridi (tecrübe) |
| `button_normal.png` | 300x60 | Buton plakası, normal |
| `button_hover.png` | 300x60 | Buton, üzerine gelince (aydınlık) |
| `button_pressed.png` | 300x60 | Buton, basılı (karanlık/gömülü) |
| `button_disabled.png` | 300x60 | Buton, devre dışı (soluk gri) |
| `icon_close.png` | 48x48 | Kırmızı X |
| `icon_settings.png` | 48x48 | Dişli |
| `icon_check.png` | 48x48 | Onay işareti |
| `icon_arrow_up/down/left/right.png` | 48x48 | Dört yön oku |
| `item_slot.png` | 64x64 | Boş envanter yuvası |
| `rarity_frame_common/rare/epic/legendary.png` | 64x64 | Nadirlik çerçeveleri |
| `skull_crest.png` | 96x64 | Boynuzlu kurukafa süsü (panel başlığı) |
| `toggle_off.png` / `toggle_on.png` | 128x48 | Aç/kapa anahtarı |

## Kullanım: 9-slice

Oyun arayüzü her şeyi serbest ölçülerde çizdiği için (sekme 150x50, kart
280x80, boss barı 700x25...) bu PNG'ler doğrudan blitlenmez. `ui_nineslice.py`
modülü köşeleri bozmadan kenarları ve ortayı gererek her ölçüyü karşılar.
Dilim sınırları `nineslice.json` içindedir.

```python
import ui_nineslice as n9

n9.draw(screen, "panel_frame.png", rect)                      # panel
n9.draw(screen, "button_normal.png", rect)                    # buton/kart/satır
n9.draw_bar(screen, "bar_frame.png", rect, "bar_fill_hp.png", 0.62)
inner = n9.content_rect("panel_frame.png", rect)              # metin alanı
```

`draw`/`draw_bar` varlık bulunamazsa `False` döner; çağıran taraf eski
`ui_theme` çizimine düşebilir.

### En küçük ölçüler (önemli)

9-slice köşeleri gerilmediği için her varlığın bir alt sınırı var. Altına
inilirse otomatik olarak bu ölçüye yükseltilir, yani **kutu taşar**:

| Varlık | Min ölçü | Uygun bileşenler |
|---|---|---|
| `button_normal.png` (+durumlar) | 54x26 | `TabButton` 150x50 / 180x40, `Button` 300x60, `SkillButton` 340x75, `EquippedRow` 400x68, `BackpackItemCard` 280x80, `MarketCard` 400x80 |
| `panel_frame_small.png` | 82x82 | `ClassCard`, orta boy paneller |
| `panel_frame.png` | 106x106 | envanter/craft/ayarlar overlay'leri, büyük paneller |
| `bar_frame.png` | 62x12 | tüm durum çubukları |
| `item_slot.png`, `rarity_frame_*` | 30x30 | envanter yuvaları (48 ve 64px'te test edildi) |

Kısa bileşenlerde (satır/kart/sekme) `panel_frame.png` **kullanılmaz** —
min yüksekliği 106px, bu bileşenler 40-80px. Onlar için `button_normal.png`
kullanılır.

### Bar yükseklikleri

`bar_frame.png` üst/alt rayları ~5px; oluk `yükseklik - 10` piksel kalır.
Şu anki HUD barları 12px ([game_scene.py:1142](../../../scenes/game_scene.py#L1142))
olduğundan oluk 2px'e düşüyor ve dolgu neredeyse görünmüyor.
**Önerilen: 24px** (oluk 14px). Boss barı 25px hâliyle uygun.

### Oyuna bağlandığı yerler

| Yer | Ne kullanıyor |
|---|---|
| [ui_theme.render_banner_button](../../../ui_theme.py) | `button_normal/hover/pressed/disabled` + buton rengiyle toplamalı tonlama (menü renk kodlaması korunur) |
| [ui_theme.draw_panel](../../../ui_theme.py) | `panel_frame` / `panel_frame_small` |
| [game_scene._draw_hud_bar](../../../scenes/game_scene.py) | `bar_frame` + `bar_fill_hp/shield/green` |
| [game_scene.draw_boss_healthbar](../../../scenes/game_scene.py) | `bar_frame` + `bar_fill_hp` |
| [game_scene.draw_inventory](../../../scenes/game_scene.py) | içerik zemini olarak `panel_frame` |

`ui_theme.USE_NINESLICE = False` yapmak hepsini eski prosedürel çizime
döndürür. Varlıklar/manifest bulunamazsa bu düşüş zaten otomatiktir.

**`draw_panel` çerçeveyi rect'in dışına çizer.** Çağıran kod rect'i içerik
alanı sayıp başlığı kenara yakın koyduğu için (eski çerçeve 3px'ti), 52px'lik
gotik kenar doğrudan rect üzerine çizilse başlıkları örtüyordu.
`ui_nineslice.outer_rect()` bu dönüşümü yapar.

### Launcher

Launcher tkinter ile yazılı; tkinter'da çalışma zamanında 9-slice yok, ama
Tk 8.6 PNG okuyabiliyor. Bu yüzden gotik parçalar launcher'ın **tam
ölçülerinde** önceden çizilir:

```
python tools/generate_launcher_chrome.py
```

Çıktı `launcher/` alt klasörüne gider (arka plan, durum kartı, buton
durumları, başlık çubuğu, kapat/küçült ikonları, progress bar) ve yerleşim
`launcher/layout.json` ile birlikte yazılır. **Launcher konumları bu JSON'dan
okur** — ölçüler ile konumlar birbirinden kopmasın diye tek kaynak orada.
`layout.json` yoksa `launcher/main.py` içindeki yedek sabitler kullanılır,
PNG'ler eksikse de eski widget arayüzüne düşer.

Arka plan `launcher_bg_a.png` (360x272, pixflux) tam 2x ölçeklenip
karartma/degrade bindirilerek üretilir; bu yüzden bulanıklık olmaz.
`launcher_bg_b.png` kullanılmayan alternatif bir varyanttır.

Pencere çerçevesizdir (`overrideredirect`): başlık çubuğu, sürükleme, kapatma
ve küçültme launcher içinde uygulanır.

### Dolgu renkleri

HUD'daki mevcut renklerle eşleşmesi için: can `bar_fill_hp.png`, enerji kalkanı
`bar_fill_shield.png` (mavi), XP `bar_fill_green.png` (kodda yeşil) veya
`bar_fill_xp.png` (altın), mana `bar_fill_mana.png`.

**`panel_frame.png` opaktır** (koyu dolgusu kendi içinde), diğer iki panel
çerçevesinin ortası şeffaftır — arkasına kendi zeminini çizmeniz gerekir.

**Buton durumları** aynı plakadan türetildiği için piksel piksel hizalıdır;
durum değişiminde kayma olmaz. Aynı şey dolgu şeritleri ve `toggle_on` için de
geçerli.

## Üretim yöntemi

Deneme hesabı 40 üretim hakkı verdiğinden `create_ui_asset` (20-40 üretim/çağrı)
ve `create_image_pro` kullanılamadı; her varlık **`create_image_pixflux`** ile
(1 üretim) oluşturuldu. Referans sayfalarından kırpılan palet görselleri
`color_image_base64` ile geçirilerek renk uyumu sağlandı.

Model çıktısı `no_background` bayrağına rağmen düz bir zemin üzerinde
döndüğünden, arka plan kenardan başlayan flood-fill ile yerel olarak silindi
(kapalı iç bölgeler korunur).

Buton durumları, dolgu renkleri, nadirlik çerçeveleri ve ok yönleri **yerel
olarak** (HSV derecelendirme / döndürme) türetildi: hem üretim hakkı harcamaz
hem de durumlar arası geometri birebir aynı kalır.

Toplam 30/40 üretim harcandı.

## Varlıkları yeniden üretme

```
python tools/fix_asset_right_caps.py       # sağ uçları kapat (aynalama)
python tools/generate_nineslice_meta.py    # nineslice.json + doğrulama
python tools/generate_launcher_chrome.py   # launcher parçaları + layout.json
```

`fix_asset_right_caps.py` idempotenttir. Modelin ürettiği bazı yatay
varlıklarda (bar çerçevesi, buton plakaları) sol uçta süslü kap varken sağ uç
tuvalin kenarından taşmış, yani dikey kapatma kenarı yoktu; 9-slice bunu
kopyaladığı için sağ köşeler kesik görünüyordu. Script sol kapı aynalayarak
sağa yazar.

## Bilinen eksikler

- `rarity_frame_*` çerçeveleri `item_slot.png` üzerinden renklendirildiği için
  tonlar birbirine yakın; nadirlik ayrımı zayıf. Daha belirgin kenar rengi
  isteniyorsa doygunluk artırılabilir.
- `bar_frame.png` yuvası referanslardaki kadar kalın değil.
- `panel_frame_small.png` model tarafından açık taş tonunda üretildi, koyulaştırma
  ile setin geri kalanına yaklaştırıldı; yine de dokusu diğer panellerden farklı.
