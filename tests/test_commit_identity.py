"""Every commit is authored and committed as the repository owner, tsipa740@gmail.com.

Owner rule 2026-10-28: no commit under any other identity (git falls back to user@host when
user.email is not set). The tracked hooks refuse such commits
(.githooks/check_commit_identity.py, pre-commit and pre-push); GitHub's web interface commits as
committer 'GitHub <noreply@github.com>' with the owner as author, which stays allowed.
"""
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / '.githooks/check_commit_identity.py'
SPEC = importlib.util.spec_from_file_location('commit_identity_check', SCRIPT)
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)

OWNER = 'Sergei Iudin', 'tsipa740@gmail.com'
AGENT = 'agent', 'agent@example.invalid'
GITHUB = 'GitHub', 'noreply@github.com'


def in_git_checkout():
    run = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], cwd=ROOT, capture_output=True, text=True)
    return run.returncode == 0 and run.stdout.strip() == 'true'


class IdentityRuleTests(unittest.TestCase):
    def test_only_the_owner_authors_and_github_may_commit(self):
        """INDEPENDENT: owner rule 2026-10-28."""
        self.assertEqual(CHECK.problems(OWNER[1], OWNER[1], 'c'), [])
        self.assertEqual(CHECK.problems(OWNER[1], GITHUB[1], 'c'), [])
        self.assertEqual(CHECK.problems('TSIPA740@gmail.com', OWNER[1], 'c'), [])
        self.assertEqual(len(CHECK.problems(AGENT[1], OWNER[1], 'c')), 1)
        self.assertEqual(len(CHECK.problems(OWNER[1], AGENT[1], 'c')), 1)
        self.assertEqual(len(CHECK.problems(GITHUB[1], GITHUB[1], 'c')), 1)
        self.assertEqual(len(CHECK.problems('', '', 'c')), 2)
        self.assertEqual(CHECK.email('Sergei Iudin <tsipa740@gmail.com> 1761700000 -0700'), OWNER[1])

    def test_repository_history_has_only_the_owner(self):
        """INDEPENDENT: owner rule 2026-10-28, on the checked-out history (rewritten 2026-10-28)."""
        if not in_git_checkout():
            self.skipTest('not a git checkout')
        run = subprocess.run([sys.executable, str(SCRIPT), '--history', 'HEAD'], cwd=ROOT,
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)


class IdentityHookTests(unittest.TestCase):
    """The checker and the tracked hooks in an isolated repository without a remote."""

    def setUp(self):
        if shutil.which('git') is None:
            self.skipTest('git not available')
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.git('init', '-q')
        self.git('config', 'core.hooksPath', 'empty-test-hooks')
        self.git('config', 'commit.gpgsign', 'false')

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args, env=None):
        return subprocess.check_output(['git', *args], cwd=self.root, env=env, stderr=subprocess.DEVNULL).decode().strip()

    def commit(self, name, author, committer):
        path = self.root / name
        path.write_text(name + '\n')
        self.git('add', name)
        self.git('-c', f'user.name={committer[0]}', '-c', f'user.email={committer[1]}', 'commit', '-qm', name,
                 f'--author={author[0]} <{author[1]}>')
        return self.git('rev-parse', 'HEAD')

    def run_check(self, *args, stdin=None, identity=None):
        env = None
        if identity:
            env = dict(os.environ, GIT_AUTHOR_NAME=identity[0], GIT_AUTHOR_EMAIL=identity[1],
                       GIT_COMMITTER_NAME=identity[0], GIT_COMMITTER_EMAIL=identity[1])
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.root, input=stdin, text=True,
                              capture_output=True, env=env)

    def test_staged_commit_identity(self):
        """INDEPENDENT: pre-commit refuses the agent host identity and accepts the owner."""
        self.assertEqual(self.run_check('--staged', identity=OWNER).returncode, 0)
        result = self.run_check('--staged', identity=AGENT)
        self.assertEqual(result.returncode, 1)
        self.assertIn('BLOCKED new commit: author agent@example.invalid', result.stderr)

    def test_every_outgoing_commit_is_checked(self):
        """INDEPENDENT: a later owner commit cannot hide an agent commit below it in a push."""
        base = self.commit('base', OWNER, GITHUB)
        agent = self.commit('agent', AGENT, AGENT)
        tip = self.commit('tip', OWNER, OWNER)
        result = self.run_check('--pre-push', 'origin', stdin=f'refs/heads/b {tip} refs/heads/b {base}\n')
        self.assertEqual(result.returncode, 1)
        self.assertIn(f'BLOCKED {agent[:12]}: author {AGENT[1]}', result.stderr)
        self.assertIn(f'BLOCKED {agent[:12]}: committer {AGENT[1]}', result.stderr)
        self.assertNotIn(tip[:12], result.stderr)
        # A new branch: everything not on the remote (no remote here, so all three commits).
        result = self.run_check('--pre-push', 'origin', stdin=f'refs/heads/b {tip} refs/heads/b {"0" * 40}\n')
        self.assertEqual(result.returncode, 1)
        self.assertIn(agent[:12], result.stderr)
        self.assertEqual(self.run_check('--pre-push', 'origin', stdin=f'refs/heads/b {base} refs/heads/b {"0" * 40}\n')
                         .returncode, 0)
        deletion = f'(delete) {"0" * 40} refs/heads/b {tip}\n'
        self.assertEqual(self.run_check('--pre-push', 'origin', stdin=deletion).returncode, 0)
        self.assertEqual(self.run_check('--history', tip).returncode, 1)
        self.assertEqual(self.run_check('--history', base).returncode, 0)

    def test_tracked_hooks_run_the_identity_check(self):
        """INDEPENDENT: the hooks in .githooks call the check (core.hooksPath .githooks, AGENTS.md)."""
        hooks = self.root / '.githooks'
        hooks.mkdir()
        for name in ('pre-commit', 'pre-push', 'check_commit_identity.py'):
            shutil.copyfile(ROOT / '.githooks' / name, hooks / name)
            (hooks / name).chmod(0o755)
        checker = self.root / '.codex/skills/sinumerik-backups/scripts/check_credentials.py'
        checker.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / '.codex/skills/sinumerik-backups/scripts/check_credentials.py', checker)
        # The agent commit is history made before the hooks were on.
        base = self.commit('base', OWNER, OWNER)
        tip = self.commit('agent', AGENT, AGENT)
        self.git('config', 'core.hooksPath', '.githooks')
        push = self.root / 'push-input.txt'
        push.write_text(f'refs/heads/b {tip} refs/heads/b {base}\n')
        result = subprocess.run(['git', 'hook', 'run', '--to-stdin=' + str(push), 'pre-push', '--', 'origin', 'unused'],
                                cwd=self.root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn(f'BLOCKED {tip[:12]}: author {AGENT[1]}', result.stderr)
        # With the hooks on, git commit itself refuses the agent identity and takes the owner's.
        with self.assertRaises(subprocess.CalledProcessError):
            self.commit('refused', AGENT, AGENT)
        self.assertEqual(self.git('rev-parse', 'HEAD'), tip)
        self.git('reset', '-q')
        accepted = self.commit('accepted', OWNER, OWNER)
        self.assertNotEqual(accepted, tip)


if __name__ == '__main__':
    unittest.main()
