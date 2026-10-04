# Envanter, sekmeler ve atölye — 4 Ekim 2026

Aktif kaynakta uygulanmıştır; masaüstü kurulumuna aktarılmadı, yayın yapılmadı.

## Kullanım

Envanterde eşyanın ikonunu veya isim alanını sol tuşla tutup uygun kuşanma yuvasına bırak: eşya kuşanılır, eski eşya çantaya döner. Kuşanılan eşyayı çanta alanına bırak: çıkarılır. Eşyayı Atölye alanına bırak: aynı eşya craft hedefi olur; kopyası üretilmez. Yanlış yuva veya dışarı bırakma eşyayı değiştirmez. ESC sürüklemeyi iptal eder. Mevcut Giy/Sat/Craft ve sağ tıkla çıkar kısayolları korunur.

Çanta 3×4 görünür kart kullanır. Filtreler, geliş sırası/isim/nadirlik sıralaması, tekerlekle sayfalama, büyük ekranda kısa eşya özellikleri ve kuşanılanla tooltip kıyaslaması bulunur. Sıralama yalnız görünümü değiştirir.

Bütün sekmeler ortak ekran sınırlarına sığan gotik menüyü kullanır. 1–7 sekme kısayolu vardır; yetenek arama kutusunda yazarken devreye girmez. Kahraman stat satırları küçük ekran zorluk satırına taşmaz. Yetenek ağacının arama/zoom/pan özellikleri korunur. Yükseliş başlığı ve açılmış ağaç çizimi düzeltildi. Kervan listesi ekran boyutundan türetilir, tekerlekle sayfalanır; fiyat ve sende bulunan adet birlikte gösterilir. Aura sayfaları 4 kart içerir; kapasite, çıkar/kuşan/dolu durumları ve tam fiyat gösterilir, tekerlekle sayfa değişir. Sinerjiler aktif ve tamamlanmaya yakın olanları önce gösterir; sahip olunan kart oranı ve eksik kart isimleri görünür.

## Atölye

Orblar ve Tarifler ayrı seçimlerdir. Seçmek kaynak tüketmez; Uygula işlemi yapar. Başarısız işlemler altın/orb tüketmez. Hedef eşya ikonu, okunur stat isimleri, prefix/suffix yuva sayısı, işlem açıklaması ve maliyet gösterilir.

Seçili özellik tarifi, özelliği kesin değerle ekler. Eşya başına tek tarif özelliği vardır. Tarif değiştirildiğinde doğal özellikler korunur. Doğal aynı özellik veya dolu hedef tarafına yazılmaz. Normal eşya başarılı tarifte Magic olur. Mühürlü ve artık oyuncunun sahip olmadığı eşya işlenemez. Başlangıç tarifi T3/50 altın, Wave 10 itibarıyla T2/300, Wave 20 itibarıyla T1/1200. Bu fiyatlar ilk tasarım değerleridir; oynayarak ekonomi ölçümü yapılmalıdır. Tarif işareti gerçek kaydet/yükle testinden geçti.

## Doğrulama ve kalan kapsam

356 test + 79 alt test geçti. Syntax/import kontrolü başarılı, diff boşluk hatası yok. 1280×720 ve 1600×1000 gerçek oyun çizicisiyle bütün sekmeler; aura/yükseliş kilitli-açık durumları, sinerji ilerlemesi, sürükleme ve iki craft modu çizdirilip görsel kontrol edildi. Gerçek kayıtlar kullanılmadı. İnsan tarafından fareyle oynanış kabulü henüz yapılmadı.

Bu değişiklik tam ARPG matematik/loot dönüşümü değildir. Stat birimleri (özellikle ağaçtaki düz zırh delme ile oransal tüketici), savunma/hasar eğrileri, eşya seviyesiyle affix tier havuzları, doğal affixlerin silah uyumluluğu, malzeme/söküm ekonomisi, koruma/aktarma gibi ileri craft katmanları ayrıca tamamlanmalıdır. Tarifler kumarın yanına kontrollü ilk yolu ekler; PoE derinliğinin tamamlandığı iddia edilmez. B-W04 ve ağacın konseptle birebir görsel yoğunluk kabulü açık kalır.


## Yeni görsel tasarım
Taş/bronze gotik salon zemini, 2×3 kuşanma yuvaları, 4×3 eşya vitrini, sınıf portresi ve mühür ikonları uygulandı. Eski filtre buton dizisi kaldırıldı: isim araması, nadirlik/tür açılır seçimleri, sıralama ve temizleme tek araç çubuğunda. Orblar varsayılan görünür; tür filtresinden seçilebilir. Açık menü eşya sürüklemesini engeller. 357 test + 79 alt test geçti. Yeni galeri outputs/gotik_sekmeler_yeni_tasarim.md (box-2 çalışma alanı).
