# 🎮 Boxhead 2.0 — Kapsamlı Fikir Havuzu (v2 Güncelleme Adayları)

> **Hazırlayan:** AI Game Designer | **Tarih:** 2025-08-08
> **Kaynak Analiz:** 9 sınıf, 18 evolution, 56 yetenek, 38 kart, 8 sinerji, 31+ item, 15 set, 13 orb, 22 kristal yükseltme, 24+ düşman tipi, 1 boss, 4 biome, 20 aura — tamamı incelendi.
> **İlham Kaynakları:** Path of Exile, Diablo IV, Hades, Vampire Survivors, Risk of Rain 2, Dead Cells, Slay the Spire, Enter the Gungeon

---

## 📋 İÇİNDEKİLER

| # | Kategori | Fikir Sayısı |
|---|----------|-------------|
| A | Yeni Sınıflar (Classes) | 4 |
| B | Yeni Silahlar & Silah Tipleri | 6 |
| C | Yeni Kartlar (Cards) | 12 |
| D | Yeni Düşman Türleri | 8 |
| E | Yeni Boss & Mini-Boss Sistemi | 5 |
| F | Yeni Sinerjiler | 6 |
| G | Yeni Oyun Mekanikleri & Sistemler | 10 |
| H | Yeni Eserler (Artifacts) | 4 |
| I | Yeni Auralar | 4 |
| J | Yeni Kristal Yükseltmeler | 4 |
| K | Yeni Set Bonusları | 3 |
| L | Skill Tree Genişletmeleri | 4 |
| M | Yeni Status Effect'ler | 3 |
| **TOPLAM** | | **73 Fikir** |

---

## A. YENİ SINIFLAR (CLASSES) — 4 Fikir

### A1. 🕯️ Chronomancer (Zaman Büyücüsü)
**Konsept:** Zamanı manipüle eden, düşmanları yavaşlatıp kendi hızını artıran taktiksel sınıf. Hades'teki "Aspect of Beowulf" ve PoE'deki Temporal Rift mekaniklerinden ilham.

**Temel İstatistikler:**
- HP: 80 (düşük), Hız: 4.8, dmgMult: +30%
- attack_cooldown: 600ms (orta)
- **Özel Pasif — Zaman Dilasyonu:** Her 5. saldırı, 2 saniyeliğine kendisine %40 hız artışı ve tüm yakındaki düşmanlara %50 yavaşlatma uygular.

**Başlangıç Silahı:** "Kum Saati Asası" (Ranged, physDmg: 10, frostDmgFlat: 5)

**Benzersiz Mekanik — Zaman Geri Sarma (Rewind):**
- Q tuşu ile aktive edilir. 8 saniyelik cooldown.
- Son 3 saniye içindeki pozisyonuna ve HP'sine geri döner (PoE'deki "Temporal Rift" gibi).
- Geri sarma esnasında geçtiği yolda zamansal bir iz bırakır ve bu iz temas eden düşmanlara 2s stun uygular.

**Evolution Yolları:**
1. **Zaman Lordu (chronomancer_timelord):** dmgMult +0.6, attack_speed +0.4, HP delta: -30. Pasif: `time_loop` — Her 15 saniyede bir, son 5 saniyede verdiği toplam hasarı tekrar uygular (Phantom hit).
2. **Kum Kalesi (chronomancer_sandcastle):** armor +40, max_hp +60, dodgeChance +0.15, HP delta: 0. Pasif: `stasis_field` — Ölümcül hasar alındığında 3 saniyeliğine zaman durur (tüm düşmanlar donar, oyuncu hareket edebilir). 120s cooldown.

---

### A2. 🃏 Gambler (Kumarbaz)
**Konsept:** RNG tabanlı, yüksek risk-yüksek ödül sınıf. Slay the Spire'daki "Silent" ve Enter the Gungeon'daki "The Pilot" gibi şans mekaniklerini kullanır.

**Temel İstatistikler:**
- HP: 90, Hız: 5.0, dmgMult: +10%
- attack_cooldown: 500ms
- **Özel Pasif — Şans Çarkı:** Her saldırıda %20 ihtimalle hasarı 3x olur, %10 ihtimalle saldırı hiç hasar vermez (miss).

**Başlangıç Silahı:** "Zarif İskambil" (Ranged, physDmg: 11, critChance: 0.10)

**Benzersiz Mekanik — Kart Çekişi (Card Draw):**
- Her 10 düşman öldürmede rastgele bir "Kumarbaz Kartı" çeker:
  - ♠ Maça: 5 saniyeliğine tüm saldırılar kritik vurur.
  - ♥ Kupa: Tam can yenileme.
  - ♦ Karo: 200 bonus altın.
  - ♣ Sinek: Etraftaki tüm düşmanlara 100 hasar.
  - 🃏 Joker (%5 şans): Yukarıdakilerin HEPSİ aynı anda.

**Evolution Yolları:**
1. **Şeytan Kumarbazcı (gambler_devil):** critChance +0.3, critDmg +2.0, HP delta: -40. Pasif: `devils_luck` — Miss ihtimali kaldırılır, 3x hasar ihtimali %35'e çıkar.
2. **Kader Okuyucu (gambler_fortune):** dodgeChance +0.2, magicFind +0.5, goldGain +0.5, HP delta: 0. Pasif: `fortune_wheel` — Her dalga başında rastgele bir aura efekti 30 saniyeliğine aktif olur.

---

### A3. ⚡ Monk (Keşiş / Dövüşçü)
**Konsept:** Hızlı kombo tabanlı yakın dövüşçü. Diablo III'ün Monk sınıfından ilham. Ardışık saldırılar güçlenir.

**Temel İstatistikler:**
- HP: 95, Hız: 5.5, dmgMult: +15%
- attack_cooldown: 250ms (oyundaki en hızlı)
- **Özel Pasif — Kombo Zinciri:** Ardışık 3 vuruş yaparsa 4. vuruş AoE shockwave olur (120 yarıçap). Zincir 2 saniye vurmayınca kırılır.

**Başlangıç Silahı:** "Çıplak Yumruk" (Melee, physDmg: 6, meleeRange: 40, attackCooldown: 250ms)

**Benzersiz Mekanik — Chi Akışı:**
- Her 3 kombo tamamlandığında 1 "Chi" noktası kazanır (max 5).
- Q tuşuyla Chi harcayarak güçlü teknikler kullanır:
  - 1 Chi: Şok Dalgası (200 yarıçap AoE, stun 1.5s)
  - 3 Chi: Bin Yumruk (0.5 saniyede 10 hızlı vuruş)
  - 5 Chi: Ejder Yumruğu (Düz çizgide 500 birim uzunluğunda delici hasar dalgası)

**Evolution Yolları:**
1. **Fırtına Keşişi (monk_storm):** attack_speed +0.5, speed +2.0, critChance +0.15, HP delta: -25. Pasif: `lightning_fists` — Her vuruş %25 ihtimalle chain lightning tetikler (3 düşmana sıçrar).
2. **Demir Keşiş (monk_iron):** armor +60, max_hp +100, combatRegen +3, HP delta: 0. Pasif: `iron_body` — Kombo zinciri aktifken gelen hasar %30 azalır. 5 Chi'de tamamen hasar bağışıklığı (2 saniye).

---

### A4. 🌿 Druid (Druid / Doğa Büyücüsü)
**Konsept:** Şekil değiştiren hibrit sınıf. İnsan formunda iyileştirici/destekçi, hayvan formunda saldırgan. Risk of Rain 2'deki "REX" ve WoW Druid'inden ilham.

**Temel İstatistikler:**
- HP: 110, Hız: 4.4, dmgMult: +10%
- attack_cooldown: 700ms
- **Özel Pasif — Doğanın Dengesi:** İnsan formunda etraftaki minyonlara saniyede 5 HP iyileştirme aurası yayar. Hayvan formunda lifesteal %10 kazanır.

**Başlangıç Silahı:** "Doğa Asası" (Ranged, physDmg: 9, poisonDps: 5)

**Benzersiz Mekanik — Form Değiştirme (Q tuşu, 10s cooldown):**
- **İnsan Formu:** Ranged saldırı, minyonları iyileştirir, her 8 saniyede bir "Doğa Kökü" dikenli bitki çağırır (3 saniyelik tuzak, 500 yarıçapında oyuncuya yönelen düşmanları yavaşlatır).
- **Ayı Formu:** Melee saldırı (dmg 2x, meleeRange +30, armor +30 geçici), hız %20 azalır. Her vuruş %5 ihtimalle düşmanı 1.5s stun eder.

**Evolution Yolları:**
1. **Büyük Ayı (druid_bear):** armor +80, max_hp +150, lifesteal +0.15, HP delta: 0. Pasif: `permanent_bear` — Kalıcı ayı formunda kalır. Stun ihtimali %15'e çıkar. Melee hasar 2.5x.
2. **Orman Bilgesi (druid_sage):** minionCount +2, regen +5, elementDmgMult +0.4, HP delta: -20. Pasif: `nature_army` — Her 10 saniyede bir düşmanı "Doğa Minyonu"na dönüştürür (30 saniyeliğine tarafını değiştirir).

---

## B. YENİ SİLAHLAR & SİLAH TİPLERİ — 6 Fikir

### B1. ⛓️ Zincirli Tırpan (Flail / Chain Weapon)
**Silah Tipi:** Yeni kategori — `chain` (Orta menzilli melee)
**Mekanik:** 
- Menzil: meleeRange + 80 (kılıçtan uzun, ranged'den kısa). 
- Dönerek 360° ark çizer (tam daire saldırı).
- Her vuruşta zincir ucundaki düşmanı 40 birim geriye çeker (reverse knockback — oyuncuya doğru çeker).
- Geri çekilen düşmanlar birbirlerine çarparak bonus hasar alır (bilardo efekti).

**Tier Örnekleri:**
| Tier | İsim | physDmg | Özel |
|------|-------|---------|------|
| T4 | Paslı Zincir | 10 | meleeRange: 80 |
| T3 | Çelik Tırpan | 25 | meleeRange: 90, pullForce: 50 |
| T2 | Ruh Zinciri | 55 | meleeRange: 100, pullForce: 70, lifesteal: 0.05 |
| T1 | Kaos Tırpanı | 110 | meleeRange: 120, pullForce: 100, chainTargets: 3 |

---

### B2. 🪃 Geri Dönen Disk (Glaive / Ricochet Disc)
**Silah Tipi:** Yeni kategori — `glaive` (Otomatik sekme ranged)
**Mekanik:**
- Atıldığında en yakın düşmana gider, ardından otomatik olarak en yakın 2. düşmana seker, sonra oyuncuya geri döner.
- Geri dönüş yolunda da hasar verir.
- Her sekmede hasar %15 azalır (damage decay).
- Aynı anda sadece 1 disk havada olabilir (havadayken tekrar atamazsın — timing mekanik).

**Tier Örnekleri:**
| Tier | İsim | physDmg | Sekme | Özel |
|------|-------|---------|-------|------|
| T4 | Bakır Disk | 14 | 2 | — |
| T3 | Gümüş Glaive | 30 | 3 | damageDecay: %10 |
| T2 | Mithril Disk | 60 | 4 | damageDecay: %5, frostDmg: 10 |
| T1 | Yıldırım Diski | 120 | 6 | damageDecay: 0, chainLightning: true |

---

### B3. 📿 Tespih / Whip (Kırbaç)
**Silah Tipi:** Yeni kategori — `whip` (Uzun menzilli melee)
**Mekanik:**
- Çok uzun melee menzili (meleeRange + 150) ama dar ark (0.4 rad ≈ 23°).
- Her 5. vuruşta "Kırbaç Fırtınası" — tam 360° saldırı ve tüm vurulanlara 1s slow uygular.
- Düşmanları arkaya iter (yüksek knockback).
- Beastmaster ile sinerji: Kırbaç vuruşu minyonlara %20 hız buff'ı verir (2 saniye).

**Tier Örnekleri:**
| Tier | İsim | physDmg | Menzil | Özel |
|------|-------|---------|--------|------|
| T4 | Deri Kırbaç | 8 | +150 | knockback: 60 |
| T3 | Dikenli Kırbaç | 22 | +170 | knockback: 80, bleed: 3 DPS |
| T2 | Ejder Kırbacı | 48 | +200 | knockback: 100, fireDmg: 15 |
| T1 | Cehennem Kırbacı | 95 | +250 | knockback: 140, fireDmg: 40, chainHit: 2 |

---

### B4. 🧪 Simya Silahı: Transmutasyon Tabancası
**Silah Tipi:** `transmuter` (Ranged — Alchemist özel silahı ama herkes kullanabilir)
**Mekanik:**
- Vurduğu düşmana 3 farklı element arasında rastgele biri uygulanır (Ateş, Buz, Zehir).
- Eğer düşman zaten başka bir element etkisi altındaysa, "Element Patlaması" tetiklenir:
  - Ateş + Buz = Buhar Patlaması (150 yarıçap AoE, 2x hasar)
  - Ateş + Zehir = Toksik Alev (200 yarıçap, 10 saniyelik yanma alanı)
  - Buz + Zehir = Kristalize (Düşman 3 saniye donar ve parçalanınca yakınlara zehir yayar)

---

### B5. 🎯 Otomatik Nişangah (Sentinel Drone)
**Silah Tipi:** `drone` (Engineer özel silahı — Taret ve Ranged arası hibrit)
**Mekanik:**
- Oyuncunun etrafında yörüngede dönen 1-3 drone. Her drone bağımsız olarak en yakın düşmana ateş eder.
- Drone'lar oyuncunun turret statlarını kullanır ama %60 etkinlikle.
- Oyuncu hareket ettikçe drone'lar da takip eder (taretlerden farkı: mobil).
- Drone sayısı: base 1, turretLimit ile artar (max 3).

---

### B6. 🗡️ İkili Bıçak (Dual Daggers)
**Silah Tipi:** `dual` (Ultra-hızlı melee — Ninja özel ama herkes kullanabilir)
**Mekanik:**
- Her saldırı aslında 2 ardışık vuruştur (çift el ile). Her vuruş tek bıçak hasarının %60'ı.
- Toplam DPS: tek bıçak × 1.2 (kılıçtan biraz düşük ama çok daha hızlı).
- Benzersiz: Her çift vuruş %8 ihtimalle "Bıçak Fırtınası" tetikler — 0.3 saniyede 5 hızlı vuruş (her biri %30 hasar).
- Backstab bonus'u çift uygulanır (Ninja ile sinerji: 2x → 4x ilk vuruş).

---

## C. YENİ KARTLAR (CARDS) — 12 Fikir

### C1. 🌑 Gölge Klonu (Shadow Clone) — Offense
- **Efekt:** Her 12 saniyede bir, oyuncunun pozisyonunda 4 saniyelik bir gölge klon belirir. Klon, oyuncunun %40 hasarı ile otomatik saldırır ve düşman saldırılarını çeker (tank).
- **Bedel:** Klon aktifken oyuncunun kendi hasarı %20 azalır.
- **Stats:** `dmgMult: -0.20`

### C2. 🔄 Entropi (Entropy) — Curse
- **Efekt:** Her öldürülen düşman %3 ihtimalle "Zaman Çökmesi" tetikler — 2 saniyeliğine ekrandaki TÜM düşmanlar ve mermiler donar.
- **Bedel:** Oyuncu da %30 yavaşlar (kalıcı). Zaman Çökmesi esnasında oyuncu da ateş edemez.
- **Stats:** `speed: -1.5`

### C3. 💎 Midas Dokunuşu (Midas Touch) — Support
- **Efekt:** Her vuruş %5 ihtimalle düşmanı 2 saniyeliğine "Altın" yapar — Altın düşman 3x hasar alır ve öldüğünde 5x altın düşürür.
- **Bedel:** Oyuncunun base hasar çarpanı %25 azalır.
- **Stats:** `dmgMult: -0.25, goldGain: +0.3`

### C4. 🧬 Mutasyon (Mutation) — Curse
- **Efekt:** Her level atladığında rastgele bir stat kalıcı olarak +%20 artar (herhangi biri: HP, hasar, hız, zırh, krit, vb.) AMA başka bir rastgele stat da kalıcı olarak -%15 azalır.
- **Bedel:** Kontrol edemezsin — tamamen RNG. Bazen hasar artar zırh düşer, bazen ikisi de kötü olabilir.
- **Stats:** Yok (dinamik)

### C5. ⚡ Statik Zırh (Static Armor) — Survival
- **Efekt:** Hasar aldığında çevresinde 80 yarıçaplı elektrik dalgası yayılır (gelen hasarın %50'si kadar AoE hasar verir düşmanlara). Thorns'un gelişmiş versiyonu.
- **Bedel:** Enerji kalkanı tamamen devre dışı kalır (maxEnergyShield = 0).
- **Stats:** `maxEnergyShield: -9999`

### C6. 🏹 Ricochet Master (Sekme Ustası) — Offense
- **Efekt:** Tüm mermilere +3 sekme (bounce) ekler. Her sekmede hasar %10 ARTAR (decay yerine amplify).
- **Bedel:** Mermi hızı %40 azalır. Pierce tamamen kaldırılır (pierce = 0).
- **Stats:** `bounce: +3, bullet_speed: -2, pierce: -99`

### C7. 🩸 Kan Bankası (Blood Bank) — Survival
- **Efekt:** Fazla iyileşme (overheal) boşa gitmez — "Kan Bankası"nda birikir (max 500). Q tuşuyla Kan Bankası'nı patlat: Biriken canın %150'si kadar etraftaki düşmanlara AoE hasar + biriken canın %50'si kadar kendini iyileştir.
- **Bedel:** Normal can yenilenmesi (regen) %50 yavaşlar.
- **Stats:** `regen: -50%` (çarpansal)

### C8. 🌀 Kaos Alanı (Chaos Field) — Elemental
- **Efekt:** Oyuncunun etrafında 150 yarıçaplı bir alan oluşur. Bu alanda düşmanların zırhı %50 azalır ve element dirençleri kaldırılır.
- **Bedel:** Oyuncunun kendi zırhı da bu alanda %30 azalır.
- **Stats:** `armor: -30` (sadece aura alanında)

### C9. 🎭 Doppelganger (İkiz) — Minion
- **Efekt:** Kalıcı olarak oyuncunun yanında bir "İkiz" doğar. İkiz, oyuncunun silahını ve istatistiklerinin %30'unu kullanarak bağımsız saldırır. Ölürse 30 saniye sonra yeniden doğar.
- **Bedel:** Oyuncunun kendi hasarı %25 azalır.
- **Stats:** `dmgMult: -0.25`

### C10. 💀 Son Nefes (Last Breath) — Curse
- **Efekt:** Oyuncu öldüğünde (revive kullanmadan önce) çevresinde devasa bir patlama oluşur: Ekrandaki TÜM düşmanlara mevcut max HP'sinin 5 katı kadar hasar verir. Eğer bu patlama en az 10 düşmanı öldürürse, oyuncu %30 HP ile diriltilir (ek bir revive gibi).
- **Bedel:** Max HP kalıcı olarak %25 azalır.
- **Stats:** `max_hp: -25%` (çarpansal)

### C11. 🧲 Yerçekimi Kuyusu (Gravity Well) — Support
- **Efekt:** Her 20 saniyede bir, oyuncunun pozisyonunda 3 saniyelik bir yerçekimi kuyusu oluşur. 200 yarıçapındaki tüm düşmanları merkeze çeker ve %40 yavaşlatır.
- **Bedel:** Oyuncunun kendi mıknatıs yarıçapı (magnet) %50 azalır.
- **Stats:** `magnetRadius: -50%`

### C12. 🔥 Fırın (The Furnace) — Elemental
- **Efekt:** Öldürülen düşmanlar %30 ihtimalle patlar ve etraflarına 60 yarıçapında ateş hasarı yayar (ölen düşmanın max HP'sinin %10'u kadar). Zincirleme reaksiyon yapabilir (patlayan düşman başka düşmanı öldürürse o da patlayabilir).
- **Bedel:** Oyuncunun buz hasarı tamamen kaldırılır (frostDmg = 0).
- **Stats:** `frostDmgFlat: -999, frostDamage: -999`

---

## D. YENİ DÜŞMAN TÜRLERİ — 8 Fikir

### D1. 🪞 Ayna Gözcüsü (Mirror Sentinel)
- **HP:** 250 × ws | **Hasar:** 20 × ws | **Hız:** 1.5 | **XP:** 60
- **Mekanik — Yansıtma Kalkanı:** Önünden gelen mermileri %40 ihtimalle geri yansıtır (oyuncuya geri döner). Yansıtılan mermiler orijinal hasarın %60'ı kadar vuruşur.
- **Zayıflık:** Arkadan gelen saldırılara karşı savunmasız (2x hasar alır). Melee saldırılar yansıtılamaz.
- **Neden İyi:** Oyuncuyu pozisyon değiştirmeye ve melee/flanking stratejilere zorlar. Sniper oyuncuları için counterplay.

### D2. 🕸️ Ağ Örgücüsü (Web Weaver)
- **HP:** 140 × ws | **Hasar:** 8 × ws | **Hız:** 2.5 | **XP:** 45
- **Mekanik — Ağ Bırakma:** Hareket ederken arkasında yapışkan ağ izi bırakır (100×100 alan, 8 saniye sürer). Ağa basan oyuncu %70 yavaşlar ve 1 saniye saldırı yapamaz (silenced). Ağ birikir.
- **Mekanik — Yumurta Bırakma:** Ölünce %25 ihtimalle 3 adet Swarm Bat çıkaran yumurta bırakır (2 saniye kuluçka süresi — yumurtayı patlat yoksa bat'ler çıkar).
- **Neden İyi:** Alan kontrolü yapan düşman. Oyuncuyu haritada daha dikkatli dolaşmaya zorlar.

### D3. 🔮 Faz Kayıcısı (Phase Shifter)
- **HP:** 160 × ws | **Hasar:** 25 × ws | **Hız:** 3.0 | **XP:** 70
- **Mekanik — Faz Kayması:** Mermiler %50 ihtimalle bu düşmanın içinden geçer (hasar vermeden). Efekt: Yarı saydam görünüm, hasar almadığında parıltı.
- **Mekanik — Solid Phase:** Her 3 saniyede bir 1.5 saniyeliğine tamamen katılaşır (parlaklık artar, renk koyulaşır). Bu sürede normal hasar alır ve kendisi de saldırır.
- **Zayıflık:** Element hasarları (ateş, buz, zehir) faz kaymasından etkilenmez — her zaman isabet eder.
- **Neden İyi:** Pure physical build'leri zorlar, element investment'ı ödüllendirir.

### D4. 🫀 Parazit (Parasite)
- **HP:** 60 × ws | **Hasar:** 0 | **Hız:** 4.5 | **XP:** 30
- **Mekanik — Yapışma:** Oyuncuya ulaştığında yapışır (hasar vermez). Yapışan parazit oyuncunun statlarını düşürür: Her parazit başına -%5 dmgMult, -%0.3 hız. Aynı anda max 5 parazit yapışabilir.
- **Mekanik — Temizleme:** Parazitler dash ile veya alan hasarı (AoE) ile temizlenir. Temizlenmezse 10 saniye sonra "olgunlaşır" ve oyuncudan ayrılıp tam güçlü bir Normal düşmana dönüşür.
- **Neden İyi:** Tamamen yeni bir tehdit tipi — doğrudan hasar yerine debuff. Alchemist ve AoE build'leri ödüllendirir.

### D5. 🏰 Savaş Kulesi (War Tower)
- **HP:** 800 × ws | **Hasar:** 30 × ws | **Hız:** 0 (sabit) | **XP:** 150
- **Mekanik — Sabit Kule:** Hareketsiz ama 400 yarıçapında alan kontrolü yapar. Her 1.5 saniyede mermi yağmuru (3 mermi, oyuncuya doğru).
- **Mekanik — Buff Aurası:** 300 yarıçapındaki tüm düşmanlara +%25 hasar ve +%15 hız verir.
- **Zayıflık:** Hareketsiz olduğu için uzaktan kolayca vurulabilir. Ama çevresinde çok düşman olduğu için yaklaşmak zor.
- **Neden İyi:** Haritada stratejik hedefler oluşturur. Önce kuleyi mi yoksa çevresindeki düşmanları mı yok edeceğine karar vermelisin.

### D6. 💨 Hırsız Cin (Pickpocket Imp)
- **HP:** 100 × ws | **Hasar:** 5 × ws | **Hız:** 5.0 | **XP:** 40
- **Mekanik — Altın Çalma:** Oyuncuya temas ettiğinde 50-150 altın çalar ve kaçmaya başlar. 10 saniye içinde öldürülürse çaldığı altın + %50 bonus geri düşer.
- **Mekanik — Hırsız Refleksi:** İlk vuruşu her zaman dodge eder (garantili kaçınma). Sonraki vuruşlar normal.
- **Neden İyi:** Loot Goblin'in tersi — kaçırmak yerine çaldığını geri almak mekaniği. Acil karar verme gerektirir.

### D7. ⚗️ Mutant Bilim İnsanı (Mad Scientist)
- **HP:** 200 × ws | **Hasar:** 15 × ws | **Hız:** 1.8 | **XP:** 80
- **Mekanik — Düşman Güçlendirme:** Her 5 saniyede bir, etrafındaki rastgele bir düşmana "mutasyon" uygular: %50 daha fazla HP, %30 daha fazla hasar, boyut 1.3x.
- **Mekanik — Ölüm İksiri:** Ölünce 150 yarıçapında zehir bulutu bırakır (15 DPS, 5 saniye).
- **Neden İyi:** Öncelikli hedef olarak stratejik karar verme gerektirir. Bırakırsan etraftaki düşmanlar tanklaşır.

### D8. 🌊 Dalga Yok Edicisi (Tide Breaker)
- **HP:** 500 × ws | **Hasar:** 20 × ws | **Hız:** 1.2 | **XP:** 120
- **Mekanik — Dalga İtme:** Her 4 saniyede bir, önünde 300 birim genişliğinde bir şok dalgası yayar. Dalga oyuncuyu 200 birim geriye iter ve 0.5s stun uygular.
- **Mekanik — Dalga Kırıcı:** Bu düşman knockback'e tamamen bağışıktır. Ayrıca çevresindeki düşmanlar da %50 daha az knockback alır.
- **Neden İyi:** Knockback tabanlı build'lere karşı counter. Oyuncuyu pozisyon yönetimi konusunda zorlar.

---

## E. YENİ BOSS & MİNİ-BOSS SİSTEMİ — 5 Fikir

### E1. 🐉 İkinci Boss: Kristal Ejderha (Crystal Dragon)
**Spawn:** Wave 20 Boss
**HP Formülü:** `6000 * (1.15 ** wave_level) * diff_mult`
**Mekanik — 4 Faz Sistemi:**

1. **Faz 1 — Hava Saldırısı (HP: %100-%75):** Ejderha ekranın üstünde uçar (vurulmaz). Yere doğru kristal mermiler yağdırır. Oyuncu kristal yağmurlarından kaçmalı. Her 10 saniyede bir yere iner ve 5 saniyeliğine vurulabilir hale gelir.

2. **Faz 2 — Nefes Saldırısı (HP: %75-%50):** Yere iner. Önünde koni şeklinde kristal nefes atar (120° ark, 400 birim menzil, büyük hasar). Nefes yönünü 2 saniye önceden kırmızı uyarı gösterir. Aynı zamanda kristal dikenler yere serpilir (hazard).

3. **Faz 3 — Kristal Labirent (HP: %50-%25):** Haritaya kristal duvarlar yerleştirir ve labirent oluşturur. Ejderha labirentin merkezinde kalır. Oyuncu labirenti geçerek ejderhaya ulaşmalı. Duvarlar vurulunca kırılabilir (300 HP her duvar). Ama ejderha sürekli yeni duvarlar oluşturur.

4. **Faz 4 — Çılgınlık (HP: %25-%0):** Tüm kristal duvarlar patlar (AoE hasar). Ejderha sabit pozisyonda kalır ve delice mermi rain atar (Bullet Hell modu). 360° dönen kristal halkalar + yere düşen kristal bombalar. DPS yarışı — oyuncunun ejderhayı %25 HP'den sıfıra indirmesi gerekir, aksi halde kristal yağmuru gittikçe yoğunlaşır.

---

### E2. 🕷️ Üçüncü Boss: Kraliçe Arachne (Spider Queen)
**Spawn:** Wave 30 Boss
**HP Formülü:** `8000 * (1.15 ** wave_level) * diff_mult`
**Mekanik — 3 Faz + Add Yönetimi:**

1. **Faz 1 — Ağ Krallığı:** Haritanın %60'ı yapışkan ağlarla kaplanır (hareket hızı %50 azalır ağ üstünde). Kraliçe merkezdedir ve etrafındaki 8 yumurtadan sürekli Spider (venom_spider) çağırır. Yumurtalar yok edilmelidir (her biri 500 HP).

2. **Faz 2 — Zehir Tsunami:** Ağlar temizlenir. Kraliçe haritanın bir kenarından diğerine doğru zehir dalgası gönderir (platformer tarzı — dalganın üzerinden atılma / kaçma mekaniği). Her 5 saniyede dalga yönü değişir.

3. **Faz 3 — Bebek Patlama:** Kraliçe merkezde kalır ve kendini koruyucu kozaya sarar (5 saniye hasar almaz). Bu sırada 50 adet bebek örümcek (mini swarm_bat statlarında) dalga halinde doğar. Koza açıldığında Kraliçe 3 saniyeliğine vulnerable olur. Bu döngü tekrarlar.

---

### E3. 🎪 Mini-Boss Sistemi (Her 5 Wave'de)
**Yeni Mekanik:** Normal boss'lar yerine (Wave 10, 20, 30), arada kalan her 5. wave'de (Wave 5, 15, 25) rastgele bir Mini-Boss çıkar.

**Mini-Boss Havuzu (6 adet):**
1. **Golem Muhafız:** HP: 2000 × ws, çok yavaş (0.6 hız), her 3 saniyede zemin darbesi (200 yarıçap AoE + stun 1s).
2. **Gölge İkizi:** HP: 1500 × ws, oyuncunun silahını kopyalar ve oyuncuya karşı kullanır. Oyuncunun dmgMult'ını yansıtır.
3. **Cehennem Ateşçisi:** HP: 1000 × ws, sürekli etrafında dönen ateş halkası (150 yarıçap, 30 DPS). Ateş halkası genişleyip daralır.
4. **Kristal Dev:** HP: 3000 × ws, gelen hasarın %30'unu emer ve her 15 saniyede bir emerdiği hasarı kristal patlama olarak geri verir.
5. **Fırtına Lordu:** HP: 1200 × ws, sürekli hareket eden yıldırım çubukları çağırır (dikey lazer hatları, 2 saniye uyarı sonrası 1 saniye aktif).
6. **Parazit Ana:** HP: 2500 × ws, her 3 saniyede 2 Parazit düşman çağırır. Yapışan parazitler onun HP'sini iyileştirir.

---

### E4. 🏆 Boss Rush Modu (Yeni Özel Dalga Tipi)
**Tetiklenme:** Wave 25 özel dalga olarak veya Kristal Yükseltme ile açılabilen ayrı bir mod.
**Mekanik:**
- Normal düşmanlar yok. Sadece Mini-Boss'lar arka arkaya çıkar.
- Her 30 saniyede bir yeni Mini-Boss spawn olur. Aynı anda max 2 Mini-Boss aktif olabilir.
- 5 Mini-Boss yenildiğinde Bonus Ödül: Garanti Unique eşya + 1000 Kristal.
- Her yenilen Mini-Boss sonrası oyuncu 10 saniyelik iyileşme süresi alır (regen 10x).

---

### E5. 💀 Nemesis Sistemi (Kalıcı Düşman Evrimi)
**İlham:** Shadow of Mordor Nemesis System
**Mekanik:**
- Oyuncuyu öldüren Elite düşman "Nemesis" olur ve kayıt altına alınır.
- Nemesis, sonraki oyunlarda (run) tekrar karşına çıkar — bu sefer daha güçlü (her yenilgide +%20 HP, +%10 hasar, max 3 seviye güçlenme).
- Nemesis'in ismi, modifikatörleri ve görünümü kaydedilir.
- Nemesis'i yendiğinde garanti Rare+ eşya ve 2x kristal ödülü verir.
- Max 3 aktif Nemesis olabilir. En eski olanı yenisi gelince silinir.

---

## F. YENİ SİNERJİLER — 6 Fikir

### F1. 🌪️ Fırtına Birliği (storm_alliance)
- **Gereken Kartlar:** `storm_caller` + `ice_shirt`
- **Bonus:** Her yıldırım çarpması aynı zamanda 2 saniyelik donma (freeze) uygular. `frostDmgFlat: +15`

### F2. 🧛 Vampir İmparatorluğu (vampire_empire)
- **Gereken Kartlar:** `vampire_touch` + `undead_army`
- **Bonus:** Minyonlar da lifesteal kazanır (%10). Ölen minyonlar %30 ihtimalle diriltilir. `minionLifesteal: 0.10`

### F3. 💣 Kaotik İnfaz (chaotic_execution)
- **Gereken Kartlar:** `chaos_theory` + `executioner`
- **Bonus:** İnfaz eşiği %30'dan %45'e çıkar. İnfaz edilen düşmanlar patlar (80 yarıçap AoE). `execute_threshold: +0.15`

### F4. 🛡️ Cam Kale (glass_castle)
- **Gereken Kartlar:** `glass_cannon` + `iron_will`
- **Bonus:** Pasif kalkan cooldown'u 60 saniyeden 20 saniyeye düşer. Kalkan kırılınca 100 yarıçapında shockwave. `passiveShieldCd: -40`

### F5. 🃏 Ölüm Kumarı (death_gamble)
- **Gereken Kartlar:** `death_pact` + `death_wish`
- **Bonus:** Max HP 1'e düşer (zaten death_pact %90 azaltıyor) AMA verilen hasar 5x olur (toplam). Ayrıca her öldürme 1 HP iyileştirir. `dmgMult: +2.0, killHpBonus: +1`

### F6. 🔮 Element Ustası (elemental_mastery)
- **Gereken Kartlar:** `fire_soul` + `frozen_time` + `poison_master` (3'lü sinerji)
- **Bonus:** 3 elementin hepsine sahip olduğunda, tüm element hasarları %50 artar ve her saldırı 3 elementin hepsini aynı anda uygular. `elementDmgMult: +0.50, allElementApply: true`

---

## G. YENİ OYUN MEKANİKLERİ & SİSTEMLER — 10 Fikir

### G1. 🏪 Gezgin Tüccar (Wandering Merchant) Sistemi
- **Mekanik:** Her 7 wave'de bir haritada "Gezgin Tüccar" NPC belirirdi (yeşil ikon, haritada 30 saniye kalır).
- **Sunduğu:** 3 adet özel eşya (normal dükkânda bulunmayan). Bunlar:
  - **Reçete (Recipe):** 2 belirli eşyayı birleştirerek Unique eşya yaratma tarifi.
  - **Kutsama (Blessing):** 1 dalgalık geçici buff (ör: 2x XP, sonsuz mermi, %100 krit).
  - **Harita Parçası (Map Fragment):** 3 parça birleştirilince "Gizli Oda" açılır (ek boss + garanti Unique ödül).
- **Risk:** Tüccara ulaşmak için aktif dalga sırasında haritada hareket etmelisin.

### G2. 🧬 Ascension (Yükseliş) Sistemi — Prestige Mekanizması
- **Mekanik:** Wave 30+ ulaşan oyuncu "Yükseliş" yapabilir (oyunu bitirir ve kalıcı bonuslar kazanır).
- **Yükseliş Seviyeleri:** Her yükseliş +1 seviye. Her seviye:
  - +%5 kalıcı başlangıç hasarı
  - +10 kalıcı başlangıç HP'si
  - +%3 kalıcı kristal kazanımı
  - Yeni zorluk seviyeleri açar
- **Max Yükseliş:** 10. Her yükseliş sonrası düşmanlar da %10 daha güçlenir (scaling challenge).
- **Özel:** Yükseliş 5'te "Yükseliş Silahı" açılır — sınıfa özel efsanevi silah (T0 tier).

### G3. 🗺️ Harita Modifikatörleri (Map Modifiers) Sistemi
- **Mekanik:** Her oyun başlangıcında 3 harita modifikatörü seçilebilir. Zorluk arttıkça ödül de artar.
- **Modifikatör Örnekleri:**
  - **Karanlık:** Görüş alanı %50 azalır. Ödül: +%30 XP.
  - **Kalabalık:** Düşman sayısı 2x. Ödül: +%50 Kristal.
  - **Fakir:** Altın düşmez. Ödül: +%100 Magic Find.
  - **Hızlı:** Tüm düşmanlar %30 hızlı. Ödül: +%40 Altın.
  - **Kırılgan:** Oyuncu max HP'si yarıya düşer. Ödül: Her dalga garanti kart seçimi.
  - **Lanetli:** Düşmanlar ölünce patlayan zehir bulutu bırakır. Ödül: +%25 Hasar.
- **Zorluk Puanı:** Seçilen modifikatörlerin toplam zorluk puanına göre dalga sonu ödülü katlanır.

### G4. 🏠 Üs Sistemi (Home Base / Hub)
- **Mekanik:** Oyunlar arasında bir "Üs" ekranı. Buradan:
  - **Demirci:** Kristal harcayarak silah Tier'ini yükselt (T4 → T3 → T2 → T1).
  - **Kütüphane:** Keşfedilen düşman türlerinin istatistiklerini ve zayıf noktalarını gösteren "Bestiary" (yaratık ansiklopedisi).
  - **Eğitim Alanı:** Sınıf yeteneklerini ve combo'ları deneyebileceğin sonsuz can düşmanlarla dolu alan.
  - **Kupa Odası:** Başarımlar (achievements) ve en iyi skorlar.

### G5. 🎯 Combo Finisher Sistemi
- **Mekanik:** Mevcut kill combo sistemine "Finisher" eklenir.
- **Combo Eşikleri ve Finisher'lar:**
  - **10 Combo → Küçük Patlama:** Oyuncunun etrafında 100 yarıçap AoE (30 hasar).
  - **25 Combo → Mermi Yağmuru:** 2 saniyeliğine gökyüzünden rastgele mermiler yağar.
  - **50 Combo → Zaman Yavaşlaması:** 3 saniyeliğine düşmanlar %50 yavaşlar.
  - **100 Combo → Süpernova:** Ekrandaki TÜM düşmanlara max HP'nin %30'u kadar hasar.
- **Kırılma Cezası:** Combo kırıldığında (3 saniye öldürmeme) oyuncu 1 saniye hız debuff'ı alır.

### G6. 🌙 Gece / Gündüz Döngüsü
- **Mekanik:** Her 3 dalga bir "Gece" döngüsü, her 3 dalga bir "Gündüz" döngüsü.
- **Gündüz Efektleri:** Normal oyun. Kervan aktif. Daha az düşman ama daha güçlü.
- **Gece Efektleri:** Görüş alanı daralmaz ama:
  - Düşman sayısı %50 artar.
  - Yeni "Gece Düşmanları" eklenir (Vampir, Yarasa, Gölge Yürüyücüsü).
  - Loot kalitesi artır (+%25 Magic Find gece bonusu).
  - Blood Moon sadece gece tetiklenir.

### G7. 🏹 Silah Ustalığı (Weapon Mastery) Sistemi
- **Mekanik:** Her silah tipiyle (Melee, Ranged, Bomb, Turret, Pet, Chain, Whip, Glaive, Dual) ne kadar çok savaşırsan o silah tipinde o kadar ustalaşırsın.
- **Seviyeler:** Her silah tipi için 5 Mastery seviyesi:
  1. **Çırak (100 kill):** +%5 hasar o silah tipiyle.
  2. **Kalfa (500 kill):** +%10 hasar, +%5 saldırı hızı.
  3. **Usta (2000 kill):** +%15 hasar, silah tipine özel pasif (ör: Melee: +20 meleeRange, Ranged: +1 pierce).
  4. **Büyükusta (5000 kill):** +%20 hasar, silah tipine özel aktif yetenek.
  5. **Efsane (10000 kill):** +%25 hasar, silah başlangıç tier'i T3 olarak açılır.
- **Kalıcılık:** Mastery kalıcıdır (run'lar arasında korunur).

### G8. 🃏 Kart Evrimi (Card Evolution) Sistemi
- **Mekanik:** Aynı kartı 2. kez çektiğinde (eğer zaten aktifse teklif edilmemeli diye düşünülebilir, bu durumda özel bir mekanikle), kart "Evrimleşir":
  - **Normal → Gelişmiş:** Bonus stats %50 artar, bedel %25 artar.
  - **Gelişmiş → Efsanevi:** Bonus stats 2x olur, ek bir pasif efekt kazanır, bedel %50 artar.
- **Örnek:** 
  - `Iron Will (Normal)`: +50 HP, -%10 hız → 
  - `Iron Will (Gelişmiş)`: +75 HP, -%12.5 hız, kalkan cooldown 45s → 
  - `Iron Will (Efsanevi)`: +100 HP, -%15 hız, kalkan cooldown 30s, kalkan kırılınca 50 thorns 5 saniyeliğine

### G9. 📦 Hazine Odası Sistemi (Treasure Room)
- **Mekanik:** Her 10 dalga sonunda (boss yenildikten sonra) bir "Hazine Odası" portalı açılır.
- **İçerik:** Oyuncu portaldan geçer ve 30 saniyelik bir bonus odaya girer:
  - 3-5 adet garanti Rare+ sandık (tıkla ve al).
  - 1 adet "Dilek Kuyusu": 1000 altın at, rastgele ama güçlü bir buff al (gelecek 5 dalga boyunca).
  - 1 adet "Kadim Yazıt": Okuduğunda kalıcı +1 SP kazanırsın (sadece 1 kez okunabilir).
- **Risk:** Hazine odasındayken süre dolarsa, odadaki tüm düşmanlara kalmış düşmanlar canlanır ve çıkış kapanır (5 Elite düşman spawn olur — yenmedikçe çıkamazsın).

### G10. 🔄 Dinamik Zorluk Ayarlama (Adaptive Difficulty)
- **Mekanik:** Oyun performansını izler ve otomatik zorluk ayarlar:
  - Oyuncu çok rahat geçiyorsa (wave'i 60 saniyeden kısa bitiriyorsa): Düşman HP +%10 sonraki dalga.
  - Oyuncu zorlanıyorsa (HP %20'nin altına düşüyorsa wave sırasında): Sonraki dalga %10 daha az düşman.
  - Bu ayarlama max ±%30 sınırında kalır.
- **İsteğe Bağlı:** Ayarlardan açılıp kapatılabilir. Açıkken kristal ödüller %15 artar.

---

## H. YENİ ESERLER (ARTIFACTS) — 4 Fikir

### H1. 🌀 Portalcı'nın Pusulası (Portal Compass)
- **Cooldown:** 45s
- **Efekt:** Kullanıldığında haritada rastgele bir noktaya anında ışınlanırsın. Işınlanma noktasında 2 saniyelik shockwave (150 yarıçap, 80 hasar, stun 1s).
- **Bonus:** Işınlanma sonrası 3 saniyeliğine %30 hız artışı ve gelen hasardan %25 azalma.
- **Risk:** Nereye ışınlanacağını kontrol edemezsin — düşman kümesinin ortasına da düşebilirsin.

### H2. 🧿 Ruh Hapsi (Soul Prison)
- **Cooldown:** 60s
- **Efekt:** Kullanıldığında 300 yarıçapındaki tüm düşmanları 4 saniyeliğine "Hapis" boyutuna gönderir (ekrandan kaybolurlar). Bu sürede o düşmanlar ne saldırabilir ne hasar alabilir.
- **Bonus:** Süre dolduğunda geri gelen düşmanlar 2 saniyeliğine %50 yavaşlar ve zırhları %30 azalır.
- **Strateji:** Kritik anlarda nefes alma alanı yaratır. Boss faz geçişlerinde kullanışlı.

### H3. ⚗️ Homunculus Şişesi (Homunculus Flask)
- **Cooldown:** 30s
- **Efekt:** Kullanıldığında 15 saniyeliğine bir "Homunculus" çağırır — mini bir klon minyon. Homunculus oyuncunun %50 statlarına sahiptir ve bağımsız saldırır.
- **Özel:** Homunculus ölürse patlama yapar (100 yarıçap, 60 hasar). Süre dolduğunda sessizce kaybolur.

### H4. 📜 Kadim Mühür (Ancient Seal)
- **Cooldown:** 90s (en uzun cooldown)
- **Efekt:** Kullanıldığında haritadaki EN GÜÇLÜ düşmanı (en yüksek HP'li) 5 saniyeliğine "Mühürler" — tamamen hareketsiz ve saldıramaz, ama hasar da almaz.
- **Bonus:** Mühürlü düşman etrafındaki 200 yarıçaptaki diğer düşmanlar demoralize olur: -%30 hasar, -%20 hız (5 saniye).
- **Strateji:** Boss savaşında minyonları temizlemek için boss'u mühürleyebilirsin. Veya tehlikeli Elite'i geçici olarak devre dışı bırakabilirsin.

---

## I. YENİ AURALAR — 4 Fikir

### I1. 🌌 Boşluk Yankısı (Void Echo)
- **Fiyat:** 80.000 Altın
- **Efekt:** Her saldırı %15 ihtimalle "Yankı" yaratır — 0.5 saniye sonra aynı saldırı tekrar eder (bedava ikinci vuruş). Yankılanmış saldırı orijinal hasarın %60'ını verir.
- **Bedel:** Max HP -%100 (çok riskli).

### I2. 🎵 Savaş Ritmi (Battle Rhythm)
- **Fiyat:** 50.000 Altın
- **Efekt:** Saldırı hızı sürekli bir sinüs dalgası ile değişir: 3 saniyelik döngüde min %50 → max %200 saldırı hızı arasında gidip gelir. "Ritim"e uyum sağlayan oyuncu pik anlarda çok yüksek DPS çıkarabilir.
- **Bedel:** Sabit saldırı hızı yerine değişken hız — tahmin edilemezlik.

### I3. 🕷️ Avcının Ağı (Hunter's Web)
- **Fiyat:** 60.000 Altın
- **Efekt:** Hareketsiz durduğunda (1.5 saniye hareket etmeme) oyuncunun etrafında 200 yarıçaplı "avcı ağı" oluşur. Ağa giren düşmanlar %60 yavaşlar ve %20 daha fazla hasar alır. Oyuncu hareket edince ağ 2 saniye sonra kaybolur.
- **Bedel:** Hareket halindeyken saldırı hızı %15 azalır.

### I4. 💫 Yıldız Düşüşü (Starfall)
- **Fiyat:** 100.000 Altın
- **Efekt:** Her 30 saniyede bir, gökyüzünden rastgele 3 noktaya meteor düşer. Her meteor 120 yarıçapında AoE, 200 hasar + 3 saniyelik yanma bırakır. Meteor konumları 2 saniye öncesinden kırmızı dairelerle gösterilir.
- **Bedel:** Meteorlar ayrım yapmaz — oyuncuya da hasar verebilir!

---

## J. YENİ KRİSTAL YÜKSELTMELERİ — 4 Fikir

### J1. 🗡️ Silah Mirası (weapon_legacy) — Max Rank: 3
- **Efekt:** Her rank'te başlangıç silahı +1 nadirlik seviyesi ile başlar.
  - Rank 1: Normal → Magic (1 affix ile).
  - Rank 2: Magic → Rare (2 affix ile).
  - Rank 3: Rare → Rare + garanti 1 T2 affix.
- **Maliyet:** [3000, 6000, 12000]
- **Neden:** Early game'i güçlendirir, farklı başlangıç build'leri keşfetmeye teşvik eder.

### J2. 🧬 Gen Hafızası (gene_memory) — Max Rank: 5
- **Efekt:** Her rank'te önceki run'da kazanılan toplam deneyimin %2'si sonraki run'a aktarılır (başlangıçta bonus XP olarak).
  - Rank 1: %2 XP aktarımı.
  - Rank 5: %10 XP aktarımı.
- **Maliyet:** [2000, 3500, 5500, 8000, 12000]
- **Neden:** Uzun run'ları ödüllendirir. Başarısız run'lar bile bir miktar ilerleme hissi verir.

### J3. 🎰 Şans Artırıcı (fortune_boost) — Max Rank: 3
- **Efekt:** Dalga sonu ödül sandığından çıkan eşyanın nadirlik şansını artırır.
  - Rank 1: Rare ihtimali +%10.
  - Rank 2: Rare ihtimali +%20, Unique ihtimali +%5.
  - Rank 3: Rare ihtimali +%30, Unique ihtimali +%10.
- **Maliyet:** [2500, 5000, 10000]

### J4. 🛡️ İkinci Şans (second_chance) — Max Rank: 2
- **Efekt:** Wave başlangıcında oyuncunun HP'si %50'nin altındaysa, otomatik olarak %50'ye tamamlanır.
  - Rank 1: %40'ın altındaysa %40'a tamamla.
  - Rank 2: %50'nin altındaysa %50'ye tamamla.
- **Maliyet:** [4000, 8000]

---

## K. YENİ SET BONUSLARI — 3 Fikir

### K1. 🎭 SET_SHAPESHIFTER (Şekil Değiştiren)
- **(2) Parça:** Her 30 saniyede bir rastgele bir sınıfın pasif bonusu 10 saniyeliğine aktif olur.
- **(3) Parça:** Bonus süresi 15 saniyeye çıkar. Ayrıca form değişiminde 100 yarıçap AoE shockwave.
- **(4) Parça:** 2 sınıf bonusu aynı anda aktif olur. Değişim süresi 20 saniye.

### K2. 🧪 SET_EXPERIMENT (Deneyci)
- **(2) Parça:** Crafting orblarının başarı şansı %20 artar.
- **(3) Parça:** Orb kullanımında %10 ihtimalle orb tüketilmez (geri iade).
- **(4) Parça:** Lanetli Küre (corrupted_orb) artık negatif suffix eklemez — sadece Broken suffix ekler.

### K3. 🌪️ SET_TEMPEST (Kasırga)
- **(2) Parça:** Hareket halindeyken etrafında küçük kasırga oluşur (60 yarıçap, 5 DPS).
- **(3) Parça:** Kasırga yarıçapı 100'e çıkar, DPS 15 olur. Düşmanları hafifçe iter.
- **(4) Parça:** Kasırga yarıçapı 150, DPS 30. Her 5 saniyede kasırgadaki düşmanlara 1s stun.

---

## L. SKILL TREE GENİŞLETMELERİ — 4 Fikir

### L1. 🌳 6. Yetenek Grubu: "HAYATTA KALMA 2.0" (İleri Savunma)
Mevcut 5 gruba ek olarak, Wave 15+ açılan ileri savunma yetenekleri:

| # | İsim | Stat | Artış/Seviye | Max Seviye |
|---|------|------|-------------|------------|
| 51 | 🔄 İkinci Rüzgâr | reviveHpPercent | +%10 (diriliş HP'si) | 5 |
| 52 | 🩹 Savaş Veteranı | combatArmorBonus | +5 zırh (savaşta ekstra) | 10 |
| 53 | 💪 İnatçı | tenacity (CC süresini azaltma) | -%8 CC süresi | 5 |
| 54 | 🛡️ Son Kale | lowHpDefense (<%30 HP'de hasar azaltma) | +%5 hasar azaltma | 10 |

### L2. 🌳 7. Yetenek Grubu: "EKONOMİ" (Altın & Loot)
| # | İsim | Stat | Artış/Seviye | Max Seviye |
|---|------|------|-------------|------------|
| 55 | 💰 Hazine Avcısı | chestSpawnChance | +%3 ekstra sandık şansı | 5 |
| 56 | 🏪 Pazarlıkçı | shopDiscount | +%5 kervan indirimi | 5 |
| 57 | 📦 Geniş Çanta | backpackSize | +2 envanter slotu | 3 |
| 58 | 🎁 Hediye Paket | bossLootBonus | +%20 boss loot kalitesi | 5 |

### L3. Mevcut Gruplara Ek Yetenekler (Dallanma)
Mevcut skill tree'ye "Dallanma (Branching)" eklenir — belirli bir yeteneğin max seviyeye ulaşması yeni bir yeteneği açar:

- **Vampir (Max 10) → Kan Lordluğu:** Her lifesteal iyileştirmesi %10 ihtimalle 2x olur. (Max 5 seviye, +%2 per level)
- **Kritik Ustası (Max 10) → Yıkıcı Darbe:** Kritik vuruşlar %15 ihtimalle düşmanı 1s stun eder. (Max 3 seviye, +%5 per level)
- **Geniş Alan (Max 10) → Süpernova Tepkisi:** AoE saldırılar %5 ihtimalle 2x yarıçapla patlar. (Max 5 seviye, +%1 per level)
- **Mıknatıs (Max 10) → Vakum:** 15 saniyede bir tüm yerdeki itemler otomatik toplanır. (Max 1 seviye)

### L4. Sınıfa Özel Yetenek Dalı (Class-Specific Skills)
Her sınıf için 3 adet özel yetenek eklenir (sadece o sınıf görebilir):

**Warrior Özel:**
- ⚔️ Parry (Savuşturma): +%3 ihtimalle gelen melee hasarı yansıtma (Max 5)
- 🩸 Kan İzi: Her melee vuruş %2 ihtimalle Bleed (kanama 5 DPS, 3s) uygular (Max 5)
- 💪 Aşırı Güç: Melee hasarın %5'i ekstra knockback olarak uygulanır (Max 5)

**Sniper Özel:**
- 🎯 Headshot: +%2 ihtimalle 5x hasar vuruşu (Max 5)
- 🔭 Marksman: +50 mermi menzili (Max 5)
- ⏱️ Soğukkanlılık: 3 saniye hareketsiz kaldığında sonraki atış garanti kritik (Max 1)

---

## M. YENİ STATUS EFFECT'LER — 3 Fikir

### M1. 💔 Kanama (Bleed)
- **Renk:** Koyu Kırmızı (180, 30, 30)
- **Mekanik:** Saniye başına DoT hasarı (Poison gibi). AMA farklı olarak, kanayan düşman hareket ettikçe hasar ARTAR (%50 bonus DPS hareket halindeyken). Sabit duran düşmana normal DPS.
- **İstifleme:** Max 3 stack. Her stack bağımsız DPS ve süre.
- **Sinerji:** Warrior ve Ninja melee vuruşlarıyla uygulanabilir.

### M2. ⛓️ Zincirlenme (Shackle)
- **Renk:** Gri-Metalik (120, 120, 140)
- **Mekanik:** Zincirlenmiş düşman 3 saniye boyunca mevcut pozisyonundan 100 birimden fazla uzaklaşamaz (görünmez zincir). Hareket etmeye çalışır ama geri çekilir.
- **Bonus:** Zincirlenmiş düşmana vurulan hasar %15 artar (sabit hedef avantajı).
- **Sinerji:** Flail/Chain silahlarıyla otomatik uygulanır.

### M3. 🔮 Lanet (Hex)
- **Renk:** Koyu Mor (100, 30, 130)  
- **Mekanik:** Lanetlenmiş düşmanın zırhı tamamen kaldırılır (0'a düşer) ve gelen hasar %20 artar. Süre: 4 saniye.
- **Özel:** Lanetli düşman öldüğünde %20 ihtimalle laneti yakınlardaki 2 düşmana yayar (bulaşıcı lanet).
- **Sinerji:** Sorcerer ve Curse kartlarıyla tetiklenebilir.

---

## 📊 FİKİR ÖNCELİK MATRİSİ

| Öncelik | Fikirler | Neden |
|---------|----------|-------|
| 🔴 Kritik (İlk Ekle) | G3 (Harita Modifikatörleri), E1 (Kristal Ejderha Boss), E3 (Mini-Boss), G5 (Combo Finisher) | Oyun döngüsüne derinlik katar, replayability artırır |
| 🟠 Yüksek | A1 (Chronomancer), A3 (Monk), C1 (Shadow Clone), C12 (Fırın), G8 (Kart Evrimi) | Yeni oynanış tarzları ve stratejiler |
| 🟡 Orta | B1 (Zincirli Tırpan), B2 (Geri Dönen Disk), D1 (Ayna Gözcüsü), D4 (Parazit), F6 (Element Ustası) | İçerik çeşitliliği |
| 🟢 Düşük (QoL) | G4 (Üs Sistemi), G7 (Silah Mastery), G10 (Adaptif Zorluk), J2 (Gen Hafızası) | Meta-progression ve polish |

---

> **NOT:** Bu fikirler mevcut `YENI_OZELLIKLER_PLANI.md` ile çakışmamaktadır. O plandaki Necromancer, Bard, Bumerang, Tuzak, Boks Eldiveni, Mimic ve yeni auralar bu dosyada tekrar edilmemiştir. İki dosya birbirini tamamlar niteliktedir.

> **Dengeleme Notu:** Tüm sayısal değerler taslaktır. Gerçek implementasyonda `AGENTS.md`'deki Power Budget Rule ve Numeric Envelopes'a uygun olarak ayarlanmalıdır.
