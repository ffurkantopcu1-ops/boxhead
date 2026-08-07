
import math

class MockPlayer:
    def __init__(self, stats):
        self.stats = stats

def calculate_minion_dmg(base_dmg, minion_dmg_stat):
    # minion_dmg_stat is what inventory_manager.py produces (base 1.0 + bonuses)
    total_mult = minion_dmg_stat 
    # Simplified calculation based on minion.py
    final_dmg = base_dmg * total_mult
    return final_dmg

def calculate_minion_hp(base_hp, minion_hp_stat):
    # minion_hp_stat is base 1.0 + bonuses
    final_hp = base_hp * minion_hp_stat
    return final_hp

# Stats from item_system.py after fix
pets = {
    "Yavru Kurt (T1)": {"minionDamage": 0.08, "minionMaxHp": 0.40, "base_dmg": 45},
    "Alfa Kurt (T3)": {"minionDamage": 0.60, "minionMaxHp": 3.00, "base_dmg": 45},
    "Ejder Yavrusu (T1)": {"minionDamage": 0.12, "minionMaxHp": 0.60, "base_dmg": 35},
    "Kadim Ejder (T3)": {"minionDamage": 0.80, "minionMaxHp": 4.50, "base_dmg": 35},
}

print("--- PET STAT VERIFICATION (AFTER FIX) ---")
for name, data in pets.items():
    # Base multiplier is 1.0
    stat_dmg = 1.0 + data["minionDamage"]
    stat_hp = 1.0 + data["minionMaxHp"]
    
    dmg = calculate_minion_dmg(data["base_dmg"], stat_dmg)
    hp = calculate_minion_hp(100, stat_hp) # Base minion HP is 100
    
    print(f"{name}:")
    print(f"  Multiplier: {stat_dmg:.2f}x")
    print(f"  Damage: {dmg:.2f}")
    print(f"  HP: {hp:.2f}")
    print("-" * 30)
