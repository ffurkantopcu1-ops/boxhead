"""Reproducible equal-budget builds; actual primary attacks and intake paths.
Stationary single target, no summons/active skills, no kill-stack buffs.
Wave/level/gear stages are scenarios, not claims about guaranteed drop progression.
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import sys, json, random, copy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
from entities.player import Player
from entities.enemy import Enemy
from logic.skill_tree import SkillTree
from logic.item_system import ItemSystem
from logic.card_system import CardSystem
from logic.ascendancy import Ascendancy

CLASSES = list(Player.STARTING_WEAPON_BASES) + ["beastmaster"]
STAGES = [(1, 1, 0, 4), (20, 20, 19, 2), (50, 50, 49, 1), (50, 50, 49, 1)]
CLASS_CARDS = {
    "warrior": ["rampage", "chaos_theory", "double_edge", "crit_overload"],
    "ninja": ["thousand_cuts", "chaos_theory", "crit_overload", "assassinate"],
    "sniper": ["deadeye", "headhunter", "crit_overload", "long_barrel"],
    "bloodwalker": ["chaos_theory", "double_edge", "crit_overload", "blood_fire"],
    "sorcerer": ["arcane_surge", "fire_soul", "void_touch", "crit_overload"],
    "alchemist": ["poison_master", "toxic_blood", "venomous_strike", "corrosion"],
    "bomber": ["cluster_bomb", "demolition", "napalm", "bomb_barrage"],
    "engineer": ["auto_targeting", "overclock", "factory_line", "reinforced_turrets"],
    "beastmaster": ["war_commander", "swarmlord", "alpha_bond", "spirit_link"],
}

def build(class_id, level, points, tier, route, stress=False):
    p = Player("p1", 1000, 1000, class_id)
    p.level = level
    p.skill_points = points
    prefix = "early1" if route == "defense" else ("early2" if route == "utility" else "main")
    preferred = [f"{class_id}_{prefix}_{i}" for i in range(1, 6)]
    preferred += [f"{class_id}_notable_core" if prefix=="main" else f"{class_id}_{prefix}_notable"]
    branches = (1, 2) if route == "defense" else (2, 1)
    for branch in branches:
        preferred += [f"{class_id}_path{branch}_{i}" for i in range(1, 6)]
        preferred += [f"{class_id}_keystone_{branch}"]
    for _ in range(points):
        choices = SkillTree.allocatable_nodes(p.allocated_nodes)
        choices = [x for x in choices if not SkillTree.is_start(x)]
        if not choices:
            break
        def score(nid):
            n = SkillTree.BY_ID[nid]
            stats = n.get("stats", {})
            weight = ({"armor": .04, "max_hp_pct": .2, "regen": 1, "dodgeChance": 50, "maxEnergyShield": .1}
                      if route == "defense" else
                      {"physDmgFlat": .2, "physDmgMult": 40, "critChance": 30, "attack_speed_bonus": 40, "lifesteal": 10})
            return (preferred.index(nid) if nid in preferred else 100,
                    -sum(stats.get(k, 0)*v for k, v in weight.items()), nid)
        SkillTree.allocate(p, min(choices, key=score))
    if tier < 4:
        for slot in ("weapon", "helmet", "chest"):
            candidates = [x for x in ItemSystem.bases if x["type"] == slot and x.get("tier") == tier]
            if slot == "weapon":
                candidates = [x for x in candidates if x.get("weaponClass") == class_id]
                if class_id == "engineer":
                    candidates = [x for x in candidates if x.get("isFlamethrower")]
            if candidates:
                item = copy.deepcopy(candidates[0])
                item.update(rarity="Normal", prefixes=[], suffixes=[])
                p.inv_manager.equipped[slot] = item
    if level >= 20:
        evos = [eid for eid, e in Player.EVOLUTIONS.items() if e["class_base"] == class_id]
        if evos:
            p.apply_evolution(evos[-1 if route == "defense" else 0])
    if stress:
        random.seed(871)
        system = ItemSystem()
        for slot in ("weapon", "helmet", "chest"):
            item = p.inv_manager.equipped.get(slot)
            if item:
                item["rarity"] = "Rare"
                system.apply_affixes(item)
        p.ascendancy_points = 5
        for _ in range(5):
            choices = sorted(n for n in Ascendancy.allocatable_nodes(p.ascendancy_nodes)
                             if Ascendancy.BY_ID[n]["subclass"] == p.evolution)
            if not choices:
                break
            Ascendancy.allocate(p, choices[0])
        p._benchmark_cards = CardSystem()
        for card in CLASS_CARDS[class_id]:
            assert p._benchmark_cards.apply_card(card,p), card
    p.inv_manager.recalculate_stats()
    p.hp = p.max_hp
    p.energy_shield = p.max_energy_shield
    p.facing_angle = 0
    p.aim_x, p.aim_y = 1070, 1000
    return p

def arena(p, wave):
    game = SimpleNamespace(players={"p1":p}, local_player_id="p1",
        wave={"current_diff":"Normal", "number":wave}, enemies=[], clouds=[],
        projectiles=[], minions=[], turrets=[], events=[], particles=[], entity_id_counter=0,
        kill_streak=0, grid=None, obstacles=[], drops=[],
        stats={"total_damage_taken":0.0, "total_damage_dealt":0.0},
        card_system=getattr(p,"_benchmark_cards",None) or CardSystem(), add_event=Mock(), kill_enemy=Mock(),
        record_damage_dealt=Mock(), track_quest=Mock(), trigger_shake=Mock())
    game.iter_enemies_near = lambda *args: list(game.enemies)
    p.game = game
    return game

def primary_dps(p, wave, seconds=20, target_count=1, fps=120):
    if (p.inv_manager.equipped.get("weapon") or {}).get("isMinion") or (p.inv_manager.equipped.get("weapon") or {}).get("isCommander"):
        return None, None  # Command/pets need a separate summon benchmark.
    random.seed(731)
    game = arena(p, wave)
    targets = [Enemy(i+1, 1070, 1000 + (i-target_count//2)*8 if target_count>1 else 1000, game, wave_level=wave) for i in range(target_count)]
    for enemy in targets:
        enemy.hp = enemy.max_hp = 1e9
    game.enemies = targets
    elapsed, next_shot = 0.0, 0.0
    p.hp = p.max_hp * .5
    leech_total = 0.0
    self_cost_total = 0.0
    original_intake = p.take_damage
    def intake(amount, **kwargs):
        nonlocal self_cost_total
        actual = original_intake(amount, **kwargs)
        if kwargs.get("is_self_damage"):
            self_cost_total += actual or 0.0
        return actual
    p.take_damage = intake
    p.energy_shield = 0  # Measure life cost without borrowing a finite shield.
    def wrap(original_damage):
        def damage(*args, **kwargs):
            nonlocal leech_total
            before = p.lifesteal_buffer
            original_damage(*args, **kwargs)
            leech_total += max(0, p.lifesteal_buffer-before)
            p.lifesteal_buffer = 0
        return damage
    for enemy in targets:
        enemy.take_damage = wrap(enemy.take_damage)
    while elapsed < seconds - 1e-9:
        dt = min(1/fps, seconds-elapsed)
        p.hp = p.max_hp * .5  # Sustained mid-life damage potential; report its life cost.
        if elapsed + 1e-9 >= next_shot:
            p.specialization.execute_attack(p, game)
            next_shot += p.stats["attack_cooldown"]/1000
        for projectile in game.projectiles[:]:
            projectile.update(dt, game)
        game.projectiles = [x for x in game.projectiles if not x.dead]
        for cloud in game.clouds[:]:
            cloud.update(dt, game)
        game.clouds = [x for x in game.clouds if not x.dead]
        for i, enemy in enumerate(targets):
            enemy.effect_manager.update(dt, enemy, game)
            enemy.x, enemy.y = 1070, 1000+(i-target_count//2)*8 if target_count>1 else 1000
        elapsed += dt
    dealt = sum(1e9 - enemy.hp for enemy in targets)
    p.take_damage = original_intake
    p._benchmark_self_cost_s = self_cost_total/seconds
    return dealt/seconds, leech_total/seconds

def survival(p, wave, leech_per_second, count=6, seconds=30, fps=60, self_cost_per_second=0):
    game = arena(p, wave)
    enemies = [Enemy(i,1000,1000,game,wave_level=wave) for i in range(count)]
    for enemy in enemies:
        enemy.hp = enemy.max_hp = 1e9
    game.enemies = enemies
    p.hp, p.energy_shield = p.max_hp, p.max_energy_shield
    p.lifesteal_buffer = 0
    elapsed = 0.0
    random.seed(922)
    while elapsed < seconds - 1e-9 and p.hp > 0:
        dt = min(1/fps, seconds-elapsed)
        for e in enemies:
            e.update_contact(dt,p)
        if p.hp > 0 and self_cost_per_second:
            p.take_damage(self_cost_per_second*dt,force=True,is_self_damage=True)
        if p.hp > 0:
            p.lifesteal_buffer += max(0.0, leech_per_second or 0)*dt
            p.update_recovery(dt,game)
        elapsed += dt
    return {"survival_s": round(elapsed,3), "alive":p.hp>0,
            "remaining_hp_pct":round(100*p.hp/p.max_hp,2)}

def measure():
    pygame.init()
    pygame.display.set_mode((64,64))
    rows = []
    for stage_index,(wave, level, points, tier) in enumerate(STAGES):
        stress = stage_index == 3
        for cls in CLASSES:
            for route in ("defense", "offense"):
                p = build(cls,level,points,tier,route,stress=stress)
                dps, leech = primary_dps(p,wave)
                pack_dps, _ = primary_dps(build(cls,level,points,tier,route,stress=stress),wave,target_count=6)
                hp = 200*(1.25**((wave-1)//10))*(1+.05*wave)
                row = {"class":cls, "route":route, "wave":wave,"stress":stress,
                    "cards":CLASS_CARDS[cls] if stress else [],
                    "points":points, "allocated_points":sum(SkillTree.get_cost(n) for n in p.allocated_nodes),
                    "tier":tier,"hp":round(p.max_hp,2),"es":round(p.max_energy_shield,2),
                    "armor":round(p.stats.get("armor",0),2), "dodge":round(p.stats.get("dodgeChance",0),3),
                    "movement_px_s":round(p.get_movement_speed()*60,2),
                    "primary_dps":round(dps,2) if dps is not None else None,
                    "six_target_total_dps":round(pack_dps,2) if pack_dps is not None else None,
                    "normal_kill_s":round(hp/dps,2) if dps else None,
                    "leech_generated_s":round(leech,2) if leech is not None else None,
                    "self_cost_s":round(getattr(p,"_benchmark_self_cost_s",0),2)}
                row["six_contacts_no_attacks"] = survival(p,wave,0)
                row["six_contacts_with_primary_leech"] = survival(p,wave,leech,self_cost_per_second=getattr(p,"_benchmark_self_cost_s",0))
                rows.append(row)
    return {"assumptions":{"difficulty":"Normal","seconds":20,
        "attack_target":"stationary normal enemy at 70px; actual hit/projectile/cloud/DoT paths",
        "investment":"equal SP, Normal gear/evolution; separate late stress stage adds seeded Rare affixes, four class cards, five ascendancy points; no summons/active skills",
        "survival":"six immortal stationary attackers up to30s; seed922; contact+regen; leech and self-damage costs fed at measured average rates (optimistic)",
        "limitations":"engineer flame weapon measured without turrets; beastmaster DPS not measured; no player positioning, kill drops, boss telegraphs; not a global balance guarantee"},
        "rows":rows}


def measure_weapon_swaps():
    """Same late investment, different legal weapon families; no companion DPS."""
    pygame.init()
    pygame.display.set_mode((64,64))
    families = {}
    for base in ItemSystem.bases:
        if base.get("type")!="weapon" or base.get("tier")!=1:
            continue
        if base.get("isTurret") or base.get("isMinion") or base.get("isCommander"):
            continue
        families.setdefault(base["name"],base)
    rows=[]
    for cls in CLASSES:
        for family,base in families.items():
            p=build(cls,50,49,1,"offense",stress=True)
            previous=p.inv_manager.equipped.get("weapon") or {}
            weapon=copy.deepcopy(base)
            weapon.update(rarity="Rare",prefixes=copy.deepcopy(previous.get("prefixes",[])),suffixes=copy.deepcopy(previous.get("suffixes",[])))
            p.inv_manager.equipped["weapon"]=weapon
            p.inv_manager.recalculate_stats()
            p.hp=p.max_hp
            p.energy_shield=p.max_energy_shield
            dps,leech=primary_dps(p,50)
            rows.append({"class":cls,"weapon_family":base.get("weaponClass","other"),"weapon":weapon["name"],
                         "primary_dps":round(dps,2) if dps is not None else None,
                         "leech_s":round(leech,2) if leech is not None else None,
                         "self_cost_s":round(getattr(p,"_benchmark_self_cost_s",0),2)})
    return {"assumptions":"level50,49SP,5ascendancy,4class cards,three Rare items; same weapon affixes per class; primary only, no minions/turrets/active skills", "rows":rows}


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    result=measure()
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Measured {len(result['rows'])} equal-budget scenarios.")
