from logic.data_loader import load_data


class SynergySystem:
    # Kaynak: data/synergies.json
    SYNERGIES = load_data('synergies')

    def __init__(self):
        self.active_synergies = []
        # Uygulanan bonusların defteri: {sinerji_id: {stat: val}}.
        # Sinerji bonusları skills_permanent'a KALICI yazılır; kart kaldırma
        # mekaniği olmadığı için bugün geri alma gerekmiyor, ama ileride
        # (kart satma/reset) eklenirse remove_synergy() ile temiz dönülebilir.
        self.applied_bonuses = {}

    def check_synergies(self, active_card_ids, player):
        """Check and apply any newly unlocked synergies."""
        # Döngü içinde return edilince aynı kartla açılan 2. sinerji kaçıyordu;
        # hepsi uygulanır, UI bildirimi için ilki döndürülür.
        newly_activated = []
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
                self.applied_bonuses[syn['id']] = dict(syn['bonus'])
                newly_activated.append(syn)

        if newly_activated:
            # Recalculate stats (tüm sinerjiler uygulandıktan sonra bir kez)
            if hasattr(player, 'inv_manager'):
                player.inv_manager.recalculate_stats()
                player.hp = min(player.hp, player.max_hp)
            return newly_activated[0]  # UI bildirimi için ilk sinerji
        return None
    
    def remove_synergy(self, synergy_id, player):
        """Bir sinerjinin skills_permanent katkısını geri alır.

        Bugün hiçbir yerden çağrılmıyor (kart kaldırma yok); kalıcı yazmanın
        tek yönlü olmasını kırılganlıktan çıkarmak için tutulur.
        """
        bonus = self.applied_bonuses.pop(synergy_id, None)
        if not bonus:
            return False
        sp = getattr(player, 'skills_permanent', {})
        for stat, val in bonus.items():
            sp[stat] = sp.get(stat, 0) - val
        player.skills_permanent = sp
        if synergy_id in self.active_synergies:
            self.active_synergies.remove(synergy_id)
        if hasattr(player, 'inv_manager'):
            player.inv_manager.recalculate_stats()
            player.hp = min(player.hp, player.max_hp)
        return True
