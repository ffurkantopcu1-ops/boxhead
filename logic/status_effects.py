import pygame
import math
import random

class StatusEffect:
    def __init__(self, name, duration, dps=0, speed_mult=1.0, disables_skills=False, disables_movement=False, color=(255, 255, 255)):
        self.name = name
        self.duration = duration
        self.timer = duration
        self.dps = dps
        self.speed_mult = speed_mult
        self.disables_skills = disables_skills
        self.disables_movement = disables_movement
        self.color = color
        self.active = True
        self.vis_accum = 0 # For damage text accumulation
        self.tick_timer = 0.5 # New: Show damage text every 0.5 seconds
        # Yığın (stack) bekleme sayacı: aynı kaynağın her karede yığın
        # eklemesini engeller (F5)
        self.stack_cd = 0.0

    def update(self, dt, target, game):
        self.timer -= dt
        if self.stack_cd > 0:
            self.stack_cd -= dt
        if self.timer <= 0:
            self.active = False
            return

        # Apply DPS
        if self.dps > 0:
            damage = self.dps * dt
            is_enemy = hasattr(target, 'type') and target.type != 'player' and hasattr(target, 'take_damage')
            if is_enemy:
                # DoT zırh/kalkan formülünden geçsin diye take_damage üzerinden akar;
                # take_damage ölümde kill_enemy'yi zaten çağırır (çift çağrı olmasın)
                target.take_damage(damage, game, is_dot=True, from_player=True)
            elif hasattr(target, 'hp'):
                target.hp -= damage

            if hasattr(target, 'hp'):
                self.vis_accum += damage
                self.tick_timer -= dt
                if self.tick_timer <= 0:
                    accum_int = int(self.vis_accum)
                    if accum_int >= 1:
                        # Show damage text if it's an enemy or if it's significant for player
                        if is_enemy:
                            game.add_event("damage_text", target.x, target.y, value=accum_int, color=self.color, timer=0.5)
                        self.vis_accum -= accum_int
                    self.tick_timer = 0.5

            # Check for death (oyuncu olmayan ve take_damage'i olmayan hedefler için)
            if not is_enemy and hasattr(target, 'hp') and target.hp <= 0:
                if hasattr(target, 'dead'):
                    target.dead = True
                    if hasattr(game, 'kill_enemy'):
                        game.kill_enemy(target)

# Zehir yığınları arasındaki minimum süre. Zehir bulutu her karede
# apply_dot çağırdığı için 60 FPS'te 4 karede (0.067 sn) tavana ulaşıyor,
# "yığın" mekaniği sabit 4x çarpana dönüşüyordu (F5).
POISON_STACK_INTERVAL = 0.5


class StatusEffectManager:
    def __init__(self):
        self.effects = [] # List of active effects on a specific entity

    def add_effect(self, effect):
        # Refresh duration if same effect already exists
        for existing in self.effects:
            if existing.name == effect.name:
                if existing.name == "Poison":
                    # Additive yığın en fazla 4 katına çıkabilir; sınırsız yığın
                    # saldırı hızıyla karesel DPS büyümesi yaratıyordu (F1).
                    # Yığın artışı ZAMANA bağlı: iki yığın arasında en az
                    # POISON_STACK_INTERVAL saniye geçmeli (F5).
                    if existing.stack_cd <= 0:
                        existing.dps = min(existing.dps + effect.dps, effect.dps * 4)
                        existing.stack_cd = POISON_STACK_INTERVAL
                    else:
                        existing.dps = max(existing.dps, effect.dps)
                else:
                    existing.dps = max(existing.dps, effect.dps)
                existing.timer = max(existing.timer, effect.duration)
                existing.speed_mult = min(existing.speed_mult, effect.speed_mult)
                return
        self.effects.append(effect)

    def update(self, dt, target, game):
        # Update speed_mod and other flags
        target.speed_mod = getattr(target, '_base_speed_mod', 1.0)
        target.is_silenced = False
        target.is_stunned = False

        for eff in self.effects[:]:
            eff.update(dt, target, game)
            if not eff.active:
                self.effects.remove(eff)
                continue
            
            # Apply multipliers/flags
            target.speed_mod *= eff.speed_mult
            if eff.disables_skills:
                target.is_silenced = True
            if eff.disables_movement:
                target.is_stunned = True
                target.speed_mod = 0

    def draw_icons(self, screen, x, y, radius):
        # Draw small dots or icons above the target
        offset_x = -((len(self.effects) - 1) * 6)
        for i, eff in enumerate(self.effects):
            pygame.draw.circle(screen, eff.color, (int(x + offset_x + i * 12), int(y - radius - 25)), 4)
            # Pulse effect
            if int(pygame.time.get_ticks() / 200) % 2 == 0:
                pygame.draw.circle(screen, (255, 255, 255), (int(x + offset_x + i * 12), int(y - radius - 25)), 5, 1)

def apply_burn(manager, duration=3.0, dps=15.0):
    manager.add_effect(StatusEffect("Burn", duration, dps=dps, color=(231, 76, 60)))

def apply_slow(manager, duration=3.0, mult=0.5, name="Slow"):
    # name: farkli kaynaklarin (camur/buz/ag) birbirini ezmemesi icin ayrilabilir
    manager.add_effect(StatusEffect(name, duration, speed_mult=mult, color=(52, 152, 219)))

def apply_silence(manager, duration=3.0):
    manager.add_effect(StatusEffect("Silence", duration, disables_skills=True, color=(149, 165, 166)))

def apply_stun(manager, duration=1.0):
    manager.add_effect(StatusEffect("Stun", duration, disables_movement=True, disables_skills=True, color=(241, 196, 15)))
