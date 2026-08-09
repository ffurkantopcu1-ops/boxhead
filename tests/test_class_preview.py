"""Sınıf seçim ekranındaki statlar gerçekten taban değerlerle uyuşuyor mu?

NEDEN: Ekrandaki statlar uzun süre ELLE yazılmıştı. Sınıf tabanlarına global
%20 hız zammı yapıldığında ekran güncellenmedi ve 9 sınıfın 8'inde gösterilen
hız gerçeğin 1/1.2'si kaldı (ör. Warrior 5.0 gösteriliyordu, gerçek 6.0).
Oyuncu build kararını gördüğü sayıya göre veriyor; yanlış sayı, yanlış karar.

Bu test gösterimin türetilmiş kaldığını garanti eder: biri tekrar elle değer
yazarsa veya taban değişip gösterim geride kalırsa burada patlar.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.inventory_manager import InventoryManager


class TestClassPreview(unittest.TestCase):

    def test_her_sinifin_onizlemesi_var(self):
        for class_id in InventoryManager.CLASS_IDS:
            with self.subTest(sinif=class_id):
                preview = InventoryManager.get_class_preview(class_id)
                self.assertTrue(preview, f"{class_id}: önizleme boş")

    def test_gosterilen_hiz_taban_hizla_ayni(self):
        """En kritik alan: hız. 8/9 sınıfta yanlış olan buydu."""
        for class_id, base in InventoryManager.CLASS_BASES.items():
            if "speed" not in base:
                continue
            with self.subTest(sinif=class_id):
                shown = InventoryManager.get_class_preview(class_id, limit=99).get("Hız")
                self.assertIsNotNone(shown, f"{class_id}: hız gösterilmiyor")
                self.assertAlmostEqual(
                    float(shown), base["speed"], places=1,
                    msg=f"{class_id}: ekranda {shown}, taban {base['speed']}")

    def test_yuzdesel_statlar_tabanla_ayni(self):
        """HP/hasar/alan gibi çarpan statları da doğru yüzdeye çevrilmeli."""
        checks = [("max_hp_mult", "HP"), ("dmgMult", "Hasar"),
                  ("aoe", "Alan"), ("dotDmgMult", "DoT"),
                  ("elementDmgMult", "Elem"), ("lifesteal", "Emme")]
        for class_id, base in InventoryManager.CLASS_BASES.items():
            preview = InventoryManager.get_class_preview(class_id, limit=99)
            for key, label in checks:
                if key not in base or label not in preview:
                    continue
                with self.subTest(sinif=class_id, stat=key):
                    shown = float(preview[label].replace('%', ''))
                    self.assertAlmostEqual(
                        shown, base[key] * 100, places=0,
                        msg=f"{class_id}.{key}: ekranda {preview[label]}, "
                            f"taban {base[key] * 100:+.0f}%")

    def test_secim_ekrani_stat_yazmiyor(self):
        """Sahne dosyasında elle stat sözlüğü kalmamalı (regresyon kilidi)."""
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'scenes', 'class_select_scene.py')
        with open(path, encoding='utf-8') as f:
            src = f.read()
        self.assertIn("get_class_preview", src,
                      "Sınıf önizlemesi türetilmiyor olabilir")
        # class_list girdilerinde elle "stats": { ... } bulunmamalı
        self.assertNotIn('"stats": {"', src,
                         "class_select_scene.py'de elle yazılmış stat sözlüğü var")


if __name__ == '__main__':
    unittest.main()
