# MASTER PROMPT: Pygame Bullet Hell Boss System Architecture

**To the AI Assistant (Gemini Flash):**
You are an expert Game Developer specializing in Python and Pygame. Your task is to implement a robust, high-performance Boss System for a top-down shooter game (similar to Boxhead / Realm of the Mad God). 
Read this architecture document carefully. Follow the exact data structures, performance optimization techniques, and state machine designs outlined below. Your goal is to write clean, modular, and 60 FPS-capable code.

---

## 1. PERFORMANCE OPTIMIZATION (Bullet Hell Core)
To handle hundreds of bullets on screen without dropping below 60 FPS in Pygame:
*   **Object Pooling (Zorunlu):** Do not use `list.append()` and `list.remove()` or `del` during gameplay. Pre-allocate a `ProjectilePool` array of 2000+ objects at startup. Use an `is_active` boolean flag to reuse objects.
*   **Vectorial Math (Önceden Hesaplama):** Avoid calling `math.sin` and `math.cos` every frame for moving bullets. When firing a bullet, calculate its movement vector ONCE: `velocity = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * speed`. In the update loop, simply do `pos += velocity * dt`.
*   **Draw Optimization:** Use `pygame.Surface.blits()` for batch rendering all active bullets of the same type in a single call, or use simple geometric shapes (`pygame.draw.circle`) if sprites are too heavy.

## 2. DATA STRUCTURE: Boss Definition JSON
The boss system must be highly data-driven. Create a parser that reads boss configurations from a dictionary or JSON file.

```json
{
  "id": "abyssal_lord",
  "name": "Lord of the Abyss",
  "max_hp": 15000,
  "phases": [
    {
      "phase_id": 1,
      "name": "Labyrinth of Fire",
      "type": "survival",
      "trigger_hp_percent": 100,
      "duration_ms": 12000,
      "invulnerable": true,
      "attacks": [
        {
          "pattern": "maze_wall",
          "projectile_id": "fire_orb",
          "cooldown_ms": 2000,
          "speed": 50,
          "damage": 30,
          "status_effect": "burn"
        }
      ]
    },
    {
      "phase_id": 2,
      "name": "Static Silence",
      "type": "damage",
      "trigger_hp_percent": 75,
      "duration_ms": 0, 
      "invulnerable": false,
      "attacks": [
        {
          "pattern": "screen_wipe",
          "projectile_id": "void_wave",
          "cooldown_ms": 3000,
          "speed": 400,
          "damage": 50,
          "status_effect": "silence"
        }
      ],
      "safe_spots": [
        {"radius": 80, "lifetime_ms": 3000, "pattern": "random_player_vicinity"}
      ]
    }
  ]
}
```

## 3. FINITE STATE MACHINE (FSM) ARCHITECTURE
Implement a modular State Machine for the Boss. 

```python
class BossPhase:
    def enter(self, boss): pass
    def update(self, boss, dt): pass
    def exit(self, boss): pass

class SurvivalPhase(BossPhase):
    # Handles invulnerability, timer-based transitions, bullet hell patterns
    pass

class DamagePhase(BossPhase):
    # Handles vulnerability, safe spot generation, HP-based transitions
    pass
```

## 4. PHASE DESIGNS & MECHANICS
You must implement the logic for the following creative phases:

### Phase 1: "Labyrinth of Fire" (Survival Phase)
*   **Mechanic:** Boss becomes completely invulnerable. Instead of aiming at the player, the boss shoots slow-moving, dense lines of bullets that form a maze.
*   **Player Goal:** The player cannot damage the boss and must simply navigate the moving maze until the phase timer runs out.
*   **Status Effect:** Touching walls applies `Burn` (DoT) and `Slow`.

### Phase 2: "Static Silence" (Damage Phase)
*   **Mechanic:** Boss teleports to the center and becomes vulnerable. It fires massive, high-speed radial waves ("screen wipes") that cover the whole map.
*   **Safe Spots:** Just before a wave fires, glowing green "Safe Spot" circles spawn on the map. The player must stand inside them to avoid the wave damage.
*   **Status Effect:** Getting hit outside the safe spot applies `Silence` (Player cannot shoot or use skills for 3 seconds).

### Phase 3: "Orbital Chaos" (Enrage / Hybrid Phase)
*   **Mechanic:** Triggers at 20% HP. Bullets spawn and orbit around the boss at varying distances, expanding and contracting like a breathing lung. The player must weave through the orbits to deal final damage.

## 5. VISUAL FEEDBACK & TELEGRAPHING
Do not leave the player guessing. Implement visual telegraphing:
*   **Telegraphing (Saldırı Uyarısı):** 0.5 to 1.5 seconds before a heavy attack, draw a translucent red polygon or line on the `pygame` surface indicating the hit zone.
*   **Invulnerability Cue:** When the boss is in a Survival phase, draw a pulsing semi-transparent blue/white shield circle around the boss sprite.
*   **Safe Spot Indicators:** Draw pulsating green circles on the floor (`pygame.SRCALPHA` surface).
*   **Status Effects:** Tint the player's sprite or draw a small icon above them (e.g., Blue tint for Slow, Gray tint for Silence).

## 6. YOUR TASK (Action Items)
Based on this architecture, please write the Python code for:
1.  The `ProjectilePool` and `StatusEffect` manager.
2.  The `BossFSM` class and the Phase logic.
3.  The math/logic functions for the `spiral`, `maze_wall`, and `screen_wipe` attack patterns.
4.  The Pygame rendering functions for Telegraphs and Safe Spots.

Provide the code in clean, easily copy-pasteable blocks with brief explanations.
