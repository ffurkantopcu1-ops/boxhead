# -*- coding: utf-8 -*-
"""Prosedürel arena haritası regresyon testleri.

Kapsam:
  * Determinizm — aynı seed her zaman aynı arenayı üretmeli (kayıt/yükleme
    sonrası arena değişirse oyuncu "harita bozuldu" olarak görür).
  * Sözleşme — logic/tilemap.py'nin ürettiği her dekor türünün
    tile_renderer'da bir çizim dalı olmalı; olmayan tür sessizce BOŞ bir
    yüzey döndürür ve zeminde hiç fark edilmez.
  * Biyom paleti — BiomeSystem'deki her biyomun zemin renkleri tam olmalı.
  * Kayıt round-trip'i — map_seed kayda yazılıp geri okunmalı, eski
    kayıtlarda (alan yok) çökmemeli.

Pygame penceresi açmadan çalışır (SDL dummy)."""
import os
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
pygame.init()
pygame.display.set_mode((320, 240))

import tile_renderer
from logic.biome_system import BiomeSystem
from logic.tilemap import BIOME_DECOR, VARIANT_COUNT, TileMap

BIOME_IDS = tuple(BiomeSystem.BIOMES)
SAMPLE = [(tx, ty) for tx in range(0, 40, 3) for ty in range(0, 40, 3)]


class TestDeterminism(unittest.TestCase):
    def _snapshot(self, tmap):
        out = []
        for tx, ty in SAMPLE:
            out.append((tmap.variant_at(tx, ty),
                        tmap.decor_at(tx, ty, "forest"),
                        tmap.landmark_at(tx, ty, "forest")))
        return out

    def test_same_seed_same_map(self):
        # Kayıt yalnızca seed'i taşıyor; aynı seed farklı arena üretirse
        # yüklenen oyun başka bir haritada açılır.
        self.assertEqual(self._snapshot(TileMap(1234)), self._snapshot(TileMap(1234)))

    def test_different_seed_differs(self):
        self.assertNotEqual(self._snapshot(TileMap(1234)), self._snapshot(TileMap(9876)))

    def test_variant_within_range(self):
        tmap = TileMap(42)
        for tx, ty in SAMPLE:
            v = tmap.variant_at(tx, ty)
            self.assertIsInstance(v, int)
            self.assertGreaterEqual(v, 0)
            self.assertLess(v, VARIANT_COUNT)

    def test_border_marks_arena_edges(self):
        # Oyuncu 50..4950'ye kilitli; sınır bandı bunun görsel karşılığı.
        tmap = TileMap(7, world_size=5000)
        n = tmap.tiles_across - 1
        self.assertTrue(tmap.is_border(0, 5))
        self.assertTrue(tmap.is_border(n, 5))
        self.assertTrue(tmap.is_border(5, 0))
        self.assertFalse(tmap.is_border(n // 2, n // 2))


class TestRenderContract(unittest.TestCase):
    def setUp(self):
        tile_renderer.clear_cache()

    def test_every_biome_has_full_palette(self):
        for bid, b in BiomeSystem.BIOMES.items():
            for key in ("floor_color_1", "floor_color_2", "grid_line_color", "accent_color"):
                self.assertIn(key, b, f"{bid} biyomunda {key} eksik")
                self.assertEqual(len(b[key]), 3, f"{bid}.{key} RGB üçlüsü olmalı")
            self.assertIn(bid, BIOME_DECOR, f"{bid} için dekor listesi yok")

    def test_every_decor_kind_draws_something(self):
        # Bilinmeyen bir tür _make_decor'da hiçbir dala girmez ve tamamen
        # saydam bir yüzey döner — zeminde fark edilmez, sessizce kaybolur.
        for bid in BIOME_IDS:
            for kind in BIOME_DECOR[bid]:
                for surf in tile_renderer._decor_for(bid, kind):
                    self.assertGreater(
                        surf.get_bounding_rect().width, 0,
                        f"{bid}/{kind} dekoru boş çiziliyor (çizim dalı yok?)")

    def test_tiles_and_border_build_for_every_biome(self):
        for bid in BIOME_IDS:
            tiles = tile_renderer._tiles_for(bid)
            self.assertEqual(len(tiles), VARIANT_COUNT)
            self.assertEqual(tiles[0].get_size(), (128, 128))
            self.assertEqual(tile_renderer._border_for(bid).get_size(), (128, 128))

    def test_draw_floor_covers_surface(self):
        # Zemin ayrıca fill() edilmiyor; karolar tüm görüş alanını kaplamazsa
        # önceki karenin artıkları ekranda kalır.
        tmap = TileMap(3)
        surf = pygame.Surface((640, 480)).convert()
        surf.fill((255, 0, 255))
        tile_renderer.draw_floor(surf, 1000, 1000, 640, 480, "forest", tmap)
        for pos in ((0, 0), (639, 0), (0, 479), (639, 479), (320, 240)):
            self.assertNotEqual(surf.get_at(pos)[:3], (255, 0, 255),
                                f"{pos} boyanmadı — zeminde delik var")


class TestSaveRoundTrip(unittest.TestCase):
    """Gerçek kayıt dosyalarına dokunmaz: kendine ait geçici slotu kullanır
    ve sonunda siler (bkz. AGENTS.md — saves/ altındaki dosyalar korunur)."""

    SLOT = "__pytest_tilemap_tmp__"

    def tearDown(self):
        path = os.path.join("saves", f"{self.SLOT}.json")
        if os.path.exists(path):
            os.remove(path)

    def _fresh_logic(self):
        from logic.game_logic import GameLogic
        return GameLogic(None, 1920, 1080, "warrior")

    def test_seed_survives_save_and_load(self):
        from logic.save_manager import SaveManager
        src = self._fresh_logic()
        src.wave["level"] = 14
        SaveManager.save_game(src, self.SLOT)

        dst = self._fresh_logic()
        self.assertNotEqual(dst.map_seed, src.map_seed, "yeni oyun aynı seed'i aldı")
        SaveManager.load_game(dst, self.SLOT)
        self.assertEqual(dst.map_seed, src.map_seed)
        self.assertEqual(dst.tilemap.seed, src.tilemap.seed)

    def test_biome_synced_to_loaded_wave(self):
        from logic.save_manager import SaveManager
        src = self._fresh_logic()
        src.wave["level"] = 25          # BiomeSystem'e göre "ice" aralığı
        SaveManager.save_game(src, self.SLOT)

        dst = self._fresh_logic()
        SaveManager.load_game(dst, self.SLOT)
        expected, _ = dst.biome_system.get_biome_for_wave(dst.wave["level"])
        self.assertEqual(dst.wave["biome"], expected)
        self.assertEqual(dst.biome_system.current_biome_id, expected)

    def test_old_save_without_seed_still_loads(self):
        import json
        from logic.save_manager import SaveManager
        src = self._fresh_logic()
        SaveManager.save_game(src, self.SLOT)

        path = os.path.join("saves", f"{self.SLOT}.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        data["wave"].pop("map_seed", None)      # map_seed'den önceki kayıt
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        dst = self._fresh_logic()
        before = dst.map_seed
        self.assertTrue(SaveManager.load_game(dst, self.SLOT) is not False)
        self.assertEqual(dst.map_seed, before, "eski kayıt mevcut seed'i bozmamalı")


if __name__ == "__main__":
    unittest.main()
