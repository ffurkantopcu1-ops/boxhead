from logic.data_loader import load_data


class SynergySystem:
    # Kaynak: data/synergies.json
    SYNERGIES = load_data('synergies')

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
