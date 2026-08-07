# Boxhead 2.0 — Olası Bug Analizi

Bu rapor statik kod analizi sonucunda hazırlanmıştır. Kodda değişiklik yapılmamıştır.

## Kritik

### 1. 25. dalgada oyun çökebilir

`boss_rush` özel dalgasında `duration` alanı bulunmuyor. `next_wave()` bu alanı zorunlu olarak okuduğu için 25. dalgaya geçiş sırasında `KeyError` oluşur.

- `logic/game_logic.py:35`
- `logic/game_logic.py:679`

### 2. `meta.json` normal kayıt slotu olarak algılanıyor

`SaveManager.get_save_slots()` kayıt dizinindeki bütün JSON dosyalarını kabul ediyor. Bu nedenle meta ilerleme dosyası yükleme menüsünde `meta` adlı normal bir kayıt olarak gösteriliyor.

- Bu slot yüklenirse `save_data["player"]` bulunamadığı için oyun çöker.
- Yükleme ekranında toplu silme kullanılırsa `meta.json` da silinerek kristal ve günlük görev ilerlemesi kaybedilebilir.
- Mevcut ortamda `get_save_slots()` fonksiyonunun gerçekten `meta` adlı bir slot döndürdüğü doğrulandı.

İlgili yerler:

- `logic/save_manager.py:82`
- `logic/save_manager.py:110`
- `scenes/game_scene.py:299`

### 3. Midas Eli artifact'i oyunu çökertebilir

Artifact yakınında bir düşman varken `game.wave_level` okunuyor. `GameLogic` üzerinde böyle bir alan yok; mevcut dalga `game.wave["level"]` içinde tutuluyor. Bu yol `AttributeError` üretir.

- `entities/player.py:1005`

## Yüksek Öncelik

### 4. Kayıttan yüklenen sınıfın davranışı yanlış kalabilir

Yükleme sırasında `class_id` ve `class_name` değiştiriliyor, ancak `reinit_specialization()` çağrılmıyor. Örneğin sniper kaydı warrior olarak oluşturulmuş bir oyuncu nesnesine yüklenirse sınıf mantığı ve renk warrior olarak kalabilir.

- `logic/save_manager.py:88`
- `entities/player.py:233`

### 5. Yükleme sonrası XP eşiği yanlış kalıyor

`xp_to_next_level` kaydedilmiyor ve yüklenen seviyeye göre yeniden hesaplanmıyor. Yeni oyuncu nesnesinin varsayılan `100` eşiği yüksek seviyeli bir kayıtta kalabilir. Sonraki XP kazanımı hatalı veya zincirleme seviye atlamaya neden olabilir.

- `logic/save_manager.py:40`
- `entities/player.py:34`
- `entities/player.py:496`

### 6. Kayıt sistemi önemli ilerleme alanlarını kaydetmiyor

Mevcut kayıt verisi aşağıdaki çalışma durumlarının önemli bölümünü içermiyor:

- Sınıf evrimi ve evrim pasifi
- Kalıcı kart istatistikleri
- Satın alınmış ve aktif auralar
- Öz/essence ilerlemesi
- Otomatik satış modu
- Oyuncu konumu
- Enerji kalkanı
- Seçili zorluk
- Bazı aktif veya kalıcı sınıf bayrakları

Oyuna devam edildiğinde seviye ve ekipman doğru görünse bile karakter yapısı ve gücü değişebilir.

- `logic/save_manager.py:34`

### 7. Evrimlerin maksimum can değişimi etkisiz kalıyor

`apply_evolution()` içindeki `max_hp_delta` önce doğrudan uygulanıyor. Hemen ardından çağrılan `recalculate_stats()` maksimum canı temel istatistiklerden tekrar yazdığı için değişiklik siliniyor. Paladin `+80 HP` ve Martyr `-50 HP` gibi etkiler uygulanmayabilir.

- `entities/player.py:952`
- `entities/player.py:965`
- `logic/inventory_manager.py:285`

### 8. Zorluk çarpanları mevcut ve yeni düşmanlara farklı uygulanıyor

`GameLogic.update_difficulty()` ile mevcut düşmanlara uygulanan değerler, `Enemy.__init__()` ile yeni doğan düşmanlara uygulanan değerlerden farklıdır.

Örnek:

| Zorluk | Mevcut düşman HP/Hasar | Yeni düşman HP/Hasar |
|---|---:|---:|
| Hard | 5x / 3x | 2x / 1.5x |
| Very Hard | 20x / 7x | 5x / 3x |
| Impossible | 100x / 20x | 10x / 5x |

Ayrıca zorluk değiştirilirken eski zırh çarpanı geri alınmıyor. Zorluklar arasında tekrar tekrar geçiş yapmak düşman zırhını kalıcı biçimde katlayabilir.

- `logic/game_logic.py:824`
- `logic/game_logic.py:844`
- `entities/enemy.py:311`

## Orta Öncelik

### 9. Dalga olaylarının çoğu yalnızca açıklama metni gösteriyor

`fast_enemies`, `elite_rain`, `no_shooting` ve `boon` olaylarında tanımlanan çarpan ve bayrakları kullanan bir oyun mantığı bulunamadı. Yalnızca `swarm` olayındaki `enemy_count_mult` uygulanıyor.

- `logic/game_logic.py:26`
- `logic/game_logic.py:689`

### 10. Günlük görevlerin çoğu ilerletilemiyor

Kod tabanında yalnızca şu görev olayları için `track()` çağrısı bulundu:

- `kill`
- `kill_elite`
- `kill_boss`
- `kill_while_low`

Aşağıdaki 14 görev türü tanımlı olmasına rağmen bunları ilerleten çağrı bulunamadı:

- `blood_moon_survive`
- `collect_rarity`
- `collect_unique`
- `dodge_hits`
- `earn_gold`
- `evolve`
- `max_combo`
- `minion_kills`
- `pick_cards`
- `reach_level`
- `reach_wave`
- `sell_items`
- `spend_gold`
- `use_artifact`

- `logic/quest_system.py:5`
- `logic/game_logic.py:519`

### 11. Oyun sonu istatistiklerinin çoğu sürekli sıfır gösteriliyor

Hasar verilen, hasar alınan ve kazanılan altın sayaçları oluşturulup oyun sonu ekranında gösteriliyor; ancak bu değerleri artıran kod bulunmuyor. Yalnızca hayatta kalma süresi ve geçilen dalga güncelleniyor.

- `scenes/game_scene.py:73`
- `scenes/game_scene.py:213`
- `scenes/game_scene.py:1769`

### 12. Kombo hız bonusu başka kod tarafından sıfırlanıyor

`GameLogic` kombo miktarına göre `speed_mod` hesaplıyor. Ardından oyuncu güncellemesindeki durum efekti yöneticisi `speed_mod` değerini yeniden `1.0` yapıyor. Bu nedenle açıklanan kombo hız artışı hareket hızına yansımayabilir.

- `logic/game_logic.py:157`
- `logic/status_effects.py:64`
- `entities/player.py:342`

## Doğrulama Notları

- Tüm Python kaynakları geçici bir bytecode dizini kullanılarak sözdizimi kontrolünden geçti.
- Normal `check_all_syntax.py` çalıştırması mevcut `__pycache__` dosyasına yazma izni nedeniyle ilk denemede durdu; kaynak kodda sözdizimi hatası değildi.
- Import smoke testi ve manuel oyun testi yapılamadı; ortamda `pygame` kurulu değil.
- Statik analiz sırasında hiçbir Python kaynağı veya oyuncu kayıt dosyası değiştirilmedi.

## Önerilen Düzeltme Sırası

1. 25. dalgadaki `duration` hatası
2. `meta.json` dosyasının kayıt slotlarından ayrılması ve silme işlemlerinden korunması
3. Midas Eli içindeki geçersiz `wave_level` erişimi
4. Kayıt/yükleme sözleşmesinin sınıf, XP ve kalıcı ilerleme alanlarıyla tamamlanması
5. Zorluk çarpanlarının tek bir kaynaktan uygulanması
6. Evrim maksimum can hesabının istatistik sistemine dahil edilmesi
7. Günlük görev ve dalga olayı bağlantılarının tamamlanması
