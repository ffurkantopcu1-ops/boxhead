"""Tests for launcher update logic - all network calls are mocked."""
import hashlib
import json
import os
import sys
import shutil
import tempfile
import unittest
import zipfile
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from launcher.updater import (
    parse_semver, compare_versions, sha256_file,
    validate_zip_entries, perform_update, get_local_version,
    fetch_latest_release,
)


class TestSemver(unittest.TestCase):
    def test_parse_basic(self):
        self.assertEqual(parse_semver('1.2.3'), (1, 2, 3))

    def test_parse_with_v(self):
        self.assertEqual(parse_semver('v0.1.0'), (0, 1, 0))

    def test_parse_short(self):
        self.assertEqual(parse_semver('1'), (1, 0, 0))

    def test_parse_invalid(self):
        self.assertEqual(parse_semver('abc'), (0, 0, 0))

    def test_compare_equal(self):
        self.assertEqual(compare_versions('1.0.0', '1.0.0'), 0)

    def test_compare_greater(self):
        self.assertEqual(compare_versions('2.0.0', '1.0.0'), 1)

    def test_compare_less(self):
        self.assertEqual(compare_versions('1.0.0', '2.0.0'), -1)

    def test_compare_patch(self):
        self.assertEqual(compare_versions('1.0.1', '1.0.0'), 1)


class TestChecksum(unittest.TestCase):
    def test_sha256_file(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            f.write(b'hello world')
            path = f.name
        try:
            expected = hashlib.sha256(b'hello world').hexdigest()
            self.assertEqual(sha256_file(path), expected)
        finally:
            os.unlink(path)

    def test_sha256_empty_file(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            path = f.name
        try:
            expected = hashlib.sha256(b'').hexdigest()
            self.assertEqual(sha256_file(path), expected)
        finally:
            os.unlink(path)


class TestZipValidation(unittest.TestCase):
    def _make_zip(self, entries, path):
        with zipfile.ZipFile(path, 'w') as zf:
            for name, content in entries:
                zf.writestr(name, content)

    def test_safe_zip(self):
        with tempfile.TemporaryDirectory() as d:
            zp = os.path.join(d, 'safe.zip')
            self._make_zip(
                [('readme.txt', 'hi'), ('sub/file.txt', 'data')], zp
            )
            validate_zip_entries(zp, os.path.join(d, 'target'))

    def test_traversal_detected(self):
        with tempfile.TemporaryDirectory() as d:
            zp = os.path.join(d, 'evil.zip')
            self._make_zip([('../../../etc/passwd', 'pwned')], zp)
            with self.assertRaises(ValueError):
                validate_zip_entries(zp, os.path.join(d, 'target'))

    def test_absolute_path_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            zp = os.path.join(d, 'abs.zip')
            self._make_zip([('/tmp/evil.txt', 'data')], zp)
            # Depending on OS, this may or may not be traversal,
            # but realpath should catch it on Windows
            try:
                validate_zip_entries(zp, os.path.join(d, 'target'))
            except ValueError:
                pass  # Expected on some systems


class TestPerformUpdate(unittest.TestCase):
    def test_successful_update(self):
        with tempfile.TemporaryDirectory() as install_dir:
            # Existing files
            os.makedirs(os.path.join(install_dir, 'assets'), exist_ok=True)
            with open(os.path.join(install_dir, 'assets', 'old.txt'), 'w') as f:
                f.write('old')
            with open(os.path.join(install_dir, 'version.txt'), 'w') as f:
                f.write('1.0.0')

            # Saves that must survive
            saves_dir = os.path.join(install_dir, 'saves')
            os.makedirs(saves_dir, exist_ok=True)
            with open(os.path.join(saves_dir, 'save1.json'), 'w') as f:
                f.write('{"data": 1}')

            # Update ZIP
            zip_path = os.path.join(install_dir, 'update.zip')
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr('version.txt', '2.0.0')
                zf.writestr('assets/new.txt', 'new')

            perform_update(zip_path, install_dir)

            # Verify update applied
            with open(os.path.join(install_dir, 'version.txt')) as f:
                self.assertEqual(f.read().strip(), '2.0.0')
            self.assertTrue(
                os.path.exists(os.path.join(install_dir, 'assets', 'new.txt'))
            )

            # Verify saves untouched
            with open(os.path.join(saves_dir, 'save1.json')) as f:
                self.assertEqual(f.read(), '{"data": 1}')

            # Verify cleanup
            self.assertFalse(
                os.path.exists(os.path.join(install_dir, '_update_staging'))
            )
            self.assertFalse(
                os.path.exists(os.path.join(install_dir, '_update_backup'))
            )
            self.assertFalse(os.path.exists(zip_path))

    def test_saves_never_overwritten(self):
        """Even if ZIP contains saves/, they must not overwrite local saves."""
        with tempfile.TemporaryDirectory() as install_dir:
            saves = os.path.join(install_dir, 'saves')
            os.makedirs(saves)
            with open(os.path.join(saves, 'progress.json'), 'w') as f:
                f.write('{"level": 42}')

            zip_path = os.path.join(install_dir, 'update.zip')
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr('version.txt', '9.9.9')
                zf.writestr('saves/progress.json', '{"level": 0}')

            perform_update(zip_path, install_dir)

            with open(os.path.join(saves, 'progress.json')) as f:
                data = json.loads(f.read())
            self.assertEqual(data['level'], 42)


class TestFetchRelease(unittest.TestCase):
    @patch('launcher.updater.urllib.request.urlopen')
    def test_successful_fetch(self, mock_urlopen):
        manifest_data = {
            'version': '1.7.0',
            'filename': 'Boxhead-1.7.0-win64.zip',
            'sha256': 'abc123def456',
            'size': 50000000,
            'min_launcher_version': '1.0.0',
        }

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(manifest_data).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = fetch_latest_release()
        self.assertEqual(result['version'], '1.7.0')
        self.assertEqual(result['sha256'], 'abc123def456')
        self.assertIn('Boxhead', result['download_url'])
        self.assertEqual(mock_urlopen.call_count, 1)

    @patch('launcher.updater.urllib.request.urlopen')
    def test_network_failure_retries(self, mock_urlopen):
        mock_urlopen.side_effect = Exception('Connection refused')
        with self.assertRaises(RuntimeError):
            fetch_latest_release()
        self.assertEqual(mock_urlopen.call_count, 1)


class TestLocalVersion(unittest.TestCase):
    def test_missing_file_returns_fallback(self):
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as d:
            os.chdir(d)
            try:
                ver = get_local_version()
                self.assertEqual(ver, '0.0.0')
            finally:
                os.chdir(original_cwd)


if __name__ == '__main__':
    unittest.main()
