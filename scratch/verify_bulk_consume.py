import sys
import os

class MockPlayer:
    def __init__(self):
        self.inventory = [
            {'name': 'Health Essence', 'type': 'essence', 'essence_type': 'max_hp', 'val': 50},
            {'name': 'Speed Essence', 'type': 'essence', 'essence_type': 'speed', 'val': 0.5},
            {'name': 'Iron Sword', 'type': 'weapon', 'rarity': 'Normal'},
            {'name': 'Armor Essence', 'type': 'essence', 'essence_type': 'armor', 'val': 10}
        ]
        self.essence_stats = {'max_hp': 0, 'speed': 0, 'armor': 0}
        self.hp = 100
        self.max_hp = 100
        
    def consume_essence(self, e_type, val):
        if e_type in self.essence_stats:
            self.essence_stats[e_type] += val
            if e_type == 'max_hp':
                self.hp += val
                self.max_hp += val
            return True
        return False

    def consume_all_essences(self):
        # The logic we just implemented
        essences = [it for it in self.inventory if it.get('type') == 'essence']
        if not essences:
            return 0
        
        count = len(essences)
        for it in essences:
            self.consume_essence(it['essence_type'], it['val'])
            self.inventory.remove(it)
            
        return count

def test_bulk_consume():
    print("Testing Bulk Essence Consumption...")
    p = MockPlayer()
    initial_inv_size = len(p.inventory)
    
    count = p.consume_all_essences()
    
    print(f"  - Consumed {count} essences.")
    assert count == 3
    assert len(p.inventory) == 1
    assert p.inventory[0]['name'] == 'Iron Sword'
    assert p.essence_stats['max_hp'] == 50
    assert p.essence_stats['speed'] == 0.5
    assert p.essence_stats['armor'] == 10
    assert p.max_hp == 150
    
    print("  - Bulk consume test passed!")

if __name__ == "__main__":
    test_bulk_consume()
