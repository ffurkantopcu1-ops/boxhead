import math
import pygame
import vfx
import audio

class Engineer:
    """Active field engineer: pulse kit, aimed sentries and focus commands."""
    # --- ALEV SİLAHI (Flamethrower) ---
    # Diğer arketiplerden farkı: mermi üretmez, her saldırıda ÖNÜNDEKİ KONİYİ
    # tarar. Atış aralığı çok kısa olduğu için sürekli bir akış hissi verir;
    # tek vuruş hasarı düşük, asıl hasar yanma (burn) yığılmasından gelir.
    FLAME_ARC = 0.62            # ~35 derece koni
    FLAME_BASE_RANGE = 210      # taban menzil (silah 'range' ile artırır)

    def execute_flamethrower(self, player, game, weapon):
        angle = player.facing_angle
        local = player.inv_manager.get_item_local_stats("weapon") or {}

        rng = (self.FLAME_BASE_RANGE + local.get("range", 0)) * \
              player.stats.get("meleeRangeMult", 1.0)
        arc = self.FLAME_ARC

        fire_mult, _frost_mult, elem_mult = player.get_elemental_mults()
        dmg_mult = player.stats.get("dmgMult", 1.0) * player.get_conditional_dmg_mult()
        # Alev hasarı ateş statlarından okunur; fiziksel taban yok.
        base_fire = player.get_elemental_base("fireDamage", "fireDmgFlat")
        tick_dmg = base_fire * dmg_mult * fire_mult
        burn_dps = tick_dmg * 0.9 * (1.0 + player.stats.get('dotDmgMult',0))
        import random
        is_crit = random.random() < player.stats.get('critChance',0.05)
        if is_crit:
            tick_dmg *= player.get_critical_multiplier()

        audio.play('flame')
        vfx.flamethrower(game, player.x, player.y, angle, rng, arc)

        hit_any = False
        for e in game.iter_enemies_near(player.x, player.y, rng + 80):
            if e.dead or getattr(e, 'is_trap', False):
                continue
            dx, dy = e.x - player.x, e.y - player.y
            hit_range = rng + e.radius
            if dx * dx + dy * dy > hit_range * hit_range:
                continue
            angle_to_e = math.atan2(dy, dx)
            diff = abs(((angle_to_e - angle) + math.pi) % (2 * math.pi) - math.pi)
            # Yakında koni genişler: dipte dar olması silahı kullanılmaz yapıyor
            dist = math.hypot(dx, dy)
            eff_arc = arc + (0.9 if dist < 70 else 0.0)
            if diff > eff_arc / 2:
                continue
            if tick_dmg > 0:
                e.take_damage(tick_dmg, game, is_crit=is_crit, from_player=True)
            # Yanma yığılır: alevin içinde kalmak cezalandırır
            e.apply_dot('fire', burn_dps, 2.0)
            hit_any = True

        return hit_any

    def execute_pulse(self,player,game,weapon):
        import random
        from entities.projectile import Projectile
        mult=player.stats.get("dmgMult",1)*player.get_conditional_dmg_mult()
        damage=(max(0,player.stats.get("physDmg",10))+player.stats.get("physDmgFlat",0)*player.get_added_damage_effectiveness())
        damage+=max(0,player.level-1)*.45
        damage*=mult*(1+player.stats.get("physDmgMult",0))
        crit=random.random()<player.stats.get("critChance",.05)
        if crit: damage*=player.get_critical_multiplier()
        count=max(1,min(4,int(player.stats.get("projectileCount",1))))
        budget=1/(1+.25*(count-1))
        fire,frost,_=player.get_elemental_mults()
        for i in range(count):
            a=player.facing_angle+(i-(count-1)/2)*.12
            shot=Projectile(game.entity_id_counter,player.x,player.y,math.cos(a)*11,math.sin(a)*11,
                            damage*budget,pierce=min(4,max(0,int(player.stats.get("pierce",0)))),
                            bounce=min(2,max(0,int(player.stats.get("bounce",0)))),is_crit=crit,lifetime=90)
            shot.color=(130,215,200)
            shot.fire_dmg=player.get_elemental_base("fireDamage","fireDmgFlat")*mult*fire*budget
            shot.frost_dmg=player.get_elemental_base("frostDamage","frostDmgFlat")*mult*frost*budget
            shot.poison_dps=player.stats.get("poisonDps",0)*mult*budget
            shot.dot_mult=1+player.stats.get("dotDmgMult",0)
            game.projectiles.append(shot)
            game.entity_id_counter+=1
        audio.play("shoot")

    def execute_attack(self,player,game):
        weapon=player.inv_manager.equipped.get("weapon")
        if player.execute_weapon_override(game,weapon): return
        if weapon and (weapon.get("isRanged") or weapon.get("isBomb")):
            player.shoot(game)
        elif weapon and weapon.get("isMelee"):
            player.execute_fallback_melee(game,weapon)
        else:
            player.shoot(game)

    def update(self, dt, player, game):
        pass
        
    def draw_visuals(self, screen, camera_x, camera_y):
        pass
        
