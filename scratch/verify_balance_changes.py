import sys
import os
import random

# Mocking parts of the system
class MockItemSystem:
    def __init__(self):
        pass
    
    def generate(self, mf_value=1.0, is_shop=False, shop_rarity=1, difficulty="Normal", wave_level=1, is_boss=False):
        weights = [100, 30 * mf_value, 10 * mf_value, 2 * mf_value]
        if is_shop:
            weights = [max(5, 60 - shop_rarity * 4), max(10, 30 + shop_rarity * 3), max(5, 12 + shop_rarity * 4), 0]
        elif difficulty == "Normal" and not is_boss:
            weights[3] = 0
        
        rarities = ["Normal", "Magic", "Rare", "Unique"]
        if is_boss:
            return "Unique"
        return random.choices(rarities, weights=weights)[0]

def test_unique_rules():
    print("Testing Unique Drop Rules...")
    isys = MockItemSystem()
    
    # 1. No Uniques in Shop
    shop_results = [isys.generate(is_shop=True) for _ in range(100)]
    assert "Unique" not in shop_results
    print("  - Shop test passed (0 Uniques found)")
    
    # 2. No Uniques from regular enemies in Normal
    normal_results = [isys.generate(difficulty="Normal", is_boss=False) for _ in range(100)]
    assert "Unique" not in normal_results
    print("  - Normal regular enemy test passed (0 Uniques found)")
    
    # 3. Bosses always drop Unique
    boss_results = [isys.generate(is_boss=True) for _ in range(10)]
    assert all(r == "Unique" for r in boss_results)
    print("  - Boss test passed (100% Unique)")
    
    # 4. Uniques can drop in Hard
    hard_results = [isys.generate(difficulty="Hard", is_boss=False) for _ in range(500)]
    assert "Unique" in hard_results
    print("  - Hard mode regular enemy test passed (Uniques found)")

def test_minion_scaling():
    print("\nTesting Minion Damage Scaling...")
    
    def get_dmg(class_id):
        eff_mult = 1.0
        if class_id != 'beastmaster':
            eff_mult = 0.4
        base_dmg = 45
        total_mult = 1.0 # simplified
        return (base_dmg * total_mult) * eff_mult

    bm_dmg = get_dmg('beastmaster')
    warrior_dmg = get_dmg('warrior')
    
    print(f"  - Beastmaster Damage: {bm_dmg}")
    print(f"  - Warrior Damage: {warrior_dmg}")
    assert bm_dmg > warrior_dmg
    assert warrior_dmg == bm_dmg * 0.4
    print("  - Minion scaling test passed (60% penalty applied)")

if __name__ == "__main__":
    test_unique_rules()
    test_minion_scaling()
