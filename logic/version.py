import os
import sys

def _base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_version():
    try:
        vfile = os.path.join(_base_path(), 'version.txt')
        with open(vfile, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except (FileNotFoundError, OSError):
        return '0.0.0'

def parse_semver(v_str):
    parts = v_str.lstrip('v').split('.')
    nums = []
    for p in parts[:3]:
        try:
            nums.append(int(p))
        except ValueError:
            nums.append(0)
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums)

def compare_versions(a, b):
    ta, tb = parse_semver(a), parse_semver(b)
    if ta < tb: return -1
    if ta > tb: return 1
    return 0
