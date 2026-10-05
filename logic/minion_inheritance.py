"""Single-pass pet combat inheritance, independent of stat source."""
# Only these weapons transfer their own modifiers without the card.
WEAPON_STATS = {
    'physDmg': 'minionPhysDmgFlat', 'physDmgFlat': 'minionPhysDmgFlat',
    'physDmgMult': 'minionPhysDmgMult',
    'fireDamage': 'minionFireDmgFlat', 'fireDmgFlat': 'minionFireDmgFlat',
    'fireDmgMult': 'minionFireDmgMult',
    'frostDamage': 'minionFrostDmgFlat', 'frostDmgFlat': 'minionFrostDmgFlat',
    'frostDmgMult': 'minionFrostDmgMult', 'elementDmgMult': 'minionElementDmgMult',
    'poisonDps': 'minionPoisonDpsFlat', 'dotDmgMult': 'minionDotDmgMult',
    'attack_speed_bonus': 'minionRate', 'attack_speed_mult': 'minionRate', 'fireRate': 'minionRate',
    'projectileCount': 'minionProjectileCount', 'bounce': 'minionBounce', 'pierce': 'minionPierce',
    'critChance': 'minionCrit', 'critDmg': 'minionCritDmg',
}

# These are already consumed centrally for all owner attacks, including pets.
SHARED_EFFECTS = frozenset(('armorPen', 'armorPenFlat', 'bossDmgMult', 'brutal',
    'fullHealthDmg', 'lowHealthDmg', 'lowHpExec', 'executeExplosion',
    'killComboDmg', 'statusDuration', 'frost_slow', 'thiefChance',
    'blackHoleChance', 'treePoisonConversion', 'treeSingleShot', 'treeNoCrit'))

# Defense/resource recovery remains on the owner; pets are immortal.
EXCLUDED = frozenset(('max_hp', 'maxHp', 'max_hp_pct', 'max_hp_mult', 'armor',
    'maxEnergyShield', 'esRegen', 'esDelayReduction', 'regen', 'hpRegen',
    'combatRegen', 'dodgeChance', 'lifesteal', 'orbHealMult', 'reflectionAura',
    'shieldExplosion', 'thorns', 'damage_taken_mult'))

def is_tamer_weapon(item):
    return bool(item and (item.get('isMinion') or item.get('isCommander')))

def combat_stats(owner):
    stats = owner.stats
    result = {key: value for key, value in stats.items() if key not in EXCLUDED}
    if not getattr(owner, 'has_minion_inheritance', False):
        return result
    for source, target in WEAPON_STATS.items():
        # Aliases are already normalized by InventoryManager.
        if source == 'attack_speed_mult':
            continue
        value = stats.get(source, 0)
        if source == 'critChance':
            value -= .05
        if source == 'projectileCount':
            value = max(0, value-1)
        result[target] = result.get(target, 1 if target in
            ('minionRate', 'minionRange', 'minionProjectileCount') else 0) + value
    result['minionDamage'] = result.get('minionDamage', 0) + stats.get('dmgMult', 1)-1
    result['minionRange'] = result.get('minionRange', 1) * max(.1, 1+stats.get('meleeRangeMult', 0))
    result['minionExtraRange'] = max(0, stats.get('meleeRange', 0)+stats.get('meleeRangeFlat', 0))+max(0, stats.get('range', 0))
    result['minionConditionalMult'] = owner.get_conditional_dmg_mult()
    from logic.inventory_manager import InventoryManager
    base_speed = InventoryManager.CLASS_BASES.get(owner.class_id, {}).get('speed', 4.8)
    result['minionMoveMult'] = owner.get_movement_speed() / max(.1, base_speed)
    # A pet's auto attack has no separate skill CD: cooldown reduction scales it.
    result['minionCooldownMult'] = max(.1, 1-min(.9, stats.get('cooldownReduction', 0)))
    return result
