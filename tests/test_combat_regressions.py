"""Combat regressions using the actual attack and damage paths."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import pygame
import pytest
from entities.player import Player
from entities.enemy import Enemy
from logic.skill_tree import SkillTree

@pytest.fixture
def combat():
    pygame.init()
    pygame.display.set_mode((64, 64))
    def create(class_id="warrior"):
        player = Player("p1", 0, 0, class_id)
        game = SimpleNamespace(
            players={"p1": player}, local_player_id="p1",
            wave={"current_diff": "Normal"}, kill_streak=0, enemies=[],
            clouds=[], projectiles=[], entity_id_counter=0,
            add_event=Mock(), kill_enemy=Mock(), track_quest=Mock(),
            record_damage_dealt=Mock(), trigger_shake=Mock(), events=[],
            stats={"total_damage_taken": 0, "total_damage_dealt": 0})
        game.iter_enemies_near = lambda *args: list(game.enemies)
        enemy = Enemy(1, 70, 0, game)
        enemy.hp = enemy.max_hp = 1000000
        enemy.armor = 0
        player.game = game
        player.hp = player.max_hp = 1000
        player.energy_shield = 0
        player.facing_angle = 0
        player.stats.update(critChance=0, dodgeChance=0, armor=0, lifesteal=0,
                            fireDamage=0, fireDmgFlat=0, frostDamage=0,
                            frostDmgFlat=0, poisonDps=0)
        game.enemies.append(enemy)
        return player, enemy, game
    return create

@pytest.mark.parametrize("class_id", ["warrior", "ninja", "bloodwalker"])
def test_physical_bonus_changes_melee_hit_but_not_poison(combat, class_id):
    player, enemy, game = combat(class_id)
    player.stats.update(physDmgMult=0, poisonDps=10, elementDmgMult=0, dotDmgMult=0)
    enemy.apply_dot = Mock()
    before = enemy.hp
    player.specialization.execute_attack(player, game)
    damage = before - enemy.hp
    poison = next(c.args[1] for c in enemy.apply_dot.call_args_list if c.args[0] == "poison")
    enemy.apply_dot.reset_mock()
    player.stats["physDmgMult"] = .5
    before = enemy.hp
    player.specialization.execute_attack(player, game)
    assert before - enemy.hp == pytest.approx(damage * 1.5)
    new_poison = next(c.args[1] for c in enemy.apply_dot.call_args_list if c.args[0] == "poison")
    assert new_poison == pytest.approx(poison)

@pytest.mark.parametrize("class_id", ["warrior", "ninja", "bloodwalker"])
def test_dot_bonus_changes_poison_and_burn_but_not_hit(combat, class_id):
    player, enemy, game = combat(class_id)
    player.stats.update(poisonDps=10, fireDamage=10, dotDmgMult=0)
    enemy.apply_dot = Mock()
    before = enemy.hp
    player.specialization.execute_attack(player, game)
    damage = before - enemy.hp
    dots = {c.args[0]: c.args[1] for c in enemy.apply_dot.call_args_list}
    enemy.apply_dot.reset_mock()
    player.stats["dotDmgMult"] = .5
    before = enemy.hp
    player.specialization.execute_attack(player, game)
    assert before - enemy.hp == pytest.approx(damage)
    for call in enemy.apply_dot.call_args_list:
        assert call.args[1] == pytest.approx(dots[call.args[0]] * 1.5)

@pytest.mark.parametrize("boss_type", ["boss", "crystal_dragon", "arachne"])
def test_boss_bonus_applies_to_every_boss(combat, boss_type):
    player, enemy, game = combat()
    enemy.type = boss_type
    player.stats["bossDmgMult"] = .5
    before = enemy.hp
    enemy.take_damage(20, game, from_player=True)
    assert before - enemy.hp == pytest.approx(30)

def test_boss_bonus_does_not_change_environmental_damage(combat):
    player, enemy, game = combat()
    enemy.type = "crystal_dragon"
    player.stats["bossDmgMult"] = 10
    before = enemy.hp
    enemy.take_damage(20, game)
    assert before - enemy.hp == pytest.approx(20)

def test_reflection_does_not_bounce_back_or_create_leech(combat):
    player, enemy, game = combat()
    player.stats.update(reflectionAura=.5, thorns=3, lifesteal=.5)
    player.hp = 900
    enemy.thorns = .5
    before = enemy.hp
    player.take_damage(10, force=True)
    assert player.hp == pytest.approx(890)
    assert before - enemy.hp == pytest.approx(8)
    assert player.lifesteal_buffer == 0

def test_enemy_thorns_does_not_retrigger_player_thorns(combat):
    player, enemy, game = combat()
    player.stats.update(reflectionAura=.5, thorns=3)
    enemy.thorns = .5
    before = enemy.hp
    enemy.take_damage(20, game, from_player=True)
    assert before - enemy.hp == pytest.approx(20)
    assert player.hp == pytest.approx(990)

@pytest.mark.parametrize("kind", ["environment", "dot", "reflection", "shield", "trap"])
def test_non_leechable_damage_cannot_create_lifesteal(combat, kind):
    player, enemy, game = combat("bloodwalker")
    player.hp = 500
    player.stats["lifesteal"] = .2
    kwargs = {"from_player": True}
    if kind == "environment":
        kwargs["from_player"] = False
    elif kind == "dot":
        kwargs["is_dot"] = True
    elif kind == "reflection":
        kwargs["is_reflected"] = True
    elif kind == "shield":
        enemy.elite_shield = 100
    elif kind == "trap":
        enemy.is_trap = True
    enemy.take_damage(20, game, **kwargs)
    assert player.lifesteal_buffer == 0
    assert player.hp == 500

def test_lifesteal_uses_mitigated_hit(combat):
    player, enemy, game = combat()
    player.hp = 500
    player.stats["lifesteal"] = .2
    enemy.armor = 100
    enemy.take_damage(100, game, from_player=True)
    assert player.lifesteal_buffer == pytest.approx(10)
    assert player.hp == 500

def test_bloodwalker_does_not_heal_from_blocked_melee_hit(combat):
    player, enemy, game = combat("bloodwalker")
    player.hp = 500
    player.stats["lifesteal"] = .2
    enemy.elite_shield = 100000
    player.specialization.execute_attack(player, game)
    assert player.hp == 500
    assert player.lifesteal_buffer == 0

def test_exact_shield_depletion_triggers_break_cooldown(combat):
    player, enemy, game = combat()
    player.energy_shield = 10
    player.passive_shield_cd = 5
    player.take_damage(10, force=True)
    assert player.energy_shield == 0
    assert player.hp == 1000
    assert player._shield_timer == 5

def test_zero_and_negative_damage_have_no_effect(combat):
    player, enemy, game = combat()
    player.energy_shield = 10
    player.take_damage(-10)
    player.take_damage(0)
    assert player.energy_shield == 10
    assert player.hp == 1000
    assert player.i_frame_timer == 0

def test_new_bridges_never_touch_starts():
    for class_id in ("warrior", "sniper", "engineer", "beastmaster", "bomber",
                     "alchemist", "sorcerer", "bloodwalker", "ninja"):
        start = "start_" + class_id
        assert all(SkillTree.BY_ID[n]["arm"] == class_id for n in SkillTree.ADJ[start])

def test_all_classes_connected_without_traversing_foreign_starts():
    for cls, start in SkillTree.START_BY_CLASS.items():
        if cls == "core":
            continue
        seen = {start}
        pending = [start]
        while pending:
            for neighbor in SkillTree.ADJ[pending.pop()]:
                if neighbor not in seen and not SkillTree.is_start(neighbor):
                    seen.add(neighbor)
                    pending.append(neighbor)
        assert all(n["id"] in seen for n in SkillTree.NODES if n["type"] == "keystone")

def test_generator_reproduces_checked_in_data():
    root = Path(__file__).resolve().parents[1]
    path = root / "data" / "skill_tree.json"
    before = path.read_bytes()
    subprocess.run([sys.executable, str(root / "tools" / "generate_skill_tree.py")], check=True)
    assert path.read_bytes() == before

@pytest.mark.parametrize("class_id,expected", [("warrior", 100), ("bloodwalker", 200)])
@pytest.mark.parametrize("fps", [30, 60, 144])
def test_leech_recovery_scales_with_max_life_and_not_fps(combat, class_id, expected, fps):
    player, enemy, game = combat(class_id)
    player.hp = 500
    player.lifesteal_buffer = 200
    for _ in range(fps):
        player.update_lifesteal(1 / fps)
    assert player.hp == pytest.approx(500 + expected)

def test_multiple_hits_feed_the_same_capped_pool(combat):
    player, enemy, game = combat()
    player.hp = 500
    player.stats["lifesteal"] = .2
    enemy.take_damage(10, game, from_player=True)
    enemy.take_damage(10, game, from_player=True)
    assert player.lifesteal_buffer == pytest.approx(4)
    enemy.take_damage(100000, game, from_player=True)
    assert player.lifesteal_buffer == 200

def test_full_life_discards_leech_pool(combat):
    player, enemy, game = combat()
    player.lifesteal_buffer = 200
    player.update_lifesteal(1)
    assert player.hp == 1000
    assert player.lifesteal_buffer == 0

def test_dead_player_cannot_recover_from_leech(combat):
    player, enemy, game = combat()
    player.hp = 0
    player.lifesteal_buffer = 200
    player.update_lifesteal(1)
    assert player.hp == 0
    assert player.lifesteal_buffer == 0

def test_void_staff_projectile_draw_does_not_crash():
    from entities.projectile import Projectile
    surface = pygame.Surface((64, 64))
    projectile = Projectile(1, 32, 32, 1, 0, 10, p_type="black_hole")
    projectile.draw(surface, 0, 0)

def test_all_generated_stats_have_player_facing_labels():
    import runpy
    root = Path(__file__).resolve().parents[1]
    generator = runpy.run_path(str(root / "tools" / "generate_skill_tree.py"))
    used = {key for node in generator["generate"]() for key in node["stats"]}
    assert used <= set(generator["STAT_LABEL"])


@pytest.mark.parametrize("fps", [30, 60, 144])
def test_contact_has_discrete_frame_independent_damage_and_thorns(combat, fps):
    p,e,g = combat()
    p.stats["thorns"] = 3
    before = e.hp
    for _ in range(fps*10):
        e.update_contact(1/fps,p)
    assert p.hp == pytest.approx(1000-20*e.dmg)
    assert before-e.hp == pytest.approx(60)
    assert g.stats["total_damage_taken"] == pytest.approx(20*e.dmg)

def test_contact_leaving_does_not_reset_cooldown(combat):
    p,e,g = combat()
    e.update_contact(.5,p)
    e.update_contact(.1,p,False)
    e.update_contact(.1,p)
    assert p.hp == pytest.approx(1000-e.dmg)
    e.update_contact(.3,p)
    assert p.hp == pytest.approx(1000-2*e.dmg)

@pytest.mark.parametrize("fps", [30,60,144])
def test_fire_hazard_exact_duration_bypasses_hit_defenses(combat,fps):
    from logic.hazards import Hazard
    p,e,g = combat()
    p.stats.update(armor=10000,dodgeChance=1,thorns=30)
    p.i_frame_timer = 5
    p.dash_active_timer = 5
    hazard = Hazard(0,0,"fire",duration=2)
    before=e.hp
    for _ in range(fps*3):
        hazard.update(1/fps,[p],[],g)
    assert p.hp == pytest.approx(990)
    assert not hazard.active
    assert e.hp == before
    assert p.i_frame_timer == 5

def test_dot_uses_shield_and_actual_damage_accounting(combat):
    p,e,g=combat()
    p.hp=3
    p.energy_shield=5
    assert p.take_damage(20,is_dot=True)==8
    assert p.hp==0
    assert p.energy_shield==0
    assert g.stats["total_damage_taken"]==8

@pytest.mark.parametrize("armor,expected", [(10000,2.5),(-10000,40)])
def test_armor_has_damage_envelope_even_for_temporary_stats(combat,armor,expected):
    p,e,g=combat()
    p.stats["armor"]=armor
    p.take_damage(10,force=True)
    assert 1000-p.hp==pytest.approx(expected)

def test_status_effect_applies_final_partial_tick_and_shield(combat):
    from logic.status_effects import StatusEffect
    p,e,g=combat()
    p.energy_shield=2
    effect=StatusEffect("Poison",duration=.15,dps=20)
    effect.update(.1,p,g)
    effect.update(.1,p,g)
    assert not effect.active
    assert p.energy_shield==0
    assert p.hp==pytest.approx(999)

@pytest.mark.parametrize("fps",[30,60,144])
def test_lightning_keeps_tick_remainder_without_player_ownership(combat,fps):
    from logic.hazards import Hazard
    p,e,g=combat()
    p.stats.update(lifesteal=.5,bossDmgMult=10)
    e.x=e.y=0
    e.type="boss"
    hazard=Hazard(0,0,"lightning",duration=2.2)
    before=e.hp
    for _ in range(fps*3):
        hazard.update(1/fps,[p],[e],g)
    assert before-e.hp==pytest.approx(40)
    assert p.hp==pytest.approx(960)
    assert p.lifesteal_buffer==0
    assert hazard.tick_timer==pytest.approx(.2)

def test_weak_poison_reapplication_does_not_reduce_existing_stack(combat):
    from logic.status_effects import StatusEffectManager,StatusEffect
    manager=StatusEffectManager()
    manager.add_effect(StatusEffect("Poison",3,dps=100))
    manager.add_effect(StatusEffect("Poison",3,dps=1))
    assert manager.effects[0].dps>=100

def test_player_slow_uses_strongest_source_with_floor_after_haste_cap(combat):
    from logic.status_effects import apply_slow
    p,e,g=combat()
    p.stats["speed"]=100
    p._base_speed_mod=2
    p._adrenaline_timer=1
    p._gladiator_timer=1
    p._ks_stacks=50
    apply_slow(p.effect_manager,3,.5,"Mud")
    apply_slow(p.effect_manager,3,.1,"Ice")
    p.effect_manager.update(.01,p,g)
    assert p.get_movement_speed()==pytest.approx(2.4)
    p.dash_active_timer=1
    assert p.get_movement_speed()==pytest.approx(8.4)

def test_friendly_black_hole_does_not_pull_or_hurt_owner(combat):
    from entities.cloud import Cloud
    p,e,g=combat()
    p.x=10
    cloud=Cloud(8,0,0,120,3,is_black_hole=True)
    cloud.update(.1,g)
    assert p.x==10
    assert p.hp==1000
    assert e.x<70
    assert e.hp==1000000

def test_hostile_black_hole_deals_continuous_damage(combat):
    from entities.cloud import Cloud
    p,e,g=combat()
    p.x=10
    p.stats["dodgeChance"]=1
    cloud=Cloud(8,0,0,120,3,is_black_hole=True,is_hostile=True)
    cloud.dmg=20
    cloud.update(.1,g)
    assert p.x<10
    assert p.hp==pytest.approx(998)

@pytest.mark.parametrize("fps",[30,60,144])
def test_shield_recovery_preserves_partial_delay(combat,fps):
    p,e,g=combat()
    p.max_energy_shield=100
    p.energy_shield=0
    p.es_timer=.35
    for _ in range(fps):
        p.update_recovery(1/fps,g)
    assert p.energy_shield==pytest.approx(6.5)

@pytest.mark.parametrize("fps",[30,60,144])
def test_hostile_black_hole_terminal_tick(combat,fps):
    from entities.cloud import Cloud
    p,e,g=combat()
    cloud=Cloud(8,0,0,120,.15,is_black_hole=True,is_hostile=True)
    cloud.dmg=20
    for _ in range(fps):
        cloud.update(1/fps,g)
    assert p.hp==pytest.approx(997)
    assert cloud.dead

def test_equal_budget_warrior_builds_keep_damage_survival_tradeoff():
    from tools.measure_combat_balance import build,primary_dps,survival
    tank=build("warrior",20,19,2,"defense")
    damage=build("warrior",20,19,2,"offense")
    tdps,tleech=primary_dps(tank,20)
    ddps,dleech=primary_dps(damage,20)
    assert len(tank.allocated_nodes)==len(damage.allocated_nodes)==20
    assert ddps > tdps*1.2
    assert survival(tank,20,tleech)["survival_s"] > survival(damage,20,dleech)["survival_s"]*1.5
    # Six contacts must remain threatening even with a sustainable primary attack.
    assert not survival(tank,20,tleech)["alive"]

def test_late_sustain_cannot_afk_through_six_contacts():
    from tools.measure_combat_balance import build,primary_dps,survival
    p=build("bloodwalker",50,49,1,"offense")
    _,leech=primary_dps(p,50)
    result=survival(p,50,leech)
    assert not result["alive"]
    assert 5 < result["survival_s"] < 25


def test_secondary_damage_cannot_generate_leech_or_another_proc(combat):
    p,e,g=combat()
    p.hp=500
    p.stats["lifesteal"]=.5
    p.lightning_proc_hits=1
    p.self_dmg_on_hit=.02
    e.take_damage(10,g,from_player=True,is_secondary=True)
    assert e.hp==pytest.approx(999990)
    assert p.hp==500
    assert p.lifesteal_buffer==0
    assert getattr(p,"_lightning_hit_count",0)==0

def test_lightning_one_hit_threshold_is_finite_and_costs_once(combat):
    p,e,g=combat()
    p.lightning_proc_hits=1
    p.self_dmg_on_hit=.02
    p.stats["lifesteal"]=.2
    e.take_damage(10,g,from_player=True)
    assert e.hp==pytest.approx(999970)
    assert p.hp==980
    assert p.lifesteal_buffer==pytest.approx(2)
    assert g.record_damage_dealt.call_count==2

def test_piercing_fire_has_one_pulse_and_no_persistent_cloud(combat):
    from entities.projectile import Projectile
    p,e,g=combat()
    targets=[]
    for i in range(6):
        foe=Enemy(i+1,70,0,g)
        foe.hp=foe.max_hp=1000000
        foe.armor=0
        targets.append(foe)
    g.enemies=targets
    projectile=Projectile(20,70,0,1,0,10,pierce=6,aoe=100)
    projectile.fire_dmg=20
    for foe in targets:
        projectile.on_hit(foe,g)
    assert sum(1000000-foe.hp for foe in targets)==pytest.approx(120)
    assert not g.clouds
    assert all(len(foe.effect_manager.effects)==1 for foe in targets)

def test_bomb_cloud_dot_bonus_does_not_increase_impact(combat):
    from entities.projectile import Projectile
    p,e,g=combat()
    projectile=Projectile(2,70,0,1,0,5,p_type="bomb",aoe=100)
    projectile.fire_dmg=10
    projectile.poison_dps=12
    projectile.dot_mult=3
    g.particles=[]
    projectile.explode(g)
    assert 1000000-e.hp==pytest.approx(10)
    assert g.clouds[0].fire_dmg==30
    assert g.clouds[0].poison_dps==36

@pytest.mark.parametrize("class_id",["warrior","ninja","bloodwalker"])
def test_critical_multiplier_has_consumption_cap(combat,class_id):
    p,e,g=combat(class_id)
    p.stats.update(critChance=0,critDmg=100)
    p.specialization.execute_attack(p,g)
    normal=1000000-e.hp
    before=e.hp
    p.stats["critChance"]=1
    p.specialization.execute_attack(p,g)
    assert before-e.hp==pytest.approx(normal*3.5)

@pytest.mark.parametrize("class_id",["sniper","sorcerer","alchemist","bomber","engineer","beastmaster"])
def test_offclass_sword_scales_with_weapon_and_keeps_class(combat,class_id):
    p,e,g=combat(class_id)
    p.inv_manager.equipped["weapon"]={"name":"Sword","isMelee":True}
    p.stats.update(physDmg=10,critChance=0)
    p.specialization.execute_attack(p,g)
    damage=1000000-e.hp
    before=e.hp
    p.stats["physDmg"]=100
    p.specialization.execute_attack(p,g)
    assert before-e.hp==pytest.approx(damage*10)
    assert p.class_id==class_id

def test_excess_projectiles_keep_bounded_attack_budget(combat):
    p,e,g=combat("sniper")
    p.stats.update(projectileCount=1,critChance=0,bounce=0,pierce=0)
    p.shoot(g)
    single=g.projectiles[0].dmg
    g.projectiles=[]
    p.stats["projectileCount"]=100
    p.shoot(g)
    assert len(g.projectiles)==6
    assert sum(x.dmg for x in g.projectiles)<=single*3
    assert all(x.fire_dmg==0 for x in g.projectiles)

def test_mine_uses_element_payload_and_keeps_crit(combat):
    p,e,g=combat("bomber")
    p.stats.update(fireDamage=10,frostDamage=20,physDmgMult=.5,critChance=1)
    p.specialization.execute_attack(p,g)
    projectile=g.projectiles[0]
    assert projectile.fire_dmg>0 and projectile.frost_dmg>0
    projectile.x,projectile.y=e.x,e.y
    projectile.explode(g)
    mine=g.clouds[0]
    expected=(projectile.dmg+(projectile.fire_dmg+projectile.frost_dmg)*projectile.hit_crit_mult)*projectile.mine_dmg_mult
    assert mine.mine_dmg==pytest.approx(expected)
    assert mine.is_crit
    assert mine.poison_dps==0
    e.take_damage=Mock()
    mine.detonate(g)
    assert e.take_damage.call_args.kwargs["is_crit"]

def test_overkill_does_not_generate_damage_or_leech(combat):
    p,e,g=combat()
    e.hp=5
    p.hp=500
    p.stats["lifesteal"]=.2
    e.take_damage(10000,g,from_player=True)
    assert e.hp==0
    assert p.lifesteal_buffer==pytest.approx(1)
    g.record_damage_dealt.assert_called_once_with(5,is_dot=False)

@pytest.mark.parametrize("class_id",["warrior","bloodwalker"])
def test_melee_fire_splash_scales_linearly_with_targets(combat,class_id):
    p,e,g=combat(class_id)
    p.stats.update(fireDamage=20,critChance=0)
    foes=[e]
    for i in range(5):
        foe=Enemy(i+2,70,0,g)
        foe.hp=foe.max_hp=1000000
        foe.armor=0
        foes.append(foe)
    g.enemies=foes
    p.specialization.execute_attack(p,g)
    # Each recipient gets at most one 10-damage secondary fire splash.
    p.stats["fireDamage"]=0
    g.enemies=[e]
    before=e.hp
    p.specialization.execute_attack(p,g)
    physical=before-e.hp
    # Subtract the second probe from the first target.
    first_damage=sum(1000000-foe.hp for foe in foes)-physical
    assert first_damage==pytest.approx(6*physical+6*10*p.stats['dmgMult']*p.get_elemental_mults()[0])


@pytest.mark.parametrize("fps",[30,60,144])
def test_fast_piercing_projectile_hits_all_crossed_targets(combat,fps):
    from entities.projectile import Projectile
    p,e,g=combat()
    foes=[]
    for i in range(6):
        foe=Enemy(i+1,70+i*20,0,g)
        foe.hp=foe.max_hp=1000000
        foe.armor=0
        foes.append(foe)
    g.enemies=foes
    projectile=Projectile(20,0,0,100,0,10,pierce=6)
    for _ in range(fps):
        if not projectile.dead:
            projectile.update(1/fps,g)
    assert all(foe.hp==pytest.approx(999990) for foe in foes)

def test_fast_hostile_projectile_cannot_tunnel_through_player(combat):
    from entities.projectile import Projectile
    p,e,g=combat()
    p.x=70
    projectile=Projectile(20,0,0,100,0,10,is_hostile=True)
    projectile.update(.03,g)
    assert p.hp==990
    assert projectile.dead

def test_swept_collision_hits_nearest_before_farther_target(combat):
    from entities.projectile import Projectile
    p,e,g=combat()
    near=Enemy(2,40,0,g)
    near.hp=near.max_hp=1000000
    near.armor=0
    g.enemies=[e,near]
    projectile=Projectile(20,0,0,100,0,10)
    projectile.update(.03,g)
    assert near.hp==999990
    assert e.hp==1000000

def test_death_explosion_is_bounded_by_player_not_boss_life(combat):
    p,e,g=combat()
    p.stats.update(physDmg=100,physDmgFlat=0,fireDamage=0,frostDamage=0,poisonDps=0,dmgMult=2)
    assert p.get_death_explosion_damage(100)==30
    assert p.get_death_explosion_damage(100000000)==800

def test_environment_ignores_player_pierce_combo_and_impossible_penalty(combat):
    p,e,g=combat()
    e.armor=100
    p.stats.update(armorPen=1,brutal=2,killComboDmg=1)
    g.kill_streak=100
    g.wave["current_diff"]="Impossible"
    e.take_damage(20,g)
    assert e.hp==999990

@pytest.mark.parametrize("class_id",["warrior","ninja","bloodwalker"])
def test_frost_dot_bonus_is_consistent_for_melee(combat,class_id):
    p,e,g=combat(class_id)
    p.stats.update(frostDamage=20,dotDmgMult=0,critChance=0)
    e.apply_dot=Mock()
    p.specialization.execute_attack(p,g)
    base=next(c.args[1] for c in e.apply_dot.call_args_list if c.args[0]=="frost")
    e.apply_dot.reset_mock()
    p.stats["dotDmgMult"]=1
    p.specialization.execute_attack(p,g)
    enhanced=next(c.args[1] for c in e.apply_dot.call_args_list if c.args[0]=="frost")
    assert enhanced==pytest.approx(base*2)

@pytest.mark.parametrize("class_id",["sorcerer","alchemist","bomber"])
def test_area_build_damage_stays_close_across_fps(class_id):
    from tools.measure_combat_balance import build,primary_dps
    results=[]
    for fps in (30,60,144):
        p=build(class_id,20,19,2,"offense")
        damage,_=primary_dps(p,20,target_count=6,fps=fps)
        results.append(damage)
    assert max(results)/min(results)<1.08, (class_id,results)

def test_bomber_starting_damage_has_viable_preparation_budget():
    from tools.measure_combat_balance import build,primary_dps
    warrior,_=primary_dps(build("warrior",1,0,4,"offense"),1)
    bomber,_=primary_dps(build("bomber",1,0,4,"offense"),1)
    assert warrior*.5 < bomber < warrior


@pytest.mark.parametrize("class_id",["warrior","ninja","bloodwalker","sniper","sorcerer","alchemist","bomber","engineer","beastmaster"])
def test_flame_weapon_keeps_cone_mechanics_across_classes(combat,class_id):
    p,e,g=combat(class_id)
    p.inv_manager.equipped["weapon"]={"name":"Flame","isFlamethrower":True}
    p.stats.update(fireDamage=10,critChance=0)
    p.specialization.execute_attack(p,g)
    assert e.hp<1000000
    assert not g.projectiles
    assert any(effect.name=="Burn" for effect in e.effect_manager.effects)
    assert p.class_id==class_id

@pytest.mark.parametrize("class_id",["warrior","ninja","bloodwalker","sniper","sorcerer","engineer","beastmaster"])
def test_bomb_family_is_thrown_across_classes(combat,class_id):
    p,e,g=combat(class_id)
    p.inv_manager.equipped["weapon"]={"name":"Grenade","isBomb":True}
    p.stats.update(poisonDps=10,critChance=0)
    p.specialization.execute_attack(p,g)
    assert g.projectiles
    assert all(projectile.type=="bomb" and projectile.airborne for projectile in g.projectiles)
    assert p.class_id==class_id


@pytest.mark.parametrize("fps",[30,60,144])
def test_actual_attack_cadence_preserves_fractional_time(combat,fps):
    p,e,g=combat()
    p.stats["attack_cooldown"]=75
    p._attack_elapsed=0
    attacks=0
    for _ in range(fps*3):
        attacks+=p.update_attack(1/fps,g,True)
    assert attacks==40

def test_idle_attack_cannot_bank_an_unbounded_burst(combat):
    p,e,g=combat()
    p.stats["attack_cooldown"]=100
    p.update_attack(30,g,False)
    assert p.update_attack(.01,g,True)==1
    assert p.update_attack(30,g,True)<=4

def test_added_damage_effectiveness_preserves_weapon_base(combat):
    p,e,g=combat("engineer")
    p.inv_manager.equipped["weapon"]={"itemBase":{"fireDamage":30,"attackCooldown":70}}
    p.stats.update(fireDamage=100,fireDmgFlat=0)
    assert p.get_added_damage_effectiveness()==pytest.approx(.2)
    assert p.get_elemental_base("fireDamage","fireDmgFlat")==pytest.approx(44)

def test_swept_projectile_preserves_attackable_pillar(combat):
    from entities.projectile import Projectile
    p,e,g=combat()
    e.is_trap=True
    e.type="pillar"
    projectile=Projectile(20,0,0,100,0,10)
    projectile.update(.03,g)
    assert e.hp==999990

@pytest.mark.parametrize("class_id", list(SkillTree.START_BY_CLASS.keys()))
def test_initial_clusters_offer_three_distinct_support_entries(class_id):
    start=SkillTree.START_BY_CLASS[class_id]
    choices=SkillTree.allocatable_nodes({start})
    assert len(choices)==3
    assert len({SkillTree.BY_ID[n]['cluster'] for n in choices})==3
    for entry in choices:
        ring=[entry.rsplit('_',1)[0]+'_'+str(j) for j in range(7)]
        for direction in ((0,1,2),(0,6,5)):
            allocated={start}
            for j in direction:
                assert SkillTree.is_allocatable(ring[j],allocated)
                allocated.add(ring[j])
            notable=entry.rsplit('_',1)[0]+'_notable'
            assert SkillTree.is_allocatable(notable,allocated)

def make_duel(combat):
    from entities.boss import AbyssalLord
    from entities.projectile_pool import ProjectilePool
    player,_,game=combat()
    player.x,player.y=2650,2500
    player.take_damage=Mock(return_value=0)
    game.projectile_pool=ProjectilePool(100)
    boss=AbyssalLord(2,2500,2500,game,10)
    game.enemies=[boss]
    return player,boss,game

@pytest.mark.parametrize("fps",[30,60,144])
def test_boss_cadence_and_projectile_ceiling_ignore_fps(combat,fps):
    p,b,g=make_duel(combat)
    b.hp=b.max_hp*.25
    peak=0
    for _ in range(fps*60):
        b.update(1/fps,g)
        g.projectile_pool.update(1/fps,g)
        peak=max(peak,len(g.projectile_pool.active_objects))
    assert b.attacks_resolved==17
    assert peak<=7
    assert not b.invulnerable
    assert b.state in ("recover","windup","charge")

@pytest.mark.parametrize("move",["cleave","charge","ring","slam"])
def test_boss_no_damage_or_projectile_before_warning_finishes(combat,move):
    p,b,g=make_duel(combat)
    b.begin_attack(g)
    b.move=move
    b.timer=b.MOVES[move][0]
    b.update(b.timer-.01,g)
    assert not p.take_damage.called
    assert not g.projectile_pool.active_objects
    assert b.state=="windup"

def test_boss_cleave_has_safe_rear_and_recovery(combat):
    p,b,g=make_duel(combat)
    b.begin_attack(g)
    p.x=2350
    b.update(1,g)
    p.take_damage.assert_not_called()
    assert b.state=="recover" and b.timer==pytest.approx(1.8)
    before=b.hp
    b.take_damage(100,g,from_player=True)
    assert b.hp<before

def test_boss_slam_has_safe_melee_interior(combat):
    p,b,g=make_duel(combat)
    p.x=2570
    b.move="slam"
    b.telegraph_origin=(2500,2500)
    b.resolve_attack(g)
    p.take_damage.assert_not_called()
    p.x=2700
    b.resolve_attack(g)
    assert p.take_damage.call_count==1

def test_boss_charge_locks_aim_and_hits_once(combat):
    p,b,g=make_duel(combat)
    b.begin_attack(g)
    b.move="charge"
    b.resolve_attack(g)
    for _ in range(60):
        b.update(.55/60,g)
    assert p.take_damage.call_count==1
    assert b.state=="recover"
    assert b.x==pytest.approx(b.charge_end[0])

def test_boss_ring_leaves_player_corridor_and_clears_on_death(combat):
    import math
    p,b,g=make_duel(combat)
    b.move="ring"
    b.aim=0
    b.resolve_attack(g)
    shots=g.projectile_pool.active_objects
    assert len(shots)==7
    assert all(abs(math.atan2(s.vy,s.vx))>math.pi/3 for s in shots)
    for _ in range(240):
        g.projectile_pool.update(1/120,g)
    assert not g.projectile_pool.active_objects
    p.take_damage.assert_not_called()
    b.resolve_attack(g)
    b.take_damage(b.hp*100,g,from_player=True)
    assert b.dead and not any(s.active for s in b.owned_projectiles)

def test_boss_difficulty_preserves_health_ratio(combat):
    p,b,g=make_duel(combat)
    b.hp=b.max_hp*.4
    b.apply_difficulty("Hard")
    assert b.hp/b.max_hp==pytest.approx(.4)
    assert b.boss_dmg_mult==1.5

def test_boss_pool_swept_collision_does_not_skip_player(combat):
    from entities.projectile_pool import BossProjectile
    p,_,g=combat()
    p.x,p.y=100,0
    p.take_damage=Mock(return_value=5)
    shot=BossProjectile()
    shot.reset(0,0,100,0,5,lifetime=120)
    shot.update(1/30,g)
    p.take_damage.assert_called_once_with(5)
    assert not shot.active and p.last_attacker_type=="boss"

def test_avoided_boss_projectile_does_not_apply_burn(combat):
    from entities.projectile_pool import BossProjectile
    p,_,g=combat()
    p.take_damage=Mock(return_value=0)
    shot=BossProjectile()
    shot.reset(p.x,p.y,0,0,5,status_effect="burn")
    shot.update(.01,g)
    assert not p.effect_manager.effects

def test_clusters_have_independent_cross_paths_and_pivots():
    for cls in SkillTree.START_BY_CLASS:
        entry=SkillTree.BY_ID[next(iter(SkillTree.ADJ['start_'+cls]))]
        ring_ids={n['id'] for n in SkillTree.NODES if n['arm']==cls and n.get('cluster')==entry['cluster']}
        exits={nb for n in ring_ids for nb in SkillTree.ADJ[n] if nb not in ring_ids and nb!='start_'+cls}
        assert len(exits)>=2
        assert not any(SkillTree.BY_ID[n]['type']=='notable' for n in exits)


def test_dead_boss_does_not_clear_reused_projectile_of_another_boss(combat):
    p,b,g=make_duel(combat)
    b.move="ring"
    b.resolve_attack(g)
    shot=b.owned_projectiles[0]
    shot.reset(1,1,1,1,1)
    shot.boss_owner_id=12345
    b.clear_projectiles()
    assert shot.active

def sentry_fixture(combat):
    from entities.turret import Turret
    p,e,g=combat("engineer")
    p.x,p.y=1000,1000
    e.x,e.y=1300,1000
    g.turrets=[]
    p.level=1
    p.stats.update(turretDmg=1,turretRate=1,turretMaxHp=150,turretLimit=2,projectileCount=1,pierce=0,bounce=0,physDmg=10,physDmgFlat=0,dmgMult=1,armor=0)
    t=Turret(100,1100,1000,owner=p)
    g.turrets.append(t)
    return p,e,g,t

@pytest.mark.parametrize("fps",[30,60,144])
def test_turret_timing_with_boot_is_independent_of_fps(combat,fps):
    p,e,g,t=sentry_fixture(combat)
    for _ in range(10*fps): t.update(1/fps,g)
    assert t.shot_count==17
    assert t.age==pytest.approx(10)

def test_turret_expiry_does_not_fire_past_lifetime(combat):
    p,e,g,t=sentry_fixture(combat)
    t.age=23.9
    t.boot_remaining=0
    t.update(1,g)
    assert t.dead and t.shot_count==0

def test_live_turret_stats_preserve_health_ratio_and_use_pixel_range(combat):
    p,e,g,t=sentry_fixture(combat)
    t.hp=75
    p.stats.update(turretMaxHp=300,turretRange=25,turretDmg=2,turretRate=2)
    t.sync_stats()
    assert t.hp==150 and t.range==525 and t.dmg_mult==2 and t.fire_rate==2

def test_turret_keeps_target_until_focus_command(combat):
    from entities.enemy import Enemy
    p,e,g,t=sentry_fixture(combat)
    t.choose_target(g)
    other=Enemy(3,1120,1000,g)
    g.enemies.append(other)
    assert t.choose_target(g) is e
    p.aim_x,p.aim_y=other.x,other.y
    assert p.try_command_turrets(g)
    assert t.choose_target(g) is other
    assert not p.try_command_turrets(g)
    p.update_turret_command(10)
    assert p.turret_command_cooldown==0 and p.turret_focus_target is None

def test_turret_outside_control_radius_cannot_fire(combat):
    p,e,g,t=sentry_fixture(combat)
    p.x=-1000
    t.update(3,g)
    assert not g.projectiles
    p.x=1000
    t.update(.01,g)
    assert t.shot_count<=1

def test_turret_projectile_never_leechs_or_triggers_player_on_hit(combat):
    p,e,g,t=sentry_fixture(combat)
    p.hp=500
    p.stats["lifesteal"]=.5
    p.self_dmg_on_hit=.1
    p.take_damage=Mock()
    p.lightning_proc_hits=1
    t.boot_remaining=0
    t.shoot(g)
    g.projectiles[0].on_hit(e,g)
    assert p.lifesteal_buffer==0
    p.take_damage.assert_not_called()
    assert g.projectiles[0].is_turret_proj

def test_turret_impossible_penalty_applies_once(combat):
    p,e,g,t=sentry_fixture(combat)
    t.boot_remaining=0
    t.shoot(g)
    before=e.hp
    g.projectiles[-1].on_hit(e,g)
    normal=before-e.hp
    g.wave["current_diff"]="Impossible"
    t.shoot(g)
    before=e.hp
    g.projectiles[-1].on_hit(e,g)
    assert before-e.hp==pytest.approx(normal*.5)

@pytest.mark.parametrize("fps",[30,60,144])
def test_turret_each_contact_attacker_has_own_timer(combat,fps):
    from entities.enemy import Enemy
    p,e,g,t=sentry_fixture(combat)
    t.hp=t.max_hp=100000
    p.stats["turretMaxHp"]=100000
    e.x,e.y=t.x,t.y
    e.dmg=10
    second=Enemy(4,t.x,t.y,g)
    second.dmg=10
    g.enemies.append(second)
    for _ in range(fps): t.update(1/fps,g)
    assert t.max_hp-t.hp==pytest.approx(20*100/120)

def test_deploy_uses_cursor_caps_range_and_does_not_spend_charge_on_overlap(combat):
    p,e,g,t=sentry_fixture(combat)
    p.aim_x,p.aim_y=3000,1000
    p.turret_charges=2
    assert p.try_place_turret(g)
    placed=g.turrets[-1]
    assert placed.x==1280 and placed.y==1000
    assert p.turret_charges==1
    assert not p.try_place_turret(g)
    assert p.turret_charges==1

def test_deploy_replaces_only_owners_oldest_turret(combat):
    from entities.turret import Turret
    p,e,g,t=sentry_fixture(combat)
    t.age=10
    other=Turret(111,1200,1100,owner=Mock())
    g.turrets.append(other)
    p.stats["turretLimit"]=1
    p.aim_x,p.aim_y=1000,1250
    assert p.try_place_turret(g)
    assert t.dead and not other.dead

def test_no_command_when_silenced_dead_or_no_turrets(combat):
    p,e,g,t=sentry_fixture(combat)
    p.is_silenced=True
    assert not p.try_command_turrets(g)
    p.is_silenced=False
    p.hp=0
    assert not p.try_command_turrets(g)
    p.hp=100
    g.turrets=[]
    assert not p.try_command_turrets(g)

def test_legacy_saved_kit_is_normalized_without_losing_affixes(combat):
    p,e,g,t=sentry_fixture(combat)
    item=p.inv_manager.equipped["weapon"]
    item["itemBase"]={"turretDmg":1.1,"projectileCount":1,"magicFind":.3}
    item["prefixes"]=[{"stat":"armor","val":3,"name":"Test"}]
    p.inv_manager.recalculate_stats()
    assert item["itemBase"]["physDmg"]==10
    assert item["itemBase"]["turretDmg"]==.1
    assert item["itemBase"]["magicFind"]==.3
    assert item["prefixes"][0]["val"]==3
    before=dict(p.stats)
    p.inv_manager.recalculate_stats()
    assert p.stats==before

def test_engineer_roundtrip_preserves_sentries_and_command_cooldown(combat,tmp_path,monkeypatch):
    from logic.game_logic import GameLogic
    from logic.save_manager import SaveManager
    monkeypatch.setattr(SaveManager,"SAVE_DIR",str(tmp_path))
    src=GameLogic(None,1024,768,"engineer")
    p=src.players[src.local_player_id]
    p.aim_x,p.aim_y=p.x+180,p.y
    assert p.try_place_turret(src)
    t=src.turrets[-1]
    t.age=12
    t.hp=t.max_hp*.6
    p.turret_command_cooldown=7
    p.turret_recharge=2
    SaveManager.save_game(src,"sentry")
    dst=GameLogic(None,1024,768,"engineer")
    SaveManager.load_game(dst,"sentry")
    q=dst.players[dst.local_player_id]
    assert q.turret_charges==p.turret_charges
    assert q.turret_recharge==2 and q.turret_command_cooldown==7
    assert len(dst.turrets)==1
    restored=dst.turrets[0]
    assert restored.age==12
    assert restored.hp/restored.max_hp==pytest.approx(.6)
    assert restored.owner is q

def test_engineer_hud_exposes_deploy_and_focus(combat):
    from scenes.game_scene import GameScene
    p,e,g,t=sentry_fixture(combat)
    scene=GameScene.__new__(GameScene)
    abilities=scene.get_abilities(p)
    assert any(a["key"]=="R" for a in abilities)
    assert any(a["key"]=="E" and a["name"]=="Odak Ateşi" for a in abilities)

def test_turret_multiple_barrels_converge_on_single_target(combat):
    p,e,g,t=sentry_fixture(combat)
    t.boot_remaining=0
    t.shoot(g)
    first=g.projectiles.pop()
    before=e.hp
    first.on_hit(e,g)
    single=before-e.hp
    p.stats["projectileCount"]=4
    t.shoot(g)
    before=e.hp
    for shot in g.projectiles:
        for _ in range(100):
            if shot.dead: break
            shot.update(1/120,g)
    assert before-e.hp==pytest.approx(single*4/1.9)

def test_architect_repairs_only_near_owner_and_after_damage_delay(combat):
    p,e,g,t=sentry_fixture(combat)
    p.evolution_passive="heal_turret"
    t.hp=75
    t.age=5
    t.update(1,g)
    assert t.hp==pytest.approx(78.75)
    t.take_damage(10,g)
    hp=t.hp
    t.update(.5,g)
    assert t.hp==hp
    p.x=-1000
    t.update(3,g)
    assert t.hp==hp

def test_old_engineer_save_without_new_fields_loads_with_ready_charges(combat,tmp_path,monkeypatch):
    from logic.game_logic import GameLogic
    from logic.save_manager import SaveManager
    monkeypatch.setattr(SaveManager,"SAVE_DIR",str(tmp_path))
    src=GameLogic(None,1024,768,"engineer")
    SaveManager.save_game(src,"legacy")
    path=tmp_path/"legacy.json"
    data=json.loads(path.read_text(encoding="utf-8"))
    data.pop("turrets")
    for name in ("turret_charges","turret_recharge","turret_command_cooldown"):
        data["player"].pop(name)
    path.write_text(json.dumps(data),encoding="utf-8")
    dst=GameLogic(None,1024,768,"engineer")
    SaveManager.load_game(dst,"legacy")
    q=dst.players[dst.local_player_id]
    assert q.turret_charges==q.get_turret_max_charges()
    assert q.turret_command_cooldown==0

@pytest.mark.parametrize("flat,ratio,remaining", [(2, 0, 98), (2, .2, 78.4), (200, 0, 0)])
def test_flat_armor_penetration_preserves_percentage_units(combat, flat, ratio, remaining):
    player, enemy, game = combat()
    enemy.armor = 100
    player.stats.update(armorPenFlat=flat, armorPen=ratio, bossDmgMult=0)
    before = enemy.hp
    enemy.take_damage(100, game, from_player=True)
    assert before - enemy.hp == pytest.approx(100 * 100 / (100 + remaining))


def test_late_boss_still_threatens_scaled_life_builds(combat):
    from tools.measure_combat_balance import build
    from entities.boss import AbyssalLord
    player,enemy,game=combat()
    boss=AbyssalLord(2,70,0,game,50)
    for route in ('offense','defense'):
        p=build('warrior',50,49,1,route)
        p.stats['dodgeChance']=0
        before=p.hp
        p.take_damage(boss.attack_damage(boss.MOVES['slam'][2]),force=True)
        fraction=(before-p.hp)/p.max_hp
        assert .04<fraction<.3
    early=AbyssalLord(3,70,0,game,10)
    assert early.attack_damage(22)<100
