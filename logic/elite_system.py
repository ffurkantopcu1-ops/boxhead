import random
import math

class EliteSystem:
    """Düşmanlara rastgele elit modifikatörler ekleyen sistem."""
    
    MODIFIERS = [
        {
            "id": "swift",
            "name": "⚡ Hızlı",
            "color": (52, 152, 219),
            "hp_mult": 1.0,
            "dmg_mult": 1.0,
            "speed_mult": 1.8,
            "reward_mult": 1.5,
            "desc": "Çok hızlı hareket eder"
        },
        {
            "id": "thorny",
            "name": "🌵 Dikenli",
            "color": (39, 174, 96),
            "hp_mult": 1.3,
            "dmg_mult": 1.0,
            "speed_mult": 0.9,
            "reward_mult": 1.8,
            "thorns": 0.15,  # %15 of damage dealt is reflected
            "desc": "Vurunca hasar yansıtır"
        },
        {
            "id": "vampiric",
            "name": "🦇 Vampir",
            "color": (192, 57, 43),
            "hp_mult": 1.2,
            "dmg_mult": 1.3,
            "speed_mult": 1.0,
            "reward_mult": 2.0,
            "lifesteal": 0.20,  # Heals 20% of damage dealt
            "desc": "Vurduğunda can çalar"
        },
        {
            "id": "armored",
            "name": "🛡️ Zırhlı",
            "color": (149, 165, 166),
            "hp_mult": 2.0,
            "dmg_mult": 0.8,
            "speed_mult": 0.7,
            "reward_mult": 2.0,
            "armor": 50,
            "desc": "Çok dayanıklı ama yavaş"
        },
        {
            "id": "berserker",
            "name": "😡 Öfkeli",
            "color": (231, 76, 60),
            "hp_mult": 0.8,
            "dmg_mult": 2.5,
            "speed_mult": 1.3,
            "reward_mult": 2.5,
            "desc": "Az canlı ama çok güçlü"
        },
        {
            "id": "splitting",
            "name": "🔀 Bölünen",
            "color": (155, 89, 182),
            "hp_mult": 0.6,
            "dmg_mult": 0.7,
            "speed_mult": 1.1,
            "reward_mult": 3.0,
            "splits_on_death": 2,  # Spawns 2 mini copies
            "desc": "Öldürünce 2'ye bölünür"
        },
        {
            "id": "frozen",
            "name": "❄️ Dondurucu",
            "color": (41, 128, 185),
            "hp_mult": 1.5,
            "dmg_mult": 1.0,
            "speed_mult": 0.8,
            "reward_mult": 2.0,
            "frost_aura": True,  # Slows nearby player
            "desc": "Yakınındaki oyuncuyu yavaşlatır"
        },
        {
            "id": "shielded",
            "name": "🔮 Kalkanlı",
            "color": (241, 196, 15),
            "hp_mult": 1.0,
            "dmg_mult": 1.0,
            "speed_mult": 1.0,
            "reward_mult": 2.5,
            "shield_hp": 0.5,  # 50% of max HP as shield that regens
            "desc": "Enerji kalkanına sahip"
        }
    ]
    
    @staticmethod
    def should_apply(wave_level):
        """Wave seviyesine göre elit düşman olma şansı."""
        if wave_level < 5:
            return False
        # Wave 5: %10, Wave 10: %20, Wave 20: %35, cap at %40
        chance = min(0.40, 0.05 + wave_level * 0.015)
        return random.random() < chance
    
    @staticmethod
    def apply_modifier(enemy, wave_level):
        """Düşmana rastgele bir elit modifikatör uygular."""
        # Wave 15+ can get 2 modifiers
        num_mods = 1
        if wave_level >= 15 and random.random() < 0.2:
            num_mods = 2
        
        available = EliteSystem.MODIFIERS.copy()
        random.shuffle(available)
        applied = []
        
        for mod in available[:num_mods]:
            enemy.max_hp *= mod['hp_mult']
            enemy.hp = enemy.max_hp
            enemy.dmg *= mod['dmg_mult']
            enemy.speed *= mod['speed_mult']
            
            # Store modifier data on the enemy
            if not hasattr(enemy, 'elite_mods'):
                enemy.elite_mods = []
            enemy.elite_mods.append(mod)
            
            # Mark as elite
            enemy.is_elite = True
            enemy.elite_color = mod['color']
            enemy.elite_reward_mult = getattr(enemy, 'elite_reward_mult', 1.0) * mod['reward_mult']
            
            # Special properties
            if 'thorns' in mod:
                enemy.thorns = mod['thorns']
            if 'lifesteal' in mod:
                enemy.elite_lifesteal = mod['lifesteal']
            if 'armor' in mod:
                enemy.elite_armor = mod.get('armor', 0)
            if 'splits_on_death' in mod:
                enemy.splits_on_death = mod['splits_on_death']
            if 'frost_aura' in mod:
                enemy.frost_aura = True
            if 'shield_hp' in mod:
                enemy.elite_shield = enemy.max_hp * mod['shield_hp']
                enemy.elite_shield_max = enemy.elite_shield
            
            applied.append(mod)
        
        # Visual: Make elite enemies slightly bigger
        enemy.radius = int(enemy.radius * 1.2)
        
        return applied
    
    @staticmethod
    def get_elite_name(enemy):
        """Get display name for an elite enemy."""
        if not hasattr(enemy, 'elite_mods') or not enemy.elite_mods:
            return ""
        names = [m['name'] for m in enemy.elite_mods]
        return " ".join(names)
