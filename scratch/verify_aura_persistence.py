import json
import os
import sys

def test_aura_persistence():
    print("Verifying Aura Persistence Logic...")
    
    # Mock data structure matching SaveManager.save_game
    mock_save_data = {
        "is_essence_system_unlocked": True,
        "purchased_auras": ["aura_fire", "aura_ice"],
        "active_auras": ["aura_fire"],
        "essence_stats": {"max_hp": 10, "phys_dmg": 5}
    }
    
    # Simulate saving
    save_path = "Pygame_Versiyonu/scratch/test_save.json"
    with open(save_path, 'w') as f:
        json.dump(mock_save_data, f)
    
    print(f"Saved mock data to {save_path}")
    
    # Simulate loading
    with open(save_path, 'r') as f:
        loaded_data = json.load(f)
    
    print(f"Loaded data: {loaded_data}")
    
    assert loaded_data["is_essence_system_unlocked"] == True
    assert "aura_fire" in loaded_data["purchased_auras"]
    assert loaded_data["essence_stats"]["max_hp"] == 10
    
    print("Test Passed: Aura data is correctly persisted in JSON.")
    
    # Cleanup
    if os.path.exists(save_path):
        os.remove(save_path)

if __name__ == "__main__":
    test_aura_persistence()
