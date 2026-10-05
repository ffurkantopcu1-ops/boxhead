"""Shared card combat rules, independent of weapon attack implementations."""
from collections import deque

def fire_only(player):
    return bool(getattr(player,'has_furnace',False) or player.stats.get('treeFireOnly',0))

def add_conversion_poison(enemy,amount,duration=4.0):
    from logic.status_effects import StatusEffect
    effects=enemy.effect_manager.effects
    if effects and effects[-1].name=='CardConversionPoison' and abs(effects[-1].timer-duration)<1e-9:
        effects[-1].dps+=amount/duration
    else:
        effects.append(StatusEffect('CardConversionPoison',duration,dps=amount/duration,color=(90,220,100)))

def death_blast(game,enemy,player):
    furnace=getattr(player,'has_furnace',False)
    echo=player.stats.get('cardDeathBlast',0)
    if (not furnace and not echo) or getattr(enemy,'is_trap',False):
        return
    queue=getattr(game,'_card_blast_queue',None)
    if queue is None:
        queue=game._card_blast_queue=deque()
    queue.append((enemy,player))
    if getattr(game,'_card_blast_processing',False):
        return
    game._card_blast_processing=True
    try:
        # Nested deaths queue their blasts instead of recursing. Each enemy is
        # rewarded once by kill_enemy's looted guard, so the chain is finite.
        while queue:
            source,owner=queue.popleft()
            scale=(1.0 if getattr(owner,'has_furnace',False) else 0.0)+.35*owner.stats.get('cardDeathBlast',0)
            radius=min(240,120*max(.1,owner.stats.get('aoe',1)))
            damage=min(source.max_hp*.35,owner.get_death_explosion_damage(source.max_hp)*scale*owner.get_elemental_mults()[0])
            game.add_event('explosion',source.x,source.y,radius=int(radius),color=(255,125,35),timer=.4)
            for target in list(game.iter_enemies_near(source.x,source.y,radius)):
                if target is source or target.dead or getattr(target,'is_trap',False):
                    continue
                if (target.x-source.x)**2+(target.y-source.y)**2<=radius*radius:
                    target.take_damage(damage,game,from_player=True,is_secondary=True,damage_type='fire')
    finally:
        game._card_blast_processing=False
