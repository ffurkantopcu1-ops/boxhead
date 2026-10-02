"""Measure the new boss cadence and three early routes with real combat paths."""
import json,collections
from pathlib import Path
from unittest.mock import Mock
import pygame
from tools.measure_combat_balance import build,primary_dps,arena,measure,CLASSES
from entities.boss import AbyssalLord
from entities.projectile_pool import ProjectilePool
from logic.skill_tree import SkillTree

def measure_duel():
    pygame.init()
    pygame.display.set_mode((64,64))
    rows=[]
    for fps in (30,60,144):
        p=build("warrior",10,9,3,"offense")
        g=arena(p,10)
        g.projectile_pool=ProjectilePool(100)
        p.take_damage=Mock(return_value=0)
        p.x,p.y=2650,2500
        boss=AbyssalLord(999,2500,2500,g,10)
        boss.hp=boss.max_hp*.25
        recover=0
        peak=0
        for _ in range(fps*60):
            boss.update(1/fps,g)
            g.projectile_pool.update(1/fps,g)
            recover+=boss.state=="recover"
            peak=max(peak,len(g.projectile_pool.active_objects))
        rows.append({"fps":fps,"seconds":60,"phase":3,"attacks":boss.attacks_resolved,
                     "peak_projectiles":peak,"recovery_seconds":round(recover/fps,3)})
    early=[]
    paths=[]
    for cls in CLASSES:
        dist={"start_"+cls:0}
        q=collections.deque(dist)
        while q:
            n=q.popleft()
            for nb in SkillTree.ADJ[n]:
                if nb not in dist:
                    dist[nb]=dist[n]+1
                    q.append(nb)
        own=min(dist[n["id"]] for n in SkillTree.NODES if n["arm"]==cls and n["type"]=="keystone")
        foreign=min(dist[n["id"]] for n in SkillTree.NODES if n["arm"] not in (cls,"core") and n["type"]=="keystone")
        paths.append({"class":cls,"initial_choices":len(SkillTree.ADJ["start_"+cls]),
                      "own_keystone_steps":own,"nearest_foreign_keystone_steps":foreign})
        for route,prefix in (("offense","main"),("defense","early1"),("utility","early2")):
            p=build(cls,6,5,4,route)
            dps,_=primary_dps(p,1,seconds=10)
            early.append({"class":cls,"route":route,"points":5,"nodes":sorted(p.allocated_nodes),
                          "primary_dps":round(dps,2) if dps is not None else None,
                          "hp":p.max_hp,"armor":p.stats.get("armor",0),"es":p.max_energy_shield,
                          "speed":p.get_movement_speed(),"tree_stats":SkillTree.resolve_stats(p.allocated_nodes)})
    return {"version":"1.23.0","assumptions":"Boss 60s at 25% HP; damage reception mocked to preserve stationary probe. Early level6 5SP T4; primary attacks only, pets/turrets excluded.",
            "boss_cadence":rows,"path_costs":paths,"early_builds":early,
            "late_builds":measure()}

if __name__=="__main__":
    import sys
    result=measure_duel()
    Path(sys.argv[1]).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Measured 27 early builds, 72 late builds and boss cadence at three FPS.")
