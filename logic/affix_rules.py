"""Shared loot and bench rules: item level, compatible pools and discrete rolls."""
import random

COUNT_STATS = {'projectileCount', 'bounce', 'pierce', 'minionCount',
               'minionProjectileCount', 'minionPierce', 'minionBounce'}
FLAT_STATS = {'maxHp', 'armor', 'thorns', 'fireDamage', 'frostDamage',
              'poisonDps', 'minionArmor', 'toxicAura', 'shockwave', 'magnetRadius'}

def item_level(item):
    # Old items infer their level from the base, without changing their rolls.
    return max(1, int(item.get('ilvl', {4:1, 3:10, 2:20, 1:30}.get(item.get('tier',4),1))))

def best_tier(level):
    return 1 if level >= 20 else (2 if level >= 10 else 3)

def compatible(item, stat):
    if item.get('type') != 'weapon':
        return True
    melee = item.get('isMelee', False)
    helper = any(item.get(k) for k in ('isCommander','isTurret','isMinion'))
    if stat == 'minionCount': return helper
    if stat in ('meleeRangeMult','shockwave'): return melee
    if stat in ('projectileCount','bounce','spreadAngle'): return not melee and not item.get('isBomb',False)
    return True

def affix_pool(item, side, definitions):
    kind = item.get('type')
    group = 'weapon' if kind == 'weapon' else ('armor' if kind in ('helmet','chest') else ('pet' if kind=='pet' else 'utility'))
    return [a for a in definitions.get(group+'_'+side,[]) if compatible(item,a['stat'])]

def roll_value(affix, tier):
    low, high = affix['tiers'][tier]
    if affix['stat'] in COUNT_STATS | FLAT_STATS:
        return random.randint(int(low), int(high))
    return round(random.uniform(low,high), 4)

def bench_value(affix, tier):
    low,high=affix['tiers'][tier]
    value=(low+high)/2
    return int(round(value)) if affix['stat'] in COUNT_STATS | FLAT_STATS else round(value,4)
