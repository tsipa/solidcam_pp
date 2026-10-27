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

# VERICUT

- For VERICUT project/control work, use
  [.codex/skills/vericut-control/SKILL.md](.codex/skills/vericut-control/SKILL.md).
