# Changelog

## 1.2.0

### Added
- HellBlast explosion guard (merged from `goetyhellblastfix` 0.0.2): hellfire blasts without an owner no longer crash the server on impact. Damage and knockback are unchanged; only the burn step is skipped when no owner exists.
- `build.ps1`: one-command build. Reads the version from `META-INF/mods.toml` and produces a byte-identical jar on every run.

### Changed
- Mixin guards: 22 → 23 (22 `isAlliedTo` guards + 1 `HellBlast` guard).
- Mod version: 1.1.2 → 1.2.0. Mod description now covers both guarded crash types.
- Test harness (`test/GoetyFixTest.java`): registers the `HereticServant` and `HellBlast` guards; dependency assertions now report actual values.
- README (EN / ZH): HellBlast section, install notes, log-based verification, changelog.

### Compatibility
- Forge 1.20.1, Goety 2.5.49 – 2.5.58.4.
- Replaces `goetyhellblastfix` 0.0.2 — uninstall its jar before installing this one.
- Coexists with `goety-apostle-fix` (modId `goetyfix`).
- For 1.21.1 / NeoForge, use v2.0.0.
