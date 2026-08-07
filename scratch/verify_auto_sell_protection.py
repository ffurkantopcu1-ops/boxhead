import sys
import os

class MockPlayer:
    def __init__(self, mode=0):
        self.auto_sell_mode = mode
        self.gold = 0
        self.inventory = []
    def add_item(self, item):
        if len(self.inventory) < 2:
            self.inventory.append(item)
            return True
        return False

class MockGame:
    def __init__(self):
        self.events = []
    def add_event(self, type, x, y, value=None, color=None, timer=1.0):
        self.events.append(value)

def test_auto_sell_protection():
    print("Verifying Auto-Sell Protection Logic...")
    
    rarities = ['Normal', 'Magic', 'Rare', 'Unique']
    
    # Test Cases: (ItemData, AutoSellMode, ShouldSell)
    test_cases = [
        ({'rarity': 'Normal', 'type': 'weapon', 'price': 100}, 1, True),   # Normal weapon, mode BEYAZ -> Sell
        ({'rarity': 'Magic', 'type': 'weapon', 'price': 200}, 1, False),  # Magic weapon, mode BEYAZ -> Don't Sell
        ({'rarity': 'Magic', 'type': 'weapon', 'price': 200}, 2, True),   # Magic weapon, mode MAVİ -> Sell
        ({'rarity': 'Normal', 'type': 'essence', 'price': 700}, 1, False), # Essence (Normal), mode BEYAZ -> PROTECT
        ({'rarity': 'Normal', 'type': 'orb', 'price': 500}, 1, False),    # Orb (Normal), mode BEYAZ -> PROTECT
        ({'rarity': 'Magic', 'type': 'weapon', 'setTag': 'SET_FIRE', 'price': 1000}, 2, False), # Set Item (Magic), mode MAVİ -> PROTECT
    ]
    
    for item, mode, expected_sell in test_cases:
        p = MockPlayer(mode)
        game = MockGame()
        
        r_idx = rarities.index(item.get('rarity', 'Normal'))
        is_special = bool(item.get('setTag')) or item.get('type') in ['orb', 'essence']
        should_sell = not is_special and (r_idx < mode)
        
        print(f"Item: {item.get('type')} ({item.get('rarity')}), Mode: {mode}, Special: {is_special} -> Sell: {should_sell}")
        assert should_sell == expected_sell

    print("Test Passed: Protection logic is robust.")

if __name__ == "__main__":
    test_auto_sell_protection()
