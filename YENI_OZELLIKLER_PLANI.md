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

---

## 3. Düşmanlar (Enemies)

*   **Mimic:**
    *   `entities/enemy.py` içine "mimic" tipi eklenecek.
    *   Mimic başlangıçta sabit duracak ve bir sandık/kristal sprite'ı çizecek.
    *   Oyuncu belli bir mesafeye (aggro range) girdiğinde uyanıp hızla oyuncuya doğru koşan tehlikeli bir yaratığa dönüşecek.

---

## 4. Auralar (Auras)

*   `logic/aura_system.py` dosyasına eklenecekler:
    *   **Çürüme Aurası (Decay):** `decay_aura` -> Düşük oranlı (örn: saniyede %0.5) can ve zırh eritme.
    *   **Manyetik Alan (Magnetic):** `magnetic_aura` -> Yerdeki XP ve eşyaları çekme menzilini/hızını devasa oranda artırır.
    *   **Yansıma (Reflection):** `reflection_aura` -> Gelen mermi hasarının bir kısmını engeller ve geri yansıtır.
*   **Entegrasyon:** `logic/game_logic.py` içindeki aura döngüsüne bu özel auraların (eşya çekme, zırh eritme) mantığı işlenecek.

---

## 5. Engineer (Taret Sınıfı) UI Geliştirmesi ve Dengeleme

*   **Taret Bilgi Ekranı (Turret UI):**
    *   Minyon istatistiklerinin (hasar, hız vb.) ekranda gösterildiği gibi, Engineer sınıfı için de benzer bir arayüz paneli oluşturulacak.
    *   Bu ekranda Taretlerin; **Hasar (Damage), Mermi Sayısı (Projectiles), Sekme (Bounce), Delip Geçme (Pierce)** ve **Atış Hızı (Fire Rate)** gibi güncel istatistikleri oyuncuya anlık olarak gösterilecek.
    *   **Değişecek Dosyalar:** `ui_elements.py` ve `logic/game_logic.py` içerisinde HUD çizim alanları.
*   **Engineer Dengelemesi (Balancing):**
    *   Mevcut sistemde taretlerin yetersiz kaldığı veya fazla güçlendiği durumlar incelenip, taretlerin hasar çarpanları (`turretDmg`), mermi sayısı kapasiteleri ve ateşleme oranları (`turretRate`) yeniden ölçeklendirilecek.
    *   Ayrıca yeni eklenen özellikler ve silahlarla birlikte uyumlu çalışması için Engineer'in başlangıç veya gelişim eğrisinde optimizasyon yapılacak.
