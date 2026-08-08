import pygame

# Aura Sınıfı: Her bir aurayı temsil eder
class Aura:
    def __init__(self, id, name, description, cost, stats):
        self.id = id
        self.name = name
        self.description = description
        self.cost = cost
        self.stats = stats # {stat_name: value}

# Aura Sistemi Yöneticisi
class AuraManager:
    def __init__(self):
        self.auras = {
            # --- TANK / SURVIVAL ---
            "mountain": Aura("mountain", "Dağın Ruhu", "+500 maksimum can; hareket hızı -1.5.", 100000, {"max_hp": 500, "speed": -1.5}),
            "titan_skin": Aura("titan_skin", "Titan Derisi", "+150 zırh ile doğrudan hasarı azaltır.", 125000, {"armor": 150}),
            "juggernaut": Aura("juggernaut", "Ezici Güç", "Saniyede +20 can yenilenmesi sağlar.", 150000, {"hpRegen": 20, "statusDuration": -0.5}),
            "unbreakable": Aura("unbreakable", "Kırılmaz", "+1000 maksimum can; kaçınma şansı 50 puan azalır.", 200000, {"max_hp": 1000, "dodgeChance": -0.5}),
            
            # --- MINION / SUMMONER ---
            "beastmaster": Aura("beastmaster", "Canavar Terbiyecisi", "Tüm minyonların hasarı %50 artar.", 100000, {"minionDamage": 0.5}),
            "swarm_leader": Aura("swarm_leader", "Sürü Lideri", "Aynı anda +2 minyon çağırabilirsin.", 150000, {"minionCount": 2}),
            "pack_mentality": Aura("pack_mentality", "Sürü Psikolojisi", "Aktif her minyon, minyon hasarına %5 katkı sağlar.", 175000, {"minion_synergy": 0.05}),
            "frenzy": Aura("frenzy", "Sürü Öfkesi", "Minyonların saldırı hızı %50 artar.", 125000, {"minionRate": 0.5}),
            
            # --- GLASS CANNON / DPS ---
            "assassin": Aura("assassin", "Suikastçı", "Kritik hasar %50 artar; maksimum can 200 azalır.", 100000, {"critDmg": 0.5, "max_hp": -200}),
            "berserker": Aura("berserker", "Berserker", "Tüm saldırı hasarı %40 artar.", 125000, {"dmgMult": 0.4}),
            "lethality": Aura("lethality", "Ölümcüllük", "Düşman zırhının %50'sini yok sayar.", 150000, {"armorPen": 0.5}),
            "flurry": Aura("flurry", "Mermi Yağmuru", "Saldırı hızı %30 artar.", 125000, {"attack_speed_mult": 0.3}),
            
            # --- ELEMENTAL / MAGIC ---
            "inferno": Aura("inferno", "Cehennem Ateşi", "Her saldırıya 50 sabit ateş hasarı ekler.", 100000, {"fireDamage": 50}),
            "frostbite": Aura("frostbite", "Ayaz", "Her saldırıya 20 sabit buz hasarı ekler ve hedefi %30 yavaşlatır.", 100000, {"frostDamage": 20, "frost_slow": 0.3}),
            "archmage": Aura("archmage", "Başbüyücü", "Element hasarı %100 artar; fiziksel hasar devre dışı kalır.", 150000, {"elementDmgMult": 1.0, "physDmg": -999}),
            "static": Aura("static", "Statik Alan", "Yakındaki düşmanlara periyodik 30 yıldırım hasarı verir.", 125000, {"static_field": 30}),
            
            # --- ECONOMY / UTILITY ---
            "midas": Aura("midas", "Midas'ın Dokunuşu", "Tüm altın kazanımını %100 artırır.", 100000, {"goldGain": 1.0}),
            "scavenger": Aura("scavenger", "Leşçil", "Nadir eşya bulma değerini %50 artırır.", 100000, {"magicFind": 0.5}),
            "fleet": Aura("fleet", "Rüzgâr Ayak", "Hareket hızına +2.5 ekler.", 100000, {"speed": 2.5}),
            "time_warp": Aura("time_warp", "Zaman Bükme", "Eser ve özel yetenek bekleme sürelerini %15 azaltır.", 150000, {"cooldownReduction": 0.15}),
            
            # --- YENİ EKLENEN AURALAR ---
            "decay_aura": Aura("decay_aura", "Çürüme Aurası", "Yakınındaki düşmanların HP'sini sürekli azaltır.", 150000, {"decayAura": 1}),
            "magnetic_aura": Aura("magnetic_aura", "Manyetik Alan", "Düşman mermilerini yavaşlatır.", 200000, {"magneticAura": 1}),
            "reflection_aura": Aura("reflection_aura", "Ayna Kalkan", "Alınan hasarın %50'sini geri yansıtır.", 180000, {"reflectionAura": 0.5}),
            "starfall_aura": Aura("starfall_aura", "Yıldız Yağmuru", "Sürekli olarak yakındaki düşmanlara meteor düşürür.", 250000, {"starfallAura": 1})
        }
        # Not: Toplamda 40'a tamamlanabilir, şimdilik temel 20 adet eklendi.

    def get_aura(self, aura_id):
        return self.auras.get(aura_id)

    def get_all_auras(self):
        return list(self.auras.values())
