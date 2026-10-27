"""Local checks for credentials in staged files and outgoing commit history."""
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / '.codex/skills/sinumerik-backups/scripts/check_credentials.py'
SPEC = importlib.util.spec_from_file_location('backup_credential_check', SCRIPT)
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class BackupCredentialTests(unittest.TestCase):
    def test_encoded_passwords_and_utf16_are_credentials(self):
        """INDEPENDENT: a populated password remains a secret in encoded form."""
        text = '[DEVICE_6]\nType=smb\nPassword=ENCODED_TEST_VALUE\n'
        for encoding in ('utf-8', 'utf-16le', 'utf-16be'):
            with self.subTest(encoding=encoding):
                findings = CHECK.audit('logdrive.ini', text.encode(encoding))
                self.assertTrue(findings)
                self.assertNotIn('ENCODED_TEST_VALUE', '\n'.join(findings))

    def test_empty_fields_and_symbols_are_not_passwords(self):
        """INDEPENDENT: empty XML/config fields and symbol names contain no value."""
        data = b'Password=\nUsername=ANONYMOUS\n<password/>\n<password></password>\nEE.Password\n'
        self.assertEqual(CHECK.audit('logdrive.ini', data), [])

    def test_xml_keys_and_urls_are_rejected(self):
        """INDEPENDENT: XML fields, key material, and credential URLs expose secrets."""
        for text in ('<password>TEST_ONLY</password>', '<camera password="TEST_ONLY"/>',
                     '-----BEGIN OPENSSH PRIVATE KEY-----', 'smb://test:TEST_ONLY@host/share'):
            with self.subTest(format=text[:20]):
                self.assertTrue(CHECK.audit('backups/config.xml', text.encode()))

    def test_ard_decompression_and_sanitized_copy(self):
        """INDEPENDENT: credentials inside a compressed ARD must be inspected."""
        header = zlib.compress(b'<dc areas="@HMI"></dc>')
        unsafe = header + zlib.compress(b'Password=COMPRESSED_TEST_ONLY\n')
        safe = header + zlib.compress(b'Password=\n')
        self.assertTrue(CHECK.audit('NOLOG.ard', unsafe))
        self.assertEqual(CHECK.audit('NOLOG.ard', safe), [])
        self.assertTrue(CHECK.audit('unknown.ard', b'unsupported binary format'))
        self.assertTrue(CHECK.candidate('arbitrary/path/backup.ARD'))
        self.assertTrue(CHECK.candidate('backups/settings.xml'))
        self.assertFalse(CHECK.candidate('tests/test_backup_credentials.py'))

    def test_staged_blob_and_intermediate_outgoing_commits_are_checked(self):
        """INDEPENDENT: cleaning a worktree or a later commit cannot clean history."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.DEVNULL).decode().strip()

            def commit(message):
                git('-c', 'user.name=Credential guard test', '-c', 'user.email=test@example.invalid',
                    '-c', 'commit.gpgsign=false', 'commit', '-qm', message)
                return git('rev-parse', 'HEAD')

            def run_check(*args, stdin=None):
                return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=root,
                                      input=stdin, text=True, capture_output=True)

            git('init', '-q')
            # This isolated fixture intentionally creates unsafe history so the
            # pre-push checker can prove it refuses that history. No remote exists.
            git('config', 'core.hooksPath', 'empty-test-hooks')
            (root / 'README').write_text('Synthetic credential-check fixture\n')
            git('add', 'README')
            base = commit('base')
            config = root / 'logdrive.ini'
            config.write_text('Password=HISTORY_TEST_ONLY\n')
            git('add', 'logdrive.ini')
            config.write_text('Password=\n')  # clean worktree; index still unsafe
            result = run_check('--staged')
            self.assertEqual(result.returncode, 1)
            self.assertNotIn('HISTORY_TEST_ONLY', result.stderr)
            config.write_text('Password=HISTORY_TEST_ONLY\n')
            commit('unsafe intermediate fixture')
            config.write_text('Password=\n')
            git('add', 'logdrive.ini')
            self.assertEqual(run_check('--staged').returncode, 0)
            tip = commit('sanitized tip fixture')
            push = f'refs/heads/test {tip} refs/heads/test {base}\n'
            result = run_check('--pre-push', 'origin', stdin=push)
            self.assertEqual(result.returncode, 1)
            self.assertIn('logdrive.ini', result.stderr)
            self.assertNotIn('HISTORY_TEST_ONLY', result.stderr)
            deletion = f'(delete) {"0" * 40} refs/heads/test {tip}\n'
            self.assertEqual(run_check('--pre-push', 'origin', stdin=deletion).returncode, 0)
            # Run the actual tracked hook too, without contacting any remote.
            hooks = root / '.githooks'
            hooks.mkdir()
            for name in ('pre-commit', 'pre-push'):
                shutil.copyfile(SCRIPT.parents[4] / '.githooks' / name, hooks / name)
                (hooks / name).chmod(0o755)
            bundled = root / '.codex/skills/sinumerik-backups/scripts/check_credentials.py'
            bundled.parent.mkdir(parents=True)
            shutil.copyfile(SCRIPT, bundled)
            git('config', 'core.hooksPath', '.githooks')
            push_input = root / 'push-input.txt'
            push_input.write_text(push)
            result = subprocess.run(['git', 'hook', 'run', '--to-stdin=' + str(push_input),
                                     'pre-push', '--', 'origin', 'unused'],
                                    cwd=root, text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('BLOCKED logdrive.ini', result.stderr)
            self.assertNotIn('HISTORY_TEST_ONLY', result.stderr)
            config.write_text('Password=STAGED_TEST_ONLY\n')
            git('add', 'logdrive.ini')
            result = subprocess.run(['git', 'hook', 'run', 'pre-commit'], cwd=root,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('BLOCKED logdrive.ini', result.stderr)
            self.assertNotIn('STAGED_TEST_ONLY', result.stderr)
