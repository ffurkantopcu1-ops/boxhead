"""Random wave rules stay disabled, including legacy session/save data."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import json
from types import SimpleNamespace
from unittest.mock import patch
import pygame
import pytest
from logic.game_logic import GameLogic
from logic.save_manager import SaveManager
from entities.enemy import Enemy

LEGACY_EVENT = dict(id="legacy", desc="OLD EVENT", enemy_speed=2,
                    force_elite=True, enemy_count_mult=3, enemy_hp_mult=4,
                    xp_mult=.5, regen_mult=2, rare_drop=True, sound_aggro=True)

@pytest.fixture
def game(tmp_path, monkeypatch):
    monkeypatch.setattr(SaveManager, "SAVE_DIR", str(tmp_path))
    pygame.init()
    pygame.display.set_mode((64,64))
    return GameLogic(SimpleNamespace(), 1280, 720)

@pytest.mark.parametrize("wave", [1, 4, 6, 11, 31])
def test_new_wave_ignores_legacy_event_even_when_random_roll_is_zero(game, wave):
    game.wave.update(level=wave-1, event=LEGACY_EVENT.copy())
    with patch("random.random", return_value=0):
        game.next_wave()
    assert game.wave["event"] is None
    from logic.wave_pacing import wave_count
    assert game.wave["total_to_spawn"] == wave_count(wave, "Normal")
    assert game.wave["announce_lines"] == [f"DALGA {wave} BAŞLIYOR!"]

def test_legacy_event_does_not_alter_enemy_or_regeneration(game):
    game.wave.update(level=1, event=LEGACY_EVENT.copy())
    enemy = Enemy(1, 300, 300, game, type="swarm_bat")
    original_hp, original_damage, original_speed = enemy.hp, enemy.dmg, enemy.speed
    game._apply_global_modifiers(enemy)
    assert enemy.type == "swarm_bat"
    assert enemy.hp == original_hp
    assert enemy.dmg == original_damage
    assert enemy.speed == pytest.approx(original_speed*1.1)  # forest only
    p = game.players["p1"]
    p.hp = 20
    p.stats.update(regen=4, hpRegen=0, combatRegen=0)
    p.update_recovery(1,game)
    assert p.hp == pytest.approx(24)

def test_load_legacy_wave_preserves_progress_and_discards_event(game, tmp_path):
    game.wave.update(level=4,event=LEGACY_EVENT.copy())
    p = game.players["p1"]
    p.gold = 123
    p.revive_count = 0
    SaveManager.save_game(game,"legacy")
    path = tmp_path/"legacy.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["wave"]["event"] = LEGACY_EVENT.copy()
    path.write_text(json.dumps(data),encoding="utf-8")
    SaveManager.load_game(game,"legacy")
    assert game.wave["level"] == 4
    assert game.wave["event"] is None
    assert p.gold == 123
    assert p.revive_count == 0

@pytest.mark.parametrize("wave", [5, 10, 15])
def test_scheduled_encounters_remain(game, wave):
    game.wave["level"] = wave-1
    game.next_wave()
    assert game.wave["event"] is None
    if wave == 10:
        assert any(e.type == "boss" for e in game.enemies)
    else:
        assert game.wave["special"] == game.SPECIAL_WAVES[wave]
