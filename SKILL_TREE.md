# Yeni ana yetenek ağacı — 4 Ekim 2026

896 bağlı düğüm, dokuz sınıf başlangıcı, ikonlu gotik arayüz, sınıf içi alternatif halkalar ve komşu sınıf ortak yolları uygulanmıştır. İlk büyük seçim 4 SP. Ana bütçe 100 SP; seviye başına 2 SP, seviye 51 itibarıyla üst sınır. Uzmanlık puanları ayrıdır.

12 merkez özelliği özel çıkmaz yolların sonunda bulunur. Her sınıftan ilk erişim 19 SP, ikinci merkeze minimum ek yatırım 15 SP. Merkezler birbirine bağlı değildir. Zehir dönüşümü ve saf alev birbirini dışlar; diğer birleşimler puan bedeliyle mümkündür.

Merkez özellikleri: doğrudan hasarın yarısını dört saniyelik zehre dönüştürme; +%200 ateş ve diğer hasarları kapatma; tek mermiyle çift hasar; kritik yerine sabit hasar; geniş alan/yavaş saldırı; uzun erişim/düşük can; kalabalık fakat zayıf yardımcılar; hızlı fakat kırılgan yardımcılar; can çalma fakat yenilenmeme; kalkan/düşük can; hızlı kaçınma/zırhsızlık; zırh/can fakat yavaşlık ve kaçınmasızlık. Sayısal denge kullanıcı denemeleriyle değiştirilebilir.

Eski ağaç tahsisleri sürüm geçişinde iade edilip sınıf başlangıcı yeniden kurulur. Kaydet-yükle tekrarında çift iade engellenmiştir. Gerçek kullanıcı kaydı değiştirilmedi.

Görsel durum: referans bağlayıcı hedeftir. Mevcut çizim önceki seyrek ara sürümden daha yoğun olsa da referansın birebir son görünümü değildir; uzun bağlantılar, dış boşluklar ve ikon çeşitliliğinde görsel son düzenleme gerekir. Genel görünüm ve 1280/1600 yakın planlar gerçek oyun çizicisiyle üretilmiştir.

Doğrulama: 339 test + 79 alt test geçti. Topoloji ölçümünde 44 birim altındaki düğüm çakışması yok. Normal/sıfır meta/3 seed/9 sınıf/2 tercih ile 54 otomatik erken koşunun 42 tanesi Wave 5'i geçti. Kontrolcü insan oynanışını temsil etmez; B-W04 açık kalır. Normal erken düşman havuzu, sayı/tempo ve kamikaze uyarısı düzenlendi. Bazı hasar kaynakları ölçümde unknown kalabilir.

Kaynak değişiklikleri yayımlanmadı, masaüstü kurulumu güncellenmedi. Sürüm dosyası, paketleme dosyaları ve gerçek kayıtlar korunmuştur.

Ağaç verisi tools/generate_skill_tree.py ile tools/tree_clusters.py üzerinden üretilir; JSON elle değiştirilmez. tools/inspect_new_tree.py puan yollarını, tools/render_new_tree.py gerçek arayüzü, tools/measure_early_runs.py erken koşuları doğrular.
