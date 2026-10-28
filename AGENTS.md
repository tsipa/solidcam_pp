# Machine backups and credentials

- Before staging, committing, or pushing `.ard` archives or Samba/SMB files from
  machine backups, remove passwords, tokens, private keys, and other secrets.
  Encoded or encrypted passwords are still credentials and must also be removed.
- Inspect decompressed archive contents; a clean filename such as `NOLOG.ard`
  does not establish that a backup is sanitized. Never add the unsanitized source
  archive to Git, including temporarily or in a commit that is later amended.
- Prefer an export without credential-bearing files such as both copies of
  `logdrive.ini`. Preserve the source backup and sanitize only a separate copy.
- Use [.codex/skills/sinumerik-backups/SKILL.md](.codex/skills/sinumerik-backups/SKILL.md)
  for backup inspection and publication. Run its credential checker before adding
  a new backup. The checker is a guard for known formats, not proof that an
  unfamiliar binary format contains no secrets; inspect unsupported data first.
- Enable the tracked local hooks in every clone before committing or pushing:
  `git config core.hooksPath .githooks`. Check with `git config --get core.hooksPath`.
  Git does not activate hooks merely because their files were fetched or pulled.
  Do not bypass these hooks with `--no-verify` or disable them to publish a backup.
  The pre-push hook checks outgoing commit contents, including intermediate
  commits, before Git sends them to the remote.

# Commit identity

- Every commit is authored and committed as `Sergei Iudin <tsipa740@gmail.com>`.
  Set `git config user.name "Sergei Iudin"` and `git config user.email tsipa740@gmail.com`
  before committing. The hooks refuse any other identity
  (`.githooks/check_commit_identity.py`, also in pre-push for every outgoing commit).

# VERICUT

- For VERICUT project/control work, use
  [.codex/skills/vericut-control/SKILL.md](.codex/skills/vericut-control/SKILL.md).

# CAM trace and fixture identities

- Before staging any recorded CAM trace, NC example, fixture, manifest or supporting
  documentation, remove original part and operation names, including their paths,
  filenames, comments, messages and debug output. Apply this to compressed contents
  as well; never commit the raw source or an original-to-neutral name mapping.
- Use stable neutral aliases for operations and related geometry/setup identities.
  Tool names and tool data may remain unchanged. Preserve numeric machining inputs,
  event order, change flags and native precision.
- The SolidCAM user account (`user_account` in `start_of_file`) is an identity as
  well; the extractor writes `USER`. Neutralize account, computer/host and Windows
  user names, including user-profile paths such as `C:\Users\<name>`, wherever they
  appear.
- The post now emits CAMDBG readouts at trace_level 5. Extract supported fields with
  `python -m pp_tests.tools.input_trace`; do not add raw debug NC to the repository.
  Inspect new debug string fields for identities before extending the extractor.
- Follow [tests/fixtures/README.md](tests/fixtures/README.md#sanitization-rules)
  when recording or updating fixtures. Check the decompressed export for original
  names and distinctive fragments before staging; automatic field replacement alone
  does not establish that an unfamiliar trace format is sanitized.
