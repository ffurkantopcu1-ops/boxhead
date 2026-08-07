import random

class MockItemSystem:
    def __init__(self):
        self.bases = [
            {'name': 'Sword T4', 'tier': 4},
            {'name': 'Sword T3', 'tier': 3},
            {'name': 'Sword T2', 'tier': 2},
            {'name': 'Sword T1', 'tier': 1}
        ]

    def generate(self, wave_level):
        unlocked_tier = 4
        if wave_level >= 30: unlocked_tier = 1
        elif wave_level >= 20: unlocked_tier = 2
        elif wave_level >= 10: unlocked_tier = 3
        
        valid_bases = [b for b in self.bases if b.get('tier', 4) >= unlocked_tier]
        return random.choice(valid_bases)

def test_tier_system():
    print("Testing Tiered Item System...")
    isys = MockItemSystem()
    
    # 1. Wave 5: Only T4
    results_w5 = [isys.generate(5)['name'] for _ in range(50)]
    assert all(r == 'Sword T4' for r in results_w5)
    print("  - Wave 5 test passed (Only T4)")
    
    # 2. Wave 15: T4 and T3
    results_w15 = [isys.generate(15)['name'] for _ in range(100)]
    assert 'Sword T3' in results_w15
    assert 'Sword T4' in results_w15
    assert 'Sword T2' not in results_w15
    print("  - Wave 15 test passed (T4, T3)")
    
    # 3. Wave 25: T4, T3, T2
    results_w25 = [isys.generate(25)['name'] for _ in range(100)]
    assert 'Sword T2' in results_w25
    assert 'Sword T1' not in results_w25
    print("  - Wave 25 test passed (T4, T3, T2)")
    
    # 4. Wave 35: All
    results_w35 = [isys.generate(35)['name'] for _ in range(100)]
    assert 'Sword T1' in results_w35
    print("  - Wave 35 test passed (All tiers)")

if __name__ == "__main__":
    test_tier_system()
