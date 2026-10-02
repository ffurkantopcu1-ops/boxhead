# Ana pasif ağaç ve uzmanlık ağacı

Ana ağaç tools/generate_skill_tree.py tarafından üretilir: 319 düğüm, dokuz ayrı sınıf başlangıcı, üç erken rota, iki üst uzmanlık dalı ve iki keystone. JSON elle değiştirilmez.

Her sınıf ilk puanından itibaren üç farklı düğüm seçebilir. Saldırı rotası mevcut main kimliklerini kullanır; dayanıklılık ve yardımcı mekanik rotaları early1/early2 kimliklerini taşır. Her rota beş küçük düğümden sonra altıncı puanda kendi ustalığına ulaşır. Dayanıklılık ustalığı path1, yardımcı ustalık path2 girişine bağlanır. Üçüncü derinlikte yatay bağlantılar yön değiştirmeyi sağlar; derinliği veya puan bedelini atlatmaz.

Saldırı rotasındaki altıncı puan ustalığı ortak köprülerin girişidir. Diğer rotalardan bu kavşağa bağlı dallar üzerinden gidilir. Komşu sınıfa geçmek dört ortak düğüm ve hedef ustalık için toplam 5 ek puan ister. Kendi keystone'una en kısa yol 12, yabancı keystone'a 17 puan olmaya devam eder.

27 erken rota senaryosu ve 72 geç oyun senaryosu tools/measure_boss_tree_balance.py ile gerçek savaş fonksiyonlarından ölçülür. Minyon/taret ve aktif beceri hasarı bu ölçümlere dahil değildir. Başlangıç bonusları saldırı, dayanıklılık ve konumlandırma arasında farklı bütçeler taşır. Keystone bedelleri korunur.

Önceki yayımlanan 211 düğümün bütün kimlikleri korunur; kayıtlı tahsisler ve SP kaybolmaz. Ana rota isimleri ve bonusları yeniden dengelenmiştir; eski tahsisler yeni değerleri kullanır. Sınıf kimliği ve başlangıcı silah değişiminde değişmez. Sınıflar arası köprüler iki sınıfta kullanılabilen ortak build temalarını taşır.

Uzmanlık (ascendancy) ayrı ağaç ve puan para birimidir; evrim seçiminden sonra açılır. Tahsisler koşu kaydında saklanır.

Testler ilk üç seçeneği, beş adımın her rotada oynanabilirliğini, farklı ustalık girişlerini, bütün ağacın bağlantısını, keystone bedellerini, kimlikleri ve üreticinin JSON ile eşitliğini doğrular. Gerçek oyun çizicisiyle yakınlaştırılmış ağaç ve tooltip görselleri kontrol edildi.
