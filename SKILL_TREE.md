# SKILL_TREE.md — Node-based skill tree (design)

A Path-of-Exile-style **pathed skill tree** that replaces the old flat 56-skill
buy grid. This doc records the decisions and the contract so the data, engine, UI,
and save format stay in sync. Turkish is the UI language; identifiers are English.

## Decisions (locked)

- **Pathing, deterministic.** A node can be allocated only if it is a class
  **start node** or is connected to a node you already own. The tree layout never
  shuffles. Per-run variety comes from *which lane you commit to*, not RNG.
- **Run-scoped.** Allocation lives in the run's save data (like `p.skills`), not in
  `meta.json`. It resets each run. (Meta progression stays in the Crystal Shop.)
- **Currency: existing Skill Points (`p.skill_points`).** +1 per level-up
  (`entities/player.py` `_apply_level_up_stats`), 1 SP per node. **No new currency.**
  The old flat grid already spent SP this way; the tree just gates spending behind
  pathing. Every allocated node returns 1 SP on a full refund.
- **Cards are untouched.** Cards are *wave-paced* (every 3rd wave,
  `logic/game_logic.py`), a random layer. SP/tree is *level-paced*. They already
  coexist; the tree changes nothing about cards.
- **Structure: hub + class arms.** One shared **core** hub every class can path,
  plus one small themed **arm** per class (all 9 classes, including bomber). Each
  class **starts at the mouth of its own arm** (start node auto-allocated, 0 SP).
  From the start you branch outward into class-specific power or inward through a
  core gate into the shared core.
- **Scarcity.** A normal run (~level 20–30 → ~20–30 SP) affords roughly a quarter
  of the graph, so you must pick a direction. Pathing depth — not per-node cost —
  is the gate; every node costs 1 SP.

### Why this isn't just a PoE clone
PoE's tree is permanent and XP-fed; ours is **run-scoped and level-fed**, a
survival tree that grows as you push deeper and resets on death. PoE's variety
comes from loot/gems; ours pairs a deterministic backbone with the game's existing
**random wave cards**. And it fits one screen — no giant pannable web.

## Node schema (`data/skill_tree.json`)

A flat JSON list of node objects. Edges are undirected and declared once via
`connects` (id references); the engine builds symmetric adjacency.

```jsonc
{
  "id": "w_bulwark",           // unique string id (save contract — never rename)
  "name": "🛡️ Siper",          // Turkish display name
  "desc": "+80 Max Can, +12 Zırh",
  "arm": "warrior",            // "core" or a class id; drives layout + theming
  "type": "minor",             // "minor" | "notable" | "keystone" | "start"
  "start": false,              // true for the one auto-allocated node per class
  "stats": { "max_hp": 80, "armor": 12 },  // summed into recalculate_stats
  "flags": {},                 // optional non-stat effects (keystones), see below
  "connects": ["w_hide", "core_gate_armor"],
  "pos": [220, 400]            // layout coords on the ~1000x700 tree canvas
}
```

- **`stats`** keys MUST be keys `InventoryManager.recalculate_stats` already sums
  (e.g. `max_hp`, `dmgMult`, `armor`, `speed`, `critChance`, `attack_speed_bonus`,
  `lifesteal`, `physDmgFlat`, `meleeRangeFlat`, `aoe_bonus`, `dotDmgMult`,
  `elementDmgMult`, `turretDmg/Rate/Limit`, `minionDamage/Count`, `pierce`,
  `bounce`, `projectileCount`). Downsides use the existing `max_hp_pct` pool
  (a `-15` there = −15% max HP), matching the card system.
- **`flags`** carry keystone effects that aren't a stat sum — they set the same
  player attributes cards already use (e.g. `berserker_rage`, `execute_threshold`).
  Applying flags is centralized so keystones and cards can't double-define one.
- **`start`** node: `type` = `"start"`, `stats` empty, auto-allocated at run start,
  costs 0 SP, never refunded.

### Node types (budget guidance)
- **minor** — one modest stat, on the scale of a single old skill rank
  (e.g. `max_hp 40`, `dmgMult 0.10`, `armor 8`).
- **notable** — a themed bump worth ~2–3 minors, may combine two stats.
- **keystone** — build-defining: a large bonus **paired with a real downside**
  (matches the class-balance rule in `AGENTS.md`). Gated deep in an arm.

## Topology

- **Core** (`arm: "core"`): a central notable `core_heart` ringed by generic
  **gate** minors (`core_gate_*`, one per class arm), gates linked in a cycle and
  each to the heart, plus a couple of deeper core notables. Every class arm
  attaches to exactly one gate, so from any start you can walk the whole core —
  scarcity, not walls, keeps builds distinct.
- **Arms** (`arm: <class_id>`): `start_<class>` connects to (a) the arm's first
  specialty node and (b) one themed core gate. Each arm has ~6 nodes: minors, one
  notable, and — for some classes — a keystone at the tip.

## Engine (`logic/skill_tree.py`)

`SkillTree` owns the data and rules; it holds no per-player state (like
`CrystalShop`). Per-player state is a set of allocated node ids on the player.

- `is_allocatable(node_id, allocated)` — true if node is a start node, or shares an
  edge with any id in `allocated`, and isn't already allocated.
- `allocate(player, node_id)` — validates SP + pathing, adds id, spends 1 SP.
- `refund_all(player)` — clears non-start nodes, returns SP (paid via gold at the
  UI layer, mirroring the old reset).
- `resolve_stats(allocated)` → summed `{stat: total}` dict for `recalculate_stats`.
- `apply_flags(player, allocated)` — sets keystone flag attributes.
- `start_nodes_for(class_id)` — ids auto-allocated on new run / class change.
- Module-load validation (like `card_system`/`crystal_shop`): unique ids, every
  `connects` target exists, exactly one `start` per class, each arm reaches a core
  gate.

## Integration points

- **`entities/player.py`** — `self.allocated_nodes: set[str]`, seeded with
  `SkillTree.start_nodes_for(class_id)` in `__init__`/`reinit_specialization`.
  The old `self.skills` list and `buy_skill`/`reset` are retired in favor of the
  tree (old-save `skills` levels are migrated once — see below).
- **`logic/inventory_manager.py`** — `recalculate_stats` gains one summation of
  `SkillTree.resolve_stats(player.allocated_nodes)` into `totals`, right beside the
  existing `skills` / `skills_permanent` loops. Zero new stat-application code for
  minor/notable nodes.
- **`logic/save_manager.py`** — persist `allocated_nodes` in the `player` block
  (run save, not meta). Old saves without it: seed start nodes and, one time,
  convert leftover `skills` levels into refunded SP so nothing is lost.
- **`scenes/game_scene.py`** — the SKILLS tab becomes the tree view: gem-slot nodes
  via `ui_theme`, connection lines, states (allocated / allocatable / locked),
  click to allocate, keep the SP counter and gold-cost reset. Pauses sim like the
  existing overlays. Render-validated offscreen per `AGENTS.md`.

## Validation checklist

1. `$env:PYTHONUTF8='1'; python check_all_syntax.py`
2. `python -m pytest tests/test_skill_tree.py -v` (headless): pathing rules, SP
   accounting, stat resolution, data integrity, save round-trip.
3. Balance: no single reachable path within a normal run's SP budget should exceed
   ~2× the warrior baseline for the same investment (the `AGENTS.md` envelope).
4. UI render check: allocated/allocatable/locked states and longest node name.
