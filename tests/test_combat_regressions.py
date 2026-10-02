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
