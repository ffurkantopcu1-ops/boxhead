"""Straight connections must avoid unrelated passive nodes."""
import json
import unittest
from pathlib import Path

from tools.tree_layout import RADII


class TreeLayoutTests(unittest.TestCase):
    def test_straight_edges_avoid_unrelated_nodes(self):
        root = Path(__file__).resolve().parents[1] / 'data'
        nodes = json.loads((root / 'skill_tree.json').read_text(encoding='utf-8'))
        by_id = {n['id']: n for n in nodes}
        edges = {'|'.join(sorted((n['id'], other)))
                 for n in nodes for other in n.get('connects', [])}
        for key in edges:
            first, second = key.split('|')
            points = [by_id[first]['pos'], by_id[second]['pos']]
            for a, b in zip(points, points[1:]):
                dx, dy = b[0] - a[0], b[1] - a[1]
                denominator = dx * dx + dy * dy
                for node in nodes:
                    if node['id'] in (first, second):
                        continue
                    x, y = node['pos']
                    t = max(0, min(1, ((x-a[0])*dx + (y-a[1])*dy) / denominator)) if denominator else 0
                    distance2 = (x-a[0]-t*dx)**2 + (y-a[1]-t*dy)**2
                    self.assertGreaterEqual(distance2 + 1e-6, RADII[node['type']]**2,
                                            f'{key} crosses {node["id"]}')
