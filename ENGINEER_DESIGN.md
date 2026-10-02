# Saha Mühendisi ve taretler — v1.24.0

Mühendis atış kitiyle savaşır, imlece kurduğu taretlerle alanı destekler. Alev silahları alternatif ekipman olarak kullanılabilir.

## Kontroller ve karşılıkları

- Sol tık: taret kiti artık gerçek bir atış silahıdır; hasar, kritik ve elemental bonusları kullanır.
- R: imlecin yönüne en fazla 280 px uzağa taret kurar. Başlangıçta iki şarj, her biri 5 saniyede dolar; cooldown yatırımı kısaltır.
- E: imlece yakın düşmanı taretlere hedef gösterir ve 6 saniye +%35 atış hızı verir. Bekleme süresi 10 saniye. Hedef bulunmasa da aktif taretlere hız komutu verilir.
- 220 px içindeki taretler +%20 kalibrasyon hasarı kazanır. 750 px uzağında bırakılan taretler ateş etmez.
- Taret 0,5 saniyede hazırlanır, 24 saniyelik batarya taşır. En fazla 5 taret ve 5 şarj; tekrar kurulum en eski kendi taretini değiştirir. Üst üste yerleştirme şarj harcamaz.

## Hedef seçimi ve dayanıklılık

Taret geçerli hedefini tutar; E odağı önceliklidir. Hedef ölür veya menzilden çıkarsa yakın hedefe geçer. Çoklu namlular aynı hedefte birleşir; ek namlular ortak hasar bütçesi paylaşır. Menzil bonusları piksel olarak eklenir, 500 taban en fazla 800 olur.

Taret hasarı, hızı, menzili ve canı sahibinin güncel statlarından okunur. Maksimum can değişiminde can oranı korunur. Her temas eden düşman 0,5 saniyelik kendi sayacını kullanır; taret ham temasın yarısını zırh formülünden sonra alır. Düz zırh çıkarıp zayıf düşmanlara ölümsüz olma davranışı kaldırıldı.

Kale Mimarı yakın taretlerini, son darbeden 2 saniye sonra saniyede %2,5 onarır. Yakın yapılar oyuncuya en fazla saniyede %2 can yenilenmesi sağlar. Elektrikçi taretleri her üçüncü atışta yakındaki ikinci hedefe %35 ikincil yıldırım hasarı verir.

## Hasar bütçesi ve sınırlar

Taret ham gücü 14 + (seviye−1) × 0,7 + fiziksel toplam × 0,25 + temel ateş/buz toplamı × 0,10. Taret hasar çarpanı ve oyuncunun genel hasar bonusunun yarısı uygulanır. Aktif iki taretten fazlası 1/(1+0,20×(adet−2)) ortak ağ bütçesini paylaşır.

Taret hasar çarpanı en fazla 4, hız çarpanı en fazla 3; bunlara azalan getiri uygulanır. Atış aralığı en az 0,15 saniye. En fazla 4 namlu, 4 delme, 2 sekme. Ek namlu hasar bütçesi 1/(1+0,30×(adet−1)).

Taret atışları oyuncu on-hit veya can çalma üretmez; ikincil saldırıdır. Impossible hasar cezası ortak düşman hasar yolunda yalnız bir kez uygulanır. Atış sayacı simülasyon zamanı kullanır; 30/60/144 FPS aynı sonuç verir.

## Kayıt uyumu

Sınıf, evrim, kart, eşya ve yetenek düğümü kimlikleri korunur. Eski taret kitlerinin tabanları yeni atış kitine uyarlanır; nadirlik, affix ve özel ek statlar korunur. Koşu kaydı taretlerin konumunu, kalan bataryasını, can oranını, şarjları ve komut beklemesini saklar. Eski kayıtlarda bu alanlar yoksa güvenli varsayılanlar kullanılır. Aktif odak yüklemede sona erer; kalan bekleme korunur.

## Doğrulama

tools/measure_engineer_balance.py kişisel saldırı, gerçek taret kurulum/yenileme, hazırlık, şarj, batarya ve mermi/DoT yollarını birlikte ölçer. 24 build: dört yatırım aşaması × üç rota × kit/alev. Ayrıca üç kalabalık hedef senaryosu, 30/60/144 FPS kıyası ve komutsuz ölçüm var.

30 saniyelik sabit hedeflerde başlangıç kit + iki taret yaklaşık 115 DPS, Warrior 108 DPS. Saldırı rotası geç oyun kit + filo yaklaşık 5.135 DPS, aynı yatırımlı Warrior 5.370 DPS. Bunlar gelen hasar, hareket, düşen eşyalar ve artifact becerileri olmadan ölçülen örnekler; optimum build veya bütün oynanış için denge garantisi değildir.

295 test ve 79 alt test başarılı. Taret/komut, eski kit dönüşümü ve kayıt dönüşü gerçek fonksiyonlarla sınandı. Oyun dünyası, odak işareti, yetenek çubuğu ve sınıf kartı oyun çizicileriyle oluşturulup görsel olarak kontrol edildi. Tam ekran manuel oynanış testi yapılmadı.
