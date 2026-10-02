# Hasar ve iyileşme sözleşmesi — ilk aşama

İlk aşama ortak hasar davranışını ve yanlış çalışan bonusları düzeltir. İkinci aşama aşağıda temas, sürekli hasar, savunma ve hareketi düzenler. Silah ailelerinin bütün ölçekleme/tetikleme yolları, minyonlar ve boss değerleri ayrı paketlerde gerçek build ölçümleriyle ele alınır.

- Warrior, Ninja ve Bloodwalker yakın dövüş fiziksel bonusunu fiziksel vuruşa uygular. DoT bonusu zehir ve yanmaya uygulanır; doğrudan vuruşa eklenmez. Fiziksel bonus elemental DoT'u büyütmez.
- Boss hasarı bonusu Abyssal Lord, Kristal Ejderha ve Arachne için geçerlidir. Çevresel hasar oyuncunun boss bonusunu kullanmaz.
- Yansıyan hasar yeni yansıma, vuruş tetikleyicisi veya can çalma üretmez. Üçüncü aşamada diğer ikincil hasarlar da aynı tetikleme ayrımını kullanır.
- Can çalma, oyuncunun uygun doğrudan vuruşunun düşman zırhı ve kalkanından sonraki hasarından hesaplanır. DoT, yansıma, tuzaklar ve çevresel hasar can çalmaz. Üçüncü aşamadan itibaren ölümcül vuruşun kalan canı aşan kısmı can çalma veya hasar kaydı üretmez.
- Uygun çoklu vuruşlar aynı can çalma havuzunu besler. Eski tek hedef / 0,2 saniye kilidi kaldırıldı. Havuz tavanı maksimum canın %20'sidir; dolu can veya ölüm havuzu siler.
- Başlangıç denge değeri olarak normal sınıflarda can çalma iyileşme hızı saniyede maksimum canın %10'u, Bloodwalker'da %20'sidir. Bunlar Boxhead'e özgü ilk değerlerdir; bütün ARPG'lerde ortak bir standart olduğu iddia edilmez. 30/60/144 FPS testleri aynı iyileşmeyi doğrular.
- Kalkan tam sıfıra indiğinde de kırılma tetiklenir. Sıfır/negatif hasar kalkanı veya dokunulmazlık süresini değiştirmez.

Yansıma, can çalma ve fiziksel/DoT ayrımı tests/test_combat_regressions.py içinde gerçek hasar ve saldırı fonksiyonlarıyla sınanır. Tam ekran oynanış testi otomatik olarak yapılmaz.

## İkinci aşama — v1.21.0

- Temas düşman başına 0,5 saniyede bir tam vuruştur. Yeni düşmanın sayacı 0,5 saniyeden başlar; menzilden çıkmak kalan süreyi sıfırlamaz. Uzun temasın ham DPS bütçesi önceki 2 × düşman hasarıdır. Her vuruş bir kaçınma denemesi ve bir on-hit üretir; FPS başına tetikleme yoktur. Çoklu düşman global vuruş dokunulmazlığını aşar; dash temas vuruşlarını engeller.
- Vuruş zırh çarpanı max(0,25; 100/(100+max(-75,zırh))) olur. Zırh en fazla %75 azaltır; aşırı negatif değer en fazla 4 kat hasara dönüşür. Impossible mevcut zırh yarılama kuralını korur. Kaçınma tüketim tavanı %50 ile hesaplanan stat tavanına eşitlendi.
- Oyuncu ateş/zehir/hostile kara delik/sessizlik alanı sürekli hasarı is_dot=True ile alır. Sürekli hasar kaçınma, normal vuruş dokunulmazlığı ve dash üzerinden iptal olmaz; fiziksel zırhı kullanmaz. Genel alınan hasar çarpanı ve enerji kalkanı kullanılır; diken, yansıma ve vuruş başına XP üretmez. Genel dokunulmazlık hâlâ geçerlidir.
- Çevresel ateş 5 DPS, yıldırım 1 saniyede 20 ham hasar bütçesini korur. Ateşin eski dokunulmazlık nedeniyle gerçekte işlememesi düzeltildi. Son kısmi süre ve yıldırım sayacının kalanı kaybolmaz. Çevresel yıldırım oyuncu saldırısı olarak sınıflanmaz; boss bonusu/can çalma üretmez.
- Oyuncunun Singularity bulutu sahibi çekmez veya yaralamaz; normal düşmanları 60px/s ile toplar, bossları çekmez. Düşman büyücünün bulutu is_hostile=True ile oyuncuyu çeker ve sürekli hasar verir.
- Alınan hasar istatistiği gerçek emilen kalkan + gerçekleşen can hasarıdır; ölümde fazla hasarı saymaz. Elit can çalma da bu gerçekleşen değeri kullanır.
- Yenilenme ve kalkan bekleme süresi aynı yardımcı fonksiyonda ölçülür. Beklemenin kare ortasında biten kısmı doğru hesaplanır; ölü oyuncu yenilenme ile canlanmaz. Can çalma hızları ilk aşamadaki %10/%20 bütçelerini korur.
- Kalıcı hız 7,5 üzerinde azalan getiriyle en fazla 9 (540px/s); geçici bonuslarla normal hareket en fazla 12 (720px/s). Dash ayrı 3,5 çarpanıdır. Oyuncuda en güçlü yavaşlatma geçerlidir, minimum hareket oranı %20; stun hareketi tamamen durdurabilir. Yavaşlatma hız tavanından sonra uygulanır, aşırı haste onu iptal etmez.

### Ölçüm ve sınırlar

tools/measure_combat_balance.py gerçek sınıf saldırısı, mermi, bulut, DoT, hasar alma ve iyileşme fonksiyonlarını kullanır. Dokuz sınıf × iki ağaç/evrim rotası × dört yatırım senaryosu = 72 senaryo. Başlangıç, 19 SP/T2, 49 SP/T1 ve son aşamaya Rare affixler + dört sınıf kartı + beş ascendancy puanı eklenen senaryolar eşit bütçeyle karşılaştırılır.

Tek hedef ve altı yakın hedef ölçülür. Engineer/Beastmaster hasarı boş bırakılır; minyon/taret/aktif yetenek kıyaslaması bu araçta henüz yoktur. Savunma baskısı altı ölümsüz sabit saldırganla ölçülür; leech ve saldırıların can bedeli ölçülen ortalama hızla beslenir. Bu sabit hedef/ortalama modelidir, tam oynanış veya optimum build ispatı değildir. Dalga/seviye/eşya eşleştirmeleri varsayımsal senaryolardır.

Testler 30/60/144 FPS'te temas/diken, ateş, yıldırım, kalkan gecikmesi ve hostile bulut süresini eşit sonuçla doğrular. Ayrıca aynı yatırımlı savaşçıda hasar karşılığında dayanıklılık kaybını ve geç oyun Bloodwalker'ın altı sürekli temasa karşı sınırsız yaşamamasını denetler. Tam ekran manuel oynanış testi yapılmadı.

## Üçüncü aşama — v1.22.0

- Birincil vuruş, ikincil hasar, DoT ve yansıma ayrı sınıflanır. İkincil yıldırım/patlama yeni on-hit zinciri veya can çalma üretmez. Storm Caller tek vuruş eşiğinde de sonlu kalır.
- Can çalma ve verilen hasar kaydı gerçekleşen can kaybını kullanır; kalan canı aşan bölüm sayılmaz.
- Kritik temel çarpanı 2; ek kritik bonusu azalan getirili ve en fazla 1,5 olur (toplam 3,5). Saldırı beklemesi en az 60 ms.
- Ateş sıçraması mermi başına bir kez, yakın dövüşte hedef başına bir kez uygulanır. İkincil ateş miktarı doğrudan ateşin %50'sidir. Bulut DoT çarpanı doğrudan patlamaya taşınmaz.
- Ek mermilerin ortak hasar bütçesi 1/(1+0,25*(adet-1)); en fazla 6 mermi, 6 delme, 4 sekme. Bumerang dönüş hasarı %60.
- Hızlı silahların ek hasar etkinliği temel bekleme/350 oranıdır, %20–100 arasında. Silahın kendi elemental tabanı korunur; ek fiziksel/elemental bonus ve sınıf düz hasarı bu etkinlikle ölçeklenir. Hızlı eldiven tabanları da kademelerine göre dengelendi.
- Alev silahı, bomba ve yakın dövüş aileleri sınıf değişimlerinde gerçek silah davranışını kullanır. Mayın fiziksel/elemental yükünü ve kritiği taşır; hazırlık bedeli karşılığında mayın çarpanı 6.
- Ölüm patlaması düşman maksimum canının %30'u ile oyuncunun ölçeklenmiş ham hasarının 4 katından küçük olanı kullanır; zincir derinliği 2 kalır.
- Saldırı sayacı simülasyon zamanını kullanır; boşta bir atıştan fazla birikmez ve tek güncellemede en fazla 4 telafi atışı olur. Mermiler hareket segmenti boyunca çarpışır; hızlı mermiler kareler arasında hedef atlamaz.

### Üçüncü aşama ölçümleri

72 eşit yatırım senaryosu ve 108 sınıf/silah birleşimi data/combat_balance_1.22.0.json içinde saklanır. Engineer alev silahı ölçülür, taret katkısı dahil değildir; Beastmaster çağrıları ve aktif beceriler sonraki pakettedir. Sabit hedef ölçümü hareketli oyun, boss telegraphları veya bütün olası buildler için denge garantisi değildir. 30/60/144 FPS saldırı ve mermi davranışı regresyonlarla denetlenir. Tam ekran manuel oynanış testi yapılmadı.

## Saha Mühendisi — v1.24.0

Taret kurulum, komut, canlı stat, hasar ve kayıt sözleşmesi ENGINEER_DESIGN.md içinde. Gerçek toplam hasar ölçümleri data/engineer_balance_1.24.0.json içinde. Minyon sistemi ayrı paket olarak kalır.
