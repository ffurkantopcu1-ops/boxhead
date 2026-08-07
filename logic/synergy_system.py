class SynergySystem:
    SYNERGIES = [
        {
            "id": "fire_and_ice",
            "name": "🌊 Buhar Patlaması",
            "desc": "Ateş + Buz = Her 10sn tüm düşmanlara 50 hasar",
            "required_cards": ["frozen_time", "blood_fire"],
            "bonus": {"periodicAoeDmg": 50}
        },
        {
            "id": "glass_berserker",
            "name": "💥 Cam Berserker",
            "desc": "Cam Top + Berserker = Kritik şans +%25",
            "required_cards": ["glass_cannon", "berserker_rage"],
            "bonus": {"critChance": 0.25}
        },
        {
            "id": "undead_commander",
            "name": "💀 Ölümsüz Komutan",
            "desc": "Ölümsüz Ordu + Savaş Komutanı = Minyon hızı +%50",
            "required_cards": ["undead_army", "war_commander"],
            "bonus": {"minionRate": 0.5}
        },
        {
            "id": "iron_fortress",
            "name": "🏰 Demir Kale",
            "desc": "Demir İrade + Taş Deri = Yansıtma hasarı 30",
            "required_cards": ["iron_will", "iron_skin"],
            "bonus": {"thorns": 30}
        },
        {
            "id": "death_dealer",
            "name": "☠️ Ölüm Tüccarı",
            "desc": "Ölüm Anlaşması + Cellat = Execute eşiği +%15",
            "required_cards": ["death_pact", "executioner"],
            "bonus": {"lowHpExec": 0.15}
        },
        {
            "id": "speed_demon",
            "name": "⚡ Hız Şeytanı", 
            "desc": "İvmeleyici + Adrenalin = Dodge şansı +%15",
            "required_cards": ["accelerator", "adrenaline"],
            "bonus": {"dodgeChance": 0.15}
        },
        {
            "id": "vampire_lord",
            "name": "🧛 Vampir Lordu",
            "desc": "Vampir Dokunuşu + Kan Ateşi = Can çalma +%20",
            "required_cards": ["vampire_touch", "blood_fire"],
            "bonus": {"lifesteal": 0.20}
        },
        {
            "id": "chaos_crit",
            "name": "🌀 Kaos Kritik",
            "desc": "Kaos Teorisi + Kritik Aşırı Yük = Kritik hasar +%100",
            "required_cards": ["chaos_theory", "crit_overload"],
            "bonus": {"critDmg": 1.0}
        }
    ]
    
    def __init__(self):
        self.active_synergies = []
    
    def check_synergies(self, active_card_ids, player):
        """Check and apply any newly unlocked synergies."""
        for syn in self.SYNERGIES:
            if syn['id'] in self.active_synergies:
                continue
            if all(card_id in active_card_ids for card_id in syn['required_cards']):
                self.active_synergies.append(syn['id'])
                # Apply bonus to player
                sp = getattr(player, 'skills_permanent', {})
                for stat, val in syn['bonus'].items():
                    sp[stat] = sp.get(stat, 0) + val
                player.skills_permanent = sp
                # Recalculate stats
                if hasattr(player, 'inv_manager'):
                    player.inv_manager.recalculate_stats()
                return syn  # Return newly activated synergy for UI notification
        return None
    
    def get_active_synergies(self):
        return [s for s in self.SYNERGIES if s['id'] in self.active_synergies]
