"""Kuşanılabilir her silah hasar verebilmeli — "tuzak eşya" olmamalı.

NEDEN: Taret, R tuşuna bir yetenek olarak taşınınca taret kiti "vurmayan
ekipman" oldu. Ama:
  - Mühendis hâlâ taret kitiyle başlıyordu -> sınıf hiç hasar veremiyordu
  - Yerden düşen 4 taret kiti tier'i de kuşanılınca saldırıyı öldürüyordu

Oyuncunun eline geçen bir silahın onu SİLAHSIZ bırakması, eksik içerikten
kötüdür: oyuncu sebebini anlamaz, oyunu bozuk sanır.

Bu test her sınıfın başlangıç silahıyla ve her silah tabanıyla hasar
verilebildiğini doğrular.
"""
import os
import random
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from logic.game_logic import GameLogic
from logic.item_system import ItemSystem
from logic.inventory_manager import InventoryManager


class _Scene:
    zoom_level = 1.0
    camera_x = 0.0
    camera_y = 0.0


class _Manager:
    def __init__(self):
        self.current_scene = _Scene()

    def go_to(self, *a, **k):
        pass


def _attack_result(class_id, weapon=None, swings=15):
    """(verilen hasar, taret kuruldu mu) döndürür."""
    random.seed(11)
    game = GameLogic(_Manager(), 1280, 720, class_id=class_id)
    player = game.players["p1"]
    player.game = game

    if weapon is not None:
        item = dict(weapon)
        item.setdefault("rarity", "Normal")
        item.setdefault("prefixes", [])
        item.setdefault("suffixes", [])
        player.add_item(item)
        player.inv_manager.equip(item)

    game.spawn_enemy()
    enemy = game.enemies[-1]
    enemy.x, enemy.y = player.x + 70, player.y
    enemy.hp = enemy.max_hp = 10 ** 9
    game.update_grid()
    player.facing_angle = 0.0
    player.aim_x, player.aim_y = enemy.x, enemy.y

    hp0 = enemy.hp
    turrets0 = len(game.turrets)
    for _ in range(swings):
        player.attack_timer = 0
        player.specialization.execute_attack(player, game)
        # Mermi/mayın hedefe ulaşsın, DoT işlesin
        for _ in range(40):
            for proj in list(game.projectiles):
                proj.update(1 / 60.0, game)
            game.projectiles = [p for p in game.projectiles if not p.dead]
            for cloud in list(game.clouds):
                cloud.arm_timer = 0
                cloud.update(1 / 60.0, game)
            game.clouds = [c for c in game.clouds if not c.dead]
            enemy.update(1 / 60.0, game)

    return hp0 - enemy.hp, len(game.turrets) > turrets0


class TestWeaponDamage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280, 720))

    def test_her_sinif_baslangic_silahiyla_hasar_verebiliyor(self):
        for class_id in sorted(InventoryManager.CLASS_IDS):
            with self.subTest(sinif=class_id):
                dealt, turret = _attack_result(class_id)
                self.assertTrue(
                    dealt > 0 or turret,
                    f"{class_id}: başlangıç silahıyla hiç hasar veremiyor")

    def test_hicbir_silah_tabani_tuzak_degil(self):
        weapons = [b for b in ItemSystem().bases if b.get('type') == 'weapon']
        self.assertTrue(weapons, "silah tabanı bulunamadı")
        for weapon in weapons:
            wclass = weapon.get('weaponClass')
            if wclass not in InventoryManager.CLASS_IDS:
                continue        # sınıfsız/komuta silahları ayrı davranır
            with self.subTest(silah=weapon['name']):
                dealt, turret = _attack_result(wclass, weapon)
                self.assertTrue(
                    dealt > 0 or turret,
                    f"{weapon['name']}: kuşanılınca hasar veremiyor (tuzak eşya)")


if __name__ == '__main__':
    unittest.main()
