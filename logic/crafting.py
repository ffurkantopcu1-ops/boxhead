"""Affordable, directed bench craft alongside risky currency operations."""
from logic.item_system import ItemSystem


def recipes(item):
    kind = item.get('type')
    if kind not in ('weapon','helmet','chest','amulet','pet','artifact'):
        return []
    group = 'weapon' if kind == 'weapon' else ('armor' if kind in ('helmet','chest') else ('pet' if kind == 'pet' else 'utility'))
    result = []
    for side in ('prefixes','suffixes'):
        for aff in ItemSystem.affixes.get(group+'_'+side, []):
            stat = aff['stat']
            if kind == 'weapon':
                melee = item.get('isMelee',False)
                helper = item.get('isMinion') or item.get('isCommander') or item.get('isTurret')
                if stat in ('bounce','projectileCount','spreadAngle') and melee:
                    continue
                if stat == 'minionCount' and not helper:
                    continue
                if stat == 'meleeRangeMult' and not melee:
                    continue
            result.append(dict(id=side+':'+stat, side=side, **aff))
    return result


def recipe_tier(wave):
    return 1 if wave >= 20 else (2 if wave >= 10 else 3)


def recipe_cost(wave):
    return {3:50, 2:300, 1:1200}[recipe_tier(wave)]


def apply_recipe(player, item, recipe_id, wave):
    if item.get('is_corrupted'):
        return 'Mühürlü eşya değiştirilemez.'
    # The target must still be owned; detached UI references never create items.
    if not any(it is item for it in player.inventory) and not any(it is item for it in player.inv_manager.equipped.values()):
        return 'Eşya artık sende değil.'
    recipe = next((r for r in recipes(item) if r['id'] == recipe_id), None)
    if recipe is None:
        return 'Bu tarif bu eşya için uygun değil.'
    crafted = [(side,a) for side in ('prefixes','suffixes') for a in item.get(side,[]) if a.get('crafted')]
    existing = [a for side in ('prefixes','suffixes') for a in item.get(side,[]) if not a.get('crafted')]
    if any(a['stat'] == recipe['stat'] for a in existing):
        return 'Bu özellik zaten var. Başka bir tarif seç.'
    rarity = item.get('rarity','Normal')
    limit = {'Normal':1,'Magic':1,'Rare':2,'Unique':3}.get(rarity,0)
    side = recipe['side']
    if sum(not a.get('crafted') for a in item.get(side,[])) >= limit:
        return 'Bu özellik tarafında boş yuva yok.'
    cost = recipe_cost(wave)
    if player.gold < cost:
        return f'Bu tarif için {cost} altın gerekiyor.'
    tier = recipe_tier(wave)
    lo, hi = recipe['tiers'][tier]
    value = round((lo+hi)/2,2)
    # Replacing the one bench modifier preserves every natural roll.
    for old_side,a in crafted:
        item[old_side].remove(a)
    item.setdefault(side,[]).append(dict(name=f"{recipe['name']} (T{tier})",base_name=recipe['name'],
                                       stat=recipe['stat'],val=value,tier=tier,
                                       label='P' if side=='prefixes' else 'S',crafted=True))
    if rarity == 'Normal':
        item['rarity'] = 'Magic'
    player.gold -= cost
    player.inv_manager.recalculate_stats()
    game = getattr(player,'game',None)
    if game and hasattr(game,'track_quest'):
        game.track_quest('spend_gold',cost)
    return None
