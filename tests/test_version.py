"""Tests for version parsing and comparison."""
import os
import sys
import unittest

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.version import get_version, parse_semver, compare_versions


class TestParseSemver(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(parse_semver('1.6.0'), (1, 6, 0))

    def test_with_v_prefix(self):
        self.assertEqual(parse_semver('v2.1.3'), (2, 1, 3))

    def test_two_parts(self):
        self.assertEqual(parse_semver('1.0'), (1, 0, 0))

    def test_single_part(self):
        self.assertEqual(parse_semver('5'), (5, 0, 0))

    def test_empty_string(self):
        self.assertEqual(parse_semver(''), (0, 0, 0))


class TestCompareVersions(unittest.TestCase):
    def test_equal(self):
        self.assertEqual(compare_versions('1.6.0', '1.6.0'), 0)

    def test_greater(self):
        self.assertEqual(compare_versions('1.7.0', '1.6.0'), 1)

    def test_less(self):
        self.assertEqual(compare_versions('1.5.9', '1.6.0'), -1)

    def test_patch_difference(self):
        self.assertEqual(compare_versions('1.6.1', '1.6.0'), 1)

    def test_major_difference(self):
        self.assertEqual(compare_versions('2.0.0', '1.99.99'), 1)

    def test_v_prefix_ignored(self):
        self.assertEqual(compare_versions('v1.6.0', '1.6.0'), 0)


class TestGetVersion(unittest.TestCase):
    def test_reads_file(self):
        ver = get_version()
        self.assertRegex(ver, r'^\d+\.\d+\.\d+$')


if __name__ == '__main__':
    unittest.main()
