# 🛠️ Boxhead Yeni Özellikler Uygulama Planı

Kabul ettiğiniz Necromancer, Bard, Bumerang, Tuzaklar, Boks Eldiveni, Mimic, yeni auralar ve Taret (Engineer) geliştirmelerinin oyuna kod bazında nasıl ekleneceğinin detaylı planı aşağıdadır. 

## 1. Sınıflar (Classes)

### A. Necromancer (Ölü Çağıran)
*   **Dosya:** `logic/necromancer_logic.py` (Yeni dosya oluşturulacak).
*   **Mekanikler:** 
    *   Ölen düşmanların konumunda geçici süreyle ceset (corpse) işaretleri oluşacak.
    *   Necromancer bu cesetlerin yakınındayken onları canlandırıp iskelet minyonlara (veya zombilere) dönüştürebilecek.
    *   Ceset patlatma (Corpse Explosion) yeteneği ile alan hasarı vurabilecek.
*   **Değişecek Dosyalar:** `entities/player.py`, `ui_elements.py` (Sınıf seçimine ekleme).

### B. Bard (Ozan)
*   **Dosya:** `logic/bard_logic.py` (Yeni dosya oluşturulacak).
*   **Mekanikler:**
    *   Ritmik saldırılar. Düzenli aralıklarla etrafına müzik dalgaları (ses dalgası efekti) yayarak AoE hasarı verecek.
    *   Düşmanları Charm (büyüleme) edip kısa süreliğine birbirlerine saldırmalarını sağlama yeteneği eklenecek.
*   **Değişecek Dosyalar:** `entities/player.py`, `ui_elements.py`, `entities/enemy.py` (büyülenme / friendly fire durumu için).

### C. Monk (Keşiş / Dövüşçü)
*   **Dosya:** `logic/monk_logic.py` (Yeni dosya oluşturulacak).
*   **Mekanikler:**
    *   Çok yüksek saldırı hızı ve kombo zinciri mekaniği. Ardışık 3 vuruş sonrası 4. vuruş güçlü AoE (Şok Dalgası) oluşturur.
    *   Özel Yetenek (Q): Biriken "Chi" puanlarını harcayarak patlayıcı yetenekler kullanır.
*   **Değişecek Dosyalar:** `entities/player.py`, `ui_elements.py`

---

## 2. Silahlar ve Eşyalar

*   **Bumerang / Çakram:** 
    *   `logic/item_system.py` içerisine yeni item tabanları olarak eklenecek.
    *   `entities/projectile.py` dosyasına `is_returning` mantığı eklenecek. Bumerang maksimum menzile ulaştığında oyuncuya doğru geri dönecek ve dönüş yolunda da hasar verecek.
*   **Boks Eldiveni (Gauntlets):**
    *   `logic/item_system.py` içerisine eklenecek (`isMelee = True`).
    *   Çok kısa menzil, yüksek saldırı hızı (düşük `attackCooldown`) ve yüksek `knockback` (geriye itme) gücü parametreleri tanımlanacak. 
*   **Tuzaklar ve Mayınlar:**
    *   Yere yerleştirilebilir silahlar. `entities/ground_trap.py` adlı yeni bir yapı veya Taret sisteminin (`turret.py`) hareketsiz, düşman temasında patlayan bir varyantı olarak kodlanacak.
*   **Zincirli Tırpan (Flail / Chain Weapon):**
    *   `logic/item_system.py` içerisine yeni item tabanları olarak eklenecek.
    *   Geniş 360° alan saldırısı (AoE) yapar. Tek hedefe vuran silahlara kıyasla taban hasarı daha düşük dengelenecektir (AoE avantajını dengelemek için).
    *   Vurulan düşmanları oyuncuya doğru çeker (Reverse Knockback).

---

## 3. Düşmanlar (Enemies)

*   **Mimic:**
    *   `entities/enemy.py` içine "mimic" tipi eklenecek.
    *   Mimic başlangıçta sabit duracak ve bir sandık/kristal sprite'ı çizecek.
    *   Oyuncu belli bir mesafeye (aggro range) girdiğinde uyanıp hızla oyuncuya doğru koşan tehlikeli bir yaratığa dönüşecek.
*   **Ağ Örgücüsü (Web Weaver):**
    *   Haritada hareket ederken arkasında yapışkan ağ izi bırakır. Ağa basan oyuncu yavaşlar ve geçici süre susturulur (silenced).
*   **Parazit (Parasite):**
    *   Oyuncuya yapışarak statlarını düşüren yeni tehdit tipi.
    *   Dash veya AoE hasar ile temizlenebilir. 10 saniye temizlenmezse oyuncunun *içinde değil, yakınında* olgunlaşarak normal düşmana dönüşür.
    *   **Görsel Bildiri:** Ekranda oyuncuya parazit yapıştığını belirten net bir uyarı çıkacaktır.
*   **Savaş Kulesi (War Tower):**
    *   Hareketsiz ama çevresine sürekli mermi yağan ve diğer düşmanlara buff (hasar/hız) veren stratejik hedef.
*   **Hırsız Cin (Pickpocket Imp):**
    *   Oyuncuya sadece 1 hasar vurur ancak yüksek miktarda altın çalar.
    *   Öldürüldüğünde çalınan altının yalnızca %50'si geri düşer (Bonus altın yüzdesi bu miktarı artırmaz, yani oyuncuya kesin bir altın kaybı yaşatır).
*   **Mutant Bilim İnsanı (Mad Scientist):**
    *   **Sadece Wave 20'den sonra spawn olur.** Çevresindeki rastgele düşmanları kalıcı olarak güçlendirir ve ölünce zehir bulutu bırakır.

---

## 4. Bosslar ve Sistemler

*   **Kristal Ejderha (Crystal Dragon):**
    *   Wave 20 bossu olarak eklenecek.
    *   Hava saldırıları, kristal labirent oluşturma ve mermi cehennemi gibi fazlara sahip olacak.
*   **Kraliçe Arachne (Spider Queen):**
    *   Wave 30 bossu olarak eklenecek.
    *   Yumurtalarından çıkan örümcek yavruları **XP vermeyecek** (oyuncuların farm yapmasını engellemek için).
*   **Nemesis Sistemi:**
    *   Oyuncuyu öldüren belirli bir Elite düşman "Nemesis" olarak kaydedilecek ve sonraki run'da daha güçlü olarak oyuncunun karşısına çıkacak.
    *   Sistem sadece tek bir düşmanı Nemesis yapar (Örn: Dash atan bir düşman tipi öldürürse, tüm dash atanlar değil, sadece o spesifik düşman Nemesis olur).

---

## 5. Kartlar (Cards) ve Sinerjiler

### Yeni Kartlar
*   **Gölge Klonu:** Belirli aralıklarla oyuncunun yerine savaşan ve aggro çeken bir klon yaratır.
*   **Midas Dokunuşu:** Vuruşlarda düşmanı %5 ihtimalle altına çevirir (düşman **1.5x** hasar alır ve ölünce **5x** altın düşürür). Oyuncunun taban hasarını azaltır.
*   **Mutasyon:** Level atlandığında rastgele bir stat +%20 artarken başka bir rastgele stat -%15 azalır.
*   **Statik Zırh:** Hasar alındığında çevrede elektrik dalgası yaratır, ancak enerji kalkanını tamamen sıfırlar.
*   **Ricochet Master (Sekme Ustası):** Mermilere sekme (bounce) ve her sekmede hasar artışı ekler. Mermi hızı ve pierce düşer.
*   **Kan Bankası:** Overheal (fazla iyileşme) birikir ve aktif yetenekle patlatılarak AoE hasar ve toplu iyileşme sağlar.
*   **Kaos Alanı:** Etraftaki düşmanların zırhını ve element direncini düşüren ama oyuncunun da zırhını düşüren bir aura yaratır.
*   **Doppelganger:** Kalıcı bir ikiz minyon yaratır, ancak oyuncunun kendi hasarı **%50 azalır**.
*   **Fırın:** Düşmanlar ölünce ateş patlaması yapar. Oyuncunun diğer tüm element türlerindeki hasarlarını sıfırlar ve **sadece ateş hasarı vurabilmesini** sağlayarak (diğer elementler uygulanamaz) dengelenir.

### Yeni Sinerjiler
Tüm bu sinerjiler `synergies.json`'a işlenecek:
*   **Fırtına Birliği:** `storm_caller` + `ice_shirt` (Yıldırımlar düşmanı dondurur)
*   **Vampir İmparatorluğu:** `vampire_touch` + `undead_army` (Minyonlar lifesteal kazanır)
*   **Kaotik İnfaz:** `chaos_theory` + `executioner` (İnfaz eşiği artar, düşman patlar)
*   **Cam Kale:** `glass_cannon` + `iron_will` (Kalkan cooldown kısalır, kırılınca AoE patlama)
*   **Ölüm Kumarı:** `death_pact` + `death_wish` (Max HP 1 olur, hasar devasa artar)
*   **Element Ustası:** `fire_soul` + `frozen_time` + `poison_master` (Tüm saldırılar 3 elementi de vurur, element hasarı artar)

---

## 6. Auralar (Auras)

*   `logic/aura_system.py` dosyasına eklenecekler:
    *   **Çürüme Aurası (Decay):** `decay_aura` -> Düşük oranlı (örn: saniyede %0.5) can ve zırh eritme.
    *   **Manyetik Alan (Magnetic):** `magnetic_aura` -> Yerdeki XP ve eşyaları çekme menzilini/hızını devasa oranda artırır.
    *   **Yansıma (Reflection):** `reflection_aura` -> Gelen mermi hasarının bir kısmını engeller ve geri yansıtır.
    *   **Yıldız Düşüşü Aurası (Starfall):** Belli aralıklarla rastgele konumlara meteor düşüren, ancak oyuncuya da hasar verebilecek riskli bir aura.
*   **Entegrasyon:** `logic/game_logic.py` içindeki aura döngüsüne bu özel auraların (eşya çekme, zırh eritme, meteor düşme) mantığı işlenecek.

---

## 7. Ekstra Sistemler ve Geliştirmeler

*   **Kart Evrimi (Card Evolution):**
    *   Aynı pasif kart tekrar alındığında daha güçlü bir versiyonuna (Gelişmiş -> Efsanevi) evrimleşir.
*   **Silah Mirası (Weapon Legacy):**
    *   Kristal yükseltmesi (Crystal Upgrade) olarak eklenecek. Başlangıç silahının nadirliğini (Normal -> Magic -> Rare) artırarak oyuna başlama imkanı sunar.
*   **Engineer (Taret Sınıfı) UI Geliştirmesi ve Dengeleme:**
    *   **Taret Bilgi Ekranı (Turret UI):** Taretlerin güncel istatistikleri oyuncuya anlık olarak gösterilecek.
    *   **Dengeleme:** Taretlerin hasar çarpanları, mermi sayıları ve ateşleme oranları yeniden ölçeklendirilecek.
