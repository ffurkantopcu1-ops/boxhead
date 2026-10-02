# Boss ve başlangıç rotaları — v1.23.0

Öncelik yeni boss ve her sınıfta başlangıçtan itibaren farklı build seçimleri. Minyon/taret dengesi bu sürümün kapsamına alınmadı; sonraki paket olarak kaldı.

## Echelion: Küllerin Muhafızı

Eski bossun kalkan/sütun döngüsü ve kare başına biriken mermi desenleri kaldırıldı. Yeni muhafız, yönünü kilitleyen dört okunaklı saldırı kullanır. Sürekli hasar verilebilir; bekleme fazında yaklaşır, uyarı sırasında yönünü oyuncuya döndürerek takip etmez.

| Saldırı | Uyarı | Karşılık verme süresi | Kaçış yolu |
|---|---:|---:|---|
| Kül Biçişi | 1,00 sn | 1,80 sn | 120 derecelik sektörün yanına/arkasına geç |
| Kırık Mızrak | 1,15 sn | 2,10 sn | Kilitlenen 90 px genişlikli hücum hattından yana çık |
| Köz Çemberi | 1,20 sn | 2,70 sn | 120 derecelik açık koridor; yakın iç bölge de güvenli |
| Yarık Darbesi | 1,35 sn | 2,00 sn | 130–330 px halka dışına veya içine geç |

Boss yarıçapı 55 px. Çember mermileri 150 px dışarıda doğar, 180 px/sn gider ve 2 saniyede söner. Normal dalga 10 ham saldırı hasarı yaklaşık 25–39 aralığında; oyuncunun savunması uygulanır. Can bütçesi 2600 × 1,10^dalga × zorluk çarpanı; dalga 10 Normal yaklaşık 6.744 can. Bu tek başına karşılaşmanın tamamı için süre garantisi değildir.

60 saniyelik düşük can ölçümünde 30/60/144 FPS için 17 saldırı ve en fazla 7 mermi görüldü. Yaklaşık 36,9 saniye toparlanma halinde geçti. Sabit hedefte hasar alımı ölçüm için kapatıldı; bu sonuç oynanışta hayatta kalma garantisi değildir.


Kimlik boss ve ödül/kayıt sözleşmeleri korunur. Boss mermileri öldüğünde temizlenir; havuzda başka sahip için yeniden kullanılan mermi silinmez. Mermi çarpışması hareket parçası boyunca denetlenir.
