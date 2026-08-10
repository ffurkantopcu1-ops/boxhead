import random
import math

from logic.data_loader import load_data

_MODIFIERS = load_data('elite_modifiers')
for _m in _MODIFIERS:
    _m['color'] = tuple(_m['color'])

class EliteSystem:
    """Düşmanlara rastgele elit modifikatörler ekleyen sistem."""
    
    # Kaynak: data/elite_modifiers.json
    MODIFIERS = _MODIFIERS

    @staticmethod
    def should_apply(wave_level, diff_mult=1.0):
        """Wave seviyesine (ve zorluğa) göre elit düşman olma şansı."""
        if wave_level < 5:
            return False
        # Wave 5: %10, Wave 20: %35; zorluk çarpanıyla artar, tavan %75.
        chance = min(0.75, (0.05 + wave_level * 0.015) * diff_mult)
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
            # thorns / elite_lifesteal / frost_aura bayrakları burada kurulur;
            # tüketim noktaları entities/enemy.py içindedir
            # (take_damage -> thorns, attack_player -> elite_lifesteal,
            #  update -> frost_aura).
            if 'thorns' in mod:
                enemy.thorns = mod['thorns']
            if 'lifesteal' in mod:
                enemy.elite_lifesteal = mod['lifesteal']
            if 'armor' in mod:
                # Denge: elite_armor hiçbir yerde okunmuyordu; gerçek zırha yazılır
                enemy.armor = getattr(enemy, 'armor', 0) + mod.get('armor', 0)
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

        # Zorluk degisimi (update_difficulty -> apply_difficulty) base_* uzerinden
        # yeniden hesapladigi icin elit bonuslari siliniyordu (H4)
        enemy.base_max_hp = enemy.max_hp
        enemy.base_dmg = enemy.dmg
        enemy.base_speed = enemy.speed
        enemy.base_armor = getattr(enemy, 'armor', 0)

        return applied
