# AGENTS.md

## Project Overview

Boxhead 2.0 is a single-player, top-down arena action game written in Python with
Pygame. It has no package manifest, build configuration, automated test suite, or
Git metadata in this directory. The checked-in `Boxhead.exe` and
`Boxhead_Launcher.exe` are distribution artifacts; the Python sources are the
authoritative implementation.

Run commands from the repository root. Asset and save paths are relative to the
current working directory.

## Repository Map

- `main.py`: Pygame initialization, borderless fullscreen window, and the 144 FPS
  main loop. Delta time is passed in seconds.
- `scene_manager.py`: owns the persistent scene instances and transitions among
  `MainMenu`, `ClassSelect`, and `Game`.
- `scenes/`: input handling and rendering for each screen. `game_scene.py` is the
  main UI/controller layer and intentionally pauses simulation while inventory or
  settings are open.
- `logic/game_logic.py`: central gameplay state and update loop. It owns players,
  enemies, drops, projectiles, waves, biome/card/quest systems, and transient
  combat events.
- `logic/`: independent gameplay systems such as items, inventory, cards,
  synergies, quests, auras, hazards, biomes, elites, crystal upgrades, status
  effects, and persistence.
- `entities/`: mutable world entities. Class-specific combat behavior lives in
  files such as `warrior_logic.py` and is selected by `entities/player.py`.
- `ui_elements.py`: reusable Pygame widgets and item-icon loading.
- `assets/` and `sounds/`: runtime media. Keep filenames stable unless all loading
  references are updated.
- `saves/`: mutable local player data, not fixtures. `meta.json` contains real
  progression and daily-quest state.
- `check_all_syntax.py`: the only repository-wide automated validation currently
  provided.
- `generate_enemy_sprites.py`, `transparent.py`, and `remove_bg_rembg.py`: offline
  asset utilities. They target `public/assets` and require inputs that are not
  present in this tree; they are not part of normal game startup.
- `logic/game_logic.py.tmp`: a stale-looking temporary copy. Do not treat it as
  runtime code or edit it unless the task explicitly concerns it.

## Setup And Commands

Use the existing Python 3 installation; the project is currently known to parse
under Python 3.13.

```powershell
python -m pip install pygame
python main.py
```

`main.py` immediately opens a borderless fullscreen window. Do not launch it in
headless or unattended validation. For a syntax check on Windows, force UTF-8 so
the Turkish success/error text does not fail under a legacy console encoding:

```powershell
$env:PYTHONUTF8='1'; python check_all_syntax.py
```

For a lightweight import smoke test that does not open the window:

```powershell
$env:PYGAME_HIDE_SUPPORT_PROMPT='1'; python -c "import pygame; from scene_manager import SceneManager"
```

The asset utilities additionally require Pillow, and `remove_bg_rembg.py` requires
`rembg`. Do not add these as runtime dependencies unless runtime code begins to
use them.

## Architecture And Invariants

- Preserve the flow `main.py -> SceneManager -> Scene -> GameLogic/entities`.
  Scene transitions must go through `SceneManager.change_scene()` so `on_enter()`
  runs.
- Scenes receive `(manager, screen, width, height)` and implement `on_enter()`,
  `update(dt, events)`, and `draw()`. Keep event consumption in the scene layer;
  keep simulation and rules in `logic/` or the relevant entity.
- `GameLogic.state` is a small state machine (`PLAYING`, `CARD_SELECT`,
  `EVOLUTION_SELECT`, `GAMEOVER`). New overlays must respect these states and the
  existing pause behavior.
- Time-based simulation receives seconds through `dt`. Some attacks and cooldowns
  also use Pygame/time timestamps; match the convention already used by the code
  being changed rather than silently mixing units.
- World coordinates and screen coordinates are distinct. Entity drawing methods
  accept camera offsets; `GameScene` owns camera/zoom and HUD coordinates.
- Collections are mutated during gameplay. Follow the existing snapshot iteration
  pattern (`items[:]`) or deferred removal when removing elements during updates.
- Save/load is a cross-module contract between `logic/save_manager.py`,
  `GameLogic`, `Player`, and `InventoryManager`. When adding persistent fields,
  update both serialization and restoration, use defaults for old saves, and test
  a round trip. Never overwrite or normalize existing files in `saves/` during a
  routine test.
- IDs such as class names, item/orb IDs, rarities, card IDs, enemy types, scene
  names, and difficulty labels are shared string contracts. Search all consumers
  before renaming one.
- `game_scene.py`, `player.py`, and `enemy.py` are large, coupled modules. Keep
  changes focused and avoid broad formatting or opportunistic rewrites.

## Code And Content Conventions

- Follow the existing straightforward class-based style and four-space indentation.
  There is no enforced formatter or type checker.
- Prefer explicit imports and existing local helpers. Avoid introducing a new
  framework or abstraction for a narrow change.
- Keep gameplay data in the owning system's dictionaries/lists and use `.get()` or
  `getattr()` defaults where backward compatibility or optional effects require it.
- Preserve Turkish UI copy and UTF-8 source encoding. PowerShell may display valid
  UTF-8 text as mojibake; do not rewrite strings merely because terminal output
  looks corrupted. New comments should be concise; identifiers remain English.
- Pygame drawing uses RGB tuples and immediate-mode rendering. Reuse fonts,
  surfaces, pools, and existing widgets in hot paths; do not allocate large
  surfaces or load images on every frame.
- Prefer `os.path` while touching current path code, matching the repository.
  Resolve new runtime paths relative to the project/module location if packaged
  execution must be supported.
- Do not modify `.exe`, `__pycache__/`, generated sprites, player saves, or
  `version.txt` unless the task explicitly requires those artifacts.
- Never delete `Boxhead.spec` or `Boxhead_Launcher.spec` in cleanup passes:
  both are required by the release workflow (`.github/workflows/release.yml`),
  which builds the game and the launcher from them on every `v*` tag.

## UI Theme And Layout (Mandatory)

`assets/ui/gothic/` is the visual source of truth — dark carved stone frames with
red gem rivets, matching button plates, portrait/item frames, and a skull crest.
`DESIGN.md` describes the older procedural theme; where the two disagree, the
gothic assets win. Every new or edited UI surface must match them.

### Use the theme, never hand-drawn chrome

- Buttons: `ui_elements.Button` (wraps `ui_theme.render_banner_button`, which
  uses `button_*.png`). Pick the colour from `ui_theme.COLORS`, never a raw RGB.
- Panels/tooltips: `ui_theme.draw_panel` (frame is drawn OUTSIDE the rect, for
  wide standalone panels) or `ui_theme.draw_inset_frame` (frame drawn INSIDE the
  rect, for cards/rows in a grid where the outer size is fixed).
- Item and portrait boxes: `item_slot.png`, `rarity_frame_*.png`,
  `portrait_frame.png` via `ui_nineslice.get` / `get_border`.
- Screen titles: `ui_theme.render_title` (serif + shadow), optionally flanked by
  `ui_elements.get_skull_crest`.
- A bare `pygame.draw.rect(..., border_radius=N)` as a panel, button, or slot is
  a theme violation. Flat rounded rectangles with saturated fills (the old
  "modern" look) are being removed, do not add more.

### Layout rules that have actually broken before

- **Allocate vertical space bottom-up.** Give fixed elements (footer strip,
  stat line, action row) their height first, then let the flexible element
  (portrait, list body) take the remainder. Sizing the image first and letting
  text flow after it is what pushed text out of the card in `ClassCard`.
- **Respect the frame's corners.** 9-slice `insets` equal the corner ornament
  size (40px for `panel_frame_small.png`), not the thickness of the straight
  edge. Use a smaller explicit `pad` for content, but keep text clear of the
  corners horizontally, or it renders on top of the gem rivets.
- **`draw_panel` grows the rect.** `ui_nineslice.outer_rect` puts the 52px
  gothic border outside the rect you pass. In a grid this overlaps neighbours —
  use `draw_inset_frame` there instead.
- **Fit text explicitly.** Use `render_fit`/`wrap_text` with the real available
  width; never assume a string fits. Check the widest real content (longest
  class name, 4-stat rows), not the first item.
- **Low-luminance accents are unreadable on the dark ground.** Run brand/class
  colours through `ui_theme.readable()` before using them for text or thin lines.
- **Draw the hovered/selected element last** so its glow and crest are not
  overlapped by neighbouring frames.

### Validation for UI changes

Render the screen offscreen and actually look at it before claiming it is done:

```powershell
$env:SDL_VIDEODRIVER='dummy'  # or pygame.HIDDEN on a real display
# build the scene with a stub manager, call scene.draw(), pygame.image.save(...)
```

Check both states (idle and hovered/selected) and the longest text content.
Alignment bugs in this project have consistently been found by looking at a
render, not by reading the code.

## Class And Evolution Balance (Mandatory)

Any new class or evolution/subclass MUST pass these checks before the change is
considered done. The goal: a new character must be viable but never strictly
better than existing ones ("broken").

### Power budget rule

Every meaningful strength must be paid for with an explicit weakness, matching
the existing pattern: sorcerer gets `elementDmgMult 0.6` but pays `-30% max HP`
and a slow `attack_cooldown 400`; ninja gets attack speed and dodge but the
weakest starting weapon; sniper gets `dmgMult 0.5` but `attack_cooldown 500`.
A class with only bonuses and no cost is rejected by definition.

### Numeric envelopes (derived from existing classes — stay inside them)

- `class_bases` in `logic/inventory_manager.py` is the source of truth. A new
  class MUST be added there, and values must stay within the current envelope:
  `dmgMult` bonus 0.2–0.5, `speed` 4.0–6.0, `attack_cooldown` 400–900 when
  overridden (default 350), `lifesteal` ≤ 0.20, `critChance` bonus ≤ 0.2,
  `dodgeChance` bonus ≤ 0.25. Exceeding any of these requires a compensating
  malus (HP/speed/cooldown) and a written justification in the PR/commit.
- Starting weapons (`init_class_specialization` in `entities/player.py`):
  `physDmg` 8–18, rarity `Normal` or `Magic` only. Estimate wave-1 effective
  DPS as `damage / (attack_cooldown in seconds)` including class `dmgMult`;
  it must land within ±25% of the warrior baseline (12 phys × 1.2 / 0.35s).
  Utility classes (engineer, beastmaster) may go below the band, never above.
- Evolutions (`Player.EVOLUTIONS`): each class gets exactly two paths with
  opposite trade-offs (one offensive/fragile, one defensive/sustained — see
  gladiator vs paladin). `dmgMult` ≥ 0.8 requires a negative `max_hp_delta`;
  pure stat additions without a passive identity are not enough.

### Required touchpoints checklist

A new class is a shared string contract. All of these must be updated together:
`class_bases` (inventory_manager), starting weapon + `reinit_specialization`
(player.py), a `<class>_logic.py` file in `entities/`, `class_list` and
`detailed_desc` (class_select_scene.py), `passives` dict (game_scene.py), two
`EVOLUTIONS` entries (player.py), class weapon tiers in `logic/item_system.py`
bases, and save/load compatibility (old saves without the class must still load).

### Required validation before merge

1. Syntax + import smoke test (see Validation section).
2. Manual playtest: waves 1–5 on Normal with the new class; confirm it can
   clear wave 5 but does not trivialize it (no AFK-clearing wave 5, not dead
   on wave 1 with reasonable play). If a display is unavailable, state this
   explicitly and list the numeric checks performed instead.
3. Side-by-side DPS/EHP comparison table (new class vs warrior and sniper at
   wave 1) included in the summary of the change. Effective HP = max_hp
   adjusted by armor/dodge/ES bonuses.
4. Verify no stacking loophole: the class bonus combined with its starting
   weapon and its two evolutions must not multiply into more than ~2× the
   equivalent warrior build at the same investment level.

## Validation

Every Python change must at least pass:

```powershell
$env:PYTHONUTF8='1'; python check_all_syntax.py
```

Also run the import smoke test for changes to imports or module boundaries. For
gameplay/UI changes, manually exercise the affected flow in `python main.py` when a
display is available: enter the relevant scene, test keyboard and mouse paths,
and verify pause/resume, camera positioning, and save compatibility as applicable.
There is no automated behavioral coverage, so state exactly which manual checks
were and were not performed.

When adding pure logic, prefer adding focused `unittest` coverage that avoids
opening a display. For Pygame-dependent tests, set `SDL_VIDEODRIVER=dummy` before
initialization and keep tests independent of the user's `saves/` directory.

## Fixed Bugs

- **Bug 9 (Wave Events):** Fixed wave events so that properties like `fast_enemies`, `elite_rain`, and `no_shooting` correctly modify enemy stats by adding logic to `_apply_global_modifiers` in `game_logic.py`.
- **Bug 10 (Quest Tracking):** Fixed disconnected quest tracking by hooking up `quest_system.track()` for `reach_level` (in `player.py`) and `earn_gold` (in `ground_item.py`), and ensuring progress is correctly saved to `meta.json`.
- **Bug 11 (Game Over Stats):** Added a global `stats` dictionary to `GameLogic` tracking `total_damage_dealt`, `total_damage_taken`, and `enemies_killed`, and synced `game_scene.py`'s display to correctly render these.
- **Bug 12 (Combo Speed Override):** Fixed the combo speed logic by converting the kill streak speed bonus to `_base_speed_mod` in `game_logic.py`, ensuring `status_effects.py` applies slow/haste modifiers multiplicatively instead of overriding the bonus outright.
- **Poison Stacking:** Fixed `StatusEffectManager.add_effect()` so that Poison DPS stacks additively instead of just refreshing duration.

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and automated releases.

### Workflows

- `.github/workflows/ci.yml`: Runs on push/PR to `main`. Performs syntax check,
  headless import smoke test, and unit tests on `windows-latest`.
- `.github/workflows/release.yml`: Triggered by `v*` tag push. Validates version
  consistency, builds with PyInstaller, packages as `Boxhead-VERSION-win64.zip`,
  generates SHA-256 checksum and `update.json` manifest, and publishes a GitHub
  Release with all assets. Only the release job has `contents: write` permission.

### Version System

`version.txt` is the single source of truth. `logic/version.py` reads it at runtime
(supports both source and PyInstaller-bundled paths). `scenes/menu_scene.py` displays
the version dynamically. Release workflow validates that the tag matches `version.txt`.

### Patch Notes (Auto-Generated)

`data/patch_notes.json` is auto-generated from git history — never edit it by
hand. `tools/generate_patch_notes.py` walks the `v*` tags, categorizes commit
subjects by conventional-commit prefix (`feat` → Yeni Özellikler, `fix` → Hata
Düzeltmeleri, `balance` → Denge, `perf`/`refactor` → İyileştirmeler, everything
else → Diğer), and writes the newest version first. Commits after the last tag
appear under a "Yayınlanmamış" (unreleased) heading.

Regenerate and commit BEFORE tagging a release so the packaged notes are
current:

```powershell
$env:PYTHONUTF8='1'; python tools/generate_patch_notes.py
```

Consumers: the in-game main menu ("YENİLİKLER" button, `PATCH_NOTES` state in
`scenes/menu_scene.py`, loaded via `logic/data_loader.py`) and the launcher
("YENİLİKLER (PATCH NOTES)" button in `launcher/main.py`, which reads
`data/patch_notes.json` from the install directory). The release workflow copies
`data/patch_notes.json` into the release ZIP so the launcher can read it on
installed copies; the game reads the copy bundled inside `Boxhead.exe`.

Write commit subjects with conventional prefixes (`feat:`, `fix:`, `balance:`,
...) — they become user-facing patch notes verbatim. "Release vX.Y.Z", merge
commits, and patch-notes regeneration commits are excluded automatically.

### Launcher

`launcher/` contains a Tkinter-based auto-update launcher:
- `launcher/config.py`: GitHub repo settings, paths, and constants.
- `launcher/updater.py`: Core update logic (no GUI). Handles SemVer comparison,
  SHA-256 verification, ZIP path traversal protection, staging/backup/rollback.
- `launcher/main.py`: Tkinter GUI with progress bar, status, update and play buttons.

The launcher never touches `saves/`. It uses `.part` temp files, validates checksums,
and rolls back on failure.

### Tests

`tests/test_version.py`: SemVer parsing and comparison.
`tests/test_updater.py`: Checksums, ZIP traversal detection, update/rollback,
mocked GitHub API calls, saves preservation.

Run: `python -m pytest tests/ -v`
