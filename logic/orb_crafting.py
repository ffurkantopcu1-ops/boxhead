"""Directed orb operations, with shared dry-run validation and atomic spending."""
import copy
import random
from logic.affix_rules import affix_pool, roll_value

FAMILIES = {
    'weapon': ('Silah', {'dmgMult','armorPen','bossDmgMult','projectileCount','aoe','meleeRangeMult','brutal','critChance','critDmg','bounce','spreadAngle','shockwave'}),
    'fire': ('Ateş', {'fireDamage','elementDmgMult'}),
    'frost': ('Buz', {'frostDamage','elementDmgMult'}),
    'poison': ('Zehir', {'poisonDps','dotDmgMult','statusDuration','toxicAura'}),
    'defense': ('Savunma', {'armor','thorns','dodgeChance'}),
    'life': ('Yaşam', {'maxHp','hpRegen','combatRegen','orbHealMult','lifesteal'}),
    'speed': ('Hız', {'speed','fireRate','cooldownReduction','killSpeedBoost','minionRate'}),
    'helpers': ('Yardımcı', {'minionCount','minionDamage','minionRate','minionCrit','minionFrostDmgFlat','minionProjectileCount','minionPierce','minionRange','minionBounce','orbitDrones'}),
    'fortune': ('Servet', {'goldGain','magicFind','thiefChance','xpGain','magnetRadius'}),
}
FOCUS_ORBS = {'p_add','s_add','aug'}
CONFIG_ORBS = FOCUS_ORBS | {'transmute','side_chaos'}
SIDES = ('prefixes','suffixes')
LIMITS = {'Normal':0,'Magic':1,'Rare':2,'Unique':3}


def families_for_stat(stat):
    return [key for key,(_,stats) in FAMILIES.items() if stat in stats]


def salvage_families(item):
    return sorted({family for side in SIDES for aff in item.get(side,[])
                   if not aff.get('crafted') and aff.get('tier',0)>0
                   for family in families_for_stat(aff['stat'])})


def candidates(item, side, family=None, target_stat=None):
    from logic.item_system import ItemSystem
    existing={aff['stat'] for group in SIDES for aff in item.get(group,[])}
    return [aff for aff in affix_pool(item,side,ItemSystem.affixes)
            if aff['stat'] not in existing and aff['stat']!=target_stat
            and (family is None or aff['stat'] in FAMILIES.get(family,('',set()))[1])]


def plan(item, orb_id, side, family=None, target_stat=None):
    if item.get('type') not in ('weapon','helmet','chest','amulet','pet','artifact'):
        return None,'Bu eşya üzerinde orb işlemi yapılamaz.'
    if item.get('is_corrupted'):return None,'Mühürlü eşya değiştirilemez.'
    if orb_id not in CONFIG_ORBS:return None,'Bu orb yönlendirmeli işlem için uygun değil.'
    if side not in SIDES:return None,'Ön ek veya son ek tarafını seç.'
    if family is not None and family not in FAMILIES:return None,'Geçerli bir özellik ailesi seç.'
    limit=LIMITS.get(item.get('rarity'),0)
    if not limit:return None,'Önce Tier Orbu veya tarif ile eşyanın nadirliğini yükselt.'
    if orb_id in FOCUS_ORBS:
        required={'p_add':'prefixes','s_add':'suffixes'}.get(orb_id)
        if required and side!=required:return None,'Bu orb yalnız kendi özellik tarafında çalışır.'
        if len(item.get(side,[]))>=limit:return None,'Seçilen özellik tarafında boş yuva yok.'
        pool=candidates(item,side,family)
        if not pool:return None,'Bu aileden eklenebilecek uygun özellik kalmadı.'
        return dict(kind='add',pool=pool,side=side,essence=family),None
    if orb_id=='transmute':
        if family is None:return None,'Dönüşüm için hedef özellik ailesini seç.'
        target=next((a for a in item.get(side,[]) if a['stat']==target_stat),None)
        if target is None:return None,'Eşyanın üstünden değişecek özelliği seç.'
        if target.get('crafted') or target.get('fractured') or target.get('tier',0)<=0:
            return None,'Sabit, tarif veya özel güç dönüştürülemez.'
        pool=candidates(item,side,family,target_stat)
        if not pool:return None,'Bu ailede farklı ve uygun bir özellik yok.'
        return dict(kind='replace',pool=pool,side=side,target=target_stat,essence=family),None
    if family is not None:return None,'Tek taraflı Kaos aile özü kullanmaz.'
    retained=[a for a in item.get(side,[]) if a.get('fractured') or a.get('crafted') or a.get('tier',0)<=0]
    mutable=[a for a in item.get(side,[]) if a not in retained]
    if not mutable:return None,'Seçilen tarafta yenilenebilecek doğal özellik yok.'
    temp=copy.deepcopy(item);temp[side]=retained
    pool=candidates(temp,side)
    if not pool:return None,'Yenileme için uygun doğal özellik havuzu yok.'
    count=min(len(mutable),len(pool),max(0,limit-len(retained)))
    if not count:return None,'Özellik sınırı yenilemeye izin vermiyor.'
    return dict(kind='reroll',pool=pool,side=side,retained=retained,count=count,essence=None),None


def validate(player,item,orb,side,family=None,target_stat=None):
    if not any(it is item for it in player.inventory) and not any(it is item for it in player.inv_manager.equipped.values()):
        return None,'Eşya artık sende değil.'
    if not any(it is orb for it in player.inventory) or orb.get('type')!='orb' or orb.get('stack',1)<=0:
        return None,'Bu orb artık çantanda yok.'
    proposal,error=plan(item,orb.get('orb_id'),side,family,target_stat)
    if error:return None,error
    essence=proposal['essence']
    if essence and getattr(player,'craft_essences',{}).get(essence,0)<1:
        return None,FAMILIES[essence][0]+' özü eksik. Doğal özellikli bir eşyayı sökebilirsin.'
    return proposal,None


def apply(player,item,orb,side,family=None,target_stat=None):
    proposal,error=validate(player,item,orb,side,family,target_stat)
    if error:return error
    from logic.item_system import ItemSystem
    system=ItemSystem()
    staged=copy.deepcopy(item)
    def rolled(definition):
        tier=system.roll_tier(staged['rarity'],staged)
        return dict(name=f"{definition['name']} (T{tier})",base_name=definition['name'],
                    stat=definition['stat'],val=roll_value(definition,tier),tier=tier,
                    label='P' if side=='prefixes' else 'S')
    if proposal['kind']=='add':staged.setdefault(side,[]).append(rolled(random.choice(proposal['pool'])))
    elif proposal['kind']=='replace':
        index=next(i for i,a in enumerate(staged[side]) if a['stat']==target_stat)
        staged[side][index]=rolled(random.choice(proposal['pool']))
    else:
        staged[side]=copy.deepcopy(proposal['retained'])+[rolled(a) for a in random.sample(proposal['pool'],proposal['count'])]
    system.update_item_name(staged)
    item.clear();item.update(staged)
    essence=proposal['essence']
    if essence:player.craft_essences[essence]-=1
    orb['stack']=orb.get('stack',1)-1
    if orb['stack']<=0:
        index=next(i for i,owned in enumerate(player.inventory) if owned is orb)
        del player.inventory[index]
    player.inv_manager.recalculate_stats()
    return None
