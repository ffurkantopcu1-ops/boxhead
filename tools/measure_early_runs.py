"""Seeded input-driven runs, not a substitute for a human playtest.

Real simulation, drops, XP and damage; zero meta in a temporary save directory.
Simple nearest-target aiming, eight-direction movement and reactive dash.
No shop purchases; equips collected same-class weapons and defensive gear.
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import sys, json, math, random, tempfile, contextlib, io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from collections import defaultdict
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
from logic.game_logic import GameLogic
from logic.save_manager import SaveManager
from logic.skill_tree import SkillTree
from tools.measure_combat_balance import CLASSES
from tools.tree_clusters import CLUSTERS
from tools.inspect_new_tree import path_to

def run(class_id, seed, difficulty="Normal", seconds=480, fps=30, policy="clear"):
    random.seed(seed)
    clock = [1000.0]
    keys = defaultdict(bool)
    aim = [2500, 2500]
    scene = SimpleNamespace(zoom_level=1, camera_x=0, camera_y=0, _pending_keys=[])
    with tempfile.TemporaryDirectory(prefix="boxhead-run-") as tmp, \
         patch.object(SaveManager, "SAVE_DIR", tmp), \
         patch("pygame.key.get_pressed", return_value=keys), \
         patch("pygame.mouse.get_pressed", return_value=(True, False, False)), \
         patch("pygame.mouse.get_pos", side_effect=lambda: tuple(aim)), \
         patch("pygame.time.get_ticks", side_effect=lambda: int(clock[0]*1000)), \
         patch("time.time", side_effect=lambda: clock[0]):
        g = GameLogic(SimpleNamespace(current_scene=scene), 1280, 720, class_id)
        g.wave["current_diff"] = difficulty
        p = g.players["p1"]
        damage = defaultdict(float)
        original = p.take_damage
        death_hint = [None]
        progression = []
        def take(amount, *args, **kwargs):
            source = 'self_damage' if kwargs.get('is_self_damage') else 'reflected' if kwargs.get('is_reflected') else 'dot' if kwargs.get('is_dot') else getattr(p, 'last_damage_source', 'unknown')
            attacker = getattr(p, 'last_attacker_type', 'unknown')
            dealt = original(amount, *args, **kwargs)
            damage[source] += dealt or 0
            if p.hp<=0: death_hint[0]={'source':source,'attacker':attacker}
            p.last_damage_source='unknown' 
            return dealt
        p.take_damage = take
        rows = []
        last_wave = 0
        wave_start = 0
        peak = 0
        for frame in range(seconds*fps):
            elapsed = frame/fps
            clock[0] = 1000+elapsed
            if g.wave["level"] != last_wave:
                if last_wave:
                    rows[-1].update(seconds=round(elapsed-wave_start, 2), hp_end=round(p.hp, 1), level_end=p.level, available_sp=p.skill_points, spent_sp=len(p.allocated_nodes)-1,
                                    peak_enemies=peak, damage_by_source=dict(damage), cleared=True)
                last_wave = g.wave["level"]
                if last_wave > 5: break
                if last_wave:
                    rows.append(dict(wave=last_wave, hp_start=round(p.hp,1), level=p.level,
                                     count=g.wave["total_to_spawn"], event=g.wave.get("event")))
                wave_start, peak = elapsed, 0
                damage.clear()
            if g.state == "GAMEOVER": break
            if g.state == "CARD_SELECT":
                card = g.pending_cards[0]
                g.card_system.apply_card(card["id"], p)
                g.state = "PLAYING"
            if g.state == "EVOLUTION_SELECT":
                evo = next(k for k,v in p.EVOLUTIONS.items() if v["class_base"]==class_id)
                p.apply_evolution(evo)
                g.state = "PLAYING"
            if frame % fps == 0:
                priorities=[2,0,1,3,4,5,6,7] if policy=='defense' else [0,1,3,2,4,5,6,7]
                while p.skill_points > 0:
                    choices = [n for n in SkillTree.allocatable_nodes(p.allocated_nodes)
                               if n.startswith(class_id+"_") and not SkillTree.is_start(n)]
                    if not choices: break
                    preferred=[]
                    for k in priorities:
                        target=f'{class_id}_{CLUSTERS[class_id][k][0]}_notable'
                        if target not in p.allocated_nodes:
                            preferred=path_to('start_'+class_id,target)
                            break
                    ranked=sorted(choices,key=lambda n:(preferred.index(n) if n in preferred else 1000,n))
                    ok,msg=SkillTree.allocate(p,ranked[0])
                    if not ok: break
                    progression.append({'seconds':round(elapsed,2),'wave':g.wave['level'],
                        'level':p.level,'spent_sp':len(p.allocated_nodes)-1,'node':ranked[0]})
                for item in p.inventory[:]:
                    slot = item.get("type")
                    if slot not in ("weapon", "helmet", "chest", "amulet"): continue
                    base = item.get("itemBase", {})
                    if slot=="weapon" and base.get("weaponClass") != class_id: continue
                    old = p.inv_manager.equipped.get(slot)
                    if old is None or item.get("price",0) > old.get("price",0)*1.15:
                        p.inventory.remove(item)
                        p.inv_manager.equip(item)
            enemies = [e for e in g.enemies if not e.dead and not e.is_trap]
            peak = max(peak, len(enemies))
            target = min(enemies, key=lambda e: (e.x-p.x)**2+(e.y-p.y)**2, default=None)
            keys.clear()
            if target:
                aim[:] = [target.x, target.y]
                dx, dy = target.x-p.x, target.y-p.y
                dist = max(1, math.hypot(dx, dy))
                melee = class_id in ("warrior", "ninja", "bloodwalker", "beastmaster")
                reach=(100+p.stats.get('meleeRangeFlat',0))*p.stats.get('meleeRangeMult',1)
                preferred = max(65,reach*.75) if melee else 260
                if class_id=='bomber':
                    preferred=160
                    travel=.45
                    velocity=target.speed*60
                    aim[:]=[target.x-dx/dist*velocity*travel,target.y-dy/dist*velocity*travel]
                # Avoid overlapping packs, not just the nearest target.
                pressure_x=pressure_y=0
                for foe in enemies:
                    ddx,ddy=p.x-foe.x,p.y-foe.y
                    distance=math.hypot(ddx,ddy)
                    if 1<distance<120:
                        pressure_x+=ddx/distance*(120-distance)/100
                        pressure_y+=ddy/distance*(120-distance)/100
                # Approach to weapon range, retreat when crowded, circle otherwise.
                vx, vy = dx/dist, dy/dist
                if dist < preferred:
                    vx, vy = -vx, -vy
                elif dist < preferred+60:
                    vx, vy = -vy, vx
                vx+=pressure_x*.6; vy+=pressure_y*.6
                # Steer away from arena edges.
                vx += (1 if p.x<400 else -1 if p.x>4600 else 0)*2
                vy += (1 if p.y<400 else -1 if p.y>4600 else 0)*2
                keys[pygame.K_d] = vx > .3
                keys[pygame.K_a] = vx < -.3
                keys[pygame.K_s] = vy > .3
                keys[pygame.K_w] = vy < -.3
                if dist < 65 and p.dash_timer <= 0: p.dash()
                if class_id == "engineer":
                    p.aim_x, p.aim_y = p.x-80, p.y
                    p.try_place_turret(g)
                    p.aim_x, p.aim_y = target.x, target.y
                    p.try_command_turrets(g)
                if class_id == "bloodwalker":
                    p.specialization.activate_blood_absorb(p)
            elif g.items_on_ground:
                item = min(g.items_on_ground,key=lambda e:(e.x-p.x)**2+(e.y-p.y)**2)
                keys[pygame.K_d], keys[pygame.K_a] = item.x>p.x+10, item.x<p.x-10
                keys[pygame.K_s], keys[pygame.K_w] = item.y>p.y+10, item.y<p.y-10
            g.update(1/fps)
        if rows and not rows[-1].get("cleared"):
            rows[-1].update(seconds=round(elapsed-wave_start,2), hp_end=round(p.hp,1), level_end=p.level, available_sp=p.skill_points, spent_sp=len(p.allocated_nodes)-1,
                            peak_enemies=peak, damage_by_source=dict(damage), cleared=False)
        return dict(class_id=class_id, seed=seed, difficulty=difficulty, meta="none", fps=fps,
                    outcome="cleared_5" if last_wave>5 else "death" if g.state=="GAMEOVER" or p.hp<=0 else "timeout",
                    level=p.level, waves=rows, policy=policy, progression=progression,
                    death_cause=death_hint[0], equipment={k:v.get('name') for k,v in p.inv_manager.equipped.items() if v})

if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((64,64))
    rows=[]
    classes=sys.argv[2].split(",") if len(sys.argv)>2 else CLASSES
    seeds=[int(n) for n in sys.argv[3].split(',')] if len(sys.argv)>3 else [41,73,107]
    policies=sys.argv[4].split(',') if len(sys.argv)>4 else ['clear','defense']
    for cls in classes:
        for policy in policies:
            for seed in seeds:
                with contextlib.redirect_stdout(io.StringIO()):
                    result=run(cls,seed,policy=policy)
                rows.append(result)
                print(cls,policy,seed,result['outcome'],result['level'],flush=True)
                Path(sys.argv[1]).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
