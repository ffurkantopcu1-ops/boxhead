# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Boxhead 2.0 is a single-player, top-down arena action game in Python + Pygame. UI
copy is Turkish; identifiers and comments are English. Run all commands from the
repo root — asset and save paths are relative to the current working directory.

## Related docs (read before non-trivial work)

- `AGENTS.md` — the authoritative, detailed contributor guide. Architecture
  invariants, the **class/evolution balance rules** (numeric envelopes every new
  class must stay inside), fixed-bug notes, and CI/release/patch-notes mechanics.
- `DESIGN.md` + `assets/ui/gothic/` — the **mandatory UI theme**. `assets/ui/gothic/`
  is the visual source of truth (dark stone frames, red gem rivets, skull crest);
  where DESIGN.md's older procedural description disagrees, the gothic assets win.

## Commands

```powershell
pip install -r requirements.txt        # runtime deps (pygame, truststore, certifi)
python main.py                          # run the game (opens a fullscreen window)

# Syntax check — the project's primary lint gate. Force UTF-8 so Turkish output
# doesn't crash under a legacy console encoding.
$env:PYTHONUTF8='1'; python check_all_syntax.py

# Headless import smoke test (no window)
$env:PYGAME_HIDE_SUPPORT_PROMPT='1'; $env:SDL_VIDEODRIVER='dummy'; $env:SDL_AUDIODRIVER='dummy'; python -c "import pygame; pygame.init(); from scene_manager import SceneManager"

# Tests (headless; set SDL drivers to dummy first as CI does)
$env:SDL_VIDEODRIVER='dummy'; $env:SDL_AUDIODRIVER='dummy'; python -m pytest tests/ -v
python -m pytest tests/test_balance.py -v            # a single test file
python -m pytest tests/test_balance.py::<name> -v    # a single test
```

`main.py` opens a borderless/fullscreen window and runs a 144 FPS loop — **do not
launch it in headless/unattended validation**; use the smoke test and pytest
instead. CI (`.github/workflows/ci.yml`, windows-latest, Python 3.13) runs exactly
these three gates: syntax check, import smoke test, unit tests. There is no
enforced formatter or type checker.

## Architecture

Flow: `main.py → SceneManager → Scene → GameLogic/entities`. Preserve it.

- **`main.py`** — Pygame init, window, 144 FPS main loop. Delta time (`dt`) is
  passed in **seconds**.
- **`scene_manager.py`** — owns the three persistent scene instances (`MainMenu`,
  `Game`, `ClassSelect`) and transitions. All scene switches go through
  `change_scene()` so `on_enter()` runs. Also owns display-mode handling: the game
  renders to a fixed 1920×1080 `logical_surface`, then `draw()` smoothscales it to
  the real window. Global settings persist to `saves/settings.json`.
- **`scenes/`** — input handling + rendering per screen (`base_scene.py`,
  `menu_scene.py`, `game_scene.py`, `class_select_scene.py`). Scenes get
  `(manager, screen, width, height)` and implement `on_enter()`, `update(dt, events)`,
  `draw()`. `game_scene.py` is the main UI/controller layer and pauses simulation
  while inventory/settings overlays are open. **Keep event consumption in the scene
  layer; keep simulation and rules in `logic/` or entities.**
- **`logic/game_logic.py`** — central gameplay state and update loop. Owns players,
  enemies, drops, projectiles, waves, biome/card/quest systems, and combat events.
  `GameLogic.state` is a small state machine (`PLAYING`, `CARD_SELECT`,
  `EVOLUTION_SELECT`, `GAMEOVER`); new overlays must respect these states and the
  existing pause behavior.
- **`logic/`** — independent systems: items, inventory (`inventory_manager.py`),
  cards, synergies, quests, auras, hazards, biomes, elites, crystal shop, status
  effects, persistence (`save_manager.py`).
- **`entities/`** — mutable world entities. **Class-specific combat lives in
  `<class>_logic.py`** (e.g. `warrior_logic.py`, `ninja_logic.py`) and is selected
  by `entities/player.py`. `player.py` and `enemy.py` are large and coupled — keep
  changes focused, no opportunistic rewrites.
- **`ui_theme.py` / `ui_nineslice.py` / `ui_elements.py`** — the gothic theme layer.
  Build UI through these (`Button`, `draw_panel`, `draw_inset_frame`, `render_title`,
  `COLORS`), never with bare `pygame.draw.rect(..., border_radius=N)`. See DESIGN.md.
- **`launcher/`** — standalone Tkinter auto-update launcher (`config.py`,
  `updater.py` = GUI-less update logic, `main.py` = GUI). It never touches `saves/`.

## Invariants that have bitten before

- **World vs screen coordinates are distinct.** Entity draw methods take camera
  offsets; `GameScene` owns camera/zoom and HUD coordinates.
- **Collections mutate mid-update.** When removing during iteration, follow the
  existing snapshot pattern (`items[:]`) or deferred removal.
- **Save/load is a cross-module contract** between `logic/save_manager.py`,
  `GameLogic`, `Player`, and `InventoryManager`. Adding a persistent field means
  updating both serialization and restoration, defaulting for old saves (`.get()`/
  `getattr()`), and testing a round trip. Never overwrite/normalize real files in
  `saves/` during tests. Use `logic.save_manager.SaveManager` — the root-level
  `save_manager.py` is stale and not imported by runtime code.
- **String IDs are shared contracts**: class names, item/orb IDs, rarities, card
  IDs, enemy types, scene names, difficulty labels. Search all consumers before
  renaming one.
- **Adding a class is a multi-file contract.** Balance envelopes and the full
  touchpoint checklist (`class_bases`, starting weapon, `<class>_logic.py`, class
  select scene, passives, two `EVOLUTIONS` entries, item tiers, save compat) are in
  AGENTS.md — follow them.
- Preserve Turkish UI copy and UTF-8 source. PowerShell may display valid UTF-8 as
  mojibake; do not rewrite strings because the terminal looks corrupted.
- Reuse fonts/surfaces/pools in hot paths; never load images or allocate large
  surfaces per frame.
- Don't edit `.exe`, `__pycache__/`, generated sprites, `saves/`, or `version.txt`
  unless the task requires it. Never delete `Boxhead.spec` / `Boxhead_Launcher.spec`
  (the release workflow builds from them).

## Versioning & release

`version.txt` (SemVer) is the single source of truth; `logic/version.py` reads it at
runtime (source and PyInstaller-bundled paths), `scenes/menu_scene.py` displays it.
Pushing a `v*` tag triggers `.github/workflows/release.yml`, which validates the tag
matches `version.txt`, builds with PyInstaller, and publishes the release. See
`RELEASE.md`.

Write commit subjects with conventional prefixes (`feat:`, `fix:`, `balance:`,
`perf:`, `refactor:`) — `tools/generate_patch_notes.py` turns them into the
user-facing `data/patch_notes.json` **verbatim**. That file is auto-generated; never
edit it by hand. Regenerate before tagging: `$env:PYTHONUTF8='1'; python tools/generate_patch_notes.py`.

## Validating UI changes

Alignment bugs here are consistently found by looking at a render, not by reading
code. Render offscreen (`$env:SDL_VIDEODRIVER='dummy'` or `pygame.HIDDEN`), build the
scene with a stub manager, call `scene.draw()`, and `pygame.image.save(...)`. Check
both idle and hover/selected states and the longest real text content.
