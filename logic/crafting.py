"""Affordable, directed bench craft alongside risky currency operations."""
from logic.item_system import ItemSystem


def recipes(item):
    kind = item.get('type')
    if kind not in ('weapon','helmet','chest','amulet','pet','artifact'):
        return []
    from logic.affix_rules import affix_pool
    result = []
    for side in ('prefixes','suffixes'):
        for aff in affix_pool(item,side,ItemSystem.affixes):
            result.append(dict(id=side+':'+aff['stat'], side=side, **aff))
    return result



def recipe_tier(wave, item=None):
    from logic.affix_rules import best_tier, item_level
    return best_tier(min(wave,item_level(item))) if item is not None else best_tier(wave)


def recipe_cost(wave, item=None):
    return {3:50, 2:300, 1:1200}[recipe_tier(wave,item)]


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
    cost = recipe_cost(wave,item)
    if player.gold < cost:
        return f'Bu tarif için {cost} altın gerekiyor.'
    tier = recipe_tier(wave,item)
    from logic.affix_rules import bench_value
    value = bench_value(recipe,tier)
    # Replacing the one bench modifier preserves every natural roll.
    for old_side,a in crafted:
        item[old_side].remove(a)
    item.setdefault(side,[]).append(dict(name=f"{recipe['name']} (T{tier})",base_name=recipe['name'],
                                       stat=recipe['stat'],val=value,tier=tier,
                                       label='P' if side=='prefixes' else 'S',crafted=True))
    if rarity == 'Normal':
        item['rarity'] = 'Magic'
    ItemSystem().update_item_name(item)
    player.gold -= cost
    player.inv_manager.recalculate_stats()
    game = getattr(player,'game',None)
    if game and hasattr(game,'track_quest'):
        game.track_quest('spend_gold',cost)
    return None


def advanced_recipes(item, player=None):
    """Explicit modifier selection removes repeated add/remove gambling."""
    from logic.affix_rules import item_level, best_tier
    if not recipes(item) or item.get('is_corrupted'):
        return []
    result = [dict(id='salvage',name='Söküm',side='işlem',operation=True,cost=0,
                   desc='Eşyayı parçalar. Kuşanılan eşya sökülemez. Kazanım: '+str(salvage_yield(item))+' işçilik özü.')]
    for side in ('prefixes','suffixes'):
        for aff in item.get(side,[]):
            if aff.get('fractured'): continue
            stat=aff['stat'];label=aff.get('base_name',stat)
            result.append(dict(id='remove:'+side+':'+stat,name='Çıkar: '+label,side=side,operation=True,cost=2,desc='Yalnız seçilen özelliği kaldırır. Diğer özellikler korunur.'))
            if aff.get('tier',0)>best_tier(item_level(item)):
                result.append(dict(id='upgrade:'+side+':'+stat,name='Geliştir: '+label,side=side,operation=True,cost=5,desc='Seçilen özelliği bir tier geliştirir. Eşya seviyesi sınırını aşmaz.'))
            if not aff.get('crafted') and aff.get('tier',0)>0 and not any(a.get('fractured') for g in ('prefixes','suffixes') for a in item.get(g,[])):
                result.append(dict(id='fracture:'+side+':'+stat,name='Sabitle: '+label,side=side,operation=True,cost=12,desc='Seçilen doğal özellik silinemez ve yeniden zar atılamaz. Eşya başına bir sabit özellik.'))
    if player is not None:
        from logic.affix_rules import affix_pool
        limit={'Normal':1,'Magic':1,'Rare':2,'Unique':3}.get(item.get('rarity'),0)
        existing={a['stat'] for g in ('prefixes','suffixes') for a in item.get(g,[])}
        for donor in player.inventory:
            if donor is item or donor.get('is_corrupted'):continue
            for side in ('prefixes','suffixes'):
                if len(item.get(side,[]))>=limit:continue
                pool={a['stat'] for a in affix_pool(item,side,ItemSystem.affixes)}
                for aff in donor.get(side,[]):
                    if aff.get('fractured') or aff.get('crafted') or aff.get('tier',0)<best_tier(item_level(item)):continue
                    if aff['stat'] not in pool or aff['stat'] in existing:continue
                    label=aff.get('base_name',aff['stat'])
                    result.append(dict(id=f"transfer:{id(donor)}:{side}:{aff['stat']}",name='Aktar: '+label,side=side,operation=True,cost=6,
                                       desc=f"{donor.get('name','Çanta eşyası')} üzerinden seçilen özelliği taşır. Kaynak eşya bu özelliği kaybeder, diğer özellikleri korunur."))
    return result


def salvage_yield(item):
    return {'Normal':1,'Magic':2,'Rare':4,'Unique':6}.get(item.get('rarity'),0)


def apply_advanced(player,item,operation_id):
    from logic.affix_rules import affix_pool,bench_value
    owned = any(it is item for it in player.inventory) or any(it is item for it in player.inv_manager.equipped.values())
    if not owned:return 'Eşya artık sende değil.'
    option=next((r for r in advanced_recipes(item,player) if r['id']==operation_id),None)
    if option is None:return 'İşlem artık uygun değil.'
    if operation_id=='salvage':
        if any(it is item for it in player.inv_manager.equipped.values()):return 'Söküm için önce eşyayı çantaya çıkar.'
        player.inventory.remove(item)
        player.craft_dust=getattr(player,'craft_dust',0)+salvage_yield(item)
        return None
    dust=getattr(player,'craft_dust',0)
    if dust<option['cost']:return f"{option['cost']} işçilik özü gerekiyor. Kullanmadığın eşyaları sökebilirsin."
    if operation_id.startswith('transfer:'):
        import copy
        _,token,side,stat=operation_id.split(':')
        donor=next(it for it in player.inventory if id(it)==int(token))
        source=next(a for a in donor[side] if a['stat']==stat)
        item.setdefault(side,[]).append(copy.deepcopy(source))
        donor[side].remove(source)
        if item.get('rarity')=='Normal':item['rarity']='Magic'
        player.craft_dust=dust-option['cost']
        ItemSystem().update_item_name(donor)
        ItemSystem().update_item_name(item)
        player.inv_manager.recalculate_stats()
        return None
    action,side,stat=operation_id.split(':')
    aff=next(a for a in item[side] if a['stat']==stat and not a.get('fractured'))
    if action=='remove':item[side].remove(aff)
    elif action=='fracture':aff['fractured']=True
    elif action=='upgrade':
        definition=next((a for a in affix_pool(item,side,ItemSystem.affixes) if a['stat']==stat),None)
        if definition is None:return 'Bu özellik artık eşya ile uyumlu değil.'
        tier=aff['tier']-1
        aff.update(tier=tier,val=bench_value(definition,tier),name=f"{definition['name']} (T{tier})")
    player.craft_dust=dust-option['cost']
    player.inv_manager.recalculate_stats()
    ItemSystem().update_item_name(item)
    return None
