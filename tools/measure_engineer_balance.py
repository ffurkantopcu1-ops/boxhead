"""Real engineer fleet + primary DPS, including deployment and battery uptime."""
import copy,json,random,sys
from pathlib import Path
import pygame
from tools.measure_combat_balance import build,arena,primary_dps,STAGES
from entities.enemy import Enemy
from logic.item_system import ItemSystem

POSITIONS=[(-150,-100),(-150,100),(-50,-150),(-50,150),(-200,0)]
def fleet_measure(wave,level,points,tier,route,weapon_family="kit",stress=False,commands=True,target_count=1,fps=120,seconds=30):
    random.seed(844)
    p=build("engineer",level,points,tier,route,stress=stress)
    bases=[b for b in ItemSystem.bases if b.get("weaponClass")=="engineer" and b.get("tier")==tier
           and b.get("isTurret" if weapon_family=="kit" else "isFlamethrower")]
    item=copy.deepcopy(bases[0])
    item.update(rarity="Rare" if stress else "Normal",prefixes=[],suffixes=[])
    if stress:
        random.seed(871)
        ItemSystem().apply_affixes(item)
    p.inv_manager.equipped["weapon"]=item
    p.inv_manager.recalculate_stats()
    g=arena(p,wave)
    targets=[Enemy(i+1,1170,1000+(i-target_count//2)*12,g,wave_level=wave) for i in range(target_count)]
    for e in targets: e.hp=e.max_hp=1e9
    g.enemies=targets
    p.aim_x,p.aim_y=1170,1000
    peak=0
    deployed=0
    p.hp=p.max_hp
    for _ in range(round(seconds*fps)):
        dt=1/fps
        p.update_turret_charges(dt)
        p.update_turret_command(dt)
        cap=int(p.stats.get("turretLimit",2))
        if p.turret_charges>=1 and len(g.turrets)<cap:
            for dx,dy in POSITIONS:
                if all((t.x-(p.x+dx))**2+(t.y-(p.y+dy))**2>=55**2 for t in g.turrets):
                    p.aim_x,p.aim_y=p.x+dx,p.y+dy
                    if p.try_place_turret(g): deployed+=1
                    break
            p.aim_x,p.aim_y=1170,1000
        if commands and p.turret_command_cooldown<=0:
            p.try_command_turrets(g)
        p.update_attack(dt,g,True)
        for t in g.turrets[:]: t.update(dt,g)
        for shot in g.projectiles[:]: shot.update(dt,g)
        g.projectiles=[s for s in g.projectiles if not s.dead]
        g.turrets=[t for t in g.turrets if not t.dead]
        for e in targets:
            e.effect_manager.update(dt,e,g)
            e.x,e.y=1170,1000+(targets.index(e)-target_count//2)*12
        peak=max(peak,len(g.turrets))
    return {"wave":wave,"level":level,"points":points,"tier":tier,"route":route,"weapon":weapon_family,
            "stress":stress,"evolution":p.evolution,"commands":commands,"target_count":target_count,"fps":fps,
            "total_dps":round(sum(1e9-e.hp for e in targets)/seconds,2),
            "peak_turrets":peak,"deployed":deployed,"hp":p.max_hp,
            "turret_dmg":p.stats["turretDmg"],"turret_rate":p.stats["turretRate"],
            "turret_limit":p.stats["turretLimit"],"charge_cd":p.get_turret_cooldown()}

def measure():
    pygame.init()
    pygame.display.set_mode((64,64))
    rows=[]
    baselines=[]
    for i,(wave,level,points,tier) in enumerate(STAGES):
        stress=i==3
        for route in ("offense","defense","utility"):
            for family in ("kit","flame"):
                rows.append(fleet_measure(wave,level,points,tier,route,family,stress,commands=True))
        for cls in ("warrior","sniper"):
            p=build(cls,level,points,tier,"offense",stress=stress)
            dps,_=primary_dps(p,wave,seconds=30)
            baselines.append({"class":cls,"wave":wave,"stress":stress,"primary_dps":round(dps,2)})
    packs=[fleet_measure(50,50,49,1,route,stress=True,target_count=6) for route in ("offense","defense","utility")]
    fps_rows=[fleet_measure(1,1,0,4,"offense",fps=fps) for fps in (30,60,144)]
    no_commands=fleet_measure(50,50,49,1,"offense",stress=True,commands=False)
    return {"version":"1.24.0","assumptions":"30s stationary target(s), Normal, real deployment/charges/24s battery/0.5s boot/primary/projectile/DoT paths. Fleet deployed behind player within220px; no incoming damage, kill drops or artifact skills. Early wave1 includes low-investment pilot + sentry damage. Late same SP/tier/cards/ascendancy scenarios, not optimal builds or global balance proof.",
            "rows":rows,"six_target_builds":packs,"fps":fps_rows,"without_command":no_commands,"baselines":baselines}

if __name__=="__main__":
    Path(sys.argv[1]).write_text(json.dumps(measure(),ensure_ascii=False,indent=2),encoding="utf-8")
    print("Measured 24 complete engineer builds, fleet uptime, crowd damage and FPS.")
