# Hasar ve iyileşme sözleşmesi — ilk aşama

İlk aşama ortak hasar davranışını ve yanlış çalışan bonusları düzeltir. İkinci aşama aşağıda temas, sürekli hasar, savunma ve hareketi düzenler. Silah ailelerinin bütün ölçekleme/tetikleme yolları, minyonlar ve boss değerleri ayrı paketlerde gerçek build ölçümleriyle ele alınır.

- Warrior, Ninja ve Bloodwalker yakın dövüş fiziksel bonusunu fiziksel vuruşa uygular. DoT bonusu zehir ve yanmaya uygulanır; doğrudan vuruşa eklenmez. Fiziksel bonus elemental DoT'u büyütmez.
- Boss hasarı bonusu Abyssal Lord, Kristal Ejderha ve Arachne için geçerlidir. Çevresel hasar oyuncunun boss bonusunu kullanmaz.
- Yansıyan hasar yeni yansıma, vuruş tetikleyicisi veya can çalma üretmez. Kritik/yıldırım gibi tetikleyicilerin genel ikinci hasar sınıflandırması henüz ayrıca yapılmadı.
- Can çalma, oyuncunun uygun doğrudan vuruşunun düşman zırhı ve kalkanından sonraki hasarından hesaplanır. DoT, yansıma, tuzaklar ve çevresel hasar can çalmaz. Ölümcül vuruşun kalan canı aşan kısmı vuruş hasarı içinde kalır.
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
