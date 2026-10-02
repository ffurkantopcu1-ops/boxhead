# Ana pasif ağaç ve uzmanlık ağacı

Ana ağaç tools/generate_skill_tree.py tarafından üretilir. Veri, görünüm ve üretici aynı yapıyı tarif eder: 211 düğüm; dokuz ayrı sınıf başlangıcı; her sınıfta ana yol, iki uzmanlık dalı ve iki keystone. data/skill_tree.json elle değiştirilmez.

Sınıf başlangıcının yalnız kendi ilk düğümüyle bağlantısı vardır. Ortak geçişler 6 puanlık sınıf ustalığı noktasından başlar. Komşu ustalığa ulaşmak dört ortak düğüm ve hedef ustalık için toplam 5 ek puan ister. Kendi keystone'una en kısa yol 12 puan; komşu sınıfın keystone'una en kısa yol 17 puandır. Yabancı başlangıç düğümünü tahsis etmek gerekmez; o başlangıç yine kilitlidir.

Köprüler iki sınıfta anlamlı olan fiziksel/kritik, komuta, alan kontrolü, elemental hasar, yenilenme ve çeviklik gibi temalar taşır. Ekonomi kolu ayrıca yatırım gerektirir. Keystone'ların açık bedelleri vardır; açıklamalar üretici tarafından statlardan oluşturulur.

Önceki 172 düğümlük sürümün düğüm kimlikleri korunur; kayıtlı tahsisler kaybolmaz. Bazı açıklamalar, keystone bedelleri ve bir ileri ustalık düğümünün değeri değişmiştir. Çok daha büyük ağaç, ana puan sınırı ve altınla iade eğrisi bu ilk bağlantı düzeltmesinin kapsamı değildir.

Sınıf koşu boyunca sabittir. Silah değiştirmek başlangıç düğümünü veya sınıf kimliğini değiştirmez. Yabancı pasif dallara köprülerden girilir.

Uzmanlık (ascendancy) ağacı ayrı kalır: evrim seçiminden sonra açılır ve kendi puan para birimini kullanır. İki ağacın tahsisleri koşu kaydında saklanır; kalıcı meta geliştirmelerine dönüşmez.

Testler bütün düğümlerin bağlı olduğunu, yabancı başlangıçlara basmadan keystone'lara erişildiğini, yabancı keystone'un daha pahalı olduğunu ve üreticinin kayıtlı JSON'u birebir ürettiğini denetler.
