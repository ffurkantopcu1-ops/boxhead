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
            "mountain": Aura("mountain", "Dağın Ruhu (Aura)", "+500 Max HP, -%10 Hız", 100000, {"max_hp": 500, "speed": -1.5}),
            "titan_skin": Aura("titan_skin", "Titan Derisi (Aura)", "+150 Zırh", 125000, {"armor": 150}),
            "juggernaut": Aura("juggernaut", "Juggernaut (Aura)", "Bağışıklık & +20 HP/sn Yenilenme", 150000, {"hpRegen": 20, "statusDuration": -0.5}),
            "unbreakable": Aura("unbreakable", "Kırılmaz (Aura)", "+1000 Max HP, -%50 Kaçınma", 200000, {"max_hp": 1000, "dodgeChance": -0.5}),
            
            # --- MINION / SUMMONER ---
            "beastmaster": Aura("beastmaster", "Canavar Terbiyecisi (Aura)", "Minyon Hasarı +%50", 100000, {"minionDamage": 0.5}),
            "swarm_leader": Aura("swarm_leader", "Sürü Lideri (Aura)", "+2 Maksimum Minyon", 150000, {"minionCount": 2}),
            "pack_mentality": Aura("pack_mentality", "Sürü Psikolojisi (Aura)", "Her minyon için +%5 Hasar", 175000, {"minion_synergy": 0.05}),
            "frenzy": Aura("frenzy", "Öfke Aurası (Aura)", "Minyon Hızı +%50", 125000, {"minionRate": 0.5}),
            
            # --- GLASS CANNON / DPS ---
            "assassin": Aura("assassin", "Suikastçı (Aura)", "+%50 Kritik Hasar, -200 HP", 100000, {"critDmg": 0.5, "max_hp": -200}),
            "berserker": Aura("berserker", "Berserker (Aura)", "+%40 Fiziksel Hasar, +%20 Hasar Alır", 125000, {"dmgMult": 0.4}),
            "lethality": Aura("lethality", "Ölümcüllük (Aura)", "Düşman Zırhının %50'sini Yok Sayar", 150000, {"armorPen": 0.5}),
            "flurry": Aura("flurry", "Mermi Yağmuru (Aura)", "+%30 Saldırı Hızı", 125000, {"attack_speed_mult": 0.3}),
            
            # --- ELEMENTAL / MAGIC ---
            "inferno": Aura("inferno", "Inferno (Aura)", "Saldırılara 50 Ateş Hasarı Ekler", 100000, {"fireDamage": 50}),
            "frostbite": Aura("frostbite", "Donma (Aura)", "Tüm saldırılar düşmanı %30 yavaşlatır", 100000, {"frostDamage": 20, "frost_slow": 0.3}),
            "archmage": Aura("archmage", "Başbüyücü (Aura)", "+%100 Element Hasarı, -%100 Fiziksel", 150000, {"elementDmgMult": 1.0, "physDmg": -999}),
            "static": Aura("static", "Statik Alan (Aura)", "Yakındaki düşmanlara 30 Yıldırım hasarı", 125000, {"static_field": 30}),
            
            # --- ECONOMY / UTILITY ---
            "midas": Aura("midas", "Midas'ın Dokunuşu (Aura)", "+%100 Altın Kazanımı", 100000, {"goldGain": 1.0}),
            "scavenger": Aura("scavenger", "Leşçil (Aura)", "+%50 Magic Find", 100000, {"magicFind": 0.5}),
            "fleet": Aura("fleet", "Rüzgar Ayak (Aura)", "+%30 Hareket Hızı", 100000, {"speed": 2.5}),
            "time_warp": Aura("time_warp", "Zaman Bükme (Aura)", "%15 Cooldown Azalma", 150000, {"cooldownReduction": 0.15})
        }
        # Not: Toplamda 40'a tamamlanabilir, şimdilik temel 20 adet eklendi.

    def get_aura(self, aura_id):
        return self.auras.get(aura_id)

    def get_all_auras(self):
        return list(self.auras.values())
