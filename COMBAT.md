# Hasar ve iyileşme sözleşmesi — ilk aşama

Bu sürüm ortak hasar davranışını ve yanlış çalışan bonusları düzeltir. Temas hasarı, tehlikeler, hareket hızı, tüm silah ailelerinin ölçeklemesi ve geniş ARPG dengelemesi sonraki aşamalardır.

- Warrior, Ninja ve Bloodwalker yakın dövüş fiziksel bonusunu fiziksel vuruşa uygular. DoT bonusu zehir ve yanmaya uygulanır; doğrudan vuruşa eklenmez. Fiziksel bonus elemental DoT'u büyütmez.
- Boss hasarı bonusu Abyssal Lord, Kristal Ejderha ve Arachne için geçerlidir. Çevresel hasar oyuncunun boss bonusunu kullanmaz.
- Yansıyan hasar yeni yansıma, vuruş tetikleyicisi veya can çalma üretmez. Kritik/yıldırım gibi tetikleyicilerin genel ikinci hasar sınıflandırması henüz ayrıca yapılmadı.
- Can çalma, oyuncunun uygun doğrudan vuruşunun düşman zırhı ve kalkanından sonraki hasarından hesaplanır. DoT, yansıma, tuzaklar ve çevresel hasar can çalmaz. Ölümcül vuruşun kalan canı aşan kısmı vuruş hasarı içinde kalır.
- Uygun çoklu vuruşlar aynı can çalma havuzunu besler. Eski tek hedef / 0,2 saniye kilidi kaldırıldı. Havuz tavanı maksimum canın %20'sidir; dolu can veya ölüm havuzu siler.
- Başlangıç denge değeri olarak normal sınıflarda can çalma iyileşme hızı saniyede maksimum canın %10'u, Bloodwalker'da %20'sidir. Bunlar Boxhead'e özgü ilk değerlerdir; bütün ARPG'lerde ortak bir standart olduğu iddia edilmez. 30/60/144 FPS testleri aynı iyileşmeyi doğrular.
- Kalkan tam sıfıra indiğinde de kırılma tetiklenir. Sıfır/negatif hasar kalkanı veya dokunulmazlık süresini değiştirmez.

Yansıma, can çalma ve fiziksel/DoT ayrımı tests/test_combat_regressions.py içinde gerçek hasar ve saldırı fonksiyonlarıyla sınanır. Tam ekran oynanış testi otomatik olarak yapılmaz.
