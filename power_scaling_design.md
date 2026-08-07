# BOXHEAD RPG: İki Aşamalı Güçlenme Mekaniği Tasarımı

Bu doküman, Boxhead tabanlı RPG projesi için Erken Oyun (Öz Sistemi) ve Geç Oyun (Aura Sistemi) güçlenme mekaniklerinin detaylı tasarımını içerir.

---

## 1. ERKEN OYUN: RÜN / ÖZ (ESSENCE) SİSTEMİ

**Kilit Açılma Şartı:** Wave 10 Boss'unun ilk kez kesilmesi.
**Amacı:** Oyuncunun Skill Tree ile Late Game Auralar arasındaki stat boşluğunu doldurmasını, "Grind" hissini tatmin edici kalıcı küçük ödüllerle desteklemesini sağlamak.

### Mekanik Detayları
*   **Düşme Kaynağı (Drop):** Sadece Bosslardan (%100 şans) ve Elit yaratıklardan (%15 şans) düşer.
*   **İşlev:** Toplanan "Öz"ler (Essence), karakterin en temel statlarını (Base Stats) **kalıcı** olarak artırır.
*   **Öz Çeşitleri:**
    *   *Essence of Vitality:* +2 Base Max HP
    *   *Essence of Might:* +1 Base Fiziksel Hasar
    *   *Essence of Magic:* +1 Base Büyü Hasarı
    *   *Essence of Swiftness:* +0.5 Base Hareket Hızı
    *   *Essence of Fortitude:* +1 Base Zırh

---

## 2. GEÇ OYUN: AURA SİSTEMİ (LATE GAME SCALING)

**Kilit Açılma Şartı:** Genellikle 100.000 Altın (veya daha fazla) biriktirebilecek seviyeye gelmek.
**Amacı:** Yüksek wave'lerdeki logaritmik düşman güçlenmesine karşı oyuncuya devasa çarpanlar (multiplier) veya oyun stilini kökten değiştiren pasif güçler sunmak.

### Aura Kuralları ve Limit Mekaniği
*   **Satın Alma:** Auralar, özel bir "Aura Shrine" (Aura Tapınağı) sekmesinden yüksek miktarda altın (örn. 100k - 250k) karşılığı kilitleri açılarak elde edilir.
*   **Limit Sistemi (Çok Önemli):** Karakterin doğuştan **Sadece 1 Aktif Aura Sınırı** vardır.
*   **Sınırı Artırmak (Orb Eşyası):** Oyunda aura sınırını artırmanın TEK YOLU, özel olarak düşen nadir eşya tipi olan **"Orb"** (Küre) kuşanmaktır.
    *   Oyunun eşya havuzundaki `[Aura Limit +1]` veya efsanevi orblardaki `[Aura Limit +2]` affix'leri (özellikleri) **sadece ve sadece ORB sınıfı eşyalarda** çıkabilir. Kılıçta veya zırhta çıkmaz. Bu, Orb eşyalarını endgame'in en değerli parçası yapar.

---

### AURA LİSTESİ (40 Adet - Kategorize Edilmiş)

#### 🛡️ Tank / Hayatta Kalma (Survival)
1. **Aura of the Mountain:** +500 Max HP, -%10 Hareket Hızı.
2. **Iron Maiden:** Alınan fiziksel hasarın %30'unu düşmana yansıtır.
3. **Titan's Skin:** +150 Flat Zırh.
4. **Juggernaut:** Yavaşlatma (Slow) etkilerine karşı bağışıklık, saniyede +10 HP Yenilenme.
5. **Phoenix Ash:** Öldüğünde %50 HP ile diril (300sn bekleme süresi).
6. **Vanguard:** Karşıdan (yüzün dönükken) alınan hasarlara karşı %20 Hasar Azaltma.
7. **Blood Pact:** +%20 Can Çalma (Lifesteal), fakat dışarıdan (pot vb.) alınan iyileştirmeler %50 azalır.
8. **Unbreakable:** +1000 Max HP, ancak karakter "Dodge" (Kaçınma) yapamaz.

#### 💀 Minyon / Summoner (Necromancer)
9. **Beastmaster's Command:** Minyon Hasarı +%50.
10. **Swarm Leader:** +2 Maksimum Minyon Sınırı.
11. **Necromancer's Greed:** Minyonlar öldüğünde kendi hasarlarının %200'ü kadar AoE hasar vurarak patlar.
12. **Pack Mentality:** Karakter, hayatta olan her minyonu için +%5 Total Hasar kazanır.
13. **Broodmother:** Minyonların saldırı hızı (Attack Speed) +%40 artar.
14. **Soul Link:** Karakterin aldığı hasarın %30'u eşit olarak minyonlara dağıtılır.
15. **Frenzy Aura:** Minyonlar +%50 Hareket Hızı kazanır.
16. **Vampiric Pets:** Minyonların verdiği hasarın %10'u karakteri iyileştirir.

#### ⚔️ Glass Cannon / Saf Hasar
17. **Assassin's Creed:** +%50 Kritik Hasar (Crit Damage), ancak -200 Max HP.
18. **Berserker's Rage:** +%40 Fiziksel Hasar, ancak Karakter +%20 Daha Fazla Hasar Alır.
19. **Sniper's Focus:** Karakter 2 saniye hareketsiz kalırsa Ranged (Menzilli) vuruşlar +100 Flat Hasar kazanır.
20. **Lethality:** Karakterin saldırıları düşman zırhının %50'sini yok sayar (Armor Penetration).
21. **Executioner:** Canı %20'nin altında olan düşmanlara %200 hasar vurulur.
22. **Flurry:** +%30 Saldırı Hızı.
23. **Duelist:** Yakın dövüş silahlarıyla vurulan her isabetli vuruş +50 Flat Fiziksel Hasar ekler.
24. **Death's Dance:** Karakterin aldığı hasarın %30'u anında vurulmaz, bunun yerine 3 saniye içinde kanama (DoT) olarak alınır.

#### ⚡ Elemental / Büyücü (Magic)
25. **Inferno:** Tüm saldırılar düşmana Burn (Saniyede 50 ateş hasarı) uygular.
26. **Frostbite:** Tüm saldırılar düşmanları %30 yavaşlatır (Chilled).
27. **Stormbringer:** Karakterin saldırıları %20 ihtimalle düşmanlar arasında seken Chain Lightning fırlatır.
28. **Archmage's Wisdom:** +%100 Elemental Hasar, ancak Karakterin Fiziksel Hasarı her zaman 0 olur.
29. **Void Resonance:** Tüm saldırılara +50 Flat "Void" Hasarı ekler.
30. **Elementalist:** Düşmanın üzerindeki her farklı status effect (yanma, donma vb.) için düşmana vurulan hasar +%15 artar.
31. **Arcane Overload:** Yetenekler Mana/Stamina harcamaz, ancak bunun yerine bedel olarak Can (HP) harcar.
32. **Static Field:** Karakterin yakınındaki (ör. 150 pixel) tüm düşmanlar saniyede 30 Yıldırım hasarı alır.
33. **Glacial Shield:** Karakter hasar almadan geçen her 10 saniyede bir, sonraki saldırıyı %100 engelleyen bir buz kalkanı kazanır.

#### 💰 Ekonomi / Utility (Farm & Destek)
34. **Midas Touch:** +%100 Altın Düşürme Oranı (Gold Find).
35. **Scavenger:** +%50 Eşya Düşürme Oranı (Magic Find).
36. **Fleet Footed:** +%30 Hareket Hızı (Movement Speed).
37. **Time Warp:** Tüm yeteneklerin bekleme sürelerinde (Cooldown) %15 Azalma.
38. **Explorer's Spirit:** +%100 Tecrübe Puanı (XP Gain).
39. **Magnetism:** Düşen altın ve eşyaları toplama menzili (Pickup Radius) +%300 artar.
40. **Alchemist:** Potların ve can kürelerinin iyileştirme etkisi %100 artar.

---

## 3. MATEMATİKSEL MANTIK (HASAR VE HP HESAPLAMASI)

Bu iki sistemin birbirine nasıl entegre olacağı ve hesaplama sırası (Order of Operations) oyun dengesi için kritiktir. Çarpanların (Percentage) çok erken hesaplanması oyunu bozar.

**KURAL: Önce Base statlar toplanır (Öz'ler dahil), sonra Flat eşya statları eklenir, EN SON yüzdelik (Multiplier) statlar (Eşya % ve Aura %) çarpılır.**

### Hasar Hesaplama Formülü:
1. `Base_Dmg` = Karakterin Çıplak Hasarı + **[Essence (Öz) Toplamı]**
2. `Flat_Dmg` = `Base_Dmg` + Skill_Tree_Flat + Eşyalardan_Gelen_Flat
3. `Total_Multiplier` = 1.0 + Skill_Tree_Pct + Eşyalardan_Gelen_Pct + **[Aura_Pct]**
4. `FINAL_DAMAGE` = (`Flat_Dmg` * `Total_Multiplier`) + **[Aura_Flat_Etkileri (örn: +100 Flat Sniper's Focus)]**

*Not: "Aura_Flat" statlarının çarpanlardan etkilenmemesi (en sona eklenmesi), bu statların overpowered olmasını engeller.*

---

## 4. ARAYÜZ (UI) TASARIMI FİKİRLERİ

1. **Essence (Öz) Arayüzü - "Ascension Tab":**
   * Karakter ekranında yeni bir sekme. Ortada karakterin silüeti, etrafında toplanan özlerin parlak noktalar halinde döndüğü bir "takımyıldızı" (constellation) tasarımı. 
   * Sağ tarafta basit bir liste: `Essence of Vitality (x45): +90 Base HP`.
2. **Aura Arayüzü - "Aura Shrine":**
   * Envanterden bağımsız ayrı bir pencere veya NPC etkileşimi.
   * Üstte büyük, dairesel ve altın çerçeveli **"Aktif Aura Slotları"**. Başlangıçta 1 slot açık, yanındaki 2 slot üzerinde "Kilitli (Bir Orb Kuşanarak Açın)" yazar.
   * Altta 40 auranın listelendiği, RPG oyunlarındaki yetenek kitaplarına benzeyen bir parşömen görünümü. Aktif olan auranın ikonunun etrafında sürekli dönen bir alev/büyü efekti olur.
3. **Özel Orb Eşyası Tooltip'i:**
   * Bir Orb bulunduğunda Tooltip'inde altın sarısı parlayan bir renkle (Legendary rengi): `★ AURA LIMIT +1 ★` yazar.

---

## 5. "IMPOSSIBLE" ZORLUK İÇİN DENGE ANALİZİ

Oyundaki mevcut zorluk `(1.2) ^ (Wave / 10)` şeklinde artıyor. Yani her 10 Wave'de yaratıklar eski halinin %120'si oluyor.

*   **Wave 100'de:** Yaratıklar başlangıca göre ~6.19 kat güçlü.
*   **Wave 200'de:** Yaratıklar başlangıca göre ~38.3 kat güçlü.

**Bu Sistem Dengeyi Nasıl Sağlar?**
Normalde Eşya + Skill Tree sadece doğrusal (lineer) bir büyüme sağlar. Ancak 200. Wave'e gelindiğinde doğrusal büyüme, eksponansiyel yaratık büyümesinin gerisinde kalır ve oyun "kilitlenir".
*   **Essence Sistemi:** Yaratıkların artan canına karşı oyuncunun çarpanlarının vurabileceği "Base" taşı sürekli büyüterek, çarpan etkisini (multiplier) matematiksel olarak devasa tutar.
*   **Aura Sistemi (Özellikle Orb Mekaniği):** Oyuncuyu düz hasar dizmek yerine **Synergy (Sinerji)** kurmaya zorlar. Örneğin: "Swarm Leader (Minyon Sınırı)" + "Pack Mentality (Minyona göre % hasar)" + "Beastmaster (Minyon Hasarı)". Bu üç aurayı aynı anda takabilmek için oyuncunun çok iyi `[Aura Limit +1]` veren Orb'lar farmlaması gerekir. 
*   **Sonuç:** Oyun "stat basıp ilerleme" modundan çıkarak, "Doğru eşyayı ve doğru aura kombinasyonunu bulma (Build yapma)" oyununa dönüşür. Bu da "Impossible" zorluğun son wave'lerinde tek kurtuluş yoludur.
