import math
import pygame
import random

class Bomber:
    def __init__(self):
        self.attack_cooldown = 1500
        
    def execute_attack(self, player, game):
        # Bomber: Zehirli Şişe Fırlat
        # Normal atıştan daha büyük alan hasarı (AOE)
        orig_aoe = player.stats.get("aoe", 1.0)
        player.stats["aoe"] = orig_aoe * 1.5 
        
        # Bombacıya özel: Ranged shoot but with is_bomb property
        player.shoot(game, is_bomb=True)
        
        player.stats["aoe"] = orig_aoe

    def update(self, dt, player, game):
        pass
        
    def draw_visuals(self, screen, camera_x, camera_y):
        pass
