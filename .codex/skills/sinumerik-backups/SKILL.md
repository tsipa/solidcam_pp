---
name: sinumerik-backups
description: Inspect and sanitize SINUMERIK .ard machine backups and associated Samba/SMB configuration before adding them to a Git repository. Use for archive credential audits, sanitized backup exports, and backup publication checks.
---

# SINUMERIK backups

Only publish backups after removing credentials. This includes encoded and
encrypted passwords; do not mistake them for harmless checksums. Inspect a copy
and preserve the original backup. Never stage the original even temporarily.

For supported ARD archives, inspect the decompressed zlib streams and the archive
directory. Search for populated password/secret fields, private keys, connection
URLs containing credentials, and SMB drive configuration. In 828D backups,
`logdrive.ini` can occur in both locations:

- `NC/_EXTNC_/USER/SINUMERIK/HMI/CFG/LOGDRIVE.INI`
- `HMI/_INST_/user/sinumerik/hmi/cfg/logdrive.ini`

Both copies must be sanitized or excluded. A name such as `NOLOG.ard` is not
evidence. Empty camera password fields and PLC symbol names containing
`Password` are not, by themselves, credentials.

Run the bundled checker from the repository root before staging:

```powershell
python .codex/skills/sinumerik-backups/scripts/check_credentials.py --files path/to/backup.ard
```

The checker reads archives in memory and never prints secret values. Unknown ARD
encodings or password-bearing binary data require manual investigation; do not
publish them based solely on a negative keyword search. Record the sanitized
file's SHA-256, omitted files, and inspection limits next to the backup.

This repository tracks `.githooks/pre-commit` and `.githooks/pre-push`. Enable
them once per clone with `git config core.hooksPath .githooks`; verify the value
before a commit/push. Fetch/pull updates hook files but does not enable hooks in
a new clone. Do not bypass the check. The pre-commit hook inspects staged blobs;
the pre-push hook also inspects outgoing intermediate commits, so deleting a
secret in a later commit does not make the earlier commit publishable.
