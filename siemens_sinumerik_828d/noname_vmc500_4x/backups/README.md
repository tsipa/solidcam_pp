# Sanitized SINUMERIK backup

`NOLOG.ard` is the user-provided export from `BACKUP/OCT2026`, inspected on
2026-10-27. It is copied unchanged; the original backup containing the saved SMB
password (`OCT2026.ard`) is deliberately not included.

- Size: 11,187,402 bytes.
- SHA-256: `b967f3e5f76505875b2a5375ae28bc24ea68c540fc527e60055172150121bfb6`.
- Both credential-bearing `logdrive.ini` entries present in the original export
  are absent: `NC/_EXTNC_/USER/SINUMERIK/HMI/CFG/LOGDRIVE.INI` and
  `HMI/_INST_/user/sinumerik/hmi/cfg/logdrive.ini`.
- The corresponding SMB server/login block is absent. Empty camera username and
  password fields remain; they contain no saved credentials.
- The local checker inspected the raw bytes and 220 validated, decompressed zlib
  streams for populated credential fields, private keys, and credential URLs;
  no known patterns were found. This does not prove that every binary payload or
  image is free of sensitive information. Machine data, PLC/drive data, OEM data,
  and license-option settings are intentionally retained.

Before adding another archive, follow [AGENTS.md](../../../AGENTS.md) and the
[backup skill](../../../.codex/skills/sinumerik-backups/SKILL.md). Enable local
hooks first with `git config core.hooksPath .githooks`. An archive filename alone
does not establish sanitization, and encoded passwords must also be removed.
