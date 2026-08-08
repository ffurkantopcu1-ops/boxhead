import json
import os
import sys

_CACHE = {}


def _base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_data(name):
    """data/<name>.json dosyasını okur ve cache'ler."""
    if name not in _CACHE:
        path = os.path.join(_base_path(), 'data', name + '.json')
        with open(path, 'r', encoding='utf-8') as f:
            _CACHE[name] = json.load(f)
    return _CACHE[name]
