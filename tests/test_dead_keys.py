"""Tanımlı ama HİÇ TÜKETİLMEYEN içerik anahtarlarını yakalar.

NEDEN: Bu depoda tekrar eden bir hata modu var — içerik önce veriye (JSON) veya
bir sabit listeye yazılıyor, onu OKUYAN kod hiç yazılmıyor. Oyuncuya vaat
edilen şey hiç gerçekleşmiyor ve kimse fark etmiyor. Geçmişteki örnekler:

  - 47 kartın 37'si seçildiği anda hiçbir şey yapmıyordu
  - 18 evrim pasifinin 17'si okunmuyordu
  - 20 günlük görevin 14'ü takip edilmiyordu
  - `periodicAoeDmg` sinerji bonusu hiçbir yerde okunmuyordu
  - `sound_aggro` dalga olayı hiçbir yerde okunmuyordu

Mantık: bir anahtar yalnızca TANIMLANDIĞI yerde geçiyorsa, onu tüketen kod
yok demektir. Python kaynağında adıyla hiç aranmıyorsa ölüdür.

`logic/card_system.py` zaten benzer bir doğrulama yapıyor (eksik `apply`
metodunda açılışta hata atar); bu test aynı fikri veri anahtarlarına yayar.
"""
import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _py_sources(skip=()):
    """Tüm oyun kaynağı (testler ve araçlar hariç)."""
    out = {}
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs
                   if d not in ('.git', '__pycache__', 'venv', 'tests', 'tools', 'tmp')]
        for name in files:
            if not name.endswith('.py'):
                continue
            path = os.path.join(base, name)
            rel = os.path.relpath(path, ROOT).replace('\\', '/')
            if rel in skip:
                continue
            try:
                with open(path, encoding='utf-8') as f:
                    out[rel] = f.read()
            except OSError:
                pass
    return out


def _consumed(key, sources, declared_in):
    """Anahtar, tanımlandığı yerin DIŞINDA Python kodunda geçiyor mu?"""
    pattern = re.compile(r'["\']' + re.escape(key) + r'["\']')
    for rel, src in sources.items():
        if rel in declared_in:
            continue
        if pattern.search(src):
            return True
    return False


class TestDeadKeys(unittest.TestCase):
    """Her yeni içerik anahtarının bir tüketicisi olmalı."""

    # Bilinçli istisnalar: burada olan bir anahtar "ölü" sayılmaz.
    # Yeni istisna eklerken GEREKÇE yaz — bu liste kısa kalmalı.
    ALLOWED = {
        # Ölçek/kimlik alanları; davranış anahtarı değil.
        'id', 'name', 'desc', 'category', 'apply', 'tier', 'type', 'icon_id',
        'required_cards', 'bonuses', 'stats', 'itemBase', 'color',
    }

    def setUp(self):
        self.sources = _py_sources()

    def _rapor(self, olu, nerede):
        return (f"\n{nerede} içinde tanımlı ama Python kodunda HİÇ okunmayan "
                f"anahtarlar:\n  - " + "\n  - ".join(sorted(olu)) +
                "\n\nYa tüketen kodu yaz, ya tanımı kaldır. Bilerek "
                "bırakıyorsan tests/test_dead_keys.py -> ALLOWED listesine "
                "gerekçesiyle ekle.")

    def test_sinerji_bonuslari_tuketiliyor(self):
        path = os.path.join(ROOT, 'data', 'synergies.json')
        with open(path, encoding='utf-8') as f:
            synergies = json.load(f)
        keys = set()
        for syn in synergies:
            keys.update(syn.get('bonus', {}).keys())
        olu = {k for k in keys - self.ALLOWED
               if not _consumed(k, self.sources, declared_in=())}
        self.assertFalse(olu, self._rapor(olu, 'data/synergies.json'))

    def test_dalga_olayi_anahtarlari_tuketiliyor(self):
        """WAVE_EVENTS girdilerinin davranış anahtarları okunmalı.

        `sound_aggro` tam olarak burada yakalanır: sesi olmayan bir oyunda,
        ses üzerine kurulu, hiç uygulanmamış bir mekanik ilan ediliyordu.
        """
        from logic.game_logic import GameLogic
        keys = set()
        for event in GameLogic.WAVE_EVENTS:
            keys.update(event.keys())
        # game_logic.py anahtarları TANIMLADIĞI dosya; tüketim başka yerde
        # veya aynı dosyada olabilir, o yüzden tanım satırlarını ayıklıyoruz.
        olu = set()
        for key in keys - self.ALLOWED:
            pattern = re.compile(r'["\']' + re.escape(key) + r'["\']')
            hits = 0
            for rel, src in self.sources.items():
                for line in src.splitlines():
                    if pattern.search(line) and 'WAVE_EVENTS' not in line \
                            and not line.strip().startswith('{"id":'):
                        hits += 1
            if hits == 0:
                olu.add(key)
        self.assertFalse(olu, self._rapor(olu, 'GameLogic.WAVE_EVENTS'))

    def test_kart_stat_anahtarlari_tuketiliyor(self):
        path = os.path.join(ROOT, 'data', 'cards.json')
        with open(path, encoding='utf-8') as f:
            cards = json.load(f)
        keys = set()
        for card in cards:
            keys.update(card.get('stats', {}).keys())
        olu = {k for k in keys - self.ALLOWED
               if not _consumed(k, self.sources, declared_in=())}
        self.assertFalse(olu, self._rapor(olu, 'data/cards.json'))

    def test_her_kartin_apply_metodu_var(self):
        """card_system'in açılış doğrulamasının test karşılığı."""
        from logic.card_system import CardSystem
        eksik = [c['id'] for c in CardSystem.CARDS
                 if not hasattr(CardSystem, c['apply'])]
        self.assertFalse(eksik, f"apply metodu olmayan kartlar: {eksik}")


if __name__ == '__main__':
    unittest.main()
